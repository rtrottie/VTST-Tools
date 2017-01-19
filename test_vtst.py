import os
import Vis
from Classes_Pymatgen import Poscar
import Neb_Make

print(os.environ['VESTA_DIR'])

s1 = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR.start').structure
s2 = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR.final').structure

poscar_override = [49, 48, 48, 49, 113, 102]
if poscar_override:
    atoms = []
    for i in range(int(len(poscar_override) / 2)):
        atoms.append((poscar_override[i * 2], poscar_override[i * 2 + 1]))

Neb_Make.reorganize_structures(s1, s2, poscar_override)