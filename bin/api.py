#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

# generic imports
import os
import uuid
import zipfile
import configparser
# ideal imports
import job_manager
from ideal_module import *
from utils.condor_utils import get_jobs_status, remove_condor_job
# api imports
from flask import Flask, request, redirect, jsonify
from flask_restful import Resource, Api, reqparse
from werkzeug.utils import secure_filename

# Initialize sytem configuration once for all
sysconfig = initialize_sysconfig(username = 'myqaion')
base_dir = sysconfig['IDEAL home']
#base_dir = '/user/fava/Postman/files'

# api configuration
UPLOAD_FOLDER = base_dir
ALLOWED_EXTENSIONS = {'dcm', 'zip'}

app = Flask(__name__)
api = Api(app)

# Config parser with job manager configurations
cfg_parser = configparser.ConfigParser()
file_abs_path = os.path.abspath(__file__)
ideal_dir = os.path.dirname(os.path.dirname(file_abs_path))
daemon_cfg = ideal_dir + "/cfg/log_daemon.cfg"
cfg_parser.read(daemon_cfg)

# Job manager to keep track jobs
status_manager = job_manager.log_manager(cfg_parser)

# List of all active jobs. Members will be simulation objects
jobs_list = dict()

# Function to generate UID for new jobs
def generate_job_UID():
    return uuid.uuid4().hex

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def get_and_save_file(file_key,datadir):
    if file_key not in request.files:
        # TODO: error message, in which form?
        return redirect(request.url)
    file = request.files[file_key]
    if file.filename == '':
        # TODO: error message, in which form?
        return redirect(request.url)
    if file: # and allowed_file(file):
        filename = secure_filename(file.filename)
        print(filename)
        file.save(os.path.join(datadir,filename))
        return filename
    
        
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

def remove_completed_jobs_from_list(jlist,manager):
    for key, item in jlist.copy().items():
        if manager.parser[key]['Condor status'] not in manager.end_status:
            del jlist[key]

def read_ideal_job_status(cfg_settings):
    cfg = configparser.ConfigParser()
    cfg.read(cfg_settings)
    status = cfg['DEFAULT']['status']
    
    return status


if __name__ == '__main__':

    @app.route("/version")
    def version():
        return get_version()
    
    
    @app.route("/jobs", methods=['POST'])
    def start_new_job():
        # create data dir for the job
        jobID = generate_job_UID()
        datadir = base_dir + '/data/dicom_input/' + jobID
        os.mkdir(datadir)
        app.config['UPLOAD_FOLDER'] = datadir
        
        # get data from client
        if request.method == 'POST':
            # RP dicom
            rp_filename = get_and_save_file('DicomRtPlan',datadir)	
            # RS dicom
            get_and_save_file('DicomStructureSet',datadir)
            # CT dicom
            get_and_save_file('DicomCTs',datadir)
            # RD dicom
            get_and_save_file('DicomRDose',datadir)
            
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
            
        # unzip dicom data
        unzip(datadir)
        
        # get dicom filepath
        rp = rp_filename.split('.zip')[0]
        dicom_file = datadir + '/' + rp
        
        # create simulation object  
        sysconfig.override('username',arg_username)
        mc_simulation = ideal_simulation(arg_username,dicom_file,n_particles = arg_number_of_primaries_per_beam,
                                         uncertainty=arg_percent_uncertainty_goal)
        # start simulation and append to list  
        mc_simulation.start_simulation()
        jobs_list[jobID] = mc_simulation
        
        # create new section in the job_manager
        status_manager.add_section(jobID,mc_simulation.workdir,mc_simulation.submission_date,mc_simulation.condor_id,mc_simulation.settings)
        print(status_manager.parser.sections())
        
        # check stopping criteria
        #mc_simulation.periodically_check_accuracy(150) 
        mc_simulation.start_job_control_daemon()
        
        # remove completed jobs from the list
        #remove_completed_jobs_from_list(jobs_list,status_manager)
                
        return jobID

    @app.route("/jobs/<jobId>/status", methods=['GET'])
    def get_status(jobId):
        # ~ status_manager.update_log_file()
        # ~ job_status = status_manager.parser[jobId]
        #return jsonify(dict(job_status))
        
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
            
        return cancellation_type

    app.run()
    

    

# vim: set et softtabstop=4 sw=4 smartindent:
