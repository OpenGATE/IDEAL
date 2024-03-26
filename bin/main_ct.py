from ideal_module import *
import impl.dicom_functions as dcm
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
    #rp = '/home/aresch/Data/09_ClinicalPatients/10_tagman/Pat_c3/bs1/RP1.2.752.243.1.1.20230503083217300.1066.37543.dcm'
    rp = '/home/ideal/0_Data/02_ref_RTPlans/IR2HBLc/05_FrameFactor/ISD50cm_RS/200.0MeV/OF_F1_corrected/OF_F1_corrected_tagman.dcm'
    rp = '/home/ideal/0_Data/02_ref_RTPlans/IR2HBLc/01_IDDs/ISD0cm/E120.0MeV/RP1.2.752.243.1.1.20230802152802865.1390.13763_tagman.dcm'
    rp = '/home/ideal/0_Data/02_ref_RTPlans/IR2HBLc/02_2DOptics/02_wRaShi/163p8/RP1.2.752.243.1.1.20220331135858368.2000.86552_tagman.dcm'
    rp = '/home/ideal/0_Data/02_ref_RTPlans/IR2VBLc/01_IDDs/ISD0cm/E306MeVn/RP1.2.752.243.1.1.20230510110808347.8200.36853_tagman.dcm'
    rp = '/home/ideal/0_Data/02_ref_RTPlans/IR2VBLc/04_3D/1_refBox/ISD40/Box_4_(0_0_19)_C_ISD40cm_Bio/RP1.2.752.243.1.1.20200803120552125.6520.56536_tagman.dcm'
    rp = '/home/ideal/0_Data/02_ref_RTPlans/IR2VBLc/04_3D/1_refBox/ISD40/Box_4_(0_0_5)_C_ISD40cm_Bio/RP1.2.752.243.1.1.20200731175326463.1800.17870_tagman.dcm'
    rp = '/home/ideal/0_Data/02_ref_RTPlans/01_ref_Plans_CT_RTpl_RTs_RTd/04_3Ddose/1_refBox/ISD0/Box6_pos006_C_ISD0cm_PhysRef/RP1.2.752.243.1.1.20190416091436601.4300.60587_tagman.dcm'

    # test dicom conformity
    ok_rp, mk = dcm.check_RP(rp)
    print(mk)
    #exit()
    
    #mc_simulation = ideal_simulation('fava', rp, uncertainty = 7, n_cores = 24, condor_memory = 9000)
    mc_simulation = ideal_simulation('fava', rp, n_particles=5e7, n_cores = 72)#, phantom='peak_finder')#, phantom = 'semiflex_hbl_isd0')uncertainty = 20
    
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
    #mc_simulation.start_job_control_daemon()

       
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
