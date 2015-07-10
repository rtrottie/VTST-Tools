#!/usr/bin/env python
from pymatgen.io.vaspio.vasp_input import *
from pymatgen.transformations.site_transformations import ReplaceSiteSpeciesTransformation, RemoveSitesTransformation
from Classes_Pymatgen import *
from Helpers import *
import sys
import os
import cfg
import mock

def remove_atom(prev_dir, this_dir, atom_nums, optional_files=None):
    Poscar.get_string = get_string_more_sigfig
    vasp = VaspInput.from_directory(prev_dir, optional_files)
    transformation = RemoveSitesTransformation(atom_nums)

    # Modifying POSCAR
    sd = vasp['POSCAR'].selective_dynamics
    atom_nums.sort(reverse=True)
    for i in atom_nums:
        sd.pop(i)
    vasp['POSCAR'].structure = transformation.apply_transformation(vasp['POSCAR'].structure)
    vasp['POSCAR'].comment = ' '.join(vasp['POSCAR'].site_symbols)
    vasp['POSCAR'].selective_dynamics = sd

    # Creating new POTCAR
    vasp['POTCAR'] = Potcar(vasp['POSCAR'].site_symbols)

    vasp.write_input(this_dir)
    return

def remove_atom_arbitrary(prev_dir, this_dir, atom_nums):
    job = getJobType(prev_dir)
    print('Creating new ' + str(job) + ' Job at ' + this_dir)
    if job == 'NEB':
        remove_atom_NEB(prev_dir, this_dir, atom_nums)
    elif job == 'Dimer':
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
    vasp['POSCAR'].selective_dynamics = sd

    # Creating new POTCAR
    vasp['POTCAR'] = Potcar(vasp['POSCAR'].site_symbols)

    # Modifying INCAR
    for k in vasp['INCAR'].keys():
        if k in cfg.INCAR:
            vasp['INCAR'][k] = map(lambda a: cfg.INCAR[k][a] if a in cfg.INCAR[k] else cfg.INCAR[k]['default'],
                                    vasp['POSCAR'].site_symbols)

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

    for k in NEB['INCAR'].keys():
        if k in cfg.INCAR:
            NEB['INCAR'][k] = map(lambda a: cfg.INCAR[k][a] if a in cfg.INCAR[k] else cfg.INCAR[k]['default'],
                                    NEB['POSCARs'][0].site_symbols)

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
        a1 = str(poscar.structure.species[atoms[2*i]])
        a2 = str(poscar.structure.species[atoms[2*i+1]])
        replace_atom(prev_dir, temp_dir, [atoms[2*i]], a2)
        replace_atom(temp_dir, this_dir, [atoms[2*i+1]], a1)
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
        this_NEB_dir = os.getcwd()
        atom_nums = map(lambda x: int(x), sys.argv[2:len(sys.argv)-1])
    except:
        this_NEB_dir = sys.argv[2]
        atom_nums = map(lambda x: int(x), sys.argv[3:len(sys.argv)-1])
    new_atom = sys.argv[len(sys.argv)-1]
    replace_atom_arbitrary(prev_NEB_dir, this_NEB_dir, atom_nums, new_atom)
