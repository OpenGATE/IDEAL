#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 12:35:47 2024
@author: fava
"""
from dataclasses import dataclass, asdict
from enum import Enum
import dacite
import utils.opengate_load_utils as utils

class Convergence(Enum):
    CONVERGENT = 1
    DIVERGENT = 0
    
@dataclass
class SourceConfiguration:
    # general info
    beamline_name : str
    radiation_type : str
    
    # Nozzle entrance to Isocenter distance
    distance_nozzle_iso: float
    # SMX to Isocenter distance
    distance_stearmag_to_isocenter_x : float
    # SMY to Isocenter distance
    distance_stearmag_to_isocenter_y : float
    
    # polinomial coefficients energy
    energy_mean_coeffs  : list
    energy_spread_coeffs: list
    # polinomial coefficients optics
    sigma_x_coeffs : list
    theta_x_coeffs : list
    epsilon_x_coeffs : list
    sigma_y_coeffs : list
    theta_y_coeffs : list
    epsilon_y_coeffs: list
    # beam convergence
    conv_x : Convergence
    conv_y: Convergence

@dataclass
class GeometryConfiguration:
    nozzle_directory : str
    nozzle_file_name : str
    range_shifters: list
    range_modulators: list

@dataclass
class BeamlineModel:
    source_details : SourceConfiguration
    geometry_details : GeometryConfiguration
    
def load_config_from_json(json_path):
    raw_cfg = utils.load_json(json_path)
      
    converters =  {
        Convergence: lambda x: Convergence[x]
        }
    
    # create and validate the Configuration object
    config = dacite.from_dict(
        data_class=BeamlineModel, data=raw_cfg,
        config=dacite.Config(type_hooks=converters),
     )
    
    return config

def dump_config_to_json(beamline_model,fpath):
    beamline_model.source_details.conv_x = beamline_model.source_details.conv_x.name
    beamline_model.source_details.conv_y = beamline_model.source_details.conv_y.name
    cfg_dict = asdict(beamline_model)
    utils.dict_to_json(cfg_dict, fpath)

if __name__ == '__main__':
    json_path = '/opt/share/IDEAL-1_2refactored/data/OurClinicCommissioningData/beamlines/IR2HBL/IR2HBL_ION_6_12_6.json'
    cfg = load_config_from_json(json_path)
    
    fpath = '/home/fava/test_json_dump.json'
    dump_config_to_json(cfg, fpath)
