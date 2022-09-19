import subprocess
from impl.dual_logging import get_high_level_logfile

    
def shell_output(shell_command):
    output = subprocess.getstatusoutput(shell_command) # Byte object
    ret = output[0]
    out = output[1]
    return ret, out

def condor_check_run():
    ret, out = shell_output("ps -ef | grep condor")
    if "condor_master" in out and "condor_schedd" in out:
        return 0
    else: 
        return -1
        
def get_job_daemons():
    out = subprocess.check_output("ps -ef | grep job_control_daemon.py", shell = True)
    lines = str(out).split("\\n")
    daemons = dict()
    for l in lines[:-3]:
        pid = l.split(" ")[6]
        wdir = l.split(" ")[-1]
        daemons[wdir] = pid
    
    return daemons
    
def get_jobs_status():
    jobs_status = dict()
    out = subprocess.check_output("condor_q -all -wide", shell = True)
    lines = str(out).split("\\n")
    n_jobs = len(lines)-7 # three empty lines, one with 'b ', one for title, one for machine info, vector starts from zero
    job_lines = lines[4:4+n_jobs]
    header = lines[3]
    for job in job_lines:
        job_info = [j for j in job.split(" ") if j!='']
        job_id = job_info[-1].split(".")[0]
        jobs_status[job_id] = dict()
        jobs_status[job_id]["IDs"] = job_info[-1].split(".")[1]
        jobs_status[job_id]["RUN"] = job_info[5]
        jobs_status[job_id]["IDLE"] = job_info[6]
        jobs_status[job_id]["DONE"] = job_info[4]
        if 'HOLD' in header:
            jobs_status[job_id]["DONE"] = job_info[7]
        
    return jobs_status

def condor_id(run_dagmann):
    ret, out = shell_output(run_dagmann)
    dagmann_id = out.splitlines()[1].split(" ")[-1][:-1]
    condor_id = int(dagmann_id) + 1
    
    return ret, str(condor_id)
