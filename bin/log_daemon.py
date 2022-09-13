import daemon
import os
import time
import configparser
from impl.dual_logging import get_last_log_ID

def get_condor_id(workdir):
    
    all_dirs = os.listdir(workdir)
    outdir = [i for i in all_dirs  if i.startswith('output.')]
    if outdir:
        cluster_id = outdir[0].split(".")[1]
        process_ids = [i.split(".")[2] for i in outdir]
        return cluster_id+"."+"0-"+str(len(process_ids)-1)
    else: return -1
    
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
        ret = add_id_sections(id_range,parser,logfile,cfg_log_file)
     
    # Update the status for recent sectios (date - submission date < dT)
    dT = 432000.0 # 5 days
    for i in parser.sections():
        job_age = get_job_age(parser[i])
        if job_age < dT:
            update_job_status(parser[i])
    
    # Dump the new configuration file
    with open(cfg_log_file, 'w') as configfile:
            parser.write(configfile)
        
    
def update_job_status(pars_sec):
    cfg = configparser.ConfigParser()
    cfg.read(pars_sec['Simulation settings'])
    pars_sec['Status'] = cfg['DEFAULT']['status']
    

def get_job_age(pars_section):
    now = time.time()
    submission_date = time.strptime(pars_section['Submission date'], "%Y-%m-%d %H:%M:%S")
    age = now - time.mktime(submission_date)
    
    return age
    
def add_id_sections(id_range,parser,logfile,cfg_log_file):
	# NOTE: we are reading the whole file. Better to read obly a buffer with the last N lines?
    nw = 1 # how many lines after IdealID is the working_dir in the log file
    nd = 2 # same for submission date
    ns = 4 # same for user settings
    
    with open(logfile,'r') as f:
        lines = f.readlines()
        ID_lines = [l for l in lines if ("IdealID:" in l.split(" ") and int(l.split(" ")[1]) in id_range)]
        #new_ids = [line.split(" ")[1] for line in ID_lines]
		
		# Get workdir for missing IDs
        work_dir_lines = [lines[lines.index(l)+nw][:-1] for l in ID_lines]
        work_dirs = [line.split(" ")[2] for line in work_dir_lines]
		
		# Get submission date for missing IDs
        date_lines = [lines[lines.index(l)+nd][:-1] for l in ID_lines]
        dates = [line.split(" ")[3]+" "+line.split(" ")[4] for line in date_lines]
        
        # Get settings for missing IDs
        settings = [lines[lines.index(l)+ns][:-1] for l in ID_lines]
		
	# Get condor_id for missing ID's
    condor_ids = [get_condor_id(wd) for wd in work_dirs]
    
    if condor_ids == -1: # the jobs haven't started yet
        return -1
	
    for i in range(len(id_range)):
        config_template(parser,id_range[i],work_dirs[i],dates[i],condor_ids[i],settings[i])
    
    return 0
		
def config_template(config,idealID,workdir,date,condor_id,settings):

    config[idealID] = {'Submission date': date,
						 'Work_dir': workdir,
						 'Condor_id': condor_id,
                         'Simulation settings': settings,
						 'Status': ''}

if __name__ == '__main__':

    update_log_file()
  
    
