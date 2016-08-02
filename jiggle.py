#!/usr/bin/env python

from Classes_Pymatgen import Poscar
from pymatgen.transformations.standard_transformations import PerturbStructureTransformation
import os

try:
    p = Poscar.from_file('CONTCAR')
except:
    p = Poscar.from_file('POSCAR')

s = PerturbStructureTransformation().apply_transformation(p.structure)

Poscar(s).write_file('CONTCAR')