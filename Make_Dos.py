#!/usr/bin/env python

import csv
import sys
from pymatgen.io.vasp import *
import numpy as np

v = Vasprun('vasprun.xml', parse_eigen=False)
pdos = v.pdos

unformated_doss = sys.argv[1:]

dos = []
headers = []

for unformated_dos in unformated_doss:
    if ':' in unformated_dos:
        unformated_dos = unformated_dos.split[':']
        orbitals = unformated_dos[1].split[',']
        unformated_dos = unformated_dos[0]
    else:
        orbitals = 'total'
    unformated_atoms = unformated_dos.split(',')
    atoms = []
    for atom in unformated_atoms:
        try:
            atoms.append(int(atom))
        except:
            atoms = atoms + list(np.where(np.array(v.atomic_symbols) == atom))
    def sum_orbitals(pdos, orbitals=[all]):
        for orbital in orbitals:
            if orbital == 'all'
                all_orbitals = map(lambda x: pdos[x]  ,pdos.keys())
                total = map(la)