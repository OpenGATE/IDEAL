==========================
INPUT DICOM TAGS
==========================
--------------
RP DICOM file's tags used in IDEAL
--------------
Dicom tags (name: tag) of the RT plan dicom that are used by IDEAL::

	PatientID :  0x100020
	PatientName :  0x100010
	PatientBirthDate :  0x100030
	PatientSex :  0x100040
	RTPlanLabel :  0x300a0002
	SOPInstanceUID :  0x80018
	ReferringPhysicianName :  0x80090
	PlanIntent :  0x300a000a
	OperatorsName :  
	ReviewerName :  0x300e0008
	ReviewDate :  0x300e0004
	ReviewTime :  0x300e0005
	NumberOfBeams :  0x300a0080  # uses length of beam seq, not the tag directly
	SOPClassUID :  0x80016
	IonBeamSequence :  0x300a03a2
	DoseReferenceSequence :  0x300a0010
	FractionGroupSequence :  0x300a0070
	ReferencedStructureSetSequence :  0x300c0060

	DoseReferenceSequence[i]. ReferencedROINumber :  0x30060084
	DoseReferenceSequence[i]. TargetPrescriptionDose :  0x300a0026
	ReferencedStructureSetSequence[i]. ReferencedSOPInstanceUID :  0x81155
	FractionGroupSequence[i]. ReferencedBeamSequence :  0x300c0004
	IonBeamSequence[i]. BeamNumber :  0x300a00c0
	IonBeamSequence[i]. IonControlPointSequence :  0x300a03a8
	IonBeamSequence[i]. FinalCumulativeMetersetWeight :  0x300a010e
	IonBeamSequence[i]. BeamName :  0x300a00c2
	IonBeamSequence[i].RadiationType : 0x300a00c6
	IonBeamSequence[i]. RadiationAtomicNumber :  0x300a0304
	IonBeamSequence[i]. RadiationMassNumber :  0x300a0302
	IonBeamSequence[i]. RadiationChargeState :  0x300a0306
	IonBeamSequence[i]. TreatmentMachineName :  0x300a00b2
	IonBeamSequence[i]. NumberOfRangeModulators :  0x300a0340 ***
	IonBeamSequence[i]. NumberOfRangeShifters :  0x300a0312 **
	IonBeamSequence[i]. PrimaryDosimeterUnit :  0x300a00b3
	IonBeamSequence[i]. SnoutSequence :  0x300a030c
	IonBeamSequence[i]. RangeModulatorSequence :  0x300a0342 ***
	IonBeamSequence[i]. RangeShifterSequence :  0x300a0314 # Needs NumberOfRangeShifters > 0 **

	IonBeamSequence[i].SnoutSequence[i]. SnoutID :  0x300a030f
	IonBeamSequence[i].RangeShifterSequence[i]. RangeShifterID :  0x300a0318  
	IonBeamSequence[i].RangeModulatorSequence[i]. RangeModulatorID :  0x300a0346
	IonBeamSequence[i].IonControlPointSequence[i]. PatientSupportAngle :  0x300a0122 # Couch
	IonBeamSequence[i].IonControlPointSequence[i]. IsocenterPosition :  0x300a012c
	IonBeamSequence[i].IonControlPointSequence[i]. GantryAngle :  0x300a011e
	IonBeamSequence[i].IonControlPointSequence[i]. SnoutPosition :  0x300a030d
	IonBeamSequence[i].IonControlPointSequence[i]. NominalBeamEnergy :  0x300a0114
	IonBeamSequence[i].IonControlPointSequence[i]. NumberOfScanSpotPositions : 0x300a0392
	IonBeamSequence[i].IonControlPointSequence[i]. ScanSpotMetersetWeights : 0x300a0396
	IonBeamSequence[i].IonControlPointSequence[i]. ScanSpotPositionMap : 0x300a0394
	IonBeamSequence[i].IonControlPointSequence[i]. CumulativeMetersetWeight : 0x300a0134
	IonBeamSequence[i].IonControlPointSequence[i]. ScanSpotTuneID : 0x300a0390
	IonBeamSequence[i].IonControlPointSequence[i]. NumberOfPaintings: 0x300a039a

--------------
RS DICOM file's tags used in IDEAL
--------------
Dicom tags (name: tag) of the RT structures set dicom that are used by IDEAL::

	SOPClassUID : 0x80016
	SOPInstanceUID :  0x80018
	StructureSetROISequence : 0x30060020
	ROIContourSequence :  0x30060039
	RTROIObservationsSequence : 0x30060080
	ReferencedFrameOfReferenceSequence : 0x30060010

	RTROIObservationsSequence [i].ReferencedROINumber : 0x30060084
	RTROIObservationsSequence [i].RTROIInterpretedType : 0x300600a4  # ‘EXTERNAL’ is a type
	StructureSetROISequence[i]. ROIName :  0x30060026
	StructureSetROISequence[i]. ROINumber : 0x30060022
	ROIContourSequence [i].ReferencedROINumber : 0x30060084

	ReferencedFrameOfReferenceSequence[i].RTReferencedStudySequence[i].RTReferencedSeriesSequence[i].SeriesInstanceUID: 0x20000e

