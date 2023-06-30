# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import os
import logging
import numpy as np
from utils.beamset_info import beamset_info
from impl.system_configuration import system_configuration
logger=logging.getLogger(__name__)

class gate_pbs_spot:
    def __init__(self,x,y,w):
        self._x = x
        self._y = y
        self._w = w
    def get_msw(self,tstart=None, tend=None):
        # interface is for time dependent dose calculations, but we do not support that here
        return self._w
    @property
    def msw(self):
        return self._w
    @property
    def xiec(self):
        return self._x
    @property
    def yiec(self):
        return self._y

class gate_pbs_control_point:
    def __init__(self,i):
        self.index = i
        self.spots = list()
    def get_spots(self,dummy1=None,dummy2=None):
        return self.spots
    @property
    def mswtot(self):
        return sum([spot.msw for spot in self.spots])

class gate_pbs_field:
    def __init__(self,fid,bml,radtype='unset',gantry_angle=0.,patient_angle=0.):
        self.id = fid
        self.bml = bml
        self.radiation_type = radtype.upper()
        self.control_points = list()
        self.gantry_angle = gantry_angle
        self.patient_angle = patient_angle
        self.range_shifter_ids = list()
        # dummy for now
        self.range_modulator_ids = list()
    @property
    def nspots(self):
        return sum([len(cpt.spots) for cpt in self.control_points])
    @property
    def layers(self):
        return self.control_points
    @property
    def nlayers(self):
        return len(self.control_points)
    @property
    def mswtot(self):
        return sum([cpt.mswtot for cpt in self.control_points])
    @property
    def TreatmentMachineName(self):
        return self.bml.name
    @property
    def number(self):
        return self.id
    @property
    def Number(self):
        return self.id
    @property
    def PatientSupportAngle(self):
        return self.patient_angle
    @property
    def Name(self):
        # A GATE field has only one id, either a number or a name
        return str(self.id)
    @property
    def RadiationType(self):
        return self.radiation_type
    @property
    def NumberOfRangeModulators(self):
        # dummy for now
        return 0
    @property
    def RangeModulatorIDs(self):
        # dummy for now
        return list()
    @property
    def NumberOfRangeShifters(self):
        return len(self.range_shifter_ids)
    @property
    def RangeShifterIDs(self):
        return list(self.range_shifter_ids) # return a copy of the list

class gate_pbs_plan:
    """
    It might be more appropriate to call this a 'MCsquared' or 'REGGUI' plan.
    It can still be used for reading "normal" Gate-style PBS plan text files,
    which do not contain any information about passive elements.
    """
    def __init__(self,planpath,bml=None,radtype='proton'):
        self.status = "parsing"
        self.fields = list()
        self.bml = bml
        self.radtype = radtype
        self.current_control_point = None
        self.current_field = None
        self._next_ = self._read_plan_name
        self.expect_binary = False
        logger.debug(f"going to open planfile {planpath}")
        with open(planpath,"r") as planfile:
            nskip=0
            for linenr,line in enumerate(planfile):
                lin = line.strip()
                if self._skippable(lin):
                    nskip+=1
                    continue
                #logger.debug(f"{nskip} lines skipped, now parsing line={lin} with method {str(self._next_)}")
                try:
                    self._next_(lin)
                except ValueError as ve:
                    logger.error(f'problem in line {linenr} of {planpath}: {str(ve)}')
                    self.status = "error"
                    raise
                nskip=0
        self.status = "parsed"
    def __getitem__(self,label):
        for f in self.fields:
            if str(f.Name) == str(label):
                return f
            if int(f.Number) == int(label):
                return f
        raise KeyError("attempt to get nonexisting beam with key {}".format(label))
    def GetAndClearWarnings(self):
        return list()
    @property
    def patient_info(self):
        return dict([(k,"anonymized") for k in beamset_info.patient_attrs])
    @property
    def plan_info(self):
        return dict([(k,"anonymized") for k in beamset_info.plan_attrs])
    @property
    def bs_info(self):
        bs = dict([(k,"anonymized") for k in beamset_info.bs_attrs])
        #bs_attrs = [ "Number Of Beams", "RT Plan Label", "Prescription Dose",
        #             "Target ROI Name", "Radiation Type", "Treatment Machine(s)"]
        bs["Number Of Beams"] = str(len(self.fields))
        bs["RT Plan Label"] = self.name
        bs["Radiation Type"] = ", ".join(set([str(beam.RadiationType) for beam in self.fields]))
        bs["Treatment Machine(s)"] = ", ".join(set([str(beam.TreatmentMachineName) for beam in self.fields]))
        return bs
    @property
    def beam_numbers(self):
        # NOTE 1: this is expected to be a list of STRINGS, not integers...
        # NOTE 2: since Gate/MC2 pencil beam files only store the beam numbers, names=numbers. :-)
        return [str(f.Number) for f in self.fields]
    @property
    def beam_names(self):
        return [str(f.Name) for f in self.fields]
    @property
    def mswtot(self):
        return np.sum([f.mswtot for f in self.fields])
    @property
    def nspots(self):
        return np.sum([f.nspots for f in self.fields])
    @property
    def beams(self):
        return self.fields
    @property
    def nbeams(self):
        return len(self.fields)
    @property
    def target_ROI_name(self):
        return ""
    @property
    def uid(self):
        return "NA"
    @property
    def Nfractions(self):
        return int(self.n_fractions)
    def _skippable(self,lin):
        return len(lin)==0 or lin[0]=='#'
    def _read_plan_name(self,lin):
        self.name = str(lin)
        #print(f"name is {lin}")
        self._next_ = self._read_n_fractions
    def _read_n_fractions(self,lin):
        self.n_fractions = int(lin)
        #print(f"n fractions is {lin}")
        self._next_ = self._read_fraction_ID
    def _read_fraction_ID(self,lin):
        self.n_fraction_ID = str(lin)
        #print(f"fractions ID is {lin}")
        self._next_ = self._read_n_fields
    def _read_n_fields(self,lin):
        self.n_fields = int(lin)
        #print(f"N fields is {lin}")
        #self.field_IDs = list()
        self._next_ = self._read_field_ID
    def _read_field_ID(self,lin):
        fid = str(lin)
        for f in self.fields:
            if f.id == fid:
                #print(f"going to work with field ID {lin}")
                self.current_field = f
                self._next_ = self._read_radiation_type
                return
        #fid,bmlname,radtype='proton',gantry_angle=0.,patient_angle=0.):
        self.fields.append(gate_pbs_field(fid,self.bml))
        #print(f"created new field with ID {lin}")
        #self.current_field = self.fields[-1]
        if self.n_fields == len(self.fields):
            self._next_ = self._read_msw
    def _read_radiation_type(self,lin):
        radtype = str(lin).upper()
        if radtype == 'ION':
            radtype = 'ION_6_12_6'
        if radtype not in ['PROTON','ION_6_12_6']:
            logger.debug("old type MC2 plan file without radiation type?")
            try:
                self._read_msw(lin)
                return
            except:
                raise ValueError(f'unknown radtype {radtype} in plan file')
        self.current_field.radiation_type = radtype
        self._next_ = self._read_msw
    def _read_msw(self,lin):
        msw = float(lin)
        if bool(self.current_control_point):
            self.current_control_point.msw = msw
            #print(f"icp cumulative MSW is {lin}")
            self._next_ = self._read_energy
        elif bool(self.current_field):
            self.current_field.msw = msw
            #print(f"field MSW is {lin}")
            self._next_ = self._read_gantry_angle
        else:
            self.total_msw = float(lin)
            #print(f"total MSW is {lin}")
            self._next_ = self._read_field_ID
    def _read_gantry_angle(self,lin):
        self.current_field.gantry_angle = float(lin)
        #print(f"gantry angle is {lin}")
        self._next_ = self._read_patient_angle
    def _read_patient_angle(self,lin):
        self.current_field.patient_angle = float(lin)
        #print(f"patient angle is {lin}")
        self._next_ = self._read_isocenter_position
    def _read_isocenter_position(self,lin):
        isopos = np.array([float(w) for w in lin.split()])
        if len(isopos)!=3:
            raise ValueError(f"expected ISO center with three float values, got something else: '{lin}'")
        self.current_field.IsoCenter = isopos
        self._next_ = self._read_n_control_points
    def _read_n_control_points(self,lin):
        if lin in self.bml.rs_labels:
            self.current_field.range_shifter_ids.append(lin)
            # next line shoult contain the word 'binary'
            self.expect_binary = True
            return
        elif lin.lower() == 'binary':
            # currently we do not support any other range shifters
            if self.expect_binary:
                # got it
                self.expect_binary = False
            else:
                logger.warn("Hmmmmm unexpectedly got 'binary' keyword, ignoring for now...")
            return
        elif self.expect_binary:
            raise ValueError('got unknown range shifter type "{lin}"')
        self.current_field.n_control_points = int(lin)
        self._next_ = self._read_control_point_index
    def _read_control_point_index(self,lin):
        i = int(lin)
        iexp = 1+len(self.current_field.control_points)
        if i != iexp:
            raise ValueError(f"expected control point index {iexp}, got index {i} instead")
        self.current_field.control_points.append(gate_pbs_control_point(i))
        self.current_control_point = self.current_field.control_points[-1]
        self._next_ = self._read_spot_tune_id
    def _read_spot_tune_id(self,lin):
        self.current_control_point.spot_tune_id = str(lin)
        self._next_ = self._read_msw
    def _read_energy(self,lin):
        self.current_control_point.energy = float(lin)
        if self.current_field.NumberOfRangeShifters>0:
            self._next_ = self._read_in_out
        else:
            self._next_ = self._read_n_spots
    def _read_in_out(self,lin):
        if lin.upper()!='IN':
            logger.error("expected RS 'IN' line, got {lin} instead")
        self._next_ = self._read_iso_to_rs_distance
    def _read_iso_to_rs_distance(self,lin):
        iso2rs_dist = float(lin)
        logger.debug(f"ignoring iso 2 rs distance {iso2rs_dist}")
        self._next_ = self._read_rs_wet
    def _read_rs_wet(self,lin):
        rs_wet = float(lin)
        logger.debug(f"ignoring range shifter WET {rs_wet}")
        self._next_ = self._read_n_spots
    def _read_n_spots(self,lin):
        nspots = int(lin)
        if nspots <=0:
            fid = self.current_field.id
            cid = self.current_control_point.index
            raise ValueError(f"expected positive number of spots for field ID {fid} control point index {cid}, got {nspots} instead")
        self.current_control_point.n_spots = int(lin)
        self._next_ = self._read_spot
    def _read_spot(self,lin):
        tmp = [float(w) for w in lin.split()]
        if len(tmp)!=3:
            raise ValueError(f"expected spot with three float values (x y w), got something else: '{lin}'")
        self.current_control_point.spots.append(gate_pbs_spot(*tmp))
        if len(self.current_control_point.spots) < self.current_control_point.n_spots:
            self._next_ = self._read_spot
        else:
            self.current_control_point.spots = np.array(self.current_control_point.spots)
            self.current_control_point = None
            if len(self.current_field.control_points) < self.current_field.n_control_points:
                self._next_ = self._read_control_point_index
            elif self.current_field.id != self.fields[-1].id:
                self.current_field = None
                self._next_ = self._read_field_ID
            else:
                self._next_ = self._read_nothing
    def _read_nothing(self,lin):
        msg="UNEXPECTED extra text after plan was already completely parsed: {lin}"
        logger.error(msg)
        raise ValueError(msg)


class gate_pbs_plan_file:
    """
    Class to write GATE plan descriptions from arbitrary spot specifications
    produced e.g. by a TPS such as RayStation.
    """
    def __init__(self,planpath,gangle=0.,allow0=False):
        self.planpath = planpath
        self.filename = os.path.basename(planpath)
        self.planname = self.filename[:-4]
        self.nspots_written = 0
        logger.debug("created plan={}".format(self.planname))
        self.msw_cumsum = 0.
        self.nlayers = 0
        self.nspots = 0
        self.nspots_ignored = 0
        self.wrote_header = False
        self.allow0 = allow0
    def print_summary(self):
        logger.info("plan={} in file={}".format(self.planname,self.planpath))
        if self.wrote_header:
            logger.info("wrote header, {} layers and {} spots, {} spots were ignored, msw = {}".format(self.nlayers,self.nspots,self.nspots_ignored,self.msw_cumsum))
        elif self.nlayers>0 or self.nspots>0 or self.nspots_ignored>0:
            logger.error("did NOT write header, but got nlayer={}, nspots={}, nspots_ignored={}, which SHOULD all be zero...".format(self.nlayers,self.nspots,self.nspots_ignored))
        else:
            logger.info("did write anything into plan file")
    def import_from(self,plan):
        syscfg = system_configuration.getInstance()
        self.planname = plan.name
        logger.debug("STARTING filling plan {} into GATE plan file {}".format(self.planname,self.filename))
        self.write_file_header(plan.mswtot,plan.beams)
        for j,f in enumerate(plan.beams):
            # clitkDicomRT2Gate uses beam *number*, but Alessio says that *name* is better, more reliable
            self.write_field_header(f)
            def_msw_scaling=syscfg['msw scaling']["default"]
            dose_corr_key=(f.TreatmentMachineName+"_"+f.RadiationType).lower()
            msw_scaling=syscfg['msw scaling'].get(dose_corr_key,def_msw_scaling)
            print(msw_scaling)
            msw_corr_slope = msw_scaling[0]
            msw_corr_offset = msw_scaling[1]
            

            for i,l in enumerate(f.layers):
                self.write_layer_header(i,l)
                k_e = msw_corr_slope*l.energy + msw_corr_offset
                for spot in l.spots:
                    self.write_spot(spot, lambda x : k_e*x)
        self.filehandle.close()
        logger.debug("FINISHED filling plan from {}".format(plan.name))
    def write_file_header(self,mswtot,fields=[1]):
        if self.wrote_header:
            logger.error("FILE HEADER WRITTEN MORE THAN ONCE!")
        self.filehandle=open(self.planpath,"w")

        self.filehandle.write(
"""#TREATMENT-PLAN-DESCRIPTION
#PlanName
{name:s}
#NumberOfFractions
1
##FractionID
1
##NumberOfFields
{nfields:d}
""".format(name=self.planname,nfields=len(fields)))
        for field in fields:
            # clitkDicomRT2Gate uses beam *number*, but Alessio says that *name* is better, more reliable
            self.filehandle.write("###FieldsID\n{}\n".format(field.number))
        self.filehandle.write("#TotalMetersetWeightOfAllFields\n{0:f}\n\n".format(mswtot))
        self.wrote_header = True

    def write_field_header(self,field):
        isoc=field.IsoCenter
        self.filehandle.write(
"""#FIELD-DESCRIPTION
###FieldID
{fid}
###FinalCumulativeMeterSetWeight
{mswtot:g}
###GantryAngle (in degrees)
{ga:g}
###PatientSupportAngle
{psa}
###IsocenterPosition
{isox:g} {isoy:g} {isoz:g}
###NumberOfControlPoints
{ncp:d}
#SPOTS-DESCRIPTION
""".format(fid=field.Number,
           mswtot=field.mswtot,
           ga=field.gantry_angle,
           psa=field.PatientSupportAngle,
           isox=isoc[0],
           isoy=isoc[1],
           isoz=isoc[2],
           ncp=field.nlayers,
           ))
        logger.debug("wrote field header for field={} in plan={}".format(field.Number,self.planname))
        self.msw_cumsum = 0.
    def write_layer_header(self,cpi,layer,t0=None,t1=None,nspot=None):
        if hasattr(layer,"tuneID"):
            tuneID=layer.tuneID
        else:
            tuneID="3.0"
        if nspot is None:
            nspot=len(layer.get_spots(t0,t1))
            logger.debug('getting nspots={} between t0={} and t1={} from LAYER'.format(nspot,t0,t1))
        else:
            logger.debug('getting nspots={} CALLER'.format(nspot))
        self.filehandle.write(
"""####ControlPointIndex
{cpi:d}
####SpotTuneID
{stid:s}
####CumulativeMetersetWeight
{mswtot:g}
####Energy (MeV)
{energy:g}
####NbOfScannedSpots
{nspot:g}
####X Y Weight (spot position at isocenter in mm, with weight in MU (default) or number of protons "setSpotIntensityAsNbProtons true")
""".format(cpi=cpi,stid=tuneID,mswtot=self.msw_cumsum,energy=layer.energy,nspot=nspot))
        self.nlayers += 1
        logger.debug("wrote layer header {} for plan={}, now nlayers={}".format(cpi,self.planname,self.nlayers))
    def write_spot(self,spot,tstart=None,tend=None, conversion=lambda x:x):
        msw = spot.get_msw(tstart, tend)
        if self.allow0 or msw>0:
            self.nspots_written += 1
            self.filehandle.write("{0:g} {1:g} {2:g}\n".format(spot.xiec,spot.yiec,conversion(msw)))
            self.msw_cumsum += msw
            self.nspots += 1
        else:
            self.nspots_ignored += 1


################################################################################
# UNIT TESTS
################################################################################

import unittest

class test_gate_pbs_plan_reading(unittest.TestCase):
    def test_read(self):
        gpp = gate_pbs_plan(self.good_test_plan)
        self.assertTrue(True)
    def tearDown(self):
        os.remove(self.good_test_plan)
    def setUp(self):
        self.good_test_plan = ".test.gatepbs123.txt"
        with open(self.good_test_plan,"w") as testplanfile:
            testplanfile.write("""#TREATMENT-PLAN-DESCRIPTION
#PlanName
PlanPencil
#NumberOfFractions
30
##FractionID
1
##NumberOfFields
2
###FieldsID
1
###FieldsID
2
#TotalMetersetWeightOfAllFields
13.7
 
#FIELD-DESCRIPTION
###FieldID
1
###FinalCumulativeMeterSetWeight
8.0
###GantryAngle
0
###PatientSupportAngle
0
###IsocenterPosition
106.0195      99.77137      169.7413
###NumberOfControlPoints
4
 
#SPOTS-DESCRIPTION
####ControlPointIndex
1
####SpotTunnedID
1
####CumulativeMetersetWeight
2.7
####Energy (MeV)
146.3
####NbOfScannedSpots
3
####X Y Weight
8.895 -14.735 0.4
3.026 -14.735 1.5
-2.842 -14.735 0.8
####ControlPointIndex
2
####SpotTunnedID
1
####CumulativeMetersetWeight
4.4
####Energy (MeV)
143
####NbOfScannedSpots
4
####X Y Weight
9.026 -4.684 0.1
-2.759 -4.684 0.1
0.187 -9.787 0.6
6.079 -9.787 0.9
####ControlPointIndex
3
####SpotTunnedID
1
####CumulativeMetersetWeight
6.9
####Energy (MeV)
139.7
####NbOfScannedSpots
2
####X Y Weight
9.16 -4.8 1
3.243 -4.8 1.5
####ControlPointIndex
4
####SpotTunnedID
1
####CumulativeMetersetWeight
8.0
####Energy (MeV)
136.5
####NbOfScannedSpots
1
####X Y Weight
3.413 -4.98 1.1
 
#FIELD-DESCRIPTION
###FieldID
2
###FinalCumulativeMeterSetWeight
5.7
###GantryAngle
90
###PatientSupportAngle
0
###IsocenterPosition
106.0195      99.77137      169.7413
###NumberOfControlPoints
3
 
#SPOTS-DESCRIPTION
####ControlPointIndex
1
####SpotTunnedID
1
####CumulativeMetersetWeight
0.6
####Energy (MeV)
125.4
####NbOfScannedSpots
3
####X Y Weight
0.589 -0.959 0.1
6.789 -0.959 0.2
12.99 -0.959 0.3
####ControlPointIndex
2
####SpotTunnedID
1
####CumulativeMetersetWeight
2.8
####Energy (MeV)
122.6
####NbOfScannedSpots
4
####X Y Weight
6.931 -1.069 0.4
13.16 -1.069 0.5
16.274 -6.464 0.6
10.045 -6.464 0.7
####ControlPointIndex
3
####SpotTunnedID
1
####CumulativeMetersetWeight
5.7
####Energy (MeV)
119.8
####NbOfScannedSpots
2
####X Y Weight
-8.584 15.084 1.5
-11.711 9.67 1.4
""")

# vim: set et softtabstop=4 sw=4 smartindent:
