#!/usr/bin/env python
# Removes specified atoms from the run.  Updates INCAR afterwards with values from the cfg.py.
# TODO:  Stop this from messing with the MAGMOM

# Usage: Remove_Atoms.py Previous_Dir [This_Dir] Atom_#s
import sys
from Substitute_Atoms import *
from Helpers import update_incar


if len(sys.argv) < 3:
    raise Exception('Not Enough Arguments Provided\n need: Previous_Dir [This_Dir] Atom_#s')
prev_NEB_dir = sys.argv[1]
try:
    this_NEB_dir = os.getcwd()
    atom_nums = list(map(lambda x: int(x)-1, sys.argv[2:len(sys.argv)]))
except:
    this_NEB_dir = sys.argv[2]
    atom_nums = list(map(lambda x: int(x)-1, sys.argv[3:len(sys.argv)]))
remove_atom_arbitrary(prev_NEB_dir, this_NEB_dir, atom_nums)
