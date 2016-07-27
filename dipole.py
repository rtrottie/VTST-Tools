#!/usr/bin/env python
from __future__ import print_function
import argparse
import subprocess
import numpy as np
import sys
from pymatgen.io.vasp.outputs import Chgcar
from Classes_Pymatgen import Poscar, Potcar

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('axis', help='Axis to average along (x,y,z)',
                        type=float, nargs=3)
    parser.add_argument('-a', '--atoms', help='Atoms to add up',
                        type=int, nargs='*')
    parser.add_argument('-n', '--no-calc', help='Don\'t bader volumes',
                        action='store_true')
    parser.add_argument('-o', '--origin', help='Set Origin (helps with wrap around errors)',
                        type=float, nargs=3, default=[0,0,0])
    args = parser.parse_args()

    if not args.no_calc:
        p = subprocess.Popen(['chgsum.pl', 'AECCAR0', 'AECCAR2'])
        p.wait()
        p = subprocess.Popen(['bader', 'CHGCAR', '-ref', 'CHGCAR_sum', '-p', 'sum_atom'] + [str(x) for x in args.atoms])
        p.wait()

    # Getting info about the cell
    print('Getting Electron Densities...', end='')
    sys.stdout.flush()
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
    sys.stdout.flush()
    poscar = Poscar.from_file('POSCAR')
    potcar = Potcar.from_file('POTCAR')
    natoms = poscar.natoms
    cumm_natoms = np.array([ sum(natoms[0:i+1]) for i in range(len(natoms)) ])
    for atom in args.atoms:   # iterating over ion centers
        potcarsingle = potcar[np.argmax(cumm_natoms>=atom)] # get Potcarsingle for each atom
        charge = potcarsingle.nelectrons
        site = s.sites[atom - 1] # atoms are 1 indexed
        # number = site.species_and_occu.elements[0].number
        i = np.round(np.array([site.a, site.b, site.c]) * lengths)  # getting indecies to place atomic charges in cell
        d[i[0]][i[1]][i[2]] -= (charge)  # placing ionic centers in cell
    print('done')

    # Make correction for charged species
    print('Calculating Correction for Charged Species...', end='')
    sys.stdout.flush()
    element_charge = sum(sum(sum(d)))
    bader_gridpts = len(np.nonzero(d)[2])# number of gridpoints in bader volume
    correction = -element_charge / bader_gridpts  # normalization constant to account for charged species
    axis = np.array(args.axis) / np.linalg.norm(np.array(args.axis))
    print('done')
    print('\nCharge = ' + str(element_charge) + ' e-\n')

    # integrate over charge density
    print('Calculating Dipole...', end='')
    sys.stdout.flush()
    dipole = 0
    mod_a = int(np.round(lengths[0] * args.origin[0]))
    mod_b = int(np.round(lengths[1] * args.origin[1]))
    mod_c = int(np.round(lengths[2] * args.origin[2]))
    a_axis = chg.get_axis_grid(0)
    b_axis = chg.get_axis_grid(1)
    c_axis = chg.get_axis_grid(2)
    len_a = len(chg.get_axis_grid(0))
    len_b = len(chg.get_axis_grid(1))
    len_c = len(chg.get_axis_grid(2))
    for a in range(lengths[0]):
        for b in range(lengths[1]):
            for c in range(lengths[2]):
                x = d[a][b][c]
                if x != 0:
                    dipole += (x + correction) * np.dot(axis, np.array([a_axis[a + mod_a % len_a],
                                                                        b_axis[b + mod_b % len_b],
                                                                        c_axis[c + mod_c % len_c]]))
    print('done')
    print('Dipole = ' + str(dipole))
    sys.stdout.flush()
