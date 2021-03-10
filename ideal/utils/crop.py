# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import itk
import numpy as np
import logging
logger=logging.getLogger(__name__)

# do not use this directly
def _CropAndPadImageManuallyWithNumpy(input_img,from_index,to_index,hu_value_for_padding):
    """
    We would like to use itk.RegionOfInterestFilter but that filter does recalculate the origin correctly.
    So now we do this manually, through numpy.
    """
    logger.debug("crop and pad manually with numpy")
    aimg=itk.GetArrayViewFromImage(input_img)
    logger.debug("got input image, the array view {} contiguous".format("IS" if aimg.flags.contiguous else "IS NOT"))

    if (from_index>0).all() and (to_index<=np.array(aimg.shape[::-1])).all():
        logger.debug("only cropping, no padding")
        return _CropImageManuallyWithNumpy(input_img,from_index,to_index)

    logger.debug("both cropping and padding")
    atype=aimg.dtype.type
    asize = np.array(aimg.shape)[::-1]
    new_size = to_index-from_index
    logger.debug("old size: {} new size: {}".format(asize,new_size))
    from_old = np.array([ max(i,0)         for i                in from_index ])          # i<0: padding, i>0: cropping; i==0: no change
    to_old   = np.array([ min(s,j)         for j,s              in zip(to_index,asize) ]) # j>s: padding, j<s: cropping; j==s: no change
    from_new = np.array([ max(-i,0)        for i                in from_index ])          # i<0: padding, i>0: cropping; i==0: no change
    to_new   = np.array([ inew+jorig-iorig for inew,iorig,jorig in zip(from_new,from_old,to_old) ])
    logger.debug("from indices in orig: {}".format(from_old))
    logger.debug("to indices in orig: {}".format(to_old))
    logger.debug("from indices in output: {}".format(from_new))
    logger.debug("to indices in output: {}".format(to_new))
    assert((to_new<=new_size).all())
    assert((to_new-from_new==to_old-from_old).all())
    assert((to_new-from_new>0).all())
    anew = np.full(new_size[::-1],fill_value=hu_value_for_padding,dtype=atype)
    logger.debug("new image array {} contiguous".format("IS" if anew.flags.contiguous else "IS NOT"))
    anew[from_new[2]:to_new[2],from_new[1]:to_new[1],from_new[0]:to_new[0]] = \
    aimg[from_old[2]:to_old[2],from_old[1]:to_old[1],from_old[0]:to_old[0]]
    logger.debug("new image array with shape {} is now filled".format(aimg.shape))
    new_img = itk.GetImageFromArray(anew)
    logger.debug("new image created from array, it has size {}".format(new_img.GetLargestPossibleRegion().GetSize()))
    #new_img.CopyInformation(input_img)
    spacing = np.array(input_img.GetSpacing())
    old_origin = np.array(input_img.GetOrigin())
    new_origin = old_origin + (from_index)*spacing
    new_img.SetSpacing(spacing)
    new_img.SetOrigin(new_origin)
    logger.debug("cropping and padding done, manually with numpy")
    return new_img

# do not use this directly
def _CropImageManuallyWithNumpy(input_img,from_index,to_index):
    """
    We would like to use itk.RegionOfInterestImageFilter but that filter does not recalculate the origin correctly.
    So now we do this manually, through numpy.
    """
    aimg=itk.GetArrayViewFromImage(input_img)
    logger.debug("got input image, the array view {} contiguous".format("IS" if aimg.flags.contiguous else "IS NOT"))
    assert((from_index>0).all())
    assert((to_index<=np.array(aimg.shape[::-1])).all())
    logger.debug("going to create new image, forcing slice of old array to be continuous")
    new_img = itk.GetImageFromArray( np.ascontiguousarray(aimg[from_index[2]:to_index[2],
                                                               from_index[1]:to_index[1],
                                                               from_index[0]:to_index[0]]) )
    logger.debug("going to assign spacing and origin to new image")
    #new_img.CopyInformation(input_img)
    spacing = np.array(input_img.GetSpacing())
    old_origin = np.array(input_img.GetOrigin())
    new_origin = old_origin + (from_index)*spacing
    new_img.SetSpacing(spacing)
    new_img.SetOrigin(new_origin)
    logger.debug("cropping done, manually with numpy")
    return new_img

# do not use this directly
def _CropImageWithITK(input_img,from_index,to_index):
    """
    We would like to use itk.RegionOfInterestImageFilter but that filter does not recalculate the origin correctly.
    So now we do this manually, through numpy.
    """
    cropper = itk.RegionOfInterestImageFilter.New(Input=input_img)
    region = cropper.GetRegionOfInterest()
    indx=region.GetIndex()
    size=region.GetSize()
    for j in range(3):
        indx.SetElement(j,int(from_index[j]))
        size.SetElement(j,int(to_index[j]-from_index[j]))
    region.SetIndex(indx)
    region.SetSize(size)
    cropper.SetRegionOfInterest(region)
    cropper.Update()
    return cropper.GetOutput()

# use this
crop_image=_CropImageWithITK
crop_and_pad_image = _CropAndPadImageManuallyWithNumpy

###############################################################################################
# UNIT TESTING
###############################################################################################

import unittest

