#!/usr/bin/env python
from Classes_Pymatgen import *
from pymatgen.io.vasp.outputs import *
import os
import sys
import shutil
import cfg

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


if len(sys.argv) == 1 or sys.argv[1] != '0':
    try:
        run = Vasprun('vasprun.xml', parse_dos=False, parse_eigen=False, parse_potcar_file=False)
        if not run.converged:
            cont = input('Run has not converged.  Continue? (1/0 = yes/no):  ')
            if cont == 1:
                pass
            else:
                sys.exit('Run will not be updated')
    except:
        print('Could Not Read vasprun.xml, continuing anyway')
        run = Vasprun
        run.incar = Incar.from_file('INCAR')
        run.incar['STAGE_NUMBER'] = -1
        run.incar['STAGE_NAME'] = 'init'

else:
    run = Vasprun
    run.incar = Incar.from_file('INCAR')
    run.incar['STAGE_NUMBER'] = -1
    run.incar['STAGE_NAME'] = 'init'


if 'STAGE_FILE' in run.incar:
    conv_file = run.incar["STAGE_FILE"]
else:
    conv_file = "CONVERGENCE"
for incar_adjust_file in [conv_file, '../' + conv_file, '../../' + conv_file, '../../../' + conv_file]: # Look up at least three directories
    if os.path.exists(incar_adjust_file):
        break

updates = parse_incar_update(incar_adjust_file)

incar = Incar.from_file("INCAR")
diff = incar.diff(run.incar)
for i in cfg.INCAR_format[-1][1]:
    if i in diff["Different"].keys() or i in ['NPAR']:
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

if 'STAGE_NUMBER' not in run.incar or (len(sys.argv) > 1 and sys.argv[1] == 'ask'):
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
    prev_stage_name = run.incar['STAGE_NAME']

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
    os.mkdir(prev_stage_name)
    for f in saved_files:
        if os.path.exists(f):
            shutil.copy(f,os.path.join(prev_stage_name, f))

new_incar = run.incar.__add__(Incar(stage))
new_incar.write_file('INCAR')
if kpoints:
    kpoints.write_file('KPOINTS')
