#!/usr/bin/env python
# Compares two outputs to check for differences in final states

# Usage: Verify.py Dir_1 [Dir_2]

import sys
import os
from Classes_Pymatgen import *
from pymatgen.io.vasp.outputs import *

def check_atoms(run1, run2):
    o1 = Outcar(os.path.join(run1, 'OUTCAR'))
    o2 = Outcar(os.path.join(run2, 'OUTCAR'))
    v1 = Vasprun(os.path.join(run1, 'vasprun.xml'))
    v2 = Vasprun(os.path.join(run2, 'vasprun.xml'))

    for i in range(len(v1.atomic_symbols)):
        if v1.atomic_symbols[i] != v2.atomic_symbols[i]:
            return False
    return True

def check_magnetization(run1, run2, check_diff = 0.005, check_per = 0.05):
    o1 = Outcar(os.path.join(run1, 'OUTCAR'))
    o2 = Outcar(os.path.join(run2, 'OUTCAR'))
    v1 = Vasprun(os.path.join(run1, 'vasprun.xml'))
    v2 = Vasprun(os.path.join(run2, 'vasprun.xml'))

    orbitals = ['p', 's', 'd', 'tot']
    difference = []
    prev_count = 0
    this_count = 0
    this_ion = ''
    for i in range(len(o1.magnetization)):
        if this_ion != v1.atomic_symbols[i]:
            prev_count = prev_count + this_count
            this_count = 0
            this_ion = v1.atomic_symbols[i]
        for orb in orbitals:
            m1 = o1.magnetization[i][orb]
            m2 = o2.magnetization[i][orb]
            if abs(m1-m2) < check_diff:
                continue
            elif (abs(m1) < 0.001 ) or (abs(m2) < 0.001):
                difference.append([v1.atomic_symbols[i], i+1, orb, m1, m2])
            elif abs(m1 - m2) / min(abs(m1),abs(m2)) <= check_per:
                continue
            else:
                difference.append([v1.atomic_symbols[i], i-prev_count+1, i+1, orb, m1, m2])
        this_count = this_count + 1
    return difference

def check_charge(run1, run2, check_diff = 0.025, check_per = 0.00):
    o1 = Outcar(os.path.join(run1, 'OUTCAR'))
    o2 = Outcar(os.path.join(run2, 'OUTCAR'))
    v1 = Vasprun(os.path.join(run1, 'vasprun.xml'))
    v2 = Vasprun(os.path.join(run2, 'vasprun.xml'))

    orbitals = ['p', 's', 'd', 'tot']
    difference = []
    prev_count = 0
    this_count = 0
    this_ion = ''
    for i in range(len(o1.charge)):
        if this_ion != v1.atomic_symbols[i]:
            prev_count = prev_count + this_count
            this_count = 0
            this_ion = v1.atomic_symbols[i]
        for orb in orbitals:
            m1 = o1.charge[i][orb]
            m2 = o2.charge[i][orb]
            if abs(m1-m2) < check_diff:
                continue
            elif (abs(m1) < 0.001 ) or (abs(m2) < 0.001):
                difference.append([v1.atomic_symbols[i], i+1, orb, m1, m2])
            elif abs(m1 - m2) / min(abs(m1),abs(m2)) <= check_per:
                continue
            else:
                difference.append([v1.atomic_symbols[i], i-prev_count+1, i+1, orb, m1, m2])
        this_count = this_count + 1
    return difference


def verify_run(run1, run2):
    if not check_atoms(run1, run2):
        return 'Not the same Atoms'
    mag = check_magnetization(run1, run2)
    chg = check_charge(run1, run2)
    return (mag, chg)

if os.path.basename(sys.argv[0]) == 'Verify.py':
    if len(sys.argv) < 2:
        raise Exception('Not Enough Arguments Provided\n need: Dir_1 [This_Dir]')
    elif len(sys.argv) == 2:
        differences = verify_run(sys.argv[1], os.path.abspath('.'))
    elif len(sys.argv) == 3:
        differences = verify_run(sys.argv[1], sys.argv[2])
    else:
        raise Exception('Too Many Arguments Provided\n need: Dir_1 [This_Dir]')

    print('Magnetization\n')
    for dif in differences[0]:
        print(' '.join(dif) + '\n')

    print('Charge\n')
    for dif in differences[1]:
        print(' '.join(dif) + '\n')
