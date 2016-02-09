#!/usr/bin/env python
# Removes specified atoms from the run.  Updates INCAR afterwards with values from the cfg.py.


# Usage: Remove_Atoms.py Previous_Dir [This_Dir] [Atom] Atom_#s
from Substitute_Atoms import *
import argparse

parser.add_argument('-t', '--time', help='walltime for run (integer number of hours)',
                    type=int, default=0)
if len(sys.argv) < 3:
    raise Exception('Not Enough Arguments Provided\n need: Previous_Dir [This_Dir] [Atom] Atom_#s')
prev_NEB_dir = sys.argv[1]
try:
    this_NEB_dir = os.getcwd()
    atom_nums = list(map(lambda x: int(x)-1, sys.argv[2:len(sys.argv)]))
    atom = None
except:
    if os.path.isdir(sys.argv[2]):
        this_NEB_dir = sys.argv[2]
        atom = None
        try:
            atom_nums = list(map(lambda x: int(x)-1, sys.argv[3:len(sys.argv)]))
            atom = None
        except:
            atom = sys.argv[3]
            atom_nums = list(map(lambda x: int(x)-1, sys.argv[4:len(sys.argv)]))
    else:
        this_NEB_dir = os.getcwd()
        atom_nums = list(map(lambda x: int(x)-1, sys.argv[3:len(sys.argv)]))
        atom = sys.argv[2]

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
