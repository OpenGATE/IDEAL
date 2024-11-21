#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 13:39:17 2023

@author: fava
"""

from opengate.contrib.beamlines.ionbeamline import BeamlineModel

def get_beamline_model_from_config(beamline_data):
    beamline = BeamlineModel()
    beamline.name = beamline_data.beamline_name
    beamline.radiation_types = beamline_data.radiation_type
    # Nozzle entrance to Isocenter distance
    beamline.distance_nozzle_iso = beamline_data.distance_nozzle_iso
    # SMX to Isocenter distance
    beamline.distance_stearmag_to_isocenter_x = beamline_data.distance_stearmag_to_isocenter_x
    # SMY to Isocenter distance
    beamline.distance_stearmag_to_isocenter_y = beamline_data.distance_stearmag_to_isocenter_y
    
    # polinomial coefficients energy
    beamline.energy_mean_coeffs = beamline_data.energy_mean_coeffs
    beamline.energy_spread_coeffs = beamline_data.energy_spread_coeffs
    # polinomial coefficients optics
    beamline.sigma_x_coeffs = beamline_data.sigma_x_coeffs
    beamline.theta_x_coeffs = beamline_data.theta_x_coeffs
    beamline.epsilon_x_coeffs = beamline_data.epsilon_x_coeffs
    beamline.sigma_y_coeffs = beamline_data.sigma_y_coeffs
    beamline.theta_y_coeffs = beamline_data.theta_y_coeffs
    beamline.epsilon_y_coeffs = beamline_data.epsilon_y_coeffs
    # beam convergence
    beamline.conv_x = beamline_data.conv_x.value
    beamline.conv_y = beamline_data.conv_y.value
    
    return beamline

