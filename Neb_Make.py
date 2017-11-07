#!/usr/bin/env python
#TODO:  Ask to sort
import argparse
from Classes_Pymatgen import *
from pymatgen.core import PeriodicSite
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
    atom_is_1 = []
    atom_is_2 = []
    atoms_1 = []
    atoms_2 = []
    for i_1, i_2 in atoms: # Make ordered lists of atom indicies
        atom_is_1.append(i_1)
        atom_is_2.append(i_2)
        atoms_1.append(structure_1[i_1])
        atoms_2.append(structure_2[i_2])

    # Remove sites
    structure_2_mutable = structure_2.copy() # type: Structure
    structure_2_mutable.remove_sites(atom_is_2)

    if autosort_tol > 0:
        structure_1_mutable = structure_1.copy() # type: Structure
        structure_1_mutable.remove_sites(atom_is_1)
        images = structure_1_mutable.interpolate(structure_2_mutable, 1, autosort_tol=autosort_tol)
        new_s_1 = images[0] # type: Structure
        new_s_2 = images[1] # type: Structure

        for atom in atoms_1: # type: PeriodicSite
            atom = atom
            new_s_1.append(atom.specie, atom.frac_coords, properties=atom.properties)

        for atom in atoms_2: # type: PeriodicSite
            atom = atom
            new_s_2.append(atom.specie, atom.frac_coords, properties=atom.properties)

        def sort_fxn(atom):
            # return correct order for structure_1
            i = 0
            for s1_atom in structure_1: # type: PeriodicSite
                if s1_atom.distance(atom) < 0.001 : # If site matches site in structure_1
                    return i
                i = i+1

            # return correct order for structure_2
            i=0
            for s2_atom in atoms_2:
                if s2_atom.distance(atom) < 0.01: # If atom should have been moved
                    return atom_is_1[i] # where it should be in structure 1
                i = i+1
            i = 0
            for s1_atom in structure_1: # type: PeriodicSite
                if s1_atom.distance(atom) < autosort_tol : # If site is within auto_sort_tol of structure_1
                    return i
                i = i+1
            raise Exception('FAILED SORT on: {}'.format(atom))
        new_s_1.sort(sort_fxn)
        new_s_2.sort(sort_fxn)
    else:
        new_s_1 = structure_1
        new_s_2 = structure_2_mutable
        for _ in range(len(atom_is_1)): # Going to insert based on position in structure 1
            i = atom_is_1.index(min(atom_is_1)) # find minimum index (to preserve correct ordering)
            atom = structure_2[atom_is_2[i]] # type: PeriodicSite  ;  get atom from original structure
            new_s_2.insert(atom_is_2[i], atom.specie, atom.frac_coords, properties=atom.properties)
            for l in [atom_is_1, atom_is_2]: # remove minimum index
                l.pop(i)


    return (new_s_1, new_s_2)

def nebmake(directory, start, final, images, tolerance=0, ci=False, poscar_override=[], linear=False, write=True):

    if type(start) == str:
        start_POSCAR = os.path.join(start, 'CONTCAR') if os.path.exists(os.path.join(start, 'CONTCAR')) and os.path.getsize(os.path.join(start, 'CONTCAR')) > 0 else os.path.join(start, 'POSCAR')
        final_POSCAR = os.path.join(final, 'CONTCAR') if os.path.exists(os.path.join(final, 'CONTCAR')) and os.path.getsize(os.path.join(final, 'CONTCAR')) > 0 else os.path.join(final, 'POSCAR')
        p1 = Poscar.from_file(start_POSCAR)
        p2 = Poscar.from_file(final_POSCAR)
        s1 = p1.structure
        s2 = p2.structure
    else:
        s1 = start
        s2 = final
    # s1.sort()
    # s2.sort()
    atoms = []
    if poscar_override:
        for i in range(int(len(poscar_override)/2)):
            atoms.append( (poscar_override[i*2], poscar_override[i*2+1]) )
        (s1, s2) = reorganize_structures(s1, s2, atoms=atoms, autosort_tol=tolerance)
        tolerance=0
    try:
        structures = s1.interpolate(s2, images, autosort_tol=tolerance)
    except:
        a=input('Failed.  Type y to sort --> ')
        if a=='y':
            s1.sort()
            s2.sort()
        structures = s1.interpolate(s2, images, autosort_tol=tolerance)


    if not linear:
        from pymatgen.io.ase import AseAtomsAdaptor
        from ase.neb import NEB
        structures_ase = [ AseAtomsAdaptor.get_atoms(struc) for struc in structures ]
        neb = NEB(structures_ase)
        neb.interpolate('idpp') # type: NEB
        structures = [ AseAtomsAdaptor.get_structure(atoms) for atoms in neb.images ]

    if write:
        start_OUTCAR = os.path.join(start, 'OUTCAR')
        final_OUTCAR = os.path.join(final, 'OUTCAR')
        incar = Incar.from_file(os.path.join(start, 'INCAR'))
        kpoints = Kpoints.from_file(os.path.join(start, 'KPOINTS'))
        potcar = Potcar.from_file(os.path.join(start, 'POTCAR'))
        incar['ICHAIN'] = 0
        incar['IMAGES'] = images-1
        incar['LCLIMB'] = ci

        for i, s in enumerate(structures):
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
    return structures

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
    parser.add_argument('--linear', help='Use linear interpolation instead of idpp', action='store_true')
    parser.add_argument('--sp_opt', help='Set up single_point optimization', action='store_true')
    args = parser.parse_args()
    if args.sp_opt:
        print('Initializing Structures')
        nebmake(args.directory, args.initial, args.final, 1, args.tolerance, linear=True, poscar_override=args.atom_pairs)
        for f in ['WAVECAR', 'CHGCAR']:
            print('Copying {}s'.format(f))
            shutil.copy(os.path.join(args.initial, f), os.path.join(args.directory, '00', f))
            shutil.copy(os.path.join(args.final, f), os.path.join(args.directory, '01', f))
        shutil.move('00', '0000')
        shutil.move('01', '1000')
        shutil.copy('0000/POSCAR', 'POSCAR.1')
        shutil.copy('1000/POSCAR', 'POSCAR.2')
        shutil.copy(os.path.join(args.initial, 'vasprun.xml'), '0000')
        shutil.copy(os.path.join(args.final, 'vasprun.xml'), '1000')
        i = Incar.from_file(os.path.join(args.directory, 'INCAR'))
        del i['IMAGES']
        del i['ICHAIN']
        del i['LCLIMB']
        i.write_file(os.path.join(args.directory, 'INCAR'))
    else:
        nebmake(args.directory, args.initial, args.final, args.images+1, args.tolerance, args.climbing_image, poscar_override=args.atom_pairs, linear=args.linear)