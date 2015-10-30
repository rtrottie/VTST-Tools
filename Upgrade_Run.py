#!/usr/bin/env python
from Classes_Pymatgen import *
from pymatgen.io.vasp.outputs import *
import os
import sys
import shutil

saved_files = ['CONTCAR, vasprun.xml', 'OUTCAR', 'INCAR', 'KPOINTS', 'POSCAR']

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


if sys.argv[1] != '0':
    run = Vasprun('vasprun.xml', parse_dos=False, parse_eigen=False, parse_potcar_file=False)
    if not run.converged:
        cont = input('Run has not converged.  Continue? (1/0 = yes/no):  ')
        if cont == 1:
            pass
        else:
            sys.exit('Run will not be updated')
else:
    run = Vasprun
    run.incar = Incar.from_file('INCAR')
    run.incar['STAGE_NUMBER'] = -1


if 'STAGE_FILE' in run.incar:
    conv_file = run.incar["STAGE_FILE"]
else:
    conv_file = "CONVERGENCE"
for incar_adjust_file in [conv_file, '../' + conv_file, '../../' + conv_file, None]: # Look up at least three directories
    if os.path.exists(incar_adjust_file):
        break

updates = parse_incar_update(incar_adjust_file)

incar = Incar.from_file("INCAR")
diff = incar.diff(run.incar)
if len(diff["Different"].keys()) > 0:
    err_msg = 'INCAR appears different than the vasprun.xml.  Problems with: ' + ' '.join(diff["Different"].keys())
    cont = input(err_msg + '  Continue? (1/0 = yes/no):  ')
    if cont == 1:
        pass
    else:
        sys.exit('Run will not be updated')

if 'STAGE_NUMBER' not in run.incar or sys.argv[1] == 'ask':
    prompt = 'Run does not appear to have been staged previously.\nWhat stage should be selected:\n'
    stages = '\n'.join(list(map(lambda x: '    ' + str(x['STAGE_NUMBER']) + ' ' +x['STAGE_NAME'], updates)))
    print(prompt+stages)
    cont = input('    or cancel (c) :  ')
    if cont == -1:
        sys.exit('Canceled')
    else:
        stage = updates[int(cont)]
        if int(cont) > 0:
            prev_stage_name = updates[int(cont)-1]['STAGE_NAME']
        else:
            prev_stage_name = None
else:
    stage = updates[int(run.incar['STAGE_NUMBER'])+1]
    if int(run.incar['STAGE_NUMBER'])+1 < 1:
        prev_stage_name = run.incar['STAGE_NAME']

kpoints = False
for val in stage.keys():
    if val in run.incar:
        run.incar.pop(val)
    elif val == 'REMOVE':
        to_remove = stage.pop('REMOVE').replace(',',' ').split()
        for item in to_remove:
            run.incar.pop(item)
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
    os.mkdir(prev_stage_name)
    for f in saved_files:
        if os.path.exists(f):
            shutil.copy(f,os.path.join(prev_stage_name, f))

new_incar = run.incar.__add__(Incar(stage))
new_incar.write_file('INCAR')
if kpoints:
    kpoints.write_file('KPOINTS')
