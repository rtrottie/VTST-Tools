#!/usr/bin/env python
# Freezes all atoms around a specified atom, by default, 4 angstrom radius (chosen arbitrarily).  Creates file named
# selective_dynamics which saves the previous selective_dynamics to be restored later.  Saves POSCAR to current folder

# Usage: Freeze_Atoms [Dir] Atom_# [Unfrozen_Distance]
from pymatgen.io.vasp.inputs import Poscar
from Classes_Pymatgen import get_string_more_sigfig
import os
import sys
import argparse
import pymatgen.io.vasp


def freeze_atoms_except_neighbors(dir : str, atom : int, unfrozen_dist=4):
    '''

    #!/usr/bin/env python
    Freezes all atoms around a specified atom, by default, 4 angstrom radius (chosen arbitrarily).  Creates file named
    selective_dynamics which saves the previous selective_dynamics to be restored later.  Saves POSCAR to current folder

    :param dir: Directory to freeze atoms in
    :param atom: number of atom in POSCAR of dir
    :param unfrozen_dist: radius to freeze atom in
    '''
    poscar = Poscar.from_file(os.path.join(dir, 'POSCAR'))
    if os.path.exists(os.path.join(dir, 'selective_dynamics')): # if atoms are alread frozen, we don't want to overwrite original SD
        raise Exception('Selective Dynamics File Exists')
    sd_orig = poscar.selective_dynamics
    with open(os.path.join(dir, 'selective_dynamics'),'w+') as f:
        f.write(str(sd_orig))
    neigh = poscar.structure.get_neighbors(poscar.structure.sites[atom], unfrozen_dist, True) # find nearby atoms
    neigh = list(map(lambda x: x[2], neigh)) # get indices
    neigh.append(atom-1) # add center atom
    for i in range(len(sd_orig)): # freeze all atoms not in neigh
        if i not in neigh:
            sd_orig[i] = [False, False, False]
    poscar.selective_dynamics = sd_orig
    Poscar.get_string = get_string_more_sigfig
    poscar.write_file(os.path.join(dir, 'POSCAR'))
    return

def unfreeze_atoms(directory, sd_file='.selective_dynamics'):
    '''
    Unfreeze atoms in given directory
    :param directory:
    :param sd_file:
        file that is a str(list) of selective dynamics
    :return:
    '''

    # Parse sd_file
    with open(sd_file) as f:
        sd = [['True' in x] * 3 for x in f.read().split('],')]

    poscar = Poscar.from_file(os.path.join('directory', 'POSCAR')) # type: Poscar
    poscar.selective_dynamics = sd
    poscar.write_file('POSCAR')
    return




if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('atom', help='atom number (0 indexed) to freeze from',
                        default=-1, nargs="?")
    parser.add_argument('-r', '--radius', help='radius to freeze around (default 4)')
    parser.add_argument('-d', '--directory', help='Input directory (default = ".")',
                        default='.')
    parser.add_argument('-u', '--undo', help='Read selective_dynamics file and undo frozen atoms',
                        action='store_true')
    parser.add_argument('--sd', '--selective_dynamics', help='Selective Dynamics file', default='.selective_dynamics')
    args = parser.parse_args()

    if args.undo:
        unfreeze_atoms(args.directory, sd_file=args.selective_dynamics)
    else:
        freeze_atoms_except_neighbors(args.directory, args.atom, args.radius)