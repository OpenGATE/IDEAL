.. _todo-label:

=========
TODO list
=========

* Make IDEAL/pyidc into a "pip" project.
* Support rotating gantry.
* Support range shifter on movable snout.
* Some parameters can now be overridden by the command line interface ``clidc.py``, but not by the GUI ``socrates.py``, and vice versa. E.g. in the ``socrates.py`` , a phantom geometry can be translated by changing the isocenter coordinates, but the ``clidc.py`` does not yet have an option for requesting such a change. The functionalities of the user interfaces should be as similar as possible.
* The job_executor and idc_details classes are too big, lots of implementation details should be delegated into separate classes.
  + Specifically, the creation of the Gate work directory and the creation of all condor-related files should be wrapped in separate classes. And then it should be more straightforward to support other cluster job management systems, such as SLURM and OpenPBS.
* There are still many ways in which the user can provide wrong input and then get an error that is uninformative. For instance, using "G4_Water" instead of "G4_WATER" as override material for a ROI results in a KeyError that only says that the "key" is unknown.
