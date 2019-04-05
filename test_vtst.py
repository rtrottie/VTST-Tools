import os
os.environ['PATH'] = 'D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\envs\\pymatgen;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\envs\\pymatgen\\Library\\mingw-w64\\bin;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\envs\\pymatgen\\Library\\usr\\bin;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\envs\\pymatgen\\Library\\bin;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\envs\\pymatgen\\Scripts;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\envs\\pymatgen\\bin;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\Library\\mingw-w64\\bin;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\Library\\usr\\bin;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\Library\\bin;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\Scripts;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\bin;C:\\Program Files (x86)\\Common Files\\Oracle\\Java\\javapath;C:\\ProgramData\\Oracle\\Java\\javapath;C:\\WINDOWS\\system32;C:\\WINDOWS;C:\\WINDOWS\\System32\\Wbem;C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\;D:\\Program Files\\Git\\cmd;C:\\Users\\RyanTrottier\\.dnx\\bin;C:\\Program Files\\Microsoft DNX\\Dnvm\\;C:\\Program Files (x86)\\Windows Kits\\8.1\\Windows Performance Toolkit\\;C:\\Program Files\\Microsoft SQL Server\\130\\Tools\\Binn\\;D:\\Program Files\\MATLAB\\R2018a\\bin;C:\\Program Files (x86)\\Mozilla Firefox;D:\\Program Files\\OpenBabel-2.4.1;C:\\Users\\RyanTrottier\\AppData\\Local\\Microsoft\\WindowsApps;C:\\Users\\RyanTrottier\\AppData\\Local\\Pandoc\\;C:\\Users\\RyanTrottier\\AppData\\Local\\Programs\\MiKTeX 2.9\\miktex\\bin\\x64\\;;D:\\Users\\RyanTrottier\\AppData\\Local\\Continuum\\miniconda3\\envs\\pymatgen\\lib\\site-packages\\numpy\\.libs'

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
# temp_file = False
# temp_file = ''

structure = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR').structure
vis = temp_file
supercell, paths = get_supercell_and_path_interstitial_diffusion(structure, vis=vis)
# structure = get_smallest_expansion(structure, 7.5)
# _, structure = get_interstitial_diffusion_pathways_from_cell(structure, Element('H'), vis=temp_file, dummy='Li')
# # Poscar(structure).write_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\temp.vasp')
#
# # structure = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\pathways.vasp').structure
# paths = get_unique_diffusion_pathways(structure, Element('Li'), get_center_i(structure, Element('H')))
# supercell, paths = get_supercell_for_diffusion(structure, paths)

print(paths)


