#!/usr/bin/env python
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import os
import pydicom
import numpy as np
#import SimpleITK as sitk
import itk
import logging
import time
logger=logging.getLogger(__name__)

class ct_image_base:
    @property
    def meta_data(self):
        slicetimes = [ int(s.get("InstanceCreationTime","0")) for s in self._slices ]
        return {
                "Institution Name"   : str(self._slices[0].get("InstitutionName","anonymized")),
                "Series Instance UID": self._uid,
                "Creation Date"      : str(self._slices[0].get("InstanceCreationDate","anonymized")),
                "Imaging time"       : "{}-{}".format(min(slicetimes),max(slicetimes)),
                "NVoxelsXYZ"         : tuple(self.size.tolist()),
                "NVoxelsTOT"         : np.prod(self.array.shape),
                "Resolution [mm]"    : tuple(self.voxel_size.tolist()),
                "Origin [mm]"        : tuple(self.origin.tolist()),
                "Center [mm]"        : tuple((self.origin+0.5*(self.size-1)*self.voxel_size).tolist()),
                }
    @property
    def img(self):
        # TODO: should we return a copy or a reference?
        return self._img
    @property
    def nvoxels(self):
        # more intuitive name than 'size'
        return np.array(self._img.GetLargestPossibleRegion().GetSize())
    @property
    def size(self):
        return np.array(self._img.GetLargestPossibleRegion().GetSize())
    @property
    def physical_size(self):
        return self.size*np.array(self._img.GetSpacing())
    @property
    def voxel_size(self):
        return np.array(self._img.GetSpacing())
    @property
    def origin(self):
        return np.array(self._img.GetOrigin())
    @property
    def array(self):
        return self._img_array
    @property
    def slices(self):
        return self._slices
    @property
    def uid(self):
        return str(self._slices[0].SeriesInstanceUID)
    def write_to_file(self,mhd):
        assert(mhd[-4:].lower() == ".mhd")
        itk.imwrite(self._img,mhd)

class ct_image_from_dicom(ct_image_base):
    def __init__(self,ddir,uid=None):
        # TODO: is there really not any ITK library function that actually does this for us?
        self._ndepth = 0
        uid,flist = self._get_series_filenames(ddir,uid)
        if not bool(uid) or len(flist)<=1:
            raise RuntimeError("no CT image found in dir {}".format(ddir))
        logger.debug("got {} CT files, first={} last={}".format(len(flist),flist[0],flist[-1]))
        self._slices = [pydicom.read_file(f) for f in flist]
        logger.debug("got {} CT slices".format(len(self._slices)))
        #slice_nrs = list()
        #for i,s in enumerate(self._slices):
        #    logger.debug("{}th has instance number '{}' with type '{}'".format(i,str(s.InstanceNumber),type(s.InstanceNumber)))
        #    #slice_nrs.append(int(s.InstanceNumber))
        #if set([1]) == set(np.diff([int(s.InstanceNumber) for s in self._slices]).tolist()):
        #    logger.debug("yep, CT series is correctly sorted")
        #else:
        #    logger.info("CT series needs sorting!")
        self._slices.sort( key = lambda x: float(x.ImagePositionPatient[2]) )
        slice_thicknesses = np.round(np.diff([s.ImagePositionPatient[2] for s in self._slices]),decimals=2)
        pixel_widths = np.round([s.PixelSpacing[0] for s in self._slices],decimals=2)
        pixel_heights = np.round([s.PixelSpacing[1] for s in self._slices],decimals=2)
        spacing = []
        logger.debug("going to obtain voxel spacing")
        for sname,spacings in zip(["pixel width","pixel height","slice thickness"],
                                  [pixel_widths,pixel_heights,slice_thicknesses]):
            if 1<len(set(spacings)):
                # TO DO: define rounding error tolerance
                logger.warn("The {} seems to suffer from rounding issues (or missing slices): min={} mean={} median={} std={} max={}".format(
                    sname,np.min(spacings),np.mean(spacings),np.median(spacings),np.std(spacings),np.max(spacings) ))
            spacing.append(np.mean(spacings))
        logger.debug("spacing is ({},{},{})".format(*spacing))
        origin = self._slices[0].ImagePositionPatient[:]
        logger.debug("origin is ({},{},{})".format(*origin))
        # TODO: is it possible that some self._slices have a different intercept and slope?
        intercept = np.int16(self._slices[0].RescaleIntercept)
        slope = np.float64(self._slices[0].RescaleSlope)
        logger.debug("HU rescale: slope={}, intercept={}".format(slope,intercept))
        if slope != 1:
            self._img_array = np.stack([s.pixel_array for s in self._slices]).astype(np.int16)
            self._img_array = (slope*self._img_array).astype(np.int16)+intercept
        else:
            self._img_array = np.stack([s.pixel_array for s in self._slices]).astype(np.int16)+intercept
        logger.debug("after HU rescale: min={}, mean={}, median={}, max={}".format( np.min(self._img_array),
                                                                                    np.mean(self._img_array),
                                                                                    np.median(self._img_array),
                                                                                    np.max(self._img_array)))
        self._img = itk.GetImageFromArray(self._img_array)
        self._img.SetSpacing(tuple(spacing))
        self._img.SetOrigin(tuple(origin))
        self._uid = uid
    def _get_series_filenames(self,ddir,uid):
        logger.debug("getting DICOM series IDs in dir={}, depth={}".format(ddir,self._ndepth))
        #ids = sitk.ImageSeriesReader_GetGDCMSeriesIDs(ddir)
        dcmseries_reader = itk.GDCMSeriesFileNames.New(Directory=ddir)
        ids = dcmseries_reader.GetSeriesUIDs()
        logger.debug("got DICOM {} series IDs".format(len(ids)))
        flist=list()
        if uid:
            if uid in ids:
                try:
                    #flist = sitk.ImageSeriesReader_GetGDCMSeriesFileNames(ddir,uid)
                    flist = dcmseries_reader.GetFileNames(uid)
                    return uid,flist
                except:
                    logger.error('something wrong with series uid={} in directory {}'.format(uid,ddir))
                    raise
        else:
            ctid = list()
            for suid in ids:
                #flist = sitk.ImageSeriesReader_GetGDCMSeriesFileNames(ddir,suid)
                flist = dcmseries_reader.GetFileNames(suid)
                f0 = pydicom.dcmread(flist[0])
                if not hasattr(f0,'SOPClassUID'):
                    logger.warn("weird, file {} has no SOPClassUID".format(os.path.basename(flist[0])))
                    continue
                descr = pydicom.uid.UID_dictionary[f0.SOPClassUID][0]
                if descr == 'CT Image Storage':
                    logger.debug('found CT series id {}'.format(suid))
                    ctid.append(suid)
                else:
                    logger.debug('not CT: series id {} is a "{}"'.format(suid,descr))
            if len(ctid)>1:
                raise ValueError('no series UID was given, and I found {} different CT image series: {}'.format(len(ctid), ",".join(ctid)))
            elif len(ctid)==1:
                uid = ctid[0]
                #flist = sitk.ImageSeriesReader_GetGDCMSeriesFileNames(ddir,uid)
                flist = dcmseries_reader.GetFileNames(uid)
                return uid,flist
        # still no files?
        subdirs = [os.path.realpath(os.path.join(ddir,d)) for d in os.listdir(ddir) if os.path.isdir(os.path.join(ddir,d))]
        for subdir in subdirs:
            logger.debug("trying to find CT image series in subdirectory {}".format(subdir))
            self._ndepth += 1
            uid,flist = self._get_series_filenames(subdir,uid)
            self._ndepth -= 1
            if bool(uid) and bool(flist):
                break
        return uid,flist

