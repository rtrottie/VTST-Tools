#!/usr/bin/env python
# Switches specified atoms from the run.  Updates INCAR afterwards with values from the cfg.py.  Atoms are switched
# pairwise so when called with 1 2 3 4, 1 and 2 switch, and 3 and 4 switch
# TODO:  Stop this from messing with the MAGMOM

# Usage: Remove_Atoms.py Previous_Dir [This_Dir] Atom_#s

__author__ = 'ryan'
import sys
from Substitute_Atoms import *


if len(sys.argv) < 3:
    raise Exception('Not Enough Arguments Provided\n need: Previous_Dir [This_Dir] Atom_#s')
prev_NEB_dir = sys.argv[1]
try:
    this_NEB_dir = os.getcwd()
    atom_nums = list(map(lambda x: int(x), sys.argv[2:len(sys.argv)]))
except:
    this_NEB_dir = sys.argv[2]
    atom_nums = list(map(lambda x: int(x), sys.argv[3:len(sys.argv)]))
switch_atom_arbitrary(prev_NEB_dir, this_NEB_dir, atom_nums)
