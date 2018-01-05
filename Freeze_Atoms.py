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


def freeze_atoms_except_neighbors(input : str, atom : int, output : str, invert=False, unfrozen_dist=4):
    '''

    #!/usr/bin/env python
    Freezes all atoms around a specified atom, by default, 4 angstrom radius (chosen arbitrarily).  Creates file named
    selective_dynamics which saves the previous selective_dynamics to be restored later.  Saves POSCAR to current folder

    :param input: Directory to freeze atoms in
    :param atom: number of atom in POSCAR of dir
    :param invert: Normally will leave all atoms in radius able to move, setting this to true will freeze all atoms in radius
    :param unfrozen_dist: radius to freeze atom in
    '''
    atom = atom-1
    poscar = Poscar.from_file(input)
    if os.path.exists(os.path.join(input, 'selective_dynamics')): # if atoms are alread frozen, we don't want to overwrite original SD
        raise Exception('Selective Dynamics File Exists')
    sd_orig = poscar.selective_dynamics if poscar.selective_dynamics != None else [[True, True, True]]*len(poscar.structure)
    with open(os.path.join(input, 'selective_dynamics'), 'w+') as f:
        f.write(str(sd_orig))
    neigh = poscar.structure.get_neighbors(poscar.structure.sites[atom], unfrozen_dist, True) # find nearby atoms
    neigh = list(map(lambda x: x[2], neigh)) # get indices
    neigh.append(atom) # add center atom
    if invert: # if radius should be frozen
        for i in range(len(sd_orig)): # freeze all atoms not in neigh
            if i in neigh:
                sd_orig[i] = [False, False, False]
    else: # radius should be unfrozen
        for i in range(len(sd_orig)): # freeze all atoms not in neigh
            if i not in neigh:
                sd_orig[i] = [False, False, False]
    poscar.selective_dynamics = sd_orig
    Poscar.get_string = get_string_more_sigfig
    poscar.write_file(output)
    return

def unfreeze_atoms(input, sd_file='.selective_dynamics'):
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

    poscar = Poscar.from_file(input) # type: Poscar
    poscar.selective_dynamics = sd
    poscar.write_file(input)
    return




if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('atom', help='atom number (1 indexed) to unfreeze around',
                        default=None, nargs="?", type=int)
    parser.add_argument('-r', '--radius', help='radius to freeze around (default 4)',
                        type=float, default=4)
    parser.add_argument('--input', help='input POSCAR file (default = "POSCAR")',
                        default='POSCAR')
    parser.add_argument('--output', help='output POSCAR file (default = "POSCAR.sd.vasp")',
                        default='POSCAR.sd.vasp')
    parser.add_argument('-u', '--undo', help='Read selective_dynamics file and undo frozen atoms',
                        action='store_true')
    parser.add_argument('-i', '--invert', help='freeze atoms around index, instead of leaving radius available to move',
                        action='store_true')
    parser.add_argument('--sd', '--selective_dynamics', help='Selective Dynamics file', default='./selective_dynamics')
    args = parser.parse_args()

    if args.undo:
        unfreeze_atoms(args.input, sd_file=args.sd)
    else:
        freeze_atoms_except_neighbors(args.input, args.output, args.atom, args.invert, args.radius)