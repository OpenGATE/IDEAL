# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import sys
from PyQt5 import QtWidgets
from gui.gui_utils import NameValuePairWidget
import logging
logger = logging.getLogger(__name__)

class TabPatientIO( QtWidgets.QWidget ):
    def __init__(self,parent,current):
        QtWidgets.QWidget.__init__(self,parent)
        self.current = current
        # patient info
        self.patientInfo = NameValuePairWidget(self, "Patient" )
        self.planInfo = NameValuePairWidget(self, "Plan" )
        self.ctInfo = NameValuePairWidget(self, "Planning CT" )
        self.bsInfo = NameValuePairWidget(self, "Beam Set" )
        self.gridLayoutPatientData = QtWidgets.QGridLayout()
        self.gridLayoutPatientData.addWidget(self.patientInfo,1,1)
        self.gridLayoutPatientData.addWidget(self.planInfo,2,1)
        self.gridLayoutPatientData.addWidget(self.ctInfo,1,2)
        self.gridLayoutPatientData.addWidget(self.bsInfo,2,2)
        #self.patientData = QtWidgets.QWidget()
        #self.patientData.setLayout(self.gridLayoutPatientData)
        ## collect all
        #self.vBoxlayoutPatientIO = QtWidgets.QVBoxLayout()
        #self.vBoxlayoutPatientIO.addWidget(self.patientData)
        #self.setLayout(self.vBoxlayoutPatientIO)
        self.setLayout(self.gridLayoutPatientData)
        current.Subscribe(self)
    def PlanUpdate(self):
        self.patientInfo.SetValues( *self.current.GetPatientInfo() )
        self.planInfo.SetValues(    *self.current.GetPlanInfo()    )
        self.ctInfo.SetValues(      *self.current.GetCTInfo()      )
        self.bsInfo.SetValues(      *self.current.GetBeamSetInfo() )
        self.repaint()
        #self.parentWidget().update()

# vim: set et softtabstop=4 sw=4 smartindent:
