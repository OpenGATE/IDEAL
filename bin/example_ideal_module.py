import impl.ideal_module as idc
import time
import sys

if __name__ == '__main__':
    
    # initialize system configuration object:
    sysconfig = idc.initialize_sysconfig(filepath='',username='',debug=True)
    prefix="\n * "
    
    # initialize simulation
    #rp = "/home/ideal/0_Data/02_ref_RTPlans/IR2HBLc/01_IDDs/ISD0cm/E120.0MeV/RP1.2.752.243.1.1.20230802152802865.1390.13763_tagman.dcm"
    rp = "/home/ideal/0_Data/02_ref_RTPlans/01_ref_Plans_CT_RTpl_RTs_RTd/02_2DOptics/01_noRaShi/01_HBL/E120MeVu/RP1.2.752.243.1.1.20220202141407926.4000.48815_tagman.dcm"
    beamline_override = None
    ct_protocol = None
    mc_simulation = idc.ideal_simulation('fava', rp, n_particles=1000., n_threads=4, n_cores=1)#,phantom='air_box')
    # other available options: uncertainty,time_limit, n_cores, condor_memory, phantom... see /opt/share?IDEAL-1_1release/bin/ideal_module.py for more
    
    # test dicom conformity
    mc_simulation.verify_dicom_input_files()
    
    # read in data
    mc_simulation.read_in_data(verify=False)
    
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

    # check stopping criteria in the background
    #mc_simulation.start_job_control_daemon()
     
    # plan independent queries (ideal queries)
    # version
    print(idc.get_version())
    
    # phantoms
    phantoms = idc.list_available_phantoms()
    print("available phantoms: {}{}".format(prefix,prefix.join(phantoms)))
    
    # override materials
    override_materials = idc.list_available_override_materials()
    print("available override materials: {}{}".format(prefix,prefix.join(override_materials)))
    
    # ct protocols
    protocols = idc.get_ct_protocols()
    print("available CT protocols: {}{}".format(prefix,prefix.join(protocols)))

    # beamlines
    blmap = idc.list_available_beamline_names()
    for beamline,plist in blmap.items():
        print("Beamline/TreatmentMachine {} has a beam model for radiation type(s) '{}'".format(beamline,"' and '".join(plist)))
