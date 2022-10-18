#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

from ideal_module import *
from flask import Flask, request
from flask_restful import Resource, Api, reqparse

if __name__ == '__main__':
    app = Flask(__name__)
    api = Api(app)
    
    
    @app.route("/")
    def show_parameters():
        return """To retrieve the version : make any request to /version\n
                To start a computation : make a POST request to /calc\n
                Please include the following keys/values in the form data of the POST request:\n
                file\t:\tDICOM planfile with a sequence of ion beams.\n 
                dicom_planfile\t:\tpath to DICOM planfile with a sequence of ion beams.\n
                NOTE that file will overwrite any input given by dicom_file!\n
                username\t:\tThe user name will be included in paths of output & logging files & directories, in order to make it easier to know which user requested which simulations.\n
                debug\t:\tdebugging mode: do not delete any temporary/intermediate data.(FLAG)\n
                score_dose_on_full_CT\t:\tdebugging feature: write out dose on CT grid (i.e. no resampling to TPS dose resolution and the CT will not be cropped, but material overrides WILL be performed).(FLAG)\n
                beams\t:\tConfig: list of beams that should be simulated (default: all)\n
                list_beam_names\t:\tQuery: list of beam names defined in a given treatment plan.(FLAG)\n
                CT_protocol\t:\tConfig: which CT protocol (HU to density calibration curve) to use.\n
                list_available_CT_protocols\t:\tQuery: list which CT protocols (HU to density calibration curve) are available.(FLAG)\n
                phantom\t:\tConfig: which phantom to use.\n
                list_available_phantoms\t:\tQuery: list which phantoms can be used.(FLAG)\n
                list_roi_names\t:\tQuery: list which ROI names are defined in the structure set used by the input plan(s).(FLAG)\n
                nvoxels\t:\tConfig: number of dose grid voxels per dimension, i.e. 13 5 41.\n
                default_nvoxels\t:\tQuery: list default number of dose grid voxels per dimension, for a given treatment plan.(FLAG)\n
                beamline_override\t:\tConfig: override the beamline (treatment machine) for all beams. Default: use for each beam the treatment machine given by DICOM plan.\n
                list_available_beamline_names\t:\tQuery: list the names of the available beam line (treatment machine) models.(FLAG)\n
                padding_material\t:\tConfig: name of material to use for padding the CT in case the dose matrix sticks out.\n
                material_overrides\t:\tConfig: list of material override specifications of the form 'ROINAME:MATERIALNAME'.\n
                list_available_override_materials\t:\tQuery: list which override materials can be used in the -n (padding material) and -m (ROI-wise material override) options.(FLAG)\n
                sysconfig\t:\tConfig: alternative system configuration file (default is <installdir>/cfg/system.cfg.\n
                number_of_cores\t:\tStats: Number of concurrent subjobs to run per beam (if 0: njobs = number of cores as given in the system configuration file).\n
                number_of_primaries_per_beam\t:\tStats: number of primary ions to simulate.\n
                percent_uncertainty_goal\t:\tStats: average uncertainty to achieve in dose distribution.\n
                time_limit_in_minutes\t:\tStats: number of minutes each simulation job is allowed to run. Actual simulation time will be at least 5 minutes longer due to pre- and post-processing, as well as possible queue waiting time.\n
                """ #TODO HTML format correctly, works on Postman though 

    @app.route("/version")
    def get_version():
        return get_version()
    
    @app.route("/login", methods=['POST'])
    def get_username():
        arg_username = request.form.get('username')
        initialize_sysconfig(username = arg_username)
        return 'hello ' + arg_username
    
    @app.route("/login/CT_protocols") # must be called after get_username
    def list_ct_protocols():
        protocols = get_ct_protocols()
        prefix="\n * "
        return "available CT protocols: {}{}".format(prefix,prefix.join(protocols))
    
    @app.route("/login/override_materials") # must be called after get_username
    def list_override_materials():
        override_materials = list_available_override_materials()
        prefix="\n * "
        return "available override materials: {}{}".format(prefix,prefix.join(override_materials))

    @app.route("/login/phantoms") # must be called after get_username
    def list_phantoms():
        phantoms = list_available_phantoms()
        prefix="\n * "
        return "available phantoms: {}{}".format(prefix,prefix.join(phantoms))
    
    @app.route("/login/beamlines") # must be called after get_username
    def list_beamlines():
        blmap = list_available_beamline_names()
        prefix="\n * "
        return "available beamlines: {}{}".format(prefix,prefix.join(blmap))

    
    @app.route("/login/initialize", methods=['POST'])
    def initialize_simulation():
        # Necessary inputs
        arg_file = request.files.get('file')
        input_file_path = "/home/username/Downloads/IDEAL-1.0.0-rc.0/bin/INPUT_FILE" # TODO make somehow relative
        prefix="\n * "
#        if arg_file is not None:
#            arg_file.save(input_file_path)
#            command_from_api.append(input_file_path)
#        else:
        arg_dicom_file = request.form.get('dicom_file')
        if arg_dicom_file is None:
            return "Error, no dicom given."

        arg_username = request.form.get('username')
        if arg_username is None:
            return "Error, no username given."
                  
        arg_number_of_primaries_per_beam = request.form.get('number_of_primaries_per_beam')
        print("type n. particles: "+str(type(arg_number_of_primaries_per_beam)))
        if arg_number_of_primaries_per_beam is None:
            arg_number_of_primaries_per_beam = 0
        else: 
            arg_number_of_primaries_per_beam = int(request.form.get('number_of_primaries_per_beam'))

        arg_percent_uncertainty_goal = request.form.get('percent_uncertainty_goal')
        print("type uncertainty: "+str(type(arg_percent_uncertainty_goal)))
        if arg_percent_uncertainty_goal is None:
            arg_percent_uncertainty_goal = 0
        else:
            arg_percent_uncertainty_goal = float(arg_percent_uncertainty_goal)
        
        arg_time_limit_in_minutes = request.form.get('time_limit_in_minutes')
        print("type timeout: "+str(type(arg_time_limit_in_minutes)))
        if arg_time_limit_in_minutes is None:
            arg_time_limit_in_minutes = 0
        else:
            arg_time_limit_in_minutes = int(arg_time_limit_in_minutes)
            
        # create simulation object  
        global mc_simulation
        mc_simulation = ideal_simulation(arg_username,arg_dicom_file,n_particles = arg_number_of_primaries_per_beam,
                                         uncertainty=arg_percent_uncertainty_goal,time_limit=arg_time_limit_in_minutes) 
        
        # plan queries
        arg_list_beam_names = request.form.get('list_beam_names') # Query TODO
        if arg_list_beam_names is not None:
            beam_names = mc_simulation.get_plan_beam_names()
            return "Beam names in {}:{}{}".format(arg_dicom_file,prefix,prefix.join(beam_names))

        arg_list_roi_names = request.form.get('list_roi_names') # Query TODO
        if arg_list_roi_names is not None:
            roi_names = mc_simulation.get_plan_roi_names()
            return "ROI names in {}:{}{}".format(arg_dicom_file,prefix,prefix.join(roi_names))

        arg_default_nvoxels = request.form.get('default_nvoxels') # Query TODO
        if arg_default_nvoxels is not None:
            	nx,ny,nz = mc_simulation.get_plan_nvoxels()
            	sx,sy,sz = mc_simulation.get_plan_resolution()
            	return "nvoxels for {0}:\n{1} {2} {3} (this corresponds to dose grid voxel sizes of {4:.2f} {5:.2f} {6:.2f} mm)".format(arg_dicom_file,nx,ny,nz,sx,sy,sz)
        
        
        # set other inputs when given
        
#        arg_test_dicom = request.form.get('test dicom')
#        if arg_test_dicom is not None:
#            command_from_api.append(f"-TD{arg_test_dicom}")

#        arg_debug = request.form.get('debug_mode')
#        if arg_debug is not None:
#            command_from_api.append("-d")

        arg_score_dose_on_full_CT = request.form.get('score_dose_on_full_CT')
        if arg_score_dose_on_full_CT is not None:
            mc_simulation.score_dose_on_full_CT = arg_score_dose_on_full_CT
        
        arg_beams = request.form.get('beams')
        if arg_beams is not None:
            mc_simulation.beams = arg_beams

        arg_CT_protocol = request.form.get('CT_protocol')
        if arg_CT_protocol is not None:
            mc_simulation.ctprotocol = arg_CT_protocol

        arg_nvoxels = request.form.get('nvoxels')
        if arg_nvoxels is not None:
            mc_simulation.nvoxels = arg_nvoxels       

        arg_beamline_override = request.form.get('beamline_override')
        if arg_beamline_override is not None:
            mc_simulation.beamline_override = arg_beamline_override

        arg_padding_material = request.form.get('padding_material')
        if arg_padding_material is not None:
            mc_simulation.padding_material = arg_padding_material

        arg_material_overrides = request.form.get('material_overrides')
        if arg_material_overrides is not None:
            mc_simulation.material_overrides = arg_material_overrides

#        arg_sysconfig = request.form.get('sysconfig')
#        if arg_sysconfig is not None:
#            command_from_api.append(f"-s{arg_sysconfig}")

        arg_number_of_cores = request.form.get('number_of_cores')
        if arg_number_of_cores is not None:
            mc_simulation.number_of_cores = int(arg_number_of_cores)
                
        return "simulation object initialized"
    
    @app.route("/login/initialize/check_dicoms")
    def check_dicoms():
        return mc_simulation.verify_dicom_input_files()
    
    @app.route("/login/initialize/start")
    def start_simulation():
        mc_simulation.start_simulation()
        #mc_simulation.periodically_check_accuracy(150)
        return "simulation started!"   
    
    @app.route("/login/initialize/periodically_check_accuracy")
    def periodically_check_accuracy():
        mc_simulation.periodically_check_accuracy(150)
        return mc_simulation.stats
    
    @app.route("/login/initialize/start/accuracy")
    def check_accuracy():
        stats = mc_simulation.check_accuracy()
        return stats
    
    @app.route("/login/initialize/rois")
    def get_roi_names():
        rois = mc_simulation.get_plan_roi_names()
        prefix="\n * "
        return "beams in the treatment plan: {}{}".format(prefix,prefix.join(rois))
    
    @app.route("/login/initialize/resolution")
    def get_resolution():
        nx,ny,nz = mc_simulation.get_plan_nvoxels()
        sx,sy,sz = mc_simulation.get_plan_resolution()
        return "nvoxels:\n{0} {1} {2} (this corresponds to dose grid voxel sizes of {3:.2f} {4:.2f} {5:.2f} mm)".format(nx,ny,nz,sx,sy,sz)
    
    @app.route("/login/initialize/beams")
    def get_beams():
        beams = mc_simulation.get_plan_beam_names()
        prefix="\n * "
        return "beams in the treatment plan: {}{}".format(prefix,prefix.join(beams))
    

    app.run()

# vim: set et softtabstop=4 sw=4 smartindent:
