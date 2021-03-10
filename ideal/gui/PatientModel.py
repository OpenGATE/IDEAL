# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from impl.system_configuration import system_configuration
from impl.hlut_conf import hlut_conf
import os
import numpy as np
import logging
logger = logging.getLogger()

class ROIDetails( QtWidgets.QWidget ):
    """
    Select which ROI is used as "External" contour for cropping the image.
    Override material definition (fixed HU value) for certain ROIs.
    """
    def __init__(self,current):
        QtWidgets.QWidget.__init__(self)
        self.current = current
        logger.debug("creating ROI image details widget")
        self.rp_filepath = ""
        self.roitable = QtWidgets.QLabel("If you import a treatment plan, then you'll find a ROI table here")
        self.vBoxlayoutROIDetails = QtWidgets.QVBoxLayout()
        self.vBoxlayoutROIDetails.addWidget(self.roitable)
        self.setLayout(self.vBoxlayoutROIDetails)
        self.no_override = "(no override)"
        self.roinames=list()
        self.padding_due_to_dosegrid = False
        syscfg = system_configuration.getInstance()
        self.ct_override_material_list = [self.no_override] + sorted(syscfg['ct override list'].keys())
        current.Subscribe(self)
    def PlanUpdate(self):
        logger.debug("updating ROI details table")
        if self.rp_filepath != self.current.rp_filepath and self.current.structure_set is not None:
            self.vBoxlayoutROIDetails.removeWidget(self.roitable)
            del self.roitable
            logger.debug("going to collect ROI details")
            roinums=list(self.current.roinumbers)
            self.roinames=list(self.current.roinames)
            roitypes=list(self.current.roitypes)
            self.padding_due_to_dosegrid = self.current.DoseGridSticksPartlyOutsideOfCTVolume()
            if self.padding_due_to_dosegrid:
                logger.debug("adding pseudo-roi: padding voxels to account for dose grid sticking out of CT")
                roinums.insert(0,str(-1))
                self.roinames.insert(0,"Dose Padding")
                roitypes.insert(0,"Extra")
            realNroi = len(self.current.roinumbers)
            fakeNroi = len(roinums)
            logger.debug("got {} ROIs{}".format(fakeNroi,"." if fakeNroi==realNroi else ", including one 'fake' ROI for dose-grid induced padding on the CT."))
            self.roitable = QtWidgets.QTableWidget()
            self.roitable.setColumnCount(3)
            self.roitable.setRowCount(fakeNroi)
            #self.roitable.setHorizontalHeaderLabels(["ROI number", "ROI name", "ROI type", "material override"])
            self.roitable.setHorizontalHeaderLabels(["ROI name", "ROI type", "material override"])
            self.roitable.setVerticalHeaderLabels(roinums)
            logger.debug("created ROI details table with 3 columns")
            self.vBoxlayoutROIDetails.addWidget(self.roitable)
            for i,(roinum,roiname,roitype) in enumerate(zip(roinums,self.roinames,roitypes)):
                logger.debug("setting i={},roinum={},roiname={} row".format(i,roinum,roiname))
                self.roitable.setItem(i,0,QtWidgets.QTableWidgetItem(roiname))
                self.roitable.setItem(i,1,QtWidgets.QTableWidgetItem(roitype))
                self.roitable.setItem(i,2,QtWidgets.QTableWidgetItem())
                for j in [0,1,2]:
                    self.roitable.item(i,j).setFlags(QtCore.Qt.ItemIsEnabled)
            if self.padding_due_to_dosegrid:
                self.roitable.item(0,2).setText(self.current.dosepad_material)
            self.roitable.itemDoubleClicked.connect(self.UpdateHUOverrides)
            self.roitable.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Preferred)
            self.vBoxlayoutROIDetails.addWidget(self.roitable)
            self.rp_filepath = self.current.rp_filepath
        else:
            logger.debug("ROI table is still up to date")
        #QtWidgets.QWidget.update(self)
    def UpdateHUOverrides(self,HUitem):
        c=HUitem.column()
        if c != 2:
            logger.debug("got doubleclick signal for column {}, skipping".format(c))
            return
        r=HUitem.row()
        if self.padding_due_to_dosegrid and r==0:
            list_of_materials = list(self.ct_override_material_list[1:])
            curtxt = self.current.dosepad_material
            title="select padding material"
            purpose="Padding the CT with this material to include dose grid"
        else:
            title="select override material"
            roiname = self.roinames[r]
            purpose= "ROI='{}'".format(roiname)
            curtxt = str(HUitem.text())
            list_of_materials = list(self.ct_override_material_list)
        if not curtxt:
            curtxt = self.no_override
        icurrent = 0
        if curtxt in self.ct_override_material_list:
            icurrent = list_of_materials.index(curtxt)
        else:
            errmsg = "PROGRAMMING ERROR: before selection: unknown override material={} for {} ????".format(curtxt,purpose)
            logger.error(errmsg)
            raise RuntimeError(errmsg)
        logger.debug("before selection: i={} material={} from the override list for {}".format(icurrent,curtxt,purpose))
        name,ok = QtWidgets.QInputDialog.getItem(self, title, purpose, list_of_materials,icurrent,editable=False)
        if not ok:
            logger.debug("user doubleclicked '{}' but then clicked 'cancel', so I kept the override setting equal to '{}'".format(purpose,curtxt))
            return
        newtxt = str(name)
        if newtxt == curtxt:
            logger.debug("user doubleclicked on '{}' and 'OK' but kept the override setting equal to '{}'".format(purpose,curtxt))
            return
        logger.debug("user doubleclicked {} and chose to replace '{}' with '{}'".format(purpose,curtxt,newtxt))
        if self.padding_due_to_dosegrid and r==0:
            self.current.dosepad_material = newtxt
            HUitem.setText(newtxt)
        else:
            if newtxt == self.no_override:
                self.current.RemoveHUOverride(roiname)
                HUitem.setText("")
            else:
                self.current.SetHUOverride(roiname,newtxt)
                HUitem.setText(newtxt)
        QtWidgets.QWidget.update(self)

