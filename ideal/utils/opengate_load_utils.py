#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 11:59:34 2024

@author: fava
"""
import json
from scipy.spatial.transform import Rotation
import numpy as np

def load_json(fpath):
    with open(fpath,'r') as fp:
        data = json.load(fp)
    return data

def dict_to_json(data, fpath):
    with open(fpath, 'w') as fp:
        json.dump(data,fp)
        
def setup_user_info(data):
    keys_to_remove = ['type']
    if 'rotation' in data:
        if type(data['rotation'][0]) == dict:
            # convert into rotation matrix
            rotations_list = []
            for rot in data["rotation"]:
                axis = rot["axis"]
                angle = rot["angle_deg"]
                rotation  = (Rotation.from_euler(axis, angle, degrees=True)).as_matrix()
                rotations_list.append(rotation)
            data.update(rotation = rotations_list)
        else:
            data['rotation'] = [np.array(r) for r in data['rotation']]
    for k in keys_to_remove:
        if k in data:
            data.pop(k)
            
def load_volumes_from_dict(sim,data_dict):
    for volume in data_dict["volumes"]:
        v = sim.add_volume(volume["type"], volume["name"])
        setup_user_info(volume)
        v.user_info.update(volume)
        
def load_actors_from_dict(sim,data_dict):
    for actor in data_dict["actors"]:
        a = sim.add_actor(actor['type'], actor['name'])
        setup_user_info(actor)
        a.user_info.update(actor)
        
if __name__ == '__main__':
    import os
    import opengate as gate
    sim = gate.Simulation()
    data_dir = '/opt/share/IDEAL-1_2refactored/data/MedAustronCommissioningData'
    common_dir = "/opt/share/IDEAL-1_2refactored/data/OurClinicCommissioningData/beamlines/common/"
    nozzle_fname = "nozzle_example.json"
    rifi_x_fname = "RiFi2mmX.json"
    rifi_y_fname = "RiFi2mmY.json"
    nozzle_dict = load_json(os.path.join(common_dir,nozzle_fname))
    print('loaded nozzle')
    rifi_x_dict = load_json(os.path.join(common_dir,rifi_x_fname))
    rifi_y_dict = load_json(os.path.join(common_dir,rifi_y_fname))
    print('loaded rifi')
    load_volumes_from_dict(sim,nozzle_dict)
    load_volumes_from_dict(sim,rifi_x_dict)
    load_volumes_from_dict(sim,rifi_y_dict)
    world = sim.world
    world.size = [6000, 5000, 5000]
    sim.visu = True
    sim.volume_manager.add_material_database(os.path.join(data_dir,'GateMaterials.db'))
    rifi = sim.volume_manager.get_volume("RiFi2mmX Element")
    print(rifi)
    sim.run()
    