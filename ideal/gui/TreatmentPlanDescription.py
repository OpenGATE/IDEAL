# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from impl.beamline_model import beamline_model
from impl.system_configuration import system_configuration
import functools
import logging
logger = logging.getLogger(__name__)

def label_combinations(available,used):
    sa=set(available)
    su=set(used)
    if not su.issubset(sa):
        logger.error("incompatible sets of available and used labels")
        logger.error("the available set should be a superset of the used ones")
        return []
    iu=0
    na=len(sa)
    nc=2**na
    combs=list()
    for i in range(nc):
        comb=list()
        for j,label in enumerate(sa):
            if i&(2**j)==2**j:
                comb.append(label)
        combs.append(comb)
        if set(comb)==su:
            iu=i
    return combs,iu

class TabTPdescription( QtWidgets.QWidget ):
    def __init__(self,details):
        QtWidgets.QWidget.__init__(self)
        self.details = details
        details.Subscribe(self)
        details.Subscribe(self,"CTPHANTOM") # with PHANTOM enable override features
        self.TPlayout = QtWidgets.QVBoxLayout()
        self.beamTable = QtWidgets.QTableWidget()
        self.headers=["Beam Name",
                      "Radiation Type",
                      "Treatment Machine",
                      "Patient Support Angle [deg]",
                      #"IsoCenter Name",
                      "x | R-L [mm]","y | A-P [mm]","z | I-S [mm]",
                      #"Snout ID","Snout Pos [mm]", "Gap [mm]", "Gantry [deg]",
                      "Snout ID","Snout Pos [mm]", "Gantry [deg]",
                      "Range Shifter", "Range Modulators",
                      "Spot Tune ID",
                      "Nr. of energy layers",
                      "NP (1e6 / fx)", "Spot min", "Spot max" ]
        self.beamTable.setRowCount(0)
        self.beamTable.setColumnCount(len(self.headers))
        self.beamTable.setHorizontalHeaderLabels(self.headers)
        self.TPlayout.addWidget(self.beamTable)
        self.setLayout(self.TPlayout)
        self.beamTable.itemDoubleClicked.connect(self.HandleOverrideRequest)
        self.override_cache=dict()
        self.rs_combos=dict()
        self.rm_combos=dict()
        self.rl_spinbox=dict()
        self.ap_spinbox=dict()
        self.is_spinbox=dict()
        #self.phantom_overrideDialog = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Cancel)
        #self.phantom_overrideDialog.accepted.connect(self.ApplyOverride)
        #self.phantom_overrideDialog.rejected.connect(self.IgnoreOverride)
    def HandleOverrideRequest(self,tablewidget):
        logger.debug("got override request for row={} column={}".format(tablewidget.row(),tablewidget.column()))
        if self.details.run_with_CT_geometry:
            logger.debug("we are in CT geometry => ignore")
            return
        logger.debug("we are in PHANTOM geometry => show dialog")
        #self.phantom_overrideDialog.show()
    def ApplyOverride(self):
        logger.debug("overriding")
        #self.phantom_overrideDialog.hide()
    def IgnoreOverride(self):
        logger.debug("override canceled")
        #self.phantom_overrideDialog.hide()
    def update_ctphantom(self):
        logger.debug("update CT/Phantom status")
        jrs=self.headers.index("Range Shifter")
        jrm=self.headers.index("Range Modulators")
        jrl=self.headers.index("x | R-L [mm]")
        jap=self.headers.index("y | A-P [mm]")
        jis=self.headers.index("z | I-S [mm]")
        logger.debug("enable overrides")
        ctgeometry = self.details.run_with_CT_geometry
        for i,beam in enumerate(self.details.bs_info.beams):
            rs_combo = self.beamTable.cellWidget(i,jrs)
            rm_combo = self.beamTable.cellWidget(i,jrm)
            rl_spinbox = self.beamTable.cellWidget(i,jrl)
            ap_spinbox = self.beamTable.cellWidget(i,jap)
            is_spinbox = self.beamTable.cellWidget(i,jis)
            isoC = beam.IsoCenter if ctgeometry else self.details.PhantomISOinMM(beam.Name)
            if rs_combo is None:
                logger.error("PROGRAMMING ERROR: didn't get RS combo widget back")
                raise RuntimeError("PROGRAMMING ERROR: didn't get RS combo widget back")
            if rm_combo is None:
                logger.error("PROGRAMMING ERROR: didn't get RM combo widget back")
                raise RuntimeError("PROGRAMMING ERROR: didn't get RM combo widget back")
            if ctgeometry:
                logger.debug("disable & remove overrides, back to plan settings")
                rs_combo.setCurrentIndex(self.override_cache[beam.Name]["rsi"])
                rm_combo.setCurrentIndex(self.override_cache[beam.Name]["rmi"])
            rm_combo.setEnabled(not ctgeometry)
            rs_combo.setEnabled(not ctgeometry)
            rl_spinbox.setValue(isoC[0])
            rl_spinbox.setReadOnly(ctgeometry)
            ap_spinbox.setValue(isoC[1])
            ap_spinbox.setReadOnly(ctgeometry)
            is_spinbox.setValue(isoC[2])
            is_spinbox.setReadOnly(ctgeometry)
        if ctgeometry:
            self.details.ResetOverrides()
    def PlanUpdate(self):
        #beams = self.details.rp_dataset.IonBeamSequence
        beams = self.details.bs_info.beams
        ctgeometry = self.details.run_with_CT_geometry
        logger.debug('updating {} beams'.format(len(beams)))
        self.beamTable.setRowCount(len(beams))
        self.override_cache = dict()
        self.rs_combos = dict()
        self.rm_combos = dict()
        syscfg = system_configuration.getInstance()
        for i,beam in enumerate(beams):
            bml_name = beam.TreatmentMachineName
            bml = beamline_model.get_beamline_model_data(bml_name, syscfg['beamlines'])
            logger.debug('updating beam {}'.format(i))
            if not beam.PrimaryDosimeterUnit == "NP":
                raise ValueError("primary dosimetry unit should be 'NP', other units are not (yet) supported.")
            #icps = beam.layers
            isoC = beam.IsoCenter if ctgeometry else self.details.PhantomISOinMM(beam.Name)
            j=self.headers.index("x | R-L [mm]")
            #self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(str(isoC[0])))
            self.rl_spinbox[beam.Name] = QtWidgets.QDoubleSpinBox()
            self.rl_spinbox[beam.Name].setRange(-1000.,+1000.)
            self.rl_spinbox[beam.Name].setSingleStep(5.0)
            self.rl_spinbox[beam.Name].setValue(isoC[0])
            self.rl_spinbox[beam.Name].setReadOnly(ctgeometry)
            self.beamTable.setCellWidget(i,j,self.rl_spinbox[beam.Name])
            j=self.headers.index("y | A-P [mm]")
            #self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(str(isoC[2])))
            self.ap_spinbox[beam.Name] = QtWidgets.QDoubleSpinBox()
            self.ap_spinbox[beam.Name].setRange(-1000.,+1000.)
            self.ap_spinbox[beam.Name].setSingleStep(5.0)
            self.ap_spinbox[beam.Name].setValue(isoC[2])
            self.ap_spinbox[beam.Name].setReadOnly(ctgeometry)
            self.beamTable.setCellWidget(i,j,self.ap_spinbox[beam.Name])
            j=self.headers.index("z | I-S [mm]")
            #self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(str(isoC[1])))
            self.is_spinbox[beam.Name] = QtWidgets.QDoubleSpinBox()
            self.is_spinbox[beam.Name].setRange(-1000.,+1000.)
            self.is_spinbox[beam.Name].setSingleStep(5.0)
            self.is_spinbox[beam.Name].setValue(isoC[1])
            self.is_spinbox[beam.Name].setReadOnly(ctgeometry)
            self.beamTable.setCellWidget(i,j,self.is_spinbox[beam.Name])
            #j=self.headers.index("IsoCenter Name")
            #self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem("(TBD)"))
            j=self.headers.index("Patient Support Angle [deg]")
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(str(beam.PatientSupportAngle) if ctgeometry else "NA"))
            #j=self.headers.index("Gap [mm]")
            #self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem("(TBD)"))
            j=self.headers.index("Beam Name")
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(beam.Name))
            j=self.headers.index("Radiation Type")
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(beam.RadiationType))
            j=self.headers.index("Treatment Machine")
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(bml_name))
            j=self.headers.index("Snout ID")
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(beam.SnoutID))
            j=self.headers.index("Snout Pos [mm]")
            logger.debug('halfway done with updating beam {}'.format(i))
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(str(beam.SnoutPosition)))
            j=self.headers.index("Gantry [deg]")
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(str(beam.gantry_angle)))
            j=self.headers.index("Nr. of energy layers")
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(str(beam.NumberOfEnergies)))
            j=self.headers.index("NP (1e6 / fx)")
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(str(float(beam.FinalCumulativeMetersetWeight)/1.0e6)))
            weights = [float(w)/1.0e6 for l in beam.layers for w in l.weights if w>0]
            j=self.headers.index("Spot min")
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(str(min(weights))))
            j=self.headers.index("Spot max")
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(str(max(weights))))
            j=self.headers.index("Spot Tune ID")
            tunes = set([l.tuneID for l in beam.layers])
            if len(tunes)>1:
                logger.warn("{} spot tune IDs for beam {}".format(len(tunes),str(beam.BeamName)))
            self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem(tunes.pop()))
            #self.beamTable.setItem(i,j,QtWidgets.QTableWidgetItem("NO" if beam.NumberOfRangeShifters==0 else "YES"))
            logger.debug("adding RS combobox to TP table")
            rs_options,irs = label_combinations(bml.rs_labels,beam.RangeShifterIDs)
            self.rs_combos[beam.Name] = QtWidgets.QComboBox()
            self.rs_combos[beam.Name].addItems(["NONE"]+["+".join(opt) for opt in rs_options[1:]])
            self.rs_combos[beam.Name].setCurrentIndex(irs)
            self.rs_combos[beam.Name].setEnabled(not ctgeometry)
            j=self.headers.index("Range Shifter")
            self.beamTable.setCellWidget(i,j,self.rs_combos[beam.Name])
            logger.debug("adding RM combobox to TP table")
            rm_options,irm = label_combinations(bml.rm_labels,beam.RangeModulatorIDs)
            self.rm_combos[beam.Name] = QtWidgets.QComboBox()
            self.rm_combos[beam.Name].addItems(["NONE"]+["+".join(opt) for opt in rm_options[1:]])
            self.rm_combos[beam.Name].setCurrentIndex(irm)
            self.rm_combos[beam.Name].setEnabled(not ctgeometry)
            j=self.headers.index("Range Modulators")
            self.beamTable.setCellWidget(i,j,self.rm_combos[beam.Name])
            self.override_cache[beam.Name]=dict(rsa=rs_options,rsi=irs,rsc=self.rs_combos[beam.Name],rma=rm_options,rmi=irm,rmc=self.rm_combos[beam.Name])
            for j in range(len(self.headers)):
                item=self.beamTable.item(i,j)
                if item:
                    item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.rs_combos[beam.Name].currentIndexChanged[int].connect( functools.partial(self.UpdateRSOverride,beam.Name) )
            self.rm_combos[beam.Name].currentIndexChanged[int].connect( functools.partial(self.UpdateRMOverride,beam.Name) )
            self.rl_spinbox[beam.Name].editingFinished.connect( functools.partial(self.UpdatePhantomIsoOverride,beam.Name) )
            self.ap_spinbox[beam.Name].editingFinished.connect( functools.partial(self.UpdatePhantomIsoOverride,beam.Name) )
            self.is_spinbox[beam.Name].editingFinished.connect( functools.partial(self.UpdatePhantomIsoOverride,beam.Name) )
            logger.debug('done with updating beam {}'.format(i))
        #QtWidgets.QWidget.update(self)
    def UpdatePhantomIsoOverride(self,beamname):
        new_rl = self.rl_spinbox[beamname].value() # x
        new_ap = self.ap_spinbox[beamname].value() # y
        new_is = self.is_spinbox[beamname].value() # z
        self.details.UpdatePhantomIsoOverride(beamname,(new_rl,new_ap,new_is))
    def UpdateRSOverride(self,beamname,irs):
        rs_options = self.override_cache[beamname]["rsa"]
        rs_plan = self.override_cache[beamname]["rsi"]
        if irs<0 or irs>=len(rs_options):
            logger.debug("PROGRAMMING ERROR in rs override stuff")
            return
        logger.debug("{}: new RS choice is {} the TPS setting".format(beamname,"the same as" if rs_plan==irs else "different from"))
        self.details.UpdateRSOverride(beamname,rs_options[irs])
    def UpdateRMOverride(self,beamname,irm):
        rm_options = self.override_cache[beamname]["rma"]
        rm_plan = self.override_cache[beamname]["rmi"]
        if irm<0 or irm>=len(rm_options):
            logger.debug("PROGRAMMING ERROR in rm override stuff")
            return
        logger.debug("{}: new RM choice is {} the TPS setting".format(beamname,"the same as" if rm_plan==irm else "different from"))
        self.details.UpdateRMOverride(beamname,rm_options[irm])

# vim: set et softtabstop=4 sw=4 smartindent:
