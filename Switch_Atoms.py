#!/usr/bin/env python
__author__ = 'ryan'
import sys
from Substitute_Atoms import *


if len(sys.argv) < 3:
    raise Exception('Not Enough Arguments Provided\n need: Previous_Dir [This_Dir] Atom_#s New_Atom')
prev_NEB_dir = sys.argv[1]
try:
    this_NEB_dir = os.getcwd()
    atom_nums = list(map(lambda x: int(x), sys.argv[2:len(sys.argv)]))
except:
    this_NEB_dir = sys.argv[2]
    atom_nums = list(map(lambda x: int(x), sys.argv[3:len(sys.argv)]))
switch_atom_arbitrary(prev_NEB_dir, this_NEB_dir, atom_nums)
