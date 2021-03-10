# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import numpy as np
import os
import configparser
import logging
logger=logging.getLogger(__name__)

class phantom_specs:
    def __init__(self,dirname,label):
        assert(os.path.isdir(dirname))
        mac=os.path.join(dirname,label)+".mac"
        cfg=os.path.join(dirname,label)+".cfg"
        for f in [mac,cfg]:
            if not os.path.exists(f):
                raise IOError("file {} for phantom '{}' not found".format(f,label))
        self._mac = mac
        phantom_parser = configparser.ConfigParser()
        phantom_parser.read(cfg)
        docs=phantom_parser["documentation"]
        self._label=label
        self._tooltip=docs["tooltip"]
        self._gui_name=docs["gui name"]
        self._help_text=docs["help text"]
        dosegrid=phantom_parser["dose grid"]
        self._grid_size=np.array( ( dosegrid.getfloat("x grid size [mm]"),
                                    dosegrid.getfloat("y grid size [mm]"),
                                    dosegrid.getfloat("z grid size [mm]") ) )
        self._nvoxels=np.array( ( dosegrid.getint("number of x voxels"),
                                  dosegrid.getint("number of y voxels"),
                                  dosegrid.getint("number of z voxels") ) )
        self._voxel_size=self._grid_size/self._nvoxels
        self._dose_to_water=dosegrid.getboolean("dose to water")
        logger.debug("label={} name='{}', tooltip='{}' help=\n'{}'".format(self.label,self.gui_name,self.tooltip,self.help_text))
        logger.debug("grid size (x,y,z) = {} mm".format(tuple(self.dose_grid_size)))
        logger.debug("# voxels (x,y,z) = {}".format(tuple(self.dose_nvoxels)))
        logger.debug("voxel size (x,y,z) = {} mm".format(tuple(self.dose_voxel_size)))
        logger.debug("dose to water conversion: {}".format("YES" if self.dose_to_water else "NO"))
    def __repr__(self):
        return self._gui_name
    def __str__(self):
        return self._gui_name
    @property
    def mac_file_path(self):
        return self._mac
    @property
    def label(self):
        return self._label
    @property
    def tooltip(self):
        return self._tooltip
    @property
    def gui_name(self):
        return self._gui_name
    @property
    def help_text(self):
        return self._help_text
    @property
    def dose_grid_size(self):
        return self._grid_size.copy()
    @property
    def dose_voxel_size(self):
        return self._voxel_size.copy()
    @property
    def dose_nvoxels(self):
        return self._nvoxels.copy()
    @property
    def dose_to_water(self):
        return self._dose_to_water
    @property
    def meta_data(self):
        return {"label":self._label,"mac":self._mac,"cfg":self._mac.replace("mac","cfg")}

# vim: set et softtabstop=4 sw=4 smartindent:
