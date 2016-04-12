# Functions which check and maintain VASP runs
# Not meant to be called from command line
from custodian.vasp.jobs import *
from custodian.vasp.handlers import *
from monty.os.path import which
from pymatgen.io.vaspio.vasp_input import *
import Dim_Check

class NEBNotTerminating(FrozenJobErrorHandler):

    is_terminating = True

    def correct(self):
        return {"errors": ["Frozen job"], "actions": None}

class DimerDivergingHandler(ErrorHandler):
    is_monitor = True
    is_terminating = True

    def check(self):
        if os.path.exists("DIMCAR") and os.path.getsize('DIMCAR') > 0:
            with open("DIMCAR") as f:
                dimcar = list(map(lambda x: [x.split()], reversed(f.readlines())))
                dimcar = list(reduce(lambda x,y: x if x[-1][0] == y[0][0] else x + y, dimcar))
                if len(dimcar) <= 10:
                    return False
                elif float(dimcar[0][1]) < 5:
                    return False
                elif (float(dimcar[0][1]) > float(dimcar[1][1])) and (float(dimcar[0][1]) > float(dimcar[2][1])):
                    return True
        else:
            return False

    def correct(self):
        content = "LABORT = .TRUE."
        #Write STOPCAR
        actions = [{"file": "STOPCAR",
                    "action": {"_file_create": {'content': content}}}]
        m = Modder(actions=[FileActions])
        for a in actions:
            m.modify(a["action"], a["file"])
        # Actions is being returned as None so that custodian will stop after
        # STOPCAR is written. We do not want subsequent jobs to proceed.
        return {"errors": ["Dimer Force Too High"], "actions": None}

class DimerCheckMins(ErrorHandler):
    is_monitor = False
    is_terminating = False
    raises_runtime_error = False

    def __init__(self, output_filename="vasprun.xml"):
        """
        Initializes the handler with the output file to check.

        Args:
            output_vasprun (str): Filename for the vasprun.xml file. Change
                this only if it is different from the default (unlikely).
        """
        self.output_filename = output_filename

    def check(self):
        try:
            v = Vasprun(self.output_filename)
            if v.converged and len(v.ionic_steps) <= 5:
                Dim_Check.check_dimer(os.path.abspath('.'), True)
                return False
        except:
            pass
        return True

    def correct(self):
        return {"errors": ['no minima created'], 'actions' : None}

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
        if not set(files).issuperset({"INCAR", "POSCAR", "POTCAR", "KPOINTS"}):
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

    def postprocess(self):
        print('Postprocessing')
        VaspJob.postprocess(self)
        try:
            v = Vasprun(self.output_file)
            if v.converged and len(v.ionic_steps) <= 5:
                print('Creating Mins')
                Dim_Check.check_dimer(os.path.abspath('.'))
        except:
            pass



StandardJob = VaspJob