#!/usr/bin/env python
from jinja2 import Environment, FileSystemLoader
from pymatgen.io.vaspio.vasp_input import Incar
import sys
import os

template_location = ('/home/rytr1806/NEB-Tools')
template = 'Simple_NEB_Moderator.jinja.py'

env = Environment(loader=FileSystemLoader(template_location))
template = env.get_template(template)

if len(sys.argv) < 2:
    sys.argv.append(2)
if len(sys.argv) < 3:
    sys.argv.append('NEB_' + os.path.basename(os.getcwd()))
if len(sys.argv) < 4:
    sys.argv.append(4)
nodes_per_image = int(sys.argv[1])
jobname = sys.argv[2]
time = int(sys.argv[3])
incar = Incar.from_file('INCAR')
images = int(incar['IMAGES'])

keywords = {'J' : jobname,
            'hours' : time,
            'nodes' : images*nodes_per_image,
            'nntasks_per_node' : 12,
            'logname' : jobname + '.log',
            'tasks' : images*nodes_per_image*12,
            'user' : os.environ['USER']}

with open(keywords['logname']+'.py', 'w+') as f:
    f.write(template.render(keywords))
