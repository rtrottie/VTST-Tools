#!/usr/bin/env python


import argparse
from Classes_Pymatgen import *

parser = argparse.ArgumentParser()
parser.add_argument('center', help='magmom to check values from',
                    type=int, default=0)
parser.add_argument('radius', help='Number of values to check around (default = 3 (7 jobs)) OPTIONAL',
                    type=int, default=5, nargs='?')
args = parser.parse_args()

poscar = Poscar.from_file('CONTCAR' if os.path.exists('CONTCAR') and os.path.getsize('CONTCAR') > 0 else 'POSCAR')
potcar = Potcar.from_file('POTCAR')
incar = Incar.from_file('INCAR')
kpoints = Incar.from_file('KPOINTS')

if not os.path.exists('nupdown'):
    os.makedirs('nupdown')

for i in range(args.center - args.radius, args.center + args.radius + 1):
    dir = os.path.join('nupdown', str(i).zfill(3))
    if not os.path.exists(dir):
        os.makedirs(dir)

    incar['NUPDOWN'] = i
    incar.write_file(os.path.join(dir, 'INCAR'))
    kpoints.write_file(os.path.join(dir, 'KPOINTS'))
    poscar.write_file(os.path.join(dir, 'POSCAR'))
    potcar.write_file(os.path.join(dir, 'POTCAR'))