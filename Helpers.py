# Various functions called by other functions
# Not meant to be called from command line

import os
import subprocess
from pymatgen.core.structure import *
import cfg
import shutil
from Classes_Pymatgen import *

def xfrange(start, stop, step):
    start = float(start)
    while start < stop:
        yield start
        start += step

def neb2dim(neb_dir, dimer_dir):
    dimer_dir = os.path.abspath(dimer_dir)
    os.chdir(neb_dir)
    if not os.path.exists('exts.dat'):
        os.system(os.path.join(os.environ['VTST_DIR'],'nebspline.pl'))
    if not os.path.exists(dimer_dir):
        os.makedirs(dimer_dir)
    os.system(os.path.join(os.environ['VTST_DIR'],'neb2dim.pl') + ' > /dev/null')
    if os.path.join(os.path.abspath(neb_dir), 'dim') != dimer_dir:
        for f in os.listdir('dim'):
            shutil.move(os.path.join('dim', f), dimer_dir)

    os.chdir(dimer_dir)
    incar = Incar.from_file('INCAR')
    incar['ICHAIN'] = 2
    incar['EDIFF'] = 1e-7
    incar.pop('IMAGES');
    try:
        incar.pop('SPRING');
    except:
        pass
    try:
        incar.pop('LCLIMB')
    except:
        pass
    os.remove(os.path.join(dimer_dir, 'INCAR'))
    incar.write_file('INCAR')

def getImageDistance(POSCAR_1, POSCAR_2):
    full_distance_string = subprocess.check_output(os.path.join(os.environ['VTST_DIR'],'diffcon.pl')+ ' '+ POSCAR_1 +' ' +POSCAR_2, shell=True)
    distance = full_distance_string.split('\n')[-4].split(' ')[-1] # Stripping rest of the file away
    return distance

def getJobType(dir):
    if os.path.basename(dir) == 'INCAR':
        incar = Incar.from_file(dir)
    else:
        incar = Incar.from_file(os.path.join(dir,'INCAR'))
    if os.path.exists(os.path.join(dir, 'gfstringq.exe')):
        return 'GSM'
    elif 'ICHAIN' in incar:
        if incar['ICHAIN'] == 0:
            return 'NEB'
        elif incar['ICHAIN'] == 2:
            return 'Dimer'
        else:
            raise Exception('Not yet Implemented')
    elif 'IMAGES' in incar:
            return 'NEB'
    else:
        return 'Standard'

def getLoopPlusTimes(outcar):
    grep = subprocess.check_output('grep LOOP+: ' + outcar, shell=True).strip().split('\n')
    times = map(lambda l: float(l.split()[-1]), grep)
    return times

def getMaxLoopTimes(times):
    return sum(map(lambda x: max(x),
                   zip(*times)))

def update_incar(structure, incar):
    for k in incar.keys():
        if k in cfg.INCAR:
            species = map(lambda sp: str(sp), structure.species)
            if k != 'MAGMOM':
                species = list(species)
                lspecies = list(map(lambda x: [x], species))
                species = reduce(lambda x,y: x+y if x[-1] != y[0] else x + y[1:-1],
                                 map(lambda x: [x], species))
            incar[k] = list(map(lambda a: cfg.INCAR[k][a] if a in cfg.INCAR[k] else cfg.INCAR[k]['default'],
                            species))

def load_variables(file_loc):
    vars = {}
    with open(file_loc) as f:
        for l in f.readlines():
            variable_value = l.split(':')
            vars[variable_value[0].strip()] = variable_value[1].strip()
    return vars