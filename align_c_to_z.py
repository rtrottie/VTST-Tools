#!/usr/bin/env python
"""
script to align the arbitrary c vector to the z axis.
"""
from Classes_Pymatgen import *
from pymatgen.core.operations import *
import numpy as np

p = Poscar.from_file('POSCAR')
s = p.structure

a = struc.lattice.matrix[2] / np.linalg.norm(struc.lattice.matrix[2])

b = np.array([0, 0, 1.0])

th = np.arccos(np.dot(a, b))
v = np.cross(a,b)
s = np.linalg.norm(v)
c = np.dot(a,b)

vx = np.matrix([[    0, -v[2],  v[1]],
                [ v[2],     0, -v[0]],
                [-v[1],  v[0],     0]])

R = np.identity(3) + vx + vx*vx*(1-c)/(s*s)

sym = SymmOp.from_rotation_and_translation(R)

struc.apply_operation(sym)

Poscar(struc, selective_dynamics=p.selective_dynamics).write_file('POSCAR')