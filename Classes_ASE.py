# functions to improve  ASE and output setup
# Not meant to be called from command line
from ase.calculators.vasp import Vasp
import os

class StandardVasp(Vasp):
    def write_input(self, atoms, directory='./'):
        from ase.io.vasp import write_vasp
        write_vasp(os.path.join(directory, 'POSCAR'), self.atoms_sorted, symbol_count = self.symbol_count)
        self.write_sort_file(directory=directory)