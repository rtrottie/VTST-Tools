from StructureTools import get_distance_from_plane, check_distances_from_plane
from Classes_Pymatgen import *
from pymatgen.analysis.defects.generators import InterstitialGenerator
from Vis import view, open_in_VESTA
from get_migration import get_interstitial_diffusion_pathways_from_cell


from pymatgen.core import Structure
s = Poscar.from_file('/scratch/rtrottie/vasp/h-diffusion/testing/CONTCAR').structure

temp_file = 'D:\\Users\\RyanTrottier\\Documents\\Scrap\\temp.vasp'
temp_file = 'testing.vasp'
get_interstitial_diffusion_pathways_from_cell(s, Element('H'), vis=temp_file, dummy='Li')

