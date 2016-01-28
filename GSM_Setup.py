#!/usr/bin/env python

import os
import sys
import Helpers
import shutil
import jinja2
import ase.io
from ase.utils.geometry import wrap_positions
from Classes_Pymatgen import *
import argparse

def wrap_positions_right(positions, center, cell):
    scale = [1,1,1]
    x=0; y=0; z=0
    for i in range(len(positions)):
        if abs(center[i] - positions[i]) > 0.5:
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

def GSM_Setup(start, final=None, images=None, center=[0.5,0.5,0.5], f_center=None):

    file_loc = os.environ['GSM_DIR']
    jinja_vars = Helpers.load_variables(os.path.join(file_loc, 'VARS.jinja2'))
    if f_center == None:
        f_center = center
    if images == None:
        if final: #is GSM
            images = 9
        else: # is SSM
            images = 40

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

    if not os.path.exists('scratch'):
        os.makedirs('scratch')

    shutil.copy(os.path.join(file_loc, 'gfstringq.exe'), 'gfstringq.exe')
    shutil.copy(os.path.join(file_loc, 'status'), 'status')
    shutil.copy(start_pos, 'POSCAR.start')
    shutil.copy(final_pos, 'POSCAR.final')
    incar = Incar.from_file(os.path.join(start, 'INCAR'))
    incar['NSW']=0
    incar.write_file('INCAR')
    try:
        shutil.copy(os.path.join(start, 'KPOINTS'), 'KPOINTS')
        shutil.copy(os.path.join(start, 'POTCAR'), 'POTCAR')
    except:
        pass
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
    os.chmod('status', 0o755)
    start = ase.io.read(start_pos)
    final = ase.io.read(final_pos)
    if center:
        start.wrap(center)
        final.wrap(center)
    ase.io.write('scratch/initial0000.temp.xyz',[start,final])
    poscar = Poscar.from_file('POSCAR.start')
    if poscar.selective_dynamics:
        with open('scratch/initial0000.temp.xyz', 'r') as f:
            sd = Poscar.from_file('POSCAR.start').selective_dynamics
            sd = map(lambda l : '\n' if (l[0] or l[1] or l[2]) else ' "X"\n', sd)
            to_zip = ['\n', '\n'] + sd + ['\n', '\n'] + sd
            zipped = zip(f.readlines(), to_zip)
            xyz = map(lambda (x,y) : x.rstrip()+y, zipped)
            with open('scratch/initial0000.xyz', 'w') as f:
                f.writelines(xyz)
        os.remove('scratch/initial0000.temp.xyz')
    else:
        shutil.move('scratch/initial0000.temp.xyz', 'scratch/initial0000.xyz')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('initial', help='structure file or VASP run folder for initial structure')
    parser.add_argument('final', help='structure file or VASP run folder for final structure (GSM only)',
                        default=None, nargs='?')
    parser.add_argument('-t', '--type', help='type of run to initialize (currently done based on whether final is provided, so this is not used)',
                        choices=['gsm', 'ssm', 'fsm'], default='gsm')
    parser.add_argument('-n', '--nodes', help='number of nodes along string (defaults : 9 for GSM 40 for SSM)',
                        type=int)
    parser.add_argument('-c', '--center', help='center of cell in fractional coordinates to account for non-periodic boundary conditions',
                        nargs=3, type=float)
    parser.add_argument('-f', '--finalcenter', help='center of final cell in fractional coordinates (defaults to center)',
                        nargs=3, type=float)
    args = parser.parse_args()