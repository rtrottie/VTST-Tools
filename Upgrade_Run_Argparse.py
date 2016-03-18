#!/usr/bin/env python
from pymatgen.io.vasp.outputs import *
from Classes_Pymatgen import *
import os
import sys
import shutil
import cfg
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('-i', '--initialize', help='Initialize Vasp Run from CONVERGENCE file',
                    action='store_true')
parser.add_argument('-s', '--stage', help='Forces Upgrade to specified run',
                    type=int, default=-1)
parser.add_argument('-f', '--file-convergence', help='Location of CONVERGENCE file on disk',
                    type=str)
parser.add_argument('-p', '--parent-directories', help='Number of Parent directories to look up into for CONVERGENCE file (DEFAULT: 5) overruled by -f option',
                    type=int, default=5)
parser.add_argument('-v', '--compare-vasprun.xml', help='Compare entire INCAR and vasprun.xml instead of just checking updated values.  Will almost always result in a prompt to continue.',
                    action='store_true')

convergence = parser.add_mutually_exclusive_group()
convergence.add_argument('--convergence-auto', help='Checks for Convergence, automatically stops if run isn\'t fully converged',
                         action='store_true')
convergence.add_argument('--convergence-ignore', help='Makes no convergence check',
                         action='store_true')

args = parser.parse_args()

saved_files = ['CONTCAR, vasprun.xml', 'OUTCAR', 'INCAR', 'KPOINTS', 'POSCAR', 'MODECAR', 'NEWMODECAR']

def parse_incar_update(f_string):
    with open(f_string) as f:
        dicts = []
        this_stage = None
        for line in f:
            if line[0].isdigit():
                if this_stage != None:
                    dicts.append(this_stage)
                this_stage = {}
                designation = line.split()
                this_stage['STAGE_NUMBER'] = int(designation[0])
                this_stage['STAGE_NAME'] = designation[1]
            else:
                setting = line.replace('=',' ').split()
                if len(setting) >= 2:
                    this_stage[setting[0].upper()] = ' '.join(setting[1:])
    dicts.append(this_stage)
    return dicts

if args.initialize:
    run = Vasprun
    run.incar = Incar.from_file('INCAR')
    run.incar['STAGE_NUMBER'] = -1
    run.incar['STAGE_NAME'] = 'init'

else:
    if args['convergence-ignore']:
        try:
            run = Vasprun('vasprun.xml', parse_dos=False, parse_eigen=False, parse_potcar_file=False)
        except:
            run = Vasprun
            run.incar = Incar.from_file('INCAR')
            run.converged = False
    else:
        try:
            run = Vasprun('vasprun.xml', parse_dos=False, parse_eigen=False, parse_potcar_file=False)
        except Exception as e:
            if args['convergence-auto']:
                raise e
            run = Vasprun
            run.incar = Incar.from_file('INCAR')
            run.converged = False
        finally:
            if not run.converged:
                cont = input('Run has not converged.  Continue? (1/0 = yes/no):  ')
                if cont == 1:
                    pass
                else:
                    sys.exit('Run will not be updated')


if args['file-convergence']:
    conv_file = args['file-convergence']
elif 'STAGE_FILE' in run.incar:
    conv_file = run.incar["STAGE_FILE"]
else:
    conv_file = None
    for i in range(args['parent-directories'] + 1):
        conv_file_test = '../' * i + 'CONVERGENCE'
        if os.path.exists(conv_file_test):
            conv_file = conv_file_test
            break

if conv_file == None or not os.path.exists(conv_file):
    raise Exception('CONVERGENCE File does not exist')

updates = parse_incar_update(conv_file)
incar = Incar.from_file("INCAR")

if args.stage != -1:
    stage = updates[args.stage]
    if int(args.stage) > 0:
        prev_stage_name = updates[int(cont)-1]['STAGE_NAME']
        prev_stage = updates[args.stage - 1]
    else:
        prev_stage_name = 'init'
else:
    stage = updates[int(run.incar['STAGE_NUMBER'])+1]
    prev_stage_name = run.incar['STAGE_NAME']

ignored_keys = ['NPAR', 'KPAR', 'AUTO_TIME', 'AUTO_GAMMA', 'AUTO_MEM']

if args['compare-vasprun.xml']:
    diff = incar.diff(run.incar)
    for i in cfg.INCAR_format[-1][1]:
        if i in diff["Different"].keys() or i in ignored_keys:
            diff["Different"].pop(i)
    if len(diff["Different"].keys()) > 0:
        err_msg = 'INCAR appears different than the vasprun.xml.  Problems with: ' + ' '.join(diff["Different"].keys())
        for key in diff["Different"].keys():
            err_msg = err_msg + '\n  ' + key + '   '
            if key in run.incar:
                err_msg = err_msg + 'vasprun.xml :  ' + str(run.incar[key]) + '   '
            else:
                err_msg = err_msg + 'vasprun.xml :  N/A   '
            if key in incar:
                    err_msg = err_msg + 'INCAR : ' + str(incar[key])
            else:
                err_msg = err_msg + 'INCAR :  N/A'
        cont = input(err_msg + '\n  Continue? (1/0 = yes/no):  ')
        if cont == 1:
            run.incar = incar
        else:
            sys.exit('Run will not be updated')
else:
    err_msg = 'CONVERGENCE previous stage appears different than what is in the vasprun.xml.  Problems with: '
    error = False
    for key in prev_stage.keys:
        if key not in ignored_keys:
            if key in run.incar:
                if run.incar[key] != prev_stage[key]:
                    err_msg = err_msg + '\n' + key + ':  vasprun.xml :  ' + str(run.incar[key]) + '     ' + 'CONV : ' + str(incar[key])
                    error = True
            else:
                err_msg = err_msg + '\n' + key + ':  vasprun.xml :  ' + str(run.incar[key]) + '     ' + 'CONV : ' + str(incar[key])
                error = True
    if error:
        cont = input(err_msg + '\n  Continue? (1/0 = yes/no):  ')
        if cont == 1:
            run.incar = incar
        else:
            sys.exit('Run will not be updated')



################
### OLD CODE ###
################


kpoints = False
for val in stage.keys():
    if val in run.incar:
        run.incar.pop(val)
    elif val == 'REMOVE':
        to_remove = stage.pop('REMOVE').replace(',',' ').split()
        for item in to_remove:
            try:
                run.incar.pop(item)
            except:
                print('Could not remove ' + item +' because it does not exist.')
    elif val == 'DELETE':
        to_delete = stage.pop('DELETE').replace(',',' ').split()
        for item in to_delete:
            try:
                os.remove(item)
            except:
                print('Could not delete ' + item +' because it does not exist.')
    elif val == 'KPOINTS':
        kpt = stage.pop('KPOINTS').replace(',',' ').split()
        if len(kpt) == 1 and kpt[0] == 'G':
            kpoints = Kpoints.gamma_automatic()
        elif len(kpt) == 3 or (len(kpt) == 4 and kpt[0] == 'G'):
            kpoints = Kpoints.gamma_automatic((int(kpt[-3]), int(kpt[-2]), int(kpt[-1]) ))
        elif (len(kpt) == 4 and kpt[0] == 'M'):
            kpoints = Kpoints.monkhorst_automatic((int(kpt[-3]), int(kpt[-2]), int(kpt[-1]) ))
        else:
            raise Exception('Kpoint not formated correctly need [G/M] x y z [x_shift, y_shift, z_shift] or G')

if prev_stage_name:
    os.makedirs(os.path.join('backup', prev_stage_name))
    for f in saved_files:
        if os.path.exists(f):
            shutil.copy(f,os.path.join('backup', prev_stage_name, f))

new_incar = run.incar.__add__(Incar(stage))
new_incar.write_file('INCAR')
if kpoints:
    kpoints.write_file('KPOINTS')
