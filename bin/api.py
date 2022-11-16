#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

# generic imports
import os
import zipfile
import configparser
# ideal imports
from ideal_module import *
from utils.condor_utils import remove_condor_job, get_job_daemons, kill_process
# api imports
from flask import Flask, request, redirect, jsonify
from flask_restful import Resource, Api, reqparse
from werkzeug.utils import secure_filename

# Initialize sytem configuration once for all
sysconfig = initialize_sysconfig(username = 'myqaion')
base_dir = sysconfig['IDEAL home']
input_dir = base_dir + '/data/dicom_input/'
#base_dir = '/user/fava/Postman/files'

# api configuration
UPLOAD_FOLDER = base_dir
ALLOWED_EXTENSIONS = {'dcm', 'zip'}

app = Flask(__name__)
api = Api(app)

# List of all active jobs. Members will be simulation objects
jobs_list = dict()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def get_file(file_key):
    if file_key not in request.files:
        # TODO: error message, in which form?
        return redirect(request.url)
    file = request.files[file_key]
    if file.filename == '':
        # TODO: error message, in which form?
        return redirect(request.url)
    if file: # and allowed_file(file):
        return file    
        
def unzip(dir_name):
    extension = ".zip"
    os.chdir(dir_name)
    for item in os.listdir(dir_name):
        if item.endswith(extension):
            file_name = os.path.abspath(item)
            zip_ref = zipfile.ZipFile(file_name) # create zipfile object
            zip_ref.extractall(dir_name)
            zip_ref.close()
            os.remove(file_name)

def read_ideal_job_status(cfg_settings):
    cfg = configparser.ConfigParser()
    cfg.read(cfg_settings)
    status = cfg['DEFAULT']['status']
    
    return status

def generate_input_folder(input_dir,filename,username):
    rp = filename.split('.zip')[0]
    folders = [i for i in os.listdir(input_dir) if (username in i) and (rp in i)]
    index = len(folders)+1
    ID = username + '_' + str(index) + '_' + rp
    # create data dir for the job
    datadir = input_dir + ID
    os.mkdir(datadir)
    
    return datadir, rp
    

if __name__ == '__main__':

    @app.route("/version")
    def version():
        return get_version()
    
    
    @app.route("/jobs", methods=['POST'])
    def start_new_job():        
        # get data from client
        if request.method == 'POST':
            # RP dicom
            rp_file = get_file('DicomRtPlan')
            rp_filename = secure_filename(rp_file.filename)
            # RS dicom
            rs_file = get_file('DicomStructureSet')
            # CT dicom
            ct_file = get_file('DicomCTs')
            # RD dicom
            rd_file = get_file('DicomRDose')
            
            # username
            arg_username = request.form.get('Username')
            if arg_username is None:
                return "Error, no username given."
            
            # stopping criteria
            arg_number_of_primaries_per_beam = request.form.get('NumberOfParticles')
            if arg_number_of_primaries_per_beam is None:
                arg_number_of_primaries_per_beam = 0
            else: 
                arg_number_of_primaries_per_beam = int(request.form.get('NumberOfParticles'))
    
            arg_percent_uncertainty_goal = request.form.get('Uncertainty')
            if arg_percent_uncertainty_goal is None:
                arg_percent_uncertainty_goal = 0
            else:
                arg_percent_uncertainty_goal = float(arg_percent_uncertainty_goal)
        
        
        datadir, rp = generate_input_folder(input_dir,rp_filename,arg_username)
        app.config['UPLOAD_FOLDER'] = datadir
        
        #save files in folder
        rp_file.save(os.path.join(datadir,rp_file.filename))
        rs_file.save(os.path.join(datadir,rs_file.filename))
        ct_file.save(os.path.join(datadir,ct_file.filename))
        rd_file.save(os.path.join(datadir,rd_file.filename))
        
        # unzip dicom data
        unzip(datadir)
        
        # create simulation object
        dicom_file = datadir + '/' + rp
        sysconfig.override('username',arg_username)
        mc_simulation = ideal_simulation(arg_username,dicom_file,n_particles = arg_number_of_primaries_per_beam,
                                         uncertainty=arg_percent_uncertainty_goal)
        
        # check dicom files
        ok, missing_keys = mc_simulation.verify_dicom_input_files()
        
        if not ok:
            msg = {'missing keys in dicom files': missing_keys}
            return jsonify(msg)
        
        # Get job UID
        jobID = mc_simulation.outputdir.split("/")[-1]
        
        # start simulation and append to list  
        mc_simulation.start_simulation()
        jobs_list[jobID] = mc_simulation
        
        # check stopping criteria
        mc_simulation.start_job_control_daemon()

                
        return jobID

    @app.route("/jobs/<jobId>/status", methods=['GET'])
    def get_status(jobId):
        # alternative, simpler version:
        cfg_settings = jobs_list[jobId].settings
        status = read_ideal_job_status(cfg_settings)
        return jsonify({'status': status})
        
    
    @app.route("/jobs/<jobId>", methods=['DELETE'])
    def stop_job(jobId):
        args = request.args
        cancellation_type = args.get('cancelationType')
        
        if jobId not in jobs_list:
            return 'job already completed or not launched'

        if cancellation_type=='soft':
            simulation = jobs_list[jobId]
            simulation.soft_stop_simulation(simulation.cfg)
        if cancellation_type=='hard':
            condorId = jobs_list[jobId].condor_id
            remove_condor_job(condorId)
        
        # kill job control daemon
        daemons = get_job_daemons('job_control_daemon.py')
        kill_process(daemons[simulation.workdir])
        
        return cancellation_type

    app.run()
    

    

# vim: set et softtabstop=4 sw=4 smartindent:
