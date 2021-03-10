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

A beam model consists of two text files, namely a "source properties" text file
and a beamline details macro file.

----------------------
Source properties file
----------------------

The source properties file is a one of the main inputs for the
`Gate TPS pencil beam actor`_. The name of the source
properties file should be of the form
``<TreatmentMachineName>_<RadiationType>_source_properties.txt``. For instance,
for a beamline named ``IR2HBL`` that can be used both for protons and carbon
ions, two source properties files should be provided, named
``IR2HBL_PROTON_source_properties.txt`` and
``IR2HBL_ION_6_12_6_source_properties.txt``, respectively. The source properties file
defines:

    * in which plane the source particles will be generated
    * source axis distance (X and Y)
    * optical properties (beam size, angular spread, emittance; polynomials in energy)
    * range properties (energy offset between generation and isocenter, energy spread; polynomial in energy)
    * monitor unit calibration (polynomial in energy)

An example of a source properties files can be found in the `GateContrib project on GitHub`_.
The procedure for fitting a pencil beam model for Gate is described in [FuchsBeamlineModels2020]_.
The scripts that were used for that publication are (at the time of writing these docs) not yet open source, but we hope that they soon will be.

.. todo::

    IDEAL currently supports only one single beam model per beam line.
    If your clinic has e.g. two different spot tunes,
    e.g. one spot tune with smaller and one with larger spot sizes,
    then this distinction is not supported by IDEAL.
    A simple solution (in a future release of IDEAL) might be
    to include the spot tune label (often this is a version number, like "3.0")
    in the names of the source properties files.

---------------------------
Beamline details macro file
---------------------------

This macro file should be named ``<TreatmentMachineName>_beamline_details.mac``.
For the example of a beamline named ``IR2HBL``, this would be ``IR2HBL_beamline_details.mac``.
The information in it should be formatted using the `Gate/Geant4 macro language`_

The minimal content for this file is to specify for each supported radiation
type and for each of the two lateral directions whether the beam is convergent
(or not) in the source generation plane.
This is done by defining an alias that will be used by IDEAL in the configuration of the TPS PencilBeam source actor [#beamline_convergence_footnote]_.
The names of the two aliases should be ``<RADIATION_TYPE>_XTHETA`` and ``<RADIATION_TYPE>_YPHI``; for instance,
for a beamline which supports two radiation types, namely a convergent proton beam and a divergent carbon beam,
the definitions would be::

    /control/alias PROTON_CONVERGENCE_XTHETA     true
    /control/alias PROTON_CONVERGENCE_YPHI       true
    /control/alias ION_6_12_6_CONVERGENCE_XTHETA false
    /control/alias ION_6_12_6_CONVERGENCE_YPHI   false

In addition to the convergence information, the beamline details may contain the definition of the geometry
of the parts of the nozzle that are relevant for particle propagation between the
generation plane and the isocenter, for example the ionization chambers and collimators (if any).

For elaborate nozzle models, or for modeling several nozzles with common design
elements, it may be preferable to split up the code in multiple source files,
using the standard Geant4 ``/control/execute data/macro.mac`` directive.  Those
extra files can reside either in the common beamline folder, or in the
treatment machine specific beamline subfolder.  In the latter case, the names
of the extra files and folders should all start with the treatment machine
name.  Relative paths should be used to refer to the executable macros and
other input data.  All files and folders in the ``common`` folder and in the
treatment machine specific folder will be copied into the ``data`` subfolder of
the Gate working directory for each IDEAL job; hence all paths to input data
and to external macros run with ``/control/execute`` should be referred to with
a path that starts with ``./data``.

---------------------------------------
Optional beamline description text file
---------------------------------------

Finally, each beamline directory optionally can contain a text file
``<TreatmentMachineName>_description.txt`` with a short description of the
beamline that can be displayed by the IDEAL user interaces to the user.

------------------------------------------------------
Alternative beamline models for commissioning/research
------------------------------------------------------

A commissioning/research user may create a beamline model directory with a name
that is different from all actual "treatment machine names" in the clinic or
data set [#beamline_name_footnote]_.  The beamline model in this directory will
only be used if the user explicitly overrides the beamline model to use for
IDEAL, instead of the model(s) that have the same name as the treatment
machines. This can be desirable for commissioning and research activities (and
should be avoided by users in a 'clinical' role). For instance, it might be
instructive to compare a simple beam model in which primary particles are
generated at the exit of the nozzle with a more elaborate model that starts at
the entrance of the nozzle and takes all nozzle details into account.

Note that the name of the alternative beamline model should be used everywhere
where normally the "treatment machine name" would be used. E.g. if you have a
beamline named ``IR5`` and you create an alternative beamline model named
``MyToyModelForIR5``, then the source properties file for protons should be
named ``MyToyModelForIR5_PROTON_source_properties.txt``.


.. _Gate TPS pencil beam actor: https://opengate.readthedocs.io/en/latest/source_and_particle_management.html#tps-pencil-beam-source

.. _GateContrib project on GitHub: https://github.com/OpenGATE/GateContrib/blob/master/GATE-RTion/TPSPencilBeamSource/data/OrientationTest_SourceDescriptionFile.txt

.. _Gate/Geant4 macro language: https://opengate.readthedocs.io/en/latest/getting_started.html#the-user-interface-a-macro-language

.. rubric:: Footnotes

.. [#beamline_convergence_footnote] This convergence information should really be part of the source properties file.  Also, for some beamlines the convergence may depend on energy, e.g. for low energies the beam is divergent and for higher energies it is convergent. In a future releases of Gate (and GateRTion, and IDEAL) these issues will hopefully be addressed; the convergence information should be part of the source properties file and the parametrization should allow this to be energy dependent.

.. [#beamline_name_footnote] It is advisable to choose beamline model names with only alphanumerical characters, so without e.g. spaces, commas and parentheses.
