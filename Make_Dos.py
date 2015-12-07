#!/usr/bin/env python

import csv
import sys
from pymatgen.io.vasp import *
import numpy as np

v = Vasprun('vasprun.xml', parse_eigen=False)
tdos = v.complete_dos

unformated_doss = sys.argv[1:]

dos = []
headers = []


def sum_orbitals(pdos, atoms, orbitals=['all']):
    pdos_reduced = list(map(lambda x: pdos[x], atoms))
    if orbitals == ['all']:
        orbitals = pdos[0].keys()
    for orbital in orbitals:
        if orbital == 'all':
            all_orbitals = list(map(lambda x: pdos[x], pdos[0].keys()))
            'total'
    return

def get_dos(dos, site, orbital='all'):
    if orbital == 'all':
        return dos.get_site_dos(dos.structure.sites[site])
    elif orbital == 't2g' or orbital == 'e_g' or orbital == 'eg':
        if orbital == 'eg':
            orbital = 'e_g'
        return dos.get_site_t2g_eg_resolved_dos(dos.structure.sites[site])[orbital]
    elif orbital == 's' or orbital == 'p' or orbital == 'd':
        return dos.get_site_spd_dos(dos.structure.sites[site])[orbital.upper()]
    else:
        return dos.get_site_orbital_dos(dos.structure.sites[site], orbital)
m = max(max(tdos.densities[1]), max(tdos.densities[-1]))
scaling_factors = [1.5/m]
columns = [list(map(lambda x: x-tdos.efermi, tdos.energies.tolist())), list(map(lambda x: x/m*1.5, tdos.densities[1])), list(map(lambda x: -x/m*1.5, tdos.densities[-1]))]
title = ['Energy', 'Total +', 'Total -']

for unformated_dos in unformated_doss:
    if ':' in unformated_dos:
        unformated_dos = unformated_dos.split(':')
        orbitals = unformated_dos[1].split(',')
        unformated_dos = unformated_dos[0]
    else:
        orbitals = ['all']
    unformated_atoms = unformated_dos.split(',')
    atoms = []
    for orbital in orbitals:
        for atom in unformated_atoms:
            if '-' in atom:
                start_end = atom.split('-')
                for a in range(int(start_end[0]), int(start_end[1])+1):
                    atoms.append(a-1)
            else:
                try:
                    atoms.append(int(atom)-1)
                except:
                    atoms = atoms + np.where(np.array(v.atomic_symbols) == atom)[0].tolist()
        headers.append(unformated_dos +':' + orbital + ' +')
        headers.append(unformated_dos +':' + orbital + ' -')
        up_down = list(map(lambda site: get_dos(tdos, site, orbital), atoms))
        up = list(map(lambda dos: dos.densities[1].tolist(), up_down))
        up = reduce(lambda x,y: list(map(lambda i: x[i]+y[i], range(len(x)))), up)
        down = list(map(lambda dos: dos.densities[-1].tolist(), up_down))
        down = reduce(lambda x,y: list(map(lambda i: x[i]+y[i], range(len(x)))), down)
        m = max(max(up), max(down))
        scaling_factors.append(1/m)
        norm_up = list(map(lambda x: x/m, up))
        norm_down = list(map(lambda x: -x/m, down))
        title.append(unformated_dos.replace(',','-') + ':' + orbital + ' +')
        title.append(unformated_dos.replace(',','-') + ':' + orbital + ' -')
        columns.append(norm_up); columns.append(norm_down)



csv_list = range(len(columns[0]))
title.append('Scaling Factors')
csv_str = ','.join(title)

for i in range(len(columns[0])):
    csv_str = csv_str + '\n'
    for j in range(len(columns)):
        try:
            csv_str = csv_str + str(columns[j][i])
            if j != len(columns)-1:
                csv_str = csv_str + ','
        except:
            pass

with open('DOS.csv', 'w') as f:
    f.write(csv_str)
