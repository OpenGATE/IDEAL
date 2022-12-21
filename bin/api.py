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
import hashlib
import time
# ideal imports
from ideal_module import *
from utils.condor_utils import remove_condor_job, get_job_daemons, kill_process, zip_files
from utils.api_utils import transfer_files_to_server, get_api_cfg
# api imports
from flask import Flask, request, redirect, jsonify, Response, send_file, send_from_directory
from flask_restful import Resource, Api, reqparse
from werkzeug.utils import secure_filename

# Initialize sytem configuration once for all
sysconfig = initialize_sysconfig(username = 'myqaion')
base_dir = sysconfig['IDEAL home']
input_dir = sysconfig["input dicom"]
log_dir = sysconfig['logging']
daemon_cfg = os.path.join(base_dir,'cfg/log_daemon.cfg')
log_parser = configparser.ConfigParser()
log_parser.read(daemon_cfg)
api_cfg = get_api_cfg(log_parser['Paths']['api_cfg'])
commissioning_dir = sysconfig['commissioning']

# api configuration
UPLOAD_FOLDER = base_dir
ALLOWED_EXTENSIONS = {'dcm', 'zip'}

app = Flask(__name__)
api = Api(app)

# List of all active jobs. Members will be simulation objects
jobs_list = dict()

def timestamp():
    return time.strftime("%Y_%m_%d_%H_%M_%S")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS  
        
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
    if 'RUNNING GATE' in status:
        status = 'running'
    elif status == 'submitted':
        pass
    elif 'POSTPROCESSING' in status and 'FAILED' not in status:
        status = 'postprocessing'
    elif status == 'FINISHED':
        status = 'finished'
    elif 'FAILED' in status:
        status = 'failed'
    else:
        status = 'waiting'
    
    return status

def generate_input_folder(input_dir,filename,username):
    rp = filename.split('.zip')[0]
    folders = [i for i in os.listdir(input_dir) if (username in i) and (rp in i)]
    index = len(folders)+1
    ID = username + '_' + str(index) + '_' + rp
    # create data dir for the job
    datadir = os.path.join(input_dir,ID)
    os.mkdir(datadir)
    
    return datadir, rp

def sha1_directory_checksum(path):
    digest = hashlib.sha1()

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ['phantoms']]
        for names in files:
            file_path = os.path.join(root, names)

            # Hash the path and add to the digest to account for empty files/directories
            digest.update(hashlib.sha1(file_path[len(path):].encode()).digest())

            # Per @pt12lol - if the goal is uniqueness over repeatability, this is an alternative method using 'hash'
            # digest.update(str(hash(file_path[len(path):])).encode())

            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f_obj:
                    while True:
                        buf = f_obj.read(1024 * 1024)
                        if not buf:
                            break
                        digest.update(buf)

    return digest.hexdigest()
    

