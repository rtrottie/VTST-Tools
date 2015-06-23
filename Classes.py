import os
import subprocess
import shutil
import math
import logging
from custodian.vasp.jobs import *
from pymatgen.io.vaspio_set import MITNEBVaspInputSet
from pymatgen.io.vaspio.vasp_input import Incar, Kpoints
from pymatgen.io.vaspio.vasp_output import Outcar
from pymatgen.io.smartio import read_structure
from pymatgen.io.vaspio_set import MITVaspInputSet
from monty.json import MontyDecoder
from monty.os.path import which

class NEBJob(VaspJob):
    def run(self):
        """
        Perform the actual VASP run.

        Returns:
            (subprocess.Popen) Used for monitoring.
        """
        cmd = list(self.vasp_cmd)
        if self.auto_gamma:
            kpts = Kpoints.from_file("KPOINTS")
            if kpts.style == "Gamma" and tuple(kpts.kpts[0]) == (1, 1, 1):
                if self.gamma_vasp_cmd is not None:
                    cmd = self.gamma_vasp_cmd
                elif which(cmd[-1] + ".gamma"):
                    cmd[-1] += ".gamma"
        logging.info("Running {}".format(" ".join(cmd)))
        with open(self.output_file, 'w') as f:
            p = subprocess.Popen(cmd, stdout=f)
        #os.system(" ".join(cmd) + " > " + self.output_file)
        return p

    def setup(self):
        """
        Performs initial setup for VaspJob, including overriding any settings
        and backing up.
        """
        files = os.listdir(".")
        num_structures = 0
        if not set(files).issuperset(['KPOINTS','INCAR','POTCAR']):
            raise RuntimeError("Necessary files missing.  Need: KPOINTS, INCAR, and POTCAR.  Unable to continue.")
        incar = Incar.from_file('INCAR')
        self._images = incar["IMAGES"]
        for i in xrange(self._images):
            if not os.path.isfile(os.path.join(str(i).zfill(2),'POSCAR')):
                raise RuntimeError("Expected file at : " + os.path.join(str(i).zfill(2),'POSCAR'))

