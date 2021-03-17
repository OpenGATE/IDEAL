########
Overview
########

========
Synopsis
========

IDEAL is a set python modules and scripts that can be used to compute the
dose distribution (in the patient or in a phantom) for a given treatment plan.
The dose calculations are based on Geant4/Gate (specifically Gate-RTion).

.. _disclaimer-label:

===========
Disclaimers
===========

* IDEAL is **NOT** a medically certified product.
* This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License [GPLv3]_ for more details.
* IDEAL has been developed and tested for clinical use at EBG MedAustron GmbH, using the specific combination of beamlines, treatment planning software and computing infrastructure in that clinic. We wrote this software with the hope that it will be useful in other clinics as well, but we cannot guarantee that it will work correctly right out of the box. 

.. _intended-use-label:

============
Intended Use
============

Clinical use
    "IDEAL is a software system designed for dose calculation of treatment plans
    produced by a Treatment Planning System (TPS) for scanned ion beam delivery.
    IDEAL provides an independent estimate of the dose distribution expected for
    the proposed treatment plan. The evaluation and review of the dose
    distributions is done by the qualified trained radiation therapy personnel. The
    intended use is as a quality assurance tool only and not as a treatment
    planning device."

Research use
    IDEAL is intended as a research tool to study dose distributions
    in PBS ion beam therapy.  Research topics could include the properties of
    passive elements, biological effect models, patient motion and much more.

.. _user-roles-label:

==============
Intended Users
==============

IDEAL was written to be used by medical physicists and/or IT professionals in
scanned ion beam therapy clinics.  The user roles are:

clinical user
   Medical physicist in charge of patient specific quality assurance (PSQA).
   This user uses IDEAL to obtain an independent dose calculation, as described 
   in :ref:`intended-use-label`.

commissioning user
   Medical physicist in charge of validating and commissioning IDEAL. This user will
   provide all site specific data, such as beam models, geometrical details of nozzles
   and passive elements, Hounsfield lookup tables for all CT protocols, etc.

admin user
   Medical physicist or IT professional who installs and maintains the IDEAL software
   on a clinical site. The admin user makes sure that the software is correctly installed,
   assists the commissioning user with configuring the IDEAL with the correct and up to date
   commissioning data and manages the queue of calculation jobs on the cluster.

research user
   Medical physicist who uses IDEAL for "research" purposes, i.e. any purpose that is not
   the independent dose calculation of a clinical treatment plan.

The software currently allows to assign these roles to users, however in the
1.0 release these roles are not enforced. This is a TODO item.

===============
User interfaces
===============

IDEAL can be used through several user interfaces:

#. Command line interface: the `clidc.py` script ("command line independent dose calculation") can be used to trigger a dose calculation based on a given DICOM treatment plan file that was exported (together with the corresponding CT, structure set and TPS dose calculations) from the TPS to directory on a shared file system (IDEAL typically does not run on the same hardware as the TPS). The output (dose distributions for each beam in the plan) is saved in DICOM as well. This interface is useful for commissioning and research.
#. Via a custom PyQt GUI: only to be used for research.
#. Research scripting: IDEAL has been written in a modular way, such that its functionality is available to research users via python modules.
