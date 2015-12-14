#!/usr/bin/env python

import os
import sys
import Helpers
import shutil
import jinja2
import ase.io
from ase.utils.geometry import wrap_positions
from Classes_Pymatgen import *

def wrap_positions_right(positions, center, cell):
    new_pos = []
    x=0; y=0; z=0
    for i in range(len(positions)):
        if abs(positions[i] - center[i] ) > 0.5:
            if positions[i] < center[i]:
                scale = positions[i] + 1
            else:
                scale = positions[i] - 1
        else:
            scale = positions[i]
        x += cell[i][0] * scale
        y += cell[i][1] * scale
        z += cell[i][2] * scale

    return (x,y,z)

def GSM_Setup():

    file_loc = os.environ['GSM_DIR']
    jinja_vars = Helpers.load_variables(os.path.join(file_loc, 'VARS.jinja2'))


    if len(sys.argv) == 1:
        start = 'start'
        final = 'final'
    elif len(sys.argv) == 2:
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



    if not os.path.isfile(start):
        start_pos = os.path.join(start, 'CONTCAR') if os.path.exists(os.path.join(start, 'CONTCAR')) else os.path.join(start, 'POSCAR')
    else:
        start_pos = start
        start = os.path.dirname(start)
    if not os.path.isfile(final):
        final_pos = os.path.join(final, 'CONTCAR') if os.path.exists(os.path.join(final, 'CONTCAR')) else os.path.join(final, 'POSCAR')
    else:
        final_pos = final
        final = os.path.dirname(final)
    images = int(jinja_vars['IMAGES'])


    if not os.path.exists('scratch'):
        os.makedirs('scratch')

    shutil.copy(os.path.join(file_loc, 'gfstringq.exe'), 'gfstringq.exe')
    shutil.copy(os.path.join(file_loc, 'status'), 'status')
    shutil.copy(start_pos, 'POSCAR.start')
    shutil.copy(final_pos, 'POSCAR.final')
    incar = Incar.from_file(os.path.join(start, 'INCAR'))
    incar['NSW']=0
    incar['NELM'] = 100
    incar.write_file('INCAR')
    shutil.copy(os.path.join(start, 'KPOINTS'), 'KPOINTS')
    shutil.copy(os.path.join(start, 'POTCAR'), 'POTCAR')
    if os.path.exists(os.path.join(start, 'WAVECAR')):
        os.makedirs('scratch/IMAGE.01')
        shutil.copy(os.path.join(start, 'WAVECAR'), 'scratch/IMAGE.01/WAVECAR')
    if os.path.exists(os.path.join(final, 'WAVECAR')):
        os.makedirs('scratch/IMAGE.' + str(images-1).zfill(2))
        shutil.copy(os.path.join(final, 'WAVECAR'), 'scratch/IMAGE.' + str(images-1).zfill(2) + '/WAVECAR')

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
    final_positions = []
    for i in range(len(final)):
        pos = [final[i].a, final[i].b, final[i].c]
        center = [start[i].a, start[i].b, start[i].c]
        final_positions.append(wrap_positions_right(pos, center, start.cell))
    final.set_positions(final_positions)
    ase.io.write('scratch/initial0000.temp.xyz',[start,final])
    with open('scratch/initial0000.temp.xyz', 'r') as f:
        sd = Poscar.from_file('POSCAR.start').selective_dynamics
        sd = map(lambda l : '\n' if (l[0] or l[1] or l[2]) else ' "X"\n', sd)
        to_zip = ['\n', '\n'] + sd + ['\n', '\n'] + sd
        zipped = zip(f.readlines(), to_zip)
        xyz = map(lambda (x,y) : x.rstrip()+y, zipped)
        with open('scratch/initial0000.xyz', 'w') as f:
            f.writelines(xyz)
    os.remove('scratch/initial0000.temp.xyz')

if os.path.basename(sys.argv[0]) == 'GSM_Setup.py':
    GSM_Setup()