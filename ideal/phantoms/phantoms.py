#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 29 15:07:55 2023

@author: fava
"""
import opengate as gate
from scipy.spatial.transform import Rotation

def add_phantom(sim, phantom_name, dose_name, gantry_angle = 90):
    
    cm = gate.g4_units.cm
    mm = gate.g4_units.mm
    
    phantom = sim.add_volume("Box", "phantom")
    dose = sim.add_actor("DoseActor", dose_name)
    r = Rotation.from_euler("z", gantry_angle, degrees=True)
    
    if phantom_name == 'peak_finder':
        phantom.size = [500 * mm, 500 * mm, 400 * mm]
        phantom.rotation = (Rotation.from_euler("y", 90, degrees=True)).as_matrix()
        phantom.translation = [-200.0, 0.0, 0.0]
        phantom.material = "G4_WATER"
        
        detector = sim.add_volume("Tubs", f"{phantom_name}_{gantry_angle}")
        detector.mother = phantom.name
        detector.material = "G4_WATER"
        detector.rmax = 40.3 * mm
        detector.rmin = 0
        detector.dz = 200 * mm
        
        dose.attached_to = detector.name
        dose.size = [1, 1, 8000]
        dose.spacing = [80.6, 80.6, 0.05]
        
    if phantom_name == 'peak_finder_vbl':
        phantom.size = [400 * mm, 400 * mm, 400 * mm]
        phantom.rotation = (Rotation.from_euler("x", 90, degrees=True)).as_matrix()
        phantom.translation = [0.0, 200.0, 0.0]
        phantom.material = "G4_WATER"
        
        detector = sim.add_volume("Tubs", f"{phantom_name}_{gantry_angle}")
        detector.mother = phantom.name
        detector.material = "G4_WATER"
        detector.rmax = 40.3 * mm
        detector.rmin = 0
        detector.dz = 200 * mm
        
        dose.attached_to = detector.name
        dose.size = [1, 1, 8000]
        dose.spacing = [80.6, 80.6, 0.05]
        
    if phantom_name == 'air_box':
        phantom.size = [600 * mm, 310 * mm, 310 * mm]
        #phantom.rotation = r.as_matrix()
        phantom.translation = [300.0, 0., 0.]
        phantom.material = "G4_AIR"       
        detector = phantom
        
        dose.attached_to = detector.name
        dose.size = [300, 620, 620]
        dose.spacing = [2, 0.5, 0.5]
        dose.score_in = 'water'
        
    if phantom_name == 'air_box_vbl':
        phantom.size = [310 * mm, 600 * mm, 310 * mm]
        phantom.rotation = (Rotation.from_euler("z", -90, degrees=True)).as_matrix()
        phantom.translation = [0.0, -300.0, 0]
        phantom.material = "G4_AIR"       
        detector = phantom
        
        dose.attached_to = detector.name
        dose.size = [620, 60, 620]
        dose.spacing = [0.5, 10., 0.5]
        dose.score_in = 'water'
    
    # if phantom_name == 'peak_finder' or phantom_name == 'peak_finder_vbl':
    #     phantom.size = [400 * mm, 400 * mm, 400 * mm]
    #     phantom.rotation = (r*Rotation.from_euler("x", 90, degrees=True)).as_matrix()
    #     phantom.translation = list(r.apply([0.0, 200.0, 0.0]))
    #     phantom.material = "G4_WATER"
        
    #     detector = sim.add_volume("Tubs", f"{phantom_name}_{gantry_angle}")
    #     detector.mother = phantom.name
    #     detector.material = "G4_WATER"
    #     detector.rmax = 40.3 * mm
    #     detector.rmin = 0
    #     detector.dz = 200 * mm
        
    #     dose.attached_to = detector.name
    #     dose.size = [1, 1, 8000]
    #     dose.spacing = [80.6, 80.6, 0.05]
        
    # if phantom_name == 'air_box' or phantom_name == 'air_box_vbl':
    #     phantom.size = [310 * mm, 600 * mm, 310 * mm]
    #     phantom.rotation = r.as_matrix()
    #     phantom.translation = list(r.apply([0.0, -300.0, 0]))
    #     phantom.material = "G4_AIR"       
    #     detector = phantom
        
    #     dose.attached_to = detector.name
    #     dose.size = [620, 300, 620]
    #     dose.spacing = [0.5, 2, 0.5]
        
    return detector, dose
