#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

# generic imports
import os
import configparser
import jwt

# ideal imports
import ideal_module as idm
import utils.condor_utils as cndr 
import utils.api_utils as ap 
import impl.dual_logging as ideal_logging
# api imports
import logging
from flask import Flask, request, jsonify, Response 
from flask.logging import default_handler
from flask_sqlalchemy import SQLAlchemy
from apiflask import APIFlask, HTTPTokenAuth, abort
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import utils.api_schemas as api_s 

# get api configuration file
this_cmd = os.path.realpath(__file__) 
bin_dir = os.path.dirname(this_cmd)
base_dir = os.path.dirname(bin_dir)
daemon_cfg = os.path.join(base_dir,'cfg/log_daemon.cfg')
sysconfig_path = os.path.join(base_dir,'cfg/system.cfg')
log_parser = configparser.ConfigParser()
log_parser.read(daemon_cfg)
ideal_history_cfg = log_parser['Paths']['cfg_log_file']
api_cfg = ap.get_api_cfg(log_parser['Paths']['api_cfg'])

# set up logger
api_logfile_path = api_cfg['logging']['logfile']
log_severity = api_cfg['logging']['severity']

ideal_logging.configure_api_logging(api_logfile_path,level = log_severity)

# create application
app = APIFlask(__name__,title='IDEAL interface', version='1.0')
auth = HTTPTokenAuth(scheme='Bearer')
api_log = logging.getLogger()

# Initialize sytem configuration once for all
sysconfig = idm.initialize_sysconfig(username = 'myqaion')

input_dir = sysconfig["input dicom"]
log_dir = sysconfig['logging']
commissioning_dir = sysconfig['commissioning']

# api configuration
host_IP = api_cfg['server']['IP host']
api_log.info(f"API database: {'sqlite:///' + api_cfg['server']['credentials db']}")
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + api_cfg['server']['credentials db']# os.path.join(base_dir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# List of all active jobs. Members will be simulation objects
max_queue_size = 50
jobs_list = dict()
queue = ap.preload_status_overview(ideal_history_cfg,max_size=max_queue_size)

# register database 
db = SQLAlchemy(app)

User = api_s.define_user_model(db)  
Server = api_s.define_server_credentials_model(db)

@auth.verify_token
def verify_tocken(token): 
    if token is None:
        abort(401, message='Invalid token')
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        current_user = User.query.filter_by(uid=data['public_id']).first()
    except:
        abort(401, message='Invalid token')
  
    if current_user is None:
       abort(401, message='Invalid token')

    return current_user
 

@app.route("/v1/auth", methods=['POST'])
def authentication():
    username = request.headers.get('account_login')
    pwd = request.headers.get('account_pwd')
    if not username:
        abort(400, message="Missing required header: 'Account-Login")
    if not pwd:
        abort(400, message="Missing required header: Account-Pwd")
    user = User.query.filter_by(username=username).first()
    if not user:
        return abort(401, message='Could not verify user!', detail={'WWW-Authenticate': 'Basic-realm= "No user found!"'})  
    if not check_password_hash(user.password, pwd):
        return abort(401, message='Could not verify password!', detail= {'WWW-Authenticate': 'Basic-realm= "Wrong Password!"'})  
    token = jwt.encode({'public_id': user.uid}, app.config['SECRET_KEY'], 'HS256')

    return jsonify({'authToken': token, 'userRole':user.role, 'firstName':user.firstname, 'lastName':user.lastname}), 200 

@app.route("/v1/version")
@app.auth_required(auth)
def version():
    return idm.get_version()

@app.post("/v1/jobs")
@app.auth_required(auth)
def start_new_job():  
    # clean input directory
    ap.remove_directory_contents(input_dir)
    
    # get data from client
    data = api_s.SimulationRequest().load({**request.form, **request.files})

    rp_file = data['dicomRtPlan']
    rp_filename = secure_filename(rp_file.filename)
    rs_file = data['dicomStructureSet']
    rd_file = data['dicomRDose']
    ct_file = data['dicomCTs']

    files_dict = {}
    if ap.check_file_extension(rp_file.filename):
        files_dict["dicomRtPlan"] = 'wrong file extension'
    if ap.check_file_extension(rs_file.filename):
        files_dict["dicomStructureSet"] = 'wrong file extension'
    if ap.check_file_extension(rd_file.filename):
        files_dict["dicomRDose"] = 'wrong file extension'
    if ap.check_file_extension(ct_file.filename):
        files_dict["dicomCTs"] = 'wrong file extension'
    if files_dict:
        return jsonify(files_dict), 422
    
    arg_username = data['username']
    if not ap.check_username(sysconfig,arg_username):
        return jsonify({"username":"user not recognized"}), 400
    ref_checksum = data['configChecksum']
    arg_number_of_primaries_per_beam = data['numberOfParticles']
    arg_percent_uncertainty_goal = data['uncertainty']
    
    phantom = None 
    if 'phantom' in data:
        phantom = data['phantom']
    
    data_checksum = ap.sha1_directory_checksum(commissioning_dir,sysconfig_path)

    if data_checksum != ref_checksum:
        return jsonify({"configChecksum":"Configuration has changed from frozen original one"}), 503
    
    datadir, rp = ap.generate_input_folder(input_dir,rp_filename,arg_username)
    app.config['UPLOAD_FOLDER'] = datadir
    
    #save files in folder and  unzip dicom data
    rp_file.save(os.path.join(datadir,secure_filename(rp_file.filename)))
    rp = ap.unzip_file(datadir,rp_file.filename)
    rs_file.save(os.path.join(datadir,secure_filename(rs_file.filename)))
    rs = ap.unzip_file(datadir,rs_file.filename)
    ct_file.save(os.path.join(datadir,secure_filename(ct_file.filename)))
    cts = ap.unzip_file(datadir,ct_file.filename)
    rd_file.save(os.path.join(datadir,secure_filename(rd_file.filename)))
    rds = ap.unzip_file(datadir,rd_file.filename)
    
    # init simulation object
    dicom_file = os.path.join(datadir,rp[0])
    mc_simulation = idm.ideal_simulation(arg_username,dicom_file,n_particles = arg_number_of_primaries_per_beam,
                                         uncertainty=arg_percent_uncertainty_goal, phantom = phantom)
    
    # check dicom
    ok, missing_keys = mc_simulation.verify_dicom_input_files()
    if not ok:
        #return Response(str(missing_keys), status=422, mimetype='application/json')
        return jsonify(missing_keys), 422
    
    api_log.info('All DICOM files read in correctly and conform to IDEAL standards')
    
    # create simulation object
    try:
        mc_simulation.read_in_data(verify=False)
    except Exception as e:
        abort(500, message=str(e))
        
    # Get job UID
    jobID = mc_simulation.jobId
    api_log.info(f'Created simulation object with {jobID = }')
    
    # start simulation and append to list 
    api_log.info('Trying to create working directory and dispatch the simulations to HTCondor')
    try:
        mc_simulation.start_simulation()
    except Exception as e:
        api_log.error(e)
        abort(500, message=str(e))
        
    api_log.info('Simulations submitted successfully')
    # remove oldest job if the queue has reached max size
    if len(jobs_list) >= max_queue_size:
        api_log.warning(f'Reached max number of tracked simulations ({max_queue_size}). Only the latest {max_queue_size} will be available from this API. Older simulations can still be monitored from {ideal_history_cfg}')
        print('POP FIRST!')
        first_job = next(iter(jobs_list))
        jobs_list.pop(first_job)
        
    jobs_list[jobID] = mc_simulation   
    api_log.info(f'Simulation with {jobID = } added to the jobs list')
        
    return Response(jobID, status=201, mimetype='text/plain')
    
@app.get("/v1/jobs")
@app.auth_required(auth)
def get_queue():
    for jobId in jobs_list.keys():
        cfg_settings = jobs_list[jobId].settings
        status = ap.read_ideal_job_status(cfg_settings)
        queue[jobId] = status
    return jsonify(queue)

@app.route("/v1/jobs/<jobId>", methods=['DELETE','GET'])
@app.auth_required(auth)
def stop_job(jobId):
    if jobId not in jobs_list:
        return Response('Job does not exist', status=404, mimetype='text/plain')

    if request.method == 'DELETE':
        args = request.args
        cancellation_type = args.get('cancellationType')
        # set default to soft
        if cancellation_type is None:
            cancellation_type = 'soft'
        if cancellation_type not in ['soft', 'hard']:
            return Response('CancellationType not recognized, choose amongst: soft, hard', status=400, mimetype='text/plain')
        
        cfg_settings = jobs_list[jobId].settings
        status = ap.read_ideal_job_status(cfg_settings)
        
        if status == ap.FINISHED:
            return Response('Job already finished', status=199, mimetype='text/plain')

        if cancellation_type=='soft':
            simulation = jobs_list[jobId]
            simulation.soft_stop_simulation(simulation.cfg)
            # kill job control daemon
            try:
                daemons = cndr.get_job_daemons('job_control_daemon.py')
                cndr.kill_process(daemons[simulation.workdir])
            except:
                print('Looks like daemon is not running, not possible to kill it')
            
        if cancellation_type=='hard':
            simulation = jobs_list[jobId]
            condorId = jobs_list[jobId].condor_id
            cndr.remove_condor_job(condorId)
            # kill job control daemon
            try:
                daemons = cndr.get_job_daemons('job_control_daemon.py')
                cndr.kill_process(daemons[simulation.workdir])
            except:
                print('Looks like daemon is not running, not possible to kill it')
        
        
        
        return cancellation_type
    
    if request.method == 'GET':
        # some checks
        if jobId not in jobs_list:
            return Response('Job does not exist', status=404, mimetype='text/plain')
        if not isinstance(jobId,str):
            return Response('JobId must be a string', status=400, mimetype='text/plain')
        
        # Transfer output result upon request
        cfg_settings = jobs_list[jobId].settings
        status = ap.read_ideal_job_status(cfg_settings)
        
        if status != ap.FINISHED:
            return Response('Job not finished yet', status=409, mimetype='text/plain')
        
        outputdir = jobs_list[jobId].outputdir
        username = 'admin'
        server = Server.query.filter_by(username=username).first()
        login_data = {'account-login': server.username_b64, 'account-pwd': server.password}
        r = ap.transfer_files_to_server(outputdir,api_cfg,login_data)
        if r.status_code == 200:
            return Response('The results will be sent', status=200, mimetype='text/plain')
        else:
            return Response('Failed to transfer results', status=r.status_code, mimetype='text/plain')

@app.route("/v1/jobs/<jobId>/status", methods=['GET'])
@app.auth_required(auth)
def get_status(jobId):
    if jobId not in jobs_list:
        return Response('Job does not exist', status=404, mimetype='text/plain')
    if not isinstance(jobId,str):
        return Response('JobId must be a string', status=400, mimetype='text/plain')
    
    cfg_settings = jobs_list[jobId].settings
    status = ap.read_ideal_job_status(cfg_settings)
    return jsonify({'status': status})


if __name__ == '__main__':
    
    cert = api_cfg['server']['ssl cert']
    key = api_cfg['server']['ssl key']
    context = (cert, key)
    app.run(host=host_IP,port=5000)#,ssl_context=context)
    

    

# vim: set et softtabstop=4 sw=4 smartindent:
