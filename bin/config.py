#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 15:30:20 2024

@author: fava
"""

import json

class SimConfiguration:
    def __init__(self,path):
        self.simulation_data_dict = self.get_info_from_cfg(path)
        self.beam_names = list(self.simulation_data_dict.keys())
     
    def get_beamline_cfg_path(self,beam_name):
        return self.simulation_data_dict[beam_name]["beamline_cfg_path"]
    
    def read_json_cfg(self,path):
        with open(path, 'r') as file:
            data = json.load(file)
        return data
    
    def get_info_from_cfg(self,path):
        cfg_dict = self.read_json_cfg(path)
        for beam_name in cfg_dict.keys():
            rad_type = cfg_dict[beam_name]['radtype'].lower()
            is_generic_ion = 'ion' in rad_type
            cfg_dict[beam_name]['radtype'] = ' '.join(rad_type.split('_')[:-1]) if is_generic_ion else rad_type
            cfg_dict[beam_name]['mass number'] = float(rad_type.split('_')[2]) if is_generic_ion else 1
                    
        return cfg_dict
        

if __name__ == '__main__':
    path = '/var/work/IDEAL-1_2ref/yjia_IDEAL_1_1_acc_v0_IDEAL_comm_IR2HBLc_IDD_ISD50_IR2HBLc_E213_4_1_2024_11_10_16_00_18/rungate.0/opengate_simulation.json'
    sim_cfg = SimConfiguration(path)
     