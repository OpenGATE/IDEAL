.. _architecture-label:

======================
Architectural overview
======================

--------
Synopsis
--------

The core functionality of the IDEAL software is to compute the dose
distribution for any PBS ion beam treatment plan, using Geant4/GATE as the dose
engine.  The primary purpose is to provide an independent dose calculation tool
that may be useful in clinics, but software is designed to be useful also for a
variety of research topics related to dose calculations.

Since a Geant4/GATE simulation typically requires a lot of CPU time to enough
primaries to reach a sufficiently low Type A uncertainty, IDEAL is designed to
run on a GNU/Linux cluster in order to achieve the statistical goal within a
reasonable time.

IDEAL is implemented as a set of python modules and scripts.

The two central modules in IDEAL are the humbly named `idc_details` and
`job_executor`.  The `idc_details` module is responsible for collecting and
checking the input data and the user settings. The `job_executor` is
responsible for the execution of all steps of the calculation, which is
organized in three phases: pre-processing, simulation and post-processing.

IDEAL currently has two scripts that provide user interfaces (UI): one "command
line" user interface (`clidc.py`) and  one "graphical" user interface
(`sokrates.py`). Both these UIs are effectively just differently implemented
wrappers around the `idc_details` and `job_executor` modules; with `clidc.py`,
the user specififies the input plan file and simulation details via command
line options while `sokrates.py`, these inputs are selected with traditional
GUI-elements such as drop-down menus, radio buttons, etc. Research users are of
course not limited to these UI scripts and can write their own scripts based on
the IDEAL modules.

---------------------
Detailed IDC Workflow
---------------------

Flowchart.

Details enumerated list of steps with references to the flowchart and the modules in which these steps are implemented.

(To be continued.)