class HUDetails( QtWidgets.QWidget ):
    def __init__(self,current):
        QtWidgets.QWidget.__init__(self)
        self.current = current
        current.Subscribe(self)
        all_hluts = hlut_conf.getInstance()
        self.density_files = dict([(name,specs.get_density_file()) for name,specs in all_hluts.items()])
        self.HUselector = QtWidgets.QComboBox(self)
        self.dummy  = "(choose protocol)"
        self.HUselector.addItem(self.dummy)
        for k in self.density_files.keys():
            self.HUselector.addItem(k)
        self.vBoxlayoutHUDetails = QtWidgets.QVBoxLayout()
        self.vBoxlayoutHUDetails.addWidget(self.HUselector)
        self.tableAndPlot = QtWidgets.QWidget()
        self.hBoxlayoutHUTableAndPlot = QtWidgets.QHBoxLayout()
        self.HUdensity_table = QtWidgets.QTableWidget()
        self.HUdensity_table.setColumnCount(2)
        self.HUdensity_table.setHorizontalHeaderLabels(["HU", "density [g/cm3]"])
        self.hBoxlayoutHUTableAndPlot.addWidget(self.HUdensity_table)
        try:
            vuvuzela=logging.getLogger('matplotlib.font_manager')
            if vuvuzela:
                logger.debug("try to mute matplotlib logging output")
                vuvuzela.setLevel(logging.ERROR)
            else:
                logger.debug("failed to acquire the matplotlib logger")
            from matplotlib.backends.backend_qt5agg import ( FigureCanvas, NavigationToolbar2QT as NavigationToolbar )
            from matplotlib.figure import Figure
            self.HUdensity_canvas = FigureCanvas(Figure(figsize=(3,3)))
            self.HUdensity_axes = self.HUdensity_canvas.figure.add_subplot(111)
            self.HUdensity_axes.plot([-1024,0,3000],[0,1,10])
            self.HUdensity_axes.set_xlabel(r"HU")
            self.HUdensity_axes.set_ylabel(r"$\rho$ [g/cm$^3$]")
            self.HUdensity_axes.set_title(r"(dummy curve)")
            self.hBoxlayoutHUTableAndPlot.addWidget(self.HUdensity_canvas)
        except ImportError as ie:
            self.HUdensity_canvas = None
            self.HUdensity_axes = None
            logger.warn("No HU plot possible, because: {}".format(ie))
        self.tableAndPlot.setLayout(self.hBoxlayoutHUTableAndPlot)
        self.vBoxlayoutHUDetails.addWidget(self.tableAndPlot)
        self.setLayout(self.vBoxlayoutHUDetails)
        self.HUselector.currentIndexChanged[str].connect(self.SetHLUTFile)
    def PlanUpdate(self):
        if self.current.ctprotocol_name is None:
            for i,k in enumerate(self.density_files.keys()):
                if k == self.current.ctprotocol_name:
                    self.HUselector.setCurrentIndex(i+1)
            self.HUselector.setCurrentIndex(0)
        else:
            self.HUselector.setCurrentIndex(0)
    def SetHLUTFile(self,s):
        logger.debug("got signal for SetHLUTFile with arg of type {} and value {}".format(type(s),s))
        newHLUT = str(s)
        if self.HUdensity_axes:
            self.HUdensity_axes.clear()
            self.HUdensity_axes.set_title(r"(dummy curve)")
        else:
            logger.debug("matplot does not work on this machine => no figure")
        if newHLUT == self.dummy:
            logger.debug("(still) NO density file path")
            self.HUdensity_table.setRowCount(0)
            self.current.SetHLUT()
        elif newHLUT in self.density_files.keys():
            newHLUTpath = self.density_files[newHLUT]
            logger.debug("Using density file path {}".format(newHLUTpath))
            HUtable = np.loadtxt(newHLUTpath)
            logger.debug("table shape is {}".format(HUtable.shape))
            logger.debug("table type is {}".format(HUtable.dtype))
            assert(len(HUtable.shape)==2)
            ncol = HUtable.shape[1]
            assert(ncol==2 or ncol==3)
            self.HUdensity_table.setRowCount(HUtable.shape[0])
            if ncol==2:
                HU=HUtable[:,0]
                rho=HUtable[:,1]
                for i,(h,r) in enumerate(HUtable):
                    self.HUdensity_table.setItem(i,0,QtWidgets.QTableWidgetItem("{}".format(h)))
                    self.HUdensity_table.setItem(i,1,QtWidgets.QTableWidgetItem("{}".format(r)))
            elif ncol==3:
                HUtmp=list()
                RHOtmp=list()
                if not (HUtable[1:,0]==HUtable[:-1,1]).all():
                    logger.warn("HU density table for {newHLUT} for seems weird, HU values not contiguous!")
                for i,(h0,h1,rh) in enumerate(HUtable):
                    self.HUdensity_table.setItem(i,0,QtWidgets.QTableWidgetItem("{}".format(h0)))
                    self.HUdensity_table.setItem(i,1,QtWidgets.QTableWidgetItem("{}".format(rh)))
                    HUtmp += [h0,h1]
                    RHOtmp += [rh,rh]
                HU = np.array(HUtmp)
                rho = np.array(RHOtmp)
            else:
                raise RuntimeError(f"corrupt density file for {newHLUT}, number of columns should be 2 or 3 (got {ncol})")
            #self.HUdensity_table.repaint()
            if self.HUdensity_axes:
                self.HUdensity_axes.plot(HU,rho)
                self.HUdensity_axes.set_xlim(-1500,+3500)
                self.HUdensity_axes.set_xlabel(r"HU")
                self.HUdensity_axes.set_ylabel(r"$\rho$ [g/cm$^3$]")
                self.HUdensity_axes.grid()
                self.HUdensity_axes.set_title(newHLUT)
                self.HUdensity_axes.figure.canvas.draw()
            self.current.SetHLUT( kw=newHLUT )
        else:
            logger.error("UNKNOWN DENSITY FILE {}".format(newHLUT))



