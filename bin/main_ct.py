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
    phantom = None #'air_box'
    # initialize simulation

    #rp = '/var/data/IDEAL/io/IDEAL_ro/Commissioning/IR2Hc/1_IRPDs/120/RP1.2.752.243.1.1.20201014092550939.3300.30673.dcm'
    rp = '/home/ideal/0_Data/10_PatientData/08_Anon_Patient_FOR_GATE_HBL/RP1.2.752.243.1.1.20240419161735713.2140.37143.dcm'
    
    # test dicom conformity
    ok_rp, mk = dcm.check_RP(rp)
    print(mk)
    #exit()
    
    #mc_simulation = ideal_simulation('fava', rp, uncertainty = 7, n_cores = 24, condor_memory = 9000)
    mc_simulation = ideal_simulation('fava', rp, n_particles=5000000,ct_protocol='Ad_Pl_Abd3mm')#, phantom = 'semiflex_hbl_isd0')
    
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
