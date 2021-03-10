# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
import sys
import logging
logger = logging.getLogger(__name__)

from impl.version import version_info
from gui.PatientIO import TabPatientIO
from gui.PatientModel import TabPatientModel
from gui.TreatmentPlanDescription import TabTPdescription
from gui.IDC import TabIDC
from gui.JobManagement import TabJobManagement

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,details):
        QtWidgets.QMainWindow.__init__(self)
        # hide the actual content: RT plan details
        self.current_details = details
        self._warnings = list()
        # Resize width and height
        self.resize(1250, 600)
        # Add tabs
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(TabPatientIO(self,self.current_details),"Patient I/O")
        self.tabs.addTab(TabPatientModel(self.current_details),"Model")
        self.tabs.addTab(TabTPdescription(self.current_details),"Plan description")
        self.tabs.addTab(TabIDC(self.current_details),"IDC Specs && Submit")
        self.tabs.addTab(TabJobManagement(self.current_details),"IDC Job Management")
        #self.vBoxlayoutMain.addWidget(self.tabs)
        #self.setLayout(self.vBoxlayoutMain)
        self.setCentralWidget(self.tabs)
        # Set title
        self.setWindowTitle('IDEAL: research GUI for IDEAL')
        self.fileMenu = self.menuBar().addMenu("File")
        self.aboutMenu = self.menuBar().addMenu("About")

        # menu item for "new plan"
        self.actionNewPlan = QtWidgets.QAction("New",self)
        self.actionNewPlan.setShortcut(QtGui.QKeySequence.New)
        self.actionNewPlan.triggered.connect(self.OpenNewPlanFile)
        self.fileMenu.addAction(self.actionNewPlan)

        # menu item for "toggle verbosity"
        #self.actionToggleVerbosity = QtWidgets.QAction("Verbosity",self)
        #self.actionToggleVerbosity.setShortcut(QtGui.QKeySequence("Ctrl+V"))
        #self.actionToggleVerbosity.setCheckable(True)
        #if logger.handlers[1].level == logging.DEBUG:
        #    self.actionToggleVerbosity.setChecked(QtCore.Qt.Checked)
        #else:
        #    self.actionToggleVerbosity.setChecked(QtCore.Qt.Unchecked)
        #self.actionToggleVerbosity.toggled.connect(self.ToggleDebug)
        #self.fileMenu.addAction(self.actionToggleVerbosity)

        # menu item for "quit"
        self.actionQuit = QtWidgets.QAction("Quit",self)
        self.actionQuit.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        self.actionQuit.triggered.connect(self.Quit)
        self.fileMenu.addAction(self.actionQuit)

        ## menu item for "redraw"
        #self.actionRefresh = QtWidgets.QAction("Refresh",self)
        #self.actionRefresh.setShortcut(QtGui.QKeySequence.Refresh)
        #self.actionRefresh.triggered.connect(self.tabs.update)
        #self.fileMenu.addAction(self.actionRefresh)

        # about: version and help
        self.actionVersionInfo = QtWidgets.QAction("Version",self)
        self.actionVersionInfo.triggered.connect(self.ShowVersion)
        self.aboutMenu.addAction(self.actionVersionInfo)
        self.version_info_window = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,"Version info",version_info,QtWidgets.QMessageBox.Ok)
        self.version_info_window.accepted.connect(self.version_info_window.hide)

        self.actionHelp = QtWidgets.QAction("Help",self)
        self.actionHelp.triggered.connect(self.ShowHelp)
        self.aboutMenu.addAction(self.actionHelp)
        self.help_window = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,"Help","TO DO: write helpful text here.",QtWidgets.QMessageBox.Ok)
        self.help_window.accepted.connect(self.help_window.hide)

    def ShowVersion(self):
        self.version_info_window.show()
    def ShowHelp(self):
        self.help_window.show()
    def OpenNewPlanFile(self):
        newfile,_ = QtWidgets.QFileDialog.getOpenFileName(self,
                'Select DICOM plan file', self.current_details.input_dicom, "DICOM RT plan files (RP*.dcm);;all DICOM files (*.dcm)")
        if newfile:
            newfile = str(newfile)
            logger.debug("file dialog returned {}".format(newfile))
            try:
                self.current_details.SetPlanFilePath(newfile)
                self._warnings = self.current_details.GetAndClearWarnings()
                if self._warnings:
                    nw=len(self._warnings)
                    logger.debug("got {} warnings".format(nw))
                    for iw,w in enumerate(self._warnings):
                        QtWidgets.QMessageBox.warning(self,"WARNING {}/{}".format(iw+1,nw),w)
                else:
                    logger.debug("looks like we read the plan successfully, no serious errors/warnings")
                self._warnings = list()
            except Exception as e:
                logger.error("got exception '{}'".format(str(e)))
                QtWidgets.QMessageBox.critical(self,"Unrecoverable error while reading {}".format(newfile),str(e))
        else:
            logger.debug("file dialog returned nothing; try again!")
    def Quit(self):
        logger.debug("goodbye!")
        sys.exit(0)
    #def ToggleDebug(self):
    #    termstream = logger.handlers[1]
    #    clarify = "(on terminal stream only; the log file stream always remains on DEBUG)"
    #    if termstream.level == logging.DEBUG:
    #        logger.debug("muting down logging level " + clarify)
    #        termstream.setLevel(logging.INFO)
    #    else:
    #        logger.info("making the logging level more noisy " + clarify)
    #        termstream.setLevel(logging.DEBUG)

# vim: set et softtabstop=4 sw=4 smartindent:
