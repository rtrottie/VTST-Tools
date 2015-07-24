__author__ = 'ryan'
import os

def open_in_VESTA(molecule,type):
    VESTA_DIR = '/home/ryan/programs/vesta/VESTA-x86_64/VESTA '
    SCRATCH = '/home/ryan/scratch/scratch.' + type

    molecule.to(type, SCRATCH)
    os.system(VESTA_DIR+SCRATCH)

def open_in_Jmol(molecule,type):
    JMOL_DIR = '/home/ryan/programs/jmol/jmol-14.2.14_2015.06.01/jmol '
    SCRATCH = '/home/ryan/scratch/scratch.' + type

    molecule.to(type, SCRATCH)
    os.system(JMOL_DIR+SCRATCH)
