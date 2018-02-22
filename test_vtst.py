from align_bond_along_a import align_a_to_vector, set_vector_as_boundary
from Classes_Pymatgen import *
from Generate_Surface import Generate_Surface

structure = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR').structure

ss = Generate_Surface(structure, [1,1,0], 1, 1, 8, vacuum=12, cancel_dipole=True, vis='vesta', orth=True)


pass