class CTImageDetails( QtWidgets.QWidget ):
    def __init__(self,current):
        QtWidgets.QWidget.__init__(self)
        self.current = current
        logger.debug("creating ct image details widget")
        self.hBoxlayoutCTImageDetails = QtWidgets.QHBoxLayout()
        logger.debug("going to create ROI details widget")
        self.roidetails = ROIDetails(current)
        self.roidetails.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Preferred)
        self.hBoxlayoutCTImageDetails.addWidget(self.roidetails)
        logger.debug("going to create HLUT details widget")
        self.hudetails = HUDetails(current)
        self.hudetails.setSizePolicy(QtWidgets.QSizePolicy.Maximum,QtWidgets.QSizePolicy.Preferred)
        self.hBoxlayoutCTImageDetails.addWidget(self.hudetails)
        self.setLayout(self.hBoxlayoutCTImageDetails)
        logger.debug("DONE creating ct image details widget")

class PhantomDetails( QtWidgets.QWidget ):
    def __init__(self,current):
        QtWidgets.QWidget.__init__(self)
        self.current = current
        logger.debug("start creating phantom details widget")
        syscfg = system_configuration.getInstance()
        self._phantoms = syscfg["phantom_defs"]

        logger.debug("creating PHANTOM widget (e.g. 'PMMA box' or 'WATER box')")
        self.phantomLabel = QtWidgets.QLabel("Phantom")
        self.phantomComboBox = QtWidgets.QComboBox(self)
        self.phantomComboBox.addItems(["choose phantom"]+[spec.gui_name for spec in self._phantoms.values()])
        self.phantomComboBox.setCurrentIndex(0)
        self.phantomWidget = QtWidgets.QWidget()
        self.hBoxlayoutPHANTOM = QtWidgets.QHBoxLayout()
        self.hBoxlayoutPHANTOM.addWidget(self.phantomLabel)
        self.hBoxlayoutPHANTOM.addWidget(self.phantomComboBox)
        self.phantomWidget.setLayout(self.hBoxlayoutPHANTOM)

        self.vBoxlayoutPhantomDetails = QtWidgets.QVBoxLayout()
        self.vBoxlayoutPhantomDetails.addWidget(self.phantomWidget)
        self.setLayout(self.vBoxlayoutPhantomDetails)

        self.phantomComboBox.currentIndexChanged[int].connect(self.UpdatePhantomGEO)

        self.rp_filepath = self.current.rp_filepath
        self.current.Subscribe(self)
        logger.debug("finished creating phantom details widget")

    def PlanUpdate(self):
        if self.rp_filepath != self.current.rp_filepath:
            self.phantomComboBox.setCurrentIndex(0)
            self.rp_filepath = self.current.rp_filepath
    def UpdatePhantomGEO(self,iph):
        if iph == 0:
            logger.debug("un-setting the phantom definition")
            self.current.UpdatePhantomGEO(None)
        else:
            assert(iph<=len(self._phantoms))
            phspecs = list(self._phantoms.values())[iph-1]
            logger.debug("change phantom to label={} GUI name=".format(phspecs.label,phspecs.gui_name))
            self.current.UpdatePhantomGEO(phspecs)

class TabPatientModel( QtWidgets.QWidget ):
    def __init__(self,current):
        QtWidgets.QWidget.__init__(self)
        self.current = current
        self.hBoxlayoutPatientModel = QtWidgets.QHBoxLayout()
        self.geometryButtonGroup = QtWidgets.QButtonGroup()
        self.geometryButtonGroup.setExclusive(True)
        #
        self.CTwidget = QtWidgets.QWidget()
        self.vBoxlayoutCT = QtWidgets.QVBoxLayout()
        self.selectCTcheckbox = QtWidgets.QCheckBox("Select CT geometry")
        self.selectCTcheckbox.setCheckState(QtCore.Qt.Checked)
        self.vBoxlayoutCT.addWidget( self.selectCTcheckbox )
        self.geometryButtonGroup.addButton(self.selectCTcheckbox,0)
        logger.debug("going to create image details widget")
        self.CTdetails = CTImageDetails(current)
        self.vBoxlayoutCT.addWidget( self.CTdetails )
        self.CTwidget.setLayout(self.vBoxlayoutCT)
        self.CTwidget.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Preferred)
        self.hBoxlayoutPatientModel.addWidget(self.CTwidget)
        #
        self.PHANTOMwidget = QtWidgets.QWidget()
        self.vBoxlayoutPHANTOM = QtWidgets.QVBoxLayout()
        self.selectPHANTOMcheckbox = QtWidgets.QCheckBox("Select PHANTOM geometry")
        self.selectPHANTOMcheckbox.setCheckState(QtCore.Qt.Unchecked)
        self.vBoxlayoutPHANTOM.addWidget( self.selectPHANTOMcheckbox )
        self.geometryButtonGroup.addButton(self.selectPHANTOMcheckbox,1)
        logger.debug("going to create phantom details widget")
        self.PHANTOMdetails = PhantomDetails(current)
        self.vBoxlayoutPHANTOM.addWidget( self.PHANTOMdetails )
        self.PHANTOMwidget.setLayout(self.vBoxlayoutPHANTOM)
        self.PHANTOMwidget.setSizePolicy(QtWidgets.QSizePolicy.Maximum,QtWidgets.QSizePolicy.Preferred)
        self.hBoxlayoutPatientModel.addWidget(self.PHANTOMwidget)
        #
        self.setLayout(self.hBoxlayoutPatientModel)
        #
        self.geometryButtonGroup.buttonClicked[int].connect(self.UpdateGeometrySelection)
        self.CTdetails.setEnabled(False)
        self.PHANTOMdetails.setEnabled(False)
        self.selectCTcheckbox.setEnabled(False)
        self.selectPHANTOMcheckbox.setEnabled(False)
        self.current.Subscribe(self)
        logger.debug("done with MODEL tab")
    def UpdateGeometrySelection(self,igeo):
        assert(type(igeo)==int)
        assert(igeo==0 or igeo==1)
        self.current.SetGeometry(igeo)
        if igeo==0:
            assert(self.current.have_CT)
            self.CTdetails.setEnabled(True)
            self.PHANTOMdetails.setEnabled(False)
        if igeo==1:
            self.CTdetails.setEnabled(False)
            self.PHANTOMdetails.setEnabled(True)
    def PlanUpdate(self):
        if self.current.have_CT:
            self.selectCTcheckbox.setCheckState(QtCore.Qt.Checked)
            self.selectPHANTOMcheckbox.setCheckState(QtCore.Qt.Unchecked)
            self.CTdetails.setEnabled(True)
            self.PHANTOMdetails.setEnabled(False)
            self.selectCTcheckbox.setEnabled(True)
            self.selectPHANTOMcheckbox.setEnabled(True)
        else:
            self.selectCTcheckbox.setCheckState(QtCore.Qt.Unchecked)
            self.selectPHANTOMcheckbox.setCheckState(QtCore.Qt.Checked)
            self.CTdetails.setEnabled(False)
            self.PHANTOMdetails.setEnabled(True)
            self.selectCTcheckbox.setEnabled(False)
            self.selectPHANTOMcheckbox.setEnabled(False)
        #QtWidgets.QWidget.update(self)

# vim: set et softtabstop=4 sw=4 smartindent:
