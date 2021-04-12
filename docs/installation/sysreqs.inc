.. _sysreqs-label:

*******************
System requirements
*******************

========
Hardware
========

IDEAL will run CPU-intensive simulations. [GateRTion]_ is single threaded, so
in order to get results within a clinically reasonable time frame, many
instances of GateRTion need to run in parallel on sufficiently fast CPUs.
While this can in principle be achieved with a single machine, in the following
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
* At least 8 GiB of RAM per core [#ramfoot]_.
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

For all cluster nodes: Linux. Any major modern operating system (e.g. [Ubuntu]_ 18.04 or later) should work.

------
Python
------

* Python [Python3]_ version 3.6 or later should be installed on all nodes.
* Submission node: `virtualenv` and `pip` are used to install modules that are not part of the standard library.
* In case the IDEAL cluster is not directly connected to the internet, the intranet should contain a repository that is accessible by the submission node and provides up to date release of the following python modules (versions are *minimum* versions):

===================== ========= ============================= ======= ======================= =======
Module                Version   Module                        Version Module                  Version
===================== ========= ============================= ======= ======================= =======
alabaster             0.7.12    Babel                         2.8.0   backcall                0.1.0
certifi               2020.6.20 chardet                       3.0.4   cycler                  0.10.0
decorator             4.4.2     docutils                      0.16    filelock                3.0.12
htcondor              8.9.8     idna                          2.10    imagesize               1.2.0
ipython               7.13.0    ipython-genutils              0.2.0   itk                     5.0.1
itk-core              5.0.1     itk-filtering                 5.0.1   itk-io                  5.0.1
itk-numerics          5.0.1     itk-registration              5.0.1   itk-segmentation        5.0.1
jedi                  0.17.0    Jinja2                        2.11.2  kiwisolver              1.1.0
MarkupSafe            1.1.1     matplotlib                    3.2.1   numpy                   1.18.2
packaging             20.4      parso                         0.7.0   pexpect                 4.8.0
pickleshare           0.7.5     pip                           20.2.4  pkg-resources           0.0.0
prompt-toolkit        3.0.5     ptyprocess                    0.6.0   pydicom                 1.4.2
Pygments              2.6.1     pyparsing                     2.4.6   python-daemon           2.2.4
python-dateutil       2.8.1     pytz                          2020.1  requests                2.24.0
scipy                 1.4.1     setuptools                    46.0.0  six                     1.14.0
snowballstemmer       2.0.0     Sphinx                        3.2.1   sphinxcontrib-applehelp 1.0.2
sphinxcontrib-devhelp 1.0.2     sphinxcontrib-htmlhelp        1.0.3   sphinxcontrib-jsmath    1.0.1
sphinxcontrib-qthelp  1.0.3     sphinxcontrib-serializinghtml 1.1.4   traitlets               4.3.3
urllib3               1.25.10   wcwidth                       0.1.9   wheel                   0.34.2
===================== ========= ============================= ======= ======================= =======

--------
HTCondor
--------

IDEAL relies on the [HTCondor]_ cluster management system for
running many simulations in parallel [#clusterfoot]_.  Any recent release (e.g.
8.6.8) should work well. All major Linux distributions provide HTCondor as a
standard package. The full documentation of HTCondor can be found on the
HTCondor web page.  Below some of the specific details for configuring and
running HTCondor are described. These are meant as guidance, the optimal
configuration may depend on the details of available cluster.


.. _condorconfig:

^^^^^^^^^^^^^
Configuration
^^^^^^^^^^^^^

Each (submit or calculation) node has HTCondor configuration files stored under ``/etc/condor/``.
The ``/etc/condor/condor_config`` file contains the default settings of a subset of all configurable options.
This file should not be edited, since any edits may be overwritten by OS updates.
The settings below may be added either to the ``/etc/condor/condor_config.local`` file, or in a series
of files ``/etc/condor/config.d/NNN_XXXXXX``, where ``NNN`` are numbers (to define the order) and ``XXXXXX`` are
keywords that help you remember what kind of settings are defined in them.

The options described below are important for running IDEAL.  The values of the
settings are sometimes used in the definition of other settings, so be careful
with the order in which you add them.

The configuration can be identical for all nodes, except for the daemon settings.

Condor host
    The submit node should be "condor host", which is declared by setting ``CONDOR_HOST`` to the IP address of the submit node: ::

        CONDOR_HOST = w.x.y.z

Enable communication with other nodes
    The simplest way to configure this is to just enable communication ("allow
    write") for each node with all nodes in the cluster, including the node
    itself. The ``ALLOW_WRITE`` is a comma-separated list of all hostnames and
    IP addresses.  For ease of reading, the nodes can be added one by one, like
    this: ::

        ALLOW_WRITE = $(FULL_HOSTNAME), $(IP_ADDRESS), 127.0.0.1, 127.0.1.1
        ALLOW_WRITE = $(ALLOW_HOST), submit_node_hostname, w.x.y.z
        ALLOW_WRITE = $(ALLOW_HOST), calc_node_hostname, w.x.y.z
        ALLOW_WRITE = $(ALLOW_HOST), calc_node_hostname, w.x.y.z
        ALLOW_WRITE = $(ALLOW_HOST), calc_node_hostname, w.x.y.z

Which daemons on which nodes
    This is the only item that requires different configuration for submit and calculation nodes.

    For the *submit* node: ::

        DAEMON_LIST  = MASTER, COLLECTOR, NEGOTIATOR, SCHEDD, GANGLIAD

    For the *calculation* nodes: ::

        ALLOW_NEGOTIATOR = $(CONDOR_HOST) $(IP_ADDRESS) 127.*
        DAEMON_LIST  = MASTER, STARTD, SCHEDD

Network and filesystem
    Make sure to configure the correct ethernet port name and the full host name of the submit node ::

        BIND_ALL_INTERFACES = True
        NETWORK_INTERFACE = ethernet_port_name
        CUSTOM_FILE_DOMAIN = submit_node_full_hostname
        FILESYSTEM_DOMAIN = $(CUSTOM_FILE_DOMAIN)
        UID_DOMAIN = $(CUSTOM_FILE_DOMAIN)

Resource limits 
    HTCondor should try to use all CPU power, but refrain from starting jobs if the disk space, RAM or swap exceed some safe thresholds ::

        SLOT_TYPE_1 = cpus=100%,disk=90%,ram=90%,swap=10%
        NUM_SLOTS_TYPE_1 = 1
        SLOT_TYPE_1_PARTITIONABLE = True

        
Resource guards
    Define what to do when some already running job exceeds its resource limits ::

        MachineMemoryString = "$(Memory)"
        SUBMIT_EXPRS = $(SUBMIT_EXPRS)  MachineMemoryString
        MachineDiskString = "$(Disk)"
        SUBMIT_EXPRS = $(SUBMIT_EXPRS)  MachineDiskString
        SYSTEM_PERIODIC_HOLD_memory = MATCH_EXP_MachineMemory =!= UNDEFINED && \
                               MemoryUsage > 1.0*int(MATCH_EXP_MachineMemoryString)
        SYSTEM_PERIODIC_HOLD_disc = MATCH_EXP_MachineDisk =!= UNDEFINED && \
                               DiskUsage > int(MATCH_EXP_MachineDiskString)
        SYSTEM_PERIODIC_HOLD = ($(SYSTEM_PERIODIC_HOLD_disc)) || ($(SYSTEM_PERIODIC_HOLD_memory))
        SYSTEM_PERIODIC_HOLD_REASON = ifThenElse(SYSTEM_PERIODIC_HOLD_memory, \
                                   "Used too much memory", ""), ifThenElse(SYSTEM_PERIODIC_HOLD_disc, \
                                   "Used too much disk space","Reason unknown")
        
        MEMORY_USED_BY_JOB_MB = ResidentSetSize/1024
        MEMORY_EXCEEDED = ifThenElse(isUndefined(ResidentSetSize), False, ( ($(MEMORY_USED_BY_JOB_MB)) > RequestMemory ))
        PREEMPT = ($(PREEMPT)) || ($(MEMORY_EXCEEDED))
        WANT_SUSPEND = ($(WANT_SUSPEND)) && ($(MEMORY_EXCEEDED)) =!= TRUE
        WANT_HOLD = ( $(MEMORY_EXCEEDED) )
        WANT_HOLD_REASON = \
                ifThenElse( $(MEMORY_EXCEEDED), \
                "$(MemoryUsage) $(Memory) Your job exceeded the amount of requested memory on this machine.",\
                 undefined )

Miscellaneous
    ::

        ##########################################
        COUNT_HYPERTHREAD_CPUS=FALSE
        START = TRUE
        SUSPEND = FALSE
        PREEMPT = FALSE
        PREEMPTION_REQUIREMENTS = FALSE
        KILL = FALSE
        ALL_DEBUG = D_FULLDEBUG D_COMMAND
        POOL_HISTORY_DIR = /var/log/condor/condor_history
        KEEP_POOL_HISTORY = True
        MaxJobRetirementTime    = (1 *  $(MINUTE))
        CLAIM_WORKLIFE = 600
        MAX_CONCURRENT_DOWNLOADS = 15
        MAX_CONCURRENT_UPLOADS = 15


----
ROOT
----

Any release with major release number 6 should work.

------
Geant4
------

GATE-RTion requires Geant4 version 10.03.p03, compiled **without** multithreading.

----------
GATE-RTion
----------

GATE-RTion [GateRTion]_ is a special release of Gate [GateGeant4]_, dedicated
to clinical applications in pencil beam scanning particle therapy.  If all
nodes run the same hardware, then this can be compiled and installed once on
the shared disk of the cluster and then be used by all nodes. If the different
cluster nodes have different types of CPU then it can be good to compile
Geant4, ROOT and Gate-RTion separately on all nodes and install it on the local
disks (always under the same local path).

After installation, a short shell script should be created that can be "sourced" in order to set up the shell environment
for running ``Gate``, including the paths not only of ``Gate`` itself, but also of the Geant4 and ROOT libraries and data sets.
For instance:

.. _gate-env-sh-label:

.. include:: gate_env.sh
    :code: bash
 
