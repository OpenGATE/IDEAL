#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 15:30:19 2024

@author: fava
"""
import pydicom
import itk
from collections import namedtuple
import os
from pathlib import Path
import logging
import impl.IDEAL_dictionary as ideal_tags

logger=logging.getLogger(__name__)

Dicom = namedtuple('Dicom', 'directory filename type data')

                   
class dicom_files:
    def __init__(self,rp_fpath):
        if not os.path.exists(rp_fpath):
            logger.error(f"got non-existing RP DICOM file path {rp_fpath}")
        if not rp_fpath.endswith('dcm'):
            logger.error(f'Invalid extension for RT plan file. File path: {rp_fpath}')
            raise ValueError(f'Rt plan filepath provided is not a DICOM file! Provided path: {rp_fpath}')
            
        self.rp_fpath = Path(rp_fpath)
        self.dicom_dir = self.rp_fpath.parent
        
        # read RP file, check it, if good store it
        logger.debug(f'Trying to read dicom RT plan file {self.rp_fpath.name}')
        rp_data = pydicom.dcmread(rp_fpath)
        self.rp_data = Dicom(self.dicom_dir,self.rp_fpath.name,get_dcm_type(rp_data),rp_data)
        logger.debug('RT plan file read successfully')
        
        # extract SOPInstanceUID -> identifies all files
        self.uid = self.rp_data.data.SOPInstanceUID 
        self.ss_ref_uid = self.rp_data.data.ReferencedStructureSetSequence[0].ReferencedSOPInstanceUID
        
        # read all dicom in rp folder, organize them by type
        self.all_dcm = read_all_dcm(self.dicom_dir)
        
        # find RD files relative to the input plan, check them, if good store them
        self.rd_data = self.get_dose_data(rpuid=self.uid)
        
        # find RS file relative to the input plan, check it, if good store it
        self.rs_data = self.get_structures_data(ss_ref_uid=self.ss_ref_uid)
        self.ct_series_uid = self.rs_data.data.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].SeriesInstanceUID
                       
        # find CT files relative to the input plan, check them, if good store them
        self.ct_slices = self.get_ct_data(ct_series_uid= self.ct_series_uid)
        
    def get_structures_data(self,ss_ref_uid=None):
        logger.debug("going to find structure set files")
        rs_candidates = [d for d in self.all_dcm if d.type == 'RT Structure Set Storage']
        if ss_ref_uid:
            logger.debug(f"going to try to find the file with structure set with UID '{ss_ref_uid}'")
            rs_candidates = [d for d in rs_candidates if d.data.SOPInstanceUID == ss_ref_uid]
        if len(rs_candidates) == 0:
            logger.error('No structure set found!')
            raise IOError('No dicom structure set file was found in the plan directory')
        if len(rs_candidates) > 1:
            logger.warning('Weird, only one set of structure is expected')
            raise IOError('Multiple structure set dicom files found')
        return rs_candidates[0]

    def get_ct_data(self,ct_series_uid=None):
        logger.debug("going to find CT files")
        ct_slices = [d for d in self.all_dcm if d.type == 'CT Image Storage']
        if ct_series_uid:
            logger.debug(f"looking for file with series UID '{ct_series_uid}'")
            ct_slices = [d for d in ct_slices if d.data.SeriesInstanceUID == ct_series_uid]
            if len(ct_slices) == 0:
                logger.error(f"No CT file found for series UID {ct_series_uid}")
        cd_data = Dicom(ct_slices[0].directory,ct_slices[0].filename,'CT Image Storage',[ct.data for ct in ct_slices])
        return cd_data
    
    def get_dose_data(self, rpuid=None):
        logger.debug(f"going to find RD dose files in directory {self.all_dcm[0].directory}")
        logger.debug("for UID={} PLAN".format(rpuid if rpuid else "any/all"))
        all_doses = [d for d in self.all_dcm if d.type == 'RT Dose Storage']
        if rpuid:
            all_doses = [d for d in all_doses if d.data.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID == rpuid]
            if len(all_doses) == 0:
                logger.error(f"No dose file found for RP uid {rpuid}")
                    
        return all_doses
    
        
    def verify_all_dicom(self):
        ok = True 
        missing_keys = {}

        ok_rp, mk = check_RP(self.rp_data.data)
        ok = ok and ok_rp
        if mk:
            missing_keys['dicomRtPlan'] = mk
        
        ok_rs, mk = check_RS(self.rs_data.data)
        ok = ok and ok_rs
        if mk:
            missing_keys['dicomStructureSet'] = mk

        for rd in self.rd_data:
            ok_rd, mk = check_RD(rd.data)
            ok = ok and ok_rd
            if mk:
                missing_keys['dicomRDose'] = mk
                break
        i = 0   

        for ct in self.ct_slices.data:
            i+=1
            #print("CT file nr ",i)
            ok_ct, mk = check_CT(ct)
            ok = ok and ok_ct
            if mk:
                missing_keys['dicomCTs'] = mk
                
        return ok, missing_keys   
    
def get_dcm_type(dcm):
    if 'SOPClassUID' not in dcm:
        raise IOError("bad DICOM filemissing SOPClassUID")
    return dcm.SOPClassUID.name  

def read_all_dcm(dicom_dir):
    all_dcm = []
    logger.debug('going to read in all dicom files in the RT plan file folder')
    for path in dicom_dir.iterdir():
        if str(path).endswith('dcm'):
            logger.debug(f"Trying to read file {str(path)}")
            data = pydicom.dcmread(path)
            type_ = get_dcm_type(data)
            all_dcm.append(Dicom(dicom_dir,path.name,type_,data))
        else:
             logger.debug(f"Found file with no .dcm suffix: {str(path)}")
    return all_dcm
        
def check_RP(data):
    
	ok = True
	dp = ideal_tags.IDEAL_RP_dictionary()
	
	# keys used by IDEAL from RP file (maybe keys are enought?)
	genericTags = dp.RPGeneral
	ionBeamTags = dp.IonBeamSequence
	doseSeqTags = dp.DoseReferenceSequence
	refStructTags = dp.ReferencedStructureSetSequence
	fractionTags = dp.FractionGroupSequence
	icpTags = dp.IonControlPointSequence
	snoutTag = dp.SnoutID
	raShiTag = dp.RangeShifterID
	rangeModTag = dp.RangeModulatorID
	
	## --- Verify that all the tags are present and return an error if some are missing --- ##
		
	missing_keys = []
	
	# check first layer of the hierarchy
	loop_over_tags_level(genericTags, data, missing_keys)

	if "IonBeamSequence" in data:
	
		# check ion beam sequence
		loop_over_tags_level(ionBeamTags, data.IonBeamSequence[0], missing_keys)
		
		# check icp sequence
		if "IonControlPointSequence" not in missing_keys:			
			loop_over_tags_level(icpTags, data.IonBeamSequence[0].IonControlPointSequence[0], missing_keys)
			
		# check snout, rashi and rangMod
		if "NumberOfRangeModulators" not in missing_keys:
			if data.IonBeamSequence[0].NumberOfRangeModulators != 0:
				if "RangeModulatorSequence" not in data.IonBeamSequence[0]:
					missing_keys.append("RangeModulatorSequence")
				elif rangeModTag not in  data.IonBeamSequence[0].RangeModulatorSequence[0]:
					missing_keys.append(rangeModTag)			
			
		if "NumberOfRangeShifters" not in missing_keys:
			if data.IonBeamSequence[0].NumberOfRangeShifters != 0:
				if "RangeShifterSequence" not in data.IonBeamSequence[0]:
					missing_keys.append("RangeShifterSequence")
				elif raShiTag not in  data.IonBeamSequence[0].RangeShifterSequence[0]:
					missing_keys.append(raShiTag)
		
		if "SnoutSequence" not in missing_keys:
			if snoutTag not in  data.IonBeamSequence[0].SnoutSequence[0]:
				missing_keys.append("SnoutID")
			
				
	if "DoseReferenceSequence" in data:
			
		# check dose sequence
		loop_over_tags_level(doseSeqTags, data.DoseReferenceSequence[0], missing_keys)
	
	if "ReferencedStructureSetSequence" in data:
		
		# check reference structure sequence
		loop_over_tags_level(refStructTags, data.ReferencedStructureSetSequence[0], missing_keys)
		
	if "FractionGroupSequence" in data:
		
		# check fractions sequence
		loop_over_tags_level(fractionTags, data.FractionGroupSequence[0], missing_keys)

	if missing_keys:
		ok = False
		#raise ImportError("DICOM RP file not conform. Missing keys: ",missing_keys)
	#else: print("\033[92mRP file ok \033[0m")
	return ok, missing_keys
		
def check_RS(data):
	
    # bool for correctness of file content
	ok = True 
	ds = ideal_tags.IDEAL_RS_dictionary()
	
	# keys and tags used by IDEAL from RS file
	genericTags = ds.RS
	structTags = ds.StructureSetROISequence 
	contourTags = ds.ROIContourSequence 
	observTags = ds.RTROIObservationsSequence
	
	## --- Verify that all the tags are present and return an error if some are missing --- ##
		
	missing_keys = []
	
	# check first layer of the hierarchy
	loop_over_tags_level(genericTags, data, missing_keys)
	
	if "StructureSetROISequence" in data:
	
		# check structure set ROI sequence
		loop_over_tags_level(structTags, data.StructureSetROISequence[0], missing_keys)
		
	if "ROIContourSequence" in data:
	
		# check ROI contour sequence
		loop_over_tags_level(contourTags, data.ROIContourSequence[0], missing_keys)
		
	if "RTROIObservationsSequence" in data:
	
		# check ROI contour sequence
		loop_over_tags_level(observTags, data.RTROIObservationsSequence[0], missing_keys)
		
	if missing_keys:
		ok = False
		#raise ImportError("DICOM RS file not conform. Missing keys: ",missing_keys) 
	#else: print("\033[92mRS file ok \033[0m")
	return ok, missing_keys
	
def check_RD(data):
	ok = True

	dd = ideal_tags.IDEAL_RD_dictionary()
	
	# keys and tags used by IDEAL from RD file
	genericTags = dd.RD 
	planSeqTag = dd.ReferencedRTPlanSequence
	refBeamTag = dd.ReferencedBeamNumber
	
	## --- Verify that all the tags are present and return an error if some are missing --- ##
		
	missing_keys = []
	
	# check first layer of the hierarchy
	loop_over_tags_level(genericTags, data, missing_keys)
	
	# check referenced RT Plan seq 
	if "ReferencedRTPlanSequence" in data:
	
		# check ROI contour sequence
		loop_over_tags_level(planSeqTag, data.ReferencedRTPlanSequence[0], missing_keys)
		
		if "DoseSummationType" in data:
			if data.DoseSummationType != "PLAN":
				# check also ReferencedFractionGroupSequence
				if "ReferencedFractionGroupSequence" not in data.ReferencedRTPlanSequence[0]:
					missing_keys.append("ReferencedFractionGroupSequence")
				elif refBeamTag not in data.ReferencedRTPlanSequence[0].ReferencedFractionGroupSequence[0].ReferencedBeamSequence[0]:
					missing_keys.append("ReferencedBeamNumber under ReferencedRTPlanSequence/ReferencedFractionGroupSequence/ReferencedBeamSequence")
		
	if missing_keys:
		ok = False
		#raise ImportError("DICOM RD file not conform. Missing keys: ",missing_keys) 
	#else: print("\033[92mRD file ok \033[0m")
	return ok, missing_keys

def check_CT(data):
	ok = True

	dct = ideal_tags.IDEAL_CT_dictionary()
	
	# keys and tags used by IDEAL from CT file
	genericTags = dct.CT
	
	## --- Verify that all the tags are present and return an error if some are missing --- ##
	missing_keys = []
	
	# check first layer of the hierarchy
	loop_over_tags_level(genericTags, data, missing_keys)
	
	if missing_keys:
		ok = False
		#raise ImportError("DICOM CT file not conform. Missing keys: ",missing_keys) 
	#else: print("\033[92mCT file ok \033[0m")
	return ok, missing_keys
	
def loop_over_tags_level(tags, data, missing_keys):
	
	for key in tags:
		
		if (key not in data) or (data[key].value) is None:
			
			missing_keys.append(key)
		
	#return missing_keys

# function used in IDEAL code to check tags. Alternative to my approach.

def sequence_check(obj,attr,nmin=1,nmax=0,name="object"):
    print("checking that {} has attribute {}".format(name,attr))
    assert(hasattr(obj,attr))
    seq=getattr(obj,attr)
    print("{} has length {}, will check if it >={} and <={}".format(name,len(seq),nmin,nmax))
    assert(len(seq)>=nmin)
    assert(nmax==0 or len(seq)<=nmax)
    
if __name__ == '__main__':
    rp_fpath = "/home/ideal/0_Data/02_ref_RTPlans/01_ref_Plans_CT_RTpl_RTs_RTd/02_2DOptics/01_noRaShi/01_HBL/E120MeVu/RP1.2.752.243.1.1.20220202141407926.4000.48815_tagman.dcm"
    task_2_1_1 = dicom_files(rp_fpath)
    task_2_1_1.verify_all_dicom()
        
        