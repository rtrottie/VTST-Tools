#!/usr/bin/env python
from Classes_Pymatgen import *
from pymatgen.transformations.site_transformations import *
import os
import sys

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

    s1 = ins1.apply_transformation(r1.apply_transformation(p1.structure))
    s2 = ins2.apply_transformation(r2.apply_transformation(p2.structure))
    p1 = Poscar(s1)
    p2 = Poscar(s2)
    p1.write_file(os.path.join(writeDir, 'POSCAR-1'))
    p2.write_file(os.path.join(writeDir, 'POSCAR-2'))

if os.path.basename(sys.argv[0]) == 'Vacancy_Correction.py':
    if len(sys.argv) < 2:
        raise Exception('Not Enough Arguments Provided\n need: POSCAR_1 POSCAR_2 Atom_1 Atom_2 [Dir]')
    elif len(sys.argv) == 5:
        reorder_vacancies(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], os.path.abspath('.'))
    elif len(sys.argv) == 6:
        reorder_vacancies(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], os.path.abspath(sys.argv[5]))
    else:
        raise Exception('Too Many Arguments\n need: POSCAR_1 POSCAR_2 Atom_1 Atom_2 [Dir]')