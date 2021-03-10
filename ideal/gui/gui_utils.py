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

class NameValuePairWidget( QtWidgets.QWidget ):
    def __init__(self,parent,name):
        QtWidgets.QWidget.__init__(self,parent)
        self.vBoxlayout = QtWidgets.QVBoxLayout()
        self.name_label = QtWidgets.QLabel(name)
        self.kvbox = QtWidgets.QWidget()
        self.kvboxFormLayout = QtWidgets.QFormLayout()
        self.kvbox.setLayout(self.kvboxFormLayout)
        self.vBoxlayout.addWidget(self.name_label)
        self.vBoxlayout.addWidget(self.kvbox)
        self.setLayout(self.vBoxlayout)
    def Reset(self):
        self.vBoxlayout.removeWidget(self.kvbox)
        del self.kvboxFormLayout
        del self.kvbox
        self.kvbox = QtWidgets.QWidget()
        self.kvboxFormLayout = QtWidgets.QFormLayout()
        self.kvbox.setLayout(self.kvboxFormLayout)
        self.vBoxlayout.addWidget(self.kvbox)
    def GetName(self):
        return self.name_label.text()
    def GetValue(self):
        return self.value_label.text()
    def SetValues(self,vals,keys):
        self.Reset()
        for i,(k,v) in enumerate(zip(keys,vals)):
            #if self.kvboxFormLayout.rowCount()>i:
            #    self.kvboxFormLayout.itemAt(i,QtWidgets.QFormLayout.LabelRole).widget().setText(str(k))
            #    self.kvboxFormLayout.itemAt(i,QtWidgets.QFormLayout.FieldRole).widget().setText(str(v))
            #else:
            self.kvboxFormLayout.addRow(str(k),QtWidgets.QLabel(str(v)))
        self.parentWidget().update()

# vim: set et softtabstop=4 sw=4 smartindent:
