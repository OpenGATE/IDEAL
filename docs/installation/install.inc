.. _ideal-install-label:

******************
IDEAL installation
******************

============================
Installing the IDEAL scripts
============================

For the current 1.0rc release, IDEAL is obtained by cloning from GitLab or unpacking a tar ball, provided by at the IDEAL source repository: https://gitlab.com/djboersma/ideal. In a future release (1.0), we hope that the code can simply be installed with ``pip install ideal`` (which would then also perform some of the post-install steps). The code should be installed on the :ref:`shared disk of the IDEAL cluster <shareddisk>`. The install directory will be referred to in this manual as the "IDEAL top directory". The IDEAL top directory has the following contents:

.. list-table:: IDEAL top directory contents
    :widths: auto
    :header-rows: 1
    :align: left

    * - Name
      - Type
      - Description
    * - bin
      - Folder
      - Executable scripts and ``IDEAL_env.sh``
    * - cfg
      - Folder
      - System configuration file(s)
    * - docs
      - Folder
      - Source file for this documentation
    * - ideal
      - Folder
      - Python modules implementing the IDEAL functionality
    * - gpl-3.0.txt
      - File
      - Open Source license, referred to by the `LICENSE` file
    * - LICENSE
      - File
      - Open Source license
    * - RELEASE_NOTES
      - File
      - Summary of changes between releases 

.. _first-install-script-label:

=============================
The `first_install.py` script
=============================

IDEAL will not function correctly immediately after a clean install (cloning it from GitLab or extracting it from a tar ball).

Right after the install, it is recommended to run the ``bin/first_install.py`` script. This script will attempt to create a minimal working setup:

* Some additional python modules installed (using ``virtualenv``) in a so-called "virtual environment" named ``venv``. 
* Folders for commissioning data (definitions of beam lines, CTs, phantoms), logs, temporary data and output need to be created.
* The available resources and the simulation preferences need to be specified in a "system configuration" file ``cfg/system.cfg`` in the IDEAL install directory.

The script tries to perform all the trivial steps of the installation. Simple
examples of a beam line model, CT protocols and a phantom are provided.  These
examples are hopefully useful to give an idea of where and how you should
install your own beam models, CT protocols and phantoms. The details are described
in the :ref:`Commissioning <commissioning-label>` chapter.

This script is supposed to be run after all previous steps have been performed. Specifically:

    * A Linux cluster is available running the same OS on all nodes (e.g. Ubuntu 18.04) and with a fast shared disk that is accessible by all cluster nodes and has at least 200 GiB of free space.
    * Geant4, ROOT and GateRTion should all be installed on the shared disk. A ``gate_env.sh`` shell script is available to configure a shell environment (``source /path/to/gate_env.sh``) such that these are usable. Specifically, the ``Gate --version`` command should return the version blurb corresponding to "GateRTion 1.0".
    * HTCondor is installed and configured. All nodes on the Linux cluster run the same OS (e.g. Ubuntu 18.04).
    * Python version 3.6 or newer and ``virtualenv`` are installed.

The ``first_install.py`` script will thoroughly check these assumptions but the checks are not exhaustive.

The minimum input for the script is the file path of the ``gate_env.sh`` script.
It is recommended to also give the name of the clinic (with the -C option).
Many more options are available, see the script's '--help' output.


===================================
Installing necessary python modules
===================================

The installation step described in this section is performed by the
:ref:`first_install.py script <first-install-script-label>`.


If you did *not* run the ``first_install.py`` script, then please read the rest of this section.

IDEAL needs several external python modules that are not included in a default
python installation.  In order to avoid interference with python module needs
for other applications, the preferred way of installing these modules is using
a virtual environment called ``venv`` in the IDEAL top directory.  This may be
done using the following series of commands (which may be provided in an
install script in a later release of IDEAL) in a bash shell after a ``cd`` to
the IDEAL top directory::

    virtuelenv -p python3 --prompt='(IDEAL 1.0) ' venv
    source ./venv/bin/activate
    pip install filelock htcondor itk matplotlib numpy pydicom
    pip install python-daemon python-dateutil scipy
    deactivate

(The modules ``ipython``, ``Sphinx`` and ``PyQt5`` are optional. The first enables
interactive, python-based analysis, the second enables you to generate these docs
yourself, and the third enables the somewhat clunky ``sokrates.py`` GUI interface.)

If you decide to install the virtual environment under a different path, then
you need to edit the ``bin/IDEAL_env.sh`` script to use the correct path for
``source /path/to/virtualenv/bin/activate`` line, or to remove that line
altogether.

====================================
Installing additional python modules
====================================

You can of course add extra modules with ``pip``. There are three modules in
particular that might be desirable when working with IDEAL:

    * ``ipython``: a python command line program, which can be useful for debugging (e.g., query DICOM files using the ``pydicom`` module)
    * ``Sphinx``: enables you to generate these docs yourself (``cd docs; make html``).
    * ``PyQt5``: enables running the ``sokrates.py`` GUI. It's a bit clunky, but some users like it.

In a fresh shell, ``cd`` to the IDEAL install directory and then run::

    source ./venv/bin/activate
    pip install ipython Sphinx PyQt5
    deactivate

Alternatively, in a shell in which you already ran ``source bin/IDEAL_env.sh``,
you can directory run ``pip install ipython Sphinx PyQt5``.

.. _directory setup:

===========================
Set up the data directories
===========================

Like the virtual environment, this installation step may be automated in an
installation step in the next release.  IDEAL needs a couple of folder to store
logging, temporary data and output, respectively. In a bash shell after a ``cd`` to
the IDEAL top directory, do::

     mkdir data
     mkdir data/logging
     mkdir data/workdir
     mkdir data/output
     mkdir data/MyClinicCommissioningData

The subdirectories of ``data`` are described in more detail below.

.. _logging-dir-label:

-----------
``logging``
-----------

The ``logging`` directory is where all the debugging level output will be stored. In case something goes
wrong, these logging files may help to investigate what went wrong. When you report issues to the
developers, it can be useful to attach the log file(s).

-----------
``workdir``
-----------

The ``workdir`` directory will contain a subfolder for every time you use IDEAL
to perform a dose calculation.  The unique name of each subfolder is composed
of the user's initials, the name and/or label of the plan and a time stamp of
when you submitted the job.  The subfolder will contain all data to run the
GATE simulations, preprocessing the input data and postprocessing the output
data:

    * The GATE directory with the ``mac`` scripts and data needed to run the simulations.
    * Temporary output, saved every few minutes, from all condor subjobs running this simulation.
    * Files that are used or generated by HTCondor for managing all the jobs.
    * Three more IDEAL-specific log files, namely: ``preprocessor.log``, ``postprocessor.log`` and ``job_control_daemon.log``.

The temporary data can take up a lot of space, typically a few dozen GiB,
depending on the number of voxels in CT (after cropping it to a minimal
bounding box containing the "External" ROI and the TPS dose distribution) and
on the number of cores in your cluster. After a successful run, the temporary
data is archived in compressed form, for debugging analysis in case errors
happened or if there are questions about the final result.

.. note::
    When an IDEAL job runs unsuccessfully, the temporary data is **NOT**
    automatically compressed/archived, since the user may want to investigate.
    Do not forget to delete or compress these data after the investigation has
    concluded, to avoid inadvertently filling up the disk too quickly.

After compressed archiving job work directory still still occupies up to a few
GiB per plan, which will add up when running IDEAL routinely for many plans [#cleanupfoot]_.

.. _outputdir:

----------
``output``
----------

The ``output`` directory will contain a subfolder of each IDEAL job, using the
same naming scheme as for the work directories.
In IDEAL's :ref:`system configuration file <syscfgfile-label>` the user (with
admin/commissioning role) can define which output will actually be saved, e.g.
physical and/or effective dose, DICOM and/or MHD.  This output directory serves
to store the original output of the IDEAL job. If the path of a second output
directory is given in the :ref:`system configuration file <syscfgfile-label>`, then
the job output subfolder will be copied to that second location (e.g. on a CIFS
file share, where it can be accessed by users on Windows devices).

.. _commissioningdir:

----------------------------
Commissioning Data Directory
----------------------------

In the example  ``MyClinic`` could be replaced by the name of your particle therapy clinic.
If you are a researcher who studies plans from multiple different clinics, may
want to create a commissioning data directory for each clinic.

This directory will contain the commissioning data for
your particle therapy clinic. The details are laid out in :ref:`the commissionig chapter <commissioning-label>`.


.. rubric:: Footnotes

.. [#ramfoot] The RAM requirement is driven mostly by Carbon ion simulation memory needs. For proton plans the RAM requirements are more relaxed.
.. [#clusterfoot] In future releases, other cluster management systems such as SLURM and OpenPBS may be supported as well.
.. [#cleanupfoot] A future release of IDEAL might run an automatic clean up of the oldest temporary data in order to ensure that the new jobs will not run out of disk space.