if __name__ == '__main__':

    @app.route("/version")
    def version():
        return get_version()
    
    
    @app.route("/jobs", methods=['POST'])
    def start_new_job():        
        # get data from client

        # RP dicom
        if 'dicomRtPlan' not in request.files:
            return Response("{dicomRtPlan':'missing key'}", status=400, mimetype='application/json')
        rp_file = request.files['dicomRtPlan']
        if rp_file.filename == '':
            return Response("{dicomRtPlan':'missing file'}", status=400, mimetype='application/json')
        rp_filename = secure_filename(rp_file.filename)
        
        # RS dicom
        if 'dicomStructureSet' not in request.files:
            return Response("{dicomStructureSet':'missing key'}", status=400, mimetype='application/json')
        rs_file = request.files['dicomStructureSet']
        if rs_file.filename == '':
            return Response("{dicomStructureSet':'missing file'}", status=400, mimetype='application/json')
        
        # CT dicom
        if 'dicomCTs' not in request.files:
            return Response("{dicomCTs':'missing key'}", status=400, mimetype='application/json')
        ct_file = request.files['dicomCTs']
        if ct_file.filename == '':
            return Response("{dicomCTs':'missing file'}", status=400, mimetype='application/json')
        
        # RD dicom
        if 'dicomRDose' not in request.files:
            return Response("{dicomRDose':'missing key'}", status=400, mimetype='application/json')
        rd_file = request.files['dicomRDose']
        if rd_file.filename == '':
            return Response("{dicomRDose':'missing file'}", status=400, mimetype='application/json')
      
        # username
        arg_username = request.form.get('username')
        if arg_username is None:
            return Response("{username':'missing'}", status=400, mimetype='application/json')
        
        # checksum
        ref_checksum = request.form.get('configChecksum')
        if ref_checksum is None:
            return Response("{configChecksum':'missing'}", status=400, mimetype='application/json')
        
        
        # stopping criteria
        arg_number_of_primaries_per_beam = request.form.get('numberOfParticles')
        if arg_number_of_primaries_per_beam is None:
            arg_number_of_primaries_per_beam = 0
        else: 
            arg_number_of_primaries_per_beam = int(request.form.get('numberOfParticles'))

        arg_percent_uncertainty_goal = request.form.get('uncertainty')
        if arg_percent_uncertainty_goal is None:
            arg_percent_uncertainty_goal = 0
        else:
            arg_percent_uncertainty_goal = float(arg_percent_uncertainty_goal)
            
        if arg_percent_uncertainty_goal == 0 and arg_number_of_primaries_per_beam == 0:
            return Response("{stoppingCriteria':'missing'}", status=400, mimetype='application/json')
    
        # optional: run with phantom (only MedAustron commissioning)
        phantom = request.form.get('phantom')
        
        data_checksum = sha1_directory_checksum(commissioning_dir)
        if data_checksum != ref_checksum:
            return Response("{configChecksum':'Configuration has changed fromfrozen original one'}", status=503, mimetype='application/json')
        
        datadir, rp = generate_input_folder(input_dir,rp_filename,arg_username)
        app.config['UPLOAD_FOLDER'] = datadir
        
        #save files in folder
        rp_file.save(os.path.join(datadir,secure_filename(rp_file.filename)))
        rs_file.save(os.path.join(datadir,secure_filename(rs_file.filename)))
        ct_file.save(os.path.join(datadir,secure_filename(ct_file.filename)))
        rd_file.save(os.path.join(datadir,secure_filename(rd_file.filename)))
        
        # unzip dicom data
        unzip(datadir)
        
        # create simulation object
        dicom_file = datadir + '/' + rp
        mc_simulation = ideal_simulation(arg_username,dicom_file,n_particles = arg_number_of_primaries_per_beam,
                                         uncertainty=arg_percent_uncertainty_goal, phantom = phantom)
        
        # check dicom files
        ok, missing_keys = mc_simulation.verify_dicom_input_files()
        
        if not ok:
            return Response(missing_keys, status=400, mimetype='application/json')
        
        # Get job UID
        jobID = mc_simulation.jobId
        
        # start simulation and append to list  
        mc_simulation.start_simulation()
        jobs_list[jobID] = mc_simulation
        
        # check stopping criteria
        mc_simulation.start_job_control_daemon()

                
        return jobID

    @app.route("/jobs/<jobId>", methods=['DELETE','GET'])
    def stop_job(jobId):
        if jobId not in jobs_list:
            return Response('Job does not exist', status=404, mimetype='string')
            #return '', 400
        if request.method == 'DELETE':
            args = request.args
            cancellation_type = args.get('cancelationType')
            # set default to soft
            if cancellation_type is None:
                cancellation_type = 'soft'
            if cancellation_type not in ['soft', 'hard']:
                return Response('CancelationType not recognized, choose amongst: soft, hard', status=400, mimetype='string')
            
            cfg_settings = jobs_list[jobId].settings
            status = read_ideal_job_status(cfg_settings)
            
            if status == 'FINISHED':
                return Response('Job already finished', status=199, mimetype='string')
    
            if cancellation_type=='soft':
                simulation = jobs_list[jobId]
                simulation.soft_stop_simulation(simulation.cfg)
                # kill job control daemon
                daemons = get_job_daemons('job_control_daemon.py')
                kill_process(daemons[simulation.workdir])
                
            if cancellation_type=='hard':
                condorId = jobs_list[jobId].condor_id
                remove_condor_job(condorId)
                # kill job control daemon
                daemons = get_job_daemons('job_control_daemon.py')
                kill_process(daemons[simulation.workdir])
            
            
            # TODO: shall we remove job from the list to avoid second attempt to cancel?
            return cancellation_type
        
        if request.method == 'GET':
            # Transfer output result upon request
            cfg_settings = jobs_list[jobId].settings
            status = read_ideal_job_status(cfg_settings)
            
            if status != 'FINISHED':
                return Response('Job not finished yet', status=409, mimetype='string')
            
            outputdir = jobs_list[jobId].outputdir
            r = transfer_files_to_server(outputdir,api_cfg)
            if r.status_code == 200:
                return Response('The results will be sent', status=200, mimetype='string')
            else:
                return Response('Failed to transfer results', status=r.status_code, mimetype='string')
    
    @app.route("/jobs/<jobId>/status", methods=['GET'])
    def get_status(jobId):
        if jobId not in jobs_list:
            return Response('Job does not exist', status=404, mimetype='string')
            #return '', 400
        
        cfg_settings = jobs_list[jobId].settings
        status = read_ideal_job_status(cfg_settings)
        return jsonify({'status': status})
        


    app.run()
    

    

# vim: set et softtabstop=4 sw=4 smartindent:
