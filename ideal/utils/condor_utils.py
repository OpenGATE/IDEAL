import subprocess
import os
 
def shell_output_ret(shell_command):
    output = subprocess.getstatusoutput(shell_command) # Byte object
    ret = output[0]
    out = output[1]
    return ret, out
    
def shell_output(shell_command):
	return subprocess.check_output(shell_command, shell = True)
	
def condor_check_run():
    # TODO: check if all machines are connected (nr of expected machine should be known)
    ret, out = shell_output_ret("ps -ef | grep condor")
    if "condor_master" in out and "condor_schedd" in out:
        return 0
    else: 
        return -1
    
def get_pids(daemon):
    out = shell_output("ps -ef | grep " + daemon)
    lines = str(out).split("\\n")
    daemons = list()
    for l in lines[:-3]:
        cont = [p for p in l.split(" ") if p!='']
        #print(cont)
        if 'python' in cont:
            pid = cont[1] 
            daemons.append(pid)
			   
    return daemons

def kill_process(pid):
    ret = os.system("kill -9 {}".format(pid))  
    if ret != 0:
        raise Exception('Could not kill daemon')
    return ret
       
def get_job_daemons(daemon):
    out = shell_output("ps -ef | grep " + daemon)
    lines = str(out).split("\\n")
    daemons = dict()
    for l in lines[:-3]:
        cont = [p for p in l.split(" ") if p!='']
        pid = cont[1]
        if not pid.isnumeric():
            raise AssertionError("pid is not a number") 
        wdir = cont[-1]
        if '/rungate.' not in wdir:
            raise AssertionError("got wrong or non-existing working directory")
        daemons[wdir] = pid
    
    return daemons
    
def get_jobs_status():
    jobs_status = dict()
    out = shell_output("condor_q -all -wide")
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
            jobs_status[job_id]["HOLD"] = job_info[7]
        else:
            jobs_status[job_id]["HOLD"] = "_"
        
    return jobs_status

def condor_id(run_dagmann):
    ret, out = shell_output_ret(run_dagmann)
    dagmann_id = out.splitlines()[1].split(" ")[-1][:-1]
    condor_id = int(dagmann_id) + 1
    
    return ret, str(condor_id)
