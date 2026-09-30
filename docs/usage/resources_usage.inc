.. _resources-usage-label:

====================================
RAM, CPUs, Disk Space Usage
====================================

In IDEAL v2, the usage of resources is strongly dependent on the system configuration in terms of number of cores and number of threads.
One IDEAL simulation is parallelized into multiple GATE simulations, each corresponding to an HT condor job.
In contrast to previous, single-threaded versions of IDEAL, in IDEAL v2 the number of GATE simulations does not correspond to the number of active CPU cores,
as each simulation uses multiple threads/cores.
Instead, the number of CPUs used is equal to the number of GATE simulations times the number of threads per simulation.

------------------------------------
Disk space usage
------------------------------------
The usage of disk space depends on several factors. The major ones are listed below:

* The size of the scoring grid. This affects the size of the temporary dose images stored in the working directory of IDEAL.

* The disk space usage scales with the number of GATE simulation splits. A temporary output folder with the simulation results is in fact created for each simulation split.
  To reduce disk space usage, one could run the same IDEAL simulation with the same total number of CPU cores, but increasing the number of threads per simulation. 
  This results in less GATE simulation splits.
  
* The disk space also scales with the number of scored quantities. If, for instance, a user decides to score both physical and RBE weighted dose, 
  two images will be stored on disk per GATE simulation split.
  
* Finally, the disk space depends on the number of beams per beamset. Indeed, each beam dose is scored separately by IDEAL.


------------------------------------
RAM usage
------------------------------------
The RAM usage is mainly dominated by the fact that each GATE simulation has to keep in memory a large matrix in which to store the accumulated dosimetric quantities (e.g dose, LET...).
Thanks to MT, the user can reduce the RAM usage, by reducing the number of GATE simulation splits, without affecting the calculation time (as the total number of CPU cores will not change).

* The RAM usage scales with the number of GATE simulations.

* Increasing the number of threads, with constant total number of cores, reduces the RAM usage. However, the scaling is not completely linear, as each thread stores some thread-local variables,
  resulting in an additional RAM overhead per thread.
  
* The RAM usage increases with the number of scored outputs, as more images have to be kept in memory.

