#!/usr/bin/env python

import argparse
from Classes_Pymatgen import *
from pymatgen.core import Site
import os
import shutil

def reorganize_structures(structure_1 : Structure, structure_2 : Structure, atoms=[], autosort_tol=0.5):
    '''

    :param structure_1_mutable: Structure
        Structure to interpolate between
    :param structure_2_mutable: Structure
        Structure to interpolate between
    :param atoms:
        list of tuples of atoms that should be the same between structures
    :return: Structure
    '''

    # parse Atoms into two lists
    atom_i_1 = []
    atom_i_2 = []
    atoms_1 = []
    atoms_2 = []
    for i_1, i_2 in atoms:
        atom_i_1.append(i_1)
        atom_i_2.append(i_2)
        atoms_1.append(structure_1[i_1])
        atoms_2.append(structure_2[i_2])

    # Remove sites
    structure_1_mutable = structure_1.copy() # type: Structure
    structure_2_mutable = structure_2.copy() # type: Structure
    structure_1_mutable.remove_sites(atom_i_1)
    structure_2_mutable.remove_sites(atom_i_2)

    images = structure_1_mutable.interpolate(structure_2_mutable, 1, autosort_tol=autosort_tol)
    new_s_1 = images[0] # type: Structure
    new_s_2 = images[1] # type: Structure

    for atom in atoms_1: # type: Site
        atom = atom
        new_s_1.append(atom.specie, atom.coords, properties=atom.properties)

    for atom in atoms_2: # type: Site
        atom = atom
        new_s_1.append(atom.specie, atom.coords, properties=atom.properties)

    return (new_s_1, new_s_2)

def nebmake(directory, start, final, images, tolerance=0, ci=False, poscar_override=[]):
    start_POSCAR = os.path.join(start, 'CONTCAR') if os.path.exists(os.path.join(start, 'CONTCAR')) and os.path.getsize(os.path.join(start, 'CONTCAR')) > 0 else os.path.join(start, 'POSCAR')
    final_POSCAR = os.path.join(final, 'CONTCAR') if os.path.exists(os.path.join(final, 'CONTCAR')) and os.path.getsize(os.path.join(final, 'CONTCAR')) > 0 else os.path.join(final, 'POSCAR')

    start_OUTCAR = os.path.join(start, 'OUTCAR')
    final_OUTCAR = os.path.join(final, 'OUTCAR')
    incar = Incar.from_file(os.path.join(start, 'INCAR'))
    kpoints = Kpoints.from_file(os.path.join(start, 'KPOINTS'))
    potcar = Potcar.from_file(os.path.join(start, 'POTCAR'))

    p1 = Poscar.from_file(start_POSCAR)
    p2 = Poscar.from_file(final_POSCAR)
    s1 = p1.structure
    s2 = p2.structure
    if poscar_override:
        atoms = []
        for i in range(int(len(poscar_override)/2)):
            atoms.append( (poscar_override[i*2], poscar_override[i*2+1]))
        (s1, s2) = reorganize_structures(s1, s2, atoms=atoms, autosort_tol=tolerance)
        structures = poscar_override[0].interpolate(poscar_override[1], images, autosort_tol=tolerance)
    structures = s1.interpolate(s2, images, autosort_tol=tolerance)

    incar['ICHAIN'] = 0
    incar['IMAGES'] = images-1
    incar['LCLIMB'] = ci

    i=0
    for s in structures:
        folder = os.path.join(directory, str(i).zfill(2))
        os.mkdir(folder)
        Poscar(s, selective_dynamics=p1.selective_dynamics).write_file(os.path.join(folder, 'POSCAR'))
        if i == 0:
            shutil.copy(start_OUTCAR, os.path.join(folder, 'OUTCAR'))
        if i == images:
            shutil.copy(final_OUTCAR, os.path.join(folder, 'OUTCAR'))
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
    parser.add_argument('-a', '--atom_pairs', help='pair certain atoms', type=int, nargs='*', default=[])
    args = parser.parse_args()
    nebmake(args.directory, args.initial, args.final, args.images+1, args.tolerance, args.climbing_image, poscar_override=args.atom_pairs)