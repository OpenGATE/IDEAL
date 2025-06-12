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
import opengate as gate
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

def write_hu2mat_txt(voxel_materials,file_path):
    with open(file_path,'w') as f:
        for v in voxel_materials:
            for e in v:
                f.write(f'{e} ')
            f.write('\n')

def generate_hlut_cache(density,composition,HUtol,db=None):
    syscfg = system_configuration.getInstance()
    tstart=datetime.now()
    cache_dir = hlut_cache_dir(density,composition,HUtol,create=True)
    if db is None:
        materialsdb = os.path.join(syscfg['commissioning'],syscfg['materials database'])
    else:
        materialsdb = db
    humatdb = os.path.join(cache_dir,'patient-HUmaterials.db')
    hu2mattxt = os.path.join(cache_dir,'patient-HU2mat.txt')
    gcm3 = gate.g4_units.g_cm3
    sim = gate.Simulation()
    sim.volume_manager.add_material_database(materialsdb)
    voxel_materials, created_materials = gate.geometry.materials.HounsfieldUnit_to_material(sim, HUtol*gcm3, composition, density)
    gate.geometry.materials.write_material_database(sim, created_materials, humatdb)
    write_hu2mat_txt(voxel_materials,hu2mattxt)
    
    logger.info("generating cache for {} and {} with density tolerance {} g/cm3".format(density,composition,HUtol))
    logger.info("cache dir: {}".format(cache_dir))
    tend=datetime.now()
    dbl_chk = os.path.exists(humatdb) and os.path.exists(hu2mattxt)
    logger.info("job took {} seconds, new HLUT cache files {} exist.".format((tend-tstart).total_seconds(),("DO" if dbl_chk else "DO NOT")))
    success = dbl_chk
    return success, cache_dir

# vim: set et softtabstop=4 sw=4 smartindent:
