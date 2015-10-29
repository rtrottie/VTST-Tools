from Classes_Pymatgen import *
from pymatgen.io.vasp.outputs import *
import os
import sys

saved_files = ['CONTCAR, vasprun.xml']

os.chdir('/home/ryan/scratch')

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



run = Vasprun('vasprun.xml', parse_dos=False, parse_eigen=False, parse_potcar_file=False)

if not run.converged:
    cont = input('Run has not converged.  Continue? (y/n):  ')
    if cont[0] == 'y':
        pass
    else:
        sys.exit('Run will not be updated')

for incar_adjust_file in ['CONVERGENCE', '../CONVERGENCE', '../../CONVERGENCE', None]: # Look up at least three directories
    if os.path.exists(incar_adjust_file):
        break

updates = parse_incar_update(incar_adjust_file)

if 'STAGE_NUMBER' not in run.incar:
    prompt = 'Run does not appear to have been staged previously.\nWhat stage should be selected:\n'
    stages = '\n'.join(list(map(lambda x: '    ' + str(x['STAGE_NUMBER']) + ' ' +x['STAGE_NAME'], updates)))
    print(prompt+stages)
    cont = input('    or cancel (c) :  ')
    if cont[0] == 'c':
        sys.exit('Canceled')
    elif cont.isdigit():
        stage = updates[int(cont)]
    else:
        sys.exit('Improper value provided')
else:
    stage = updates[int(run.incar['STAGE_NUMBER'])]

if 'REMOVE' in stage.keys():
    to_remove = stage.pop('REMOVE').replace(',',' ').split()
    for item in to_remove:
        run.incar.pop(item)