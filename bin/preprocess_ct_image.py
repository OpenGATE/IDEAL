#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

# Create logger with file handler, because the output of PRE scripts in condor DAGman does not get saved.
import logging
if False:
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
else:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s')
    logfilename="preprocessor.log"
    fh = logging.FileHandler(logfilename)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

import os,sys
import tarfile
import configparser
import pydicom
import numpy as np
#import SimpleITK as sitk
import itk
from datetime import datetime
from utils.roi_utils import region_of_interest, list_roinames
from utils.itk_image_utils import itk_image_from_array
from utils.bounding_box import bounding_box
from utils.ct_dicom_to_img import ct_image_from_dicom
from utils.crop import crop_and_pad_image
from utils.mass_image import create_mass_image

current_action=""

def update_user_logs(user_cfg,status,section="DEFAULT",changes=dict()):
    # this function is used in three places, maybe I should upgrade it to a module
    global current_action
    current_action="updating user logs"
    if bool(user_cfg):
        parser=configparser.ConfigParser()
        logger.debug("going to read user logs/settings in {}".format(user_cfg))
        with open(user_cfg,"r") as fp:
            parser.read_file(fp)
        logger.debug("going to update user logs/settings in section {}".format(section))
        if bool(changes):
            parser[section].update(changes)
        parser['DEFAULT']["status"] = status
        parser['DEFAULT']["date and time of last update"] = datetime.now().ctime()
        with open(user_cfg,"w") as fp:
            parser.write(fp)
        logger.debug("finished updating user logs/settings in {}".format(user_cfg))