class test_crop(unittest.TestCase):
    def setUp(self):
        print("hello!")
        self.nxyz = (33,44,55)
        self.nzyx = self.nxyz[::-1]
        self.orig_array = np.random.normal(0.,10.,self.nzyx).astype(np.float32)
        self.orig_image = itk.GetImageFromArray(self.orig_array)
        self.orig_origin = np.array([-111.1,222.2,123.45678])
        self.orig_spacing = np.array([10.10,20.20,30.30])
        self.orig_image.SetOrigin(self.orig_origin)
        self.orig_image.SetSpacing(self.orig_spacing)
    def tearDown(self):
        print("goodbye!")
    def testNormalCrop(self):
        ifrom=np.array([5,6,7])
        ito=np.array([30,40,50])
        cropped_image = _CropImageManuallyWithNumpy(self.orig_image,ifrom,ito)
        cropped_image2 = _CropAndPadImageManuallyWithNumpy(self.orig_image,ifrom,ito,-1024)
        itk_cropped_image = _CropImageWithITK(self.orig_image,ifrom,ito)
        # spacing
        self.assertTrue(np.allclose(np.array(cropped_image.GetSpacing()), self.orig_spacing))
        self.assertTrue(np.allclose(np.array(cropped_image2.GetSpacing()), self.orig_spacing))
        self.assertTrue(np.allclose(np.array(itk_cropped_image.GetSpacing()), self.orig_spacing))
        # origin
        self.assertTrue(np.allclose(np.array(cropped_image.GetOrigin()), self.orig_origin+self.orig_spacing*ifrom))
        self.assertTrue(np.allclose(np.array(cropped_image2.GetOrigin()), self.orig_origin+self.orig_spacing*ifrom))
        self.assertTrue(np.allclose(np.array(itk_cropped_image.GetOrigin()), self.orig_origin+self.orig_spacing*ifrom))
        # size
        new_size = np.array(cropped_image.GetLargestPossibleRegion().GetSize())
        new_size2 = np.array(cropped_image2.GetLargestPossibleRegion().GetSize())
        itk_new_size = np.array(itk_cropped_image.GetLargestPossibleRegion().GetSize())
        exp_size = ito-ifrom
        self.assertTrue((new_size==exp_size).all())
        self.assertTrue((new_size2==exp_size).all())
        self.assertTrue((itk_new_size==exp_size).all())
        # values
        new_array = itk.GetArrayFromImage(cropped_image)
        new_array2 = itk.GetArrayFromImage(cropped_image2)
        itk_array = itk.GetArrayFromImage(itk_cropped_image)
        self.assertTrue((new_array == self.orig_array[ifrom[2]:ito[2],ifrom[1]:ito[1],ifrom[0]:ito[0]]).all())
        self.assertTrue((new_array2 == self.orig_array[ifrom[2]:ito[2],ifrom[1]:ito[1],ifrom[0]:ito[0]]).all())
        self.assertTrue((itk_array == self.orig_array[ifrom[2]:ito[2],ifrom[1]:ito[1],ifrom[0]:ito[0]]).all())

class test_crop_and_pad(unittest.TestCase):
    def setUp(self):
        print("hello!")
        self.nxyz = (33,44,55)
        self.nzyx = self.nxyz[::-1]
        self.orig_array = np.random.normal(0.,10.,self.nzyx).astype(np.float32)
        self.orig_image = itk.GetImageFromArray(self.orig_array)
        self.orig_origin = np.array([-101.1,202.2,103.45078])
        self.orig_spacing = np.array([11.10,21.20,31.30])
        self.orig_image.SetOrigin(self.orig_origin)
        self.orig_image.SetSpacing(self.orig_spacing)
    def tearDown(self):
        print("goodbye!")
    def testNormalCropAndAdd(self):
        # x: pad left, crop right
        # y: crop left, pad right
        # z: pad left, pad right
        # (cropping left & right is already tested in the other test case)
        ifrom=np.array([-5,6,-7])
        ito=np.array([30,80,70])
        cropped_padded_image2 = _CropAndPadImageManuallyWithNumpy(self.orig_image,ifrom,ito,-1024.1024)
        padval=np.float32(-1024.1024)
        # spacing
        self.assertTrue(np.allclose(np.array(cropped_padded_image2.GetSpacing()), self.orig_spacing))
        # origin
        self.assertTrue(np.allclose(np.array(cropped_padded_image2.GetOrigin()), self.orig_origin+self.orig_spacing*ifrom))
        # size
        exp_size = ito-ifrom
        new_size2 = np.array(cropped_padded_image2.GetLargestPossibleRegion().GetSize())
        self.assertTrue((new_size2==exp_size).all())
        new_array2 = itk.GetArrayFromImage(cropped_padded_image2)
        self.assertTrue(np.allclose(new_array2[7:62,0:38,5:35],self.orig_array[0:55,6:44,0:30]))
        self.assertTrue(np.allclose(new_array2[:,:,0:5],padval))
        self.assertTrue(np.allclose(new_array2[:,38:74,:],padval))
        self.assertTrue(np.allclose(new_array2[0:7,:,:],padval))
        self.assertTrue(np.allclose(new_array2[62:77,:,:],padval))

# vim: set et softtabstop=4 sw=4 smartindent:
