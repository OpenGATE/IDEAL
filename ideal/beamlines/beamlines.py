#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 13:39:17 2023

@author: fava
"""

from opengate.contrib.beamlines.ionbeamline import BeamlineModel

def get_beamline_model(treatment_machine, ion_type, full_nozzle = True):
    valid_beamlines = ['ir2hbl','ir2vbl']
    valid_ion_types = ['proton', 'ion 6 12']
    ion_type = ion_type.lower()
    treatment_machine = treatment_machine.lower()
    
    name_map = {'proton': 'p',
                'ion 6 12': 'c'}
    
    if treatment_machine not in valid_beamlines:
        raise ValueError(f'Beamline {treatment_machine} not valid. Valid beamline names are: {valid_beamlines}')
        
    if ion_type not in valid_ion_types:
        raise ValueError(f'{ion_type} not valid. Valid ion types names are: {valid_ion_types}')
    
    beamline_name = treatment_machine + name_map[ion_type]
    beamline = BeamlineModel()
    
    if beamline_name.lower() == 'ir2hblc':
        beamline.name = beamline_name
        beamline.radiation_types = 'ion 6 12'
        # Nozzle entrance to Isocenter distance
        beamline.distance_nozzle_iso = 1300.00  # 1648 * mm#1300 * mm
        # SMX to Isocenter distance
        beamline.distance_stearmag_to_isocenter_x = 7420.00
        # SMY to Isocenter distance
        beamline.distance_stearmag_to_isocenter_y = 6700.00
        # polinomial coefficients
        beamline.energy_mean_coeffs = [-1.83481739e-09,5.89084156e-06,-3.63090091e-03,1.26758582e+01,-6.16308889e+01]
        # [-5.86216222e-15, 7.91870677e-12 ,-3.97643490e-09  ,8.18415708e-07,-4.34642534e-06 ,-2.63326460e-02  ,1.59812266e+01 ,-1.99456215e+02]
        beamline.energy_spread_coeffs = [1.00827097e-08,-1.21039188e-05,5.18035576e-03,-8.93161239e-01,5.14070469e+01]
        
        if full_nozzle:
            # IDEAL v1
            beamline.sigma_x_coeffs = [ -5.80689e-14, 9.10249e-11, -5.75230e-8, 1.85977e-5, -3.20430e-3, 2.74490e-1, -7.133]
            beamline.theta_x_coeffs = [8.10201e-18, -1.75709e-14, 1.44445e-11, -5.82592e-9, 1.22471e-6, -1.28547e-4, 6.066e-3]
            beamline.epsilon_x_coeffs = [-5.74235e-16, 9.12245e-13, -5.88501e-10, 1.96763e-7, -3.58265e-5, 3.35307e-3, -122.935e-3]
            beamline.sigma_y_coeffs = [-1.07268e-13, 1.61558e-10, -9.92211e-8, 3.19029e-5,-5.67757e-3, 5.29884e-1, -17.749]
            beamline.theta_y_coeffs = [-1.13854e-17, 1.52020e-14, -7.49359e-12, 1.57991e-9, -8.98373e-8 ,-1.30862e-5, 1.638e-3]
            beamline.epsilon_y_coeffs = [-2.54669e-16, 3.71028e-13, -2.14188e-10, 6.21900e-8, -9.46711e-6, 7.09187e-4, -19.511e-3]
            beamline.conv_x = 0
            beamline.conv_y = 0
    
        else:
            pass
            
    if beamline_name.lower() == 'ir2vblc':
        beamline.name = beamline_name
        beamline.radiation_types = 'ion 6 12'
        # Nozzle entrance to Isocenter distance
        beamline.distance_nozzle_iso = 1300.00  # 1648 * mm#1300 * mm
        # SMX to Isocenter distance
        beamline.distance_stearmag_to_isocenter_x = 1000000.00
        # SMY to Isocenter distance
        beamline.distance_stearmag_to_isocenter_y = 31000.00
        # polinomial coefficients
        beamline.energy_mean_coeffs = [-1.83481739e-09,5.89084156e-06,-3.63090091e-03,1.26758582e+01,-6.16308889e+01]
        beamline.energy_spread_coeffs = [1.00827097e-08,-1.21039188e-05,5.18035576e-03,-8.93161239e-01,5.14070469e+01]
        
        if full_nozzle:
            # IDEAL v1
            beamline.sigma_x_coeffs = [-9.842040084750049e-14,1.4339239619766868e-10,-8.271300478138489e-08,2.3887095991373426e-05,-0.0036003649890835572,0.2684471421714016,-5.725996573705991]
            beamline.theta_x_coeffs = [1.7306128888988973e-16,-2.5800923401980013e-13,1.543253632465758e-10,-4.721266952313676e-08,7.774183442544784e-06,-0.0006554678402801344,0.022766840436389536]
            beamline.epsilon_x_coeffs = [9.809056503915192e-16,-1.4470482267954518e-12,8.496200773395331e-10,-2.520139114008825e-07,3.943827090345832e-05,-0.0030559640552833803,0.09196185027440158]
            beamline.sigma_y_coeffs = [-5.6222378692239063e-14,6.688337175002942e-11,-2.8756419486286192e-08,5.075107008176484e-06,-0.00021101148868636196,-0.02727620004128624,3.881984663971355]
            beamline.theta_y_coeffs = [4.815848032362203e-18,-8.136687787495001e-15,5.5206943316987364e-12,-1.9826149605530987e-09,4.1926942469801947e-07,-5.247564092461628e-05,0.003156874459486511]
            beamline.epsilon_y_coeffs = [-8.977876709717306e-17,1.26304810509032e-13,-7.239629805208852e-11,2.180962101911428e-08,-3.6532906278332863e-06,0.0003200067328890606,-0.01089371576631501]
            beamline.conv_x = 0
            beamline.conv_y = 0
            # beamline.sigma_x_coeffs = [1.5943942747298905e-12, -1.3573008720583147e-09, 4.582494119002659e-07, -7.8544354717104e-05, 0.007207549950494291, -0.33167765844386016, 8.242022737546591]
            # beamline.theta_x_coeffs = [1.577334659523127e-15, -1.3623650519619609e-12, 4.691882906324577e-10, -8.195174429018992e-08, 7.603277739411377e-06, -0.00035280493020203987, 0.006576743055613493]
            # beamline.epsilon_x_coeffs = [8.415001763307367e-15, -7.333560409003245e-12, 2.56258765250337e-09, -4.572846534847599e-07, 4.373103911460697e-05, -0.0021166272398411077, 0.04069276856096986]
            # beamline.sigma_y_coeffs = [-2.4894008941855016e-13, 4.213681305374646e-10, -2.3628675499640942e-07, 6.081430457156373e-05, -0.007777446520947233, 0.47991199076968244, -8.530125004481272]
            # beamline.theta_y_coeffs = [-3.476239709218675e-16, 4.294280965414517e-13, -2.047104316932742e-10, 4.792294091911703e-08, -5.716998795434794e-06, 0.00031774236542247476, -0.004762733182449692]
            # beamline.epsilon_y_coeffs = [-2.884870072901028e-15, 2.7172809079602575e-12, -1.029124645035029e-09, 1.9918636854484521e-07, -2.0572845483371444e-05, 0.0010584957501051184, -0.01953782873054139]
        else:
           pass
       
    return beamline