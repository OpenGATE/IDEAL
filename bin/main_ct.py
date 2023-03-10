from ideal_module import *
import time
import sys

def get_user_input():
    global user_stop
    signal = input('Type stop to stop simulation')
    if signal == 'stop':
        user_stop = True
        
if __name__ == '__main__':
    
    # initialize system configuration object:
    sysconfig = initialize_sysconfig(filepath='',username='',debug=True)
    prefix="\n * "
    
    # initialize simulation
    #rp = "/user/fava/TPSdata/IR2_hbl_CTcase_1beamsets_2beams/RP1.2.752.243.1.1.20220908173524437.2800.84524.dcm"
    #rp = "/home/fava/TPSdata/01_helloWorld_box6_phys_RS8B/RP1.2.752.243.1.1.20220801133212703.1200.64476.dcm"
    #rp = "/user/fava/TPSdata/IR2_hbl_CTcase_1beamsets_1beam/RP1.2.752.243.1.1.20220908175519909.4900.28604.dcm"
    #rp = "/home/fava/TPSdata/commissioningWaterPhantom/RP1.2.752.243.1.1.20221130173300633.2200.62123_tagman.dcm"
    #rp = "/home/ideal/0_Data/02_ref_RTPlans/01_ref_Plans_CT_RTpl_RTs_RTd/02_2DOptics/01_noRaShi/E120MeVu_HBL_25spots/RP1.2.752.243.1.1.20220202141407926.4000.48815_tagman.dcm"
    #rp = "/user/fava/TPSdata/IR2_HBL_VBL_5beams_withAndWithout_RaShi/RP1.2.752.243.1.1.20221011195636370.7600.32087.dcm"
    #rp = "/home/ideal/0_Data/03_refCTs/02_AirPhantom/01_HBL/RS11B_AirPhantom_ISD60cm/RP1.2.752.243.1.1.20221212162638754.3000.70405.dcm"
    #rp = "/home/aresch/Data/05_CTs/RS11B_AirPhantom_ISD38cm_HBL_uniformLayerSpacing/RP1.2.752.243.1.1.20221214172710019.3400.45263.dcm"
    rp = "/home/fava/TPSdata/Box4_uniformPhysDose_center_SingleRightBeam/RP1.2.752.243.1.1.20220712093231484.2300.41658.dcm"
    
    # ~ rp = "/home/ideal/0_Data/03_refCTs/02_AirPhantom/01_HBL/RS11B_AirPhantom_Asymmetric/DoseGrid_2_1_3mm/RP1.2.752.243.1.1.20221215163915223.5700.52753.dcm"
    #rp = "/home/fava/TPSdata/IR2_hbl_CTcase_1beamsets_1beam/RP1.2.752.243.1.1.20220908175519909.4900.28604.dcm"
    # ~ rp = "/home/fava/artificialCT_TPSplan/RP1.2.752.243.1.1.20221215163915223.5700.52753.dcm"
    #rp = '/home/fava/TPSdata/RP1.2.752.243.1.1.20230119115736709.2000.75541.dcm'
    #rp = '/home/ideal/0_Data/05_functionalTests/01_TPSource/01_SpotPositions/01_HBL_11spots_Asym_1energyLayer/RP1.2.752.243.1.1.20230208112529712.8000.27166.dcm'
    #rp = '/home/ideal/0_Data/05_functionalTests/01_TPSource/01_SpotPositions/02_VBL_11spots_Asym_1energyLayer/RP1.2.752.243.1.1.20230208123131901.1300.38613.dcm'
    #rp = '/home/aresch/Data/06_OpenGate_TestCases/02_AbsDoseWater_5x5cmFS_120MeVn/RP1.2.752.243.1.1.20230202091405431.1510.33134.dcm'
    #rp = '/home/ideal/0_Data/05_functionalTests/01_TPSource/01_SpotPositions/03_VBL_8spots_Asym_2energyLayer/RP1.2.752.243.1.1.20230209125156239.1400.48148.dcm'
    mc_simulation = ideal_simulation('fava', rp, n_particles = 1000, n_cores = 24, condor_memory = 9000, phantom = 'air_box')
    
    # test dicom conformity
    #mc_simulation.verify_dicom_input_files()
    
    # plan specific queries
    roi_names = mc_simulation.get_plan_roi_names()
    print("ROI names in {}:{}{}".format(rp,prefix,prefix.join(roi_names)))
    
    beam_names = mc_simulation.get_plan_beam_names()
    print("Beam names in {}:{}{}".format(rp,prefix,prefix.join(beam_names)))
    
    nx,ny,nz = mc_simulation.get_plan_nvoxels()
    sx,sy,sz = mc_simulation.get_plan_resolution()
    print("nvoxels for {0}:\n{1} {2} {3} (this corresponds to dose grid voxel sizes of {4:.2f} {5:.2f} {6:.2f} mm)".format(rp,nx,ny,nz,sx,sy,sz))    
    
    # start simulation
    mc_simulation.start_simulation()

    # check stopping criteria
    mc_simulation.start_job_control_daemon()

       
    '''
    # periodically check accuracy
    stop = False
    save_curdir=os.path.realpath(os.curdir)
    t0 = None
    os.chdir(mc_simulation.cfg.workdir)
    global user_stop
    user_stop = False
    while not stop or not user_stop:
        time.sleep(150)
        if t0 is None:
            t0 = datetime.fromtimestamp(os.stat('tmp').st_ctime)
            print(f"starting the clock at t0={t0}")
        sim_time_minutes = (datetime.now()-t0).total_seconds()/60.
        # check accuracy    
        complete, stats = mc_simulation.check_accuracy(sim_time_minutes,input_stop=user_stop)
        threading.Thread(target = get_user_input).start()
        stop = complete
        print("user wants to exit simulation " + str(user_stop))
        print(stats)

    os.chdir(save_curdir)
    '''        
    # plan independent queries (ideal queries)
    # version
    print(get_version())
    
    # phantoms
    phantoms = list_available_phantoms()
    print("available phantoms: {}{}".format(prefix,prefix.join(phantoms)))
    
    # override materials
    override_materials = list_available_override_materials()
    print("available override materials: {}{}".format(prefix,prefix.join(override_materials)))
    
    # ct protocols
    protocols = get_ct_protocols()
    print("available CT protocols: {}{}".format(prefix,prefix.join(protocols)))

    # beamlines
    blmap = list_available_beamline_names()
    for beamline,plist in blmap.items():
        print("Beamline/TreatmentMachine {} has a beam model for radiation type(s) '{}'".format(beamline,"' and '".join(plist)))
