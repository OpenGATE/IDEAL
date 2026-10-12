#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 12 10:58:11 2026

@author: fava
"""

import utils.api_utils as ap

if __name__ == "__main__":
    commissioning_dir = '/opt/share/IDEAL-2_0/data/MedAustronCommissioningData'
    sysconfig_path = '/opt/share/IDEAL-2_0/cfg/system.cfg'
    checksum = ap.sha1_directory_checksum(commissioning_dir, sysconfig_path)
    print(checksum)
