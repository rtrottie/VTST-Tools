#!/usr/bin/env python

import argparse
from Classes_Pymatgen import *
import os



def nebmake(directory, start, final, images, tolerance=0):
    start_POSCAR = os.path.join(start, 'CONTCAR') if os.path.exists(os.path.join(start, 'CONTCAR')) and os.path.getsize(os.path.join(start, 'CONTCAR')) > 0 else os.path.join(start, 'POSCAR')
    final_POSCAR = os.path.join(final, 'CONTCAR') if os.path.exists(os.path.join(final, 'CONTCAR')) and os.path.getsize(os.path.join(final, 'CONTCAR')) > 0 else os.path.join(final, 'POSCAR')

    start_OUTCAR = os.path.join('OUTCAR')
    final_OUTCAR = os.path.join('OUTCAR')
    incar = Incar.from_file(os.path.join(start, 'INCAR'))
    kpoints = Kpoints.from_file(os.path.join(start, 'KPOINTS'))
    potcar = Potcar.from_file(os.path.join(start, 'POTCAR'))

    p1 = Poscar.from_file(start_POSCAR)
    p2 = Poscar.from_file(final_POSCAR)
    structures = p1.structure.interpolate(p2, images, autosort_tol=tolerance)

    incar['ICHAIN'] = 0
    incar['IMAGES'] = images

    for


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('initial', help='Structure or VASP run folder of initial state')
    parser.add_argument('final', help='Structure or VASP run folder of final state')
    parser.add_argument('-n', '--nodes', help='Number of nodes on string (Default: 7)',
                        type=int, default=7)
    parser.add_argument('-t', '--tolerance', help='attempts to match structures (useful for vacancy migrations) (default: 0)',
                        type=float, default=0)
    args = parser.parse_args()