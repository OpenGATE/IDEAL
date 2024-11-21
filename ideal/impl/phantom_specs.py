# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import numpy as np
import os
import utils.opengate_load_utils as utils
import logging
from scipy.spatial.transform import Rotation
logger=logging.getLogger(__name__)

class phantom_specs:
    def __init__(self,dirname,label):
        assert(os.path.isdir(dirname))
        phantom_fpath = os.path.join(dirname,label) + '.json'
        if not os.path.exists(phantom_fpath):
            raise IOError("file {} for phantom '{}' not found".format(phantom_fpath,label))
        self._phantom_fpath = phantom_fpath
        self._label = label
        self.raw_data = self.load_config(phantom_fpath)
        self._check_phantom_in_file()
        self._setup_phantom_metadata()

    def __str__(self):
        return self.label
    
    def __repr__(self):
        return self.label
    
    def load_config(self,phantom_fpath):
        return utils.load_json(phantom_fpath)
                
    def _check_phantom_in_file(self):
        # phantom name should be both in the volume and actors section
        v_ok = False
        a_ok = True
        for v in self.raw_data['volumes']:
            if v["name"] == self.label:
                v_ok = True  
                break
        for a in self.raw_data['actors']:
            if a["attached_to"] == self.label:
                a_ok = True  
                break
        if not (v_ok and a_ok):
            raise ValueError(f'phantom {self.label} is not described in the file {self.file_path}')
            
    def _setup_phantom_metadata(self):
        self.volume_info = [v for v in self.raw_data['volumes'] if v['name'] == self.label][0]
        self.dose_info = [a for a in  self.raw_data['actors'] if a['attached_to']][0]
        self._voxel_size = np.array(self.dose_info['spacing'])
        self._nvoxels = np.array(self.dose_info['size'])
        self._grid_size = self._voxel_size*self._nvoxels
        d2w = True
        if 'score_in' in self.dose_info:
            d2w = self.dose_info['score_in'] == 'water'
        self._dose_to_water = d2w
        self._help_text = f''''
    Phantom label: {self.label}
    voxel size: {self.dose_voxel_size}
    n voxel: {self.dose_nvoxels}
    dose to water: {self.dose_to_water}
'''
        
    def add_phantom_opengate(self,sim):
        utils.load_volumes_from_dict(sim, self.raw_data)
        utils.load_actors_from_dict(sim, self.raw_data)
        detector = sim.volume_manager.get_volume(self.label)
        for actor in sim.actor_manager.actors.values():
            if actor.user_info.attached_to == self.label:
                dose = actor
                break
        
        return detector, dose
            
    @property
    def file_path(self):
        return self._phantom_fpath
    @property
    def label(self):
        return self._label
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
        return {"label":self.label,"cfg":self.file_path}

if __name__ == '__main__':
    import opengate as gate
    dirname = '/opt/share/IDEAL-1_2refactored/data/OurClinicCommissioningData/phantoms/'
    label = 'peak_finder'
    Phantom = phantom_specs(dirname,label)
    sim = gate.Simulation()
    print(Phantom.help_text)
    Phantom.add_phantom_opengate(sim)
    print(sim.volume_manager.dump_volume_tree())
    sim.run()

# vim: set et softtabstop=4 sw=4 smartindent:
