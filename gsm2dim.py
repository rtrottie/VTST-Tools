#!/usr/bin/env python

from Classes_Pymatgen import *
import argparse
import shutil


parser = argparse.ArgumentParser()
parser.add_argument('ts_image', help='Image of TS',
                    type=int)
args = parser.parse_args()

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
incar.write_file('INCAR')

print('Making MODECAR')
os.system('modemake.pl ' + grad1 + ' ' + grad2)