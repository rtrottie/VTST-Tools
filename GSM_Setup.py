#!/usr/bin/env python

import os
import sys
import Helpers
import shutil
import jinja2
import ase.io
import tempfile
from ase.utils.geometry import wrap_positions
from Classes_Pymatgen import *
from Neb_Make import reorganize_structures
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

def GSM_Setup(start, final=None, new_gsm_dir='.', images=None, center=[0.5,0.5,0.5], f_center=None,
              copy_wavefunction=False, tolerance=None, poscar_override=[], name=None, is_neb=True,
              fix_positions=True):

    # Initializing Variables to be called later in function

    file_loc = os.environ['GSM_DIR']
    jinja_vars = Helpers.load_variables(os.path.join(file_loc, 'VARS.jinja2'))
    if f_center == None:
        f_center = center
    if images == None:
        if final or is_neb: #is GSM
            images = 9
            jinja_vars["SM_TYPE"] = 'GSM'
            print('Setting up GSM run')
        else: # is SSM
            images = 40
            jinja_vars["SM_TYPE"] = 'SSM'
            print('Setting up SSM run, make sure to create ISOMERS File at scratch/ISOMERS0000')
    else:
        if final or is_neb: #is GSM
            jinja_vars["SM_TYPE"] = 'GSM'
            print('Setting up GSM run')
        else: # is SSM
            jinja_vars["SM_TYPE"] = 'SSM'
            print('Setting up SSM run, make sure to create ISOMERS File at scratch/ISOMERS0000')

    jinja_vars["IMAGES"] = images

    # Finding the Starting Structure
    if is_neb:
        start_file = os.path.join(start, '00', 'POSCAR')
        start_folder = os.path.join(start)
    elif os.path.isfile(start):
        start_file = start
        start_folder = os.path.dirname(start)
    else:
        start_file = os.path.join(start, 'CONTCAR') if os.path.exists(os.path.join(start, 'CONTCAR')) else os.path.join(start, 'POSCAR')
        start_folder = start

    # Copying and Updating Files into the directory

    if not os.path.exists(new_gsm_dir):
        os.makedirs(new_gsm_dir)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(file_loc))
    # shutil.copy(os.path.join(file_loc, 'gfstringq.exe'), os.path.join(new_gsm_dir, 'gfstringq.exe'))
    shutil.copy(os.path.join(file_loc, 'status'), os.path.join(new_gsm_dir, 'status'))
    shutil.copy(start_file, os.path.join(new_gsm_dir, 'POSCAR.start'))
    if not os.path.exists(os.path.join(new_gsm_dir, 'scratch')):
        os.makedirs(os.path.join(new_gsm_dir, 'scratch'))

    start = ase.io.read(start_file, format='vasp')
    start.wrap(center)
    initial = [start]
    if final:
        if os.path.isfile(final):
            final_file = final
            final_folder = os.path.dirname(final)
        else:
            final_file = os.path.join(final, 'CONTCAR') if os.path.exists(os.path.join(final, 'CONTCAR')) else os.path.join(final, 'POSCAR')
            final_folder = final
        final = ase.io.read(final_file, format='vasp')
        final.wrap(f_center)
        if poscar_override: # If structure needs realigning
            atoms = []
            # Format the poscar override into pairs
            for i in range(int(len(poscar_override) / 2)):
                atoms.append((poscar_override[i * 2], poscar_override[i * 2 + 1]))
            (s1, s2) = reorganize_structures(Structure.from_file(start_file), Structure.from_file(final_file), atoms=atoms, autosort_tol=tolerance) # pymatgen.core.Structure
            # Reset the start and final file
            start_file = tempfile.NamedTemporaryFile(delete=False).name
            final_file = tempfile.NamedTemporaryFile(delete=False).name
            s1.to('POSCAR', start_file)
            s2.to('POSCAR', final_file)
            start = ase.io.read(start_file, format='vasp')
            final = ase.io.read(final_file, format='vasp')
            start.wrap(center)
            final.wrap(f_center)
            shutil.copy(start_file, os.path.join(new_gsm_dir, 'POSCAR.start'))
            initial = [start, final]
        else:
            initial.append(final)

    try:
        shutil.copy(os.path.join(start_folder, 'KPOINTS'), os.path.join(new_gsm_dir, 'KPOINTS'))
    except:
        print('Copying KPOINTS failed, make sure to add an appropriate KPOINTS to the directory')
    try:
        potcar = Potcar()
        for symbol in Poscar.from_file(os.path.join(new_gsm_dir, 'POSCAR.start')).site_symbols:
            for potcar_single in Potcar.from_file(os.path.join(start_folder, 'POTCAR')): # pymatgen.io.vasp.PotcarSingle
                if symbol == potcar_single.element:
                    potcar.append(potcar_single)
                    break
        potcar.write_file(os.path.join(new_gsm_dir, 'POTCAR'))
    except:
        print('Copying POTCAR failed, make sure to add an appropriate POTCAR to the directory')
    try:
        incar = Incar.from_file(os.path.join(start_folder, 'INCAR'))
        incar['NSW']=0
        if final and 'NUPDOWN' in incar:
            incar_final = Incar.from_file(os.path.join(final_folder, 'INCAR'))
            incar['AUTO_NUPDOWN'] = 'r {} {}'.format(incar['NUPDOWN'], incar_final['NUPDOWN'])
            incar['AUTO_NUPDOWN_ITERS'] = 20
        if name:
            incar['SYSTEM'] = name
        if is_neb:
            images = incar['IMAGES']
            for tag in ['IMAGES', 'LCLIMB']:
                if tag in incar:
                    del incar[tag]
            final_folder = os.path.join(start_folder, str(images+1).zfill(2))
            final_file = os.path.join(final_folder, 'POSCAR')
            final = ase.io.read(final_file, format='vasp')
            initial.append(final)
            start_folder = os.path.join(start_folder, '00')
        incar.write_file(os.path.join(new_gsm_dir, 'INCAR'))
    except:
        print('Copying INCAR failed, make sure to add an appropriate INCAR to the directory')

    currdir = os.path.abspath('.')
    os.chdir(new_gsm_dir)
    with open('grad.py', 'w') as f:
        template = env.get_template('grad.jinja2.py')
        f.write(template.render(jinja_vars))
    with open('inpfileq', 'w') as f:
        template = env.get_template('inpfileq.jinja2')
        f.write(template.render(jinja_vars))
    os.chmod('grad.py', 0o755)
    os.chmod('status', 0o755)
    poscar = Poscar.from_file('POSCAR.start')
    if poscar.selective_dynamics:
        sd = Poscar.from_file('POSCAR.start').selective_dynamics
    else:
        sd = [(True, True, True)] * Poscar.from_file('POSCAR.start').natoms

    ase.io.write('scratch/initial0000.temp.xyz', initial, )
    if fix_positions:
        with open('scratch/initial0000.temp.xyz', 'r') as f:
            lines = [ x.split() for x in f.readlines() ]
            cell = start.get_cell()
            # sfp = final.get_scaled_positions() # Scaled Final Positions
            ssp = start.get_scaled_positions() # Scaled Final Positions
            start_i = 2
            final_i = 2*start_i + len(ssp)
            for i, pos in enumerate(ssp):
                start_coord = np.matrix([ np.float128(x) for x in lines[start_i + i][1:4] ])
                final_coord = np.matrix([ np.float128(x) for x in lines[final_i + i][1:4] ])
                final_coord_temp = final_coord
                distance = np.linalg.norm(start_coord - final_coord)
                for x in [-1, 0 , 1]:
                    for y in [-1, 0, 1]:
                        for z in [-1, 0, 1]:
                            final_coord_diff = np.matrix([x,y,z]) * cell
                            distance_temp = np.linalg.norm(start_coord - (final_coord+final_coord_diff))
                            if distance_temp < distance:
                                final_coord_temp = final_coord+final_coord_diff
                                distance = distance_temp
                lines[final_i+i][1] = final_coord_temp[0,0]
                lines[final_i+i][2] = final_coord_temp[0,1]
                lines[final_i+i][3] = final_coord_temp[0,2]

        with open('scratch/initial0000.temp.xyz', 'w') as f:
            lines = [' '.join([ str(x) for x in line ]) for line in lines]
            f.write( '\n'.join(lines) )



    with open('scratch/initial0000.temp.xyz', 'r') as f:
        # Convert True SD to frozen atoms
        sd = list(map(lambda l : '\n' if (l[0] or l[1] or l[2]) else ' "X"\n', sd))
        # Set up sd to be zipped (two buffer lines at top of each structure)
        to_zip = (['\n', '\n'] + sd) * len(initial)
        zipped = zip(f.readlines(), to_zip)
        xyz = [ ' '.join(x.split()[0:4])+y for x, y in zipped ] # Remove atom number
        with open('scratch/initial0000.xyz', 'w') as f:
            f.writelines(xyz)
        os.remove('scratch/initial0000.temp.xyz')


    if copy_wavefunction:
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


        if final: # is GSM
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

    os.chdir(currdir)





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
    parser.add_argument('--wfxn', help='Don\'t copy WAVECAR and CHGCAR',
                        action='store_false')
    parser.add_argument('--tolerance', help='attempts to match structures (useful for vacancy migrations) (default: 0)',
                        type=float, default=None)
    parser.add_argument('--name', help='Changes INCAR SYSTEM variable to value provided',
                        type=str, default=None)
    parser.add_argument('-a', '--atom_pairs', help='pair certain atoms (1 indexed)', type=int, nargs='*', default=[])
    parser.add_argument('--neb', help='make GSM from NEB Directory',
                        action='store_true')
    args = parser.parse_args()

    args.atom_pairs = [ x-1 for x in args.atom_pairs ]

    GSM_Setup(args.initial, args.final, args.directory, args.nodes, args.center, args.finalcenter, args.wfxn,
              tolerance=args.tolerance, poscar_override=args.atom_pairs, name=args.name, is_neb=args.neb)
