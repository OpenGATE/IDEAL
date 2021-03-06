# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import time
import logging

def timestamp():
    return time.strftime("%Y_%m_%d_%H_%M_%S")

def get_dual_logging(verbose=False,quiet=False,level=None,prefix="logfile",daemon_file=None):
    """
    Configure logging such that all log messages go both to
    a file and to stdout, filtered with different log levels.
    """

    #logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s')

    # create file handler which logs even debug messages
    if daemon_file:
        logfilename = daemon_file
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
