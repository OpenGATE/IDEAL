.. _cthlut-label:

====================================
CT protocol Hounsfield Lookup tables
====================================

The :ref:`commissioningdir` should have a ``CT`` subdirectory.  This directory
contains the ``hlut.conf`` configuration file and three subdirectories,
``density``, ``composition`` and ``cache``.

The ``hlut.conf`` configuration file describes for each CT protocol which DICOM
tags and values should be used to recognize it, as well as how to convert the
HU values to materials. This text file should be edited by the commissioning
physicist to provide the data for each of the relevant CT protocols in the
clinic where IDEAL is installed.

There are two different ways to define the conversion from HU to materials.
    #. For [Schneider2000]_ type conversion, provide the names of density and composition text files,  which are expected to be found in the respective subfolders.
    #. Provide a direct HU-to-material conversion table. A list of HU intervals can be given, and for each interval the name of the material is specified. This can be either a Geant4 material (e.g. ``G4_WATER``) or a material that is defined in the ``GateMaterials.db`` file (e.g. ``PMMA``).

Examples of the density and composition files for Schneider-type material
conversion can be found in the ``GateContrib`` project on GitHub:
* `density <https://github.com/OpenGATE/GateContrib/blob/master/GATE-RTion/DoseActor2-CT/data/Schneider2000DensitiesTable.txt>`_
* `composition <https://github.com/OpenGATE/GateContrib/blob/master/GATE-RTion/DoseActor2-CT/data/Schneider2000MaterialsTable.txt>`_

IDEAL will not directly use these tables. Rather, for every new combination of
density, composition and density tolerance value (usually set in the system
configuration file) it will generate a new material database and an
interpolated HU-to-material table, in which associates HU intervals directly
with a material from the the new database. The HU intervals are chosen just
small enough such that the steps in density between the subsequent materials
are less than the density tolerance value. These generated tables are stored in
a cache folder ``CT/cache`` and will be reused in following IDEAL jobs with the
same combination of CT protocol and density tolerance.
