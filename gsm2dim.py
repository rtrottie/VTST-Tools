#!/usr/bin/env python

from Classes_Pymatgen import *
import argparse
import shutil
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument('ts_image', help='Image of TS (will try to find if not given)',
                    type=int, default=-1)
args = parser.parse_args()

if args.ts_image < 0:
    energies = subprocess.check_output(['grep', 'V_profile', '|', 'tail', '-n', '1'], shell=True)
    energies = [ float(x) for x in energies.split()[1:] ]
    args.ts_image = energies.index(max(energies)) + 1
    print 'TS Image Determined to be:  ' + str(args.ts_image)


ts = 'scratch/IMAGE.' + str(args.ts_image).zfill(2)
grad1 = '../scratch/IMAGE.' + str(args.ts_image - 1).zfill(2)
grad2 = '../scratch/IMAGE.' + str(args.ts_image + 1).zfill(2)

print('Copying Old Run')

shutil.copytree(ts, 'dim')
os.chdir('dim')

print('Setting up INCAR')
incar = Incar.from_file('INCAR')
incar['ICHAIN'] = 2
incar['EDIFF'] = 1e-7
incar['NSW'] = 5000
incar['SYSTEM'] = incar['SYSTEM'] + ' dim'
incar.write_file('INCAR')

print('Making MODECAR')
os.system('modemake.pl ' + grad1 + '/POSCAR ' + grad2 + '/POSCAR &> /dev/null')