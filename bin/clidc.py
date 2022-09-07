#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------


import sys,os
import logging
from glob import glob
from impl.system_configuration import get_sysconfig
from impl.idc_details import IDC_details
from impl.idc_enum_types import MCStatType
from impl.job_executor import job_executor
from impl.hlut_conf import hlut_conf
from impl.version import version_info
from impl.dicom_functions import *

def get_args():
    import argparse
    parser = argparse.ArgumentParser( description="""
Command Line interface for Independent Dose Calculation with "IDEAL".

The main input is a DICOM plan file. The CT, structure set and TPS dose files
are supposed to be in the same directory as the plan file, or in one of its
subdirectories.  The information of the treatment plan is converted into a GATE
simulation, which is run on every core of an cluster that is managed with
HTCondor.

Since this script is used in a clinical setting, you need to specify who you
are and which role you have, using the "-l" option. The roles can be
"clinical", "commissioning", "admin" and "researcher". The "admin" user is in
charge of installing and maintaining the IDEAL software and hardware (typically
a Linux cluster). The "admin" user also assigns the user roles. The
"commissioning" user is in charge of providing and testing the beam models and
Hounsfield lookup tables for the CT protocols that are in use at the user site.
The clinical user can only use the default models and settings. A research user
can override everything.

This script has besides the 'role' option three different groups of options.

The first set of options (which have upper case single letter option names) is
for querying an input plan and to figure out which names of ROIs, beamlines, CT
protocols should be used.

The second set of options (lower case single letter option names) are for
configuring a GATE simulation of a pencil beam scanning ion therapy treatment
plan to compute the dose distribution.  For some queries you also need to
provide a configure option, e.g. for querying the default dose resolution you
need to specify either a phantom name (to indicate that you would like to
ignore the CT and compute the dose in that phantom instead) or the name of a CT
protocol (to confirm that you would like to use that).

The third set of options deals with the statistical constraints/goals, namely
the minimum number of primary particles (-n), the maximum run time (-t) and/or
the average statistical uncertainty that should be reached (-u). Do not mix the
query options with the statistical goal options. By default, none of these
constraints/goals are enabled, you enable them by providing a nonzero value. If
you enable more than one statistical goal/constraint, then the time-out
priority has the highest priority and the statistical uncertainty the lowest.

Examples of all 7 possible combinations of the three constraints/goals:

-n 1000000: stop when >1000000 primaries were simulated.
-u 1.5: stop when average statistical uncertainty in the high dose region is <1.5%.
-t 18000: stop after running for >5 hours.
-n 1000000 -u 5: run >1000000 primaries, and then continue running until <5% uncertainty is reached.
-t 18000 -u 5: try to reach <5% uncertainty, but stop if it takes >5 hours.
-t 18000 -n 1000000: try to simulate >1000000 primaries, but stop if it takes longer than 5 hours.
-t 18000 -n 1000000 -u 2.0: stop after 5 hours, unless the goals of running >1000000 primaries
                            AND <2% average statistical accuracy have been reached earlier.

The constraints are not checked after every individually simulated primary.
Rather, they are checked periodically (e.g. every two minutes, this can be
configured). This means that the constraints will be exceeded by a bit: you may
get a couple of thousand primaries more than you asked for, the simulation may
keep running for a while after the timeout has expired and/or the average
statistical uncertainty may be slightly better than the goal.
""", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dicom_planfile", default="", nargs='?',
            help="DICOM planfile with a sequence of ion beams.")
    parser.add_argument("-V","--version",default=False,action='store_true', help="Print version label and exit.")
    parser.add_argument("-TD","--test_dicoms",default=False,action='store_true', help="Check dicom files completeness.")
    parser.add_argument("-v","--verbose",default=False,action='store_true', help="write DEBUG level log messages to stdout")
    parser.add_argument("-l","--username",
            help="The user name will be included in paths of output & logging files & directories, in order to make it easier to know which user requested which simulations.")
    parser.add_argument("-d","--debug",default=False,action='store_true',
            help="debugging mode: do not delete any temporary/intermediate data")
    parser.add_argument("-f","--score_dose_on_full_CT",default=False,action='store_true',
            help="debugging feature: write out dose on CT grid (i.e. no resampling to TPS dose resolution and the CT will not be cropped, but material overrides WILL be performed).")
    parser.add_argument("-b","--beams", action='append',
            help="Config: list of beams that should be simulated (default: all)")
    parser.add_argument("-B","--list_beam_names", default=False,action='store_true',
            help="Query: list of beam names defined in a given treatment plan")
    parser.add_argument("-c","--ctprotocol",
            help="Config: which CT protocol (HU to density calibration curve) to use")
    parser.add_argument("-C","--list_available_ctprotocols",default=False,action='store_true',
            help="Query: list which CT protocols (HU to density calibration curve) are available.")
    parser.add_argument("-p","--phantom",
            help="Config: which phantom to use")
    parser.add_argument("-P","--list_available_phantoms", default=False,action='store_true',
            help="Query: list which phantoms can be used")
    parser.add_argument("-R","--list_roi_names", default=False,action='store_true',
            help="Query: list which ROI names are defined in the structure set used by the input plan(s).")
    parser.add_argument("-x","--nvoxels", nargs=3, type=int,
            help="Config: number of dose grid voxels per dimension")
    parser.add_argument("-X","--default_nvoxels", default=False, action='store_true',
            help="Query: list default number of dose grid voxels per dimension, for a given treatment plan")
    parser.add_argument("-z","--beamline_override",
            help="Config: override the beamline (treatment machine) for all beams. Default: use for each beam the treatment machine given by DICOM plan.")
    parser.add_argument("-Z","--list_available_beamline_names", default=False,action='store_true',
            help="Query: list the names of the available beam line (treatment machine) models.")
    parser.add_argument("-a","--padding_material", default="",
            help="Config: name of material to use for padding the CT in case the dose matrix sticks out.")
    parser.add_argument("-m","--material_overrides", action='append',
            help="Config: list of material override specifications of the form 'ROINAME:MATERIALNAME'")
    parser.add_argument("-M","--list_available_override_materials", default=False,action='store_true',
            help="Query: list which override materials can be used in the -n (padding material) and -m (ROI-wise material override) options.")
    parser.add_argument("-s","--sysconfig",default="",
            help="Config: alternative system configuration file (default is <installdir>/cfg/system.cfg")
    parser.add_argument("-j","--number_of_cores",default=0,type=int,
            help="Stats: Number of concurrent subjobs to run per beam (if 0: njobs = number of cores as given in the system configuration file).")
    parser.add_argument("-n","--number_of_primaries_per_beam",default=0,type=int,
            help="Stats: number of primary ions to simulate.")
    parser.add_argument("-u","--percent_uncertainty_goal",default=0.,type=float,
            help="Stats: average uncertainty to achieve in dose distribution.")
    parser.add_argument("-t","--time_limit_in_minutes",default=0,type=int,
            help="""Stats: number of minutes each simulation job is allowed to run.
    Actual simulation time will be at least 5 minutes longer due to pre- and post-processing, as well as possible queue waiting time.""")
    args = parser.parse_args()
    if args.version:
        print(version_info)
        sys.exit(0)
    # check stats, queries & configs
    stats   = [attr for attr in ["number_of_primaries_per_beam",
                                 "percent_uncertainty_goal",
                                 "time_limit_in_minutes"] if getattr(args,attr)>0]
    plan_queries = [attr for attr in ["list_roi_names",
                                      "list_beam_names",
                                      "default_nvoxels",
                                      "test_dicoms"] if bool(getattr(args,attr))]
    queries = [attr for attr in ["list_available_ctprotocols",
                                 "list_available_phantoms",
                                 "list_beam_names",
                                 "list_roi_names",
                                 "default_nvoxels",
                                 "list_available_override_materials",
                                 "list_available_beamline_names",
                                 "test_dicoms"] if bool(getattr(args,attr))]
    configs = [attr for attr in ["beams",
                                 "ctprotocol",
                                 "phantom",
                                 "nvoxels",
                                 "padding_material",
                                 "material_overrides",
                                 "score_dose_on_full_CT",
                                 "beamline_override"] if bool(getattr(args,attr))]
    #print("queries=({}) configs=({}) stats=({})".format(",".join(queries),",".join(configs),",".join(stats)))
    if len(queries)>0 and len(stats)>0:
        raise RuntimeError("Please call this script *either* with 'query' options *or* with 'statistical goal' options, not with both.")
    if len(queries)==0 and len(stats)==0:
        raise RuntimeError("Please specify either one or more query options, or one or more statistical goals/constraints!")
    if bool(args.ctprotocol) and bool(args.phantom):
        raise RuntimeError("You cannot specify BOTH a CT protocol AND a phantom geometry.")
    return args,len(queries)>0,len(plan_queries)>0
 
if __name__ == '__main__':
    args,query,plan_query = get_args()
    want_logfile="" if (bool(query) or bool(plan_query)) else "default"
    try:
        sysconfig = get_sysconfig(filepath     = args.sysconfig,
                                  verbose      = args.verbose,
                                  debug        = args.debug,
                                  username     = args.username,
                                  want_logfile = want_logfile)
        logger = logging.getLogger()
    except Exception as e:
        print(f"OOPS, sorry! Problems getting system configuration, error message = '{e}'")
        sys.exit(1)
    if 0>=args.number_of_cores:
        njobs = sysconfig['number of cores']
    else:
        njobs = args.number_of_cores
        sysconfig.override('number of cores',njobs)
    #ddir = sysconfig['HLUT/density']
    #all_density_files      = dict([(f,os.path.join(ddir,f)) for f in os.listdir(ddir)])
    all_hluts=hlut_conf.getInstance()
    all_phantom_specs      = sysconfig["phantom_defs"]
    all_override_materials = sysconfig['ct override list']
    prefix="\n * "
    if args.list_available_ctprotocols:
        print("available CT protocols: {}{}".format(prefix,prefix.join(all_hluts.keys())))
    if args.list_available_phantoms:
        print("available phantoms: {}{}".format(prefix,prefix.join(all_phantom_specs.keys())))
    if args.list_available_override_materials:
        print("available override materials: {}{}".format(prefix,prefix.join(all_override_materials.keys())))
    if args.list_available_beamline_names:
        blmap=dict()
        for src_prop in glob(os.path.join(sysconfig['beamlines'],"*","*_*_source_properties.txt")):
            b=os.path.basename(src_prop)
            d=os.path.basename(os.path.dirname(src_prop))
            p=b[len(d)+1:-len("_source_properties.txt")]
            if d in blmap:
                blmap[d].append(p)
            else:
                blmap[d] = [p]
        for beamline,plist in blmap.items():
            print("Beamline/TreatmentMachine {} has a beam model for radiation type(s) '{}'".format(beamline,"' and '".join(plist)))
    if query and not plan_query:
        sys.exit(0)
        
    if plan_query and not bool(args.dicom_planfile):
	    print("For 'plan queries' (get ROI/beam names, default number of dose grid voxels), please provide a plan file.")
	    sys.exit(1)
	# Test dicom files
    if args.test_dicoms:
        #check_RP(args.dicom_planfile)
        all_dcm = dicom_files(args.dicom_planfile)
        all_dcm.check_all_dcm()
		
    username = sysconfig["username"]
    material_overrides = dict()
    if args.material_overrides is None:
        logger.debug("did not get any material override")
    else:
        logger.debug("got material override(s):{}{}".format(prefix,prefix.join(args.material_overrides)))
        for override in args.material_overrides:
            if len(override.split(":")) != 2:
                raise RuntimeError("got bad material override '{}': should be of the form 'ROI:MATERIAL'".format(override))
                sys.exit(1)
            roi,mat = override.split(":")
            if roi in material_overrides.keys():
                raise RuntimeError("got multiple material overrides for the same ROI '{}'".format(roi))
                sys.exit(2)
            if mat.upper() not in [m.upper() for m in all_override_materials.keys()]:
                raise RuntimeError("the material '{}' is unknown/unrecognized/unsupported/forbidden".format(mat))
            # it's OK, maybe. :)
            material_overrides[roi] = mat
    matdb = os.path.join(sysconfig['commissioning'], sysconfig['materials database'])
    logger.debug("material database is {}".format(matdb))
    ##############################################################################################################
    current_details = IDC_details()
    rp = str(args.dicom_planfile)
    current_details.SetPlanFilePath(str(args.dicom_planfile))
    if bool(args.padding_material):
        mat=args.padding_material
        if mat not in [m.upper() for m in all_override_materials.keys()]:
            raise RuntimeError("the padding material '{}' is unknown/unrecognized/unsupported/forbidden".format(mat))
        current_details.dosepad_material = mat
    if bool(args.score_dose_on_full_CT):
        current_details.score_dose_on_full_CT = True
    if bool(args.beamline_override):
        logger.info(f"beamline override {args.beamline_override}")
        current_details.beamline_override = args.beamline_override
    else:
        logger.debug("NO beamline override")
    if args.phantom is not None:
        phantoms = [ spec for label,spec in all_phantom_specs.items() if args.phantom.lower() in label.lower() ]
        exact_phantoms = [ spec for label,spec in all_phantom_specs.items() if args.phantom.lower() == label.lower() ]
        if len(phantoms)==1:
            logger.info("Running plan with phantom {}".format(phantoms[0]))
            current_details.UpdatePhantomGEO(phantoms[0])
        elif len(exact_phantoms)==1:
            logger.info("Running plan with phantom {}".format(exact_phantoms[0]))
            current_details.UpdatePhantomGEO(exact_phantoms[0])
        else:
            logger.error("unknown or ambiguous phantom name '{}', see -P to get a list of available phantom options".format(args.phantom))
            sys.exit(4)
        if args.material_overrides is not None:
            raise RuntimeError("for a geometrical phantom (no CT) you cannot specify override materials")
    elif current_details.run_with_CT_geometry:
        logger.debug("Running plan with CT")
    else:
        logger.error("Plan requires a phantom geometry, please specify phantom with the -p option, see -P to get a list of available phantom options")
        sys.exit(3)
    if args.list_roi_names:
        print("ROI names in {}:{}{}".format(rp,prefix,prefix.join(current_details.roinames)))
    if args.list_beam_names:
        print("beam names in {}:{}{}".format(rp,prefix,prefix.join(current_details.beam_names)))
    if args.default_nvoxels:
        nx,ny,nz = current_details.GetNVoxels()
        sx,sy,sz = current_details.GetDoseResolution()
        print("nvoxels for {0}:\n{1} {2} {3} (this corresponds to dose grid voxel sizes of {4:.2f} {5:.2f} {6:.2f} mm)".format(rp,nx,ny,nz,sx,sy,sz))
    if plan_query:
        sys.exit(0)
    if args.nvoxels:
        logger.info("got nvoxels override: {}".format(args.nvoxels))
        for idim,nvoxel in enumerate(args.nvoxels):
            if nvoxel<1:
                raise RuntimeError("number of voxels should be positive, got nvoxels[{}]={}".format(idim,nvoxel))
            if nvoxel>1000:
                raise RuntimeError("number of voxels should be less than or equal to 1000, got nvoxels[{}]={}".format(idim,nvoxel))
            current_details.UpdateDoseGridResolution(idim,nvoxel)
    if args.phantom is None:
        logger.debug("no phantom => we will try to use the CT")
        # if the user did not specify a protocol, then 'hlut_conf' will try to detect it automagically
        # TODO: maybe wrap the 'SetHLUT' call in a try-except block?
        current_details.SetHLUT(args.ctprotocol)
        for roi,mat in material_overrides.items():
            if roi not in current_details.roinames:
                logger.error("unknown roi name '{}', the structure set used by the current plan consists of:{}{}".format(
                    roi,prefix,prefix.join(current_details.roinames)))
                raise RuntimeError("unknown roi name '{}'".format(roi))
            current_details.SetHUOverride(roi,mat)
    if args.beams is not None:
        selection = dict([(name,False) for name in current_details.beam_names])
        for name in args.beams:
            if name not in selection.keys():
                logger.error("{} is not a beam name in plan {}; known beams:{}{}".format(name,rp,prefix,prefix.join(current_details.beam_names)))
                sys.exit(4)
            selection[name]=True
        current_details.SetBeamSelection(selection)
    statset=False
    if args.percent_uncertainty_goal > 0:
        logger.debug("simulation goal is {} % average uncertainty".format(args.percent_uncertainty_goal))
        current_details.SetStatistics(MCStatType.Xpct_unc_in_target,args.percent_uncertainty_goal)
        statset=True
    if args.time_limit_in_minutes > 0:
        logger.debug("simulation goal is {} minutes per job, for {} jobs.".format(args.time_limit_in_minutes,njobs))
        current_details.SetNJobs(njobs)
        current_details.SetStatistics(MCStatType.Nminutes_per_job,args.time_limit_in_minutes)
        statset=True
    if args.number_of_primaries_per_beam > 0:
        logger.debug("simulation goal is {} ions per beam".format(args.number_of_primaries_per_beam))
        current_details.SetStatistics(MCStatType.Nions_per_beam,args.number_of_primaries_per_beam)
        statset=True
    if not statset:
        logger.error("at least positive simulation goal should be set")
        sys.exit(1)
    jobexec = job_executor.create_condor_job_executor(current_details)
    ret=jobexec.launch_subjobs()
    if ret!=0:
        logger.error("Something went wrong when submitting the job, got return code {}".format(ret))
        sys.exit(ret)

# vim: set et softtabstop=4 sw=4 smartindent:
