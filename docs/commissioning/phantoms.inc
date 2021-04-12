.. _phantoms-label:

========
Phantoms
========

In the ``phantoms`` subdirectory of the :ref:`commissioning-label` directory
you can define the phantoms that may be used in IDEAL simulations, instead of
the CT image, for instance to simulate patience specific quality assurance
(PSQA) measurements.

For every phantom, the definition is given in a pair of files with ``.cfg`` and ``.mac`` suffixes.
The filenames without the suffixes must be identical, that part defines the name of the phantom.
The mac file defines the geometry of the phantom; if the phantom is selected, then this will be included into the main Gate
macro with ``/control/execute``. The ``.cfg`` config file specifies the details of the dose grid and auxiliary text strings for use in help texts and a graphical user interface.

The water phantom installed by the ``bin/first_install.py`` should serve as a simple example:

``water_box.cfg``
    .. include:: template_commissioning_data/phantoms/water_box.cfg
        :code: ini

``water_box.mac``
    .. include:: template_commissioning_data/phantoms/water_box.mac
