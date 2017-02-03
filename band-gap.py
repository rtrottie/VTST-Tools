#!/usr/bin/env python

from pymatgen.io.vasp.outputs import *
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('vasprun', help='filename of vasprun.xml file (default: vasprun.xml',
                        nargs='?', default='vasprun.xml')
    args = parser.parse_args()
    v = Vasprun(args.vasprun)
    bs = v.get_band_structure()
    print(bs.get_band_gap())