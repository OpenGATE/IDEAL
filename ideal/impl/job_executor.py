# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

"""
This module implements the job executor, which uses a "system configuration"
(system configuration object) and a "plan details" objbect to prepare the
simulation subjobs, to run them, and to combine the partial dose distributions
into a final DICOM dose and to report success or failure.

The job executor is normally created *after* a 'idc_details' object has been
created and configured with the all the plan details and user wishes. The job
executor then creates the Gate workspace and cluster submit files. The job is
not immediately submitted to the cluster: if the user interacts with the
"socrates" GUI, then the user can inspect the configuration by running a
limited number of primaries and visualizing the result with "Gate --qt". After
the OK by the user, the job is then submitted to the cluster and the control is
taken over by the "job control daemon", which monitors the number of simulated
primaries, the statistical uncertainty and the elapsed time since the start of
the simulation and decides when to stop the simulations and accumulate the
final results.
"""

################################################################################
# API
################################################################################

class job_executor(object):
    @staticmethod
    def create_condor_job_executor(details):
        return condor_job_executor(details)
    @property
    def template_gate_work_directory(self):
        return self._RUNGATE_submit_directory
    @property
    def summary(self):
        return self._summary
    @property
    def details(self):
        return self._details
    @property
    def estimated_calculation_time(self):
        return self._ect
    def launch_gate_qt_check(self,beamname):
        return self._launch_gate_qt_check(beamname)
    def launch_subjobs(self):
        return self._launch_subjobs()

################################################################################
# IMPLEMENTATION
################################################################################

# python standard library imports
import os, stat
import re
import logging
import shutil
import time
import tarfile
from glob import glob
from subprocess import Popen
import numpy as np

# IDEAL imports
from utils.gate_pbs_plan_file import gate_pbs_plan_file
from utils.condor_utils import condor_check_run, condor_id
from impl.beamline_model import beamline_model
from impl.hlut_conf import hlut_conf
from impl.idc_enum_types import MCStatType
from impl.system_configuration import system_configuration
from impl.dual_logging import get_high_level_logfile, get_last_log_ID

logger = logging.getLogger(__name__)
# Get file handler to the high level log file
high_log = get_high_level_logfile()

class condor_job_executor(job_executor):
    def __init__(self,details):
        syscfg = system_configuration.getInstance()
        self._details = details
        self._ect = 0.
        self._badchars=re.compile("[^a-zA-Z0-9_]")
        self._time_stamp = time.strftime("%Y_%m_%d_%H_%M_%S")
        self._summary=str()
        self._summary+="TPS Plan/Beamset UID: " + details.uid + "\n"
        self._summary+="IDC user: {}\n".format(syscfg['username'])
        self._set_cleanup_policy(not syscfg['debug'])
        self._mac_files=[]
        self._qspecs={}
        self._set_n_threads()
        self._set_nprocesses() # requires n_threads to be set
        #TODO: bring outside init
        self._generate_RUNGATE_submit_directory()
        self._populate_RUNGATE_submit_directory()
        # update general log file
        high_log.info("IdealID: {}".format(str(get_last_log_ID()+1)))
        high_log.info("Working dir: {}".format(str(self._RUNGATE_submit_directory)))
        
    def _set_cleanup_policy(self,cleanup):
        self._cleanup = cleanup
        if cleanup:
            logger.debug("cleanup requested (no debugging): WILL DELETE intermediate simulation results, keep only final results")
        else:
            logger.debug("debugging requested (no cleaning): intermediate simulation results WILL NOT BE DELETED")
    def _generate_RUNGATE_submit_directory(self):
        plan_uid = self.details.uid
        user = self.details.username
        runid = 0
        while True:
            rungate_dir = os.path.join(self.details.tmpdir_job,f"rungate.{runid}")
            if os.path.exists(rungate_dir):
                runid += 1
            else:
                break
        logger.debug("RUNGATE submit directory is {}".format(rungate_dir))
        os.mkdir(rungate_dir)
        logger.debug("created template subjob work directory {}".format(rungate_dir))
        self._RUNGATE_submit_directory = rungate_dir
        
    def _set_nprocesses(self):
        # TODO: make Ncores (number of subjobs for current calculation) flexible:
        # * depending on urgency/priority
        # * depending on how busy the cluster is
        # * avoid that calculation time will depend on a single job that takes forever
        syscfg = system_configuration.getInstance()
        n_available_cores = syscfg['number of cores']
        self.n_processes = np.amax([1, round(n_available_cores/self.number_requested_cores)])
        
    
    def _setupWorDir(self):
        """ created by MFA/AR6
        11th Oct 2022 Code refactoring
        """
         ####################
        syscfg = system_configuration.getInstance()
        ####################
        assert( os.path.isdir( self._RUNGATE_submit_directory ) )
        os.chdir( self._RUNGATE_submit_directory )
        subDirsInIDCinstance = ["data","logs"]
        for d in subDirsInIDCinstance:
            os.mkdir(d)
        ####################
        shutil.copy(os.path.join(syscfg['commissioning'], syscfg['materials database']),
                    os.path.join("data",syscfg['materials database']))
        if syscfg["write dicom rbe dose"]:
            shutil.copy(os.path.join(syscfg['RBE'],syscfg['rbe table']),'data')

    def _cp_CT_hlut_to_wd(self, macfile_ct_settings):
        """ created by MFA/AR6
        11th Oct 2022 Code refactoring
        """
        dataCT = os.path.join(os.path.realpath("./data"),"CT")
        os.mkdir(dataCT)
        #shutil.copy(os.path.join(syscfg["CT"],"ct-parameters.mac"),os.path.join(dataCT,"ct-parameters.mac"))
        all_hluts = hlut_conf.getInstance()
        # TODO: should 'idc_details' ask the user about a HU density tolerance value?
        # TODO: should we try to catch the exceptions that 'all_hluts' might throw at us?
        cached_hu2mat_txt, cached_humat_db = all_hluts[self.details.ctprotocol_name].get_hu2mat_files()
        hudensity = all_hluts[self.details.ctprotocol_name].get_density_file()
        hu2mat_txt=os.path.join(dataCT,os.path.basename(cached_hu2mat_txt))
        humat_db=os.path.join(dataCT,os.path.basename(cached_humat_db))
        shutil.copy(cached_hu2mat_txt,hu2mat_txt)
        shutil.copy(cached_humat_db,humat_db)
        mcpatientCT_filepath = os.path.join(dataCT,self.details.uid.replace(".","_")+".mhd")
        ct_bb,ct_nvoxels=self.details.WritePreProcessingConfigFile(self._RUNGATE_submit_directory,mcpatientCT_filepath,hu2mat_txt,hudensity)
        macfile_ct_settings.update(#ct_bb = ct_bb, 
                                    dose_nvoxels=ct_nvoxels.tolist(), 
                                    ct_mhd=mcpatientCT_filepath, 
                                    HU2mat=hu2mat_txt, 
                                    HUmaterials=humat_db,
                                    dose_center = self.details.GetDoseCenter(),
                                    dose_size =  self.details.GetDoseSize() )
        
    def _get_macfile_info_for_beam(self, beam, macfile_beam_settings, macfile_ct_settings ):
        ####################
        syscfg = system_configuration.getInstance()
        ####################
        logger.debug(f"configuring beam {beam.Name}")
        ## TODOmfa: move to idc_details
        bmlname = beam.TreatmentMachineName
        logger.debug(f"beamline name is {bmlname}")
        beamnr = beam.Number
        beamname = re.sub(self._badchars,"_",beam.Name)
        if beamname == beam.Name:
            self._summary += "beam: '{}'\n".format(beamname)
        else:
            self._summary += "beam: '{}'/'{}'\n".format(beam.Name,beamname)
        radtype = beam.RadiationType
        physlist = self.details.get_physics_list(beam)
        
        calc_rbe_flag = radtype == 'ION_6_12_6' and syscfg['write dicom rbe dose']
        use_ct_geo_flag=self.details.run_with_CT_geometry
        
        rsids = beam.RangeShifterIDs
        rmids = beam.RangeModulatorIDs
        
        rsflag="(as PLANNED)" if rsids == beam.RangeShifterIDs else "(OVERRIDE)"
        rmflag="(as PLANNED)" if rmids == beam.RangeModulatorIDs else "(OVERRIDE)"
        
        msg  = "BeamNumber={}, BeamName={}, BeamLine={}\n".format(beamnr,beamname,bmlname)
        msg += "* Range shifter(s): {} {}\n".format( ("NONE" if len(rsids)==0 else ",".join(rsids)),rsflag)
        msg += "* Range modulator(s): {} {}\n".format( ("NONE" if len(rmids)==0 else ",".join(rmids)),rmflag)
        #msg += "* {} primaries per job => est. {} s/job.\n".format(nprim,dt)
        logger.debug(msg)
        if rsflag == "(OVERRIDE)" or rmflag == "(OVERRIDE)":
            self._summary += msg
        if self.details.dosegrid_changed:
            self._summary += "dose grid resolution changed to {}\n".format(self.details.GetNVoxels())
        # copy beam model
        beam_model = self.details.GetBeammodel(beamname)
        beammodel_fpath = beam_model.configuration_file_path
        local_beammodel_fpath = os.path.join('data',os.path.basename(beammodel_fpath))
        shutil.copy(beammodel_fpath,local_beammodel_fpath)
        # copy nozzle
        nozzle_path = beam_model.nozzle_file_path
        shutil.copy(nozzle_path,os.path.join('data',os.path.basename(nozzle_path)))
        # copy passive elements
        for label in [*rmids,*rsids]:
            rm_path = beam_model.get_element_filepath(label)
            shutil.copy(rm_path,os.path.join('data',os.path.basename(rm_path)))
        macfile_input = dict( #beamline=bml,
                              beamline_name = bmlname,
                              beamnr=int(beamnr),
                              beamname=beamname,
                              radtype=radtype,
                              rsids=rsids,
                              rmids=rmids,
                              physicslist=physlist,
                              beamline_cfg_path = local_beammodel_fpath,
                              gantry_angle=beam.gantry_angle)
        macfile_input.update(macfile_beam_settings)
        if use_ct_geo_flag:
            #nominal_patient_angle = beam.patient_angle
            mod_patient_angle = (360.0 - beam.patient_angle) % 360.0
            macfile_input.update(mod_patient_angle=mod_patient_angle,
                                  isoC= beam.IsoCenter)
            macfile_input.update(macfile_ct_settings)
        else:
            macfile_input.update( ct=use_ct_geo_flag,
                                  dose_nvoxels=list(self.details.GetNVoxels()),
                                  isoC=list(self.details.PhantomISOinMM(beam.Name)),
                                  )

        macfile_input.update(want_rbe=calc_rbe_flag,
                             rbe_model=syscfg['rbe model carbons'] if calc_rbe_flag else 'not used',
                             rbe_table_filename= syscfg['rbe table'] if calc_rbe_flag else 'not used',
                             )
            
        return macfile_input
    
    def _set_n_threads(self):
        syscfg = system_configuration.getInstance()
        hyper_thread = syscfg['hyper threading']
        number_of_threads = self.details.number_of_threads 
        self.number_requested_cores = number_of_threads
        
        if hyper_thread:
            number_of_threads*=2
        
        self.number_of_threads = number_of_threads
        
        
    def _write_python_arguments(self,syscfg):
        timeout_minutes, min_n_primaries, unc_goal_pct = self.details.mc_stat_thr
        n_threads_per_job = self.number_of_threads
        n_events_sim_max = int(min_n_primaries/self.n_processes)
        n_sim_events_first_check = 1e5
        n_sim_events_interval_check = 8e4
        stat_uncertainty_goal = unc_goal_pct/100
        phantom_spec = self.details.PhantomSpecs
        phantom_name = None
        if phantom_spec:
            phantom_name = phantom_spec.label
        #rp_fpath = 'dcm/E120.0MeV/RP1.2.752.243.1.1.20230802152802865.1390.13763_tagman.dcm'
        
        stat_uncertainty_job_i =  np.sqrt(self.n_processes)*stat_uncertainty_goal
        args_V = ['--seed ${seed}',
                  '--outputdir ${outputdir}',
                  f'--stat_uncertainty {stat_uncertainty_job_i}',
                  f'--workdir {self._RUNGATE_submit_directory}',
                  f'--number_of_threads {n_threads_per_job}',
                  f'--n_particles {n_events_sim_max}',
                  f'--phantom_name {phantom_name}']
        args_str = " ".join(args_V)
       
        return args_str

    def _write_RunGate_sh(self,rsd):
        ####################
        syscfg = system_configuration.getInstance()
        ####################
        with open("RunGATE.sh","w") as jobsh:
            jobsh.write("#!/bin/bash\n")
            jobsh.write("set -x\n")
            jobsh.write("set -e\n")
            jobsh.write("whoami\n")
            jobsh.write("who am i\n")
            jobsh.write("date\n")
            jobsh.write("echo $# arguments\n")
            jobsh.write('echo "pwd=$(pwd)"\n')
            jobsh.write("macfile=$1\n")
            jobsh.write("export clusterid=$1\n")
            jobsh.write("export procid=$2\n")
            jobsh.write("pwd -P\n")
            jobsh.write("pwd -L\n")
            jobsh.write(f"cd {rsd}\n")
            jobsh.write("pwd -P\n")
            jobsh.write("pwd -L\n")
            jobsh.write("outputdir=./output.$clusterid.$procid\n")
            jobsh.write("tmpoutputdir=./tmp/output.$clusterid.$procid\n")
            jobsh.write("mkdir -p $outputdir\n")
            jobsh.write("mkdir -p $tmpoutputdir\n")
            jobsh.write("chmod 777 ./tmp/$outputdir\n")
            jobsh.write("seed=$[1000*clusterid+procid]\n")
            jobsh.write("echo rng seed is $seed\n")
            jobsh.write("ret=0\n")
            path_opengate_scr = os.path.join(syscfg['bindir'],"start_simulations.py") 
            jobsh.write(f"source {os.path.join(syscfg['bindir'],'IDEAL_env.sh')}\n")
            jobsh.write('python ' + path_opengate_scr + ' ' + self._write_python_arguments(syscfg) + '\n')
            jobsh.write("if [ $ret -ne 0 ] ; then echo GATE FAILED WITH EXIT CODE $ret; fi\n")
            # the following is used both in postprocessing and by the job_control_daemon
            jobsh.write("echo $ret > $outputdir/gate_exit_value.txt\n")
            jobsh.write("du -hcs *\n")
            jobsh.write("date\n")
            jobsh.write("echo SECONDS=$SECONDS\n")
            jobsh.write("exit 0\n")
        os.chmod("RunGATE.sh",stat.S_IREAD|stat.S_IRWXU)     
        
    def _write_RunGATEqt_sh(self,use_ct_geo_flag):
        ####################
        syscfg = system_configuration.getInstance()
        ####################
        with open("RunGATEqt.sh","w") as jobsh:
            jobsh.write("#!/bin/bash\n")
            jobsh.write("set -x\n")
            jobsh.write("set -e\n")
            jobsh.write("macfile=$1\n")
            jobsh.write("outputdir=output_qt\n")
            jobsh.write("rm -rf $outputdir\n")
            jobsh.write("mkdir -p $outputdir\n")
            if use_ct_geo_flag:
                jobsh.write("echo running preprocess, may take a minute or two...\n")
                jobsh.write("time {}/preprocess_ct_image.py\n".format(syscfg["bindir"]))
            jobsh.write("echo starting Gate, may take a minute...\n")
            jobsh.write("Gate --qt -a[RUNMAC,mac/run_qt.mac][VISUMAC,mac/visu.mac][OUTPUTDIR,$outputdir] $macfile\n")
            jobsh.write("du -hcs *\n")
        os.chmod("RunGATEqt.sh",stat.S_IREAD|stat.S_IRWXU)
        
    def _write_RunGATE_submit(self):
        ####################
        syscfg = system_configuration.getInstance()
        ####################
        with open("RunGATE.submit","w") as jobsubmit:
            jobsubmit.write("universe = vanilla\n")
            jobsubmit.write("executable = {}/RunGATE.sh\n".format(self._RUNGATE_submit_directory))
            jobsubmit.write("should_transfer_files = NO\n")
            jobsubmit.write(f'+workdir = "{self._RUNGATE_submit_directory}"\n')
            jobsubmit.write("priority = {}\n".format(self.details.priority))
            jobsubmit.write("request_cpus = {}\n".format(self.number_requested_cores))
            # cluster job diagnostics:
            jobsubmit.write("output = logs/stdout.$(CLUSTER).$(PROCESS).txt\n")
            jobsubmit.write("error = logs/stderr.$(CLUSTER).$(PROCESS).txt\n")
            jobsubmit.write("log = logs/stdlog.$(CLUSTER).$(PROCESS).txt\n")
            # boiler plate
            jobsubmit.write("RunAsOwner = true\n")
            jobsubmit.write("nice_user = false\n") # TODO: add to sysconfig / args
            jobsubmit.write("next_job_start_delay = {}\n".format(syscfg["htcondor next job start delay [s]"]))
            jobsubmit.write("notification = error\n")
            # the actual submit command:
            for beamname,qspec in self._qspecs.items():
                origname=qspec["origname"]
                jobsubmit.write("request_memory = {}\n".format(self.details.calculate_ram_request_mb(origname)))
                jobsubmit.write("arguments = $(CLUSTER) $(PROCESS)\n")#.format(qspec['macfile']))
                jobsubmit.write("queue {}\n".format(self.n_processes))
        os.chmod("RunGATE.submit",stat.S_IREAD|stat.S_IWUSR)
        
    def _write_dagman(self,use_ct_geo_flag):
        ####################
        syscfg = system_configuration.getInstance()
        ####################
        with open("RunGATE.dagman","w") as dagman:
            if use_ct_geo_flag:
                dagman.write("SCRIPT PRE  rungate {}/preprocess_ct_image.py\n".format(syscfg["bindir"]))
            dagman.write("JOB         rungate ./RunGATE.submit\n")
            dagman.write("SCRIPT POST rungate {}/postprocess_dose_results.py\n".format(syscfg["bindir"]))
        os.chmod("RunGATE.dagman",stat.S_IREAD|stat.S_IWUSR)
        
                
    def _populate_RUNGATE_submit_directory(self):
        """
        Create the content of the Gate directory: how to run the simulation.
        TODO: This method implementation is very long, should be broken up in smaller entities.
        TODO: In particular, the HTCondor-specific stuff should be separated out,
              so that it will be easier to also support other cluster job management systems, like SLURM and OpenPBS.
        """
        ####################
        syscfg = system_configuration.getInstance()
        ####################
        save_cwd = os.getcwd()
        
        self._setupWorDir()
        
        ## re-define some variables for shorter code and clean special characters
        use_ct_geo_flag=self.details.run_with_CT_geometry
        beamset = self.details.bs_info
        beamsetname = re.sub(self._badchars,"_",beamset.name)
        spotfile = os.path.join("data","TreatmentPlan4Gate-{}.txt".format(beamset.name.replace(" ","_")))
        gate_plan = gate_pbs_plan_file(spotfile,allow0=True)
        gate_plan.import_from(beamset)
        macfile_ct_settings = dict()
        macfile_beam_settings = dict( beamset=beamsetname, spotfile=spotfile,uid=self.details.uid)
        physics_settings = self.details.get_global_physics_settings()
        macfile_beam_settings.update(physics_settings)
        if use_ct_geo_flag:
            #shutil.copytree(syscfg["CT"],os.path.join("data","CT"))
            # copy files and update dictionary with CT data
            self._cp_CT_hlut_to_wd(macfile_ct_settings)
            msg = "IDC with CT geometry"
            # the name has to end in PLAN
            plan_dose_file = f"idc-CT-{beamsetname}-PLAN"
        else:
            # TODO: should we try to only copy the relevant phantom data, instead of the entire phantom collection?
            #shutil.copytree(syscfg["phantoms"],os.path.join("data","phantoms"))
            shutil.copy(self.details.PhantomSpecs.file_path,"data")
            msg = "IDC with PHANTOM geometry"
            phantom_name=self.details.PhantomSpecs.label
            plan_dose_file = f"idc-PHANTOM-{phantom_name}-{beamsetname}-PLAN"
        logger.debug(msg)
        self._summary += msg+'\n'
        ####################
        
        # TODO: do we need this distinction between ncores and njobs?
        # maybe we'll need this for when the uncertainty goal needs to apply to the plan dose instead of beam dose?
        # TODOmfa: correct, maybe best would be: njobs = ncors/numBeams ; to check
        njobs = self.n_processes
        sim_cfg = dict()
        for beam in beamset.beams:
            bmlname = beam.TreatmentMachineName
            if not self.details.BeamIsSelected(beam.Name):
                msg = "skip simulation for de-selected beam name={} nr={} machine={}.".format(beam.Name, beam.Number,bmlname)
                logger.warn(msg)
                continue
            # create macro beam dictionary for each beam
            macfile_input = self._get_macfile_info_for_beam(beam, macfile_beam_settings, macfile_ct_settings )
            beamname = macfile_input['beamname']
            #bml = macfile_input['beamline']
            radtype = beam.RadiationType
            
            if self.details.run_with_CT_geometry:
                beam_dose_mhd = f'idc-CT-{beamset.name}-B{beam.Number}-{beam.Name}-{bmlname}.mhd'
            else:
                phantom_name=self.details.PhantomSpecs.label
                beam_dose_mhd = f'idc-PHANTOM-{phantom_name}-{beamset.name}-B{beam.Number}-{beam.Name}.mhd'
            
            #
            def_dose_corr_factor=syscfg['(tmp) correction factors']["default"]
            dose_corr_key=(bmlname+"_"+radtype).lower()
            dose_corr_factor=syscfg['(tmp) correction factors'].get(dose_corr_key,def_dose_corr_factor)
            #
            self._qspecs[beamname]=dict(nJobs=str(njobs),
                                        origname=beam.Name,
                                        dosecorrfactor=str(dose_corr_factor),
                                        dosemhd=beam_dose_mhd,
                                        dose2water=str(use_ct_geo_flag or self.details.PhantomSpecs.dose_to_water),
                                        isocenter=" ".join(["{}".format(v) for v in beam.IsoCenter]))

            macfile_input.update(beam_dose_mhd = beam_dose_mhd)
            sim_cfg[beamname] = macfile_input

            
        logger.debug("copied all beam line models into data directory")
        logger.debug("wrote mac files for all beams to be simulated")
        #self._summary + "{} seconds estimated for simulation of whole plan".format(self._ect)
        
        ## write condor files ##
        # self.number_of_threads = self.details.number_of_threads 
        rsd=self._RUNGATE_submit_directory
        self.details.WriteOpengateSimulationConfigFile(rsd, sim_cfg)
        os.makedirs(os.path.join(rsd,"tmp"),exist_ok=True) # the 'mode' argument is ignored (not only on Windows)
        os.chmod(os.path.join(rsd,"tmp"),mode=0o777)
        self._write_RunGate_sh(rsd)
        logger.debug("wrote run shell script")
        self._write_RunGATEqt_sh(use_ct_geo_flag)
        logger.debug("wrote run debugging shell script with GUI")
        # TODO: write the condor stuff directly in python?
        input_files = ["RunGATE.sh", "macdata.tar.gz","{}/locked_copy.py".format(syscfg["bindir"])]
        if use_ct_geo_flag:
            input_files.append("ct.tar.gz")
        self._write_RunGATE_submit()
        logger.debug("wrote condor submit file")
        self.details.WritePostProcessingConfigFile(self._RUNGATE_submit_directory,self._qspecs,plan_dose_file)
        self._write_dagman(use_ct_geo_flag)
        logger.debug("wrote condor dagman file")
        with tarfile.open("macdata.tar.gz","w:gz") as tar:
            #tar.add("mac")
            tar.add("data")
        logger.debug("wrote gzipped tar file with 'data' and 'mac' directory")
        os.chdir( save_cwd )
        
    def _launch_gate_qt_check(self,beam_name):
        beamname = re.sub(self._badchars,"_",beam_name)
        if beamname not in self._qspecs.keys():
            logger.error("cannot run gate-QT viewer: unknown beam name '{}'".format(beamname))
            return -1
        macfile = self._qspecs[beamname]['macfile']
        if not os.path.isdir( self._RUNGATE_submit_directory ):
            logger.error("cannot find submit directory {}".format(self._RUNGATE_submit_directory))
            return -2
        save_cwd = os.getcwd()
        os.chdir( self._RUNGATE_submit_directory)
        ret=os.system( " ".join(["./RunGATEqt.sh",macfile]))
        logger.debug("RunGATEqt.sh exited with return code {}".format(ret))
        os.chdir( save_cwd )
        logger.debug("ret={} has type {}".format(ret,type(ret)))
        return ret
    
    def _launch_subjobs(self):
        if not os.path.isdir( self._RUNGATE_submit_directory ):
            logger.error("cannot find submit directory {}".format(self._RUNGATE_submit_directory))
            return -1
        syscfg = system_configuration.getInstance()
        save_cwd = os.getcwd()
        os.chdir( self._RUNGATE_submit_directory )
        ymd_hms = time.strftime("%Y-%m-%d %H:%M:%S")
        userstuff = self.details.WriteUserSettings(self._qspecs,ymd_hms,self._RUNGATE_submit_directory)
        on = condor_check_run()
        if on == 0:
            high_log.info('Condor master and scheduler OK')
        else:
            high_log.error('Condor_master or condor_schedd NOT RUNNING! Exit the program.')
            raise RuntimeError("Condor_master or condor_schedd not running")
        ret,cid = condor_id( "condor_submit_dag ./RunGATE.dagman")
        self.submission_date = '-'
        if ret==0:
            msg = "Job submitted at {}\n".format(ymd_hms)
            self.submission_date = ymd_hms
            msg += "User settings are summarized in \n{}\n".format(userstuff)
            self.settings = userstuff
            msg += "Condor ID: {}\n".format(cid)
            high_log.info(msg)
            self._summary += msg
            msg += "Final output will be saved in \n'{}'\n".format(self.details.output_job)
            msg += "GATE job submit directory:\n'{}'\n".format(self._RUNGATE_submit_directory)
            msg += "GUI logs:\n'{}'\n".format(syscfg["log file path"])
            logger.info(msg)
            #success = launch_job_control_daemon(self._RUNGATE_submit_directory)
            #if self.details.mc_stat_type == MCStatType.Xpct_unc_in_target:
            # ~ ret=os.system( "{bindir}/job_control_daemon.py -l {username} -t {timeout} -n {minprim} -u {uncgoal} -p {poll} -d -w '{workdir}'".format(
                # ~ bindir=syscfg['bindir'],
                # ~ username=syscfg['username'],
                # ~ # DONE: change this into Nprim, Unc, TimeOut settings
                # ~ #goal=self.details.mc_stat_thr,
                # ~ timeout=self.details.mc_stat_thr[MCStatType.Nminutes_per_job],
                # ~ minprim=self.details.mc_stat_thr[MCStatType.Nions_per_beam],
                # ~ uncgoal=self.details.mc_stat_thr[MCStatType.Xpct_unc_in_target],
                # ~ poll=syscfg['stop on script actor time interval [s]'],
                # ~ workdir=self._RUNGATE_submit_directory))
            # ~ if ret==0:
                # ~ msg="successful start of job statistics daemon"
                # ~ self._summary += msg+"\n"
                # ~ logger.info(msg)
            # ~ else:
                # ~ msg="FAILED to start job statistics daemon"
                # ~ self._summary += msg+"\n"
                # ~ logger.error(msg)
        else:
            msg = "Job submit error: return value {}".format(ret)
            high_log.info(msg)
            self._summary += msg
            logger.error(msg)
        os.chdir( save_cwd )
        return ret,cid

################################################################################
# UNIT TESTS (would be nice)
################################################################################
#
#import unittest
#import sys
#from system_configuration import get_sysconfig

# vim: set et softtabstop=4 sw=4 smartindent:
