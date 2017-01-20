#!/usr/bin/env python
# Freezes all atoms around a specified atom, by default, 4 angstrom radius (chosen arbitrarily).  Creates file named
# selective_dynamics which saves the previous selective_dynamics to be restored later.  Saves POSCAR to current folder

# Usage: Freeze_Atoms [Dir] Atom_# [Unfrozen_Distance]
from pymatgen.io.vasp.inputs import Poscar
from Classes_Pymatgen import get_string_more_sigfig
import os
import sys
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

#TODO: write unfreeze atoms


if os.path.basename(sys.argv[0]) == 'Freeze_Atoms.py':
    if len(sys.argv) < 2:
        raise Exception('Not Enough Arguments Provided\n need: [Dir] Atom_#s [Distance]')
    elif len(sys.argv) == 2:
        dir = os.getcwd()
        atom = int(sys.argv[1])
        unfrozen_dist = 4
    elif len(sys.argv) == 3:
        try:
            dir = os.getcwd()
            atom = int(sys.argv[1])
            unfrozen_dist = int(sys.argv[2])
        except:
            dir = int(sys.argv[1])
            atom = int(sys.argv[2])
            unfrozen_dist = 4
    elif len(sys.argv) == 4:
        dir = int(sys.argv[1])
        atom = int(sys.argv[2])
        unfrozen_dist = int(sys.argv[3])
    else:
        raise Exception('Too Many Arguments\n need: [Dir] Atom_#s [Distance]')
    freeze_atoms_except_neighbors(dir, atom, unfrozen_dist)


