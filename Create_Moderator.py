from jinja2 import Environment, FileSystemLoader
from pymatgen.io.vaspio.vasp_input import Incar
import sys
import os

os.chdir('/home/ryan/PycharmProjects')

template_location = ('/home/ryan/PycharmProjects/NEB-Tools')
template = 'Simple_NEB_Moderator.jinja.py'

env = Environment(loader=FileSystemLoader(template_location))
template = env.get_template(template)

if len(sys.argv) <= 1:
    sys.argv.append(2)
if len(sys.argv) <= 2:
    sys.argv.append('NEB_' + os.path.basename(os.getcwd()))
if len(sys.argv) <= 3:
    sys.argv.append(4)
nodes_per_image = sys.argv[1]
jobname = sys.argv[2]
time = sys.argv[3]
incar = Incar.from_file('INCAR')
images = incar['IMAGES']

keywords = {'J' : jobname,
            'hours' : time,
            'nodes' : images*nodes_per_image,
            'nntasks_per_node' : 12,
            'logname' : jobname + '.log'}

with open(keywords['logname']+'.py', 'w+') as f:
    f.write(template.render(keywords))