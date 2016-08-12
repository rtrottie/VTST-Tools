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
    directory = os.path.abspath(directory)
    os.chdir(directory)
    ts_vasprun = Vasprun('vasprun.xml')
    if os.path.exists('meps'):
        print 'meps already exists'
        return
    else:
        os.mkdir('meps')
    for m in ['1', '2']:
        min_dir = os.path.join(directory, 'mins', 'min' + m)
        mep_dir = os.path.join(directory, 'meps', 'mep' + m)
        min_vasprun = Vasprun(os.path.join(min_dir, 'vasprun.xml'))
        os.mkdir(mep_dir)
        for f in ['WAVECAR', 'CHGCAR']:
            try:
                mep_min_folder = os.path.join(mep_dir, str(len(min_vasprun.structures)).zfill(4))
                os.mkdir(mep_min_folder)
                print('Copying Min' + f + ' for ' + m),
                shutil.copy(os.path.join(min_dir, f), os.path.join(mep_min_folder, f))
                print('Done')
            except:
                print('Failed')
            try:
                mep_min_folder = os.path.join(mep_dir, '0000')
                os.mkdir(mep_min_folder)
                print('Copying TS' + f + ' for ' + m),
                shutil.copy(f, os.path.join(mep_min_folder, f))
                print('Done')
            except:
                print('Failed')
        print('Copying ' + f + ' for ' + m),
        shutil.copy(os.path.join(min_dir, 'vasprun.xml'), os.path.join(mep_dir, 'MEP.xml'))
        print('done')
        print('Adjusting INCAR')
        incar = Incar.from_file('INCAR')
        incar['EDIFFG'] = -1000000
        incar['SYSTEM'] = 'mep' + m + ' ' + incar['SYSTEM']
        incar.pop('ICHAIN')
        if 'AUTO_TIME' in incar:
            incar.pop('AUTO_TIME')
        incar.write_file(os.path.join(mep_dir,'INCAR'))
        if runP:
            if 'PBS_O_WORKDIR' in os.environ:
                os.environ.pop('PBS_O_WORKDIR')
            os.chdir(mep_dir)
            os.system('touch ' + m + '-' + subprocess.check_output('basename $( ls ../../*.log )', shell=True).strip())
            os.system('Upgrade_Run.py -i ' + runP)
            os.system('vasp.py --ts')
            os.chdir(directory)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', help='directory to run script (Default: ".")',
                        default='.', nargs='?')
    parser.add_argument('-e', '--execute', help='Run VASP once directory is copied must provide dir to initialize',
                        type=str, default='')
    if os.path.exists('CONTCAR') and os.path.getsize('CONTCAR') > 0:
        shutil.move('CONTCAR', 'POSCAR')
    if os.path.exists('NEWMODECAR') and os.path.getsize('NEWMODECAR') > 0:
        shutil.move('NEWMODECAR', 'MODECAR')
    args = parser.parse_args()
    check_dimer(args.directory, args.execute)