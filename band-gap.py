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
    print('Energy:   {} {}'.format(bs.get_band_gap()['energy'], 'direct' if bs.get_band_gap()['direct'] else 'indirect {}'.format(bs.get_band_gap()['transition'])))