def GetMCPatientCTImage(rpdir,ssdcm,ctuid,HUoverride,HU_override_density,hlut_path, #mhd_resized,
                        mhd_orig_ct, mhd_overrides, ct_bb,
                        dose_grid_center,dose_grid_size,dose_grid_nvoxels,mhd_dose_grid_mask):

    global current_action
    current_action="initializing preprocessing"
    logger.debug("rpdir={}".format(rpdir))
    logger.debug("ctuid={}".format(ctuid))
    logger.debug("ssdcm={}".format(ssdcm))
    logger.debug("mhd_orig_ct={}".format(mhd_orig_ct))
    logger.debug("mhd_overrides={}".format(mhd_overrides))
    logger.debug("mhd_dose_grid_mask={}".format(mhd_dose_grid_mask))

    # step 1: obtain original CT and structure set from DICOM
    current_action="reading original CT"
    ct_orig = itk.imread(mhd_orig_ct)
    act_orig = itk.GetArrayFromImage(ct_orig)
    current_action="reading structure set"
    structure_set = pydicom.dcmread(os.path.join(str(rpdir),str(ssdcm)))
    logger.debug("roinames={}".format(",".join(list_roinames(structure_set))))

    # step 2: apply material overrides
    # step 2a: get name of external ROI, get HU value of air
    current_action="reading material overrides"
    tmp = [(k[1:],v) for k,v in HUoverride.items() if k[0]=="!" and k!="!HUMAX" and k!="!DOSEPAD"]
    if not len(tmp)==1:
        raise RuntimeError("PROGRAMMING ERROR: external ROI entry missing from HU overrides list.")
    external,hu_air=tmp[0]
    # step 2b: apply HUMAX, i.e. any voxel with HU>humax (except for air-padded voxels) is forced down to humax.
    if not "!HUMAX" in HUoverride:
        raise RuntimeError("PROGRAMMING ERROR: '!HUMAX' entry missing from HU overrides list.")
    current_action="applying max HU filter"
    hu_max = HUoverride["!HUMAX"]
    hu_dosepad = HUoverride.get("!DOSEPAD",hu_air) # optional
    mask = act_orig>hu_max
    #mask *= np.logical_not(act_resized==hu_air) # do not apply this override to padded voxels
    act_orig[mask] = hu_max

    # step 2c: enforce air outside of external
    current_action="overriding voxels outside external ROI with G4_AIR"
    ext_roi = region_of_interest(ds=structure_set,roi_id=external)
    ext_mask = ext_roi.get_mask(ct_orig,corrected=False)
    ext_array = itk.GetArrayViewFromImage(ext_mask)>0
    act_orig[np.logical_not(ext_array)] = hu_air
    ntot = np.prod(ext_array.shape)
    nin = np.sum(ext_array)
    nout = ntot-nin
    update_user_logs(user_logs,"PREPROCESSING AIR OVERRIDE COMPLETE",section="CT",
            changes={"orig ct nr voxels [total,external,air]":f"{ntot},{nin},{nout}"})

    # step 2d: apply other HU overrides
    current_action="overriding materials inside given ROIs"
    n_override=0
    n_rois=0
    for roiname,huval in HUoverride.items():
        if roiname[0] == "!":
            continue
        roi = region_of_interest(ds=structure_set,roi_id=roiname)
        mask = roi.get_mask(ct_orig,corrected=False)
        aroi = itk.GetArrayViewFromImage(mask)>0
        logger.debug("applying material override HU={} inside ROI '{}' on {} voxels".format(int(huval),roiname,np.sum(aroi)))
        logger.debug("aroi is contiguous: {}".format("YES" if aroi.flags.contiguous else "NO"))
        if not aroi.flags.contiguous:
            aroi=np.ascontiguousarray(aroi)
            logger.debug("NOW aroi is contiguous: {}".format("YES" if aroi.flags.contiguous else "NO"))
        logger.debug("act_orig is contiguous: {}".format("YES" if act_orig.flags.contiguous else "NO"))
        if not act_orig.flags.contiguous:
            act_orig=np.ascontiguousarray(act_orig)
            logger.debug("NOW act_orig is contiguous: {}".format("YES" if act_orig.flags.contiguous else "NO"))
        act_orig[aroi] = huval
        n_override += np.sum(aroi)
        n_rois += 1
    logger.debug("converting ct array back to ITK image")
    ct_hu_overrides = itk_image_from_array(act_orig)
    logger.debug("copying information")
    ct_hu_overrides.CopyInformation(ct_orig)
    logger.debug("done")
    update_user_logs(user_logs,"PREPROCESSING MATERIAL OVERRIDE COMPLETE",section="CT",
            changes={"material override [Nvoxels,Nrois]":f"{n_override},{n_rois}"})

    # step 3: apply padding with dose padding HU (typically water)
    current_action="padding CT image (if dose image is not contained in it)"
    logger.debug("getting bounding box")
    bb_ct_hu_overrides = bounding_box(img=ct_hu_overrides)
    bb_dose = bounding_box(xyz=np.stack((dose_grid_center-0.5*dose_grid_size,dose_grid_center+0.5*dose_grid_size)))
    if not bb_dose in bb_ct_hu_overrides:
        logger.debug("dose matrix IS NOT contained in original CT! adding dose padding")
        bb_dose_padding = bounding_box(bb=bb_ct_hu_overrides)
        bb_dose_padding.merge(bb_dose)
        #ibbmin = np.array(ct_hu_overrides.TransformPhysicalPointToIndex(bb_dose_padding.mincorner))
        #ibbmax = np.array(ct_hu_overrides.TransformPhysicalPointToIndex(bb_dose_padding.maxcorner))+1
        ibbmin,ibbmax = bb_dose_padding.indices_in_image(ct_hu_overrides)
        ct_padded = crop_and_pad_image(ct_hu_overrides,ibbmin,ibbmax,hu_dosepad)
        bb_ct_padded = bounding_box(img=ct_padded) # this might actually be slightly larger than bb_dose_padding
        logger.debug("finished padding CT to contain the dose matrix")
    else:
        logger.debug("dose matrix IS contained in original CT, no padding needed")
        ct_padded = ct_hu_overrides
        bb_ct_padded = bb_ct_hu_overrides
    logger.debug("got bounding box")

    # step 4: apply cropping/padding with out-of-external padding HU (typically air)
    current_action="cropping/padding CT image"
    logger.debug("starting crop and pad")
    #ibbmin = np.array(ct_padded.TransformPhysicalPointToIndex(ct_bb.mincorner+0.01))
    #ibbmax = np.array(ct_padded.TransformPhysicalPointToIndex(ct_bb.maxcorner-0.01))+1
    ibbmin,ibbmax = ct_bb.indices_in_image(ct_padded)
    logger.debug("size of padded CT: {}, going to crop-and-pad from index {} to index {}".format(np.array(ct_padded.GetLargestPossibleRegion().GetSize()),ibbmin,ibbmax))
    ct_overrides = crop_and_pad_image(ct_padded,ibbmin,ibbmax,hu_air)
    logger.debug("finished crop and pad")
    update_user_logs(user_logs,"PREPROCESSING CROPPING/PADDING COMPLETE")


    # step 5: produce external dose mask (to enable the "set all dose outside of exernal equal to zero").
    current_action="creating dose mask"
    logger.debug("going to create dose mask for performing 'no dose outside of external' filter")
    dose_grid_dummy = itk_image_from_array(np.zeros(dose_grid_nvoxels[::-1],dtype=np.float32))
    spacing = dose_grid_size / dose_grid_nvoxels
    dose_grid_dummy.SetOrigin(dose_grid_center-0.5*dose_grid_size+0.5*spacing)
    dose_grid_dummy.SetSpacing(spacing)
    dose_grid_mask=ext_roi.get_mask(dose_grid_dummy,corrected=False)
    itk.imwrite(dose_grid_mask,mhd_dose_grid_mask)
    logger.debug("finished creationg of dose mask for performing 'no dose outside of external' filter")
    update_user_logs(user_logs,"PREPROCESSING DOSE MASK COMPLETE")


    # step 6: write output
    current_action="writing preprocessed CT image"
    logger.debug("writing cropped, padded and overridden CT image to {}".format(mhd_overrides))
    itk.imwrite(ct_overrides,mhd_overrides)
    mhd_mass=mhd_overrides.replace(".mhd","_mass.mhd")
    current_action="creating mass file"
    mass_image = create_mass_image(ct_overrides,hlut_path,overrides=HU_override_density)
    logger.debug("writing corresponding mass image to {}".format(mhd_mass))
    current_action="writing mass file"
    itk.imwrite(mass_image,mhd_mass)
    update_user_logs(user_logs,"PREPROCESSING COMPLETE")

