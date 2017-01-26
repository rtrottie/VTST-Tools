# a quick way to visualize structures and molecules made in pymatgen.  current set up to run only on my virtual box
import os
import subprocess

def open_in_VESTA(molecule,type='cif'):
    vesta = os.path.join(os.environ['VESTA_DIR'])
    if type(molecule) == str:
        SCRATCH = molecule
    # else:
    #     SCRATCH = 'D://Users/RyanTrottier/Documents/Scrap/scratch.' + type
    #     molecule.to(type, SCRATCH)
    os.system(vesta + ' ' + SCRATCH)

def open_in_Jmol(molecule,type='cif'):
    JMOL_DIR = os.path.join(os.environ['JMOL_DIR'])
    if isinstance(molecule, str):
        return subprocess.Popen(JMOL_DIR + ' ' + molecule, shell=True)
    else:
        SCRATCH = 'D://Users/RyanTrottier/Documents/Scrap/scratch.' + type
        molecule.to(type, SCRATCH)
        return subprocess.Popen([JMOL_DIR, SCRATCH])

def view(molecule, program='jmol', type='cif'):
    if program == True or program.lower() == 'jmol':
        open_in_Jmol(molecule, type)
    elif program.lower() == 'vesta':
        open_in_VESTA(molecule,type)
    else:
        raise Exception('Unrecognized program:  ' + program.lower())