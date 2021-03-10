# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

from PyQt5 import QtWidgets
from PyQt5 import QtCore
import logging
logger = logging.getLogger(__name__)
from impl.idc_enum_types import MCStatType
from impl.idc_enum_types import MCPriorityType
from impl.job_executor import job_executor
from impl.hlut_conf import hlut_conf
from impl.system_configuration import system_configuration
import os
import numpy as np

class IDCDoseGridSettings( QtWidgets.QWidget ):
    def __init__(self,details):
        QtWidgets.QWidget.__init__(self)
        self.details = details
        details.Subscribe(self)
        details.Subscribe(self,"CTPHANTOM")
        self._assume_CT = details.run_with_CT_geometry
        self.cell = [-1,-1]
        self.vBoxLayoutIDCGridSettings = QtWidgets.QVBoxLayout()
        self.buttonDefault = QtWidgets.QPushButton("Default settings")
        self.vBoxLayoutIDCGridSettings.addWidget(self.buttonDefault)
        self.gridSettingsTable = QtWidgets.QTableWidget()
        self.gridSettingsTable.setRowCount(4)
        self.gridSettingsTable.setColumnCount(3)
        self.gridSettingsTable.setHorizontalHeaderLabels(["x | R-L", "y | A-P", "z | I-S"])
        self.gridSettingsTable.setVerticalHeaderLabels(["N voxels", "Grid size [mm]", "resolution [mm]", "center [mm]"])
        # For some reason, the none of the currentCellChanged and similar signals seem to work
        # on a spinbox widget in the tablewidget cell.
        self.iRL = 0 # x
        self.iAP = 1 # y
        self.iIS = 2 # z
        self.jNVOX = 0 # number of voxels
        self.jSIZE = 1 # size in mm
        self.jRESO = 2 # resolution (mm per voxel)
        self.jORIG = 3 # origin (arbitrary reference point)
        # "minimum dose grid resolution [mm]":0.1,
        for c,cdg in zip([self.iRL,self.iAP,self.iIS],
                         [self.ChangeDoseGridRL, self.ChangeDoseGridAP, self.ChangeDoseGridIS]):
            nvoxelbox = QtWidgets.QSpinBox(self)
            #resbox.setRange(details.min_dose_res,details.max_dose_res)
            nvoxelbox.setRange(1,1000)
            #resbox.setSingleStep(details.dose_step)
            nvoxelbox.setValue(100)
            nvoxelbox.setReadOnly(False)
            self.gridSettingsTable.setCellWidget(self.jNVOX,c,nvoxelbox)
            nvoxelbox.editingFinished.connect(cdg)
            #resbox.valueChanged[float].connect(self.ChangeDoseGrid)
            self.gridSettingsTable.setItem(self.jSIZE,c,QtWidgets.QTableWidgetItem("1.0"))
            self.gridSettingsTable.setItem(self.jRESO,c,QtWidgets.QTableWidgetItem("1.0"))
            self.gridSettingsTable.setItem(self.jORIG,c,QtWidgets.QTableWidgetItem("0.0"))
            flag = QtCore.Qt.ItemIsEnabled if self._assume_CT else QtCore.Qt.NoItemFlags
            for r in range(1,4):
                self.gridSettingsTable.item(r,c).setFlags(flag)
        self.vBoxLayoutIDCGridSettings.addWidget(self.gridSettingsTable)
        self.setLayout(self.vBoxLayoutIDCGridSettings)
        self.buttonDefault.clicked.connect(self.SetDoseGridBackToDefault)
    def PlanUpdate(self):
        if not self.details.have_dose_grid:
            return
        nvoxels = np.array(self.details.GetNVoxels())
        if self.details.run_with_CT_geometry:
            self.gridSettingsTable.setRowCount(4)
            self.gridSettingsTable.setVerticalHeaderLabels(["N voxels", "Grid size [mm]", "resolution [mm]", "center [mm]"])
            nmaxvoxels=np.maximum(nvoxels,np.ceil(self.details.dosegrid_size/self.details.min_dose_res).astype(int))
        else:
            beam_names = self.details.beam_names
            self.gridSettingsTable.setRowCount(3+len(beam_names))
            self.gridSettingsTable.setVerticalHeaderLabels(["N voxels", "Grid size [mm]", "resolution [mm]"] + ["{} center [mm]".format(name) for name in beam_names])
            nmaxvoxels=np.maximum(nvoxels,np.maximum(1000*np.ones(3),np.ceil(self.details.dosegrid_size/self.details.min_dose_res).astype(int)))
        logger.debug("nvoxels={}".format(nvoxels))
        logger.debug("nmaxvoxels={}".format(nmaxvoxels))
        # TODO: this looks a little dumb.
        # TODO: currently using patient (CT) coordinate system
        # TODO: if client wishes IEC instead, this should be easy to transform
        self.gridSettingsTable.cellWidget(self.jNVOX,self.iRL).setValue(nvoxels[self.iRL])
        self.gridSettingsTable.cellWidget(self.jNVOX,self.iRL).setRange(1,nmaxvoxels[self.iRL])
        self.gridSettingsTable.cellWidget(self.jNVOX,self.iRL).setToolTip("max={}".format(nmaxvoxels[self.iRL]))
        self.gridSettingsTable.cellWidget(self.jNVOX,self.iAP).setValue(nvoxels[self.iAP])
        self.gridSettingsTable.cellWidget(self.jNVOX,self.iAP).setRange(1,nmaxvoxels[self.iAP])
        self.gridSettingsTable.cellWidget(self.jNVOX,self.iAP).setToolTip("max={}".format(nmaxvoxels[self.iAP]))
        self.gridSettingsTable.cellWidget(self.jNVOX,self.iIS).setValue(nvoxels[self.iIS])
        self.gridSettingsTable.cellWidget(self.jNVOX,self.iIS).setRange(1,nmaxvoxels[self.iIS])
        self.gridSettingsTable.cellWidget(self.jNVOX,self.iIS).setToolTip("max={}".format(nmaxvoxels[self.iIS]))
        size = np.round(self.details.GetDoseSize(),decimals=3) # TODO: make number of decimals configurable in sysconf.cfg?
        self.gridSettingsTable.item(self.jSIZE,self.iRL).setText(str(size[self.iRL]))
        self.gridSettingsTable.item(self.jSIZE,self.iAP).setText(str(size[self.iAP]))
        self.gridSettingsTable.item(self.jSIZE,self.iIS).setText(str(size[self.iIS]))
        res = np.round(self.details.GetDoseResolution(),decimals=3)  # TODO: make number of decimals configurable in sysconf.cfg?
        self.gridSettingsTable.item(self.jRESO,self.iRL).setText(str(res[self.iRL]))
        self.gridSettingsTable.item(self.jRESO,self.iAP).setText(str(res[self.iAP]))
        self.gridSettingsTable.item(self.jRESO,self.iIS).setText(str(res[self.iIS]))
        if self.details.run_with_CT_geometry:
            center = np.round(self.details.GetDoseCenter(),decimals=3) # TODO: make number of decimals configurable in sysconf.cfg?
            self.gridSettingsTable.item(self.jORIG,self.iRL).setText(str(center[self.iRL]))
            self.gridSettingsTable.item(self.jORIG,self.iAP).setText(str(center[self.iAP]))
            self.gridSettingsTable.item(self.jORIG,self.iIS).setText(str(center[self.iIS]))
        else:
            for i,name in enumerate(self.details.beam_names):
                center = np.round(-1*self.details.PhantomISOinMM(name),decimals=3) # TODO: make number of decimals configurable in sysconf.cfg?
                self.gridSettingsTable.setItem(self.jORIG+i,self.iRL,QtWidgets.QTableWidgetItem(str(center[self.iRL])))
                self.gridSettingsTable.setItem(self.jORIG+i,self.iAP,QtWidgets.QTableWidgetItem(str(center[self.iAP])))
                self.gridSettingsTable.setItem(self.jORIG+i,self.iIS,QtWidgets.QTableWidgetItem(str(center[self.iIS])))
        flag = QtCore.Qt.ItemIsEnabled if self._assume_CT else QtCore.Qt.NoItemFlags
        for r in range(1,self.gridSettingsTable.rowCount()):
            for c in [self.iRL,self.iIS,self.iAP]:
                self.gridSettingsTable.item(r,c).setFlags(flag)
        #QtWidgets.QWidget.update(self)
    def update_ctphantom(self):
        self._assume_CT = self.details.run_with_CT_geometry
        self.PlanUpdate()
    def ChangeDoseGrid(self,c):
        newval = self.gridSettingsTable.cellWidget(self.jNVOX,c).value()
        logger.debug("change dose grid called with c={} and newval={}".format(c,newval))
        self.details.UpdateDoseGridResolution(c,newval)
        self.PlanUpdate()
    def ChangeDoseGridRL(self): # x
        self.ChangeDoseGrid(self.iRL)
    def ChangeDoseGridAP(self): # y
        self.ChangeDoseGrid(self.iAP)
    def ChangeDoseGridIS(self): # z
        self.ChangeDoseGrid(self.iIS)
    def SetDoseGridBackToDefault(self):
        self.details.SetDefaultDoseGridSettings()
        logger.debug("set dose grid back to default")
        self.PlanUpdate()

class IDCMCStatistics( QtWidgets.QWidget ):
    def __init__(self,details):
        QtWidgets.QWidget.__init__(self)
        self.details = details
        details.Subscribe(self)
        self.quantityButtonGroup = QtWidgets.QButtonGroup()
        self.quantityButtonGroup.setExclusive(True)
        self.vBoxLayoutIDCMCStatistics = QtWidgets.QVBoxLayout()
        self.quantitySelection = QtWidgets.QWidget()
        self.layoutQuantitySelection = QtWidgets.QHBoxLayout()
        self.spinboxes = list()
        self.checkboxes = list()
        syscfg = system_configuration.getInstance()
        self.ncores = syscfg['number of cores']

        for imc in range(MCStatType.NTypes):
            mcmin,mcval,mcmax,mcstep,mcdef = syscfg[MCStatType.cfglabels[imc]]
            labelMCStat = QtWidgets.QLabel( MCStatType.guilabels[imc] )
            checkboxMCStat = QtWidgets.QCheckBox(self)
            checkboxMCStat.setCheckState(QtCore.Qt.Checked if mcdef else QtCore.Qt.Unchecked)
            self.checkboxes.append(checkboxMCStat)
            self.quantityButtonGroup.addButton(checkboxMCStat,imc)
            if imc ==  MCStatType.Nminutes_per_job:
                spinboxMCStat = QtWidgets.QSpinBox(self)
                self.spinboxNJobs = QtWidgets.QSpinBox(self)
                self.spinboxNJobs.setMinimum(1)
                self.spinboxNJobs.setValue(self.ncores)
                self.spinboxNJobs.setMaximum(10000)
                self.spinboxNJobs.setSuffix(" jobs")
                self.spinboxNJobs.valueChanged[int].connect(self.UpdateNJobs)
            elif imc == MCStatType.Nions_per_beam:
                spinboxMCStat = QtWidgets.QSpinBox(self)
            else:
                spinboxMCStat = QtWidgets.QDoubleSpinBox(self)
            spinboxMCStat.setSuffix(" "+MCStatType.unit[imc])
            self.spinboxes.append(spinboxMCStat)
            logger.debug("{}. {} min={} val={} max={} step={} def={}".format(imc,MCStatType.cfglabels[imc],mcmin,mcval,mcmax,mcstep,mcdef))
            spinboxMCStat.setMinimum(mcmin)
            spinboxMCStat.setMaximum(mcmax)
            spinboxMCStat.setValue(mcval)
            spinboxMCStat.setSingleStep(mcstep)
            spinboxMCStat.setReadOnly(False)
            spinboxMCStat.setEnabled(mcdef)
            checkboxMCStat.toggled.connect(spinboxMCStat.setEnabled)
            if MCStatType.is_int[imc]:
                spinboxMCStat.valueChanged[int].connect(lambda ival: self.UpdateThresholdValue(ival,imc))
            else:
                spinboxMCStat.valueChanged[float].connect(lambda fval: self.UpdateThresholdValue(fval,imc))
            if mcdef:
                self.UpdateSelectedQuantity(imc)
            layoutSelectMCStat = QtWidgets.QVBoxLayout()
            layoutSelectMCStat.addWidget(labelMCStat)
            layoutSelectMCStat.addWidget(checkboxMCStat)
            layoutSelectMCStat.addWidget(spinboxMCStat)
            if imc ==  MCStatType.Nminutes_per_job:
                layoutSelectMCStat.addWidget(self.spinboxNJobs)
            selectMCStat = QtWidgets.QWidget()
            selectMCStat.setLayout(layoutSelectMCStat)
            self.layoutQuantitySelection.addWidget(selectMCStat)

        self.quantitySelection.setLayout(self.layoutQuantitySelection)
        self.vBoxLayoutIDCMCStatistics.addWidget(self.quantitySelection)

        self.beamSelector = QtWidgets.QTableWidget()
        self.beamSelector.setRowCount(0)
        self.beamSelector.setColumnCount(2)
        self.beamSelector.setHorizontalHeaderLabels(["Name", "Included in simulation"])
        self.beamButtonGroup = QtWidgets.QButtonGroup()
        self.beamButtonGroup.setExclusive(False)
        self.beamButtonGroup.buttonClicked[int].connect(self.UpdateBeamSelection)
        self.vBoxLayoutIDCMCStatistics.addWidget(self.beamSelector)

        self.setLayout(self.vBoxLayoutIDCMCStatistics)

        self.quantityButtonGroup.buttonClicked[int].connect(self.UpdateSelectedQuantity)

    def UpdateNJobs(self,val):
        logger.debug("update njobs value to {}".format(val))
        self.details.SetNJobs(val)
    def UpdateThresholdValue(self,val,imc=-1):
        logger.debug(f"update threshold value to {val}, imc={imc}")
        self.details.SetStatistics(imc,val)
    def UpdateSelectedQuantity(self,imc):
        logger.debug(f"update selected quantity with index={imc}")
        if imc<0 or imc>=MCStatType.NTypes:
            raise RuntimeError("PROGRAMMING ERROR: unknown index value for statistics quantifyer: {}".format(i))
        value = self.spinboxes[imc].value()
        logger.debug("{} {}".format(value,MCStatType.guilabels[imc][2:]))
        self.details.SetStatistics(imc,value)
    def UpdateBeamSelection(self,ichk):
        selection = dict()
        logger.debug('click on button {} of the beam selection button group'.format(ichk))
        for ib,b in enumerate(self.beamButtonGroup.buttons()):
            name=str(self.beamSelector.item(ib,0).text())
            yesno = (b.checkState() == QtCore.Qt.Checked)
            selection[name]=yesno
            logger.debug("selection has {} keys".format(len(selection.keys())))
            logger.debug("{}. beam {} {} selected".format(ib,name,"IS" if yesno else "IS NOT"))
        logger.debug("selection has {} keys".format(len(selection.keys())))
        logger.debug("setting selection with beam names: " + ",".join(selection.keys()))
        self.details.SetBeamSelection(selection)
    def PlanUpdate(self):
        names = self.details.beam_names
        numbers = self.details.beam_numbers
        assert(len(numbers)==len(names))
        oldNrow = self.beamSelector.rowCount()
        self.beamSelector.setRowCount(len(names))
        self.beamSelector.setVerticalHeaderLabels(numbers)
        syscfg = system_configuration.getInstance()
        for i,name in enumerate(names):
            if i < oldNrow:
                self.beamSelector.item(i,0).setText(name)
                beamCheck = self.beamButtonGroup.button(i)
                beamCheck.setCheckState(QtCore.Qt.Checked)
            else:
                self.beamSelector.setItem(i,0,QtWidgets.QTableWidgetItem(name))
                beamCheck = QtWidgets.QCheckBox()
                beamCheck.setCheckState(QtCore.Qt.Checked)
                beamWidget = QtWidgets.QWidget()
                beamLayout = QtWidgets.QHBoxLayout(beamWidget)
                beamLayout.addWidget(beamCheck)
                beamLayout.setAlignment(QtCore.Qt.AlignCenter)
                beamLayout.setContentsMargins(0,0,0,0)
                beamWidget.setLayout(beamLayout)
                self.beamSelector.setCellWidget(i,1,beamWidget)
                self.beamButtonGroup.addButton(beamCheck,i)
        for i in range(self.beamSelector.rowCount(),len(self.beamButtonGroup.buttons())):
            old_checkbox = self.beamButtonGroup.button(i)
            self.beamButtonGroup.removeButton(old_checkbox)
        self.spinboxNJobs.setValue(self.ncores)
        for imc in range(MCStatType.NTypes):
            mcmin,mcval,mcmax,mcstep,mcdef = syscfg[MCStatType.cfglabels[imc]]
            self.spinboxes[imc].setValue(mcval)
            if mcdef:
                self.checkboxes[imc].setCheckState(QtCore.Qt.Checked)
        #QtWidgets.QWidget.update(self)

class IDCUserParameters( QtWidgets.QWidget ):
    def __init__(self,details):
        QtWidgets.QWidget.__init__(self)
        self.details = details
        self.hBoxLayoutIDCUserParameters = QtWidgets.QHBoxLayout()
        self.idcDoseGridSettings = IDCDoseGridSettings(details)
        self.idcMCStatistics = IDCMCStatistics(details)
        self.hBoxLayoutIDCUserParameters.addWidget(self.idcDoseGridSettings)
        self.hBoxLayoutIDCUserParameters.addWidget(self.idcMCStatistics)
        self.setLayout(self.hBoxLayoutIDCUserParameters)

class IDCSubmit( QtWidgets.QWidget ):
    def __init__(self,details):
        QtWidgets.QWidget.__init__(self)
        #
        self.details = details
        details.Subscribe(self)
        details.Subscribe(self,"CTPHANTOM")
        details.Subscribe(self,"CTPROTOCOL")
        #
        self.widgetPriority = QtWidgets.QWidget()
        self.labelPriority = QtWidgets.QLabel("Job Priority")
        self.comboboxPriority = QtWidgets.QComboBox(self)
        self.comboboxPriority.addItems(MCPriorityType.labels)
        self.comboboxPriority.setCurrentIndex(MCPriorityType.labels.index("Normal"))
        self.hboxlayoutPriority = QtWidgets.QHBoxLayout()
        self.hboxlayoutPriority.addWidget(self.labelPriority)
        self.hboxlayoutPriority.addWidget(self.comboboxPriority)
        self.widgetPriority.setLayout(self.hboxlayoutPriority)
        #
        self.pushbuttonPrepare = QtWidgets.QPushButton("Prepare")
        #
        self.qtmenu = QtWidgets.QMenu("Run 'Gate --qt' check",self)
        #self.labelSummary = QtWidgets.QLabel("click 'Prepare' to get job summary before 'Submit'")
        self.labelSummary = QtWidgets.QTextEdit("No treatment plan selected yet.")
        self.labelSummary.setReadOnly(True)
        self.toolbuttonRunQTCheck = QtWidgets.QToolButton()
        self.toolbuttonRunQTCheck.setMenu(self.qtmenu)
        self.toolbuttonRunQTCheck.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.toolbuttonRunQTCheck.setText(self.qtmenu.title())
        #
        self.pushbuttonSubmit = QtWidgets.QPushButton("SUBMIT")
        #
        self.vBoxLayoutIDCSubmit = QtWidgets.QVBoxLayout()
        self.vBoxLayoutIDCSubmit.addWidget(self.widgetPriority)
        self.vBoxLayoutIDCSubmit.addWidget(self.pushbuttonPrepare)
        self.vBoxLayoutIDCSubmit.addWidget(self.labelSummary)
        self.vBoxLayoutIDCSubmit.addWidget(self.toolbuttonRunQTCheck)
        self.vBoxLayoutIDCSubmit.addWidget(self.pushbuttonSubmit)
        self.vBoxLayoutIDCSubmit.addWidget(QtWidgets.QLabel("TODO: cartoon of simulation setup"))
        self.setLayout(self.vBoxLayoutIDCSubmit)
        #
        self.comboboxPriority.currentIndexChanged[int].connect(self.UpdatePriority)
        self.pushbuttonPrepare.clicked.connect(self.Prepare)
        self.qtmenu.triggered.connect(self.RunQTCheck)
        self.pushbuttonSubmit.clicked.connect(self.Submit)
        #
        self.toolbuttonRunQTCheck.setEnabled(False)
        self.pushbuttonSubmit.setEnabled(False)
        self.pushbuttonPrepare.setEnabled(False)
    def Prepare(self):
        self.labelSummary.setText("...busy preparing scripts and input data...")
        self.labelSummary.repaint()
        logger.debug("create scripts, ready for submission")
        self.jobexec = job_executor.create_condor_job_executor(self.details)
        logger.debug("get job summary")
        self.labelSummary.setText(self.jobexec.summary)
        logger.debug("redefine run-gate-qt menu")
        self.qtmenu.clear()
        self.qtmenu.setTitle("Run 'Gate --qt' check")
        for beamname in self.details.beam_names:
            if self.details.beam_selection.get(beamname,False):
                logger.debug("adding {}".format(beamname))
                self.qtmenu.addAction(beamname)
            else:
                logger.debug("skipping {} (not selected)".format(beamname))
        self.toolbuttonRunQTCheck.setEnabled(True)
        self.pushbuttonSubmit.setEnabled(True)
    def UpdatePriority(self,iprio):
        assert(type(iprio)==int)
        assert(iprio>=0)
        assert(iprio<MCPriorityType.NTypes)
        self.details.priority = MCPriorityType.condor_priorities[iprio]
    def RunQTCheck(self,qa):
        beamname = str(qa.text())
        logger.debug("run Gate --qt for checking geometry")
        ret = self.jobexec.launch_gate_qt_check(beamname)
        if int(ret) != 0:
            self.pushbuttonSubmit.setEnabled(False)
            QtWidgets.QMessageBox.warning(self,"Problem","Gate --qt exited with nonzero exit code: {}. Please check the logs to get hints about what went wrong.".format(ret))
    def Submit(self):
        logger.debug("submitting job")
        ret=self.jobexec.launch_subjobs()
        logger.info("submitted job, ret={}".format(ret))
        self.labelSummary.setText(self.jobexec.summary)
        self.pushbuttonSubmit.setEnabled(False)
        self.toolbuttonRunQTCheck.setEnabled(False)
        self.pushbuttonPrepare.setEnabled(False)
    def PlanUpdate(self):
        self.pushbuttonSubmit.setEnabled(False)
        self.toolbuttonRunQTCheck.setEnabled(False)
        self.pushbuttonPrepare.setEnabled(False)
        self.qtmenu.clear()
        if self.details.run_with_CT_geometry:
            self.labelSummary.setText("select HLUT for CT in the 'Model' tab")
        else:
            self.labelSummary.setText("select phantom geometry in the 'Model' tab")
        #QtWidgets.QWidget.update(self)
    def update_ctphantom(self):
        logger.debug("CT/Phantom changed, going to update 'Prepare' settings")
        self.update_prepare()
    def update_ctprotocol(self):
        self.update_prepare()
    def update_prepare(self):
        can_prepare = False
        all_hluts = hlut_conf.getInstance()
        if self.details.bs_info is None:
            logger.debug("update_prepare: we don't have a beamset")
            self.labelSummary.setText("select a treatment plan")
            pass
        elif not self.details.run_with_CT_geometry:
            logger.debug("update_prepare: no CT, apparently phantom")
            can_prepare = self.details.PhantomSpecs is not None
            self.labelSummary.setText("click 'Prepare'" if can_prepare else "select phantom geometry in the 'Patient Model' tab")
        elif self.details.ctprotocol_name is None:
            logger.debug("update_prepare: CT protocol is None")
            self.labelSummary.setText("select CT protocol for CT in the 'Patient Model' tab")
            can_prepare = False
        elif self.details.ctprotocol_name in all_hluts:
            logger.debug("update_prepare: yay, CT protocol name is set and exists in hlut.conf!")
            self.labelSummary.setText("click 'Prepare'")
            can_prepare = True
        else:
            logger.debug("update_prepare: CT protocol is set but UNKNOWN????")
            self.labelSummary.setText("Select a different CT protocol in the 'Patient Model' tab. Check 'hlut.conf'!")
            can_prepare = False
        self.pushbuttonSubmit.setEnabled(False)
        self.toolbuttonRunQTCheck.setEnabled(False)
        logger.debug("{} the Prepare button".format("ENABLING" if can_prepare else "DISABLING"))
        self.pushbuttonPrepare.setEnabled(can_prepare)
        #QtWidgets.QWidget.update(self)
    def update_any(self):
        self.PlanUpdate()


class TabIDC( QtWidgets.QWidget ):
    def __init__(self,details):
        QtWidgets.QWidget.__init__(self)
        self.details = details
        self.hBoxLayoutIDCspecs = QtWidgets.QHBoxLayout()
        #
        self.idcUserParameters = IDCUserParameters(details)
        self.idcUserParameters.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Preferred)
        self.hBoxLayoutIDCspecs.addWidget(self.idcUserParameters)
        #
        self.idcRun = IDCSubmit(details)
        self.idcRun.setSizePolicy(QtWidgets.QSizePolicy.Maximum,QtWidgets.QSizePolicy.Preferred)
        self.hBoxLayoutIDCspecs.addWidget(self.idcRun)
        #
        self.setLayout(self.hBoxLayoutIDCspecs)

# vim: set et softtabstop=4 sw=4 smartindent:
