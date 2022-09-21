import daemon
import os
import time
import configparser
import shutil
from zipfile import ZipFile
from impl.dual_logging import get_last_log_ID
from utils.condor_utils import get_job_daemons, get_jobs_status, kill_process, condor_check_run

## CONFIGURATION VARIABLES: (to be written in a configuration file)
#  dT time after which a job is considered historic (Folder is zipped and moved to "old")
dT = 43200.0 # 1 days
# dt time after which we considered a job interrupted after being removed from the condor_q (job_control_daemon gets killed)
dt = 3600.0 # 1 h
# dH time that a job can be on hold before being interrupted
dH = 180000.0 # 5 days
# how often we run the daemon
running_freq = 10 #s
# global log file
logfile ="/opt/IDEAL-1.1test/data/logs/IDEAL_general_logs.log"
# global control file for cleaning up and debug purposes
cfg_log_file = "/opt/IDEAL-1.1test/data/logs/ideal_history.cfg"
# Directory for historical jobs (completed and failed)
completed_dir = "/opt/IDEAL-1.1test/data/old/completed"
failed_dir = "/opt/IDEAL-1.1test/data/old/failed"
# Archive for log files
logs_folder = "/opt/IDEAL-1.1test/data/logs"

def update_log_file():
    while True:  # To stop run bin/stop_log_daemon
    	# Sleep
    	time.sleep(running_freq)
    	# Wake up to work       
    	# Read config file
    	parser = configparser.ConfigParser()
    	try:
    		parser.read(cfg_log_file)
    	except:
    		raise ImportError("Could not read global cfg file")
    		
    	# Find last ID in config file
    	if parser.sections():
    		last_ID_cfg = int(parser.sections()[-1])
    	else: last_ID_cfg = 0
    
    	# Find last ID in log file
    	last_ID_log = int(get_last_log_ID())
    	
    	# Create new sections for the newly added IDs
    	if last_ID_log > last_ID_cfg:
    		id_range = range(last_ID_cfg+1,last_ID_log+1)
    		add_id_sections(id_range,parser,logfile,cfg_log_file)
    	
    	# List possible epilogue of condor jobs
    	end_status = ['SUBMISSION ERROR','INTERRUPTED', 'DONE'] 
    	
    	for i in parser.sections():
    		if parser[i]['Submission date']!= '-':
    			job_age = get_job_age(parser[i]['Submission date'],"%Y-%m-%d %H:%M:%S")
    			# Update the status for recent sections (date - submission date < dT)
    			if job_age < dT:
    				# ideal status
    				update_ideal_status(parser[i])
    				# condor status
    				if parser[i]['Condor status'] not in end_status:
    					update_job_status(parser[i])
    				# job control daemon
    				update_job_daemon_status(parser[i])
    				# kill daemons for interrupted jobs
    				kill_running_daemons(parser[i])
    			# Clean up data for historic jobs
    			else:
    				cleanup_workdir(parser[i],completed_dir,failed_dir)
    		else:
    			parser[i]['Condor status'] = 'SUBMISSION ERROR'
    			cleanup_workdir(parser[i],completed_dir,failed_dir)
        
        # Clean up historical logs
    	archive_logs()
    	
    	# Dump the new configuration file
    	with open(cfg_log_file, 'w') as configfile:
    			parser.write(configfile)
        
    
def update_ideal_status(pars_sec):
    cfg = configparser.ConfigParser()
    cfg.read(pars_sec['Simulation settings'])
    pars_sec['Status'] = cfg['DEFAULT']['status']
    
def job_on_hold(all_jobs,job_id):
    if all_jobs[job_id]['HOLD']!='_':
        return True
    else:
        return False

def update_job_status(pars_sec):
    all_jobs = get_jobs_status()
    if pars_sec['Condor id'] in all_jobs:  # job is in condor_q (running, idle, done, hold)
        job_id = pars_sec['Condor id']
        pars_sec['Condor status'] = str(all_jobs[job_id])
        print(str(all_jobs[job_id]))
        if job_on_hold(all_jobs,job_id):
            if 'On hold since' not in pars_sec:
                pars_sec['On hold since'] = time.strftime("%Y-%m-%d %H:%M:%S")
            if condor_check_run() == 0: # no problems with condor
                # try to release
                ret = os.system("condor_release {}".format())
                if ret == 0:
                    pars_sec['On hold since'] = 'Released successfully'
                else: # if it was too long on hold, remove and mark as interrupted
                    if get_job_age(pars_sec['On hold since'],"%Y-%m-%d %H:%M:%S") > dH:
                        os.system("condor_rm {}".format(job_id)) 
                        pars_sec['Condor status'] = 'INTERRUPTED' 
    else:            
        if pars_sec['Status'] == 'FINISHED':
            pars_sec['Condor status'] = 'DONE'
        else:
             if pars_sec['Condor status'] != 'BEING CHECKED':
                 pars_sec['Condor status'] = 'BEING CHECKED'
                 pars_sec['Last checked'] = time.strftime("%Y-%m-%d %H:%M:%S")
             else:
                 if get_job_age(pars_sec['Last checked'],"%Y-%m-%d %H:%M:%S") > dt: # if the job has been checked for longer then an hour
                     pars_sec['Condor status'] = 'INTERRUPTED'
                     
def update_job_daemon_status(pars_sec):
    daemons = get_job_daemons("job_control_daemon.py")
    if pars_sec['Work_dir'] in daemons:
        pid = daemons[pars_sec['Work_dir']]
        pars_sec['Job control daemon'] = 'Running with pid {}'.format(pid)
    else: 
        pars_sec['Job control daemon'] = 'Daemon killed'

def is_daemon_to_kill(pars_sec):
    is_daemon = 'Running' in pars_sec['Job control daemon']
    if pars_sec['Condor status']=='INTERRUPTED' and is_daemon:
        return True
    else:
        return False

def kill_running_daemons(pars_sec):
    if is_daemon_to_kill(pars_sec):
        pid = pars_sec['Job control daemon'].split(" ")[-1]
        ret = kill_process(pid)
        pars_sec['Job control daemon'] = 'Daemon killed manually'

def get_job_age(date_str,tformat):
    now = time.time()
    date = time.strptime(date_str, tformat)
    age = now - time.mktime(date)
    
    return age

def archive_logs():
    old_dir = logs_folder+"/old"
    if not os.path.isdir(old_dir):
        os.makedirs(old_dir)
    os.chdir(logs_folder)
    files = [f for f in os.listdir() if ".py" in f]
    for f in files:
        date_str = f.split(".py_")[1].split(".")[0]
        age = get_job_age(date_str, "%Y_%m_%d_%H_%M_%S")
        if age > dT:
            name = "old/"+f.split(".log")[0]+".zip"
            zip_files(name,[f])
            os.remove(f)

def zip_files(destin_fname,original_dirs_vec):
    myzipfile = ZipFile(destin_fname, mode='a')
    for d in original_dirs_vec:
        myzipfile.write(d)
    myzipfile.close()       
    
def zip_and_clean_folder(destin_fname,original_dirs_vec):
    zip_files(destin_fname,original_dirs_vec)
    for d in original_dirs_vec:
        shutil.rmtree(d, ignore_errors=True)
    #shutil.make_archive(destin_fname, 'zip', original_dir)
    #shutil.rmtree(original_dir, ignore_errors=True)

def cleanup_workdir(pars_sec,completed_dir,failed_dir):
    if pars_sec['Status'] == 'ARCHIVED':
        return
    
    if not os.path.isdir(failed_dir):
        os.makedirs(failed_dir)
    if not os.path.isdir(completed_dir):
        os.makedirs(completed_dir)
    
    workdir = pars_sec['Work_dir']
    root = workdir.split("work")[0] # TODO: can be read from config file too
    workdir = workdir.split("/rungate")[0] 
    # rename workdir to avoid confusion with output dir in the zip file
    os.rename(workdir,workdir+"--work")
    # get output dir
    fname =  workdir.split("work")[1]
    output = root+"output"+fname
    # dirs to be zipped
    dir_vec = [workdir+"--work",output]
       
    if pars_sec['Status'] == 'FINISHED':
        dir_name = completed_dir + fname + ".zip" # destination file

    else:
        dir_name = failed_dir + fname + ".zip" # destination file
        
    pars_sec['Status'] = 'ARCHIVED'   
    zip_and_clean_folder(dir_name,dir_vec)
        
    
        
def add_id_sections(id_range,parser,logfile,cfg_log_file):
	# TODO: we are reading the whole file. Better to read obly a buffer with the last N lines?
    nw = 1 # how many lines after IdealID is the working_dir in the log file
    nd = 3 # same for submission date
    ns = 5 # same for user settings
    nc = 6 # condor id
    
    with open(logfile,'r') as f:
        lines = f.readlines()
        ID_lines = [l for l in lines if ("IdealID:" in l.split(" ") and int(l.split(" ")[1]) in id_range)]
        #new_ids = [line.split(" ")[1] for line in ID_lines]
		
		# Get workdir for missing IDs
        work_dir_lines = [lines[lines.index(l)+nw][:-1] for l in ID_lines]
        work_dirs = [line.split(" ")[2] for line in work_dir_lines]

        dates = list()
        settings = list()
        condor_ids = list()
        for line in ID_lines:
            # Get submission date for missing IDs
            date_line = lines[lines.index(line)+nd][:-1]
            if date_line.split(" ")[2] != 'error':
                dates.append(date_line.split(" ")[3]+" "+date_line.split(" ")[4])
                # Get settings for missing IDs
                settings.append(lines[lines.index(line)+ns][:-1])
                # Get condor cluster ID
                condor_ids.append(lines[lines.index(line)+nc][:-1].split(" ")[-1])
            else:
                dates.append('-')
                settings.append('-')

 
    for i in range(len(id_range)):
        config_template(parser,id_range[i],work_dirs[i],dates[i],condor_ids[i],settings[i])
    
		
def config_template(config,idealID,workdir,date,condor_id,settings):

    config[idealID] = {'Submission date': date,
						 'Work_dir': workdir,
                         'Simulation settings': settings,
                         'Status': '',
						 'Condor id': condor_id,
                         'Condor status': '',
                         'Job control daemon': ''}


if __name__ == '__main__':
    
    with daemon.DaemonContext():
        update_log_file()

    
