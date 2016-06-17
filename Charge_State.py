#!/usr/bin/env python


import argparse
import os
import shutil
from Classes_Pymatgen import *
from Helpers import get_nelect

parser = argparse.ArgumentParser()
parser.add_argument('start', help='lowest charge value',
                    type=int)
parser.add_argument('end', help='highest charge value',
                    type=int)
parser.add_argument('-f', '--folder', help='Folder to get charge from (default : 0)',
                    type=str, default='0')
parser.add_argument('-c', '--charge', help='Charge of initial state (default : 0)',
                    type=int, default=0)
parser.add_argument('-s', '--system', help='Don\'t modify SYSTEM variable in INCAR.  By default charge state is appended to this')
args = parser.parse_args()

poscar = Poscar.from_file(os.path.join(args.folder, 'CONTCAR') if os.path.exists(os.path.join(args.folder, 'CONTCAR')) and os.path.getsize(os.path.join(args.folder, 'CONTCAR')) > 0 else os.path.join(args.folder, 'POSCAR'))
potcar = Potcar.from_file(os.path.join(args.folder, 'POTCAR'))
incar = Incar.from_file(os.path.join(args.folder, 'INCAR'))
kpoints = Kpoints.from_file(os.path.join(args.folder, 'KPOINTS'))
system = incar["SYSTEM"]
base_nelect = get_nelect(os.path.join(args.folder, 'OUTCAR'))
base_sys = incar['SYSTEM'].split()

for i in range(args.start, args.end+1):
    dir = os.path.join(str(i))
    dir = dir.replace('-', 'n')
    if not os.path.exists(dir):
        print('Setting up run in ./' + dir)
        os.makedirs(dir)

        incar['NELECT'] = base_nelect - i + args.charge
        sys = incar['SYSTEM']
        if base_sys[-1] == '0':
            sys[-1] = dir
        else:
            sys = sys + [' ', dir]
        incar['SYSTEM'] = sys
        incar.write_file(os.path.join(dir, 'INCAR'))
        kpoints.write_file(os.path.join(dir, 'KPOINTS'))
        poscar.write_file(os.path.join(dir, 'POSCAR'))
        potcar.write_file(os.path.join(dir, 'POTCAR'))
    else:
        print('Folder exists:  ' + dir)