#!/usr/bin/env python
# attempts to Fully initialize (changes ICHAIN) from an NEB run, still has a few issues

# Usage: neb2dim.py NEB_dir [Dim_dir]

import os
import shutil
from pymatgen.analysis.transition_state import NEBAnalysis
from Classes_Pymatgen import Incar
import argparse

def neb2dim(neb_dir, dimer_dir):
    neb_dir = os.path.abspath(neb_dir)
    dimer_dir = os.path.abspath(dimer_dir)
    try:
        energies = NEBAnalysis.from_dir(neb_dir).energies
    except:
        if raw_input('Failed, do: rm ' + neb_dir + '*/*.xyz and try again? (y)') == 'y':
            os.system('rm ' + neb_dir + '/*/*.xyz')
            energies = NEBAnalysis.from_dir(neb_dir).energies
        else:
            raise Exception('Could not read NEB dir')

    ts_i = list(energies).index(energies.max())

    print('Copying TS directory')
    if not os.path.exists(dimer_dir):
        os.makedirs(dimer_dir)
    for f in os.listdir(os.path.join(neb_dir, str(ts_i).zfill(2))):
        shutil.copy(os.path.join(neb_dir, str(ts_i).zfill(2), f), dimer_dir)
    for f in ['INCAR', 'KPOINTS', 'POTCAR']:
        shutil.copy(os.path.join(neb_dir, f), dimer_dir)

    print('Modifying INCAR')
    incar = Incar.from_file(os.path.join(dimer_dir, 'INCAR'))
    incar['ICHAIN'] = 2
    incar['EDIFF'] = 1e-7
    incar['NSW'] = 5000
    if 'neb' in incar['SYSTEM']:
        incar['SYSTEM'] = incar['SYSTEM'].replace('neb', 'dim')
    else:
        incar['SYSTEM'] = incar['SYSTEM'] + ' dim'
    for neb_setting in ['IMAGES', 'LCLIMB']:
        if neb_setting in incar:
            del incar[neb_setting]
    incar.write_file('INCAR')

    print('Making MODECAR')
    mode1 = os.path.join(neb_dir, str(ts_i - 1).zfill(2))
    mode2 = os.path.join(neb_dir, str(ts_i + 1).zfill(2))
    cwd = os.path.abspath('.')
    os.chdir(dimer_dir)
    os.system('modemake.pl ' + mode1 + '/CONTCAR ' + mode2 + '/CONTCAR &> /dev/null')
    os.chdir(cwd)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('neb_dir', help='location of the neb dir')
    parser.add_argument('dimer_dir', help='location of desired dimer dir (defaults to ".")',
                        default='.', nargs='?')
    args = parser.parse_args()

    dimer_dir = args.dimer_dir
    neb_dir = args.neb_dir
    neb2dim(neb_dir, dimer_dir)