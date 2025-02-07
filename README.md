# IDEAL
**I**ndependent **D**os**E** c**A**lculation for **L**ight ion beam therapy using Geant4/GATE.

This is the `1.1` release of the IDEAL project. The project was initiated in
2018 at [EBG MedAustron GmbH](https://www.medaustron.at/), in collaboration with
[ACMIT Gmbh](https://acmit.at/) and the [Medical University of Vienna](https://radioonkologie.meduniwien.ac.at/research/research-activities/).

What's new in release `1.1`:
- **API interface**: simulations can be started in IDEAL from a remote (or local) client via http or https communication. IDEAL will send the results back to the client.
- **python module**: you can now easily start simulations via python scripting and retrieve info on the DICOM data.
- you can **keep track of all the simulation** started in IDEAL, with date, working and output directories and simulation status.
  
This code has been tested to work correctly for treatment plans with the fixed beam lines of the
MedAustron clinic. At the time of this release it has not yet been tested at any other clinic, but we hope
that this software will be useful at other clinics as well.

If you wish to install this `1.1` release, please clone this code directly from
GitHub on a shared disk of the submit node of your HTCondor cluster and follow
the installation instructions. 

This project will not work until it has been properly configured.
Please take your time and read the ["installation"](https://pyidc.readthedocs.io/en/latest/installation/index.html)
and ["commissioning"](https://pyidc.readthedocs.io/en/latest/commissioning/index.html) sections of the documentation carefully.
For instructions on how to use IDEAL and its different user interfaces, check the ["user manual"](https://pyidc.readthedocs.io/en/latest/usage/index.html#) section of the documentation.
