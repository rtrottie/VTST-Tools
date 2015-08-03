#!/usr/bin/env python
import os
import cfg
import shutil
import sys
from Classes_Pymatgen import *

def check_dimer(directory):
    os.chdir(directory)
    os.system(os.path.join(cfg.VTST_DIR, 'dimmins.pl'))
    for m in ['min1', 'min2']:
        dir = os.path.join(directory, 'mins', m)
        shutil.copy(os.path.join(directory, 'WAVECAR'), dir)
        incar = Incar.from_file(os.path.join(dir,'INCAR'))
        incar['EDIFFG'] = -5e-2
        incar.pop('ICHAIN')
        incar['IOPT'] = 7
        incar.write_file(os.path.join(dir,'INCAR'))
        os.system('VTST_Custodian.py')

if os.path.basename(sys.argv[0]) == 'Dim_check.py':
    check_dimer(os.curdir())