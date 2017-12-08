from align_bond_along_a import align_a_to_vector, set_vector_as_boundary
from Classes_Pymatgen import *

structure = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR').structure

vector = structure[109].coords - structure[45].coords
new_s = set_vector_as_boundary(structure, vector)
Poscar(new_s).write_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\aligned.vasp')
Poscar(structure).write_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\aligned2.vasp')
pass