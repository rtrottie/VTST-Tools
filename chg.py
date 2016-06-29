#!/usr/bin/env python

import argparse
from pymatgen.io.vasp.outputs import *


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', type=str, default='CHGCAR')
args = parser.parse_args()

c = Chgcar.from_file(args.file)
for v in range(3):
    with open(args.file.lower() + '.' + str(v) + '.txt', 'w') as f:
        f.writelines([ str(x) + '\n' for x in c.get_average_along_axis(v) ])