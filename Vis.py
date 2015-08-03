# a quick way to visualize structures and molecules made in pymatgen.  current set up to run only on my virtual box
import os

def open_in_VESTA(molecule,type='cif'):
    VESTA_DIR = '/home/ryan/programs/vesta/VESTA-x86_64/VESTA '
    SCRATCH = '/home/ryan/scratch/scratch.' + type

    molecule.to(type, SCRATCH)
    os.system(VESTA_DIR+SCRATCH)

def open_in_Jmol(molecule,type):
    JMOL_DIR = '/home/ryan/programs/jmol/jmol-14.2.14_2015.06.01/jmol '
    SCRATCH = '/home/ryan/scratch/scratch.' + type

    molecule.to(type, SCRATCH)
    os.system(JMOL_DIR+SCRATCH)
