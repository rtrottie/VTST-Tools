#!/usr/bin/env python
from Classes_Pymatgen import *
from pymatgen.transformations.site_transformations import *
import os
import sys
import argparse

def reorder_vacancies(pos1, pos2, coord1, coord2, writeDir):
    if coord1 < coord2:
        coord2 = coord2 - 1
    elif coord2 < coord1:
        coord1 = coord1 - 1
    else:
        raise Exception('Same Coords Provided')
    p1 = Poscar.from_file(pos1)
    p2 = Poscar.from_file(pos2)
    sp1 = p1.structure.sites[coord2 - 1].specie.symbol
    sp2 = p2.structure.sites[coord1 - 1].specie.symbol
    f1 = p1.structure.sites[coord2 - 1].frac_coords
    f2 = p2.structure.sites[coord1 - 1].frac_coords
    if (sp1 != sp2):
        raise Exception('species 1 does not equal species 2')

    ins1 = InsertSitesTransformation([sp1], [f1])
    ins2 = InsertSitesTransformation([sp2], [f2])
    r1 = RemoveSitesTransformation([coord2 - 1])
    r2 = RemoveSitesTransformation([coord1 - 1])

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
    parser.add_argument('atom_1', help='migrating atom in struct_1 (1 indexed by default)')
    parser.add_argument('atom_2', help='migrating atom in struct_2 (1 indexed by default)')
    parser.add_argument('-d', '--directory', help='directory to write too')

    if os.path.isfile(start):
        start_file = start
        start_folder = os.path.dirname(start)
    else:
        start_file = os.path.join(start, 'CONTCAR') if os.path.exists(os.path.join(start, 'CONTCAR')) else os.path.join(start, 'POSCAR')
        start_folder = start

if os.path.basename(sys.argv[0]) == 'Vacancy_Correction.py':
    if len(sys.argv) < 2:
        raise Exception('Not Enough Arguments Provided\n need: POSCAR_1 POSCAR_2 Atom_1 Atom_2 [Dir]')
    elif len(sys.argv) == 5:
        reorder_vacancies(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), os.path.abspath('.'))
    elif len(sys.argv) == 6:
        reorder_vacancies(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), os.path.abspath(sys.argv[5]))
    else:
        raise Exception('Too Many Arguments\n need: POSCAR_1 POSCAR_2 Atom_1 Atom_2 [Dir]')