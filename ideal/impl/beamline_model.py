# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import os
import logging
import utils.opengate_load_utils as utils
import beamlines.config as config
from beamlines.beamlines import get_beamline_model_from_config
logger=logging.getLogger(__name__)

class beamlines:
    print('creating beamlines container object')
    cache = dict()
    
    def add_beamline_model(self,beamline_model):
        beamline = beamline_model.beamline_name
        beamline_model.check_passive_elements()
        if beamline not in beamlines.cache:
            beamlines.cache[beamline] = dict()
        rad_type = beamline_model.radiation_type
        if rad_type in beamlines.cache[beamline]:
            logger.warning(f'CAREFUL! Beamline model for {beamline} with radiation type {rad_type} already in the cache. Adding a new beamline model will override the previous one.')
        logger.debug(f'Adding beamline model for {beamline} with radiation type {rad_type}')
        beamlines.cache[beamline][rad_type] = beamline_model
        
    @property
    def available_beamlines(self):
        return list(beamlines.cache.keys())
    
    @property
    def available_beamline_models(self):
        models = ['_'.join([b,r]) for b in beamlines.cache.keys() for r in beamlines.cache[b].keys()]
        return models
    
    def has_radtype(self, beamline_name, radtype):
        return bool(radtype in beamlines.cache[beamline_name])
    
    def get_beamline_radtypes(self,beamline_name):
        return list(beamlines.cache[beamline_name].keys())
    
    def get_beamline_model(self,beamline,radtype):
        if not beamline in beamlines.cache:
            raise RuntimeError(f'No beamline model available for beamline {beamline}')
        if not radtype in beamlines.cache[beamline]:
            raise RuntimeError(f'No beamline model available for beamline {beamline} with radiation type {radtype}')
        return beamlines.cache[beamline][radtype]
    

class beamline_model:
    def __init__(self,fpath, data_dir = None):
        self.configuration_file_path = fpath
        self.load_from_file()
        self.beamline_name = self._config.source_details.beamline_name.upper()
        self.name = os.path.basename(fpath).strip('.json')
        self._rad_type = self.name.replace(f'{self.beamline_name}_','').upper()
        self._nozzle_fname = self._config.geometry_details.nozzle_file_name
        if data_dir:
            self._nozzle_dir = data_dir
        else:
            self._nozzle_dir = self._config.geometry_details.nozzle_directory

    
    def load_from_file(self,fpath=None):
        if not fpath:
            fpath = self.configuration_file_path
        self._config = config.load_config_from_json(fpath)
        
    def dump_to_file(self, fpath):
        config.dump_config_to_json(self._config, fpath)
        
    @property
    def configuration_file_path(self):
        return self._configuration_file_path
    
    @configuration_file_path.setter
    def configuration_file_path(self,fpath):
        if not os.path.exists(fpath):
            raise FileNotFoundError(f'Could not find configuration file {fpath} for beamline {self.name}')
        self._configuration_file_path = fpath
    
    @property
    def radiation_type(self):
        return self._rad_type
        
    @property
    def radiation_type_opengate(self):
        return self._config.source_details.radiation_type
          
    @property
    def nozzle_file_path(self):
        self._nozzle_fpath = os.path.join(self._nozzle_dir,self._nozzle_fname)
        return self._nozzle_fpath
    
    @property
    def rm_labels(self):
        return self._config.geometry_details.range_modulators
    
    @property
    def rs_labels(self):
        return self._config.geometry_details.range_shifters
    
    @property
    def source_details(self):
        return self._config.source_details
    
    def get_element_filepath(self, label):
        return os.path.join(self._nozzle_dir,label) + '.json'
    
    def check_passive_elements(self):
        labels = [*self.rm_labels, *self.rs_labels]
        for name in labels:
            fpath = os.path.join(self._nozzle_dir,name) + '.json'
            if not os.path.exists(fpath):
                raise FileNotFoundError(f'Beam model {self.name} has details for passive element {name}, but the configuration file {fpath} does not exist')           
    
    def add_nozzle_opengate(self, sim):
        nozzle_volumes = utils.load_json(self.nozzle_file_path)
        utils.load_volumes_from_dict(sim,nozzle_volumes)
        return sim.volume_manager.get_volume("NozzleBox")
        
    def add_element_opengate(self, sim, label):
        path = self.get_element_filepath(label)
        volumes = utils.load_json(path)
        utils.load_volumes_from_dict(sim,volumes)
            
    def get_beamline_opengate(self):
        b = get_beamline_model_from_config(self.source_details)
        return b
            
            
if __name__ == '__main__':
    import opengate as gate
    sim = gate.Simulation()
    data_dir = '/opt/share/IDEAL-1_2refactored/data/OurClinicCommissioningData/'
    sim.volume_manager.add_material_database(os.path.join(data_dir,'GateMaterials.db'))
    world = sim.world
    world.size = [6000, 5000, 5000]
    bml_name = 'IR2HBL'
    rad_type = 'ION_6_12_6'
    beamlines_dir = '/opt/share/IDEAL-1_2refactored/data/OurClinicCommissioningData/beamlines'
    fpath = '/opt/share/IDEAL-1_2refactored/data/OurClinicCommissioningData/beamlines/IR2HBL/IR2HBL_ION_6_12_6.json'
    ir2hblc = beamline_model(fpath)
    beamlines_cont = beamlines()
    beamlines_cont.add_beamline_model(ir2hblc)
    print(beamlines_cont.available_beamline_models)
    ir2hblc.add_nozzle_opengate(sim)
    ir2hblc.add_rs_opengate(sim,['RS3cmR1'])
    ir2hblc.add_rm_opengate(sim,['RiFi2mmX','RiFi2mmY'])
    print(sim.volume_manager.dump_volume_tree())
    sim.run()

# vim: set et softtabstop=4 sw=4 smartindent:
