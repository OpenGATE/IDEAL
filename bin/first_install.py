#!/usr/bin/env python3

"""
After you installed the IDEAL source code, you can use this script to set up
a (hopefully) working first draft of the data directory and the system configuration
file, and to create a virtual python environment (with ITK, matplotlib, pydicom, etc).
"""

# system stuff
import os, sys, stat
# utilities
import tempfile
import subprocess
import re
import shutil
import argparse
import getpass
import configparser

verbose=False

def printv(msg):
    if verbose:
        print(msg)

try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])),'ideal','impl'))
    import version
    printv(f"Got proper version blurb {version.blurb}.")
except ImportError:
    class version:
        blurb="IDEAL"
    printv(f"No version info found, keeping virtual env prompt shorter.")

def check_python():
    """
    We need Python version 3 and 'virtualenv', otherwise we won't even start talking.
    """
    if sys.version_info.major!=3 and sys.version_info.minor!=12:
        raise RuntimeError(f"Python version should be 3.12, got {sys.version_info} instead.")
    try:
        result=subprocess.run(["/usr/bin/which","virtualenv"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,universal_newlines=True)
        printv(f"Looks like 'virtualenv' is available: {result.stdout}")
    except subprocess.CalledProcessError as cpe:
        raise ValueError(f"Looks like 'virtualenv' is not installed? Please check this error:\n{result.stderr}")

def get_condor_node_data():
    try:
        # it would be nice to use the htcondor python bindings for this, but this seems easier
        cmdlist=["condor_status",  "-format", "%s ", "Name", "-format", "%d ","Cpus","-format","%d\n","Memory"]
        result=subprocess.run(cmdlist,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,universal_newlines=True)
        mem_per_cpu=list()
        mem_per_node=dict()
        tot_ncpus = 0
        for line in result.stdout.splitlines():
            slotname,ncpus_str,memory_mb_str = line.split()
            ncpus = int(ncpus_str)
            memory_mb = float(memory_mb_str)
            nodename=slotname.split("@")[1]
            printv(f"got condor slotname={slotname} (nodename={nodename}) ncpus={ncpus_str} memory_mb={memory_mb_str}")
            assert(ncpus>0)
            assert(memory_mb>0)
            tot_ncpus += ncpus
            mem_per_cpu.append(memory_mb/ncpus)
            if nodename in mem_per_node:
                mem_per_node[nodename] += memory_mb
            else:
                mem_per_node[nodename] = memory_mb
        # convert from MiB to GiB (more natural unit for today's users)
        if len(mem_per_cpu)==0:
            raise RuntimeError("Got no response from 'condor_status' at all.")
        min_ram_per_core = min(mem_per_cpu)/1024.
        max_ram_per_node = max(mem_per_node.values())/1024.
        printv(f"condor says total number of available CPUs is {tot_ncpus}")
        printv(f"condor says minimum ram per core is {min_ram_per_core} GiB")
        printv(f"condor says maximum ram per node is {max_ram_per_node} GiB")
        return tot_ncpus,min_ram_per_core,max_ram_per_node
    except subprocess.CalledProcessError as cpe:
        printv("*** WARNING: Failed to get cluster information with\n"+" ".join(cmdlist))
        printv(f"*** WARNING: Got error code {cpe.returncode} and error stream {cpe.stderr}")
        return 0,0,0
    except ValueError as ve:
        printv(f"Programming error (what version of Condor are you running?): {ve}")
        return 0,0,0
    except RuntimeError as re:
        printv(f"ERROR: {re}")
        return 0,0,0


# The following ``check_*`` functions each check a configuration item from the command line args.
# They save the result in the 'cfg' dictionary if it's OK.
# They raise a 'ValueError' in case something is wrong.

def check_data(args,cfg):
    """
    This function checks whether the currently selected (default or
    user-provided) path for the data directory is suitable for its purpose. We
    should have the permissions to write data in the proposed directory, to create
    it does not exist yet and if it does, then it should not contain any old data.

    TODO: check that the data directory is also visible from the condor nodes.
    """
    datadir=os.path.realpath(args.data)
    cfg["renew data"]=False
    cfg["reuse data"]=False
    if datadir != args.data:
        printv(f"You entered '{args.data}' as the data directory, I will use the full absolute path '{datadir}' instead, that should be equivalent.")
    if os.path.exists(datadir):
        # If it already exists, it should in principle be empty.
        if os.path.isdir(datadir):
            if len(os.listdir(datadir))>0:
                if args.force:
                    print(f"Warning: {datadir} is an already existing directory and it is not empty, going to rename it (with a .bak suffix) and then recreate!")
                    cfg["renew data"]=True
                else:
                    raise ValueError(f"{datadir} is an already existing directory and it is not empty! Rerun with -f to proceed anyway.")
            else:
                cfg["reuse data"]=True
                printv(f"{datadir} is an already existing and empty directory, so far so good...")
        else:
            raise ValueError(f"{datadir} seems to exist already but it is not a directory!")
        dir_check = datadir
    else:
        printv(f"{datadir} does not yet exist, going to check if at least one of the ((great-)grand-)parents exists.")
        creation_list = list()
        fullpath=datadir
        while not os.path.exists(fullpath):
            creation_list.append(os.path.basename(fullpath))
            fullpath = os.path.dirname(fullpath)
            if fullpath in creation_list:
                # this should in principle be impossible
                raise ValueError(f"I don't know how to create a directory with path '{datadir}'")
        if not os.path.isdir(fullpath):
            raise ValueError(f"I don't know how to create a directory with path '{datadir}' because '{fullpath}' is something other than a directory.")
        printv(f"{fullpath} is an already existing directory, so far so good...")
        dir_check = fullpath
    # Check that we are able to create something in (a parent directory of) the requested data directory.
    printv(f"Going to check that we can create a file in '{dir_check}'...")
    try:
        testfilename=os.path.join(dir_check,"testfile.txt")
        fp=open(testfilename,"w")
        fp.write("foo bar")
        fp.close()
        os.unlink(testfilename)
        printv("Looks like it went well.")
    except Exception as e:
        raise ValueError(f"Looks like we are not able to write anything in directory '{dir_check}': '{e}'. Please choose a data directory path to which a normal user (without sudo rights) has permissions to create files and subdirectories.")
    # Check that there is enough space
    diskspace = os.statvfs(dir_check)
    GiB = float(1024*1024*1024)
    available_GiB = diskspace.f_bsize*diskspace.f_bavail/GiB
    want_GiB = float(args.diskspace_minimum)
    if available_GiB < want_GiB:
        msg = f"It looks like there is not enough disk space in {dir_check} (available={available_GiB} GiB, want={want_GiB} GiB)"
        if args.force:
            print(f"*** WARNING: {msg}")
        else:
            raise ValueError(msg)
    # Yay!
    printv(f"data directory '{datadir}' seems OK to use for IDEAL.")
    cfg["data"] = datadir
    return

# def check_gate_env_sh(args,cfg):
#     gate_env_sh = os.path.realpath(args.gate_env_sh)
#     gate_rt_ion = False
#     if not os.path.exists(gate_env_sh):
#         raise ValueError(f"{gate_env_sh} does not seems to exist")
#     if gate_env_sh[-3:] != ".sh":
#         raise ValueError(f"Hmmmm.... got {gate_env_sh} as the Gate environment shell script, but I was expecting something with a '.sh' suffix.")
#     shtext=f"""
# set -e
# set -x
# source {gate_env_sh}
# Gate --version
# """
#     with tempfile.NamedTemporaryFile(prefix="testgateenv",suffix=".sh",delete=False) as shtest:
#         shtest.write(bytes(shtext,'utf-8'))
#         shtest.close()
#         try:
#             result = subprocess.run(["/bin/bash",shtest.name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,universal_newlines=True)
#             if str(result.stdout).strip() == 'Gate version is "GateRTion 1.0, based on GATE 8.1 (April/May 2018)"':
#                 gate_rt_ion = True
#                 printv("Gate version is 'GateRTion 1.0', good!")
#             else:
#                 print("*** WARNING: IDEAL should run with GateRTion 1.0, your gate_env.sh script provides a different version: '" + str(result.stdout).strip() + "'")
#         except subprocess.CalledProcessError as cpe:
#             msg="\n".join([f"Something seems wrong with '{gate_env_sh}, please check. I tried this: '",shtext,"', stdout="+cpe.stdout, ", stderr="+cpe.stderr])
#             raise RuntimeError(msg)
#         os.unlink(shtest.name)
#         cfg["gate_env.sh"] = gate_env_sh
#         cfg["GateRTion 1.0"] = gate_rt_ion
#         return
#     raise ValueError("I tried this: {shtext} and it looks like it does not work, I got an error...")


def check_username(args,cfg):
    c=str(args.username).strip()
    # alphanumeric and underscore are allowed
    if re.match('^\w\w\w+$', c) is not None:
        cfg["username"] = c
    else:
        raise ValueError("Please provide a username of at least 3 alphanumeric characters.")
    c=str(args.tla).strip()
    if c=='...':
        cfg["tla"] = cfg["username"][:3].upper()
    elif re.match('^\w\w\w$', c) is not None:
        cfg["tla"] = c.upper()
    else:
        raise ValueError("Please provide a three letter acronym (--tla) of exactly 3 alphanumeric characters (or leave it unspecified).")

def check_ncores_memory(args,cfg,def_ncores,def_min_ram_per_core_in_GiB,def_max_ram_per_node_in_GiB):
    warnprefix="*** WARNING: looks like you are trying to configure IDEAL with "
    if args.ncores<1:
        raise ValueError("You should allow IDEAL to use at least 1 core")
    if def_ncores>0 and args.ncores>def_ncores:
        print(warnprefix + f"more cluster cores ({args.ncores}) than the total number of CPUs on all Condor nodes ({def_ncores}).")
    if args.ncores<4:
        raise ValueError("IDEAL/Gate needs at least 4 cores to run on (recommended is 50-100 cores).")
    if args.min_memory_per_core<2.:
        raise ValueError(f"{args.min_memory_per_core} GiB/core is not enough, IDEAL/Gate needs at least 2 GiB/core (for carbon ions  at least 4GiB/core).")
    if def_min_ram_per_core_in_GiB>0 and args.min_memory_per_core>def_min_ram_per_core_in_GiB:
        print(warnprefix + f"more memory per core ({args.min_memory_per_core}) than you seem to have available on the cluster ({def_min_ram_per_core_in_GiB}), at least on some of the nodes.")
    if args.min_memory_per_core<=0.5*def_min_ram_per_core_in_GiB:
        print(warnprefix + "lower than necessary amount memory per core than you have available, it is less than half of the minimal RAM estimate based on 'condor_status' data.")
    if args.max_memory_per_node<=args.min_memory_per_core:
        raise ValueError("Maximum memory per node should be larger than minimum memory core!")
    if def_max_ram_per_node_in_GiB>0 and args.max_memory_per_node>def_max_ram_per_node_in_GiB:
        print(warnprefix + f"larger maximum memory per job ({args.max_memory_per_node}) than you seem to have available on any of the nodes ({def_max_ram_per_node_in_GiB}).")
    printv(f"Configuring ncores={args.ncores}, default is {def_ncores}.")
    cfg["ncores"] = args.ncores
    printv(f"Configuring min memory per core={args.min_memory_per_core} GiB, default is {def_min_ram_per_core_in_GiB} GiB.")
    cfg["min memory per core"] = args.min_memory_per_core * 1024
    printv(f"Configuring max memory per node={args.max_memory_per_node} GiB, default is {def_max_ram_per_node_in_GiB} GiB.")
    cfg["max memory per node"] = args.max_memory_per_node * 1024
    return

def check_clinic(args,cfg):
    c=str(args.clinic).strip()
    # alphanumeric, underscore, dot and hyphen characters are allowed.
    if re.match('^\w[\w.-]*\w$', c) is not None:
        cfg["clinic"] = c
        printv(f"using clinic name '{c}'")
        return
    l=len(c)
    nbad=len([bad for bad in c if re.match('^[^\w.-]$',bad)])
    printv(f"Clinic name length is {l}, contains {nbad} bad characters.")
    raise ValueError(f"The clinic name that you gave is not usable: '{c}'\n"
                     +"Please give a string of at least two charachters long for the clinic name.\n"
                     +"Alphanumeric, dot, hyphen and underscore charecters are allowed.\n"
                     +"First and last character should not be period or hyphen.")

def init_cfg():
    cfg = dict()
    cfg["installdir"] = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
    cfg["template commissioning data"] = os.path.join(cfg["installdir"],"docs","commissioning","template_commissioning_data")
    cfg["template system.cfg"] = os.path.join(cfg["installdir"],"docs","commissioning","template_system.cfg")
    cfg["template log_daemon.cfg"] = os.path.join(cfg["installdir"],"docs","commissioning","template_log_daemon.cfg")
    cfg["template api.cfg"] = os.path.join(cfg["installdir"],"docs","commissioning","template_api.cfg")
    cfg["venv"] = os.path.join(cfg["installdir"],"venv")
    # paranoid checks
    if not os.path.isdir(cfg["installdir"]):
        raise RuntimeError("Failed to deduce IDEAL installation directory.")
    if not os.path.isdir(cfg["template commissioning data"]):
        raise RuntimeError("Missing from IDEAL installation: template for commissioning directory ({})".format(cfg["template commissioning data"]))
    if not os.path.exists(cfg["template system.cfg"]):
        raise RuntimeError("Missing from IDEAL installation: template for system configuraton file ({})".format(cfg["template system.cfg"]))
    return cfg

def get_cfg():
    parser = argparse.ArgumentParser( description="""
Set up a minimal working system to get IDEAL working on the submit node of a
Linux cluster managed with HTCondor.  Prerequisites are that you have already
configured Condor and that the daemons are running. GateRTion 2.0 is
installed via pip during the insallation.

This script is intended to be run (successfully) only once, at installation
(however, see below).  It will help you make a minimal (hopefully) working
setup with a data directory (for all the modeling and commissioning data, logs,
temporary data and output) and the system configuration file. Once you have a
minimal working system, you can extend and improve it. Please read the IDEAL
sphinx documentation on how to create and add beam models, Hounsfield lookup
tables for different CT protocols, etcetera.

This script has a couple of obligatory inputs (there are no default values) and
a few optional ones (for things that do have a default value). You can run the
script with the "--test_dry_run" and "-v" options, then nothing is actually
done but from the output you can evaluate whether the option values are making
sense or not.

The script tries to check your inputs and checks whether the software that is
needed for installing and running IDEAL is present on the system. If anything
is deemed bad or unwise then the script will fail with a noisy error that
hopefully helps you to resolve the issue (install missing software, choose
better values). For some "issues" (for instance: you provide a path for the
IDEAL data directory which already exists and is not empty), you can choose to
ignore them by using the "--force" option (which in the example of the data
directory will then delete that directory and create a new one with the same
path).
""", formatter_class=argparse.RawDescriptionHelpFormatter)
    # define some defaults and help texts
    data_space_minimum_GiB = 200.
    cfg=init_cfg()
    printv("IDEAL install directory seems to be '{}'".format(cfg["installdir"]))
    def_data = os.path.join(cfg["installdir"],"data")
    helptxt_def_data = f"Data directory path. It should have at least {data_space_minimum_GiB} GiB of disk space available "
    helptxt_def_data += "(but you can lower that threshold with the -D option if you do not want to use the -f option)."
    helptxt_space = "Minimum disk space for the data directory (in GiB). "
    helptxt_space += f"The default value is {data_space_minimum_GiB}. "
    helptxt_space += "Experience shows that you need at least this much, choosing a lower value is possible but not recommended."
    helptxt_ncores = "Number of cluster cores to use for IDEAL. "
    helptxt_min_mem = "Minimum amount of RAM in gigabyte available per *core* on all nodes (default RAM allocation per job when submitting jobs). "
    helptxt_min_mem += "This number should be >=2, but <= 90%% of the smallest amount of RAM/core in your cluster."
    helptxt_min_mem += "E.g. if it is 8 GB/core on some hosts and 6 GB/core on others, then you say 5 here. "
    helptxt_max_mem = "Maximum amount of RAM in gigabyte available per *node* on all nodes. "
    helptxt_max_mem += "(This indirectly sets the limit for the largest possible dose calculation, "
    helptxt_max_mem += "mostly determined by the total number of dose voxels but also dependent on radiation type "
    helptxt_max_mem += "and the number of unique HU values in the CT image.) "
    helptxt_max_mem += "E.g. if there is a host in your cluster that has 200 GB of memory and the others have the same or less, then you write 200 here. "
    def_ncores,def_min_ram_per_core_in_GiB,def_max_ram_per_node_in_GiB = get_condor_node_data()
    if def_ncores>0:
        percentage = 90 # prophylaxe: do not use all available RAM
        def_min_ram_per_core_in_GiB *= percentage/100.
        def_max_ram_per_node_in_GiB *= percentage/100.
        helptxt_ncores += f"Default: {def_ncores}, the total number of CPUs in all nodes as reported by 'condor_status'."
        helptxt_min_mem += f"Default: {def_min_ram_per_core_in_GiB:.2f}, {percentage}%% of the minimum that 'condor_status' could find just now."
        helptxt_max_mem += f"Default: {def_max_ram_per_node_in_GiB:.2f}, {percentage}%% of the maximum that 'condor_status' could find just now."
    else:
        helptxt_ncores += "There is no default, because it looks like Condor is not yet up and running."
        helptxt_min_mem += "There is no default, because it looks like Condor is not yet up and running."
        helptxt_max_mem += "There is no default, because it looks like Condor is not yet up and running."
    # create the command line options
    parser.add_argument("-f","--force",default=False,action='store_true', help="Force matters: ignore existing system configuration file and data directories, and disk space.")
    parser.add_argument("-v","--verbose",default=False,action='store_true', help="Increase verbosity")
    parser.add_argument("-t","--test_dry_run",default=False,action='store_true', help="Test dry run: check input and describe what will be done, but don't actually do it.")
    parser.add_argument("-u","--username",default=getpass.getuser(), help="First user, will get all user roles. Default: you!")
    parser.add_argument("-T","--tla",default="...", help="Three Letter Acronym for the first user (default: first three letters of username), will be used in output filenames.")
    # parser.add_argument("-g","--gate_env_sh",required=True,help="Shell script that can be sourced to set the shell environment such that Gate can be run. There is no default.")
    parser.add_argument("-d","--data",default=def_data,help=helptxt_def_data)
    parser.add_argument("-D","--diskspace_minimum",type=float,default=data_space_minimum_GiB,help=helptxt_space)
    parser.add_argument("-n","--ncores",type=int,default=def_ncores,help=helptxt_ncores)
    parser.add_argument("-m","--min_memory_per_core",type=float,default=def_min_ram_per_core_in_GiB,help=helptxt_min_mem)
    parser.add_argument("-M","--max_memory_per_node",type=float,default=def_max_ram_per_node_in_GiB,help=helptxt_max_mem)
    parser.add_argument("-C","--clinic",default="OurClinic",help="Name of your clinic (keep it short, use only alphanumeric characters and underscores)")
    # do it!
    try:
        args = parser.parse_args()
        verbose = args.verbose
        cfg["force"] = args.force
        cfg["test dry run"] = args.test_dry_run
        # These functions will check the args and fill the cfg dictionary.
        # If something is wrong then they will throw an error.
        printv("Going to check data directory")
        check_data(args,cfg)
        printv("Going to check username")
        check_username(args,cfg)
        # printv("Going to check gate environment script")
        # check_gate_env_sh(args,cfg)
        printv("Going to check condor settings (number of cores, memory)")
        check_ncores_memory(args,cfg,def_ncores,def_min_ram_per_core_in_GiB,def_max_ram_per_node_in_GiB)
        printv("Going to check clinic name")
        check_clinic(args,cfg)
        # If we reach this line then all input seems to be OK!
        # if cfg["GateRTion 1.0"]:
        #     printv("Looks like we are able to define a setup with the given settings.")
        # else:
        #     printv("Looks like most things are fine, except for the Gate version.")
        #     if cfg["force"]:
        #         printv("But you are using the '-f/--force' option, so you probably knew that already.")
        return cfg
    except Exception as e:
        verbtxt = "" if verbose else "Rerunning the same command with -v may help understand what is wrong."
        print(f"Something is not right, it seems not yet possible to create your IDEAL setup:\n############\n{e}\n############\n" + verbtxt)
        sys.exit(13)

def verbose_makedirs(descr,d):
    printv(f"Creating {descr}: {d}")
    os.makedirs(d)

def make_backup(descr,d):
    assert(os.path.exists(d))
    printv(f"going to backup (actually: rename) {descr}: {d}")
    src=d
    dest=d
    i=0
    while os.path.exists(dest):
       dest = d + f".bak{i}"
       i += 1
    printv(f"{src} -> {dest}")
    os.rename(src,dest)

def make_venv(venv):
    venv_parent = os.path.dirname(venv)
    assert(os.path.isdir(venv_parent)==True)
    assert(os.path.exists(venv)==False)
    venv_stdout = venv+".stdout"
    venv_stderr = venv+".stderr"
    venv_sh = venv+".sh"
    pkglist = "filelock htcondor itk matplotlib numpy pydicom python-daemon python-dateutil scipy Flask Flask-RESTful requests pandas PyYAML cryptography Flask-SQLAlchemy apiflask"
    try:
        with open(venv_sh,"w") as venv_sh_fp:
            venv_sh_fp.write("""
            set -e
            set -x
            python3.12 -m venv  --prompt='{0}' {1}
            source {1}/bin/activate
            pip install --upgrade pip
            pip install opengate
            pip install {2}
            """.format(version.blurb,venv,pkglist))
    except Exception as e:
        raise RuntimeError(f"Looks like we do not have write permission in {venv_parent}: {e}.")
    try:
        printv("Going to create virtual environment with Python modules needed for IDEAL. May take a minute or two, depending on network speed.")
        # TODO: can we implement something like a progress bar?
        result=subprocess.run(["/bin/bash",venv_sh],stdout=open(venv_stdout,'w'),stderr=open(venv_stderr,'w'),check=True,universal_newlines=True)
    except subprocess.CalledProcessError as cpe:
        msg="\n".join(["Failed to create and populate a 'virtualenv', please check (script, stdout, stderr):",venv_sh,venv_stdout,venv_stderr])
        raise RuntimeError(msg)
    # success: cleanup
    os.unlink(venv_sh)
    os.unlink(venv_stdout)
    os.unlink(venv_stderr)
    printv("successfully installed a virtual environment in '{venv}'.")

def make_a_basic_install(cfg):
    """
    1. create the virtual environment with Python modules
    2. create & populate the data directory
    3. create the system.cfg file and fill in the template values
    """
    # if not (cfg["GateRTion 1.0"] or cfg["force"]):
    #     print("The gate_env.sh script you provided seems to provide a different version of Gate than GateRTion 1.0. Run with the -f/--force option to install anyway.")
    #     sys.exit(131)
    if cfg["test dry run"]:
        print("You requestd a 'test dry run', hence no system.cfg file was written and no data directory was created.")
        sys.exit(0)
    try:
        if not os.path.isdir(os.path.realpath(cfg["venv"])):
            print("Creating python virtual environment")
            print("GateRTion v2 is installed here via pip")
            # TODO: install the correct version of opengate (10.0.2?)
            make_venv(cfg["venv"])
            # TODO: if 'venv' DOES already exist, should we check it somehow?
        template_dict=dict()
        prefix = "TEMPLATE_"
        if cfg["renew data"]:
            make_backup("pre-existing data directory",cfg["data"])
        if not cfg["reuse data"]:
            verbose_makedirs("data directory",cfg["data"])
        for d in ["logs","work","output"]:
            dd = os.path.join(cfg["data"],d)
            verbose_makedirs(f"{d} directory",dd)
            template_dict[prefix+d.upper()] = dd
        commissioning_data_dir = os.path.join(cfg["data"],cfg["clinic"]+"CommissioningData")
        verbose_makedirs("commissioing data directory",commissioning_data_dir)
        tmplt_dir = cfg["template commissioning data"]
        for d in os.listdir(tmplt_dir):
            src=os.path.join(tmplt_dir,d)
            dest=os.path.join(commissioning_data_dir,d)
            if os.path.isdir(src):
                # beamlines, CT, phantoms
                shutil.copytree(src,dest)
            else:
                # GateMaterials.db
                shutil.copy(src,dest)
        template_dict[prefix+"DATA_DIR"]           = cfg["data"]
        template_dict[prefix+"COMMISSIONING_DATA"] = commissioning_data_dir
        template_dict[prefix+"INPUT"]              = "."
        #template_dict[prefix+"GATE_ENV_SH"]        = cfg["gate_env.sh"]
        template_dict[prefix+"NUMBER_OF_CORES"]    = cfg["ncores"]
        template_dict[prefix+"MIN_RAM_PER_CORE"]   = cfg["min memory per core"]
        template_dict[prefix+"DEF_RAM_PER_CORE"]   = cfg["min memory per core"]
        template_dict[prefix+"MAX_RAM_PER_NODE"]   = cfg["max memory per node"]
        for role,suf3 in zip(["CLINICAL","COMMISSIONING","ADMIN"],["","_C","_A"]):
            suf = "_"+role.lower() if bool(suf3) else ""
            template_dict[prefix+role+"_USER"]     = ", ".join([cfg["tla"]+suf3,cfg["username"]+suf])
        src_syscfg_path = cfg["template system.cfg"]
        dest_syscfg_path = os.path.join(cfg["installdir"],"cfg","system.cfg")
        if os.path.exists(dest_syscfg_path):
            make_backup("pre-existing system config file",dest_syscfg_path)
        chklist=list()
        with open(dest_syscfg_path,"w") as syscfg:
            for line in open(src_syscfg_path,"r"):
                if prefix in line:
                    for k,v in template_dict.items():
                        if k in line:
                            line = line.replace(k,str(v))
                            chklist.append(k)
                syscfg.write(line)
        missing = ", ".join(set(list(template_dict.keys())) - set(chklist))
        if missing:
            # programming error, or a vandalized template file?
            raise RuntimeError(f"How embarrassing. Something seems wrong with the system.cfg template: missing keys: {missing}.")
        return dest_syscfg_path,commissioning_data_dir
    except Exception as e:
        print(f"Well, bummer. Despite all checks something went wrong: {e}")
        sys.exit(1313)

def init_log_daemon_cfg(cfg):
    log_cfg = configparser.ConfigParser(allow_no_value=True)
    template_path = cfg['template log_daemon.cfg']
    log_cfg.read(template_path)
    cfg_path = os.path.join(cfg["installdir"],'cfg','log_daemon.cfg')
    log_dir = os.path.join(cfg["data"],'logs')
    work_dir = os.path.join(cfg["data"],'work')

    log_cfg['Paths']['global logfile'] =  os.path.join(log_dir, 'IDEAL_general_logs.log')  
    log_cfg['Paths']['cfg_log_file'] = os.path.join(log_dir, 'ideal_history.cfg')  
    log_cfg['Paths']['log_daemon_logs'] = os.path.join(log_dir, 'log_daemon.log')
    log_cfg['Paths']['completed_dir'] = os.path.join(work_dir, 'old', 'completed')
    log_cfg['Paths']['failed_dir'] = os.path.join(work_dir, 'old', 'failed')
    log_cfg['Paths']['logs_folder'] = log_dir
    log_cfg['Paths']['api_cfg'] = os.path.join(cfg["installdir"],'cfg','api.cfg')
    log_cfg['Paths']['syscfg'] = os.path.join(cfg["installdir"],'cfg','system.cfg')

    
    with open (cfg_path, 'w') as fp:
        log_cfg.write(fp)

def init_api_cfg(cfg):
    api_cfg = configparser.ConfigParser(allow_no_value=True)
    cfg_path = os.path.join(cfg["installdir"],'cfg','api.cfg')
    template_path = cfg['template api.cfg']
    api_cfg.read(template_path)
    
    with open (cfg_path, 'w') as fp:
        api_cfg.write(fp)
            
    
###############################################################################
if __name__ == '__main__':
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    check_python()
    cfg = get_cfg()
    syscfg,cdir = make_a_basic_install(cfg)
    init_log_daemon_cfg(cfg)
    init_api_cfg(cfg)
    print(f"""
Congratulations, looks like you got your initial IDEAL setup.
System configuration: {syscfg}
Commissioning data directory: {cdir}
Things to do next:
* inspect and improve cfg/system.cfg cfg/log_daemon.cfg cfg/api.cfg
* add density curves (and composition tables) for CT protocols under {cdir}/CT/
* define beamlines under {cdir}/beamlines
""")
