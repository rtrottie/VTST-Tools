import os
import Vis
from Classes_Pymatgen import Poscar

print(os.environ['VESTA_DIR'])


p = Poscar.from_file('D://Users/RyanTrottier/Documents/Scrap/POSCAR')
print(p)
Vis.open_in_Jmol(p)