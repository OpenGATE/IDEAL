# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

"""
This module provides a simple function that converts an ITK image with (short int) HU values
into an float32 image with density values.
"""

import numpy as np
import itk
import logging
from utils.itk_image_utils import itk_image_from_array
logger=logging.getLogger(__name__)

def create_mass_image(ct,hlut_path,overrides=dict()):
    """
    This function creates a mass image based on the HU values in a ct image, a
    Hounsfield-to-density lookup table and (optionally) a dictionary of
    override densities for specific HU values.

    If the HU-to-density lookup table has 2 columns, it is interpreted as a
    density curve that needs to be interpolated for the intermediate HU values.
    If the HU-to-density lookup table has 3 columns, then it is interpreted as
    a step-wise density table, with a constant density within each successive
    interval (no interpolation).
    """
    HLUT = np.loadtxt(hlut_path)
    logger.debug("table shape is {}".format(HLUT.shape))
    logger.debug("table data type is {}".format(HLUT.dtype))
    assert len(HLUT.shape)==2, "HU lookup table has wrong dimension (should be 2D)"
    assert HLUT.shape[1]//2==1, "HU lookup table has wrong number of columns (should be 2 or 3)"
    act=itk.GetArrayFromImage(ct)
    amass=np.zeros(act.shape,dtype=np.float32)
    done=np.zeros(act.shape,dtype=bool)
    if HLUT.shape[1]==2:
        HU=HLUT[:,0]
        rho=HLUT[:,1]
        assert (np.diff(HU)>0).all(), "HU table is not monotonic in HU"
        assert (rho>=0).all(), "all densities in HU lookup table should be non-negative"
        m=act<HU[0]
        amass[m]=rho[0]
        done|=m
        m=act>=HU[-1]
        amass[m]=rho[-1]
        done|=m
        for hu0,hu1,rho0,rho1 in zip(HU[:-1],HU[1:],rho[:-1],rho[1:]):
            m=(act>=hu0)*(act<hu1)
            assert not (m*done).any(), "programming error"
            amass[m]=rho0
            amass[m]+=(act[m]-hu0)*(rho1-rho0)/(hu1-hu0)
            done|=m
        assert done.all(), "programming error"
    else:
        n=HLUT.shape[0]
        HUfrom=HLUT[:,0]
        HUtill=HLUT[:,1]
        rho=HLUT[:,2]
        assert (HUfrom<HUtill).all(),"inconsistent HU interval"
        assert (rho>0).all(),"rho should be positive"
        if n>1:
            assert (HUfrom[1:]==HUtill[:-1]).all(),"HU intervals should be contiguous"
        m=(act>=HUfrom[0])
        assert m.all(),"Some HU values in the CT are less than the minimum in the HU table."
        for hu0,hu1,rho0 in zip(HUfrom,HUtill,rho):
            m=(act>=hu0)*(act<hu1)
            assert not (m*done).any(), "programming error"
            amass[m]=rho0
            done|=m
    for hu,rho in overrides.items():
        assert hu==int(hu), "overrides must be given for integer HU values"
        assert rho>=0, "override density values must be non-negative"
        m=(act==hu)
        amass[m]=rho
        done|=m
    if not done.all():
        logger.warn("not all voxels got a mass, some voxels are 0")
    mass=itk_image_from_array(amass)
    mass.CopyInformation(ct)
    return mass

################################################################################
# UNIT TESTS                                                                   #
################################################################################

import unittest
import os

class mass_image_test(unittest.TestCase):
    def test_normal_use(self):
        ct=itk_image_from_array(np.int16(np.arange(4*5*6).reshape(4,5,6)-10))
        hlut=np.array([[0.,0.],[50.,0.1],[100.,1.]])
        hlut_fname=".mass_image_test.{}.txt".format(os.getpid())
        np.savetxt(hlut_fname,hlut)
        overrides=dict([(hu,1.2345) for hu in range(100,110)])
        mass=create_mass_image(ct,hlut_fname,overrides)
        amass=itk.GetArrayFromImage(mass).flat[:]
        self.assertTrue(np.allclose(amass[:10],0.))
        self.assertTrue(np.allclose(amass[110:],1.2345))
        self.assertTrue(np.allclose(amass[10:60],np.arange(50)*0.1/50))
        self.assertTrue(np.allclose(amass[60:110],np.arange(50)*0.9/50+0.1))

# vim: set et softtabstop=4 sw=4 smartindent:
