.. _cmdline-interface-label:

------------------------------------
API interface: ``api.py``
------------------------------------

From version v1.1, IDEAL supports an API interface. The API is launched by running the ``bin/api.py`` file on the submission nodes and can be contacted by any client that has access to the server where IDEAL is running.
The IP address of server and client can be configured from the cfg/api.cfg file. 
The API was implemented to run on HTTPS protocol, which means that a SSL certificate (self-signed certificates would work just fine) should be created. The user can refer to the following links to have an understanding of how SSL certificates work (https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https) and how to generate and store them ( http://gagravarr.org/writing/openssl-certs/others.shtml#selfsigned-openssl).
Alternatively, the user can run the API on HTTP protocol, simply removing the ssl_context argument from the ``app.run()`` function in ``bin/api.py``.

The API requires to store users credantials in a SQLite database (.db file extension). Credentials should include:

    * username (as defined in the sysconfig.cfg file)
    * user first name
    * user last name
    * user role (as defined in the sysconfig.cfg file)
    * password 
    
The database path is stored in the ``cfg/api.cfg`` file. To create the database, the user could refer to the example script ``bin/create_db_api.py``.

To properly function, the API is supported by a background program, which keeps track of all simulations' stati and sends the results back to the client when the simulation has completed. The program requires that the ``cfg/log_daemon.cfg`` file is set up, as described in the 'Commissioning' section.
After launching the API, the user has to launch this background program, by running from the terminal::

	cd <IDEAL directory>
	source bin/IDEAL_env.sh
	python bin/log_daemon.py

Wheather the results are authomatically sent back or not, can be controlled from the ``api.cfg`` file.
    
The API currently features the following endpoints:

Authentication:

    * URL: /v1/auth
    * type of request: POST
    * parameters::
    
         account-login
         account-pwd
    
IDEAL version:

    * URL: /v1/version
    * type of request: GET

Submitting a job to IDEAL:

    * URL: /v1/jobs
    * type of request: POST
    * NOTE: the configChecksum entry refers to the sha1 checksum of the commissioning directory and of the system.cfg file. The checksum parameter was introduced to verify that the simulation settings are not changed after the system freeze. To calculate it, the user can run::
	
		import ideal.utils.api_utils as ap
		data_checksum = ap.sha1_directory_checksum(<commissioning_dir>,<sysconfig_path>)
		
    * request body example::
    
         {
		  "dicomRtPlan": "string",
		  "dicomStructureSet": "string",
		  "dicomCTs": "string",
		  "dicomRDose": "string",
		  "uncertainty": 2.5,
		  "username": "string",
		  "configChecksum": "string"
         }
         
    
Get overview of jobs in the queue:

    * URL: /v1/jobs
    * type of request: GET
    * example returned value::
    
         {
		  jobId_1: "running",
		  jobId_2: "waiting"
         }
    
Retrive results for a specific job:

    * URL: /v1/jobs/{jobId}
    * type of request: GET
    * parameters::
    
         jobId: ID of the job (available from overview). To be set in the path of the request.
    
Cancel a specific job:

    * URL: /v1/jobs/{jobId}
    * type of request: DELETE
    * parameters::
    
         jobId: ID of the job (available from overview). To be set in the path of the request.
         cancellationType: "soft" or "hard". To be set in the query. Whether the cancellation should try to return temporary results (soft) or nothing at all (hard).
    
Get the status of a specific job:

    * URL: /v1/jobs/{jobId}/status
    * type of request: GET
    * parameters::
    
         jobId: ID of the job (available from overview). To be set in the path of the request.  

    
The client API's implementation is left up to the user. However, an example client API can be found in ``receiver_test.py``, in the IDEAL directory.

Once the API is up and running, the user can contact it via a client of his/her choice. In ``bin_example_api.py``, the user can find an example of how to start jobs through the API via a python script.
  
