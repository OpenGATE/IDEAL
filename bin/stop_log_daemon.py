from utils.condor_utils import get_pids, kill_process
import os
 
if __name__ == '__main__':
	daemon = "log_daemon.py"
	pids = get_pids(daemon)
	
	for pid in pids:
		kill_process(pid)
		  

