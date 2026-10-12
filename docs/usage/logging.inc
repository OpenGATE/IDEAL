.. _logging-label:

====================================
Log files overview
====================================

IDEAL produces several log files, which can be found at different locations.
To help the user, this sections provide an overview of the available log files, the type of information they contain, and their location.
The root directory of the log files is specified in the :ref:`_syscfgfile-label`, under "directories", "logging". 

.. table::
   :widths: auto

   +-------------+-------------+-------------+-------------+
   | File name    | Location   | Corresponding program    | Details    |
   +=============+=============+=============+=============+
   |     <simulationID>.log       |            logging             | IDEAL simulation submission program|      DICOM files content, beam model and HULUT selection etc.       |
   +------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   |      preprocessor.log        |  simulation working directory  |     bin/preprocess_ct_image.py     |    Creation of 3D mhd image from CT slices, cropping and padding     |
   +------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   |      postprocessor.log       |  simulation working directory  |    bin/postprocess_dose_results.py | Sum up individual GATE simulation doses per beam and write to DICOM. Integrate other quantities, like LET and RBE doses |
   +------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   |stderr.txt, stdlog.txt, stdout.txt| working directory / logs   |   GATE simulations: bin/start_simulations.py |  Output of the GATE simulation and info on which machine each simulation is running on. One log file per GATE simulation started. |
   +------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   |        RunGATE logs          | simulation working directory   |            HT condor               |   HT condor jobs submission                                         |
   +------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   |       user_logs.cfg          |   simulation output directory  |IDEAL simulation submission program | Summary of the simulation settings, beamset data, CT data. Main log files locations indicated. Simulation status.| 
   +------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   |   ideal_history.cfg          |           logging              |           log_daemon.py            | Overview of all simualtions ran, submission times, condor and IDEAL status, corresponding working and output directories.|
   +------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   |       log_daemon.log         |           logging              |           log_daemon.py            |  log_daemon main log file, debug log_daemon.                        |
   +------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
   |          api.log             |           logging              |               api.py               |  IDEAL API main log file, debug API.                                |
   +------------------------------+--------------------------------+------------------------------------+---------------------------------------------------------------------+
