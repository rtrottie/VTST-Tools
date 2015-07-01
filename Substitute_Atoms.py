from pymatgen.io.vaspio.vasp_input import *
from pymatgen.transformations.site_transformations import ReplaceSiteSpeciesTransformation
from Classes import *
from Helpers import *
import sys
import os
import cfg


def replace_atom(prev_dir, this_dir, atom_nums, new_atom, optional_files=None):
    vasp = VaspInput.from_directory(prev_dir,optional_files)
    atom_mapping = {k:new_atom for k in atom_nums}
    transformation = ReplaceSiteSpeciesTransformation(atom_mapping)

    # Modifying POSCAR
    sd = vasp['POSCAR'].selective_dynamics
    vasp['POSCAR'].structure = transformation.apply_transformation(vasp['POSCARs'].structure)
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
    atom_mapping = {k:new_atom for k in atom_nums}
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
    print('Creating new ' + str(job) + 'Job at ' + this_dir)
    if job == 'NEB':
        replace_atom_NEB(prev_dir, this_dir, atom_nums, new_atom)
    elif job == 'dim':
        replace_atom(prev_dir, this_dir, atom_nums, new_atom, {'MODECAR', Modecar})
    elif job == 'standard':
        replace_atom(prev_dir, this_dir, atom_nums, new_atom)
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