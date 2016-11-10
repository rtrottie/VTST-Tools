# Functions which check and maintain VASP runs
# Not meant to be called from command line
from custodian.vasp.jobs import *
from custodian.vasp.handlers import *
from monty.os.path import which
from pymatgen.io.vasp.inputs import *
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
    is_terminating = False

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
        kpoints = Kpoints.from_file('KPOINTS')
        poscar = Poscar.from_file('00/POSCAR')
        potcar = Potcar.from_file('POTCAR')
        self._images = incar["IMAGES"]
        for i in range(self._images):
            if not os.path.isfile(os.path.join(str(i).zfill(2),'POSCAR')):
                raise RuntimeError("Expected file at : " + os.path.join(str(i).zfill(2),'POSCAR'))
        if self.settings_override is not None:
            VaspModder(vi=VaspInput(incar, kpoints, poscar, potcar)).apply_actions(self.settings_override)

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
        make = False
        try:
            v = Vasprun('vasprun.xml')
            if v.converged and len(v.ionic_steps) <= 5 and self.final:
                make = True
        except:
            pass
        if make:
            print('Creating Mins')
            Dim_Check.check_dimer(os.path.abspath('.'), True)
        if os.path.exists('AECCAR0') and os.path.exists('AECCAR2') and os.path.exists('CHGCAR'):
            os.system('chgsum.pl AECCAR0 AECCAR2 &> bader_info')
            if 'ISPIN' in Incar.from_file('INCAR') and Incar.from_file('INCAR')['ISPIN'] == 2:
                os.system('chgsplit.pl CHGCAR &>> bader_info ; bader CHGCAR_mag -ref CHGCAR_sum &>> bader_info')
                try:
                    shutil.copy('ACF.dat', 'ACF_mag.dat')
                    shutil.copy('AVF.dat', 'AVF_mag.dat')
                    shutil.copy('BCF.dat', 'BCF_mag.dat')
                except:
                    pass
            os.system('bader CHGCAR -ref CHGCAR_sum &>> bader_info')

class StandardJob(VaspJob):
    def postprocess(self):
        VaspJob.postprocess(self)
        if os.path.exists('AECCAR0') and os.path.exists('AECCAR2') and os.path.exists('CHGCAR'):
            os.system('chgsum.pl AECCAR0 AECCAR2 &> bader_info')
            if 'ISPIN' in Incar.from_file('INCAR') and Incar.from_file('INCAR')['ISPIN'] == 2:
                os.system('chgsplit.pl CHGCAR &>> bader_info ; bader CHGCAR_mag -ref CHGCAR_sum &>> bader_info')
                try:
                    shutil.copy('ACF.dat', 'ACF_mag.dat')
                    shutil.copy('AVF.dat', 'AVF_mag.dat')
                    shutil.copy('BCF.dat', 'BCF_mag.dat')
                except:
                    pass
            os.system('bader CHGCAR -ref CHGCAR_sum &>> bader_info')

class DynMatJob(StandardJob):
    def postprocess(self):
        return

class FrozenJobErrorHandler_cont(ErrorHandler):
    """
    Detects an error when the output file has not been updated
    in timeout seconds. Changes ALGO to Normal from Fast
    """

    is_monitor = True

    def __init__(self, output_filename="vasp.out", timeout=21600):
        """
        Initializes the handler with the output file to check.

        Args:
            output_filename (str): This is the file where the stdout for vasp
                is being redirected. The error messages that are checked are
                present in the stdout. Defaults to "vasp.out", which is the
                default redirect used by :class:`custodian.vasp.jobs.VaspJob`.
            timeout (int): The time in seconds between checks where if there
                is no activity on the output file, the run is considered
                frozen. Defaults to 3600 seconds, i.e., 1 hour.
        """
        self.output_filename = output_filename
        self.timeout = timeout

    def check(self):
        st = os.stat(self.output_filename)
        if time.time() - st.st_mtime > self.timeout:
            return True


    def correct(self):
        backup(VASP_BACKUP_FILES | {self.output_filename})

        vi = VaspInput.from_directory('.')
        actions = []
        if os.path.getsize('CONTCAR') > 0:
            actions.append({"file": "CONTCAR",
                        "action": {"_file_copy": {"dest": "POSCAR"}}})
        if vi["INCAR"].get("ALGO", "Normal") == "Fast":
            actions.append({"dict": "INCAR",
                        "action": {"_set": {"ALGO": "Normal"}}})

        VaspModder(vi=vi).apply_actions(actions)

        return {"errors": ["Frozen job"], "actions": actions}

class FrozenJobErrorHandler_dimer(ErrorHandler):
    """
    Detects an error when the output file has not been updated
    in timeout seconds. Changes ALGO to Normal from Fast
    """

    is_monitor = True

    def __init__(self, output_filename="vasp.out", timeout=21600):
        """
        Initializes the handler with the output file to check.

        Args:
            output_filename (str): This is the file where the stdout for vasp
                is being redirected. The error messages that are checked are
                present in the stdout. Defaults to "vasp.out", which is the
                default redirect used by :class:`custodian.vasp.jobs.VaspJob`.
            timeout (int): The time in seconds between checks where if there
                is no activity on the output file, the run is considered
                frozen. Defaults to 3600 seconds, i.e., 1 hour.
        """
        self.output_filename = output_filename
        self.timeout = timeout

    def check(self):
        st = os.stat(self.output_filename)
        if time.time() - st.st_mtime > self.timeout:
            return True


    def correct(self):
        backup(VASP_BACKUP_FILES | {self.output_filename})

        vi = VaspInput.from_directory('.')
        actions = []
        if os.path.getsize('CENTCAR') > 0:
            actions.append({"file": "CENTCAR",
                        "action": {"_file_copy": {"dest": "POSCAR"}}})
        if vi["INCAR"].get("ALGO", "Normal") == "Fast":
            actions.append({"dict": "INCAR",
                        "action": {"_set": {"ALGO": "Normal"}}})

        VaspModder(vi=vi).apply_actions(actions)

        return {"errors": ["Frozen job"], "actions": actions}
class MaxForceErrorHandler_dimer(ErrorHandler):
    """
    Checks that the desired force convergence has been achieved. Otherwise
    restarts the run with smaller EDIFF. (This is necessary since energy
    and force convergence criteria cannot be set simultaneously)
    """
    is_monitor = False

    def __init__(self, output_filename="vasprun.xml",
                 max_force_threshold=0.005):
        """
        Args:
            input_filename (str): name of the vasp INCAR file
            output_filename (str): name to look for the vasprun
            max_force_threshold (float): Threshold for max force for
                restarting the run. (typically should be set to the value
                that the creator looks for)
        """
        self.output_filename = output_filename
        self.max_force_threshold = max_force_threshold

    def check(self):
        try:
            v = Vasprun(self.output_filename)
            max_force = max([np.linalg.norm(a) for a
                             in v.ionic_steps[-1]["forces"]])
            if max_force > self.max_force_threshold and v.converged is True:
                return True
        except:
            pass
        return False


    def correct(self):
        backup(VASP_BACKUP_FILES | {self.output_filename})
        vi = VaspInput.from_directory(".")
        ediff = float(vi["INCAR"].get("EDIFF", 1e-4))
        ediffg = float(vi["INCAR"].get("EDIFFG", ediff * 10))
        actions = [{"file": "CENTCAR",
                    "action": {"_file_copy": {"dest": "POSCAR"}}},
                   {"dict": "INCAR",
                    "action": {"_set": {"EDIFFG": self.max_force_threshold}}}]
        VaspModder(vi=vi).apply_actions(actions)

        return {"errors": ["MaxForce"], "actions": actions}

