# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import time
import logging
import logging.handlers
import structlog
import os
import configparser
from filelock import Timeout, SoftFileLock

def timestamp():
    return time.strftime("%Y_%m_%d_%H_%M_%S")

# Root logging configuration to use when running with API
def configure_api_logging(logfile_path: str,level='INFO'):
    
    logger = logging.getLogger('api_logger')
    # set level for the file log. Console will be by default INFO
    level = logging.getLevelName(level)
    # Create a TimedRotatingFileHandler for structured logs
    file_handler = logging.handlers.TimedRotatingFileHandler(
        logfile_path,
        when="midnight",
        interval=1,
        backupCount=7,  # Keep logs for the last 7 days
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.name = 'api_logger'

    # Use a JSON format for file logs
    file_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=[
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,            # Add log level to the logs
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
            ],
        )
    )

    # Create a console handler for human-readable logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(),  # Human-readable
            foreign_pre_chain=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
            ],
        )
    )

    # Configure logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    #logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
    
    return logger
    
# Logging configuration for the single simulation instances
def configure_simulation_logging(logfile_path=None,level=logging.DEBUG,console_output = True):
    """
    Configure logging such that all log messages go both to
    a file and to stdout, filtered with different log levels.
    """

    logger = logging.getLogger()
    logger.handlers.clear()
    
    # # reset file handler
    # for handler in logger.handlers:
    #     # avoid removing the api file handler, if present
    #     if getattr(handler, "name", None) != 'api_logger':
    #         logger.removeHandler(handler)
            
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s')
       
    # add file handler, with the desired lof level 
    if logfile_path is not None:    
        fh = logging.FileHandler(logfile_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # create console handler with a higher log level
    if console_output:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        ch.setLevel(level)
        logger.addHandler(ch)

    if level==logging.DEBUG:
        logger.debug("Going to be very noisy! :-) Screen output is same as log file content. Log file is {}".format(logfile_path))
    elif level==logging.INFO:
        logger.info("Only the INFO level log messages will be printed to the screen. " +
                    "For full DEBUG level details see the logfile. Log file is {}".format(logfile_path))
    elif level==logging.WARN or level==logging.ERROR:
        logger.warn("Going to be very quiet, only warnings and errors will be printed to the screen. " +
                    "For full DEBUG level details see the logfile. Log file is {}".format(logfile_path))
    else:
        logger.info("This logging message should only appear in the log file, not on screen (daemon mode)")
        
    return logger

def update_logging_config(syscfg, jobId=None, logdir=None, level = None):
    # get the user's set type of logging output
    want_logfile =syscfg['want_logfile'].lower()
    console_output = False if want_logfile == 'yes' else True
    # if no logfile is desired, there is no update to do to the log system
    if want_logfile == 'no':
        logging.basicConfig(level=syscfg['default logging level'])
        logger = logging.getLogger(__name__)
        return
    
    # if the user doesn't provide a log directory, use the configured one
    if not logdir:
        logdir=syscfg["logdir"]
    else: 
        if not os.path.isdir(logdir):
            raise IOError(f"logging dir '{logdir}' is not an existing directory?")
    
    # if no logfile name was provided, just use the timestamp
    if not jobId:
        jobId = timestamp()
    logfilename="{}.log".format(jobId)
    logfile_path = os.path.join(logdir, logfilename)
    
    if not level:
        level = syscfg["default logging level"]
        
    logger = configure_simulation_logging(logfile_path=logfile_path,level=level,console_output = console_output)
    
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
    lockfile = logfilename + '.lock'
    lock = SoftFileLock(lockfile)
    try:
        # TODO: the length of the timeout should maybe be configured in the system configuration
        with lock.acquire(timeout=3):
            formatter = logging.Formatter('%(message)s')
            handler = logging.FileHandler(logfilename)        
            handler.setFormatter(formatter)

            logger = logging.getLogger("high_log")
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)
            logger.propagate = False  # don't propagate messages to the root logger's handlers
    except Timeout:
        print("failed to acquire lock file {} for 3 seconds".format(lockfile))
    
    return logger

def get_last_log_ID():
    this_cmd = os.path.abspath(__file__)
    impl_dir = os.path.dirname(this_cmd)
    ideal_dir = os.path.dirname(impl_dir)
    install_dir = os.path.dirname(ideal_dir)
    cfg = configparser.ConfigParser()

    cfg.read(os.path.join(install_dir,'cfg/log_daemon.cfg'))
    logfilename= cfg['Paths']['global logfile']
    
    lockfile = logfilename + '.lock'
    lock = SoftFileLock(lockfile)
    try:
        with lock.acquire(timeout=3):
            with open(logfilename,'r') as f:
                lines = f.readlines()
                ID_lines = [l for l in lines if "IdealID:" in l.split(" ")]
                if len(ID_lines)>0:
                    ID = int(ID_lines[-1].split(" ")[1])
                else: ID = 0
    except Timeout:
        print("failed to acquire lock file {} for 3 seconds".format(lockfile))
        
    return ID 
    
    
    