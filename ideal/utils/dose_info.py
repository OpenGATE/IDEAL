# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import logging
import pydicom
import itk
import numpy as np
import os
logger=logging.getLogger(__name__)

class dose_info(object):
    def __init__(self,rd,rdfp):
        self._rd = rd
        self._rdfp = rdfp
        try:
            # beam dose
            self._beamnr = str(self._rd. ReferencedRTPlanSequence[0].ReferencedFractionGroupSequence[0].ReferencedBeamSequence[0].ReferencedBeamNumber)
        except:
            # plan dose
            self._beamnr = None
        assert(self._rd.pixel_array.shape == (int(self._rd.NumberOfFrames),int(self._rd.Rows),int(self._rd.Columns)))
    @property
    def filepath(self):
        return self._rdfp
    @property
    def image(self):
        scaling = float(self._rd.DoseGridScaling)
        img = itk.GetImageFromArray(self._rd.pixel_array*scaling)
        img.SetOrigin(self.origin)
        img.SetSpacing(self.spacing)
        return img
    @property
    def ref_uid(self):
        return str(self._rd.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID)
    @property
    def spacing(self):
        return np.array([float(v) for v in self._rd.PixelSpacing[::-1]+[self._rd.SliceThickness]])
    @property
    def nvoxels(self):
        return np.array(self._rd.pixel_array.shape[::-1])
    @property
    def origin(self):
        return np.array([float(v) for v in self._rd.ImagePositionPatient])
    @property
    def is_physical(self):
        return (str(self._rd.DoseType).upper() == 'PHYSICAL')
    @property
    def is_effective(self):
        return (str(self._rd.DoseType).upper() == 'EFFECTIVE')
    @property
    def is_beam_dose(self):
        return (self._beamnr is not None)
    @property
    def is_plan_dose(self):
        return (self._beamnr is None)
    @property
    def refd_beam_number(self):
        return self._beamnr
    @staticmethod
    def get_dose_files(rd_data,only_physical=False):
        doses = dict()
        for d in rd_data:
            dcm = d.data
            drefrtp0=dcm.ReferencedRTPlanSequence[0]
            uid = str(drefrtp0.ReferencedSOPInstanceUID)
            dose_type = str(dcm.DoseType).upper()
            dose_sum_type = str(dcm.DoseSummationType)
            physical=True
            beamnr=None
            if dose_sum_type.upper() == 'PLAN':
                # the physical or effective plan dose file (hopefully)
                label = 'PLAN'
                beamdose=False
            else:
                # a beam dose file (hopefully)
                label = str(drefrtp0.ReferencedFractionGroupSequence[0].ReferencedBeamSequence[0].ReferencedBeamNumber)
                beamnr=label
                logger.debug("BEAM DOSE FILE FOR {}".format(label))
            if dose_type == 'EFFECTIVE':
                logger.debug("got EFFECTIVE=RBE dose for {}".format(label))
                label += '_RBE'
                physical=False
            elif dose_type == 'PHYSICAL':
                logger.debug("got PHYSICAL dose for {}".format(label))
            else:
                raise RuntimeError("unknown dose type {} for {} dose, UID={}".format(dose_type,label,uid))
            if label in doses.keys():
                # oopsie!
                raise RuntimeError("multiple dose files for beamnr/plan={} and UID={}".format(label,uid))
            if dose_type == 'PHYSICAL' or not only_physical:
                doses[label]=dose_info(dcm,str(d.directory /d.filename))
        # if we arrive here, things are probably fine...
        return doses

# vim: set et softtabstop=4 sw=4 smartindent:
