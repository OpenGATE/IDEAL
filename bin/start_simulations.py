import itk
import argparse
import configparser
import glob
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation
import pathlib
from nozzle.nozzle import add_nozzle
from phantoms.phantoms import add_phantom
from beamlines.beamlines import get_beamline_model
import opengate as gate
from opengate.contrib.tps.ionbeamtherapy import spots_info_from_txt, TreatmentPlanSource
from opengate.dicom.radiation_treatment import ct_image_from_mhd, get_container_size
from opengate.geometry.materials import read_voxel_materials
from opengate.tests import utility

def get_info_from_cfg(workdir):
    cfg_data = dict()
    postprocessor_cfg = configparser.ConfigParser()
    postprocessor_cfg.read(os.path.join(workdir,'postprocessor.cfg'))
    cfg_data['mhd_out_names'] = dict()
    # sections are beam names
    cfg_data['beam_names'] = []
    for section in postprocessor_cfg.sections():
        if section in ['DEFAULT', 'user logs file']:
            continue
        mhd = postprocessor_cfg[section]['dosemhd']
        cfg_data['beam_names'].append(section)
        cfg_data['mhd_out_names'][section] = mhd
    output_dir = postprocessor_cfg['DEFAULT']['first output dicom']
    user_cfg = configparser.ConfigParser()
    user_cfg.read(glob.glob(output_dir + os.path.sep + 'user_logs*'))
    rad_type = user_cfg['BS']['radiation type'].lower().replace('_',' ')
    cfg_data['treatment machine'] = user_cfg['BS']['treatment machine(s)']
    cfg_data['ion type'] = ' '.join(rad_type.split()[:-1]) if 'ion' in rad_type else rad_type
    cfg_data['nb of beams'] = int(user_cfg['BS']['number of beams'])
    cfg_data['ct filename'] = user_cfg['Plan']['sop instance uid'].replace('.','_') + '.mhd'
    cfg_data['Rashis'] = dict()
    cfg_data['RangeMods'] = dict()
    for key, value in user_cfg['Passive Elements'].items():
        for beam_name in cfg_data['beam_names']:
            if beam_name.lower() in key.lower() and 'range shifters' in key.lower():
                cfg_data['Rashis'][beam_name] = False if value == '(none)' else value.split()
            if beam_name.lower() in key.lower() and 'range modulators' in key.lower():
                cfg_data['RangeMods'][beam_name] = False if value == '(none)' else value.split()
                
    return cfg_data
    
def define_run_timing_intervals(
    n_part_per_core, n_part_check, n_threads, skip_first_n_part=0, n_last_run=1000
):
    sec = gate.g4_units.second
    n_tot_planned = n_part_per_core * n_threads
    if skip_first_n_part == 0:
        run_timing_intervals = []
        start_0 = 0
    else:
        run_timing_intervals = [[0, (skip_first_n_part / n_tot_planned) * sec]]
        start_0 = (skip_first_n_part / n_tot_planned) * sec

    end_last = (n_last_run / n_tot_planned) * sec
    n_runs = round(((n_tot_planned - skip_first_n_part - n_last_run) / n_part_check))
    # print(n_runs)

    # end = start + 1 * sec / n_runs
    end = start_0 + (1 * sec - start_0 - end_last) / n_runs
    start = start_0
    for r in range(n_runs):
        run_timing_intervals.append([start, end])
        start = end
        end += (1 * sec - start_0 - end_last) / n_runs

    run_timing_intervals.append([start, start + end_last])
    # print(run_timing_intervals)

    return run_timing_intervals

def run_sim_single_beam(rungate_workdir, cfg_data, n_particles = 0, stat_unc = 0, beam_nr=1, phantom_name = None, output_path = '', seed=None, n_threads=1, save_plots = False, gamma_index=False):

    # some variables we will probably read from config:
    beam_name = cfg_data['beam_names'][beam_nr -1]
    mhd_out_name = cfg_data['mhd_out_names'][beam_name]
    ct_filename = cfg_data['ct filename']
    treatment_machine = cfg_data['treatment machine']
    ion_type = cfg_data['ion type']
    flag_RiFi_1 = bool(cfg_data['RangeMods'][beam_name][0])
    flag_RiFi_2 =  bool(cfg_data['RangeMods'][beam_name][1])
    flag_RaShi = bool(cfg_data['Rashis'][beam_name])

    if not output_path :
        output_path = '/opt/share/IDEAL-1_2ref/'
        
        # create output dir, if it doesn't exist
    if not os.path.isdir(output_path):
        os.makedirs(output_path)
        print(f"Created: {output_path}")
    
    print(f'output_path={output_path}, phantom = {phantom_name}')    
    #output_path = pathlib.Path(output_path)
    ct_dir = os.path.join(rungate_workdir,'data','CT')
    data_dir = os.path.join(rungate_workdir,'data')
    
    # create the simulation
    sim = gate.Simulation()
    
    # main options
    sim.g4_verbose = False
    sim.g4_verbose_level = 1
    sim.visu = False
    sim.number_of_threads = n_threads
    # if seed:
    #     sim.random_seed = seed
    sim.random_engine = "MersenneTwister"
    sim.output_dir = output_path
    
    # units
    km = gate.g4_units.km
    cm = gate.g4_units.cm
    mm = gate.g4_units.mm
    um = gate.g4_units.um
    MeV = gate.g4_units.MeV
    
    # lookup tables
    hu2mat_file = os.path.join(ct_dir,'commissioning-HU2mat.txt')
    
    # add a material database
    #sim.add_material_database(os.path.join(ct_dir,'commissioning-HUmaterials.db'))
    sim.volume_manager.add_material_database(os.path.join(data_dir,'GateMaterials.db'))
    
    #  change world size
    world = sim.world
    world.size = [600 * cm, 500 * cm, 500 * cm]
    
    # get treatment plan
    plan_txt = glob.glob(args.workdir+ os.path.sep + 'data'+ os.path.sep + 'TreatmentPlan4Gate*')[0]
    beam_data_dict = spots_info_from_txt(plan_txt, ion_type, beam_nr)
    gantry_angle = beam_data_dict['gantry_angle']
    isocenter = beam_data_dict['isocenter']
    couch_angle = beam_data_dict['couch_angle']
    
    # add nozzle geometry
    nozzlebox = add_nozzle(sim, gantry_angle = gantry_angle, flag_RiFi_1 = flag_RiFi_1, flag_RiFi_2 = flag_RiFi_2, flag_RaShi = flag_RaShi)
    
  
    # set target
    dose_name = 'dose'
    
    if not phantom_name:
        mhd_ct_path = os.path.join(ct_dir, ct_filename)
        ct_cropped = itk.imread(mhd_ct_path)
        preprocessed_ct = ct_image_from_mhd(ct_cropped)
        img_origin = preprocessed_ct.origin
        origin_when_centered = (
            -(preprocessed_ct.physical_size) / 2.0 + preprocessed_ct.voxel_size / 2.0
        )
        print(f'{img_origin = }')
        print(f'{preprocessed_ct.physical_size = }')
        print(f'{preprocessed_ct.voxel_size = }')

        # get transl and rot for correct ct positioning
        iso = np.array(isocenter)

        # container
        phantom = sim.add_volume("Box", "phantom")
        phantom.size = get_container_size(ct_cropped,isocenter)
        print(f'{phantom.size = }')
        #phantom.translation = list((img_origin - origin_when_centered) - iso)
        phantom.rotation = Rotation.from_euler("y", -couch_angle, degrees=True).as_matrix()
        phantom.material = "G4_AIR"
        phantom.color = [0, 0, 1, 1]
        print(f"{iso = }")
        print(f"{couch_angle = }")

        # patient
        patient = sim.add_volume("Image", "patient")
        patient.image = mhd_ct_path
        patient.mother = phantom.name
        patient.translation = list((- origin_when_centered + img_origin) - iso)
        patient.material = "G4_AIR"  # material used by default
        patient.voxel_materials = read_voxel_materials(hu2mat_file)

        print(f'{patient.translation = }')
        
        # add dose actor
        dose = sim.add_actor("DoseActor", dose_name)
        dose.attached_to = patient.name
        n = 1
        dose.size = list(n*preprocessed_ct.nvoxels)
        dose.spacing = list(preprocessed_ct.voxel_size/n)
        dose.score_in = 'water'
        dose.output_coordinate_system = 'attached_to_image'
        sim.physics_manager.set_max_step_size(patient.name, 0.8)

    else:
        detector, dose = add_phantom(sim, phantom_name, dose_name, gantry_angle = gantry_angle)
        
        sim.physics_manager.set_max_step_size(detector.name, 0.5)
        
    dose.output_filename =  mhd_out_name
    dose.dose.active = True
    dose.hit_type = "random"
    dose.user_output.dose_uncertainty.active = False
    #dose.use_more_ram = True
    print(dose)
    
    print(f'{dose.size = }')
    
    # physics
    sim.physics_manager.physics_list_name =  'QGSP_BIC_EMZ' #'QGSP_INCLXX_HP_EMZ'
    #p.physics_list_name = "FTFP_INCLXX_EMZ"
    sim.physics_manager.set_production_cut("world", "all", 1000 * km)

    
    if stat_unc:
        dose.ste_of_mean = True
        dose.goal_uncertainty = stat_unc
        dose.thresh_voxel_edep_for_unc_calc = 0.4
    
    ## beamline model
    beamline = get_beamline_model(treatment_machine, ion_type)
 
    ## source
    n_part_per_core = n_particles if n_threads == 0  else round(n_particles/n_threads)
    #nplan = beam_data_dict['msw_beam']
    nSim = n_part_per_core  # 328935  # particles to simulate per beam
    
    tps = sim.add_source("TreatmentPlanPBSource",f"beam_{beam_nr}")
    tps.beam_model = beamline
    tps.n = nSim
    tps.beam_data_dict = beam_data_dict
    tps.sorted_spot_generation = False
    tps.particle = ion_type
    #actual_n_sim = tps.actual_sim_particles
    
    # define how often to check uncertainty
    sec = gate.g4_units.second
    if stat_unc:
        skip_first_n_part = 1e5 #if n_particles > 5e6 else n_particles/10
        n_part_check = 1e5 #if n_particles > 1e6 else round(n_particles/100)
        run_timing_intervals = define_run_timing_intervals(
            n_part_per_core, n_part_check, n_threads, skip_first_n_part=skip_first_n_part, n_last_run=1000)
        #run_timing_intervals =list( np.array(run_timing_intervals)/sec)
        print(f'{run_timing_intervals = }')

    else:
        run_timing_intervals = [[0, 1*sec]]
    sim.run_timing_intervals = run_timing_intervals
    
    start_sim = True
    if start_sim:
        # add stat actor
        stat = sim.add_actor("SimulationStatisticsActor", "Stats")
        stat.track_types_flag = True
        #stat.output_filename =  'stats.txt'
        sim.run(start_new_process=True)
        print(stat)
        utility.write_stats_txt_gate_style(stat,os.path.join(output_path,'stats.txt'))

    mhd_path = dose.dose.get_output_path()
    #img_mhd_out = itk.imread(mhd_path)
    
    
    # if not phantom_name:
    #     print('updating dose image origine')
    #     img_mhd_out.SetOrigin(preprocessed_ct.origin)
    #     itk.imwrite(img_mhd_out, mhd_path)

