#!/usr/bin/env python
# Removes specified atoms from the run.  Updates INCAR afterwards with values from the cfg.py.
# TODO:  Stop this from messing with the MAGMOM

# Usage: Remove_Atoms.py Previous_Dir [This_Dir] [Atom] Atom_#s
import sys
from Substitute_Atoms import *
from Helpers import update_incar

if len(sys.argv) < 3:
    raise Exception('Not Enough Arguments Provided\n need: Previous_Dir [This_Dir] [Atom] Atom_#s')
prev_NEB_dir = sys.argv[1]
try:
    this_NEB_dir = os.getcwd()
    atom_nums = list(map(lambda x: int(x)-1, sys.argv[2:len(sys.argv)]))
    atom = None
except:
    if os.path.isdir(sys.argv[2]):
        this_NEB_dir = sys.argv[2]
        atom = None
        try:
            atom_nums = list(map(lambda x: int(x)-1, sys.argv[3:len(sys.argv)]))
            atom = None
        except:
            atom = sys.argv[3]
            atom_nums = list(map(lambda x: int(x)-1, sys.argv[4:len(sys.argv)]))
    else:
        this_NEB_dir = os.getcwd()
        atom_nums = list(map(lambda x: int(x)-1, sys.argv[3:len(sys.argv)]))
        atom = sys.argv[2]
remove_atom_arbitrary(prev_NEB_dir, this_NEB_dir, atom_nums,atom)
