# Various functions called by other functions
# Not meant to be called from command line

import os
import subprocess
from pymatgen.core.structure import *
from pymatgen.core import PeriodicSite
from pymatgen.analysis.transition_state import NEBAnalysis
import cfg
import socket
import shutil
from Classes_Pymatgen import *
from functools import reduce
import tempfile
from math import ceil

# def pmg_to_ase(pmg_structure : Structure):
#     from ase.io import read
#     with tempfile.NamedTemporaryFile() as f:
#         pmg_structure.to('cif', f.name)
#         ase_structure = read(f.name, format='cif')
#     return ase_structure
#
# def ase_to_pmg(ase_structure):
#     from ase.io import write
#     with tempfile.NamedTemporaryFile() as f:
#         write(f.name, ase_structure, format='vasp')
#         pmg_structure = Poscar.from_file(f.name).structure
#     return pmg_structure

def get_FERE_chemical_potential(structure : Structure):
    fere = {'Fe' : -6.15,
            'Al' : -3.02,
            'O'  : -4.73
            }
    chem_pot = 0
    for a in structure: #type: PeriodicSite
        chem_pot += fere[str(a.specie)]
    return chem_pot



def pmg_to_pyl_poscar(poscar : Poscar):
    from pylada.crystal import read, write
    import pylada.crystal
    with tempfile.NamedTemporaryFile() as f:
        poscar.write_file(f.name)
        pyl = read.poscar(f.name)
    return pyl

def pmg_to_pyl(pmg : Structure):
    from pylada.crystal import Structure as Pyl_Structure
    from pylada.crystal import Atom
    pyl = Pyl_Structure(pmg.lattice.matrix)
    for i in range(len(pmg)):
        if pmg.site_properties:
            kwargs = {x: pmg.site_properties[x][i] for x in pmg.site_properties}
        else:
            kwargs = {}
        coords = pmg[i].coords
        specie = str(pmg[i].specie)
        pyl_atom = Atom(coords[0], coords[1], coords[2], specie, **kwargs)
        pyl.add_atom(pyl_atom)
    return pyl

def pyl_to_pmg(structure):
    redundant_properties = ['pos', 'type']
    pyl_dict = structure.to_dict()
    property_tags = [x for x in pyl_dict[0] if x not in redundant_properties]
    pmg_dict = {}
    for tag in property_tags:
        pmg_dict[tag] = [pyl_dict[site][tag] for site in range(len(structure))]
    coords = [ atom.pos for atom in structure ]
    species = [atom.type for atom in structure]
    return Structure(structure.cell, species, coords, coords_are_cartesian=True, site_properties=pmg_dict)

def get_smallest_expansion(structure : Structure, length : float):
    '''
    Finds the smallest expansion of the provided cell such that all sides are at minimum length.  Will change shape of
    cell if it creates a better match
    :param structure: Unit cell to convert
    :param length: Minimum vector difference
    :return:
    '''
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    sga = SpacegroupAnalyzer(structure)
    structures = [
        structure,
        structure.get_primitive_structure(),
        structure.get_reduced_structure('niggli'),
        structure.get_reduced_structure('LLL'),
        sga.get_conventional_standard_structure(),
        sga.get_primitive_standard_structure()
    ]
    best_structure = None
    for structure in structures: # type: Structure
        l = structure.lattice
        expansion = [ ceil(length / vec) for vec in l.abc ]
        possible_structure = structure * expansion
        if best_structure == None or len(possible_structure) < len(best_structure):
            best_structure = possible_structure
    return best_structure

def get_nelect(outcar):
    line = subprocess.check_output(['grep', 'NELECT', outcar])
    nelect = int(line.split()[2].split('.')[0])
    return nelect


def xfrange(start, stop, step):
    start = float(start)
    while start < stop:
        yield start
        start += step

