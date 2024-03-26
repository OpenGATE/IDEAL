# -----------------------------------------------------------------------------
#   Copyright (C): MedAustron GmbH, ACMIT Gmbh and Medical University Vienna
#   This software is distributed under the terms
#   of the GNU Lesser General  Public Licence (LGPL)
#   See LICENSE for further details
# -----------------------------------------------------------------------------

import os,stat
import hashlib
import shutil
from datetime import datetime
import logging
from impl.system_configuration import system_configuration
logger=logging.getLogger(__name__)

def hlut_hash(density,composition):
    h4sh = hashlib.md5()
    for f in [density,composition]:
        if not os.path.exists(f):
            raise IOError(f"HLUT file {f} does not exist")
        with open(f,"r") as fh:
            for line in fh:
                h4sh.update(bytes(line,encoding='utf-8'))
    return h4sh.hexdigest()

def hlut_cache_dir(density,composition,HUtol,create=False):
    syscfg = system_configuration.getInstance()
    h4sh = hlut_hash(density,composition)
    cache_dir = os.path.join(syscfg['CT'],'cache',h4sh,str(HUtol))
    if os.path.isdir(cache_dir):
        return cache_dir
    elif create:
        os.makedirs(cache_dir,exist_ok=True)
        # store original density and composition files
        cache_parent = os.path.dirname(cache_dir)
        # copying the input files so that you know to which protocol this cache dir corresponds
        shutil.copy(density,os.path.join(cache_parent,os.path.basename(density)))
        shutil.copy(composition,os.path.join(cache_parent,os.path.basename(composition)))
        return cache_dir
    # TODO: alternatively, throw something...
    return None

def generate_hlut_cache(density,composition,HUtol,db=None):
    syscfg = system_configuration.getInstance()
    cache_dir = hlut_cache_dir(density,composition,HUtol,create=True)
    if db is None:
        materialsdb = os.path.join(syscfg['commissioning'],syscfg['materials database'])
    else:
        materialsdb = db
    hlut_gen_cache_mac = os.path.join(syscfg['config dir'],'hlut_gen_cache.mac')
    humatdb = os.path.join(cache_dir,'patient-HUmaterials.db')
    hu2mattxt = os.path.join(cache_dir,'patient-HU2mat.txt')
    adict = dict([("MATERIALS_DB",              materialsdb),
                  ("SCHNEIDER_COMPOSITION_FILE",composition),
                  ("SCHNEIDER_DENSITY_FILE",    density),
                  ("DENSITY_TOLERANCE",         HUtol),
                  ("MATERIALS_INTERPOLATED",    humatdb),
                  ("HU2MAT_TABLE",              hu2mattxt)])
    aliases = "".join(["[{},{}]".format(name,val) for name,val in adict.items()])
    gensh = os.path.join("/tmp","hlut_gen_cache.sh")
    tstart = datetime.now()
    gate_log = os.path.join(syscfg['logging'],tstart.strftime("hlut_gen_cache_%y_%m_%d_%H_%M_%S.log"))
    with open(gensh,"w") as gensh_fh:
        gensh_fh.write("#!/usr/bin/env bash\n")
        gensh_fh.write("set -e\n")
        gensh_fh.write("set -x\n")
        #gensh_fh.write("source {}\n".format(syscfg['gate_env.sh']))
        gensh_fh.write("time Gate -a{} {} >& {}\n".format(aliases,hlut_gen_cache_mac,gate_log))
    os.chmod(gensh,stat.S_IREAD|stat.S_IRWXU)
    logger.info("generating cache for {} and {} with density tolerance {} g/cm3".format(density,composition,HUtol))
    logger.info("cache dir: {}".format(cache_dir))
    #ret=os.system( gensh + " >& " + gate_log )
    ret=os.system( gensh )
    tend=datetime.now()
    dbl_chk = os.path.exists(humatdb) and os.path.exists(hu2mattxt)
    logger.info("return code: {}, job took {} seconds, new HLUT cache files {} exist.".format(ret,(tend-tstart).total_seconds(),("DO" if dbl_chk else "DO NOT")))
    logger.info("logs are in: {}".format(gate_log))
    success = (ret==0) and dbl_chk
    return success, cache_dir

# vim: set et softtabstop=4 sw=4 smartindent:
