#!/usr/bin/env python
from __future__ import print_function
import argparse
import subprocess
import numpy as np
import sys
import os
from pymatgen.io.vasp.outputs import Chgcar
from Classes_Pymatgen import Poscar, Potcar
from File_Management import file_to_dict

def dipole_acf(args):
    poscar = Poscar.from_file('POSCAR')
    potcar = Potcar.from_file('POTCAR')
    natoms = poscar.natoms
    cumm_natoms = np.array([sum(natoms[0:i + 1]) for i in range(len(natoms))])
    s = poscar.structure
    lattice = s.lattice
    cart_axis = np.matrix(args.axis) * s.lattice.matrix
    unit_vector = cart_axis / np.linalg.norm((cart_axis))
    with open('ACF.dat', 'rb') as acf_file:
        acf = file_to_dict(acf_file.read(), ['#', 'x', 'y', 'z', 'charge', 'min_dist', 'volume'])
        charges_vectors = []
        for atom in args.atoms:  # iterating over ion centers
            potcarsingle = potcar[np.argmax(cumm_natoms >= atom)]  # get Potcarsingle for each atom
            core_charge = potcarsingle.nelectrons
            site = s.sites[atom - 1]  # atoms are 1 indexed
            vector = np.matrix([site.x, site.y, site.z])
            translate_vector = np.matrix([site.a < args.origin[0], site.b < args.origin[1],
                                          site.c < args.origin[2]])  # determining if site is < the origin
            charges_vectors.append((core_charge - float(acf['charge'][atom - 1]),
                                    np.dot(vector + translate_vector * lattice.matrix, np.transpose(unit_vector))))
            # number = site.species_and_occu.elements[0].number
    net_charge = sum([charge for charge, _ in charges_vectors])
    dipole = sum([(charge - net_charge / len(args.atoms)) * vector for charge, vector in charges_vectors])
    print(charges_vectors)
    print([(charge - net_charge / len(args.atoms)) * vector for charge, vector in charges_vectors])
    print('\nCharge = ' + str(net_charge) + ' e-\n')
    print('Dipole = ' + str(float(dipole)) + ' eA')
    print('Dipole = ' + str(float(dipole) / 0.20819434) + ' D')
    return float(dipole)

def dipole_chgcar(args):
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
        d[i[0] % lengths[0]][i[1] % lengths[1]][i[2] % lengths[2]] -= (charge)  # placing ionic centers in cell
    print('done')

    # Make correction for charged species
    print('Calculating Correction for Charged Species...', end='')
    sys.stdout.flush()
    element_charge = sum(sum(sum(d)))
    bader_gridpts = len(np.nonzero(d)[2])# number of gridpoints in bader volume
    correction = element_charge / bader_gridpts  # normalization constant to account for charged species
    print('done')
    print('\nCharge = ' + str(-element_charge) + ' e-\n')
    # print('\nCorrection = ' + str(correction) + ' e-\n')

    # Calculating lattice
    #axis = np.array(args.axis) # / np.linalg.norm(np.array(args.axis))
    cart_axis = np.matrix(args.axis) * s.lattice.matrix
    unit_vector = cart_axis / np.linalg.norm((cart_axis))
    a_axis = chg.get_axis_grid(0)
    b_axis = chg.get_axis_grid(1)
    c_axis = chg.get_axis_grid(2)
    len_a = len(a_axis)
    len_b = len(b_axis)
    len_c = len(c_axis)
    mod_a = int(np.round(float(len_a) * args.origin[0]))
    mod_b = int(np.round(float(len_b) * args.origin[1]))
    mod_c = int(np.round(float(len_c) * args.origin[2]))
    mat = s.lattice.matrix
    def get_first_moment(a, b, c, x):
        a = float((a - mod_a) % len_a) / len_a
        b = float((b - mod_b) % len_b) / len_b
        c = float((c - mod_c) % len_c) / len_c
        cart_vector = np.matrix([a, b, c]) * mat
        return float(np.dot(cart_vector, unit_vector.transpose())) * (x - correction)

    # integrate over charge density
    print('Calculating Dipole... ')
    sys.stdout.flush()
    dipole = 0
    for a in range(lengths[0]):
        sys.stdout.write('\r%d percent' % int(a * 100 / len_a))
        sys.stdout.flush()
        for b in range(lengths[1]):
            for c in range(lengths[2]):
                x = d[a][b][c]
                if x != 0:
                    dipole += get_first_moment(a, b, c, x)
    print('done')
    print('Dipole = ' + str(dipole) + ' eA')
    print('Dipole = ' + str(dipole / 0.20819434) + ' D')
    return dipole
    sys.stdout.flush()

def get_chg_matrix(folder):
    chg = Chgcar.from_file(os.path.join(folder, 'CHGCAR'))
    chg_matrix = chg.data['total'] / chg.ngridpts
    potcar = Potcar.from_file(os.path.join(folder, 'POTCAR'))
    poscar = Poscar.from_file(os.path.join(folder, 'POSCAR'))
    natoms = poscar.natoms
    cumm_natoms = np.array([sum(natoms[0:i + 1]) for i in range(len(natoms))])

    lengths = []
    for i in range(3):
        lengths.append(len(chg.get_axis_grid(i)))
    lengths = np.array(lengths)

    for atom in range(len(chg.structure.sites)):  # iterating over ion centers
        potcarsingle = potcar[np.argmax(cumm_natoms >= (atom+1))]  # get Potcarsingle for each atom
        charge = potcarsingle.nelectrons
        site = chg.structure.sites[atom]  # atoms are 1 indexed
        # number = site.species_and_occu.elements[0].number
        i = np.round(np.array([site.a, site.b, site.c]) * lengths)  # getting indecies to place atomic charges in cell
        chg_matrix[int(i[0] % lengths[0])][int(i[1] % lengths[1])][int(i[2] % lengths[2])] -= (charge)  # placing ionic centers in cell

    return -chg_matrix

def dipole_chgcars(dipole_folder, reference_folder):
    print('Getting Electron Densities (dipole)...', end='', flush=True)
    dipole_matrix = get_chg_matrix(dipole_folder)
    print('done')

    print('Getting Electron Densities (reference)...', end='', flush=True)
    reference_matrix   = get_chg_matrix(reference_folder)
    s = Poscar.from_file(os.path.join(reference_folder, 'POSCAR')).structure
    print('done')


    cart_axis = np.matrix(args.axis) * s.lattice.matrix
    unit_vector = cart_axis / np.linalg.norm((cart_axis))
    len_a = len(dipole_matrix)
    len_b = len(dipole_matrix[0])
    len_c = len(dipole_matrix[0][0])
    mod_a = int(np.round(float(len_a) * args.origin[0]))
    mod_b = int(np.round(float(len_b) * args.origin[1]))
    mod_c = int(np.round(float(len_c) * args.origin[2]))
    mat = s.lattice.matrix

    def get_first_moment(a, b, c, x):
        a = float((a - mod_a) % len_a) / len_a
        b = float((b - mod_b) % len_b) / len_b
        c = float((c - mod_c) % len_c) / len_c
        cart_vector = np.matrix([a, b, c]) * mat
        return float(np.dot(cart_vector, unit_vector.transpose())) * x

    print('Calculating Dipole...')
    diff = dipole_matrix - reference_matrix
    dipole = 0
    for a in range(len_a):
        sys.stdout.write('\r%d percent' % int(a * 100 / len_a))
        sys.stdout.flush()
        for b in range(len_b):
            for c in range(len_c):
                dipole += get_first_moment(a, b, c, diff[a][b][c])
    print('done')
    print('Dipole = ' + str(dipole) + ' eA')
    print('Dipole = ' + str(dipole / 0.20819434) + ' D')
    return dipole



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('axis', help='Axis to average along (x,y,z)',
                        type=float, nargs=3)
    parser.add_argument('-a', '--atoms', help='Atoms to add up',
                        type=int, nargs='*')
    parser.add_argument('-d', '--dipole', help='Folder to calculate dipole in (default = ".")',
                        default='.')
    parser.add_argument('-r', '--reference', help='Cell Reference')
    parser.add_argument('-n', '--no-calc', help='Don\'t bader volumes',
                        action='store_true')
    parser.add_argument('-o', '--origin', help='Set Origin (helps with wrap around errors)',
                        type=float, nargs=3, default=[0,0,0])
    parser.add_argument('--acf', help='Calculate dipole using ACF.dat',
                        action='store_true')
    args = parser.parse_args()



    if args.acf:
        dipole = dipole_acf(args)
    elif args.dipole and args.reference:
        dipole = dipole_chgcars(args.dipole, args.reference)
    else:
        if not args.no_calc:
            p = subprocess.Popen(['chgsum.pl', 'AECCAR0', 'AECCAR2'])
            p.wait()
            p = subprocess.Popen(
                ['bader', 'CHGCAR', '-ref', 'CHGCAR_sum', '-p', 'sum_atom'] + [str(x) for x in args.atoms])
            p.wait()
        dipole = dipole_chgcar(args)
    with open('dipole.dat', 'w') as dip_file:
        dip_file.write('Dipole = ' + str(dipole) + ' eA\nDipole = ' + str(dipole / 0.20819434) + ' D')



