#!/usr/bin/env python
# Removes specified atoms from the run.  Updates INCAR afterwards with values from the cfg.py.


# Usage: Remove_Atoms.py Previous_Dir [This_Dir] [Atom] Atom_#s
from Substitute_Atoms import *
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help='input VASP directory')
    parser.add_argument('atom_nums', 'list of atom numbers (default : 1 indexed) to remove',
                        nargs='*', type=int)
    parser.add_argument('-o', '--output_dir', help='output VASP directory (Default : ".")', default='.')
    parser.add_argument('-a', '--atom', help='when specifed removes ith member of specified atom instead of ith atom overall',
                        default=None)
    parser.add_argument('-z', '--zero_indexed', help='specifies that provided list is 0 indexed',
                        action='store_true')

    args = parser.parse_args()

    if not args.zero_indexed:
        args.atom_nums = list(map(lambda x: x-1, args.atom_nums))
    remove_atom_arbitrary(args.input_dir, args.output_dir, atom_nums, args.atom)
