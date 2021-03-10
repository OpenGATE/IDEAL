# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

from PyQt5 import QtWidgets

class TabJobManagement( QtWidgets.QWidget ):
    def __init__(self,details):
        QtWidgets.QWidget.__init__(self)
        self.details = details

# vim: set et softtabstop=4 sw=4 smartindent:
