# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

"""
This module implements the "green" box in the "prepare" diagram included in the
"device description" of IDEAL, the one that says "get beamline model".
"""

################################################################################
# API
################################################################################

class beamline_model:
    bml_cache = dict()
    @property
    def name(self):
        """
        Name or label of the "TreatmentMachine", a.k.a. beamline (e.g. IR2HBL)

        This label is used to find the corresponding calibration data: the
        source properties file, the description and possibly a mac file with
        extra beam line details, if ncessary.
        """
        return self._name
    @property
    def description(self):
        """
        Short description of the beamline (for diagnostic output, UI/GUI ornaments, etc),
        e.g. 'irradiation room 2, horizontal beamline'.
        This label may be used by a UI to assist the user.
        """
        return self._description
    def has_radtype(self,radtype):
        """
        check whether this beamline has information about a particular radtype (typically 'PROTON' or 'ION_6_12_6')
        """
        return (radtype in self._source_properties_files)
    def source_properties_file(self,radtype):
        """
        Path of text file containing the Gate-specific beam model, a text file
        that is usually referred to as the "source properties file".
        """
        return self._source_properties_files[radtype]
    def has_rm_details(self,name=None):
        """
        To check whether we actually know anything about a range modulator for this beamline.
        """
        if name:
            return (str(name) in self._rm_details)
        return bool(self._rm_details)
    def has_rs_details(self,name=None):
        """
        To check whether we actually know anything about a range shifter for this beamline.
        """
        if name:
            return (str(name) in self._rs_details)
        return bool(self._rs_details)
    @property
    def rm_labels(self):
        return self._rm_details.keys()
    @property
    def rs_labels(self):
        return self._rs_details.keys()
    def rm_details_mac_file(self,name=None):
        """
        Path of Gate mac file with range modulator (aka ripple filter) details for this beamline (geometry and material)

        This mac file should always exist but it will only be used for beams
        that are indeed planned with a range shifter.  It is assumed that each
        beam line has only one standard range shifter device.
        """
        if name:
            return self._rm_details[name]
        elif len(self._rm_details)==1:
            return self._rm_details.values()[0]
        else:
            raise KeyError("range modulator requested, no name given, several available")
    def rs_details_mac_file(self,name=None):
        """
        Path of Gate mac file with range shifter details for this beamline (geometry and material)

        This mac file should always exist but it will only be used for beams
        that are indeed planned with a range shifter.  It is assumed that each
        beam line has only one standard range shifter device.
        """
        if name:
            return self._rs_details[name]
        elif len(self._rs_details)==1:
            return self._rs_details.values()[0]
        else:
            raise KeyError("range shifter requested, no name given, several available")
    @property
    def beamline_details_mac_file(self):
        """
        Path of Gate mac file with fixed beamline details
        ("fixed" means: excluding plan/patient dependent passive elements such as the range shifter)

        (Empty string if no such details are necessary.)
        
        For very elaborate beam models you can provide more mac files in the
        same directory or subdirectories (these will be listed in the "aux"
        datamember of this class). Make sure that those extra mac files will
        be "executed" in correct order from this main beamline mac file.
        
        NOTE that this is the path of the 'master' file. It will be copied into
        the "mac" subdirectory of the Gate job working directory.
        """
        return self._beamline_details_mac_file
    @property
    def common_aux(self):
        """
        Paths of Gate mac file or directories with even more extra details that
        are not beamline specific ("common auxiliary").

        (Empty list if no such details are necessary.)

        NOTE that this are the paths of the 'master' files/directories. They
        will be copied into the "data" subdirectory of the Gate job working
        directory. This includes any mac files that are 'executed' from within
        the main 'beamline_details_mac_file'.
        """
        return self._common_aux
    @property
    def beamline_details_aux(self):
        """
        Paths of Gate mac file or directories with even more extra details.

        (Empty list if no such details are necessary.)
        
        For e.g. beam model that is specified at the entrance of a nozzle
        rather than the exit.  Note that other passive elements (such as a
        range shifter, ridge filter, bolus material, etc), are dealt with
        separately.
        Mac files in this extra collection should be 'executed' from the main
        beamline details mac file, they will *not* be included in the top level
        Gate mac file.

        NOTE that this are the paths of the 'master' files/directories. They
        will be copied into the "data" subdirectory of the Gate job working
        directory. This includes any mac files that are 'executed' from within
        the main 'beamline_details_mac_file'.
        """
        return self._beamline_details_aux
    @staticmethod
    def get_beamline_model_data(bml_name,beamlines_dir):
        if bml_name in beamline_model.bml_cache:
            return beamline_model.bml_cache[bml_name]
        bml = beamline_model_impl(bml_name,beamlines_dir)
        beamline_model.bml_cache[bml_name] = bml
        return bml

################################################################################
# IMPLEMENTATION
################################################################################

import os
import pydicom
import logging
from glob import glob
logger=logging.getLogger(__name__)


class beamline_model_impl(beamline_model):
    def __init__(self,bml_name,beamlines_dir):
        self._rs_details = dict()
        self._rm_details = dict()
        self._common_aux = list()
        self._source_properties_files = dict()
        self._beamline_details_mac_file = ''
        self._beamline_details_aux = list()
        self._name = bml_name
        self._description = "No description available"
        common_dir = os.path.join(beamlines_dir,"common")
        beamline_dir = os.path.join(beamlines_dir,self.name)
        nbml=len(bml_name)
        if os.path.isdir(common_dir):
            for f in os.listdir(common_dir):
                fpath = os.path.join(common_dir,f)
                if f[:3] == "rs_" and f[-12:] == "_details.mac":
                    rsname = f[3:-12]
                    self._rs_details[rsname] = fpath
                    logger.debug("found mac file for range shifter named '{}'".format(rsname))
                elif f[:3] == "rm_" and f[-12:] == "_details.mac":
                    rmname = f[3:-12]
                    self._rm_details[rmname] = fpath
                    logger.debug("found mac file for range modulator named '{}'".format(rmname))
                else:
                    if f[:nbml] == bml_name:
                        logger.error('found *beamline-specific* config file {} in *common* directory {}'.format(f,common_dir))
                        raise RuntimeError('SYSCONFIG ERROR found *beamline-specific* config file {} in *common* directory {}'.format(f,common_dir))
                    self._common_aux.append(fpath)
        if os.path.isdir(beamline_dir):
            descr = os.path.join(beamline_dir,"description.txt")
            if os.path.exists(descr):
                with open(os.path.join(descr)) as fdescr:
                    self._description = '\n'.join([line.strip() for line in fdescr.readlines()])
            for f in os.listdir(beamline_dir):
                fpath = os.path.join(beamline_dir,f)
                if f == bml_name+"_beamline_details.mac":
                    self._beamline_details_mac_file = fpath
                elif f[:4+nbml] == bml_name+"_rs_" and f[-12:] == "_details.mac":
                    rsname = f[nbml+4:-12]
                    if rsname in self._rs_details.keys():
                        logger.debug("beamline-specifi mac file for range shifter named '{}' overrides the common mac file for this range shifter.".format(rsname))
                    self._rs_details[rsname] = fpath
                    logger.debug("found mac file for range shifter named '{}'".format(rsname))
                elif f[:4+nbml] == bml_name+"_rm_" and f[-12:] == "_details.mac":
                    rmname = f[nbml+4:-12]
                    if rmname in self._rs_details.keys():
                        logger.debug("beamline-specifi mac file for range modulator named '{}' overrides the common mac file for this range shifter.".format(rmname))
                    self._rm_details[rmname] = fpath
                    logger.debug("found mac file for range modulator named '{}'".format(rmname))
                elif f[:1+nbml] == bml_name+"_" and f[-22:] == "_source_properties.txt":
                    radtype = f[nbml+1:-22]
                    self._source_properties_files[radtype] = fpath
                    logger.debug("found source properties file for radiation type '{}'".format(radtype))
                    if radtype not in ['PROTON','ION_6_12_6']:
                        logger.warn("funny source properties file {}, unknown rad type '{}'".format(f,radtype))
                else:
                    if f[:nbml] != bml_name:
                        logger.error('found *beamline-specific* config file {} for beamline {} without required beamline name prefix.'.format(f,bml_name))
                        raise RuntimeError('SYSCONFIG ERROR found *beamline-specific* config file {} for beamline {} without required beamline name prefix.'.format(f,common_dir))
                    self._beamline_details_aux.append(fpath)
            if not bool(self._beamline_details_mac_file):
                if len(self._beamline_details_aux)>0:
                    logger.error("there is no 'beamline_details.mac' file in {}, so the following EXTRA items would be ignored: {}; please fix!".format(
                                    beamline_dir, ",".join([os.path.basename(a) for a in self._beamline_details_aux])))
                    raise LookupError("inconsistent beamline calibration data for beamline {}".format(bml_name))
        else:
            logger.error("beam line model directory for '{}' not found, directory {} does not exist".format(bml_name,beamline_dir))
            raise LookupError("Could not find model data for requested beam line '{}'".format(bml_name))

################################################################################
# UNIT TESTS
################################################################################

import unittest
import sys

class Test_GetBeamLineModel(unittest.TestCase):
    def test_normal_beamline_model(self):
        cave_dir = os.path.dirname(sys.argv[0])
        testcal_dir = "get beamlines dir from syscfg"
        bml = 'IR2HBL'
        beammodel = beamline_model.get_beamline_model_data(bml,testcal_dir)
        self.assertEqual(beammodel.name,'IR2HBL')
        self.assertEqual(beammodel.description,'Irradiation room 2, horizontal beamline (aka MA-BeamModel-IR3.txt by A. Elia)')
        self.assertEqual(beammodel.source_properties_file,os.path.join(testcal_dir,'IR2HBL','IR2HBL_source_properties.txt'))
        self.assertEqual(beammodel.beamline_details_mac_file,os.path.join(testcal_dir,'IR2HBL','IR2HBL_beamline_details.mac'))
        self.assertEqual(beammodel.beamline_rs_details_mac_file,os.path.join(testcal_dir,'IR2HBL','IR2HBL_beamline_rs_details.mac'))
    def test_unavailable_beamline_model(self):
        cave_dir = os.path.dirname(sys.argv[0])
        testcal_dir = os.path.join(cave_dir,'shadows','test_calibration')
        bml = 'FOOBAR'
        logger.info('Now there should follow an error message about an unknown beamline named "FOOBAR".')
        with self.assertRaises(LookupError,msg="for an un-modeled treatment machine / beamline, a LookupError should be raised"):
            tmp = beamline_model.get_beamline_model_data(bml,testcal_dir)

# vim: set et softtabstop=4 sw=4 smartindent:
