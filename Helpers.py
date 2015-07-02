import os
import subprocess
from pymatgen.io.vaspio.vasp_input import Incar
import cfg



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