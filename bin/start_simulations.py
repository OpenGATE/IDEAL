import itk
import argparse
import glob
import os
import importlib
import numpy as np
from scipy.spatial.transform import Rotation
import pathlib
#from nozzle.nozzle import add_nozzle
from impl.phantom_specs import phantom_specs
import impl.beamline_model as bm
import opengate as gate
from opengate.contrib.tps.ionbeamtherapy import spots_info_from_txt
from opengate.dicom.radiation_treatment import ct_image_from_mhd, get_container_size
from opengate.geometry.materials import read_voxel_materials
from opengate.tests import utility
from config import SimConfiguration


def run_sim_single_beam(rungate_workdir, cfg_data_obj, beam_name,n_particles = 0, stat_unc = 0, phantom_name = None, output_path = '', seed=None, n_threads=1, save_plots = False, gamma_index=False):
    
    if stat_unc == 0:
        stat_unc = None
        
    # some variables we will probably read from config:
    cfg_data = cfg_data_obj.simulation_data_dict[beam_name]
    mhd_out_name = cfg_data['beam_dose_mhd']
    ion_type = cfg_data['radtype']
    beam_nr = cfg_data['beamnr']
    rm_labels =  cfg_data['rmids']
    rs_labels = cfg_data['rsids']

    if not output_path :
        output_path = '/opt/share/IDEAL-1_2ref/'
        
        # create output dir, if it doesn't exist
    if not os.path.isdir(output_path):
        os.makedirs(output_path)
        print(f"Created: {output_path}")
    
    print(f'output_path={output_path}, phantom = {phantom_name}')    
    #output_path = pathlib.Path(output_path)
    #ct_dir = os.path.join(rungate_workdir,'data','CT')
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

    
    # add a material database
    #sim.add_material_database(os.path.join(ct_dir,'commissioning-HUmaterials.db'))
    sim.volume_manager.add_material_database(os.path.join(data_dir,'GateMaterials.db'))
    
    #  change world size
    world = sim.world
    world.size = [600 * cm, 500 * cm, 500 * cm]
    
    # get treatment plan
    plan_txt = glob.glob(rungate_workdir+ os.path.sep + cfg_data['spotfile'])[0]
    beam_data_dict = spots_info_from_txt(plan_txt, ion_type, beam_nr)
    # maybe read from cfg_data
    gantry_angle = cfg_data['gantry_angle']
    gantry_rot = Rotation.from_euler('z', gantry_angle, degrees=True)
    
    ## beamline model
    beamline_cfg_path = cfg_data_obj.get_beamline_cfg_path(beam_name)
    beamline_model_obj = bm.beamline_model(beamline_cfg_path,data_dir=data_dir)
    beamline = beamline_model_obj.get_beamline_opengate()
    
    # add nozzle geometry
    nozzle = beamline_model_obj.add_nozzle_opengate(sim)
    nozzle_rot_g0 = Rotation.from_matrix(nozzle.rotation)
    nozzle.rotation = (gantry_rot * nozzle_rot_g0).as_matrix()
    nozzle.translation = list(gantry_rot.apply(nozzle.translation))

    # passive elelments
    beamline_model_obj.add_rm_opengate(sim,rm_labels)
    beamline_model_obj.add_rs_opengate(sim,rs_labels)
  
    # set target
    dose_name = 'dose'
    
    if not phantom_name:
        # run with CT geometry
        mhd_ct_path = cfg_data['ct_mhd']
        # lookup tables
        hu2mat_file = cfg_data['HU2mat']
        # patient positioning
        isocenter = cfg_data['isoC']
        couch_angle = cfg_data['mod_patient_angle']
        
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
        Phantom = phantom_specs(data_dir, phantom_name)
        detector, dose = Phantom.add_phantom_opengate(sim)
        
        
        sim.physics_manager.set_max_step_size(detector.name, 0.5)
        
    dose.output_filename =  mhd_out_name
    dose.dose.active = True
    dose.hit_type = "random"
    dose.dose_uncertainty.active = False
    #dose.use_more_ram = True
    print(dose)
    
    print(f'{dose.size = }')
    
    # physics
    sim.physics_manager.physics_list_name =  cfg_data['physicslist']
    sim.physics_manager.set_production_cut("world", "all", 1000 * km)

    
    if stat_unc:
        dose.uncertainty_goal = stat_unc
        dose.uncertainty_voxel_edep_threshold = 0.4
        dose.uncertainty_first_check_after_n_events = 1e5
    
 
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

    start_sim = True
    if start_sim:
        # add stat actor
        stat = sim.add_actor("SimulationStatisticsActor", "Stats")
        stat.track_types_flag = True
        #stat.output_filename =  'stats.txt'
        sim.run(start_new_process=False)
        print(stat)
        utility.write_stats_txt_gate_style(stat,os.path.join(output_path,'stats.txt'))

    mhd_path = dose.dose.get_output_path()


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
    
    cfg_data = SimConfiguration(os.path.join(args.workdir,'opengate_simulation.json'))
    
    for beam_name in cfg_data.beam_names:
        run_sim_single_beam(args.workdir, cfg_data, beam_name, n_particles = args.n_particles, stat_unc = args.stat_uncertainty, 
                            output_path=args.outputdir, seed=args.seed, n_threads = args.number_of_threads, phantom_name=phantom_name)
    
