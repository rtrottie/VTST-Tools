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

def GSM_Setup(start, final=None, new_gsm_dir='.', images=None, center=[0.5,0.5,0.5], f_center=None):

    # Initializing Variables to be called later in function

    file_loc = os.environ['GSM_DIR']
    jinja_vars = Helpers.load_variables(os.path.join(file_loc, 'VARS.jinja2'))
    if f_center == None:
        f_center = center
    if images == None:
        if final: #is GSM
            images = 9
            jinja_vars["SM_TYPE"] = 'GSM'
            print('Setting up GSM run')
        else: # is SSM
            images = 40
            jinja_vars["SM_TYPE"] = 'SSM'
            print('Setting up SSM run, make sure to create ISOMERS File at scratch/ISOMERS0000')
    else:
        if final: #is GSM
            jinja_vars["SM_TYPE"] = 'GSM'
            print('Setting up GSM run')
        else: # is SSM
            jinja_vars["SM_TYPE"] = 'SSM'
            print('Setting up SSM run, make sure to create ISOMERS File at scratch/ISOMERS0000')

    jinja_vars["IMAGES"] = images

    # Finding the Starting Structure
    if os.path.isfile(start):
        start_file = start
        start_folder = os.path.dirname(start)
    else:
        start_file = os.path.join(start, 'CONTCAR') if os.path.exists(os.path.join(start, 'CONTCAR')) else os.path.join(start, 'POSCAR')
        start_folder = start

    # Copying and Updating Files into the directory

    if not os.path.exists(new_gsm_dir):
        os.makedirs(new_gsm_dir)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(file_loc))
    shutil.copy(os.path.join(file_loc, 'gfstringq.exe'), os.path.join(new_gsm_dir, 'gfstringq.exe'))
    shutil.copy(os.path.join(file_loc, 'status'), os.path.join(new_gsm_dir, 'status'))
    shutil.copy(start_file, os.path.join(new_gsm_dir, 'POSCAR.start'))
    if not os.path.exists(os.path.join(new_gsm_dir, 'scratch')):
        os.makedirs(os.path.join(new_gsm_dir, 'scratch'))
    try:
        incar = Incar.from_file(os.path.join(start_folder, 'INCAR'))
        incar['NSW']=0
        incar.write_file(os.path.join(new_gsm_dir, 'INCAR'))
    except:
        print('Copying INCAR failed, make sure to add an appropriate INCAR to the directory')
    try:
        shutil.copy(os.path.join(start_folder, 'KPOINTS'), os.path.join(new_gsm_dir, 'KPOINTS'))
    except:
        print('Copying KPOINTS failed, make sure to add an appropriate KPOINTS to the directory')
    try:
        shutil.copy(os.path.join(start_folder, 'POTCAR'), os.path.join(new_gsm_dir, 'POTCAR'))
    except:
        print('Copying POTCAR failed, make sure to add an appropriate POTCAR to the directory')

    if os.path.exists(os.path.join(start_folder, 'WAVECAR')):
        print('Copying initial WAVECAR')
        if not os.path.exists(os.path.join(new_gsm_dir, 'scratch/IMAGE.01')):
            os.makedirs(os.path.join(new_gsm_dir, 'scratch/IMAGE.01'))
        shutil.copy(os.path.join(start_folder, 'WAVECAR'),
                    os.path.join(new_gsm_dir, 'scratch/IMAGE.01/WAVECAR'))
    if os.path.exists(os.path.join(start_folder, 'CHGCAR')):
        print('Copying initial CHGCAR')
        if not os.path.exists(os.path.join(new_gsm_dir, 'scratch/IMAGE.01')):
            os.makedirs(os.path.join(new_gsm_dir, 'scratch/IMAGE.01'))
        shutil.copy(os.path.join(start_folder, 'CHGCAR'),
                    os.path.join(new_gsm_dir, 'scratch/IMAGE.01/CHGCAR'))
    with open('grad.py', 'w') as f:
        template = env.get_template('grad.jinja2.py')
        f.write(template.render(jinja_vars))
    with open('inpfileq', 'w') as f:
        template = env.get_template('inpfileq.jinja2')
        f.write(template.render(jinja_vars))

    start = ase.io.read(start_file)
    start.wrap(center)
    initial = [start]

    if final: # is GSM
        if os.path.isfile(final):
            final_file = final
            final_folder = os.path.dirname(final)
        else:
            final_file = os.path.join(final, 'CONTCAR') if os.path.exists(os.path.join(final, 'CONTCAR')) else os.path.join(final, 'POSCAR')
            final_folder = final
        shutil.copy(final_file, os.path.join(new_gsm_dir, 'POSCAR.final'))
        if os.path.exists(os.path.join(final_folder, 'WAVECAR')):
            print('Copying final WAVECAR')
            if not os.path.exists(os.path.join(new_gsm_dir, 'scratch/IMAGE.' + str(images).zfill(2))):
                os.makedirs(os.path.join(new_gsm_dir, 'scratch/IMAGE.' + str(images).zfill(2)))
            shutil.copy(os.path.join(final_folder, 'WAVECAR'),
                        os.path.join(new_gsm_dir, 'scratch/IMAGE.' + str(images).zfill(2) + '/WAVECAR'))
        if os.path.exists(os.path.join(final_folder, 'CHGCAR')):
            print('Copying final CHGCAR')
            if not os.path.exists(os.path.join(new_gsm_dir, 'scratch/IMAGE.' + str(images).zfill(2))):
                os.makedirs(os.path.join(new_gsm_dir, 'scratch/IMAGE.' + str(images).zfill(2)))
            shutil.copy(os.path.join(final_folder, 'CHGCAR'),
                        os.path.join(new_gsm_dir, 'scratch/IMAGE.' + str(images).zfill(2) + '/CHGCAR'))

        final = ase.io.read(final_file)
        final.wrap(f_center)
        initial.append(final)
    os.chdir(new_gsm_dir)
    os.chmod('grad.py', 0o755)
    os.chmod('status', 0o755)
    ase.io.write('scratch/initial0000.temp.xyz', initial)
    poscar = Poscar.from_file('POSCAR.start')
    if poscar.selective_dynamics:
        with open('scratch/initial0000.temp.xyz', 'r') as f:
            sd = Poscar.from_file('POSCAR.start').selective_dynamics
            sd = map(lambda l : '\n' if (l[0] or l[1] or l[2]) else ' "X"\n', sd)
            to_zip = (['\n', '\n'] + sd) * len(initial)
            zipped = zip(f.readlines(), to_zip)
            xyz = map(lambda (x,y) : x.rstrip()+y, zipped)
            with open('scratch/initial0000.xyz', 'w') as f:
                f.writelines(xyz)
        os.remove('scratch/initial0000.temp.xyz')
    else:
        shutil.move('scratch/initial0000.temp.xyz', 'scratch/initial0000.xyz')





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('initial', help='structure file or VASP run folder for initial structure (required for SSM and GSM)')
    parser.add_argument('final', help='structure file or VASP run folder for final structure (GSM only)',
                        default=None, nargs='?')
    parser.add_argument('-d', '--directory', help='directory to put GSM run in (Defaults to "." )',
                        default='.')
    parser.add_argument('-t', '--type', help='type of run to initialize (currently done based on whether final is provided, so this is not used)',
                        choices=['gsm', 'ssm', 'fsm'], default='gsm')
    parser.add_argument('-n', '--nodes', help='number of nodes along string (defaults : 9 for GSM 40 for SSM)',
                        type=int)
    parser.add_argument('-c', '--center', help='center of cell in fractional coordinates to account for non-periodic boundary conditions',
                        nargs=3, type=float, default=[0.5,0.5,0.5])
    parser.add_argument('-f', '--finalcenter', help='center of final cell in fractional coordinates (defaults to center)',
                        nargs=3, type=float, default=None)
    args = parser.parse_args()

    GSM_Setup(args.initial, args.final, args.directory, args.nodes, args.center, args.finalcenter)
