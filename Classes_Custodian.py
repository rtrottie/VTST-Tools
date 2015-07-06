from custodian.vasp.jobs import *
from custodian.vasp.handlers import *
from monty.os.path import which
from pymatgen.io.vaspio.vasp_input import *

class NEBNotTerminating(FrozenJobErrorHandler):

    is_terminating = True

    def correct(self):
        return {"errors": ["Frozen job"], "actions": None}


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


class DimerJob(VaspJob):
    def setup(self):
        """
        Performs initial setup for VaspJob, including overriding any settings
        and backing up.
        """
        files = os.listdir(".")
        num_structures = 0
        if not set(files).issuperset({"INCAR", "POSCAR", "POTCAR", "KPOINTS", "MODECAR"}):
            for f in files:
                try:
                    struct = read_structure(f)
                    num_structures += 1
                except:
                    pass
            if num_structures != 1:
                raise RuntimeError("{} structures found. Unable to continue."
                                   .format(num_structures))
            else:
                self.default_vis.write_input(struct, ".")

        if self.backup:
            for f in VASP_INPUT_FILES:
                shutil.copy(f, "{}.orig".format(f))

        if self.auto_npar:
            try:
                incar = Incar.from_file("INCAR")
                #Only optimized NPAR for non-HF and non-RPA calculations.
                if not (incar.get("LHFCALC") or incar.get("LRPA") or
                        incar.get("LEPSILON")):
                    if incar.get("IBRION") in [5, 6, 7, 8]:
                        # NPAR should not be set for Hessian matrix
                        # calculations, whether in DFPT or otherwise.
                        del incar["NPAR"]
                    else:
                        import multiprocessing
                        # try sge environment variable first
                        # (since multiprocessing counts cores on the current machine only)
                        ncores = os.environ.get('NSLOTS') or multiprocessing.cpu_count()
                        ncores = int(ncores)
                        for npar in range(int(round(math.sqrt(ncores))),
                                          ncores):
                            if ncores % npar == 0:
                                incar["NPAR"] = npar
                                break
                    incar.write_file("INCAR")
            except:
                pass

        if self.settings_override is not None:
            VaspModder().apply_actions(self.settings_override)