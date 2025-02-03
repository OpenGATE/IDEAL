# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

# This module was created with help of the pydicom codify utility script.
#from __future__ import unicode_literals  # Only for python2.7 and save_as unicode filename
import sys
assert(sys.version_info.major == 3)
import pydicom
import numpy as np
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence
from pydicom.uid import ImplicitVRLittleEndian
from impl import version as ideal_version
from datetime import datetime
import logging
logger=logging.getLogger(__name__)

def write_dicom_dose_template(rtplan,beamnr,filename,phantom=False):
    """
    Create a template DICOM file for storing a dose distribution corresponding to a given treatment plan.
    * rtplan: a pydicom Dataset object containing a PBS ion beam plan.
    * beamnr: a *string* containing the beam number to be used for referral. Should contain "PLAN" for plan dose files.
    * filename: file path of the desired output DICOM file
    * phantom: boolean flag to indicate whether this is for a CT (False) or phantom dose (True).
    """
    unique_id = pydicom.uid.generate_uid() # create a new unique UID
    plandose = beamnr.upper() == 'PLAN'

    # File meta info data elements
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 200 # maybe 210 for phantoms (can also be RS6 vs RS5)
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.2'
    file_meta.MediaStorageSOPInstanceUID = unique_id
    # file_meta.TransferSyntaxUID = '1.2.840.10008.1.2'
    file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
    #FIXME: we probably need to apply for an official UID here
    file_meta.ImplementationClassUID = '1.2.826.0.1.3680043.1.2.100.6.40.0.76'
    if sys.version_info.major == 3:
        file_meta.ImplementationVersionName = 'DicomObjects.NET'
    else:
        file_meta.ImplementationVersionName = u'DicomObjects.NET'

    # Main data elements
    now = datetime.now()
    ds = Dataset()

    ds.AccessionNumber = ''
    ds.Manufacturer = 'ACMIT Gmbh and EBG MedAustron GmbH and Medical University of Vienna' ###
    ds.ManufacturerModelName = "IDEAL"  ###
    ds.SoftwareVersions = ideal_version.tag ###
    ds.PositionReferenceIndicator = ''

    ds.SpecificCharacterSet = 'ISO_IR 100'
    ds.InstanceCreationDate = now.strftime("%Y%m%d") #'20171121' ###
    ds.InstanceCreationTime = now.strftime("%H%M%S") # '120041' ###
    ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.481.2'
    ds.SOPInstanceUID = unique_id # '1.2.752.243.1.1.20180817170901595.1980.23430' ###
    ds.StudyDate = str(rtplan.StudyDate) # '20171103' ###
    ds.StudyTime = str(rtplan.StudyTime) # '153709' ###
    ds.Modality = 'RTDOSE'
    ds.ReferringPhysicianName = str(rtplan.ReferringPhysicianName) # 'Anonymized' ###
    if "SeriesDescription" in rtplan:
        ds.SeriesDescription = str(rtplan.SeriesDescription) ###
    if "OperatorsName" in rtplan:
        ds.OperatorsName = str(rtplan.OperatorsName) ###
    if "PatientName" in rtplan:
        ds.PatientName = str(rtplan.PatientName) ###
    if "PatientID" in rtplan:
        ds.PatientID = str(rtplan.PatientID) ###
    if "PatientBirthDate" in rtplan:
        ds.PatientBirthDate = str(rtplan.PatientBirthDate) ###
    if "PatientSex" in rtplan:
        ds.PatientSex = str(rtplan.PatientSex) ###
    ds.SliceThickness = str("1") ### overwrite by postprocessing
    ds.StudyInstanceUID = rtplan.StudyInstanceUID.strip() ###
    ds.SeriesInstanceUID = pydicom.uid.generate_uid() #rtplan.SeriesInstanceUID.strip() ###
    if hasattr(rtplan,"StudyDescription"):
        ### absent for phantom/commissioning
        ds.StudyDescription = str(rtplan.StudyDescription)
    if hasattr(rtplan,"PatientIdentityRemoved"):
        ds.PatientIdentityRemoved = str(rtplan.PatientIdentityRemoved) ### absent for phantom/commsissioning plans
        ds.DeidentificationMethod = str(rtplan.DeidentificationMethod) ### absent for phantom/commsissioning plans
    if hasattr(rtplan,"StudyID"):
        ds.StudyID = rtplan.StudyID ###
    if hasattr(rtplan,"SeriesNumber"):
        ds.SeriesNumber = rtplan.SeriesNumber ###
    if phantom:
        ds.InstanceNumber = 0 # str("0") ### only for phantom/commissioning
        ds.PatientOrientation = str('') ### only for phantom/commissioning
    ds.ImagePositionPatient = [str(-999.999), str(-999.999), str(-999.999)] ### overwrite by postprocessing
    ds.ImageOrientationPatient = [str(float(c)) for c in '100010']
    ds.FrameOfReferenceUID = rtplan.FrameOfReferenceUID.strip() ###
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = 'MONOCHROME2'
    ds.NumberOfFrames = str(9) ### overwrite by postprocessing
    ds.FrameIncrementPointer = pydicom.tag.BaseTag(0x3004000c) # That is the tag corresponding to the "GridFrameOffsetVector". All RS dose files do it like this.
    ds.Rows = 9 ### overwrite by postprocessing
    ds.Columns = 9 ### overwrite by postprocessing
    ds.PixelSpacing = [str('9'), str('9')] ### overwrite by postprocessing
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.DoseUnits = 'GY'
    ds.DoseType = 'PHYSICAL' ### TODO: for RBE we may want "effective"
    ds.DoseSummationType = 'PLAN' if plandose else 'BEAM' ### beam/plan difference
    ds.GridFrameOffsetVector = [str(c) for c in range(9) ]
    ds.DoseGridScaling = 0.999999 ### overwrite by postprocessing

    # Referenced RT Plan Sequence
    refd_rt_plan_sequence = Sequence()
    ds.ReferencedRTPlanSequence = refd_rt_plan_sequence

    # Referenced RT Plan Sequence: Referenced RT Plan 1
    refd_rt_plan1 = Dataset()
    refd_rt_plan1.ReferencedSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.8' ### different for phantoms??? check
    refd_rt_plan1.ReferencedSOPInstanceUID = rtplan.SOPInstanceUID.strip()

    if not plandose:
        # Referenced Fraction Group Sequence ## ONLY FOR BEAMS
        refd_frxn_gp_sequence = Sequence() ## ONLY FOR BEAMS
        refd_rt_plan1.ReferencedFractionGroupSequence = refd_frxn_gp_sequence ## ONLY FOR BEAMS

        # Referenced Fraction Group Sequence: Referenced Fraction Group 1 ## ONLY FOR BEAMS
        refd_frxn_gp1 = Dataset() ## ONLY FOR BEAMS

        # Referenced Beam Sequence ## ONLY FOR BEAMS
        refd_beam_sequence = Sequence() ## ONLY FOR BEAMS
        refd_frxn_gp1.ReferencedBeamSequence = refd_beam_sequence ## ONLY FOR BEAMS

        # Referenced Beam Sequence: Referenced Beam 1 ## ONLY FOR BEAMS
        refd_beam1 = Dataset() ## ONLY FOR BEAMS
        refd_beam1.ReferencedBeamNumber = beamnr ### ## ONLY FOR BEAMS
        refd_beam_sequence.append(refd_beam1) ## ONLY FOR BEAMS

        refd_frac_grp_nr = None
        for f in rtplan.FractionGroupSequence:
            fnr = str(f.FractionGroupNumber)
            if refd_frac_grp_nr is None:
                # In case the beam number is not actually found, this is a bit of a lie.
                # But we have to survive somehow when the user feeds us illegal DICOM plan files from PDM.
                refd_frac_grp_nr = fnr
            for refb in f.ReferencedBeamSequence:
                if str(refb.ReferencedBeamNumber) == str(beamnr):
                    refd_frac_grp_nr = fnr
                    break
        refd_frxn_gp1.ReferencedFractionGroupNumber = refd_frac_grp_nr ## ONLY FOR BEAMS
        refd_frxn_gp_sequence.append(refd_frxn_gp1) ## ONLY FOR BEAMS
    refd_rt_plan_sequence.append(refd_rt_plan1)

    ds.PixelData = np.ones((9,9,9),dtype=np.uint16).tobytes() ### overwrite by postprocessing

    ds.file_meta = file_meta
    #ds.is_implicit_VR = True
    #ds.is_little_endian = True
    ds.save_as(filename, enforce_file_format=True,implicit_vr=True, little_endian = True) ###

# vim: set et softtabstop=4 sw=4 smartindent:
