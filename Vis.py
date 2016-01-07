# a quick way to visualize structures and molecules made in pymatgen.  current set up to run only on my virtual box
import os

def open_in_VESTA(molecule,type='cif'):
    vesta = os.path.join(os.environ['VESTA_DIR'], 'VESTA')
    SCRATCH = '/home/ryan/scratch/scratch.' + type

    molecule.to(type, SCRATCH)
    os.system(vesta + ' ' + SCRATCH)

def open_in_Jmol(molecule,type='cif'):
    JMOL_DIR = os.path.join(os.environ['JMOL_DIR'], 'jmol')
    SCRATCH = '/home/ryan/scratch/scratch.' + type

    molecule.to(type, SCRATCH)
    os.system(JMOL_DIR + ' ' + SCRATCH)