def neb2dim(neb_dir, dimer_dir):
    dimer_dir = os.path.abspath(dimer_dir)
    if not os.path.exists(dimer_dir):
        os.makedirs(dimer_dir)

    os.chdir(neb_dir)
    os.system(os.path.join(os.environ['VTST_DIR'],'nebspline.pl'))
    os.system(os.path.join(os.environ['VTST_DIR'],'neb2dim.pl') + ' > /dev/null')
    if os.path.abspath(os.path.join(os.path.abspath(neb_dir), 'dim')) != os.path.abspath(dimer_dir):
        for f in os.listdir('dim'):
            shutil.move(os.path.join('dim', f), dimer_dir)

    os.chdir(dimer_dir)
    incar = Incar.from_file('INCAR')
    incar['ICHAIN'] = 2
    incar['EDIFF'] = 1e-7
    incar.pop('IMAGES');
    try:
        incar.pop('SPRING');
    except:
        pass
    try:
        incar.pop('LCLIMB')
    except:
        pass
    os.remove(os.path.join(dimer_dir, 'INCAR'))
    incar.write_file('INCAR')

def getImageDistance(POSCAR_1, POSCAR_2):
    full_distance_string = subprocess.check_output(os.path.join(os.environ['VTST_DIR'],'diffcon.pl')+ ' '+ POSCAR_1 +' ' +POSCAR_2, shell=True)
    distance = full_distance_string.split('\n')[-4].split(' ')[-1] # Stripping rest of the file away
    return distance

def getJobType(dir):
    if os.path.basename(dir) == 'INCAR':
        incar = Incar.from_file(dir)
    else:
        incar = Incar.from_file(os.path.join(dir,'INCAR'))
    if os.path.exists(os.path.join(dir, 'inpfileq')):
        with open('inpfileq') as inpfileq:
            for line in inpfileq.readlines():
                if len(line.split()) > 1 and 'SM_TYPE' in line.split()[0]:
                    if 'SSM' in line.split()[1]:
                        return 'SSM'
                    elif 'GSM' in line.split()[1]:
                        return 'GSM'
                    else:
                        raise Exception('Problem with following line in inpfileq:  \n' + line + '\n Expected following format: SM_TYPE   SSM/GSM')
        return 'GSM'
    elif 'ICHAIN' in incar:
        if incar['ICHAIN'] == 0:
            return 'NEB'
        elif incar['ICHAIN'] == 1:
            return 'DynMat'
        elif incar['ICHAIN'] == 2:
            return 'Dimer'
        else:
            raise Exception('Not yet Implemented')
    elif 'IMAGES' in incar:
            return 'NEB'
    else:
        return 'Standard'

def getComputerName():
    if 'VASP_COMPUTER' in os.environ:
        return os.environ['VASP_COMPUTER']
    elif 'psiops' in socket.gethostname():
        return 'psiops'
    elif 'login0' in socket.gethostname():
        return 'janus'
    elif 'rapunzel' in socket.gethostname():
        return 'rapunzel'
    elif 'login' in socket.gethostname():
        return 'peregrine'
    else:
        raise Exception('On an unrecognized computer')

def getLoopPlusTimes(outcar):
    grep = subprocess.check_output('grep LOOP+: ' + outcar, shell=True).strip().split('\n')
    times = map(lambda l: float(l.split()[-1]), grep)
    return times

def getMaxLoopTimes(times):
    return sum(map(lambda x: max(x),
                   zip(*times)))

def update_incar(structure, incar):
    for k in incar.keys():
        if k in cfg.INCAR:
            species = map(lambda sp: str(sp), structure.species)
            if k != 'MAGMOM':
                species = list(species)
                lspecies = list(map(lambda x: [x], species))
                species = reduce(lambda x,y: x+y if x[-1] != y[0] else x + y[1:-1],
                                 map(lambda x: [x], species))
            incar[k] = list(map(lambda a: cfg.INCAR[k][a] if a in cfg.INCAR[k] else cfg.INCAR[k]['default'],
                            species))

def load_variables(file_loc):
    vars = {}
    with open(file_loc) as f:
        for l in f.readlines():
            variable_value = l.split(':')
            vars[variable_value[0].strip()] = variable_value[1].strip()
    return vars

def get_midpoint(sites):
    coords = np.array([ 0.0, 0.0, 0.0])
    for site in sites: # type: PeriodicSite
        coords += site.frac_coords
    coords /= len(sites)
    return coords


