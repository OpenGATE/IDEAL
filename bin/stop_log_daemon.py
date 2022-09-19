import subprocess 
import os

def get_pids(daemon):
    out = subprocess.check_output("ps -ef | grep " + daemon, shell = True)
    lines = str(out).split("\\n")
    daemons = list()
    for l in lines[:-3]:
        cont = [p for p in l.split(" ") if p!='']
        print(cont)
        if 'python' in cont:
            pid = cont[1] 
            daemons.append(pid)
			   
    return daemons
 
if __name__ == '__main__':
	daemon = "log_daemon.py"
	pids = get_pids(daemon)
	
	for pid in pids:
		os.system("kill -9 {}".format(pid))
		  

