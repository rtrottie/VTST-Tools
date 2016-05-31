#!/usr/bin/env python
# Replaces specified atoms in the run.  Updates INCAR afterwards with values from the cfg.py.
# TODO:  Stop this from messing with the MAGMOM, U parameter
# TODO: Stop from changing POTCAR _pv _s _sv, etc...

# Usage: Substitute_Atoms.py Previous_Dir [This_Dir] Atom_#s New_Atom
from pymatgen.transformations.site_transformations import ReplaceSiteSpeciesTransformation, RemoveSitesTransformation
from Classes_Pymatgen import *
from Helpers import *
import sys
import os

def remove_atom(prev_dir, this_dir, atom_nums, optional_files=None):
    Poscar.get_string = get_string_more_sigfig
    vasp = VaspInput.from_directory(prev_dir, optional_files)
    transformation = RemoveSitesTransformation(atom_nums)

    # Modifying POSCAR
    sd = vasp['POSCAR'].selective_dynamics
    if 'MAGMOM' in vasp['INCAR']:
        mm = vasp["INCAR"]['MAGMOM']
    else:
        mm = False
    atom_nums.sort(reverse=True)
    if sd:
        for i in atom_nums:
            sd.pop(i)
    if mm:
        for i in atom_nums:
            mm.pop(i)
    vasp['POSCAR'].structure = transformation.apply_transformation(vasp['POSCAR'].structure)
    vasp['POSCAR'].comment = ' '.join(vasp['POSCAR'].site_symbols)
    if sd:
        vasp['POSCAR'].selective_dynamics = sd

    # Modifying INCAR
    #update_incar(vasp['POSCAR'].structure, vasp['INCAR'])
    if mm:
        vasp["INCAR"]['MAGMOM'] = mm

    vasp.write_input(this_dir)
    return

def remove_atom_arbitrary(prev_dir, this_dir, atom_nums, atom=None):
    job = getJobType(prev_dir)
    print('Creating new ' + str(job) + ' Job at ' + this_dir)
    if atom != None:
        poscar = Poscar.from_file(os.path.join(prev_dir, 'POSCAR'))
        plus = 0
        for i in range(len(poscar.site_symbols)):
            if atom == poscar.site_symbols[i]:
                break
            else:
                plus = plus + poscar.natoms[i]
        atom_nums = list(map(lambda x: x + plus, atom_nums))
    if job == 'Dimer':
        remove_atom(prev_dir, this_dir, atom_nums, {'MODECAR': Modecar})
    elif job == 'Standard':
        remove_atom(prev_dir, this_dir, atom_nums)
    else:
        raise Exception('Not Yet Implemented Jobtype is:  ' + str(job))
    return

def replace_atom(prev_dir, this_dir, atom_nums, new_atom, optional_files=None):
    Poscar.get_string = get_string_more_sigfig
    vasp = VaspInput.from_directory(prev_dir, optional_files)
    atom_mapping = {k-1:new_atom for k in atom_nums}
    transformation = ReplaceSiteSpeciesTransformation(atom_mapping)

    # Modifying POSCAR
    sd = vasp['POSCAR'].selective_dynamics
    vasp['POSCAR'].structure = transformation.apply_transformation(vasp['POSCAR'].structure)
    vasp['POSCAR'].comment = ' '.join(vasp['POSCAR'].site_symbols)
    if sd:
        vasp['POSCAR'].selective_dynamics = sd

    # Creating new POTCAR
    vasp['POTCAR'] = Potcar(vasp['POSCAR'].site_symbols)

    # Modifying INCAR
    update_incar(vasp['POSCAR'].structure, vasp['INCAR'])

    vasp.write_input(this_dir)
    return

def replace_atom_NEB(prev_NEB_dir, this_NEB_dir, atom_nums, new_atom):
    NEB = VaspNEBInput.from_directory(prev_NEB_dir, True)
    atom_mapping = {k-1:new_atom for k in atom_nums}
    transformation = ReplaceSiteSpeciesTransformation(atom_mapping)
    for i in range(len(NEB['POSCARs'])):
        sd = NEB['POSCARs'][i].selective_dynamics
        NEB['POSCARs'][i].structure = transformation.apply_transformation(NEB['POSCARs'][i].structure)
        NEB['POSCARs'][i].comment = ' '.join(NEB['POSCARs'][i].site_symbols)
        NEB['POSCARs'][i].selective_dynamics = sd

    NEB['POTCAR'] = Potcar(NEB['POSCARs'][i].site_symbols)


    update_incar(vasp['POSCAR'].structure, vasp['INCAR'])

    NEB.write_input(this_NEB_dir)
    return

def replace_atom_arbitrary(prev_dir, this_dir, atom_nums, new_atom):
    job = getJobType(prev_dir)
    print('Creating new ' + str(job) + ' Job at ' + this_dir)
    if job == 'NEB':
        replace_atom_NEB(prev_dir, this_dir, atom_nums, new_atom)
    elif job == 'Dimer':
        replace_atom(prev_dir, this_dir, atom_nums, new_atom, {'MODECAR': Modecar})
    elif job == 'Standard':
        replace_atom(prev_dir, this_dir, atom_nums, new_atom)
    else:
        raise Exception('Not Yet Implemented Jobtype is:  ' + str(job))
    return

def switch_atom(prev_dir, this_dir, atoms, optional_files=None):
    poscar = Poscar.from_file(os.path.join(prev_dir, 'POSCAR'))
    temp_dir = os.path.join(this_dir, 'temp')
    for i in range(len(atoms)/2):
        a1 = str(poscar.structure.species[atoms[2*i]-1])
        a2 = str(poscar.structure.species[atoms[2*i+1]-1])
        replace_atom(prev_dir, temp_dir, [atoms[2*i]], a2, optional_files)
        replace_atom(temp_dir, this_dir, [atoms[2*i+1]], a1, optional_files)
        os.system('rm -r ' + temp_dir)

def switch_atom_arbitrary(prev_dir, this_dir, atom_nums):
    job = getJobType(prev_dir)
    print('Creating new ' + str(job) + ' Job at ' + this_dir)
    if job == 'NEB':
        switch_atom_NEB(prev_dir, this_dir, atom_nums)
    elif job == 'Dimer':
        switch_atom(prev_dir, this_dir, atom_nums, {'MODECAR': Modecar})
    elif job == 'Standard':
        switch_atom(prev_dir, this_dir, atom_nums)
    else:
        raise Exception('Not Yet Implemented Jobtype is:  ' + str(job))
    return


if os.path.basename(sys.argv[0]) == 'Substitute_Atoms.py':
    if len(sys.argv) < 4:
        raise Exception('Not Enough Arguments Provided\n need: Previous_Dir [This_Dir] Atom_#s New_Atom')
    prev_NEB_dir = sys.argv[1]
    try:
        int(sys.argv[2])
        this_NEB_dir = os.getcwd()
        atom_nums = map(lambda x: int(x), sys.argv[2:len(sys.argv)-1])
    except:
        this_NEB_dir = sys.argv[2]
        atom_nums = map(lambda x: int(x), sys.argv[3:len(sys.argv)-1])
    new_atom = sys.argv[len(sys.argv)-1]
    replace_atom_arbitrary(prev_NEB_dir, this_NEB_dir, atom_nums, new_atom)
