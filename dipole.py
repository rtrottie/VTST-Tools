#!/usr/bin/env python
from __future__ import print_function
import argparse
import subprocess
import numpy as np
import sys
from pymatgen.io.vasp.outputs import Chgcar

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('axis', help='Axis to average along (x,y,z)',
                        type=int, nargs=3)
    parser.add_argument('-a', '--atoms', help='Atoms to add up',
                        type=int, nargs='*')
    args = parser.parse_args()

    p = subprocess.Popen(['chgsum.pl', 'AECCAR0', 'AECCAR2'])
    p.wait()
    p = subprocess.Popen(['bader', 'CHGCAR_sum', '-p', 'sum_atom'] + [str(x) for x in args.atoms])
    p.wait()

    # Getting info about the cell
    print('Getting Electron Densities...', end='')
    chg = Chgcar.from_file('BvAt_summed.dat')
    s = chg.structure
    d = chg.data['total'] / chg.ngridpts   # get charge density in e-/A^2
    lengths = []
    for i in range(3):
        lengths.append(len(chg.get_axis_grid(i)))
    lengths = np.array(lengths)
    print('done')

    # Adding ionic centers to cell
    print('Adding Ions to Cell...', end='')
    for atom in args.atoms:   # iterating over ion centers
        site = s.sites[atom - 1]
        charge = site.species_and_occu.elements[0].number
        i = np.round(np.array([site.a, site.b, site.c]) * lengths)  # getting indecies to place atomic charges in cell
        d[i[0]][i[1]][i[2]] -= charge  # placing ionic centers in cell
    print('done')

    # Make correction for charged species
    print('Calculating Correction for Charged Species...', end='')
    element_charge = sum(sum(sum(d)))
    bader_gridpts = len(np.nonzero(d)[2])# number of gridpoints in bader volume
    correction = -element_charge / bader_gridpts  # normalization constant to account for charged species
    axis = np.array(args.axis) / np.linalg.norm(np.array(args.axis))
    print('done')
    print('\nCharge = ' + str(element_charge) + ' e-\n')

    # integrate over charge density
    print('Calculating Dipole...', end='')
    dipole = 0
    for a in range(lengths[0]):
        for b in range(lengths[1]):
            for c in range(lengths[2]):
                x = d[a][b][c]
                if x != 0:
                    dipole += (x + correction) * np.dot(axis, np.array([chg.get_axis_grid(0)[a], chg.get_axis_grid(1)[b], chg.get_axis_grid(2)[c]]))
    print('done')
    print(str(dipole))
