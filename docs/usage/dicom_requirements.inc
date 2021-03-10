.. _dicom-requirements-label:

===========================================
Requirements and limitations on DICOM input
===========================================

What kind of treatment plans can be studied using IDEAL?

* The input treatment plan should be a plan for scanning ion beam treatment. IDEAL is **not** designed to work for e.g. passive scattering proton therapy and conventional radiation therapy with photons.
* IDEAL takes the DICOM plan file as input, and expects to find the following DICOM files in the same directory (or in subfolders):
  * Structure set file, with the ``SOP Instance UID`` that is referred to by the treatment plan,
  * CT files, with the ``Series Instance UID`` that is referred to by structure set,
  * TPS dose file(s), which refer to the ``SOP Instance UID`` of the treatment plan.
* Hounsfield lookup tables for the protocol that was used for the input CT should be available under :ref:`cthlut-label` in the :ref:`commissioningdir`.
* Beam line model for the 'Treatment Machine' should be made available under :ref:`beamline-model-label` in the :ref:`commissioningdir`.
* In case multiple TPS dose files are found (physical and/or effective dose, dose per beam and/or dose for the whole beamset) it is important that all have the same geometry (origin coordinates, voxel size a.k.a. "spacing", number of voxels in each dimension a.k.a. "image size").

Full details of how IDEAL uses DICOM can be found in the :ref:`dicom-specs-label`.
