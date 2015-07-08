import os
import subprocess
from pymatgen.io.vaspio.vasp_input import Incar
import cfg
import shutil

def neb2dim(neb_dir, dimer_dir):
    dimer_dir = os.path.abspath(dimer_dir)
    os.chdir(neb_dir)
    if not os.path.exists('exts.dat'):
        os.system(os.path.join(cfg.VTST_DIR,'nebspline.pl'))
    if not os.path.exists(dimer_dir):
        os.makedirs(dimer_dir)
    os.system(os.path.join(cfg.VTST_DIR,'neb2dim.pl') + ' > /dev/null')
    for f in os.listdir('dim'):
        shutil.move(os.path.join('dim', f), dimer_dir)

    os.chdir(dimer_dir)
    incar = Incar.from_file('INCAR')
    incar['ICHAIN'] = 2
    incar['IOPT'] = 2
    incar['EDIFF'] = 1e-7
    incar.pop('IMAGES'); incar.pop('SPRING')
    os.remove(os.path.join(dimer_dir, 'INCAR'))
    incar.write_file('INCAR')

def getImageDistance(POSCAR_1, POSCAR_2):
    full_distance_string = subprocess.check_output(os.path.join(cfg.VTST_DIR,'diffcon.pl')+ ' '+ POSCAR_1 +' ' +POSCAR_2, shell=True)
    distance = full_distance_string.split('\n')[-4].split(' ')[-1] # Stripping rest of the file away
    return distance

def getJobType(dir):
    if os.path.basename(dir) == 'INCAR':
        incar = Incar.from_file(dir)
    else:
        incar = Incar.from_file(os.path.join(dir,'INCAR'))
    if 'ICHAIN' in incar:
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