

import Vis
from Classes_Pymatgen import *
import Generate_Surface

print(os.environ['VESTA_DIR'])
s = Structure.from_file('D:\\Users\\RyanTrottier\\Downloads\\Al2FeO4_mvc-16241_computed.cif')

surf = Generate_Surface.Generate_Surface(s, [1,1,1], 10, 10, 10, vacuum=20,vis=True)
