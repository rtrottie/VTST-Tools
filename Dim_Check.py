#!/usr/bin/env python
# Starts two relaxations from opposite ends of the saddle point.  Uses the Fire Method, which should relax into
# local minima so subsequent runs should be done with the VTST code.  Files can be found in mins/min{1,2}

# usage:  Dim_Check.py
import os
import cfg
import shutil
import sys
import subprocess
import argparse
from Classes_Pymatgen import *

def check_dimer(directory, runP=False):
    os.chdir(directory)
    os.system(os.path.join(os.environ['VTST_DIR'], 'dimmins.pl'))
    for m in ['min1', 'min2']:
        dir = os.path.join(directory, 'mins', m)
        try:
            print('Copying WAVECAR to ' + m),
            shutil.copy(os.path.join(directory, 'WAVECAR'), dir)
            print('Done')
        except:
            print('Failed')
        try:
            print('Copying CHGCAR to ' + m),
            shutil.copy(os.path.join(directory, 'CHGCAR'), dir)
            print('Done')
        except:
            print('Failed')
        print('Adjusting INCAR')
        incar = Incar.from_file(os.path.join(dir,'INCAR'))
        incar['EDIFF'] = 1e-5
        incar['EDIFFG'] = incar['EDIFFG']*1.5
        incar['SYSTEM'] = m + ' ' + incar['SYSTEM']
        incar.pop('ICHAIN')
        incar['IOPT'] = 7
        if 'AUTO_TIME' in incar:
            incar.pop('AUTO_TIME')
        incar.write_file(os.path.join(dir,'INCAR'))
        if runP:
            os.chdir(dir)
            os.system('touch ' + m + '-' + subprocess.check_output('basename $( ls ../../*.log )', shell=True).strip())
            os.system('vasp.py ')
            os.chdir(directory)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', help='directory to run script (Default: ".")',
                        default='.', nargs='?')
    parser.add_argument('-r', '--run', help='Run VASP once directory is copied arguments provided here will be supplied to vasp.py',
                        args='*')
    args = parser.parse_args()
    check_dimer(args.directory, args.run)