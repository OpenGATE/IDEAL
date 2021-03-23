.. _architecture-label:

======================
Architectural overview
======================

--------
Synopsis
--------

The core functionality of the IDEAL software is to compute the dose
distribution for any PBS ion beam treatment plan, using Geant4/GATE as the dose
engine.  The primary purpose is to provide an independent dose calculation tool
that may be useful in clinics, but the software is designed to be useful also
for a variety of research topics related to dose calculations.

Since Geant4/GATE simulations are quite CPU time consuming, IDEAL is designed
to run on a GNU/Linux cluster in order to achieve the statistical goal within a
reasonable time. IDEAL is implemented as a set of python modules and scripts.
These convert the information in the input DICOM plan data into a set of data
files and scripts that can be used by Gate to simulate the delivery of each of
the beams requested in the treatment plan, using beamline model details and CT
calibration curves that are configured by the user during installation and
commissioning of the IDEAL. The dose distribution for each beam is computed
separately up to the statistical goal specified by the user: number of
primaries, :ref:`average uncertainty <uncertainty-label>` or a fixed calculation time.  The dose grid is
by default the same as used by the treatment planning system, but the user can
choose to override the spatial resolution.  The beam dose as well as the plan
dose are exported as DICOM files.

--------
Workflow
--------

A device oriented example view of the workflow is illustrated in the figure below.

.. image:: ../usage/clidc_ideal_data_flow.png
    :width: 90%
    :align: center
    :alt: "IDEAL workflow diagram"

In this view, the user is logged in to the treatment planning workstation.

#. The user exports a treatment plan from the TPS to DICOM files on a shared file
   system.  The exported data include the planning CT, the treatment plan
   (including the ion beam sequence), the structure set and physical and/or
   effective dose for the beams and/or the plan, in a folder that is also mounted
   on the submission node of the cluster.
#. The user logs in to the submission node of the cluster and runs one of the IDEAL
   user interface scripts (``clidc.py`` or ``socrates.py``) to start an independent
   dose calculation. The minimum input information is the treatment plan file and
   the statistical goal (number of primaries or average uncertainty). Optional overrides
   of the default settings are discussed in the following sections.
#. IDEAL collects and checks all necessary DICOM data referred to by the treatment plan file:
   the structure set (including exactly one ROI of type "External"), the planning CT and the TPS dose.
#. IDEAL finds the beamline model(s) corresponding to the treatment machine(s) specified
   in the plan file, as well as the conversion tables for the CT protocol of the planning CT.
#. A 'work directory' is set up with all scripts specific for the IDC of the treatment plan:
   * configuration file for :ref:`preprocessing-label` (CT image cropping, material overrides)
   * shell scripts, macros and input files for ``GateRTion``
   * configuration file for :ref:`postprocessing-label` (dose accumulation, resampling and export to DICOM)
   * submit file for HTCondor (cluster job management system) "DAGman" job.
#. The IDC is started by submitting the condor "DAGman" job. The DAGman graph has just three nodes:
   * :ref:`preprocessing-label` on the submit node, typically takes about a minute.
   * simulation on the calculation nodes (``Nbeams*Ncores`` jobs, where ``Nbeams`` is the number of beams ``Ncores`` the number of physical cores in the cluster), runtime is typically in the order of hours, depending on many factors.
   * postprocessing on the submit node, takes a couple of minutes.
#. A "job control daemon" is spawned which will regularly (typically every 300 seconds) check
   whether the statistical goal (average uncertainty or number of primaries) has been reached
   for each successive beam. If the goal is reached, then a semaphore file "STOP-<beamname>" is
   created in the work directory. The scripts that are called by the Gate "StopOnScript" actor
   check the presence of that semaphore file to decide whether to stop the simulation or to continue.

.. _preprocessing-label:

-------------
Preprocessing
-------------

The job-dependent details for the preprocessing are computed and saved to a text file by :py:meth:`ideal.impl.idc_details.WritePreProcessingConfigFile`.
The preprocessing is performed by the ``bin/preprocess_ct_image.py`` script as part of the HTCondor DAGman corresponding to the IDC job.

* Cropping: the minimum bounding box is computed that encloses both the "padded"
  External ROI volume in the planning CT and the TPS dose distribution. The External
  ROI is padded with a fixed thickness of air on all six sides. The padding thickness can
  be configured with an entry for :ref:`air box margin [mm] <air-box-margin-mm-label>`
  in the ``[simulation]`` section of the system configuration file.
* Hounsfield unit values are truncated to the maximum HU value specified in the density curve given for the relevant CT protocol.
* In all voxels whose central point is *not* within the External ROI volume, the material is overridden with air (``G4_AIR``).
* Each override specified by the IDEAL user is applied to all voxels whose central point lies within the ROI to which the override applies. The user should not specify different material overrides for two or more overlapping ROIs, since the order in which the overrides will be applied is random.
* The material overrides are implemented by extending a copy of the interpolated Schneider table corresponding to the relevant CT protocol. In the extension, HU values larger than the maximum HU value in the density curve tables are associated with the override materials, and in the preprocessed CT image those high HU values are used for the voxels that have material overrides.
* A mass file is created with the same geometry as the cropped CT image, with floating point voxel values representing the density (in grams per cubic centimeter). For voxels with material overrides (e.g. outside the external), the density value are taking from the overriding material; for all other voxels the density is obtained by a simple linear interpolation in the density curve.
* A dose mask file is created with the same geometry as the output dose files, with value 1 (0) for all voxels with the central point inside (outside) the External ROI.

.. _uncertainty-label:

----------------------------------
Calculation of average uncertainty
----------------------------------

The dose distributions of all beams in a beamset (or treatment plan) are
comptued separately.  When computing the dose for one beam, on (almost) all
physical cores of the cluster ``GateRTion`` is simulating protons or ions with
kinematics that are randomly sampled from all spots in the beam, with
probabilities proportional to the number of planned particles per spot, and
Gaussian spreads given by :ref:`source properties file <source-props-label>`
for the beamline (treatment machine) by which the beam is planned to be
delivered.

For all particles that are tracked through the TPS dose volume
within the (cropped) CT geometry, the physical dose (in water, by convention)
is computed by the ``DoseActor`` in ``GateRTion`` as the deposited energy
divided by mass, multiplied by the stopping power ratio (water to material,
where the material is either the Schneider material corresponding to
the voxel Hounsfield value or override material, in case the user
specified an override for a ROI including the voxel). The dose is
saved periodically (by default every 300 seconds,
:ref:`configurable <stop-on-script-actor-time-interval-label>`
in the system configuration file).

The final dose distribution (typically the same as for the TPS) is typically
not with the same spatial resolution as the CT.  The job control daemon
computes an estimate of the Type A ("statistical") dose uncertainty in each
(resampled) voxel by resampling the (intermediate) dose distributions of from
all condor jobs to the TPS dose grid, dividing the dose by the number of
simulated primaries by each core, and computing the weighted average and
weighted standard deviation of the dose-per-primary for each voxel. The number
of primaries simulated on each core serve as weights. The relative uncertainty
in each voxel is the the ratio of the (weighted) standard deviation and the
(weighted) average.

A "mean maximum" value of dose-per-primary is estimated by computing the mean
of the ``Ntop`` highest values in the distribution of the weighted average dose
per voxel per primary.  A threshold value is then defined as a fraction ``P`` (in percent)
of this "mean maximum" dose-per-primary value.  The "average uncertainty" is then
computed as the simple unweighted average of the relative uncertainties in those
voxels in which the dose-per-primary is higher than this threshold.

The values of Ntop :ref:`can be set <n-top-voxels-for-mean-dose-max>`  in the
system configuration file (default ``Ntop=100`` and ``P=50`` percent).

When the user starts and IDC with an uncertainty value as statistical goal,
then the job control daemon with apply this goal to the dose for every beam.
The simulations for **each** beam will not be stopped until the above described
average uncertainty estimate for the **beam** dose is below the target value.
In other engines or treatment planning systems, the average uncertainty goal
may refer to to the **plan** dose instead.

.. _postprocessing-label:

--------------
Postprocessing
--------------

Actions in post processing:

    * Accumulate dose distributions and total number of primaries from simulations on all cluster cores.
    * Scale the dose with the ratio of the planned and simulated number of primary particles.
    * Scale the dose with an overall :ref:`correction factor <correction-factors-label>`.
    * Resample the dose to the output dose geometry (typically the same as the TPS dose geometry)
    * For protons: compute a simple estimate of the "effective" dose by :ref:`multiplying with 1.1 <rbe-factor-cfg-label>`.
    * Save beam doses in the format(s) :ref:`configured <output-cfg-label>` by the user.
    * Compute the gamma index value for every voxel in the beam dose with dose above threshold, if gamma index parameters are :ref:`configured <gamma-index-cfg-label>` and the corresponding TPS beam dose is available. Output only in MHD format (no DICOM).
    * Compute plan doses (if plan dose output is :ref:`configured <output-cfg-label>` by the user).
    * Compute gamma index distributions for plan doses (if TPS plan dose is available and gamma index calculation is enabled in the system configuration).
    * Update user log summary text file with settings and performance data.
    * Copy final output (beam and plan dose files, user log summary) to another shared folder (typically a CIFS mount of a folder on Windows file share, to be :ref:`configured by the user <second-output-folder-cfg>` in the system configuration file).
    * Clean up: compress (rather than delete: to allow analysis in case of trouble) the outputs from all ``GateRTion`` simulations, remove temporary copies. This is usually the most time consuming part of the post processing.


(To be continued.)
