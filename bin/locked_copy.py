#!/usr/bin/env python3
# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import argparse
import os, shutil
from filelock import Timeout, SoftFileLock
from datetime import datetime


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("files", help="File(s) to copy to the destination directory.",nargs='*')
    parser.add_argument("-l","--lockfile", required=True, help="Lock file path.")
    parser.add_argument("-v","--verbose", default=False, action='store_true', help="Be verbose.")
    parser.add_argument("-d","--destdir", required=True, help="Destination directory.")
    args = parser.parse_args()
    for f in args.files:
        if not os.path.exists(f):
            raise RuntimeError("input file {} does not exist".format(f))
    if not os.path.isdir(args.destdir):
        raise RuntimeError("destination directory {} does not exist".format(args.destdir))
    lock = SoftFileLock(args.lockfile)
    if args.verbose:
        print("lockfile exists" if os.path.exists(args.lockfile) else "lockfile does not exist")
    t0=datetime.now()
    try:
        # TODO: the length of the timeout should maybe be configured in the system configuration
        with lock.acquire(timeout=3):
            t1=datetime.now()
            if args.verbose:
                print("acquiring lock file took {} seconds".format((t1-t0).total_seconds()))
            for f in args.files:
                shutil.copy(f,args.destdir)
            t2=datetime.now()
            if args.verbose:
                print("copying {} files took {} seconds".format(len(args.files),(t2-t1).total_seconds()))
    except Timeout:
        print("failed to acquire lock file {} for 3 seconds, giving up for now".format(args.lockfile))

# vim: set et softtabstop=4 sw=4 smartindent:
