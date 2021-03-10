.. _todo-label:

=========
TODO list
=========

TODO

#. Interact with REGGUI/MyQAiON:

   #. How should I communicate error cases back to REGGUI/MyQAiON

       * disk full
       * parsing problems
       * simulation crash (hasn't happened)

   #. Replace shared directory with https
   #. More in general: define interface

#. Automatic CT protocol recognition based on user-supplied rules
#. Use stop-on-script *always*, not only for jobs with a statistical uncertainty goal.

   * stop when the *total* number of primaries exceeds the minimum (currently: each job simulates ceil(Nprim/Ncore) primaries)
   * stop on user request, but still compute the final result
   * provide estimate of progress, time to completion
   * always compute & report average statistical uncertainty for final result (also if no goal for this was computed)
   * always compute & report gamma analysis, iff TPS physical dose is available
   * any combination of Nprim, Unc and TimeOut is possible:

       * simulation will run at least Nprim primaries, unless TimeOut is reached
       * simulation will run until the uncertainty is better than Unc, unless TimeOut is reached

   * update simulation goals/constraints (Nprim, TimeOut, Unc) during a job.

DONE

#. Check that coordinates are correct: CT has origin=0,0,0 
#. Beam line is derived from the *name* of the BDL.
#. CT calibration is also based on the *name*. New name => new cache.  It would be better to make a md5sum of the contents of the density and composition tables.
#. CT calibration currently ignores the composition table. The table that I saw is similar to ours, but it lacks the higher HU range. I am using our own Schneider composition table.
#. REGGUI can handle only one calculation at a time. It would be nice to be able to submit several.  The IDEAL daemon *can* already handle multiple jobs concurrently.
#. Jobs are identified by the name of the job directory, e.g. `MCsquare_20_08_18_11_33_35`.  We have also seen job directory that are just called "temp".  Should we anticipate that or can we assume that REGGUI will generate unique job directory names?
#. Radiation type

