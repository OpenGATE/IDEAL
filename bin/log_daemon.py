import daemon
import os
import time
import configparser
from impl.dual_logging import get_last_log_ID
from utils.condor_utils import shell_output, condor_check_run, get_job_daemons, get_jobs_status

## CONFIGURATION VARIABLES:
#  dT time after which a job is considered"old" (Remove?)

def update_log_file():
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
     
    # Update the status for recent sectios (date - submission date < dT)
    dT = 432000.0 # 5 days
    for i in parser.sections():
        if parser[i]['Submission date']!= '-':
            job_age = get_job_age(parser[i]['Submission date'])
            if job_age < dT:
                # ideal status
                update_ideal_status(parser[i])
                # condor status
                update_job_status(parser[i])
                # job control daemon
                update_job_daemon_status(parser[i])
                
    # Dump the new configuration file
    with open(cfg_log_file, 'w') as configfile:
            parser.write(configfile)
        
    
def update_ideal_status(pars_sec):
    cfg = configparser.ConfigParser()
    cfg.read(pars_sec['Simulation settings'])
    pars_sec['Status'] = cfg['DEFAULT']['status']

def update_job_status(pars_sec):
    all_jobs = get_jobs_status()
    if pars_sec['Submission date'] == '-':
        pars_sec['Condor status'] = 'SUBMISSION ERROR'
    else: # Job submitted
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
                     if get_job_age(pars_sec['Last checked']) > 3600: # if the job has been checked for longer then an hour
                         pars_sec['Condor status'] = 'INTERRUPTED'
                     
def update_job_daemon_status(pars_sec):
    daemons = get_job_daemons()
    if pars_sec['Work_dir'] in daemons:
        pars_sec['Job control daemon'] = 'Running with pid {}'.format(daemons[pars_sec['Work_dir']])
    

def get_job_age(date_str):
    now = time.time()
    date = time.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    age = now - time.mktime(date)
    
    return age
    
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

    update_log_file()
  
    
