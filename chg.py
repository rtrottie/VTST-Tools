#!/usr/bin/env python

import argparse
from pymatgen.io.vasp.outputs import *


parser = argparse.ArgumentParser()
parser.add_argument('vector', type=int)
args = parser.parse_args()

c = Chgcar.from_file('CHGCAR')
with open('charge_density.txt', 'w') as f:
    f.writelines([ str(x) + '\n' for x in c.get_average_along_axis(args.vector) ])