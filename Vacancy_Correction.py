#!/usr/bin/env python
from Classes_Pymatgen import *
from pymatgen.transformations.site_transformations import *
import os
import sys
import argparse

def reorder_vacancies(pos1, pos2, coord1, coord2, writeDir):
    if coord1 < coord2:
        coord2 = coord2-1
    elif coord2 < coord1:
        coord1 = coord1-1
    else:
        raise Exception('Same Coords Provided')
    p1 = Poscar.from_file(pos1)
    p2 = Poscar.from_file(pos2)
    sp1 = p1.structure.sites[coord2].specie.symbol
    sp2 = p2.structure.sites[coord1].specie.symbol
    f1 = p1.structure.sites[coord2].frac_coords
    f2 = p2.structure.sites[coord1].frac_coords
    if (sp1 != sp2):
        raise Exception('species 1 does not equal species 2')

    ins1 = InsertSitesTransformation([sp1], [f1])
    ins2 = InsertSitesTransformation([sp2], [f2])
    r1 = RemoveSitesTransformation([coord2])
    r2 = RemoveSitesTransformation([coord1])

    temp_s1 = ins1.apply_transformation(r1.apply_transformation(p1.structure))
    temp_s2 = ins2.apply_transformation(r2.apply_transformation(p2.structure))

    # Need to sort list to ensure atoms are the same as before
    # Unfortuantely sort function does not work as intened for this purpose
    sites_1 = []
    sites_2 = []
    site_symbols = p1.site_symbols
    for symbol in site_symbols:
        def match_symbol(site):
            return site.specie.symbol == symbol
        l_1 = [site for site in temp_s1.sites if match_symbol(site)]
        l_2 = [site for site in temp_s2.sites if match_symbol(site)]
        sites_1.extend(l_1)
        sites_2.extend(l_2)
    s1 = Structure.from_sites(sites_1)
    s2 = Structure.from_sites(sites_2)

    p1 = Poscar(s1)
    p2 = Poscar(s2)
    p1.write_file(os.path.join(writeDir, 'POSCAR-1'))
    p2.write_file(os.path.join(writeDir, 'POSCAR-2'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('struct_1', help='structure file or VASP run folder for the first structure')
    parser.add_argument('struct_2', help='structure file or VASP run folder for the second structure')
    parser.add_argument('atom_1', help='migrating atom in struct_1 (1 indexed by default)',
                        type=int)
    parser.add_argument('atom_2', help='migrating atom in struct_2 (1 indexed by default)',
                        type=int)
    parser.add_argument('-d', '--directory', help='directory to write to (default : ".")',
                        default='.')
    parser.add_argument('-z', '--zero_indexed', help='change to zero indexed for supplied atom numbers',
                        action='store_true')
    args = parser.parse_args()

    if not args.zero_indexed:
        args.atom_1 -= 1
        args.atom_2 -= 1

    if os.path.isfile(args.struct_1):
        struct_1 = args.struct_1
    else:
        struct_1 = os.path.join(args.struct_1, 'CONTCAR') if os.path.exists(os.path.join(args.struct_1, 'CONTCAR')) else os.path.join(args.struct_1, 'POSCAR')

    if os.path.isfile(args.struct_2):
        struct_2 = args.struct_2
    else:
        struct_2 = os.path.join(args.struct_2, 'CONTCAR') if os.path.exists(os.path.join(args.struct_2, 'CONTCAR')) else os.path.join(args.struct_2, 'POSCAR')

    reorder_vacancies(struct_1, struct_2, args.atom_1, args.atom_2, args.directory)