if __name__ == '__main__':
    parser=configparser.RawConfigParser()
    parser.optionxform = lambda option : option
    logger.debug('going to read CT and dose grid specs from preprocesssing config file')
    try:
        with open("preprocessor.cfg","r") as fp:
            parser.read_file(fp)
        user_logs            = parser['user logs file']['path']
        dicom                = parser['dicom']
        HUoverride           = dict([(k,np.int16(v)) for k,v in parser['HUoverride'].items()])
        HU_override_density  = dict([(int(k),float(v)) for k,v in parser['density'].items() if k != "hlut_path" ])
        hlut_path            = parser['density']["hlut_path"]
        mhd_files            = parser['mhd files']
        dose_grid            = parser['dose grid']
        ct_bounding_box      = parser['ct bounding box']
        dose_grid_center     = np.array([float(v) for v in dose_grid['dose grid center'].split()])
        dose_grid_size       = np.array([float(v) for v in dose_grid['dose grid size'].split()])
        dose_grid_nvoxels    = np.array([int(v) for v in dose_grid['dose grid nvoxels'].split()])
        #mhd_resized          = str(mhd_files.get('mhd resized'))        # mandatory
        mhd_orig_ct          = str(mhd_files.get('mhd with original ct'))# mandatory
        mhd_overrides        = str(mhd_files.get('mhd with overrides'))  # mandatory
        mhd_mass             = mhd_overrides.replace(".mhd","_mass.mhd")
        mhd_dose_grid_mask   = str(mhd_files.get('mhd dose grid mask'))  # mandatory
        ct_bb_min            = [float(v) for v in ct_bounding_box["min corner"].split()]
        ct_bb_max            = [float(v) for v in ct_bounding_box["max corner"].split()]
        ct_bb                = bounding_box(xyz=[ct_bb_min,ct_bb_max])
        #logger.debug("mhd_resized={}".format(mhd_resized))
        logger.debug("bounding box={}".format(ct_bb))
        logger.debug("mhd_overrides={}".format(mhd_overrides))
        update_user_logs(user_logs,"PREPROCESSING STARTED")
        #sys.exit(0)
        logger.debug('finished parsing config file, now going to do the preprocessing')
        GetMCPatientCTImage(dicom["directory"],
                            dicom["RSfile"],
                            dicom["CTuid"],
                            HUoverride,
                            HU_override_density,
                            hlut_path,
                            #mhd_resized,
                            mhd_orig_ct,
                            mhd_overrides,
                            ct_bb,
                            dose_grid_center,
                            dose_grid_size,
                            dose_grid_nvoxels,
                            mhd_dose_grid_mask)
        update_user_logs(user_logs,"PREPROCESSING FINISHED, JOB QUEUED")
    except Exception as e:
        logger.error("something went wrong: {}".format(e))
        update_user_logs(user_logs,f"PREPROCESSING FAILED WHILE {current_action}, check preprocessor.log")
        raise

# vim: set et softtabstop=4 sw=4 smartindent:
