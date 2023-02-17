# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import time
import logging
import os
import configparser

def timestamp():
    return time.strftime("%Y_%m_%d_%H_%M_%S")

def get_dual_logging(verbose=False,quiet=False,level=None,prefix="logfile",daemon_file=None,jobId = '', logDir =''):
    """
    Configure logging such that all log messages go both to
    a file and to stdout, filtered with different log levels.
    """

    #logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s')

    # create file handler which logs even debug messages
    if daemon_file:
        logfilename = daemon_file
    else:
        if jobId:
            logfilename="{}.log".format(jobId)
            if logDir:
                logfilename = os.path.join(logDir, logfilename)
        else:
            logfilename="{}_{}.log".format(prefix,timestamp())
            
    fh = logging.FileHandler(logfilename)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # create console handler with a higher log level
    if daemon_file is None:
        if level is None:
            if verbose:
                level=logging.DEBUG
            elif quiet:
                level=logging.WARN
            else:
                level=logging.INFO
        assert(level in [logging.DEBUG,logging.WARN,logging.INFO])
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        ch.setLevel(level)
        logger.addHandler(ch)
    else:
        level = logging.NOTSET
    if level==logging.DEBUG:
        logger.debug("Going to be very noisy! :-) Screen output is same as log file content. Log file is {}".format(logfilename))
    elif level==logging.INFO:
        logger.info("Only the INFO level log messages will be printed to the screen. " +
                    "For full DEBUG level details see the logfile. Log file is {}".format(logfilename))
    elif level==logging.WARN or level==logging.ERROR:
        logger.warn("Going to be very quiet, only warnings and errors will be printed to the screen. " +
                    "For full DEBUG level details see the logfile. Log file is {}".format(logfilename))
    else:
        logger.info("This logging message should only appear in the log file, not on screen (daemon mode)")
    return logger, logfilename

# vim: set et softtabstop=4 sw=4 smartindent:
def get_logging_n(syscfg,want_logfile="default", jobId = ''):
    if not jobId:
        jobId = timestamp()
    if not bool(want_logfile):
        logging.basicConfig(level=syscfg['default logging level'])
        logger = logging.getLogger(__name__)
        return
    msg=""
    try:
        # try to get the logging directory before anything else
        logdir=syscfg["logdir"]
        if not os.path.isdir(logdir):
            raise IOError(f"logging dir '{logdir}' is not an existing directory?")
        msg = f"got logdir={logdir} from system config file"
        # TODO: maybe we should also check here that we can actually write something to this directory
    except Exception as e:
        msg = f"WARNING: failed to get a valid log directory from your system configuration: '{e}'."
        logdir='/tmp'
    if os.path.isabs(want_logfile):
        logger,logfilepath = get_dual_logging( level  = syscfg['default logging level'],
                                               daemon_file = want_logfile )
    else:
        logger,logfilepath = get_dual_logging( level  = syscfg['default logging level'],
                                               prefix = '', jobId = jobId, logDir = logdir)
    #syscfg["log file path"]=logfilepath
    if logdir == '/tmp':
        logger.warn(msg)
    else:
        logger.debug(msg)
        
    return logger

def create_logger(loggerName, filepath):
    logger = logging.getLogger(loggerName)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s')
    fh = logging.FileHandler(filepath)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger
        

def get_high_level_logfile():
    this_cmd = os.path.abspath(__file__)
    impl_dir = os.path.dirname(this_cmd)
    ideal_dir = os.path.dirname(impl_dir)
    install_dir = os.path.dirname(ideal_dir)
    cfg = configparser.ConfigParser()

    cfg.read(os.path.join(install_dir,'cfg/log_daemon.cfg'))
    logfilename= cfg['Paths']['global logfile']
    # Get file handler to high level log file
    formatter = logging.Formatter('%(message)s')
    handler = logging.FileHandler(logfilename)        
    handler.setFormatter(formatter)

    logger = logging.getLogger("high_log")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    return logger

def get_last_log_ID():
    this_cmd = os.path.abspath(__file__)
    impl_dir = os.path.dirname(this_cmd)
    ideal_dir = os.path.dirname(impl_dir)
    install_dir = os.path.dirname(ideal_dir)
    cfg = configparser.ConfigParser()

    cfg.read(os.path.join(install_dir,'cfg/log_daemon.cfg'))
    logfilename= cfg['Paths']['global logfile']
    with open(logfilename,'r') as f:
        lines = f.readlines()
        ID_lines = [l for l in lines if "IdealID:" in l.split(" ")]
        if len(ID_lines)>0:
            ID = int(ID_lines[-1].split(" ")[1])
        else: ID = 0

        return ID 
    
    
