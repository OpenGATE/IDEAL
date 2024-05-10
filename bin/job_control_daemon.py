#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

# standard stuff
import time
import os
import sys
import logging
import configparser
from glob import glob
from datetime import datetime

# pip installed stuff
import daemon
import itk
import numpy as np
from filelock import Timeout, SoftFileLock

# IDEAL stuff
from impl.system_configuration import get_sysconfig, system_configuration
from impl.version import version_info
from utils.resample_dose import mass_weighted_resampling

def update_user_logs(user_cfg,status,section="DEFAULT",changes=dict()):
    if bool(user_cfg):
        parser=configparser.ConfigParser()
        logger.debug("going to read user logs/settings in {}".format(user_cfg))
        with open(user_cfg,"r") as fp:
            parser.read_file(fp)
        logger.debug("going to update user logs/settings in section {}".format(section))
        if bool(changes):
            parser[section].update(changes)
        parser['DEFAULT']["status"] = status
        parser['DEFAULT']["date and time of last update"] = datetime.now().ctime()
        with open(user_cfg,"w") as fp:
            parser.write(fp)
        logger.debug("finished updating user logs/settings in {}".format(user_cfg))

class dose_monitoring_config:
    """
    The dose monitoring gets its configuration input from three sources:
    * the command line arguments (e.g. to get the job stopping criteria)
    * the post processing config file (e.g. to get the mass file)
    * the system configuration file (e.g. to get the parameters for the uncertainty calculation)
    """
    def __init__(self,workdir,username,daemonize=False,uncertainty_goal_percent=0,minimum_number_of_primaries=0,time_out_minutes=0,sysconfig="",verbose=False,polling_interval_seconds=-1):
        self.workdir = workdir
        self.verbose = verbose
        self.username = username
        self.daemonize = daemonize
        self.unc_goal_pct = uncertainty_goal_percent
        self.min_num_primaries = minimum_number_of_primaries
        self.time_out_minutes = time_out_minutes
        self.time_out_seconds = time_out_minutes*60
        self.polling_interval_seconds = polling_interval_seconds
        self.sysconfigfile = sysconfig
        post_proc_cfg = os.path.join(self.workdir,"postprocessor.cfg")
        if not os.path.exists(post_proc_cfg):
            msg = f"The file {post_proc_cfg} does not seem to exist; maybe you need to set the work directory path with the -w option?"
            raise FileNotFoundError(msg)
        with open(post_proc_cfg,"r") as fp:
            cparser=configparser.RawConfigParser()
            cparser.optionxform = lambda option : option
            cparser.read_file(fp)
            self.user_cfg = cparser['user logs file']['path']
            apply_mask_mhd = cparser.getboolean("DEFAULT","apply external dose mask",fallback=False)
            mask_mhd = cparser.defaults().get("external dose mask","")
            if apply_mask_mhd and not bool(mask_mhd):
                msg = "masking of dose with external requested, but no mask provided"
                raise RuntimeError(msg)
            mass_mhd = cparser.defaults().get("mass mhd","")
            self.apply_mask_mhd = apply_mask_mhd
            self.mask_mhd = os.path.join(self.workdir,mask_mhd) if bool(mask_mhd) else None
            self.mass_mhd = os.path.join(self.workdir,mass_mhd) if bool(mass_mhd) else None
            self.out_dose_nxyz = np.array([float(w) for w in cparser.defaults().get("dose grid resolution").split()])
            self.sim_dose_nxyz = np.array([float(w) for w in cparser.defaults().get("sim dose resolution").split()])
            self.dose_mhd_list=list()
            self.beamname_list=list()
            for beamname in cparser.sections():
                if beamname.lower() =='default' or beamname.lower() =='user logs file':
                    print("skipping section '{}'".format(beamname))
                    continue
                print("going to add dose file for beam name '{}' to the list".format(beamname))
                origname = cparser[beamname]["origname"]
                self.beamname_list.append(origname)
                dosemhd=cparser.get(beamname,"dosemhd")
                dose2water=cparser.getboolean(beamname,"dose2water")
                self.dose_mhd_list.append(dosemhd.replace(".mhd","-DoseToWater.mhd" if dose2water else "-Dose.mhd"))
                print("added dose file '{}'".format(self.dose_mhd_list[-1]))


class dose_collector:
    """
    The dose collector adds up the dose from all subjobs and if necessary computes the statistical ("Type A") uncertainty.
    """
    def __init__(self,cfg):
        self.out_dose_nxyz = cfg.out_dose_nxyz.astype(int) #np.int
        self.sim_dose_nxyz = cfg.sim_dose_nxyz.astype(int) #np.int

        if bool(cfg.mask_mhd):
            self.mask = itk.imread(os.path.join(cfg.workdir,cfg.mask_mhd))
            self.amask = itk.array_view_from_image(self.mask)
            if not (self.out_dose_nxyz[::-1] == self.amask.shape).all():
                msg = "mask resolution {} inconsistent with expected output dose resolution {}".format(self.out_dose_nxyz[::-1],self.amask.shape)
                logger.error(msg)
                raise RuntimeError(msg)
        else:
            self.mask = None
        if bool(cfg.mass_mhd):
            #self.mass = itk.imread(cfg.mass_mhd)
            self.mass = itk.imread(os.path.join(cfg.workdir,cfg.mass_mhd))
            self.amass = itk.array_view_from_image(self.mass)
            if not (self.sim_dose_nxyz[::-1] == self.amass.shape).all():
                raise RuntimeError("mass resolution {} inconsistent with expected simulation dose resolution {}".format(self.sim_dose_nxyz[::-1],self.amass.shape))
        else:
            self.mass = None
        if bool(cfg.mass_mhd) != bool(cfg.mask_mhd):
            msg  = "got mass_mhd={} and mask_mhd={}".format(cfg.mass_mhd,cfg.mask_mhd)
            msg += "you should provide EITHER both the mass and the mask file, OR neither of them."
            logger.error(msg)
            raise RuntimeError(msg)
        self.cfg = cfg
        syscfg = system_configuration.getInstance()
        self.ntop = syscfg["n top voxels for mean dose max"]
        self.toppct = syscfg["dose threshold as fraction in percent of mean dose max"]
        self.reset()
    def reset(self):
        # the sums
        self.dosesum = np.zeros(self.out_dose_nxyz[::-1],dtype=float)
        # the sums of the squares
        self.dose2sum = np.zeros(self.out_dose_nxyz[::-1],dtype=float)
        self.weightsum = 0
        self.wmin = np.inf
        self.wmax = -np.inf
        self.mean_unc_pct = np.inf
        self.n = 0
    def get_nprimaries(self,dose_file):
        statActorTxt=os.path.basename(dose_file).replace("idc-","statActor-").replace("-DoseToWater.mhd",".txt").replace("-Dose.mhd",".txt")
        statspath=os.path.join(os.path.dirname(dose_file),statActorTxt)
        logger.debug("going to get #primaries from stat actor file {}".format(statspath))
        assert(os.path.exists(statspath))
        with open(statspath,"r") as sf:
            for line in sf:
                pat="# NumberOfEvents ="
                if line[:len(pat)] == pat:
                    n = int(line.strip().split(" = ")[1])
                    logger.debug("{} got {} primaries".format(dose_file,n))
                    return n
    @property
    def tot_n_primaries(self):
        return int(self.weightsum)
    def add(self,dose_file):
        lockfile = dose_file+".lock"
        dose = None
        n_primaries=0
        t0=datetime.now()
        logger.debug("lockfile exists" if os.path.exists(lockfile) else "lockfile does not exist")
        lock = SoftFileLock(lockfile)
        try:
            # TODO: the length of the timeout should maybe be configured in the system configuration
            with lock.acquire(timeout=3):
                t1=datetime.now()
                logger.info("acquiring lock file took {} seconds".format((t1-t0).total_seconds()))
                ##########################
                n_primaries = self.get_nprimaries(dose_file)
                if n_primaries<1:
                    logger.warn(f"dose file seems to be based on too few primaries ({n_primaries})")
                elif bool(self.mass) and bool(self.mask):
                    tick = time.time()
                    simdose=itk.imread(dose_file)
                    logger.debug("Time to read dose file: "+str(time.time()-tick)+"s")
                    logger.debug("resampling dose with size {} using mass file of size {} to target size {}".format(itk.size(simdose),itk.size(self.mass),itk.size(self.mask)))
                    tick = time.time()
                    dose = mass_weighted_resampling(simdose,self.mass,self.mask)
                    logger.debug("Time for resampling: "+str(time.time()-tick)+"s")
                    del simdose
                else:
                    tick = time.time()
                    dose=itk.imread(dose_file)
                    logger.debug("Time to read dose file: "+str(time.time()-tick)+"s")
                    logger.debug("read dose with size {}".format(itk.size(dose)))
                t2=datetime.now()
                logger.info("acquiring dose data {} file took {} seconds".format(os.path.basename(dose_file),(t2-t1).total_seconds()))
                if self.wmin>n_primaries:
                    self.wmin = n_primaries
                if self.wmax<n_primaries:
                    self.wmax = n_primaries
        except Timeout:
            logger.warn("failed to acquire lock for {} for 3 seconds, giving up for now".format(dose_file))
            return
        if not bool(dose):
            logger.warn("skipping {}".format(dose_file))
            return
        tick = time.time()
        adose = itk.array_from_image(dose)
        print("Time array from image: "+str(time.time()-tick)+"s")
        if adose.shape != self.dosesum.shape:
            raise RuntimeError("PROGRAMMING ERROR: dose shape {} differs from expected shape {}".format(adose.shape,self.dosesum.shape))
        tick = time.time()
        self.dosesum += adose # n_primaries * (adose / n_primaries)
        self.dose2sum += adose**2 / n_primaries # n_primaries * (adose / n_primaries)**2
        self.weightsum += n_primaries
        self.n += 1
        logger.debug("Time increment variables: "+str(time.time()-tick)+"s")
    def estimate_uncertainty(self):
        if self.n < 2:
            return
        if self.mask:
            amask = itk.array_view_from_image(self.mask)
            logger.info("applying mask with {} voxels enabled out of {}".format(np.sum(amask>0),np.prod(amask.shape)))
            self.dosesum *= amask
            self.dose2sum *= amask
        logger.info("dose sum is nonzero in {} voxels".format(np.sum(self.dosesum>0)))
        logger.info("dose**2 sum is nonzero in {} voxels".format(np.sum(self.dose2sum>0)))
        logger.info("sum of weights is {}, wmin={}, wmax={}".format(self.weightsum,self.wmin,self.wmax))
        amean = self.dosesum/self.weightsum
        amean2 = self.dose2sum/self.weightsum
        avariance = amean2 - amean**2
        m0 = avariance<0
        logger.info("negative variance in {} voxels".format(np.sum(m0)))
        avariance[m0] = 0.
        m0 = amean<0
        logger.info("negative mean in {} voxels".format(np.sum(m0)))
        amean[m0] = 0.
        m0 = amean>0
        m00 = amean2>0
        logger.info("positive mean in {} voxels".format(np.sum(m0)))
        logger.info("positive mean of squares in {} voxels".format(np.sum(m00)))
        logger.info("positive mean and mean of squares masks are different in {} voxels".format(np.sum(m0!=m00)))
        logger.info("average/median of nonzero variance in is {}/{}".format(np.mean(avariance[m0]),np.median(avariance[m0])))
        logger.info("average/median of nonzero mean in is {}/{}".format(np.mean(amean[m0]),np.median(amean[m0])))
        logger.info("average/median of nonzero mean of squares in is {}/{}".format(np.mean(amean2[m0]),np.median(amean2[m0])))
        logger.info("average/median of nonzero square of the mean in is {}/{}".format(np.mean(amean[m0]**2),np.median(amean[m0]**2)))
        std_pct = np.full_like(avariance,100.)
        std_pct[m0] = np.sqrt(avariance[m0]/self.n)*100./amean[m0]
        dmax = np.mean(np.partition(amean.flat,-self.ntop)[-self.ntop:])
        dthr = dmax * self.toppct / 100.0
        mask = (amean>dthr)
        logger.info("{} voxels have more than {} percent of the 'max dose'".format(np.sum(mask),self.toppct))
        self.mean_unc_pct = np.mean(std_pct[mask])
        # if no goal is specified, this will never converge
        converged = self.mean_unc_pct < self.cfg.unc_goal_pct
        logger.info("'mean uncertainty' = {0:.2f} pct, goal = {1} pct, => {2}".format(self.mean_unc_pct,self.cfg.unc_goal_pct,"CONVERGED" if converged else "CONTINUE"))

def check_accuracy_for_beam(cfg,beamname,dosemhd,dose_files):
    tick = time.time()
    dc=dose_collector(cfg)
    logger.debug("Time to create dose collector: "+str(time.time()-tick)+ "s")
    ndosefiles=0
    nfinished=0
    ncrashed=0
    for dose_file in dose_files:
        ndosefiles+=1
        outputdir=os.path.basename(os.path.dirname(dose_file))
        retfile = os.path.join(cfg.workdir,outputdir,"gate_exit_value.txt")
        if os.path.exists(retfile):
            try:
                with open(retfile,"r") as f:
                    ret=int(f.readline().strip())
                    if 0 == ret:
                        nfinished+=1
                        final_dose_file = os.path.join(cfg.workdir,outputdir,dosemhd)
                        dc.add(final_dose_file)
                        logger.debug(f"adding {final_dose_file} to list of summable dose files, because Gate terminated successfully.")
                    else:
                        ncrashed+=1
                        logger.warn(f"omitting {dose_file} from list of summable dose files, because Gate terminated with return code {ret}.")
            except Exception as e:
                logger.error(f"gate exit file {retfile} exists but a problem arose when trying to read the return value from it: {e}")
        else:
            tick1 = time.time()
            dc.add(dose_file)
            logger.debug("Time to add single dose file: "+str(time.time()-tick1)+ "s")
            
    logger.info(f"found {ndosefiles} dose files '{dosemhd}'")
    logger.info(f"using {dc.n} for summed dose, {nfinished} jobs have finished successfully, {ncrashed} jobs have crashed.")
    tick2 = time.time()
    dc.estimate_uncertainty()
    logger.debug("Time to check accuracy: " + str(time.time()-tick2) + "s")
    logger.debug("Tot time for accuracy: " + str(time.time()-tick) + "s")
            
    return dc

def periodically_check_statistical_accuracy(cfg):
    # Get/Create the system config only now, AFTER (possibly) daemonizing.
    # Because the system config creation also initializes the logging system,
    # which does not like to be daemonized.
#    if cfg.daemonize:
#        want_logfile=os.path.join(cfg.workdir,"job_control_daemon.log")
#    else:
#        want_logfile="default"
    #syscfg = get_sysconfig(filepath=cfg.sysconfigfile,verbose=cfg.verbose,debug=False,username=cfg.username,want_logfile=want_logfile)
    syscfg = system_configuration.getInstance()
    global logger
    logfilename = os.path.join(cfg.workdir,"job_control_daemon.log")
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s')
    fh = logging.FileHandler(logfilename)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    cfg.polling_interval_seconds = syscfg['stop on script actor time interval [s]'] if cfg.polling_interval_seconds<0 else cfg.polling_interval_seconds
    t0 = None
    save_curdir=os.path.realpath(os.curdir)
    try:
        #config_logging(cfg)
        os.chdir(cfg.workdir)
        if len(cfg.dose_mhd_list)==0:
            logger.error("zero dose files configured?!")
        while len(cfg.dose_mhd_list)>0:
            logger.debug(f"going to sleep for {cfg.polling_interval_seconds} seconds")
            time.sleep(cfg.polling_interval_seconds)
            logger.debug("waking up from polling interval sleep")
            for beamname,dosemhd in zip(cfg.beamname_list,cfg.dose_mhd_list):
                logger.info(f"checking {dosemhd} for beam={beamname}")
                dose_files = glob(os.path.join(cfg.workdir,"tmp","output.*.*",dosemhd))
                if len(dose_files) == 0:
                    logger.info(f"looks like simulation for {dosemhd} did not start yet (zero dose files)")
                    continue
                if t0 is None:
                    # as starting time we take the creation time of the tmp directory
                    # TODO: maybe I should include the path of 'tmp' in syscfg instead of hardcoding it everywhere
                    t0 = datetime.fromtimestamp(os.stat('tmp').st_ctime)
                    logger.info(f"starting the clock at t0={t0}")
                    
                status = f"RUNNING GATE FOR BEAM={beamname}"   
                dc = check_accuracy_for_beam(cfg,beamname,dosemhd,dose_files)
        
                sim_time_minutes = (datetime.now()-t0).total_seconds()/60.
                tmsg = f"Tsim = {sim_time_minutes} minutes (timeout = {cfg.time_out_minutes} minutes)"
                nmsg = f"Nsim = {dc.tot_n_primaries} primaries (minimum = {cfg.min_num_primaries})"
                umsg = f"Average Uncertainty = {dc.mean_unc_pct} pct (goal = {dc.cfg.unc_goal_pct} pct)"
                stop = False
                msg = ""
                # Maybe the following logic tree can be compactified, but for now I prefer to spell it out very explicitly
                if sim_time_minutes > cfg.time_out_minutes > 0:
                    stop = True
                    msg = "STOP: time is up: " + tmsg
                elif cfg.min_num_primaries > 0:
                    if dc.tot_n_primaries < cfg.min_num_primaries:
                        stop = False
                        msg = "CONTINUE: not yet enough primaries: " + nmsg
                    elif dc.cfg.unc_goal_pct > 0:
                        if dc.mean_unc_pct < dc.cfg.unc_goal_pct:
                            stop = True
                            msg = "STOP: uncertainty goal reached: " + umsg
                        else:
                            stop = False
                            msg = "CONTINUE: uncertainty goal NOT YET reached: " + umsg
                    else:
                        stop = True
                        msg = "STOP: desired number of primaries reached: " + nmsg
                elif dc.cfg.unc_goal_pct > 0:
                    if dc.mean_unc_pct < dc.cfg.unc_goal_pct:
                        stop = True
                        msg = "STOP: uncertainty goal reached: " + umsg
                    else:
                        stop = False
                        msg = "CONTINUE: uncertainty goal NOT YET reached: " + umsg
                else:
                    stop = False
                    msg = "CONTINUE: time out not yet reached: " + tmsg
                logger.info(f"{dosemhd} {tmsg} {nmsg} {umsg}")
                logger.info(msg)
                update_user_logs(cfg.user_cfg,status,section=beamname,changes={"job control daemon status":msg})
                if stop:
                    with open(os.path.join(cfg.workdir,"STOP_"+dosemhd),"w") as stopfd:
                        stopfd.write("{msg}\n")
                    cfg.dose_mhd_list.remove(dosemhd)
                    cfg.beamname_list.remove(beamname)
    except Exception as e:
        logger.error(f"job control daemon failed: {e}")
    os.chdir(save_curdir)

if __name__ == '__main__':

    # TODO: make it possible to create this config file without command line arguments
    # step 1: get command line args
    import argparse
    aparser = argparse.ArgumentParser(description="""
Daemon program to interact with an active IDEAL job and determine when the job
should be stopped.

NOTE: Normally, the job daemon is started by `clidc.py` after successful submission
of a job with HTCondor.  If for some reason the job daemon dies before the job
is finished, it can be restarted manually. The most important argument is '-w'
to provide the working directory of the job that is currently running (or
queued) on the cluster and in need of a job daemon.

The three criteria for stopping or continuing a job are, in order of decreasing priority:
(1) maximum simulation time (not including the preprocessing, postprocessing, and queue wait time);
(2) minimum number of primaries to simulate;
(3) maximum average uncertainty.
At least one of these three criteria should be given.
If all three are given, then the simulation will stop when the time out has
been reached, or earlier if at least the minimum of primaries was simulated and
the statistical uncertainty shrank below the threshold.
""",
epilog="""
Do NOT manually start a second daemon if one is still running for a job!
The script is not protected against such incorrect usage and the results are
undefined.
""", formatter_class=argparse.RawDescriptionHelpFormatter)
    aparser.add_argument("-s","--sysconfig",default="",help="alternative system configuration file (default is <installdir>/cfg/system.cfg)")
    aparser.add_argument("-w","--workdir",default=os.curdir,help="path to workdir of simulation to interact with")
    aparser.add_argument("-v","--verbose",default=False,action='store_true',help="be verbose")
    aparser.add_argument("-V","--version",default=False,action='store_true', help="Print version label and exit.")
    aparser.add_argument("-d","--daemonize",default=False,action='store_true',help="run as daemon in the background")
    aparser.add_argument("-l","--username",help="Your user name (default: your login name).")
    aparser.add_argument("-p","--polling_interval_seconds",type=int, default=-1,help="Override polling interval (in seconds) from the system config file.")
    aparser.add_argument("-u","--uncertainty_goal_percent",type=float,default=0.,help="Uncertainty level (in percent) at which the simulations should stop (default: 0 percent).")
    aparser.add_argument("-n","--minimum_number_of_primaries",type=int,default=0,help="If nonzero: minimum number of primaries for a simulation (default: 0).")
    aparser.add_argument("-t","--time_out_minutes",type=int,default=0, help="If nonzero: time-out, maximum of time that a job is allowed to run, apart from pre- and post-processing (default: 0 minutes).")
    args = aparser.parse_args()
    if args.version:
        print(version_info)
        sys.exit(0)
        
    cfg = dose_monitoring_config(args.workdir,args.username,daemonize=args.daemonize,uncertainty_goal_percent=args.uncertainty_goal_percent,
                                 minimum_number_of_primaries=args.minimum_number_of_primaries,time_out_minutes=args.time_out_minutes,
                                 sysconfig=args.sysconfig,verbose=args.verbose,polling_interval_seconds=args.polling_interval_seconds)
    if cfg.daemonize:
        want_logfile=os.path.join(cfg.workdir,"job_control_daemon.log")
    else:
        want_logfile="default"
    #print(f"{want_logfile=}")  
    syscfg = get_sysconfig(filepath=cfg.sysconfigfile,verbose=cfg.verbose,debug=False,username=cfg.username,want_logfile=want_logfile)
    
    if len(cfg.dose_mhd_list) == 0:
        raise RuntimeError("something is wrong: zero dose files to look at")
    if cfg.daemonize:
        print("running as daemon")
        logfile=os.path.join(cfg.workdir,"job_control_daemon.log")
        print("log file should be {}".format(logfile))
        with daemon.DaemonContext():
            periodically_check_statistical_accuracy(cfg)
    else:
        periodically_check_statistical_accuracy(cfg)
else:
    logger = logging.getLogger()


# vim: set et softtabstop=4 sw=4 smartindent:
