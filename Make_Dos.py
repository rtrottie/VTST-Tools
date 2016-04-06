#!/usr/bin/env python

import csv
import sys
from pymatgen.io.vasp import *
import numpy as np
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('vasprun', help='Location of vasprun.xml file (default: ./vasprun.xml)',
                        default='vasprun.xml')
    parser.add_argument('-g', '--group', help='Each instance of the -g flag will combine all provided elements into a column.  Example : -g O 1-3:d 6:s,p will have a summed DOS of all Oxygen Atoms and, d orbitals of atoms 1, 2, 3, and 4, and s and p orbitals of atom 6',
                        action='append', nargs='*')
    parser.add_argument('-s', help='same as group, but automatically does s orbitals',
                        action='append', nargs='*')
    parser.add_argument('-p', help='same as group, but automatically does p orbitals',
                        action='append', nargs='*')
    parser.add_argument('-d', help='same as group, but automatically does d orbitals',
                        action='append', nargs='*')
    parser.add_argument('-f', help='same as group, but automatically does f orbitals',
                        action='append', nargs='*')
    parser.add_argument('-e', '--eg', help='same as group, but automatically does eg orbitals',
                        action='append', nargs='*')
    parser.add_argument('-t', '--t2g', help='same as group, but automatically does t2g orbitals',
                        action='append', nargs='*')
    args = parser.parse_args()

def make_dos(vasprun, groups=[], output='DOS.csv'):
    v = Vasprun(vasprun, parse_eigen=False)
    tdos = v.complete_dos
    dos = []
    energies = list(map(lambda x: x-tdos.efermi, tdos.energies.tolist()))
    m = determine_scale_of_frontier_bands(energies, tdos.densities[1], tdos.densities[-1])
    scaling_factors = [1.5/m]
    columns = [energies, list(map(lambda x: x/m*1.5, tdos.densities[1])), list(map(lambda x: -x/m*1.5, tdos.densities[-1]))]
    title = ['Energy', 'Total +', 'Total -']
    for group in groups:
        atom_orbital = []
        for set in group:
            atom_indices = []
            if ':' in set:   # Determine which orbitals to add
                orbitals = set.split(':')[1].split(',')
                atoms = set.split(':')[0]
            else:
                orbitals = ['all']
                atoms = set

            if '-' in set:  # Determine what atom indicies to work with
                start_end = set.split('-')
                atom_indices = range(int(start_end[0]), int(start_end[1])+1)
            else:
                try:
                    atom_indices = [int(set)-1]
                except:
                    atom_indices = np.where(np.array(v.atomic_symbols) == set)[0].tolist()

            for orbital in orbitals:  #  Set up atom_orbital argument for later use
                atom_orbital = atom_orbital + list(map(lambda x : (x, orbital), atom_indices))

        up_down = list(map(lambda site: get_dos(tdos, site, orbital), atom_orbital))
        up = list(map(lambda dos: dos.densities[1].tolist(), up_down))
        up = reduce(lambda x,y: list(map(lambda i: x[i]+y[i], range(len(x)))), up)
        down = list(map(lambda dos: dos.densities[-1].tolist(), up_down))
        down = reduce(lambda x,y: list(map(lambda i: x[i]+y[i], range(len(x)))), down)
        m = determine_scale_of_frontier_bands(energies, up, down)
        scaling_factors.append(1/m)
        norm_up = list(map(lambda x: x/m, up))
        norm_down = list(map(lambda x: -x/m, down))
        title.append(' '.join(group) + ' +')
        title.append(' '.join(group) + ' -')
        columns.append(norm_up); columns.append(norm_down)




        csv_list = range(len(columns[0]))
        title.append('Scaling Factors')
        columns.append(scaling_factors)
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

        with open(output, 'w') as f:
            f.write(csv_str)





def sum_orbitals(pdos, atoms, orbitals=['all']):
    pdos_reduced = list(map(lambda x: pdos[x], atoms))
    if orbitals == ['all']:
        orbitals = pdos[0].keys()
    for orbital in orbitals:
        if orbital == 'all':
            all_orbitals = list(map(lambda x: pdos[x], pdos[0].keys()))
            'total'
    return

def determine_scale_of_frontier_bands(energies, up, down):
    fermi_i = len(filter(lambda x: x < 0, energies)) - 1
    m = max(max(up), max(down))
    counter = 0
    bg = True
    for i in range(fermi_i, -1, -1):
        if up[i] < m/1000 and down[i] < m/1000:
            if counter == 5:
                break
            elif bg:
                pass
            else:
                counter += 1
        else:
            bg = False
            counter = 0
    bot = i
    counter = 0
    bg = True
    for i in range(fermi_i, len(energies)):
        if up[i] < m/1000 and down[i] < m/1000:
            if counter == 5:
                break
            elif bg:
                pass
            else:
                counter += 1
        else:
            bg = False
            counter = 0
    top = i
    return max(max(up[bot:top]), max(down[bot:top]))

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






