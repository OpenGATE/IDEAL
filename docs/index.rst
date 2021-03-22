.. IDEAL documentation master file, created by

   sphinx-quickstart on Mon Aug 31 10:52:27 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to IDEAL's documentation!
=================================

\ **I**\ ndependent **D**\ os\ **E** c\ **A**\ lculation for **L**\ ight ion beam therapy using Geant4/GATE.
Also known as "pyidc" (python module for independent dose calculation).

This is the 1.0 release of the IDEAL project. This was developed between
February 2018 and March 2021 at `EBG MedAustron GmbH <https://www.medaustron.at/>`_, in collaboration with
`ACMIT Gmbh <https://acmit.at/>`_ and the `Medical University of Vienna <https://radioonkologie.meduniwien.ac.at/research/research-activities/>`_.
This code has been tested to work correctly for treatment plans with the fixed beam lines of the
MedAustron clinic. At the time of this release it has not yet been tested at any other clinic, but we hope
that this software will be useful at other clinics as well.

If you wish to install this 1.0 release, please clone this code directly from
GitHub on a shared disk of the submit node of your HTCondor cluster and follow
the installation instructions.

In order to facilitate installation with ``pip``,
the code will be reorganized a bit. In particular the ``ideal`` python module will
effectively be renamed ``pyidc``, in order to avoid a name collision with another
python module. This reorganized version of IDEAL will get release tag ``1.1``.

This project will not work until it has been properly configured, regardless of
whether you install this project by cloning or with ``pip`` (v1.1 and later).
Please take your time and read the :ref:`installation-label`
and :ref:`commissioning-label` sections of the documentation carefully.

Contents
========

.. toctree::
   :maxdepth: 2

   overview/index
   installation/index
   commissioning/index
   usage/index
   dicomspecs/index
   reference/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. citations

.. rubric:: References

.. [GateGeant4] ``Gate`` is a Geant4 application for medical imaging and dosimetry studies, see the `OpenGATE website <http://www.opengatecollaboration.org//>`_.
.. [GateRTion] Gate/Geant4 release for clinical ion therapy applications, GATE-RTion, see the `GATE-RTion website <http://www.opengatecollaboration.org/GateRTion//>`_ and *Technical Note: GATE-RTion: a GATE/Geant4 release for clinical applications in scanned ion beam therapy* by L. Grevillot et al., PMID: 32422684 `DOI: 10.1002/mp.14242 <https://doi.org/10.1002/mp.14242>`_.
.. [HTCondor]  *High Throughput Computing with Condor*, see `HTCondor home page <https://research.cs.wisc.edu/htcondor/>`_ and the `HTCondor docs <https://htcondor.readthedocs.io/en/latest//>`_.
.. [Schneider2000] Schneider W., Bortfeld T., Schlegel W.: *Correlation between CT numbers and tissue parameters needed for Monte Carlo simulations of clinical dose distributions.* `Phys Med Biol. 2000; 45: 459-478 <https://doi.org/10.1088/0031-9155/45/2/314>`_.
.. [Winterhalter2020] Carla Winterhalter et al.: *Evaluation of GATE-RTion (GATE/Geant4) Monte Carlo simulation settings for proton pencil beam scanning quality assurance*, `DOI: 10.1002/mp.14481 <http://dx.doi.org/10.1002/mp.14481>`_.
.. [FuchsBeamlineModels2020] Hermann Fuchs et al., *Computer assisted beam modeling for particle therapy* `DOI 10.1002/mp.14647 <https://aapm.onlinelibrary.wiley.com/doi/10.1002/mp.14647>`_
.. [Python3] Python 3, see the `Python main website <https://www.python.org/>`_ and the `Python docs <https://docs.python.org/3/>`_.
.. [Ubuntu] `Ubuntu Linux <https://ubuntu.com/server>`_.
.. [VeriSoft] `VeriSoft by PTW <https://www.ptwdosimetry.com/en/products/verisoft/>`_.
.. [RayStation] `RayStation by RaySearch <https://www.raysearchlabs.com/raystation/>`_.
.. [GPLv3] `GNU General Public License v3.0 <https://www.gnu.org/licenses/gpl-3.0.html>`_, by the `Free Software Foundation <https://www.fsf.org/>`_.
