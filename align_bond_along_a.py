from Classes_Pymatgen import *
from pymatgen.core.operations import *
import numpy as np

def align_c_to_vector(s : Structure, vector):
    p = Poscar.from_file('POSCAR')
    s = p.structure # type: Structure

    a = s.lattice[0]
    b = s.lattice[1]
    c = s.lattice[2]

