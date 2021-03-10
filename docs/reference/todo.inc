.. _todo-label:

=========
TODO list
=========

* Make IDEAL/pyidc into a "pip" project.
* Support rotating gantry.
* Support range shifter on movable snout.
* The job_executor and idc_details classes are too big, lots of implementation details should be delegated into separate classes.
  + Specifically, the creation of the Gate work directory and the creation of all condor-related files should be wrapped in separate classes. And then it should be more straightforward to support other cluster job management systems, such as SLURM and OpenPBS.
* There are still many ways in which the user can provide wrong input and then get an error that is uninformative. For instance, using "G4_Water" instead of "G4_WATER" as override material for a ROI results in a KeyError that only says that the "key" is unknown.
