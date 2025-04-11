# IDEAL
**I**ndependent **D**os**E** c**A**lculation for **L**ight ion beam therapy using Geant4/GATE.

This is the `2.0 beta` version of the IDEAL project. The project was initiated in
2018 at [EBG MedAustron GmbH](https://www.medaustron.at/), in collaboration with
[ACMIT Gmbh](https://acmit.at/) and the [Medical University of Vienna](https://radioonkologie.meduniwien.ac.at/research/research-activities/).

IDEAL 2.0 introduces some major changes:
- **GateRTion v2**, based on Gate 10, replaces GateRTion v1. GateRTion v2 features **Geant4 11.3.0**.
- Simplified installation process: Gate 10 is installed by IDEAL via pip. The user **does not need to compile Gate and Gean4 manually** anymore!
- **RBE weighted dose** calculation for carbon ions

This code has been tested to work correctly for treatment plans with the fixed beam lines of the
MedAustron clinic. At the time of this release it has not yet been tested at any other clinic, but we hope
that this software will be useful at other clinics as well.

If you wish to install this `2.0 beta` release, please clone this code directly from
GitHub on a shared disk of the submit node of your HTCondor cluster and follow
the installation instructions. 

Note that this installation requires **HTCondor version 23 or newer**. For older versions of HTCondor, please refer to branch v2.beta.

This project will not work until it has been properly configured.
Please take your time and read the ["installation"](https://pyidc.readthedocs.io/en/latest/installation/index.html)
and ["commissioning"](https://pyidc.readthedocs.io/en/latest/commissioning/index.html) sections of the documentation carefully.
For instructions on how to use IDEAL and its different user interfaces, check the ["user manual"](https://pyidc.readthedocs.io/en/latest/usage/index.html#) section of the documentation.
