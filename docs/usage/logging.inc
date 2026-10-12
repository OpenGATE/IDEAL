.. _logging-label:

====================================
Log files overview
====================================

IDEAL produces several log files, which can be found at different locations.
To help the user, this section provides an overview of the available log files,
the type of information they contain, and their location.

The root directory of the log files is specified in the :ref:`_syscfgfile-label`,
under ``directories`` → ``logging``.

.. table::
   :widths: auto

   +--------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   | File name                      | Location                       | Corresponding program              | Details                                                             |
   +================================+================================+====================================+=====================================================================+
   | <simulationID>.log             | logging                        | IDEAL simulation submission program | DICOM files content, beam model and HULUT selection, etc.          |
   +--------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   | preprocessor.log               | simulation working directory   | bin/preprocess_ct_image.py         | Creation of 3D MHD image from CT slices, cropping and padding.      |
   +--------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   | postprocessor.log              | simulation working directory   | bin/postprocess_dose_results.py    | Sum individual GATE simulation doses per beam and write to DICOM.   |
   |                                |                                |                                    | Integrate other quantities, like LET and RBE doses.                 |
   +--------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   | stderr.txt, stdlog.txt,        | working directory / logs       | GATE simulations:                 | Output of the GATE simulation and information on which machine       |
   | stdout.txt                     |                                | bin/start_simulations.py           | each simulation is running on. One log file per GATE simulation.    |
   +--------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   | RunGATE logs                   | simulation working directory   | HTCondor                           | HTCondor job submission.                                            |
   +--------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   | user_logs.cfg                  | simulation output directory    | IDEAL simulation submission program | Summary of the simulation settings, beamset data, CT data, main    |
   |                                |                                |                                    | log file locations, and simulation status.                          |
   +--------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   | ideal_history.cfg              | logging                        | log_daemon.py                      | Overview of all simulations run, submission times, Condor and IDEAL |
   |                                |                                |                                    | status, and corresponding working and output directories.           |
   +--------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   | log_daemon.log                 | logging                        | log_daemon.py                      | Main log file for log_daemon and debug information.                 |
   +--------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   | api.log                        | logging                        | api.py                             | Main IDEAL API log file and API debug information.                  |
   +--------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+


.. list-table::
   :header-rows: 1
   :widths: 20 20 25 35

   * - File name
     - Location
     - Corresponding program
     - Details

   * - ``<simulationID>.log``
     - ``logging``
     - IDEAL simulation submission program
     - DICOM file content, beam model and HULUT selection, etc.

   * - ``preprocessor.log``
     - simulation working directory
     - ``bin/preprocess_ct_image.py``
     - Creation of 3D MHD image from CT slices, cropping and padding.

   * - ``postprocessor.log``
     - simulation working directory
     - ``bin/postprocess_dose_results.py``
     - Sum individual GATE simulation doses per beam and write to DICOM.
       Integrate other quantities, such as LET and RBE doses.

   * - ``stderr.txt``, ``stdlog.txt``, ``stdout.txt``
     - working directory / logs
     - GATE simulations: ``bin/start_simulations.py``
     - Output of the GATE simulation and information on which machine each
       simulation is running on. One log file per GATE simulation started.

   * - RunGATE logs
     - simulation working directory
     - HTCondor
     - HTCondor job submission.

   * - ``user_logs.cfg``
     - simulation output directory
     - IDEAL simulation submission program
     - Summary of the simulation settings, beamset data, CT data, main log
       file locations, and simulation status.

   * - ``ideal_history.cfg``
     - ``logging``
     - ``log_daemon.py``
     - Overview of all simulations run, submission times, Condor and IDEAL
       status, and corresponding working and output directories.

   * - ``log_daemon.log``
     - ``logging``
     - ``log_daemon.py``
     - Main log file for ``log_daemon`` and debug information.

   * - ``api.log``
     - ``logging``
     - ``api.py``
     - Main IDEAL API log file and API debug information.
```
