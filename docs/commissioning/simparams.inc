=====================
Simulation parameters
=====================

The so-called `"cut parameters" in Geant4/Gate simulations <https://opengate.readthedocs.io/en/latest/cut_and_variance_reduction_technics.html>`_
define the level of detail into which particles need to be tracked.  This
implies a trade-off between simulation accuracy and speed. Typically, for the
volume outside of the patient volume speed is more important than accuracy,
while inside the patient volume the priorities are reversed: accuracy is more
important than speed.

The three kinds of parameters that need to be configured, per volume and per
particle, are the "cut in region", "minimum remaining" range and the "maximum
step size".  Recommended values for clinical applications were reported in
[Winterhalter2020]_.

The settings of the "cut parameters" can be different for computing the dose in
the CT or in a custom phantom.  IDEAL expects to find these settings settings
in Gate macro files named ``ct-parameters.mac`` and ``phantom-parameters.mac``,
respectively, stored in the ``material`` subdirectory of the
:ref:`commissioningdir`.

For CT simulations, the names of the relevant volumes are ``world``,
``patient_box`` and ``patient``. The ``patient`` volume is the the CT volume,
the ``patient_box`` is a slightly larger volume that includes a layer of air
around the patient, and the ``world`` volume encloses everything, including the
patient, the nozzle and the particle generation plane.

For phantom simulations, the names of the non-``world`` volumes are given in
the phantom specifications. The name of the phantom selected by the user is
available via the Geant4 alias ``{phantom_name}``.

An example of the parameter settings for CT is given below.

.. literalinclude:: ct-parameters.mac

