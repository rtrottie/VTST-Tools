import Vis
from Classes_Pymatgen import Structure, Poscar
import pymatgen.core
from math import gcd
from pymatgen.core import Molecule
import Generate_Surface
type = 'cif'

s = Structure.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR')
surf = Generate_Surface.Generate_Surface(s, [0,1,0], 3, 2, 8, vacuum=20,orth=True)[0]
sd = Generate_Surface.get_SD_along_vector(surf, 2, [.33,.8])
Poscar(surf, selective_dynamics=sd).write_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR.surfluarge.vasp')

# surf = surf[3] # pymatgen.core.Structure
# surf = Molecule.from_sites(surf.sites)

# surf = surf.to(type, 'D:\\Users\\RyanTrottier\\Documents\\Scrap\\tmp.'+type)
# surf = Molecule.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\tmp.'+type)

# center_i = 762
# center = surf[center_i] # pymatgen.core.sites.Site
# radius = 10
#
#
#
# for element in surf.symbol_set
#
# sites = [center] + [ x[0] for x in surf.get_neighbors(center, radius)]
# add_sites = surf.get_neighbors_in_shell(center.coords, radius, 2)
# add_sites.sort(key=lambda a: a[1])
#
# mol = Molecule.from_sites(sites)
# mol.to(type, 'D:\\Users\\RyanTrottier\\Documents\\Scrap\\gaus.'+type)
