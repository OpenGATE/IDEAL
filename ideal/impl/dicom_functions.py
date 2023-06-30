import pydicom
import os
import itk
from impl.IDEAL_dictionary import *
from impl.beamline_model import beamline_model
from impl.hlut_conf import hlut_conf
from impl.system_configuration import system_configuration
from utils.dose_info import dose_info
from utils.beamset_info import beam_info
from glob import glob

class dicom_files:
    def __init__(self,rp_path):
        self.dcm_dir =  os.path.dirname(rp_path) # directory with all dicom files
        # RP
        print("Get RP file")
        self.rp_path = rp_path
        self.rp_data = pydicom.read_file(rp_path)
        self.uid = self.rp_data.SOPInstanceUID # same for all files
        self.beam_numbers_corrupt = False
        self.beams = [beam_info(b,i,self.beam_numbers_corrupt) for i,b in enumerate(self.rp_data.IonBeamSequence)]
        # RD
        print("Get RD files")
        self.rds = dose_info.get_dose_files(self.dcm_dir,self.uid) #dictionary with dose[BeamNr]= doseObj containing dose image and so on. One for each RD file
        # RS
        print("Get RS file")
        self.rs_data = None
        self.rs_path = None
        self.get_RS_file()
        # CT
        print("Get CT files")
        self.ct_paths = self.get_CT_files() # list with the CT files paths
        print(self.ct_paths[1][0])
        self.ct_first_slice = pydicom.read_file(self.ct_paths[1][0])
        
        
    
    def check_all_dcm(self):
        ok = True 
        missing_keys = {'dicomStructureSet': '', 'dicomRtPlan': '', 'dicomRDose': '', 'dicomCTs': ''}
        
        #print("Checking RP file")
        ok_rp, mk = check_RP(self.rp_path)
        ok = ok and ok_rp
        if mk:
            missing_keys['dicomRtPlan'] = mk
        
        #print("Checking RS file")
        ok_rs, mk = check_RS(self.rs_path)
        ok = ok and ok_rs
        if mk:
            missing_keys['dicomStructureSet'] = mk
            
        #print("Checking RD files")
        for dp in self.rds.values():
            ok_rd, mk = check_RD(dp.filepath)
            ok = ok and ok_rd
            if mk:
                missing_keys['dicomRDose'] = mk
                break
        i = 0   
        #print("Checking CT files")
        for ct in self.ct_paths[1]:
            i+=1
            #print("CT file nr ",i)
            ok_ct, mk = check_CT(ct)
            ok = ok and ok_ct
            if mk:
                missing_keys['dicomCTs'] = mk
                
        return ok, missing_keys
            
    def check_CT_protocol(self):
        all_hluts = hlut_conf.getInstance()
        ctprotocol = all_hluts.hlut_match_dicom(self.ct_first_slice)
        print("CT protocol: ",ctprotocol)
        print("\033[92mCT protocol is fine\033[0m")
        
    def check_beamline_mod(self):
        syscfg = system_configuration.getInstance()
        for b in self.beams:
            print("Cheking beam Nr ",b.Number)
            try:
                bml = beamline_model.get_beamline_model_data(b.TreatmentMachineName, syscfg['beamlines'])
                print("Beamline name is ", b.TreatmentMachineName)
                if b.NumberOfRangeModulators > 0 and not bml.has_rm_details:
                    raise Exception("Beamline {} has no Range Modulator details".format(bml.name))
                print("Nr of Range Modulators: ",b.NumberOfRangeModulators) 
                if b.NumberOfRangeShifters > 0 and not bml.has_rs_details:
                    raise Exception("Beamline {} has no Range Shifters details".format(bml.name))
                print("Nr of Range Shifters: ",b.NumberOfRangeShifters)    
                print("\033[92mBeamline is fine\033[0m")
            except Exception as e: print(e)
     
        
    def get_RS_file(self):
        ss_ref_uid = self.rp_data.ReferencedStructureSetSequence[0].ReferencedSOPInstanceUID
        print("going to try to find the file with structure set with UID '{}'".format(ss_ref_uid))
        nskip=0
        ndcmfail=0
        nwrongtype=0
        nfiles=len([s for s in os.listdir(self.dcm_dir)])
        for s in os.listdir(self.dcm_dir):
            if s[-4:].lower() != '.dcm':
                nskip+=1
                print("no .dcm suffix: {}".format(s))
                continue
            try:
                #print(s)
                ds = pydicom.dcmread(os.path.join(self.dcm_dir,s))
                dcmtype = ds.SOPClassUID.name
            except:
                ndcmfail+=1
                continue
            if dcmtype == "RT Structure Set Storage" and ss_ref_uid == ds.SOPInstanceUID:
                print("found structure set for CT: {}".format(s))
                self.rs_data = ds
                self.rs_path = os.path.join(self.dcm_dir,s)
                break
            else:
                nwrongtype+=1
                #print("rejected structure set for CT: {}".format(s))
                #print("because it as a wrong SOP class ID: {}".format(dcmtype))
                #print("AND/OR because it has the wrong SOP Instance UID: {} != {}".format(ds.SOPInstanceUID,ss_ref_uid))
        if self.rs_data is None:
            raise RuntimeError("could not find structure set with UID={}; skipped {} with wrong suffix, got {} with 'dcm' suffix but pydicom could not read it, got {} with wrong class UID and/or instance UID. It could well be that this is a commissioning plan without CT and structure set data.".format(ss_ref_uid,nskip,ndcmfail,nwrongtype))

    def get_CT_files(self):
        dcmseries_reader = itk.GDCMSeriesFileNames.New(Directory=self.dcm_dir)
        ids = dcmseries_reader.GetSeriesUIDs()
        #print("got DICOM {} series IDs".format(len(ids)))
        flist=list()
        uid = self.rs_data.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].SeriesInstanceUID
        if uid:
            if uid in ids:
                try:
                    #flist = sitk.ImageSeriesReader_GetGDCMSeriesFileNames(ddir,uid)
                    flist = dcmseries_reader.GetFileNames(uid)
                    return uid,flist
                except:
                    logger.error('something wrong with series uid={} in directory {}'.format(uid,self.dcm_dir))
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
                    print('found CT series id {}'.format(suid))
                    ctid.append(suid)
                else:
                    print('not CT: series id {} is a "{}"'.format(suid,descr))
            if len(ctid)>1:
                raise ValueError('no series UID was given, and I found {} different CT image series: {}'.format(len(ctid), ",".join(ctid)))
            elif len(ctid)==1:
                uid = ctid[0]
                #flist = sitk.ImageSeriesReader_GetGDCMSeriesFileNames(ddir,uid)
                flist = dcmseries_reader.GetFileNames(uid)
                return flist

def verify_all_dcm_keys(dcm_dir,rp_name,rs_name,ct_names,rd_names):
    ok = True 
    missing_keys = {}
    
    #print("Checking RP file")
    rp = os.path.join(dcm_dir,rp_name[0])
    
    ok_rp, mk = check_RP(rp)
    ok = ok and ok_rp
    if mk:
        missing_keys['dicomRtPlan'] = mk
    
    #print("Checking RS file")
    rs  = os.path.join(dcm_dir,rs_name[0])
    
    ok_rs, mk = check_RS(rs)
    ok = ok and ok_rs
    if mk:
        missing_keys['dicomStructureSet'] = mk

    for rd_n in rd_names:
        rd = os.path.join(dcm_dir,rd_n)
        ok_rd, mk = check_RD(rd)
        ok = ok and ok_rd
        if mk:
            missing_keys['dicomRDose'] = mk
            break
    i = 0   

    for ct_n in ct_names:
        ct = os.path.join(dcm_dir,ct_n)
        i+=1
        #print("CT file nr ",i)
        ok_ct, mk = check_CT(ct)
        ok = ok and ok_ct
        if mk:
            missing_keys['dicomCTs'] = mk
            
    return ok, missing_keys        
       
def check_RP(filepath):
    
	ok = True
	data = pydicom.read_file(filepath)
	dp = IDEAL_RP_dictionary()
	
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
		
def check_RS(filepath):
	
    # bool for correctness of file content
	ok = True 
    
	data = pydicom.read_file(filepath) 
	ds = IDEAL_RS_dictionary()
	
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
	
def check_RD(filepath):
	ok = True
    
	data = pydicom.read_file(filepath) 
	dd = IDEAL_RD_dictionary()
	
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

def check_CT(filepath):
	ok = True
    
	data = pydicom.read_file(filepath) 
	dct = IDEAL_CT_dictionary()
	
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
		
		if key not in data:
			
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
		

# ~ if __name__ == '__main__':
		
	# ~ filepath = input()
	# ~ RP_info(filepath)

