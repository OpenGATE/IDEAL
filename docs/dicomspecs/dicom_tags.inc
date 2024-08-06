
##INPUT DICOM TAGS:


###RP DICOM file's tags used in IDEAL
```python
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

DoseReferenceSequence[0]. ReferencedROINumber :  0x30060084
DoseReferenceSequence[0]. TargetPrescriptionDose :  0x300a0026
ReferencedStructureSetSequence[0]. ReferencedSOPInstanceUID :  0x81155
FractionGroupSequence[0]. ReferencedBeamSequence :  0x300c0004
IonBeamSequence[0]. BeamNumber :  0x300a00c0
IonBeamSequence[0]. IonControlPointSequence :  0x300a03a8
IonBeamSequence[0]. FinalCumulativeMetersetWeight :  0x300a010e
IonBeamSequence[0]. BeamName :  0x300a00c2
IonBeamSequence[0].RadiationType : 0x300a00c6
IonBeamSequence[0]. RadiationAtomicNumber :  0x300a0304
IonBeamSequence[0]. RadiationMassNumber :  0x300a0302
IonBeamSequence[0]. RadiationChargeState :  0x300a0306
IonBeamSequence[0]. TreatmentMachineName :  0x300a00b2
IonBeamSequence[0]. NumberOfRangeModulators :  0x300a0340 ***
IonBeamSequence[0]. NumberOfRangeShifters :  0x300a0312 **
IonBeamSequence[0]. PrimaryDosimeterUnit :  0x300a00b3
IonBeamSequence[0]. SnoutSequence :  0x300a030c
IonBeamSequence[0]. RangeModulatorSequence :  0x300a0342 ***
IonBeamSequence[0]. RangeShifterSequence :  0x300a0314 # Needs NumberOfRangeShifters > 0 **

IonBeamSequence[0].SnoutSequence[0]. SnoutID :  0x300a030f
IonBeamSequence[0].RangeShifterSequence[0]. RangeShifterID :  0x300a0318  
IonBeamSequence[0].RangeModulatorSequence[0]. RangeModulatorID :  0x300a0346
IonBeamSequence[0].IonControlPointSequence[0]. PatientSupportAngle :  0x300a0122 # Couch
IonBeamSequence[0].IonControlPointSequence[0]. IsocenterPosition :  0x300a012c
IonBeamSequence[0].IonControlPointSequence[0]. GantryAngle :  0x300a011e
IonBeamSequence[0].IonControlPointSequence[0]. SnoutPosition :  0x300a030d
IonBeamSequence[0].IonControlPointSequence[0]. NominalBeamEnergy :  0x300a0114
IonBeamSequence[0].IonControlPointSequence[0]. NumberOfScanSpotPositions : 0x300a0392
IonBeamSequence[0].IonControlPointSequence[0]. ScanSpotMetersetWeights : 0x300a0396
IonBeamSequence[0].IonControlPointSequence[0]. ScanSpotPositionMap : 0x300a0394
IonBeamSequence[0].IonControlPointSequence[0]. CumulativeMetersetWeight : 0x300a0134
IonBeamSequence[0].IonControlPointSequence[0]. ScanSpotTuneID : 0x300a0390
IonBeamSequence[0].IonControlPointSequence[0]. NumberOfPaintings: 0x300a039a
```

###RS DICOM file's tags used in IDEAL
```python
SOPClassUID : 0x80016
SOPInstanceUID :  0x80018
StructureSetROISequence : 0x30060020
ROIContourSequence :  0x30060039
RTROIObservationsSequence : 0x30060080
ReferencedFrameOfReferenceSequence : 0x30060010

RTROIObservationsSequence [0].ReferencedROINumber : 0x30060084
RTROIObservationsSequence [0].RTROIInterpretedType : 0x300600a4  # ‘EXTERNAL’ is a type
StructureSetROISequence[0]. ROIName :  0x30060026
StructureSetROISequence[0]. ROINumber : 0x30060022
ROIContourSequence [0].ReferencedROINumber : 0x30060084

ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].SeriesInstanceUID: 0x20000e
```

###RD DICOM file's tags used in IDEAL
```python
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
ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID:  0x81155
ReferencedRTPlanSequence[0].ReferencedFractionGroupSequence : 0x300c0020 *
ReferencedRTPlanSequence[0].ReferencedFractionGroupSequence[0].ReferencedBeamSequence[0].ReferencedBeamNumber:  0x300c0006 *  # Only id DoseSummationType != ‘PLAN’
```

###CT DICOM file's tags used in IDEAL
```python
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
```


##EXPORT DICOM TAGS:
```python
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


```
