#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 14:25:29 2025

@author: fava
"""

import itk

def itk_image_from_array(arr, view=True):
    """
    When the input numpy array is of shape [1,1,x], the conversion to itk image fails:
    the output image size is with the wrong dimensions.
    We thus 'patch' itk.image_view_from_array to correct the size.

    Not fully sure if this is the way to go.
    """
    if view is True:
        image = itk.image_view_from_array(arr)
    else:
        image = itk.image_from_array(arr)
    if len(arr.shape) == 3 and arr.shape[1] == arr.shape[2] == 1:
        new_region = itk.ImageRegion[3]()
        new_region.SetSize([1, 1, arr.shape[0]])
        image.SetRegions(new_region)
        image.Update()
    return image