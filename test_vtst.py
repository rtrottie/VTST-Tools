from StructureTools import get_distance_from_plane, check_distances_from_plane
from Classes_Pymatgen import *
from pymatgen.analysis.defects.generators import InterstitialGenerator
from Vis import view, open_in_VESTA
from get_migration import get_interstitial_diffusion_pathways_from_cell, get_unique_diffusion_pathways, get_center_i
from Helpers import get_smallest_expansion


from pymatgen.core import Structure

temp_file = 'D:\\Users\\RyanTrottier\\Documents\\Scrap\\temp.vasp'
# temp_file = ''

structure = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR').structure
# structure = get_smallest_expansion(structure, 7.5)
structure = get_interstitial_diffusion_pathways_from_cell(structure, Element('H'), vis=temp_file, dummy='Li')
Poscar(structure).write_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\temp.vasp')

# structure = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\pathways.vasp').structure
paths = get_unique_diffusion_pathways(structure, Element('Li'), get_center_i(structure, Element('H')))

print(paths)


