.. _workflow-label:

==================
The IDEAL workflow
==================

------------------------------------------
An independent dose calculation with IDEAL
------------------------------------------

There are different user interfaces for IDEAL, but the basic workflow is always as follows:

* User starts user interface with username and role
* User provides DICOM input data (CT, RS, RP, RD)
* User chooses MC settings:

  * required: statistical goal (number of primaries, uncertainty, time out, or a combination of these)
  * required: CT protocol [#ctprotocol]_
  * optional: material overrides (default: only ``G4_AIR`` for volume outside of external)
  * optional: spatial resolution overrides (default: same as TPS dose)
  * optional: which beams to simulate (default: all of them)

* GATE-RTion Simulation runs for a couple of hours on a cluster (actual runtime depends on many factors)
* Beam dose distributions are exported by IDEAL as DICOM files (and MHD format, if configured that way)
* User analyzes and evaluates dose distributions using third party tools (e.g. [VeriSoft]_ or a TPS like [RayStation]_)

---------------------
Longer term work flow
---------------------

1. You work in an proton/ion beam therapy clinic and decide that Geant4-based independent dose calculations may be useful in your clinic.
2. A sufficiently powerful and extendible computer cluster is acquired, with resources as described in :ref:`sysreqs-label`.
3. IDEAL is installed on this cluster as described in :ref:`ideal-install-label` by an employee with an admin role.
4. The medical physicist(s) with a "commissioning" role develops the beam model, installs the CT Hounsfield lookup tables and edits the system configuration file with correct values (see :ref:`commissioning-label`).
5. The medical physics team runs a series of tests to make sure that the installation went well. This should probably include:

  * Integrated depth dose curves for several energies in water (using a CT of a water phantom)

    * compare with measurements (both the shape of the curve and the absolute dose)
    * determine/adjust correction factors

  * Beam profiles in air, compare with measurements
  * Example treatment plans from recent clinical practice:

    * Check level of agreement, find any systematic offsets in dose or in geometry
    * Determine cluster performance:

      * how does the simulation runtime vary with statistical goals and with complexity of the plan (number of beams, number of spots, radiation type, etc)
      * are there any crashes (e.g. due to insufficient memory)?

    * Check all combinations of beamline, radiation type, passive elements and CT protocol that you expect to use

  * **You are yourself responsible for the correct use of IDEAL and any consequences of using its results. If you intend to use IDEAL clinically, then you need follow all procedures for using "Software Of Unknown Provenance" (SOUP). IDEAL is NOT a medically certified product.**

6. Use IDEAL to perform independent dose calculations in your clinic or for research.

   * The commissioning physicist should make sure that the commissioning data are correct and up to date. Whenever new beamlines or CT protocols are introduced or the existing ones are changing, the commissioning data should be updated.
   * The admin should make sure that the disks do not fill up, by regularly purging data from older simulations.
   * Periodically review the performance of your IDEAL installation:

     * with experience you may improve some choices made during installation and commissioning
     * buy more cluster nodes, more RAM
     * share your observations, experiences and ideas for improvement with the IDEAL development team


.. [#ctprotocol] The CT protocol selection may be automated in later release, but the users will still be able to override the protocol.
