#!/usr/bin/env python
from Classes_Pymatgen import *
import sys

def no_relax(directory, runP=True):
    incar = Incar.from_file('INCAR')
    incar['NSW'] = 0
    incar['NELM'] = 1000
    if 'ICHAIN' in incar:
        incar.pop('ICHAIN')
    incar.write_file('INCAR')
    if runP:
        os.system('VTST_Custodian.py')


if os.path.basename(sys.argv[0]) == 'No_Relax.py':
    no_relax(os.path.abspath(os.curdir))