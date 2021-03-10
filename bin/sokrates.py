#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import sys,os
try:
    from PyQt5 import QtWidgets
except ImportError as ie:
    print("To enable the 'sokrates' GUI, install the 'PyQt5' python module, e.g. with 'pip install PyQt5'. See also: the installation manual.")
    sys.exit(0)

import logging
from impl.system_configuration import get_sysconfig
from impl.dual_logging import get_dual_logging
from impl.idc_details import IDC_details

     
from gui.IDEAL import MainWindow

def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v","--verbose",default=False,action='store_true',
            help="be verbose during startup (once the GUI runs, you can toggle terminal output verbosity)")
    parser.add_argument("-d","--debug",default=False,action='store_true',
            help="debugging mode: do not delete any temporary/intermediate data")
    parser.add_argument("-S","--sysconfig",default="",
            help="alternative system configuration file (default is <installdir>/cfg/system.cfg")
    parser.add_argument("-l","--username",
            help="The user name will be included in paths of output & logging files & directories, in order to make it easier to know which user requested which simulations (default: your login name).")
    args = parser.parse_args()

    return args
 
if __name__ == '__main__':
    args = get_args()
    sysconfig = get_sysconfig(filepath = args.sysconfig,
                              verbose  = args.verbose,
                              debug    = args.debug,
                              username = args.username)
    logger = logging.getLogger()
    logger.debug("Create GUI-independt object that encapsulates the implementation details.")
    current_details = IDC_details(sysconfig)
    logger.debug("Start the GUI framework.")
    app = QtWidgets.QApplication(sys.argv)
    logger.debug("Create the main window with all tabs.")
    mainwindow = MainWindow(current_details)
    current_details.set_gui_main(mainwindow)
    logger.debug("Show it ...")
    mainwindow.show()
    logger.debug("... and run until exit.")
    sys.exit(app.exec_())

# vim: set et softtabstop=4 sw=4 smartindent:
