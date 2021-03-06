#!/usr/bin/env python

from Generate_Surface import get_SD_along_vector
from Classes_Pymatgen import Poscar
from pymatgen.core import Structure
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('lower_bound', help='vector to begin freezing at',
                    default=None, type=float)
parser.add_argument('upper_bound', help='vector to end freezing at',
                    default=None, type=float)
parser.add_argument('--vector', help='Vector to Freeze along (default = 2)',
                    default=2, type=int)
parser.add_argument('--input', help='file to read (default = CONTCAR)',
                    default='CONTCAR', type=str)
parser.add_argument('--output', help='file to write (default = CONTCAR.sd)',
                    default='CONTCAR.sd', type=str)
args = parser.parse_args()

lb = args.lower_bound
ub = args.upper_bound
v = args.vector

s = Structure.from_file(args.input)
sd = get_SD_along_vector(s, v, [lb, ub])
Poscar(s, selective_dynamics=sd).write_file(args.output)