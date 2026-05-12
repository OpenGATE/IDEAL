.. _beamline-model-label:

===================
Beam line modelling
===================

The beam modelling information stored under the ``beamlines`` subdirectories of
the :ref:`commissioningdir`. For each treatment
machine in the clinic, a subdirectory to the ``beamlines`` directory should be
created, with the name equal to the same treatment machine name that is also
used in DICOM plan files.

One special beamline directory is ``common``, which can contain specifications
(of nozzle components or generic passive elements) that can be used in all beamlines.
Subfolders can be created under ``common`` to organize the resources.

A beam line model is identified by the combination of the nozzle geometry and the source parameters description.
This is reflected in the beam line configuration file, which has two sections: ``geometry_details`` and ``source_details``.
An additional section, ``from_lut``, allows the user to specify if the source parameters are provided as look up tables (LUT) 
or as energy-dependent polynomial coefficients.

The name of the beam line model file should be of the form ``<TreatmentMachineName>_<RadiationType>.json``. 
For instance, for a beamline named ``IR2HBL`` that can be used both for protons and carbon ions, two beam line model files should be provided, named
``IR2HBL_PROTON.json`` and ``IR2HBL_ION_6_12_6.json``, respectively.

The beam line model configuration, as well as the nozzle geometry configuration, are defined in JSON format. This file format supports nested data structures, which allows to easily export/import data in Gate 10.
For example, a hierarchy of Gate volumes, each with its properties (material, size, etc...), can be defined in a JSON file, which is used by Gate to set up the volumes in the simulation.

.. _source-props-label:

----------------------
Geometry details
----------------------

In this section of the beam line model, the user specifies:
	* ``nozzle_directory`` : the path of the folder containing the geometry configuration files. This can be for instance the ``common`` folder.
	* ``nozzle_file_name`` : the file name of the nozzle geometry configuration file .
	* ``range_shifters`` : the list of Range Shifters available for the beamline.
	* ``range_modulators`` : the list of Range Modulators available for the beamline.
	
The nozzle geometry file, as well as the files describing the geometry of the passive elements, should be located in the ``nozzle_directory``.
All geometry configuration files should be in JSON format, and contain a list of "volumes". Each volume is parametrized as if it was a volume object in Gate.
The nozzle geometry is rotated by IDEAL according to the gantry angle defined in the treatment plan. Specifically, IDEAL applies a rotation around the z axis in Gate coordinates,
which correspond to a rotation around the y axis in the IEC fixed reference system. Therefore, it is reccommended to define the nozzle volume along the y axis in Gate coordinates
(nozzle at gantry angle 0 degrees). As the positive y axis points toward the ground, the translation of the nozzle should be applied in the negative y direction.
The advantage of this apporoach is that the same nozzle geometry can be in principle used for different fixed beamline, as well as for a gantry beamline.

----------------------
Source details
----------------------

This section allows the user to specify the parameters that are used by Gate to define a ``TreatmentPlanPBSource``. See `Gate documentation <https://opengate-python.readthedocs.io/en/master/user_guide/user_guide_reference_sources_treatment_plan_pencil_beam_source.html>`_.
The parameters include:

``Geometrical parameters``:
	* nozzle to isocenter distance (source to axis distance)
	* distance steraing magnest from the isocenter

``Pencil beam energy dependent parameters``:
	* optical properties (beam size, angular spread, emittance, convergence)
    * range properties (energy offset between generation and isocenter, energy spread)
    * monitor unit calibration
    
    The source parameters can be either defined via look up tables, where each energy is associated to a parameter value, or
    via the coefficients of the polynomial interpolating the enrgy-parameter curve.
    Examples of both configurations can be found in the ``MyClinicCommissioningData`` directory.
    
The procedure for fitting a pencil beam model for Gate is described in [FuchsBeamlineModels2020]_.
The scripts that were used for that publication are (at the time of writing these docs) not yet open source.

The ``source_details`` section also includes a ``beamline_name`` entry. This entry will be used by IDEAL to match the treatment machine defined in the 
DICOM RT plan to the correct beam line model.


