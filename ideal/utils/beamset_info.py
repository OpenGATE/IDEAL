#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import pydicom
import os
import re
import numpy as np
from utils.dose_info import dose_info
import logging
logger=logging.getLogger(__name__)

def is_close(x,y,eps=1e-6):
    sumabs = np.abs(x)+np.abs(y)
    absdif = np.abs(x-y)
    ok = (sumabs == 0) or (absdif < eps*0.5*sumabs)
    return ok

class spot_info(object):
    def __init__(self,xiec,yiec,w):
        self.xiec = xiec
        self.yiec = yiec
        self.w = w
    def get_msw(self,t0,t1):
        return self.w

class layer_info(object):
    def __init__(self,ctrlpnt,j,cumsumchk=[],verbose=False,keep0=False):
        self._cp = ctrlpnt
        if verbose:
            logger.debug('{}. control point with type {}'.format(j,type(self._cp)))
            for k in self._cp.keys():
                if pydicom.datadict.dictionary_has_tag(k):
                    kw = pydicom.datadict.keyword_for_tag(k)
                else:
                    kw = "(UNKNOWN)"
                logger.debug('k={} keyword={}'.format(k,kw))
        nspot =int(self._cp.NumberOfScanSpotPositions)
        #assert(self._cp.NominalBeamEnergyUnit == 'MEV')
        if nspot == 1:
            self.w = np.array([float(self._cp.ScanSpotMetersetWeights)])
        else:
            self.w = np.array([float(w) for w in self._cp.ScanSpotMetersetWeights])
        assert( nspot == len( self.w ) )
        assert( nspot*2 == len( self._cp.ScanSpotPositionMap ) )
        #self.cpindex = int(self._cp.ControlPointIndex)
        #self.spotID = str(self._cp.ScanSpotTuneID)
        cmsw = float(self._cp.CumulativeMetersetWeight)
        if cumsumchk:
            logger.debug("CumulativeMetersetWeight={0:14.8g} sum of previous spots={1:14.8g} diff={2:14.8g}".format(
                cmsw, cumsumchk[0], cmsw - cumsumchk[0]))
            assert( is_close(cmsw,cumsumchk[0]) )
        #self.npainting = int(self._cp.NumberOfPaintings)
        xy = np.array([float(pos) for pos in self._cp.ScanSpotPositionMap]).reshape(nspot,2)
        self.x = np.array(xy[:,0])
        self.y = np.array(xy[:,1])
        if not keep0:
            mask=(self.w>0.)
            self.w = self.w[mask]
            self.x = self.x[mask]
            self.y = self.y[mask]
        #ixmin=np.argmin(self.x)
        #iymin=np.argmin(self.y)
        #ixmax=np.argmax(self.x)
        #iymax=np.argmax(self.y)
        #logger.debug("extreme spots on layer={}: ".format(j)+", ".join(["{}".format(xy[ixy,:]) for ixy in set([ixmin,iymin,ixmax,iymax])]))
        #self.spot_id = str(self._cp.ScanSpotTuneID)
        #self.dx = float(self._cp.ScanningSpotSize[0])/2.3549
        #self.dy = float(self._cp.ScanningSpotSize[1])/2.3549
        ##assert( cmsw>0 )
        #if (self.w<=0).any():
        #    logger.debug("%s".format(self))
        #    logger.warn("layer number {} has {} spots, {} spots have zero weight:".format(self.cpindex,len(self.w),np.sum(self.w<=0)))
        #    logger.warn("weights={}".format(self.w[:10]))
        #    #assert(np.sum(self.w<=0) == len(self.w))
        ##assert( (self.w>0).all() ^ (self.w==0.0).all() )
        wsum=np.sum(self.w)
        logger.debug("layer number {} has {} spots, of which {} with zero weight, cumsum={}, sum(w)={}".format(j,len(self.w),np.sum(self.w<=0),cmsw,wsum))
        # assert( (wsum-cmsw) < 1e-6*(wsum+cmsw) )
        #assert( self.npainting == 1 )
        cumsumchk[0]+=wsum
    @property
    def energy(self):
        # DICOM specifies energy per nucleon, Gate wants total kinetic energy
        return float(self._cp.NominalBeamEnergy)
    @property
    def tuneID(self):
        return str(self._cp.ScanSpotTuneID)
    @property
    def npainting(self):
        return int(self._cp.NumberOfPaintings)
    @property
    def mswtot(self):
        return np.sum(self.w)
    @property
    def nspots(self):
        return len(self.w)
    @property
    def weights(self):
        return self.w
    @property
    def spots(self):
        return [spot_info(x,y,w) for (x,y,w) in zip(self.x,self.y,self.w)]
    def get_spots(self,t0=None,t1=None):
        return [spot_info(x,y,w) for (x,y,w) in zip(self.x,self.y,self.w)]

class beam_info(object):
    #def __init__(self,beam,rd,i,keep0=False):
    def __init__(self,beam,i,override_number,keep0=False):
        logger.debug("loading {}th beam".format(i))
        self._dcmbeam = beam # the DICOM beam object
        self._warnings = list() # will hopefully stay empty
        logger.debug("trying to access first control point")
        self._icp0 = beam.IonControlPointSequence[0] # convenience: first control point
        self._beam_number_is_fishy = override_number # workaround for buggy TPSs, e.g. PDM
        self._index = i # the index in the beam sequence
        self._layers = list()
        mswchk = self.FinalCumulativeMetersetWeight
        cumsumchk=[0.]
        logger.debug("going to read all layers")
        for j,icp in enumerate(self._dcmbeam.IonControlPointSequence):
            li = layer_info(icp,j,cumsumchk,False,keep0)
            if 0.<li.mswtot or keep0:
                self._layers.append(li)
        logger.debug("survived reading all layers")
        if not is_close(mswchk,cumsumchk[0]):
            raise ValueError("final cumulative msw {} != sum of spot msw {}".format(mswchk,cumsumchk[0]))
        logger.debug("survived cumulative MSW check")
    def GetAndClearWarnings(self):
        # return and clear
        w=self._warnings[:]
        self._warnings = list()
        return w
    @property
    def FinalCumulativeMetersetWeight(self):
        return float(self._dcmbeam.FinalCumulativeMetersetWeight)
    @property
    def PatientSupportAngle(self):
        return float(self._icp0.PatientSupportAngle)
    @property
    def patient_angle(self):
        return float(self._icp0.PatientSupportAngle)
    @property
    def IsoCenter(self):
        if "IsocenterPosition" in self._icp0:
            if len(self._icp0.IsocenterPosition) ==3.:
                return [float(xyz) for xyz in self._icp0.IsocenterPosition]
            else:
                msg="Got corrupted isocenter = '{}'; assuming [0,0,0] for now, keep fingers crossed.".format(self._icp0.IsocenterPosition)
        else:
            msg="No isocenter specified in treatment plan; assuming [0,0,0] for now, keep fingers crossed."
        logger.error(msg)
        self._warnings.append(msg)
        # FIXME: what to do else? Cry? Throw segfaults? Drink bad coffee?
        return [0.,0.,0.]
    @property
    def Name(self):
        # TODO: the Name and name properties are identical, keep only one of them.
        return str(self._dcmbeam.BeamName)
    @property
    def Number(self):
        # TODO: the Number and number properties are identical, keep only one of them.
        nr = str(self._index+1) if self._beam_number_is_fishy else str(self._dcmbeam.BeamNumber)
        return nr
    @property
    def name(self):
        # TODO: the Name and name properties are identical, keep only one of them.
        return str(self._dcmbeam.BeamName)
    @property
    def number(self):
        # TODO: the Number and number properties are identical, keep only one of them.
        nr = str(self._index+1) if self._beam_number_is_fishy else str(self._dcmbeam.BeamNumber)
        return nr
    @property
    def RadiationType(self):
        radtype=str(self._dcmbeam.RadiationType)
        if radtype=='ION':
            ionZ=str(self._dcmbeam.RadiationAtomicNumber)
            ionA=str(self._dcmbeam.RadiationMassNumber)
            ionQ=str(self._dcmbeam.RadiationChargeState)
            radtype='_'.join(['ION',ionZ,ionA,ionQ])
        return radtype
    @property
    def gantry_angle(self):
        return float(self._icp0.GantryAngle)
    @property
    def TreatmentMachineName(self):
        if "TreatmentMachineName" in self._dcmbeam:
            return str(self._dcmbeam.TreatmentMachineName)
        # RayStation 8b exports anonymized treatment plans without the treatment machine name!
        if np.isclose(self.gantry_angle,0.0):
            # FIXME: should be solved in a way that works for any clinic, not just MedAustron
            ducktape = str("IR2VBL")
        elif np.isclose(self.gantry_angle,90.0):
            # FIXME: should be solved in a way that works for any clinic, not just MedAustron
            ducktape = str("IR2HBL")
        else:
            raise ValueError("treatment machine name is missing and gantry angle {} does not enable a good guess".format(self.gantry_angle))
        msg="treatment machine name for beam name={} number={} missing in treatment plan, guessing '{}' from gantry angle {}".format(self.name,self.number,ducktape,self.gantry_angle)
        logger.error(msg)
        self._warnings.append(msg)
        return ducktape # ugly workaround! FIXME!
    @property
    def SnoutID(self):
        if "SnoutSequence" in self._dcmbeam:
            return str(self._dcmbeam.SnoutSequence[0].SnoutID)
        # FIXME: what to do else?
        return str("NA")
    @property
    def SnoutPosition(self):
        if "SnoutPosition" in self._dcmbeam:
            return float(self._icp0.SnoutPosition)
        # FIXME: what to do else?
        return str("NA")
    @property
    def NumberOfRangeModulators(self):
        return int(self._dcmbeam.NumberOfRangeModulators)
    @property
    def RangeModulatorIDs(self):
        if self.NumberOfRangeModulators>0:
            return [rm.RangeModulatorID for rm in self._dcmbeam.RangeModulatorSequence]
        return list()
    @property
    def NumberOfRangeShifters(self):
        return int(self._dcmbeam.NumberOfRangeShifters)
    @property
    def RangeShifterIDs(self):
        if self.NumberOfRangeShifters>0:
            return [str(rs.RangeShifterID) for rs in self._dcmbeam.RangeShifterSequence]
        return list()
    @property
    def NumberOfEnergies(self):
        return len(set([icp.NominalBeamEnergy for icp in self._dcmbeam.IonControlPointSequence]))
    @property
    def nlayers(self):
        return len(self._layers)
    @property
    def layers(self):
        return self._layers
    @property
    def nspots(self):
        return sum([l.nspots for l in self.layers])
    @property
    def mswtot(self):
        return sum([l.mswtot for l in self._layers])
    @property
    def PrimaryDosimeterUnit(self):
        return str(self._dcmbeam.PrimaryDosimeterUnit)

def sequence_check(obj,attr,nmin=1,nmax=0,name="object"):
    logger.debug("checking that {} has attribute {}".format(name,attr))
    assert(hasattr(obj,attr))
    seq=getattr(obj,attr)
    logger.debug("{} has length {}, will check if it >={} and <={}".format(name,len(seq),nmin,nmax))
    assert(len(seq)>=nmin)
    assert(nmax==0 or len(seq)<=nmax)


class beamset_info(object):
    """
    This class reads a DICOM 'RT Ion Plan Storage' file and collects related information such as TPS dose files.
    It does NOT (yet) try to read a reffered structure set and/or CT images.
    This acts as a wrapper (all DICOM access on the plan file happens here). This has a few advantages over direct
    DICOM access in the other modules:
    * we can deal with different "DICOM dialects" here; some TPSs may store their plans in different ways.
    * if 'private tags' need to be taken into account then we can also do that here.
    * We can make a similar class, with the same attributes, for a treatment plan stored in a different format, e.g. for research, commissioning or QA purposes.

    Then the rest of the code can work with that in the same way.
    """
    patient_attrs = ["Patient ID","Patient Name","Patient Birth Date","Patient Sex"]
    plan_req_attrs = ["RT Plan Label","SOP Instance UID",
                      "Referring Physician Name","Plan Intent"]
    plan_opt_attrs = ["Operators Name","Reviewer Name","Review Date","Review Time" ]
    plan_attrs = plan_req_attrs + plan_opt_attrs
    #plan_attrs = ["RT Plan Name","RT Plan Label","SOP Instance UID","Operators Name",
    #              "Reviewer Name","Review Date","Review Time","Referring Physician Name","Plan Intent"]
    bs_attrs = [ "Number Of Beams", "RT Plan Label", "Prescription Dose",
                 "Target ROI Name", "Radiation Type", "Treatment Machine(s)"]
    def __init__(self,rpfp):
        self._warnings = list() # will hopefully stay empty
        self._beam_numbers_corrupt = False # e.g. PDM does not define beam numbers
        self._rp = pydicom.read_file(rpfp)
        self._rpfp = rpfp
        logger.debug("beamset: survived reading DICOM file {}".format(rpfp))
        self._rpdir = os.path.dirname(rpfp)
        self._rpuid = str(self._rp.SOPInstanceUID)
        self._dose_roiname = None # stays None for CT-less plans, e.g. commissioning plans
        self._dose_roinumber = None # stays None for CT-less plans, e.g. commissioning plans
        logger.debug("beamset: going to do some checks")
        self._chkrp()
        logger.debug("beamset: survived check, loading beams")
        self._beams = [beam_info(b,i,self._beam_numbers_corrupt) for i,b in enumerate(self._rp.IonBeamSequence)]
        logger.debug("beamset: DONE")
    def GetAndClearWarnings(self):
        # return a copy
        for b in self._beams:
            #bwarnings = b.GetAndClearWarnings()
            for w in b.GetAndClearWarnings():
                if w not in self._warnings:
                    self._warnings.append(w)
        allw = self._warnings[:]
        self._warnings = list()
        return allw
    def __getitem__(self,k):
        if type(k)==int:
            if k>=0 and k<len(self._beams):
                return self._beams[k]
            else:
                raise IndexError("attempt to get nonexisting beam with index {}".format(k))
        for b in self._beams:
            if str(k) == b.name or str(k) == b.number:
                return b
        raise KeyError("attempt to get nonexisting beam with key {}".format(k))
    def _chkrp(self):
        if 'SOPClassUID' not in self._rp:
            raise IOError("bad DICOM file {},\nmissing SOPClassUID".format(self._rpfp))
        sop_class_name = pydicom.uid.UID_dictionary[self._rp.SOPClassUID][0]
        if sop_class_name != 'RT Ion Plan Storage':
            raise IOError("bad plan file {},\nwrong SOPClassUID: {}='{}',\nexpecting an 'RT Ion Plan Storage' file instead.".format(self._rpfp,self._rp.SOPClassUID,sop_class_name))
        missing_attrs = list()
        for a in ["IonBeamSequence"]+self.plan_req_attrs+self.patient_attrs:
            b = a.replace(" ","")
            if not hasattr(self._rp,b):
                missing_attrs.append(b)
        if missing_attrs:
            raise IOError("bad plan file {},\nmissing keys: {}".format(self._rpfp,", ".join(missing_attrs)))
        self._get_rds()
        if hasattr(self._rp,"DoseReferenceSequence"):
            sequence_check(self._rp,"DoseReferenceSequence",1,1)
            if hasattr(self._rp.DoseReferenceSequence[0],"ReferencedROINumber"):
                self._dose_roinumber = int(self._rp.DoseReferenceSequence[0].ReferencedROINumber)
        if self._dose_roinumber is None:
            logger.info("no target ROI specified (probably because of missing DoseReferenceSequence)")
        sequence_check(self._rp,"IonBeamSequence",1,0)
        sequence_check(self._rp,"FractionGroupSequence",1,1)
        frac0 = self._rp.FractionGroupSequence[0]
        sequence_check(frac0,"ReferencedBeamSequence",len(self._rp.IonBeamSequence),len(self._rp.IonBeamSequence))
        number_set = set()
        for dcmbeam in self._rp.IonBeamSequence:
            nr = int(dcmbeam.BeamNumber)
            if nr < 0:
                self._beam_numbers_corrupt = True
                logger.error("CORRUPT INPUT: found a negative beam number {}.".format(nr))
            if nr in number_set:
                self._beam_numbers_corrupt = True
                logger.error("CORRUPT INPUT: found same beam number {} for multiple beams.".format(nr))
            number_set.add(nr)
        if self._beam_numbers_corrupt:
            msg="Beam numbers are corrupt! Will override them with simple enumeration, keep fingers crossed."
            logger.error(msg)
            self._warnings.append(msg)
        logger.debug("checked planfile, looks like all attributes are available...")
    def _get_rds(self):
        # The "_rds" attribute is going to be a dictionary
        # * The key for each dose is either the referenced beam number or 'PLAN'
        # * If the dose type is "effective" (as opposed to "physical") then the key has '_RBE' suffixed.
        self._rds = dose_info.get_dose_files(self._rpdir,self.uid)
        Nfound = len(self._rds.keys())
        Nexpected = len(self._rp.IonBeamSequence)
        # TODO: check beam numbers
        if Nexpected > 1:
            Nexpected += 1
        if Nfound < Nexpected: # there in addition to 'physical' dose files there may be one or several 'effective' ones.
            # oopsie!
            #raise RuntimeError("found {} dose files for UID={}, expected at least {}".format(Nfound,self.uid,Nexpected))
            logger.warn("found {} dose files for UID={}, expected at least {}".format(Nfound,self.uid,Nexpected))
        return
    @property
    def mswtot(self):
        return sum([b.mswtot for b in self._beams])
    def tps_dose_key(self,k=None,only_geo_matters=True,sumtype="any",dosetype="any"):
        logger.debug(f"tps_dose_key: k={k} only_geo_matters={only_geo_matters} sumtype={sumtype} dosetype={dosetype}")
        if self._rds is None or len(self._rds)==0:
            logger.debug(f"No TPS dose data available at all. TPS DOSE *NOT* FOUND.")
            return None
        candidates = {k:v for k,v in self._rds.items()}
        if sumtype.upper() == "BEAM":
            candidates = {k:v for k,v in candidates.items() if v.is_beam_dose}
        elif sumtype.upper() == "PLAN":
            candidates = {k:v for k,v in candidates.items() if v.is_plan_dose}
        if dosetype.upper() == "PHYSICAL":
            candidates = {k:v for k,v in candidates.items() if v.is_physical}
        elif dosetype.upper() == "EFFECTIVE":
            candidates = {k:v for k,v in candidates.items() if v.is_effective}
        if len(candidates) == 1 and k is None:
            k0=list(candidates.keys())[0]
            logger.debug(f"Exactly one TPS dose data available with key {k0}. TPS DOSE *FOUND*.")
            return k0
        logger.debug(f"we have {len(candidates)} tps doses with sumtype={sumtype} and dosetype={dosetype}")
        if k is not None:
            if k in candidates.keys():
                logger.debug(f"'{k}' is a recognized dose label. TPS DOSE *FOUND*.")
                return k
            else:
                logger.debug(f"'{k}' is not a recognized dose label")
            if k in self.beam_names:
                i = self.beam_names.index(k)
                nr = self.beam_numbers[i]
                logger.debug(f"'{k}' is a recognized beam name with index {i} beam number '{nr}'.")
            else:
                logger.debug(f"'{k}' is NOT a recognized beam name either. TPS DOSE *NOT* FOUND.")
                return None
            if nr in candidates.keys():
                logger.debug(f"'{nr}' is a recognized dose label for a dose with sumtype='{sumtype}' and dosetype='{dosetype}'. TPS DOSE *FOUND*.")
                return nr
            logger.debug(f"'{nr}' is not a recognized dose label.")
            krbe=nr+"_RBE"
            if krbe in candidates.keys():
                logger.debug(f"'{krbe}' is a recognized dose label. TPS DOSE *FOUND*.")
                return krbe
            else:
                logger.debug(f"'{krbe}' is not a recognized dose label")
        if only_geo_matters:
            geo_set=set([(tuple(rd.spacing),tuple(rd.nvoxels),tuple(rd.origin)) for key,rd in candidates.items()])
            ngeo = len(geo_set)
            if ngeo==1:
                k0=list(candidates.keys())[0]
                logger.debug(f"dose geometry is same for all TPS doses, using label {k0}. TPS DOSE *FOUND*.")
                return k0
            elif ngeo==0:
                logger.error("didn't find any dose files at all!")
            else:
                logger.error(f"Only geometry matters, but the dose files that I did find have {ngeo} different geometries.")
        logger.debug(f"k={k} only_geo_matters={only_geo_matters} sumtype={sumtype} dosetype={dosetype}: TPS DOSE *NOT* FOUND.")
        return None
    def have_tps_dose(self,k,only_geo_matters=True,sumtype="any",dosetype="any"):
        yes_no = self.tps_dose_key(k,only_geo_matters,dosetype) is not None
        return yes_no
    def tps_dose(self,k=None,only_geo_matters=True,sumtype="any",dosetype="any"):
        kk = self.tps_dose_key(k,only_geo_matters,dosetype)
        if kk is None:
            raise KeyError('Beam name/number/label "{}" not recognized. '.format(k) +
                           'Known beam name(s) is/are: "{}". '.format('", "'.join(self.beam_names)) +
                           'Known numbers are: "{}". '.format('", "'.join([str(nr) for nr in self.beam_numbers])) +
                           'Known dose labels are: "{}".'.format('", "'.join(self._rds.keys()))
                           )
        return self._rds[kk]
    @property
    def name(self):
        # It looks like RTPlanLabel is for the beamset,
        # and RTPlanName is for the entire plan including possibly several beamsets.
        # the RTPlanName is not exported anymore in RayStation 8b, so let's forget about the plan name
        # some anonymization methods are butchering all useful labeling information, even the label and name of an RT plan.
        return str(self._rp.get("RTPlanLabel","anonymized"))
    @property
    def fields(self):
        # GATE synomym for 'beams'
        return self._beams
    @property
    def beams(self):
        return self._beams
    @property
    def uid(self):
        return self._rpuid
    @property
    def beam_angles(self):
        return [str(bm.gantry_angle) for bm in self._beams]
    @property
    def beam_names(self):
        return [str(bm.Name) for bm in self._beams]
    @property
    def beam_numbers(self):
        return [str(bm.Number) for bm in self._beams]
    @property
    def Nfractions(self):
        # FIXME: some evil DICOM plan files have "NumberOfFractionsPlanned" equal to zero. Force this to be one, or is this zero somehow meaningful & useful?
        nfrac = int(self._rp.FractionGroupSequence[0].NumberOfFractionsPlanned)
        if nfrac>0:
            return nfrac
        logger.error("Got Nfractions={} ???! Using nfrac=1 instead.".format(nfrac))
        return 1
    @property
    def target_ROI_name(self):
        return self._dose_roiname
    @target_ROI_name.setter
    def target_ROI_name(self,roiname):
        self._dose_roiname = roiname
    @property
    def target_ROI_number(self):
        return self._dose_roinumber
    @property
    def plan_dose(self):
        # TODO: if there is only one beam, do we still have a 'PLAN' dose file?
        # Or *only* a dose file?
        if self._rds is None or len(self._rds)==0:
            return None
        if len(self._rds) == 1:
            return self._rds.values()[0]
        if 'PLAN' in self._rds:
            return self._rds['PLAN']
        if 'PLAN_RBE' in self._rds:
            return self._rds['PLAN_RBE']
        raise RuntimeError("could not find PLAN dose (neither physical nor effective)")
    @property
    def prescription_dose(self):
        if hasattr(self._rp,"DoseReferenceSequence"):
            if hasattr(self._rp.DoseReferenceSequence[0],"TargetPrescriptionDose"):
                return float(self._rp.DoseReferenceSequence[0].TargetPrescriptionDose)
        return "NA"
    @property
    def plan_label(self):
        return str(self._rp.get("RTPlanLabel","anonymized"))
    @property
    def sanitized_plan_label(self):
        badchars=re.compile("[^a-zA-Z0-9_]")
        return re.sub(badchars,"_",self.plan_label)
    @property
    def patient_info(self):
        return dict([(a,str(getattr(self._rp,a.replace(" ","")))) for a in self.patient_attrs])
    @property
    def plan_info(self):
        reqs = dict([(a,str(getattr(self._rp,a.replace(" ","")))) for a in self.plan_req_attrs])
        opts = dict([(a,"NA" if not hasattr(self._rp,a.replace(" ","")) else str(getattr(self._rp,a.replace(" ","")))) for a in self.plan_opt_attrs])
        reqs.update(opts)
        return reqs
    @property
    def bs_info(self):
        info = dict([ ("Number Of Beams",      str(len(self._beams))),
                      ("RT Plan Label",        self.plan_label),
                      ("Prescription Dose",    str(self.prescription_dose)),
                      ("Target ROI Name",      str(self.target_ROI_name)),
                      ("Radiation Type",       ", ".join(set([str(beam.RadiationType) for beam in self._beams]))),
                      ("Treatment Machine(s)", ", ".join(set([str(beam.TreatmentMachineName) for beam in self._beams])))
                     ])
        dirty = self.plan_label
        sanitized = self.sanitized_plan_label
        if dirty != sanitized:
            info["Sanitized RT Plan Label"] = sanitized
        return info
    def __repr__(self):
        s ="\nPLAN\n\t"   +"\n\t".join(["{0:30s}: {1}".format(a,self.plan_info[a]) for a in self.plan_attrs])
        s+="\nPATIENT\n\t"+"\n\t".join(["{0:30s}: {1}".format(a,self.patient_info[a]) for a in self.patient_attrs])
        s+="\nBEAMSET\n\t"+"\n\t".join(["{0:30s}: {1}".format(a,self.bs_info[a]) for a in self.bs_attrs])
        return s

#################################################################################

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v","--verbose",default=False,action='store_true',help="be verbose, show debugging output")
    parser.add_argument('planfile',help="RP DICOM plan file for ion beam therapy")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - line %(lineno)d - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO,format='%(levelname)s - %(message)s')
    #
    try:
        bs = beamset_info(args.planfile)
        logger.info("{}".format(bs))
    except Exception as e:
        logger.error("{}".format(e))

# vim: set et softtabstop=4 sw=4 smartindent:
