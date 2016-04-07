#!/usr/bin/env python

import argparse
from Classes_Pymatgen import *
import os



def nebmake(directory, start, final, images, tolerance=0, ci=False):
    start_POSCAR = os.path.join(start, 'CONTCAR') if os.path.exists(os.path.join(start, 'CONTCAR')) and os.path.getsize(os.path.join(start, 'CONTCAR')) > 0 else os.path.join(start, 'POSCAR')
    final_POSCAR = os.path.join(final, 'CONTCAR') if os.path.exists(os.path.join(final, 'CONTCAR')) and os.path.getsize(os.path.join(final, 'CONTCAR')) > 0 else os.path.join(final, 'POSCAR')

    start_OUTCAR = os.path.join('OUTCAR')
    final_OUTCAR = os.path.join('OUTCAR')
    incar = Incar.from_file(os.path.join(start, 'INCAR'))
    kpoints = Kpoints.from_file(os.path.join(start, 'KPOINTS'))
    potcar = Potcar.from_file(os.path.join(start, 'POTCAR'))

    p1 = Poscar.from_file(start_POSCAR)
    p2 = Poscar.from_file(final_POSCAR)
    structures = p1.structure.interpolate(p2.structure, images, autosort_tol=tolerance)

    incar['ICHAIN'] = 0
    incar['IMAGES'] = images
    incar['LCLIMB'] = ci

    i=0
    for s in structures:
        folder = os.path.join(directory, str(i).zfill(2))
        os.mkdir(folder)
        Poscar(s, selective_dynamics=p1.selective_dynamics).write_file(os.path.join(folder, 'POSCAR'))
        i += 1

    incar.write_file(os.path.join(directory, 'INCAR'))
    kpoints.write_file(os.path.join(directory, 'KPOINTS'))
    potcar.write_file(os.path.join(directory, 'POTCAR'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('initial', help='Structure or VASP run folder of initial state')
    parser.add_argument('final', help='Structure or VASP run folder of final state')
    parser.add_argument('-i', '--images', help='Number of images on string (Default: 7)',
                        type=int, default=7)
    parser.add_argument('-t', '--tolerance', help='attempts to match structures (useful for vacancy migrations) (default: 0)',
                        type=float, default=0)
    parser.add_argument('-d', '--directory', help='where to create neb (default: ".")',
                        default='.')
    parser.add_argument('-c', '--climbing_image', help='use CI', action = 'store_true')
    args = parser.parse_args()
    nebmake(args.directory, args.initial, args.final, args.images, args.tolerance, args.climbing_image)