class ct_image_from_mhd(ct_image_base):
    def __init__(self,mhd,meta_data={}):
        self._meta_data = meta_data
        self._mhd = mhd
        self._img = itk.imread(mhd)
        self._slices = []
    @property
    def array(self):
        #return itk.image_view_from_image(self._img)
        return itk.array_view_from_image(self._img)
    @property
    def uid(self):
        return "undefined"
    @property
    def meta_data(self):
        m = dict()
        m.update(self._meta_data)
        m.update( { "NVoxelsXYZ"         : tuple(self.size.tolist()),
                    "NVoxelsTOT"         : np.prod(self.array.shape),
                    "Resolution [mm]"    : tuple(self.voxel_size.tolist()),
                    "Origin [mm]"        : tuple(self.origin.tolist()),
                    "Center [mm]"        : tuple((self.origin+0.5*(self.size-1)*self.voxel_size).tolist()),
                  } )
        return m

def write_dicom_ct_image_to_mhd(ddir,mhd):
    try:
        ct = ct_image_from_dicom(ddir)
        ct.write_to_file(mhd)
    except Exception as e:
        logger.error("problem finding a CT image (or writing it): {}".format(e))
        time.sleep(3)
        raise

# for interactive use
def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v","--verbose",default=False,action='store_true',help="be verbose, show debugging output")
    parser.add_argument("-f",  "--force",default=False,action='store_true',help="overwrite existing image files")
    parser.add_argument("-o", "--output",type=argparse.FileType('w'),help="image output file (with .mhd suffix)",required=True)
    parser.add_argument("directory",help="full path of directory where to find CT*.dcm files")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - line %(lineno)d - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO,format='%(levelname)s - %(message)s')
    if not os.path.isdir(args.directory):
        raise argparse.ArgumentTypeError("'{}' is not a directory".format(args.directory))
    if not args.output.name[-4:].lower() == ".mhd":
        raise argparse.ArgumentTypeError("Only MHD supported, got '{}' as output file".format(args.output.name))
    return args.directory,args.output.name

if __name__ == '__main__':
    write_dicom_ct_image_to_mhd(*get_args())

# vim: set et softtabstop=4 sw=4 smartindent:
