from StructureTools import get_distance_from_plane, check_distances_from_plane
from Classes_Pymatgen import *
from pymatgen.analysis.defects.generators import InterstitialGenerator
from Vis import view, open_in_VESTA
from get_migration import get_interstitial_diffusion_pathways_from_cell, get_unique_diffusion_pathways, get_center_i, get_supercell_site, get_supercell_for_diffusion, get_supercell_and_path_interstitial_diffusion
from Helpers import get_smallest_expansion
import os
os.environ['VESTA_DIR']='"C:\\Program Files\\VESTA\\VESTA.exe"'


from pymatgen.core import Structure

temp_file = 'D:\\Users\\RyanTrottier\\Documents\\Scrap\\temp.vasp'
temp_file = False
# temp_file = ''

structure = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR').structure
supercell, paths = get_supercell_and_path_interstitial_diffusion(structure)
# structure = get_smallest_expansion(structure, 7.5)
# _, structure = get_interstitial_diffusion_pathways_from_cell(structure, Element('H'), vis=temp_file, dummy='Li')
# # Poscar(structure).write_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\temp.vasp')
#
# # structure = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\pathways.vasp').structure
# paths = get_unique_diffusion_pathways(structure, Element('Li'), get_center_i(structure, Element('H')))
# supercell, paths = get_supercell_for_diffusion(structure, paths)

print(paths)


