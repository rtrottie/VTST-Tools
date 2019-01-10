from StructureTools import get_distance_from_plane, check_distances_from_plane
from Classes_Pymatgen import *
from pymatgen.core import Structure
s = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\get_info.vasp').structure

print(check_distances_from_plane(s, len(s)-1, [22,56], exclude_element=[Element('O')]))
print(get_distance_from_plane(s, len(s)-1, 6, 8, 71))
