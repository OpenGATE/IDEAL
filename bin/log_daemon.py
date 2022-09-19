import daemon
import os
import time
import configparser
import shutil
from impl.dual_logging import get_last_log_ID
from utils.condor_utils import get_job_daemons, get_jobs_status

## CONFIGURATION VARIABLES:
#  dT time after which a job is considered historic (Folder is zipped and moved to "old")
dT = 36000.0 # 1 days
# dt time after which we considered a job interrupted after being removed from the condor_q (job_control_daemon gets killed)
dt = 3600.0 # 1 h
# how often we run the daemon
running_freq = 10 #s

def update_log_file():
    while True:  # To stop run bin/stop_log_daemon
        # Sleep
        time.sleep(running_freq)
        # Wake up to work
        # Main log file
        logfile="/opt/IDEAL-1.1test/data/logs/IDEAL_general_logs.log"
        
        # Read config file
        cfg_log_file = '/opt/IDEAL-1.1test/data/logs/ideal_history.cfg'
        parser = configparser.ConfigParser()
        parser.read(cfg_log_file)
        
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
        end_status = ['SUBMISSION ERROR','INTERRUPTED', 'DONE'] 
        
        for i in parser.sections():
            if parser[i]['Submission date']!= '-':
                job_age = get_job_age(parser[i]['Submission date'])
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
                    cleanup_workdir(parser[i])
            else:
                parser[i]['Condor status'] = 'SUBMISSION ERROR'
                cleanup_workdir(parser[i])
                 
        # Dump the new configuration file
        with open(cfg_log_file, 'w') as configfile:
                parser.write(configfile)
        
    
def update_ideal_status(pars_sec):
    cfg = configparser.ConfigParser()
    cfg.read(pars_sec['Simulation settings'])
    pars_sec['Status'] = cfg['DEFAULT']['status']

def update_job_status(pars_sec):
    all_jobs = get_jobs_status()
    if pars_sec['Condor id'] in all_jobs:  # job is running, idle, done
        pars_sec['Condor status'] = str(all_jobs[pars_sec['Condor id']])
    else:            
        if pars_sec['Status'] == 'FINISHED':
            pars_sec['Condor status'] = 'DONE'
        else:
             if pars_sec['Condor status'] != 'BEING CHECKED':
                 pars_sec['Condor status'] = 'BEING CHECKED'
                 pars_sec['Last checked'] = time.strftime("%Y-%m-%d %H:%M:%S")
             else:
                 if get_job_age(pars_sec['Last checked']) > dt: # if the job has been checked for longer then an hour
                     pars_sec['Condor status'] = 'INTERRUPTED'
                     
def update_job_daemon_status(pars_sec):
    daemons = get_job_daemons()
    if pars_sec['Work_dir'] in daemons:
        pars_sec['Job control daemon'] = 'Running with pid {}'.format(daemons[pars_sec['Work_dir']])
    else: 
        pars_sec['Job control daemon'] = 'Daemon killed'

def kill_running_daemons(pars_sec):
	is_daemon = 'Running' in pars_sec['Job control daemon']
	if pars_sec['Condor status']=='INTERRUPTED' and is_daemon:
		pid = pars_sec['Job control daemon'].split(" ")[-1]
		ret = os.system('kill -9 {}'.format(pid))
		if ret == 0:
			pars_sec['Job control daemon'] = 'Daemon killed manually'
		else:
			pars_sec['Job control daemon'] = 'Could not kill daemon'

def get_job_age(date_str):
    now = time.time()
    date = time.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    age = now - time.mktime(date)
    
    return age

def cleanup_workdir(pars_sec):
    if not os.path.isdir("/opt/IDEAL-1.1test/data/old/failed"):
        os.makedirs("/opt/IDEAL-1.1test/data/old/failed")
    if not os.path.isdir("/opt/IDEAL-1.1test/data/old/completed"):
        os.makedirs("/opt/IDEAL-1.1test/data/old/completed")
    
    workdir = pars_sec['Work_dir']
    basedir = workdir.split("/rungate")[0] # dir to be zipped
    
       
    if pars_sec['Status'] == 'FINISHED':
        dir_name = "/opt/IDEAL-1.1test/data/old/completed/"+os.path.basename(basedir) # destination file
        pars_sec['Status'] = 'ARCHIVED'   
        shutil.make_archive(dir_name, 'zip', basedir)
        shutil.rmtree(basedir, ignore_errors=True)
    elif pars_sec['Status'] != 'ARCHIVED':
        dir_name = "/opt/IDEAL-1.1test/data/old/failed/"+os.path.basename(basedir) # destination file
        pars_sec['Status'] = 'ARCHIVED'   
        shutil.make_archive(dir_name, 'zip', basedir)
        shutil.rmtree(basedir, ignore_errors=True)
    
def add_id_sections(id_range,parser,logfile,cfg_log_file):
	# NOTE: we are reading the whole file. Better to read obly a buffer with the last N lines?
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
	# sleep for a certain time
    	#time.sleep(running_freq)
    	# wake up and update stuff
    	update_log_file()

    
