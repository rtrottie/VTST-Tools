#!/usr/bin/env python
# Starts a run that won't move ions.  Sets NSW to 0 and raises NELM to 1000 to allow even difficult surfaces to converge
# and sets EDIFF = 1e-5. Does this only for the current directory

# Usage: No_Relax.py

from Classes_Pymatgen import *
import sys

def no_relax(directory, runP=True):
    incar = Incar.from_file('INCAR')
    incar['NSW'] = 0
    incar['NELM'] = 1000
    incar['EDIFF'] = 1e-5
    if 'ICHAIN' in incar:
        incar.pop('ICHAIN')
    incar.write_file('INCAR')
    if runP:
        os.system('VTST_Custodian.py ' + reduce(lambda x,y: str(x)+' '+str(y), sys.argv[1:], ''))


if os.path.basename(sys.argv[0]) == 'No_Relax.py':
    no_relax(os.path.abspath(os.curdir))