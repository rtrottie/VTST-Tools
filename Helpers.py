import os
import subprocess
from pymatgen.io.vaspio.vasp_input import Incar

VTST_DIR = subprocess.check_output('echo $VTST_DIR', shell=True).strip()

def getImageDistance(POSCAR_1, POSCAR_2):
    global VTST_DIR
    full_distance_string = subprocess.check_output(os.path.join(VTST_DIR,'diffcon.pl')+ ' '+ POSCAR_1 +' ' +POSCAR_2, shell=True)
    distance = full_distance_string.split('\n')[-4].split(' ')[-1] # Stripping rest of the file away
    return distance

a = getImageDistance('/home/ryan/PycharmProjects/00/POSCAR','/home/ryan/PycharmProjects/06/POSCAR')

print('done')