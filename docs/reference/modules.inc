.. _modules-label:

=======
Modules
=======

The two central modules in IDEAL are the humbly named :py:class:`ideal.impl.idc_details` and
py:class:`ideal.impl.job_executor`.  The :py:class:`ideal.impl.idc_details` module is responsible for collecting and
checking the input data and the user settings. The :py:class:`ideal.impl.job_executor` is
responsible for the execution of all steps of the calculation, which is
organized in three phases: pre-processing, simulation and post-processing.
Both modules should be used by a script (e.g. the command line user interface
script ``clidc.py``) that runs on the submission node of the cluster.

IDEAL currently has two scripts that provide user interfaces (UI): one
"command line" user interface (``clidc.py``) and one "graphical" user interface
(``sokrates.py``). Both these UIs are effectively just differently implemented
wrappers around the ``idc_details`` and ``job_executor`` modules; with ``clidc.py``,
the user specififies the input plan file and simulation details via command
line options while ``sokrates.py``, these inputs are selected with traditional
GUI-elements such as drop-down menus, radio buttons, etc. Research users are of
course not limited to these UI scripts and can write their own scripts based on
the IDEAL modules.

.. automodule:: impl.beamline_model
   :members:

.. automodule:: impl.dicom_dose_template
   :members:

.. automodule:: impl.dual_logging
   :members:

.. automodule:: impl.gate_macro
   :members:

.. automodule:: impl.gate_hlut_cache
   :members:

.. automodule:: impl.hlut_conf
   :members:

.. automodule:: impl.idc_details
   :members:

.. automodule:: impl.job_executor
   :members:

.. automodule:: impl.phantom_specs
   :members:

.. automodule:: impl.system_configuration
   :members:

.. automodule:: utils.roi_utils
   :members:

.. automodule:: utils.resample_dose
   :members:

.. automodule:: utils.mass_image
   :members:

.. automodule:: utils.gate_pbs_plan_file
   :members:

.. automodule:: utils.gamma_index
   :members:

.. automodule:: utils.dose_info
   :members:

.. automodule:: utils.ct_dicom_to_img
   :members:

.. automodule:: utils.crop
   :members:

.. automodule:: utils.bounding_box
   :members:

.. automodule:: utils.beamset_info
   :members:
