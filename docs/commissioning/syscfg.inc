.. _syscfgfile-label:

=========================
System configuration file
=========================

The configuration file contains the specifications of the computing
environment, the preferences of the users and much more. IDEAL cannot run
without these specifications.  The standard location of the system
configuration file is ``cfg/system.cfg`` relative to the installation directory
of IDEAL.

.. _cfgsyntax: https://docs.python.org/3/library/configparser.html

The `syntax of the configuration file <cfgsyntax>`_ is similar to what is found in Microsoft Windows IN files.
The configuration is divided in ``[sections]`` which contain lists of settings of the form ``label = value``.
The labels are case insensitive.
The example ``system.cfg`` file provided with the IDEAL source contains many explanatory comments that should help the commissioning user to define the correct values.

--------------
[directories]
--------------

``input dicom``
    Full path of the top directory for finding DICOM input data. This is mainly used by the research GUI, to position the starting location for the input file browser.

``tmpdir jobs``
    Full path of the "work directory" on the shared disk of the cluster. For each IDEAL job, a subfolder will be created in this directory to store all the job specific data, including the intermediate and final results of the cluster subjobs. Upon successful completion of the job, most of the bulky data in the subfolder will be compressed, but not deleted.

``first output dicom``
    Full path of the output directory on the shared disk of the cluster. For each IDEAL job, a subfolder will be created in this directory to store the final output (DICOM dose files and a text summary of the job).

.. _second-output-folder-cfg:

``second output dicom``
    Full path of the directory on an external file system (typically a Windows file share, mounted with SAMBA). The for each job, a copy of the output subfolder is stored here. This setting is optional: leaving this option empty avoids the copy.

``logging``
    Full path of the logging directory. For every IDEAL command, a logging file with all debug level logging output will be stored here.

``commissioning``
    Full path of the so-called "commissioning" directory. This contains site specific calibration and modeling data, such as beam models and HLUT tables, which are described in more detail below.


------------
[mc stats]
------------

There are three possible statistical goals for an IDEAL job: "number of
primaries", "average uncertainty" and "maximum runtime". The ranges of allowed
values and the default values of these goals are specified here, as well as which goals
are enabled by default. This information is primarily used by the GUI.

Four values should be specified for each goal, to specify the minimum, default,
maximum, and stepsize value, respectively. All values should be positive and
the default value should be within the allowed range. It is recommended to
choose the stepsize identical to the minimum value.  For the goal(s) that
should be enabled by default, the word "default" should be put at the end of
the configuration line. At least one goal should should be enabled.

For instance::

    n minutes per job   =    5        20      10080    5
    n ions per beam     =  100   1000000 1000000000  100   default
    x pct unc in target =    0.1       1.        99.   0.1

In this example, by default the goal is to simulate 1000000 primaries.  The
valid values for the number of primaries are in the range from 100 to
1000000000, and in when a GUI user clicks to increment or decrement, then the
stepsize is 100. Since Gate uses a signed integer to count primaries, the
maximum should be less than the number of cores in the cluster times
2\ :sup:`31`\ -1=2147483647.

.. _n-top-voxels-for-mean-dose-max:

The average uncertainty in the target is defined as the average of the relative uncertainty
in the voxels that have a dose larger than the a configurable fraction of the mean dose maximum.
We are not using the absolute dose maximum in a voxel, since this tends to fluctuate too much.
Instead we find the N highest dose values in the distribution, the mean of those values is the "mean dose maximum".
The number N should be be configured in the system configuration file like this::

    n top voxels for mean dose max = 100

The fraction of this "mean dose maximum" that serves as the threshold to mask the voxels that
should contribute to the "average uncertainty" is configured like this::

    dose threshold as fraction in percent of mean dose max = 50.

In this example configuration, the "mean dose maximum" is computed from the 100
highest dose values and the threshold is set at 50% of that maximum mean dose.

--------------
[simulation]
--------------

``gate shell environment``
    Full path to a shell file that will be sourced to set the environment
    variables correct for running Gate (GateRTion).  Typically this shell
    script contains lines like ``source /path/to/ROOT/bin/thisroot.sh`` and
    ``source /path/to/Geant4/bin/geant4.sh`` to set the ROOT and Geant4
    variables, plus a line like ``export PATH="/path/to/Gate/bin:$PATH"``. If
    GateRTion was compiled with ``USE_ITK`` then an additional line adding the
    ITK library directory may need to be prepended to ``LD_LIBRARY_PATH`` as
    well.

``number of cores``
    This is the number of cores that will be used to simulate a single beam.
    On a small cluster you will typically set this to the total number of available cores.
    On a medium/large cluster (>100 cores) you could set it to a smaller number,
    for instance if you would to leave cores free for other use, if you would like
    to have several simulation jobs run in parallel or if for some reason there is limited
    disk space available for the temporary job data (depending on dose grid size, up to
    a gigabyte per core).

``proton physics list``
    Geant4 physics list for protons. Recommended setting: ``QGSP_BIC_HP_EMZ``

``ion physics list``
    Geant4 physics list for ions. Recommended setting: ``Shielding_EMZ``

.. _rbe-factor-cfg-label:

``rbe factor protons``
    Usually 1.1

.. _air-box-margin-mm-label:

``air box margin [mm]``
    During preprocessing, the CT image is cropped down to enclose the minimum bounding box around the air-padded External ROI
    and TPS dose distribution. The GATE simulation uses different cut parameters and step sizes inside and outside the cropped CT volume:
    crude simulation outside, detailed simulation inside.
    The air padding serves to ensure that the detailed simulation will always start a little bit *before* the particles enter the External ROI volume.
    The default margin is 10 mm.

``remove dose outside external``
    Outside the external (in the air, typically) the dose is about the same as
    inside, but most TPS never show this. If you set this option then IDEAL
    will mask the final dose output, all voxels outside of the external are
    forced to have dose equal to zero. This is e.g. useful to avoid artifacts
    in gamma analysis.

.. _gamma-index-cfg-label:

``gamma index parameters dta_mm dd_percent thr_gray def``
    If leave this setting empty, then IDEAL will not attempt any gamma index calculations.
    If you provide four nonzero values, then IDEAL will try to compute the gamma index distribution with the TPS dose as the reference image,
    but only for the voxels that are a dose above a given threshold.
    
        * ``dta_mm``: distance parameter in mm
        * ``dd_percent``: relative dose difference parameter in percent
        * ``thr_gray``: threshold value in Gray
        * ``def``: default gamma value for target voxels with dose values below threshold

.. _stop-on-script-actor-time-interval-label:

``stop on script actor time interval [s]``
    On each core, the simulation periodically saves the intermediate result for the dose distribution and for the simulation statistics (including the number of primaries simulated so far), and checks if the job control daemon has set a flag to indicate that the statistical goal (number of primaries, average uncertainty, and/or time out) has been reached and that the simulation should stop. This setting specifies the time interval between such save & check moments. Setting this too short will result in a slow down due to network overload, setting it too long will result in overshooting the statistical goals. Two minutes is a reasonable value for this setting. For medium/large number of cores (>100) it could possibly be good to choose longer times.

``htcondor next job start delay [s]``
    When HTCondor "stages" the GateRTion jobs (starts the jobs on the calculation nodes), it starts them not all at the same
    time, but rather with a small delay between each job and the next. This is done on purpose, because all jobs will start
    by reading lots of input and configuration data. We want to avoid or at least reduce the stampede effect in which all these read requests
    are clogging up the network. The best value for this delay needs to found empirically on your network. On a fast network (and with
    fast network cards on all nodes), that is 10Gbit/s or faster, with about 50 physical cores, 1 second delay seems enough, but on a slower
    network, e.g. 1Gbit/s, it is advisable to choose a larger delay, for instance 10 seconds. It is advisable to make sure that this delay value
    times the number of cores is less than the ``stop on script actor time interval [s]``.

``minimum dose grid resolution [mm]``
    The user can configure a dose resolution that is different from the TPS dose resolution by changing the number of voxels.
    Too fine grained resolution will be costly on resources (RAM, disk space) so there is a limit for this, defined by the minimum
    size that a dose voxel should have in each dimension.

    This may not be the optimal way to guard against resource overusage, but
    it's simple and intuitive.  In later releases we could define other
    safeguards, maybe a maximum for the total number of voxels in the dose
    distribution.

.. _output-cfg-label:
    
Output options
    The dose distribution can be saved in several stages of the calculation and in various formats. You can configure which ones you would like to have:

    * ``run gamma analysis``: run and write gamma analysis result to .mhd format
    * ``write mhd unscaled dose``: sum of the dose distributions from all simulation jobs, computed in the CT geometry (cropped to a minimal box around the TPS dose distribution and the External ROI). Since the total number of simulated primaries is much smaller than the total number of particles planned, this dose is much lower than the planned dose. This dose can be useful for debugging purposes and if this option is set then this dose will be exported in MHD format.
    * ``write mhd scaled dose``: this is the unscaled dose multiplied with the '(tmp) correction factor' (see below) and with the ratio of the number of planned particles over the number of simulated particles. For example, if the correction factor is 1.01, 10\ :sup:`11` particles were planned for each of 30 fractions, and 10\ :sup:`8` particles were simulated, then the scaling factor is 30300.
    * ``write mhd physical dose``: this is the scaled dose, resampled (using mass weighted resampling) to the same dose grid as the TPS dose distribution. Saved in MHD format.
    * ``write dicom physical dose``: this is the scaled dose, resampled (using mass weighted resampling) to the same dose grid as the TPS dose distribution. Saved in DICOM format.
    * ``write mhd rbe dose``: for protons, the "Relative Biological Effect" dose is estimated by mulitplying the physical dose by the :ref:`RBE factor for protons <rbe-factor-cfg-label>` setting (typically 1.1). Saved in MHD format. IDEAL can currently not compute RBE dose for other particles than protons.

    * ``write dicom rbe dose``: Save the RBE dose (for protons) in DICOM format.
    * ``write mhd plan dose``: Compute the plan dose (sum of physica/RBE beam doses) and save in MHD format.
    * ``write dicom plan dose``: Compute the plan dose (sum of physica/RBE beam doses) and save in DICOM format.

.. _correction-factors-label:

--------------------------
[(tmp) correction factors]
--------------------------

The computed dose distribution for a given treatment plan may need to be
corrected by a constant factor to correct for a normalization error that can be
due to various causes. Typically this factor is determined using plans and
absolute dose measurements on (water) phantoms. In future releases of GateRTion
this correction factor will be integrated in the beam model, hence the '(tmp)'
in the section name.  The correction factor can be defined for each beam line
and each radiation type separately, using "TreatmentMachineName RadiationType"
as the label and a floating point number (typically close to 1.0) as the value.
For combinations of beamlines and radiation types that are not explicitly
configured, the "default" value will be used. The radiation type is "proton"
for protons and "ion_Z_A_Q" for ions, where Z is the number of protons, A is
the atomic number (number of protons plus number of neutrons) and Q is the
electric charge of the ion in units of ``e``. The radiation type for carbon
ions is ``ION_6_12_6`` and for helium ions it is ``ION_2_4_2``. For example::

    default = 1.0
    IR2HBL ION_6_12_6 = 1.0
    IR2HBL proton = 0.97371
    IR2VBL proton = 1.00
    IR3HBL proton = 0.97371

---------------
[msw scaling]
---------------
This section can be used to define an energy dependent scaling of the msw of each spot in the treatment plan. 
The user defines the scaling by providing the polynomial parameters of p(E) in descending order, where msw'(E) = p(E) * msw(E). 
The correction factor can be defined for each beam line and each radiation type separately, using "TreatmentMachineName RadiationType"
as the label.

	default = 0.0 1.0
	IR2VBL ION_6_12_6 = 0.0 1.0
	IR3HBL ION_6_12_6 =  1.81847493e-09 -1.69699096e-06  3.62323835e-04  9.82505461e-01

---------------
[condor memory]
---------------

For typical IDEAL jobs, all core will be used. But for calculations with a large CT, high resolution dose distribution and/or many 
pencil beams, the RAM usage each Gate process can be so high that it's better not to run on all cores.
An IDEAL job submission to HTCondor includes a "memory request".  This will do two things:

    #. HTCondor will assume that the job is going to use the requested amount of RAM at some point during the run. In order to avoid oversubscribing the RAM and cause swapping, HTCondor will not start running any new jobs if the sum of the requested amounts of RAM would exceed the available RAM.
    #. If a running job uses *more* than the requested amount of RAM for a too long period of time, then that job will be killed or set on hold by HTCondor (the exact policy details can be configured in the :ref:`HTCondor configuration files <condorconfig>`).

You can specify a minimum, default and maximum value of the memory request, in
units of megabyte.  IDEAL makes an estimate of the required RAM with a simple
linear formula: ``RAM = offset + cA*A + cA*B + ...``. Here ``A``, ``B`` are
quantities that are expected to impact the memory usage of the Gate simulation,
such as the number of dose voxels, number of CT voxels and the number of spots.
The estimate will be different for CT and for phantom simulations (because the
phatom does not have "CT voxels"), and for different particles (the cross
section tables, which are responsible for an important part of the RAM usage,
are significantly larger for carbon ions than for protons). The linearity
coefficients (``cA``, ``cB``, etc.) can be set by the user, based on system
observations during a series of test runs with differently sized CTs, phantoms,
dose resolutions and plans. The values given in the example below may be a good
starting configuration for your local cluster, but may need tweaking depending
on the available RAM and other factors.
 

Example configuration::
    # how much memory should condor allocate per job?
    # Condor uses the unit "MB", which might mean either 1024*1024 bytes or 1000*1000 bytes.
    condor memory request minimum [MB] =  7000
    condor memory request default [MB] =  8000
    condor memory request maximum [MB] = 50000
    condor memory fit proton ct = offset 1200 dosegrid 2.5e-05 ct 1.8e-06
    condor memory fit proton phantom = offset 500.0 dosegrid 2.0e-05 nspots 0.0060
    condor memory fit carbon ct = offset 1800 dosegrid 5e-05 
    condor memory fit carbon phantom =  offset 1000.0 dosegrid 8.0e-06
    # if e.g. a proton plan gets a dose grid of 200*200*200=8e6 voxels and a ct with 16e6 voxels
    # then the memory fit gives 1200 + 8e6*2.5e-5 + 16e6 * 1.8e-6 = 1428.8 MB estimated max RAM usage

.. _materials-details-label:

-----------
[materials]
-----------

Everything about materials and material overrides.

``materials database``
    With this setting the basename of the material database should be specified. IDEAL then expects to find
    a file with this name in the ``material`` subdirectory of the :ref:`commissioningdir`.
    This file *can* just be the standard database file `GateMaterials.db <https://github.com/OpenGATE/Gate/blob/develop/GateMaterials.db>`_ that is
    included in the source code package for Gate and defines a large number of
    materials that are important typical Gate applications but are not included in
    the standard set of Geant4 materials.  The Gate material database is a simple
    text file, which you can extend with any additional materials that are relevant
    in your clinic. It is recommended to give such an extended database file a name
    that makes it clear that this database is different from the standard material
    database file. E.g.::

        materials database = MyClinicalMaterials2020.db
        
``hu density tolerance [g/cm3]``
    The Schneider 2000 method is used to convert Hounsfield Unit (HU) values to materials, based
    on a density curve and a material composition table (see section :ref:`cthlut-label`).
    For each new combination of density and composition Geant4 needs to define a new material.
    The density tolerance value defines the maximum difference between two "equivalent" density values.
    The full range of HU values is segmented in intervals such that the densities within each interval
    are equivalent to each other, and only one material defintion is associated with each interval.

Override materials
    You may sometimes want to override the material in a region of interest (ROI) in a CT
    with a particular material from the database, to be used by Gate/Geant4 instead of the materials
    given by the Schneider tables. A typical use case for this is that in a CT of a water phantom,
    the volume of the phantom is overridden with ``G4_WATER``, the standard Geant4 definition of water.
    For all materials that you expect to use for such overrides (Geant4 materials or materials that you
    provide in the material database file, see above), you should add a line in this section
    of the system configuration file that associates the name of the material with a density (in units of ``g/cm3``).
    For instance::

	G4_WATER = 1.0
	G4_AIR = 0.00120479
	G4_GRAPHITE = 2.21
	G4_STAINLESS-STEEL = 8.0
	G4_ALANINE = 1.42
	PMMA = 1.195
	Tungsten = 19.3
	G4_Ti = 4.54

    It would be nice if you only needed to give the list of the names of the
    allowed materials and that IDEAL would figure out the densities somehow
    from Geant4's and Gate's databases. This may be implemented in a future
    release, hopefully. For now, you just need to make sure that the density
    values that you give here are consistent with what the Gate and Geant4
    databases are using.

------------
[user roles]
------------

This is the list of users that are expected/allowed to use this installation of IDEAL in a particular role.
For users with more than role you need to add one line per role. Each line is of the form ``ACRONYM, username = role``.
Here ``username`` is a name without whitespaces that contains part of the name of a user plus a word that indicates the role.
ACRONYM is a short version of the user name, for instance just the user's initials.
The role can be ``clinical``, ``commissioning`` or ``admin`` (see :ref:`user-roles-label`).
Each username and acronym should be unique.

For instance::

    OKE, obiwan = clinical
    OKE_A, obiwan_admin = admin
    OKE_C, obiwan_commissioning = commissioning
    LSK, luke = clinical
    LSK_C, luke_commissioning = commissioning
    LES, leiha = clinical
    HSO, han = clinical
    DVA, darth = commissioning
    YOD_A, yoda_admin = admin
    YOD_C, yoda_commissioning = commissioning
