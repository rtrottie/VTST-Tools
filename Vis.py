# a quick way to visualize structures and molecules made in pymatgen.  current set up to run only on my virtual box
import os
import subprocess

def open_in_VESTA(molecule,type='cif'):
    vesta = os.path.join(os.environ['VESTA_DIR'], 'VESTA')
    SCRATCH = '/home/ryan/scratch/scratch.' + type

    molecule.to(type, SCRATCH)
    os.system(vesta + ' ' + SCRATCH)

def open_in_Jmol(molecule,type='cif'):
    JMOL_DIR = os.path.join(os.environ['JMOL_DIR'], 'jmol') if 'JMOL_DIR' in os.environ else 'jmol'
    if isinstance(molecule, basestring):
        return subprocess.Popen([JMOL_DIR, SCRATCH])
    else:
        SCRATCH = '/home/ryan/scratch/scratch.' + type
        molecule.to(type, SCRATCH)
        return subprocess.Popen([JMOL_DIR, SCRATCH])

def view(molecule, program='jmol', type='cif'):
    if program == True or program.lower() == 'jmol':
        open_in_Jmol(molecule, type)
    elif program.lower() == 'vesta':
        open_in_VESTA(molecule,type)
    else:
        raise Exception('Unrecognized program:  ' + program.lower())