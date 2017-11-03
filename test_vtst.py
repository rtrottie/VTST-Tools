import Vis
from get_migration import *
type = 'cif'

s = Structure.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR')

get_vacancy_diffusion_pathways_from_cell(s, get_center_i(s, Element('O')), True)