if __name__ == '__main__':

    aparser = argparse.ArgumentParser(description="""
Nice program to launch a simulation in gate10
""", formatter_class=argparse.RawDescriptionHelpFormatter)
    aparser.add_argument("-w","--workdir",help="working directory for all jobs")
    aparser.add_argument("-N","--n_particles",type=int,default=0,help="number of particles to simulate")
    aparser.add_argument("-u","--stat_uncertainty",type=float,default=0.,help="goal statistical uncertainty")
    aparser.add_argument("-o","--outputdir",help="Output folder path")
    aparser.add_argument("-s","--seed",type=int,default=None,help="Seed for simulation")
    aparser.add_argument("-nt","--number_of_threads",type=int,default=1,help="Number of threads")
    aparser.add_argument("-p","--phantom_name",type=str,default=None,help="phantom name")
    
    args = aparser.parse_args()
    phantom_name = None if args.phantom_name == 'None' else args.phantom_name
    # get treatment plan 
    cfg_data = get_info_from_cfg(args.workdir)
    
    for beam_nr in range(cfg_data['nb of beams']):
        run_sim_single_beam(args.workdir, cfg_data, n_particles = args.n_particles, stat_unc = args.stat_uncertainty, 
                            beam_nr = beam_nr+1, output_path=args.outputdir, seed=args.seed, 
                            n_threads = args.number_of_threads, phantom_name=phantom_name)
    
