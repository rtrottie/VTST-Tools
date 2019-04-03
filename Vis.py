# a quick way to visualize structures and molecules made in pymatgen.  current set up to run only on my virtual box
import os
import subprocess
from tempfile import NamedTemporaryFile

def open_in_VESTA(molecule,type='poscar'):
    """

    :param molecule: A file or structure of a structure to view
    :param type: if structure needs to be written, what type of file.  Use Pymatgen standard
    :return: subprocess.Popen
    """
    vesta = os.path.join(os.environ['VESTA_DIR'])
    if isinstance(molecule, str):
        SCRATCH = molecule
    else:
        SCRATCH = '{}.{}'.format(NamedTemporaryFile(delete=False).name, type)
        molecule.to(type, SCRATCH)
    # return subprocess.Popen([vesta, SCRATCH])
    return subprocess.Popen(' '.join([vesta, SCRATCH]), shell=True)
    # return os.system(vesta + ' ' + SCRATCH)

def open_in_Jmol(molecule,type='cif',silent=True):
    if silent:
        silent = '&> /dev/null'
    else:
        silent = ''
    JMOL_DIR = os.path.join(os.environ['JMOL_DIR'])
    if isinstance(molecule, str):
        return subprocess.Popen(JMOL_DIR + ' ' + molecule, shell=True)
    else:
        SCRATCH = 'D://Users/RyanTrottier/Documents/Scrap/scratch.' + type
        molecule.to(type, SCRATCH)
        # return os.system(' '.join([JMOL_DIR, SCRATCH]))
        return subprocess.Popen(' '.join([JMOL_DIR, SCRATCH, silent]), shell=True, stdout='/dev/null', stderr='/dev/null')

def view(molecule, program='jmol', type='cif'):
    if program == True or program.lower() == 'jmol':
        return open_in_Jmol(molecule, type)
    elif program.lower() == 'vesta':
        return open_in_VESTA(molecule,type)
    else:
        raise Exception('Unrecognized program:  ' + program.lower())