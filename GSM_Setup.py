#!/usr/bin/env python

import os
import sys
import Helpers
import shutil
import jinja2
import ase.io
from Classes_Pymatgen import *

def GSM_Setup():

    file_loc = os.environ['GSM_DIR']
    jinja_vars = Helpers.load_variables(os.path.join(file_loc, 'VARS.jinja2'))


    if len(sys.argv) == 2:
        jinja_vars['IMAGES'] = sys.argv[1]
        start = 'start'
        final = 'final'
    elif len(sys.argv) == 3:
        start = sys.argv[1]
        final = sys.argv[2]
    elif len(sys.argv) == 4:
        start = sys.argv[1]
        final = sys.argv[2]
        jinja_vars['IMAGES'] = sys.argv[3]




    start_pos = os.path.join(start, 'CONTCAR') if os.path.exists(os.path.join(start, 'CONTCAR')) else os.path.join(start, 'POSCAR')
    final_pos = os.path.join(final, 'CONTCAR') if os.path.exists(os.path.join(final, 'CONTCAR')) else os.path.join(final, 'POSCAR')


    shutil.copy(os.path.join(file_loc, 'gfstringq.exe'), 'gfstringq.exe')
    shutil.copy(os.path.join(file_loc, 'status'), 'status')
    shutil.copy(start_pos, 'start')
    shutil.copy(final_pos, 'final')
    incar = Incar.from_file(os.path.join(start, 'INCAR'))
    incar['NSW']=0
    incar.write_file('INCAR')
    shutil.copy(os.path.join(start, 'KPOINTS'), 'KPOINTS')
    shutil.copy(os.path.join(start, 'POTCAR'), 'POTCAR')

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(file_loc))

    with open('grad.py', 'w') as f:
        template = env.get_template('grad.jinja2.py')
        f.write(template.render(jinja_vars))
    with open('inpfileq', 'w') as f:
        template = env.get_template('inpfileq.jinja2')
        f.write(template.render(jinja_vars))

    os.chmod('grad.py', 0o755)
    start = ase.io.read(start_pos)
    final = ase.io.read(final_pos)
    if not os.path.exists('scratch'):
        os.makedirs('scratch')
    ase.io.write('scratch/initial0000.xyz',[start,final])

if os.path.basename(sys.argv[0]) == 'GSM_Setup.py':
    GSM_Setup()