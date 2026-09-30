.. _log_daemon-cfg-label:

=========================
Log daemon configuration file
=========================
The log daemon configuration file allows the user to configure the :ref:`log-daemon-label` program.
After installing IDEAL, the user should take care of customizing the ``log_daemon.cfg`` file, in the ``cfg`` folder. 

----------------
[Time variables]
----------------

``historic after``
	time (in seconds) after which a job is considered hystorical. After this time, the working directory is zipped and moved to "old".
``unsuccessfull after``
	time after which a job is considered UNSUCCESSFULL after being removed from the condor queue. 
	When a job doesn't appear anymore in the condor queue, it is one of two cases. Either it was successfully terminated, or it failed, possibly for reasons related to the cluster management.
    When a job doesn't appear in the queue anymore, and after a time equals to the 'unsuccessfull after' it is not yet completed, it is marked as unsuccessful.
``on hold untill``
	time that a job can be on hold before being considered UNSUCCESSFULL
``running_freq``	
	time (in seconds) between two successive updates of the cfg_log_file

--------
[Paths]
--------

``global logfile``
	path of the global log file. This file will be created by IDEAL, if it doesn't exist yet.
``cfg_log_file``
	path of the cfg_log_file. This file will be created by IDEAL, if it doesn't exist yet.
``log_daemon_logs``
	path of the log_daemon.py logs. It is reccommanded to use the same logging directory used by IDEAL.
``completed_dir``
	directory to archive successfully completed jobs
``failed_dir``
	directory to archive failed job
``logs_folder``
	same path as the IDEAL logs 
``api_cfg``
	path of the API configuration file
``syscfg``
	path of the system.cfg file

------------
[Job status]
-------------

Dictionary of possible condor job status::

	submission_err = SUBMISSION ERROR
	unsuccessfull = UNSUCCESSFULL
	done = DONE
	killed_by_log_daem = KILLED BY LOG DAEMON
	checking = BEING CHECKED