--------------
RD DICOM file's tags used in IDEAL
--------------
Dicom tags (name: tag) of the RT dose dicom that are used by IDEAL::

	NumberOfFrames :  0x280008
	ReferencedRTPlanSequence :  0x300c0002
	Rows :  0x280010
	Columns :  0x280011
	DoseGridScaling :  0x3004000e
	PixelSpacing :  0x280030
	SliceThickness :  0x180050
	ImagePositionPatient :  0x200032
	DoseType :  0x30040004
	SOPClassUID :  0x80016
	DoseSummationType :  0x3004000a *
	DoseUnits :  0x30040002
	ReferencedRTPlanSequence[i].ReferencedSOPInstanceUID:  0x81155
	ReferencedRTPlanSequence[i].ReferencedFractionGroupSequence : 0x300c0020 *
	ReferencedRTPlanSequence[i].ReferencedFractionGroupSequence[i].ReferencedBeamSequence[i].ReferencedBeamNumber:  0x300c0006 *  # Only id DoseSummationType != ‘PLAN’

--------------
CT DICOM file's tags used in IDEAL
--------------
Dicom tags (name: tag) of the CT dicom that are used by IDEAL::

	InstitutionName :  0x80080
	InstanceCreationDate :  0x80012
	SeriesInstanceUID :  0x20000e
	SeriesDescription: 0x8103e  only if CT is from scanner (not generated artificially). CT protocol here
	Manufacturer: 0x80070  only if CT artificially generated
	NOTE: both tags not used if CT protocol is a command line input
	ImagePositionPatient :  0x200032
	RescaleIntercept :  0x281052
	RescaleSlope :  0x281053
	InstanceCreationTime :  0x80013
	PixelSpacing :  0x280030
	InstanceCreationTime 
	ImagePositionPatient[2]   #slice thickness  
	PixelSpacing[0]       #slice width  
	PixelSpacing[1]       #slice hight  


==========================
EXPORT DICOM TAGS
==========================
Dicom tags (name: tag) that are written by IDEAL in the simulated dose dicom::

	FileMetaInformationGroupLength: (0002,0000)
	FileMetaInformationVersion: (0002,0001)
	MediaStorageSOPClassUID: (0002,0002)
	MediaStorageSOPInstanceUID: (0002,0003)
	TransferSyntaxUID: (0002,0010)
	ImplementationClassUID: (0002,0012)   https://dicom.nema.org/medical/dicom/current/output/chtml/part07/sect_d.3.3.2.html#:~:text=The%20Implementation%20Class%20UID%20identifies,its%20implementation%20environment%20from%20others
	ImplementationVersionName: (0002,0013)
	AccessionNumber: (0008,0050)
	Manufacturer: (0008,0070)
	ManufacturerModelName: (0008,1090)
	SoftwareVersions: (0018,1020)
	PositionReferenceIndicator: (0020,1040
	SpecificCharacterSet: (0008,0005)
	InstanceCreationDate: (0008,0012)
	InstanceCreationTime: (0008,0013)
	SOPClassUID: (0008,0016)
	SOPInstanceUID: (0008,1155)
	StudyDate: (0008,0020)
	StudyTime: (0008,0030)
	Modality: (0008,0060)
	ReferringPhysicianName: (0008,0090) 
	if  in rtplan:
	SeriesDescription: (0008,103F)
	OperatorsName: (0008,1070)
	PatientName: (0010,0010)
	PatientID: (0010,0020)
	PatientBirthDate : (0010,0030)
	PatientSex: (0010,0040)
	StudyDescription:  (0008,1030)           ### absent for phantom/commissioning
	PatientIdentityRemoved:  (0012,0062)       ### absent for phantom/commsissioning plans
	DeidentificationMethod: (0012,0063)        ### absent for phantom/commsissioning plans
	StudyID: (0020,0010)
	SeriesNumber: (0020,0011)
	if phantom:
	InstanceNumber:  (0020,0013)    ### only for phantom/commissioning
	PatientOrientation: (0020,0020)   ### only for phantom/commissioning
	SliceThickness: (0018,0050)
	StudyInstanceUID: (0020,000D)
	SeriesInstanceUID: (0020,000E)
	ImagePositionPatient: (0020,0032)
	ImageOrientationPatient: (0020,0037)
	FrameOfReferenceUID: (0020,0052)
	SamplesPerPixel: (0028,0002)
	PhotometricInterpretation: (0028,0004)
	NumberOfFrames: (0028,0008)
	FrameIncrementPointer: (0028,0009)
	Rows: (0028,0010)
	Columns: (0028,0011)
	PixelSpacing: (0028,0030)
	BitsAllocated: (0028,0100)
	BitsStored: (0028,0101)
	HighBit: (0028,0102)
	PixelRepresentation: (0028,0103)
	DoseUnits: 3004,0002)
	DoseType: (3004,0004)
	DoseSummationType: (3004,000A)
	GridFrameOffsetVector: (3004,000C)
	DoseGridScaling: (3004,000E)
	ReferencedRTPlanSequence: (300C,0002)
	ReferencedRTPlanSequence .ReferencedSOPClassUID: (0008,1150)
	ReferencedRTPlanSequence.ReferencedSOPInstanceUID: (0008,1155)

	if not plandose: 
	ReferencedRTPlanSequence.ReferencedFractionGroupSequence: (300C,0020)    
	ReferencedRTPlanSequence.ReferencedFractionGroupSequence.ReferencedFractionGroupNumber: (300C,0022)    
	ReferencedRTPlanSequence.ReferencedFractionGroupSequence.ReferencedBeamSequence: (300C,000)
	ReferencedRTPlanSequence.ReferencedFractionGroupSequence.ReferencedBeamSequence .ReferencedBeamNumber:  (300C,0006)
	PixelData: (7FE0,0010)


