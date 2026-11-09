.. _sysreqs-label:

*******************
System requirements
*******************

========
Hardware
========

IDEAL will run CPU-intensive simulations. In order to get results within a clinically reasonable time frame, many
instances of GateRTion can be run in parallel on sufficiently fast CPUs. Parallelization can be achieved via multi-threading (MT), as well as by distributing the simulation on cluster.
IDEAL can in principle run on a single machine, however in the following
we assume a typical setup with a small/medium size cluster.

---------------
Submission Node
---------------

* At least 4 cores with a clock speed greater than 2GHz.
* At least 16 GiB of RAM.
* Local disk space for the operating system and HT Condor, 100 GiB should be sufficient.
* Shared disk: see below.

-----------------
Calculation Nodes
-----------------

* In total at least 40 cores (preferably 100-200) with a clock speed greater than 2GHz.
* At least 4 GiB of RAM per core [#ramfoot]_.
* Local disk space for the operating system and HT Condor, 100 GiB should be sufficient.


.. _shareddisk:

----------------------
Shared disk (internal)
----------------------

* At least half a terabyte.
* Storage of all software, configuration and simulation data.
* Accessible by the submission and calculation nodes.
* Internal cluster network and storage hardware should provide at least O(10Gbit/second) read and write speed.
* Should support high rewrite rate. During a simulation, temporary results up are saved for all cores typically every two minutes, O(1Gib/core).
* To create a shared disk, we advise to use nfs-kernel-server, although other similar tools are available. The key steps to create a shared disk on the folder <dir_shared> are the following:

On server::

	sudo gedit /etc/exports
	add line: <dir_shared> IP_CLIENT1(rw,no_subtree_check) IP_CLIENT2(rw,no_subtree_check) IP_CLIENT3(rw,no_subtree_check)

	sudo exportfs -ra
	sudo ufw allow from IP_CLIENT1 to any port nfs 
	sudo ufw allow from IP_CLIENT2 to any port nfs 
	sudo ufw status

	
On clients::

	mkdir <dir_shared>
	sudo mount IP_HOST:<dir_shared> <dir_shared>
	sudo gedit /etc/fstab
	add line: IP_HOST:<dir_shared> <dir_shared> nfs rw 0 0



A more detailed explanation can be found here:  https://www.blasbenito.com/post/shared-folder-beowulf-cluster/

--------------------------------------
Network access to/from submission node
--------------------------------------

The submission node should be accessible by the user, or be connected with an
external server that functions as the user interface. To this end, the
submission node should be connected to an reasonably fast internal network that
allows access to a shared directory system (typically CIFS) or HTTPS
connections with at least one other server.
Recommended data upload and download speed is 1Gbit/second or faster.

----------------------------
Mounting Windows file shares
----------------------------

A typical clinical computing environment is dominated by MS Windows devices,
and if the environment includes a Windows File Share (CIFS) then it can be convenient
to mount this from the submit node of the IDEAL cluster. This can then be
used for DICOM input to and output from IDEAL.

Ask your local MS Windows system administrator which subfolder(s) on the file
share you can use for IDEAL input/output, and with which user credentials. Some
administrators prefer to use personal user accounts for everything (so they can
track who did what, in case something went wrong), others prefer to define
"service user" accounts that can be used by several users for a particular
(limited) purpose.  Create a new folder on the submit node
(``/var/data/IDEAL/io`` in the example below) and save the user credentials in
a text file ``secrets`` with ``-r--------`` file permissions (readable only by
you).

Then run the following script (or edit ``/etc/fstab``, if you are comfortable
doing that) to create "read only" mount point for reading input and a "read and
write" mount point for writing output. The mount points *can* point to the same
folder.

.. include:: mount_shared_folder.sh
    :code: bash


========
Software
========

----------------
Operating System
----------------

For all cluster nodes: Linux. Any major modern operating system (e.g. [Ubuntu]_ 24.04 or later) should work.

------
Python
------

* Python [Python3]_ version >= 3.10 installed on all nodes.
* Submission node: `virtualenv` and `pip` are used to install modules that are not part of the standard library.
* In case the IDEAL cluster is not directly connected to the internet, the intranet should contain a repository that is accessible by the submission node and provides up to date release of the following python modules (versions are *minimum* versions):

=================== =============== =================== =============== =================== =======
Module              Version         Module              Version         Module              Version
=================== =============== =================== =============== =================== =======
APIFlask            3.1.0			itk-filtering       5.4.5			pydicom             3.0.2		
apispec             6.10.0			itk-io              5.4.5			PyJWT               2.12.1		
certifi             2026.2.25	    itk-numerics        5.4.5			pyparsing           3.3.2		
chardet             7.4.0			itk-registration    5.4.5			python-daemon       3.1.2		
cryptography        46.0.6			itk-segmentation    5.4.5			python-dateutil     2.9.0.post0		
cycler              0.12.1  		itsdangerous        2.2.0			pytz                2026.1.post1		
filelock            3.25.2			Jinja2              3.1.6			PyYAML              6.0.3		
Flask               3.1.3			kiwisolver          1.5.0			requests            2.33.1		
Flask-HTTPAuth      4.8.1			lockfile            0.12.2			scipy               1.17.1		
flask-marshmallow   1.4.0   		MarkupSafe          3.0.3			setuptools          68.2.2		
Flask-RESTful       0.3.10			marshmallow         4.2.3			six                 5.0.3		
Flask-SQLAlchemy    3.1.1			matplotlib          3.10.8			SQLAlchemy          2.0.48		
fonttools           4.62.1			numpy               2.4.4			typing-extensions   4.15.0		
greenlet            3.3.2			opencv-python       4.8.1.78	    zdata              2023.3		
htcondor            25.7.2			packaging           26.0			urllib3             2.6.3		
idna                3.11	        pandas              3.0.2			webargs             8.7.1		
importlib-metadata  9.0.0			Pillow              12.1.1			Werkzeug            3.1.7		
importlib-resources 6.1.0			pip                 26.0.1			wheel               0.34.2		
itk                 5.4.5			pkg-resources       0.0.0			zipp                3.23.0		
itk-core            5.4.5			pycparser           3.0					
=================== =============== =================== =============== =================== =======


--------
HTCondor
--------

IDEAL relies on the [HTCondor]_ cluster management system for
running many simulations in parallel [#clusterfoot]_.  
All major Linux distributions provide HTCondor as a
standard package. The full documentation of HTCondor can be found on the
HTCondor web page. 
The easiest way to configure HTCondor correctly on your cluster, is to assign a role to each machine at instalaltion time.
The detail installation procedure can be found `here <https://htcondor.readthedocs.io/en/25.x/getting-htcondor/admin-quick-start.html>`_.
First, get Condor on the central manager machine, which will also be your submit node::

   curl -fsSL https://get.htcondor.org | \
   sudo GET_HTCONDOR_PASSWORD="$htcondor_password" \
   /bin/bash -s -- --no-dry-run --central-manager \
   $central_manager_name

Note that "$central_manager_name" corresponds to the IP address of your submit node, while "$htcondor_password" is a password of your choice, which must be the same on all machines.
	
The command above will install condor and create all the configuration files necessary to make your machine the cluster's central manager. 
To use this machine as a valid submit node, create a new file "/etc/condor/config.d/50-daemons.conf", and add the following content::

	DAEMON_LIST = MASTER COLLECTOR NEGOTIATOR SCHEDD
	CUSTOM_FILE_DOMAIN = <your_submit_node_domain>
	FILESYSTEM_DOMAIN = $(CUSTOM_FILE_DOMAIN)
	UID_DOMAIN = $(CUSTOM_FILE_DOMAIN)
	TRUST_UID_DOMAIN = TRUE

Next, configure your calculation nodes via::

   curl -fsSL https://get.htcondor.org | \
   sudo GET_HTCONDOR_PASSWORD="$htcondor_password" \
   /bin/bash -s -- --no-dry-run --execute \
   $central_manager_name
   
And create a new file "/etc/condor/config.d/50-daemons.conf", with the following content::

	CUSTOM_FILE_DOMAIN = <your_submit_node_domain>
	FILESYSTEM_DOMAIN = $(CUSTOM_FILE_DOMAIN)
	UID_DOMAIN = $(CUSTOM_FILE_DOMAIN)
	TRUST_UID_DOMAIN = TRUE

Last, start condor on all machines::

	sudo systemctl enable condor
	sudo systemctl restart condor

To check that condor is running and that all machines are correctly included in the cluster, the user can run::

    condor_status

----------
GATE-RTion
----------

GATE-RTion [GateRTion]_ is a special release of Gate [GateGeant4]_, dedicated
to clinical applications in pencil beam scanning particle therapy. From IDEAL v2.0, GateRTion is installed automatically by
IDEAL, via pip. However, Gate relies on some system-level libraries, that are not by default installed in Linux. You can install these dependency as follow::

	sudo apt install \
    libgl1\
    libice6 \
    libsm6 \
    libx11-6 \
    libxext6 \
    libxrender1

