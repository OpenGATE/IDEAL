.. _phantoms-label:

========
Phantoms
========

In the ``phantoms`` subdirectory of the :ref:`commissioning-label` directory
you can define the phantoms that may be used in IDEAL simulations, instead of
the CT image, for instance to simulate patience specific quality assurance
(PSQA) measurements.

As for the nozzle geometry, the phantoms are configured via JSON files.
A user can define as complex phantom geometries as he/she wishes, by providing a list of ``volumes`` in the configuration file.
Additionally, the user defines a list of ``actors``. This usually include a ``DoseActor``, attached to one of the phantom volumes,
but could in principle be any other type of actors.
Example can be found in the ``MyClinicCommissioningData/phantoms`` folder.
