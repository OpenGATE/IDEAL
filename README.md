# IDEAL
**I**ndependent **D**os**E** c**A**lculation for **L**ight ion beam therapy using Geant4/GATE.

This is the 1.0 release of the IDEAL project. This was developed between
February 2018 and March 2021 at EBG MedAustron GmbH, in collaboration with
ACMIT Gmbh and the Medical University of Vienna.  This code has been tested to
work correctly for plan verification purposes with the fixed beam lines of the
MedAustron clinic. It has not yet been tested at any other clinic, but we hope
that this software will be useful at other clinics as well.

If you wish to install this 1.0 release, please clone this code directly from GitHub
on a shared disk of the submit node of your HTCondor cluster and follow the
installation instructions.

In order to facilitate installation with `pip`, the code will be reorganized
a git, in particular the `ideal` module will effectively be renamed `pyidc` in
order to avoid a name collision with an existing (but currently unmaintained)
"iDEAL" python module.
