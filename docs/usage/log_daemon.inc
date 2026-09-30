.. _log-daemon-label:

Starting from version 1.1, IDEAL keeps track of all the simulations that have been started, in a global log file.
The user has the possibility to have a real time overview of the status of each simulation by launching the ``log_daemon.py`` program, from the ``bin`` folder.
The program runs in the background (hence 'daemon') and is responsible for the following tasks:


#. write and update a 'cfg_log_file', which reports, for each simulation:
	- submission date and time
	- working directory path
	- IDEAL status 
	- condor id
	- condor status, in terms of how many jobs are running, idle, on hold and completed
  
#. zip the working directories of simulations considered 'hystorical' and archive them. 
#. in case the user has configured IDEAL to run via the API interface, the daemon is responsible to send back the simulation results, once the simulation has terminated.
