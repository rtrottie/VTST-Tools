# Functions which check and maintain VASP runs
# Not meant to be called from command line
from custodian.vasp.jobs import *
from custodian.vasp.handlers import *
from monty.os.path import which
from pymatgen.io.vasp.inputs import *
from pymatgen.io.vasp.outputs import Vasprun
import Dim_Check
from pymatgen.core import Structure, PeriodicSite
import numpy as np

class NEBNotTerminating(FrozenJobErrorHandler):

    is_terminating = True

    def correct(self):
        return {"errors": ["Frozen job"], "actions": None}

class NEBWalltimeHandler(WalltimeHandler):
    def check(self):
        if self.wall_time:
            run_time = datetime.datetime.now() - self.start_time
            total_secs = run_time.total_seconds()
            outcar = Outcar("01/OUTCAR")
            if not self.electronic_step_stop:
                # Determine max time per ionic step.
                outcar.read_pattern({"timings": "LOOP\+.+real time(.+)"},
                                    postprocess=float)
                time_per_step = np.max(outcar.data.get('timings')) if outcar.data.get("timings", []) else 0
            else:
                # Determine max time per electronic step.
                outcar.read_pattern({"timings": "LOOP:.+real time(.+)"},
                                    postprocess=float)
                time_per_step = np.max(outcar.data.get('timings')) if outcar.data.get("timings", []) else 0

            # If the remaining time is less than average time for 3
            # steps or buffer_time.
            time_left = self.wall_time - total_secs
            if time_left < max(time_per_step * 3, self.buffer_time):
                return True

        return False

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
            if v.converged and len(v.ionic_steps) <= 10:
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

    def postprocess(self):
        VaspJob.postprocess(self)
        images = Incar.from_file('INCAR')['IMAGES']
        is_magnetic = ('ISPIN' in Incar.from_file('INCAR')) and (Incar.from_file('INCAR')['ISPIN'] == 2)
        cwd = os.path.abspath('.')
        for i in range(images+2):
            dir = str(i).zfill(2)
            os.chdir(dir)
            if os.path.exists('AECCAR0') and os.path.exists('AECCAR2') and os.path.exists('CHGCAR'):
                os.system('chgsum.pl AECCAR0 AECCAR2 &> bader_info')
                if is_magnetic:
                    os.system('chgsplit.pl CHGCAR &>> bader_info ; bader CHGCAR_mag -ref CHGCAR_sum &>> bader_info')
                    try:
                        shutil.copy('ACF.dat', 'ACF_mag.dat')
                        shutil.copy('AVF.dat', 'AVF_mag.dat')
                        shutil.copy('BCF.dat', 'BCF_mag.dat')
                    except:
                        pass
                os.system('bader CHGCAR -ref CHGCAR_sum &>> bader_info')
            os.chdir(cwd)

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
                    struct = Structure.from_file(f)
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

def run_bader(VaspJob):
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

        if 'VASP_DEFAULT_BADER' in os.environ and 'false' in os.environ['VASP_DEFAULT_BADER'].lower():
            pass
        else:
            run_bader(VaspJob)

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
            actions.append({"file": "NEWMODECAR",
                        "action": {"_file_copy": {"dest": "MODECAR"}}})
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

class DiffusionJob(NEBJob):

    def __init__(self, diffusing_atom, constricting_atoms, nsteps=10, **kwargs):
        super().__init__(**kwargs)
        self.constricting_atoms = constricting_atoms
        self.diffusing_atom = diffusing_atom
        self.nsteps = nsteps

    is_terminating = False

    def setup(self):

        """
        Performs initial setup for VaspJob, including overriding any settings
        and backing up.
        """
        p = Poscar.from_file('POSCAR') # type: Poscar
        s = p.structure # type: Structure

        # Get Translation vectors
        a = s[self.constricting_atoms[0]].coords # type: np.array
        b = s[self.constricting_atoms[1]].coords # type: np.array
        c = s[self.constricting_atoms[2]].coords # type: np.array

        ab = b-a
        ac = c-a
        normal_vector = np.cross(ab, ac)
        normal_vector = normal_vector / np.linalg.norm(normal_vector) / 2

        # Make Endpoint Structures
        s_00 = s.copy()
        s_02 = s.copy()
        s_00.translate_sites(self.diffusing_atom, vector=normal_vector, frac_coords=False)
        s_02.translate_sites(self.diffusing_atom, vector=-normal_vector, frac_coords=False)

        os.makedirs('00', exist_ok=True)
        os.makedirs('01', exist_ok=True)
        os.makedirs('02', exist_ok=True)
        Poscar(s_00, selective_dynamics=p.selective_dynamics).write_file('00/POSCAR')
        Poscar(s   , selective_dynamics=p.selective_dynamics).write_file('01/POSCAR')
        Poscar(s_02, selective_dynamics=p.selective_dynamics).write_file('02/POSCAR')


        incar = Incar.from_file('INCAR')
        incar['IMAGES'] = 1
        incar['LCLIMB'] = True
        incar['NSW'] = self.nsteps
        incar.write_file('INCAR')

        super().setup()

    def postprocess(self):
        shutil.copy('01/CONTCAR', 'CONTCAR')
        shutil.copy('01/OUTCAR', 'OUTCAR')

class NonConvergingErrorHandler_toDamped(NonConvergingErrorHandler):
    is_terminating = False
    def correct(self):
        # if change_algo is True, change ALGO = Fast to Normal if ALGO is
        # Fast. If still not converging, following Kresse's
        # recommendation, we will try two iterations of different mixing
        # parameters. If this error is caught again, then kill the job
        vi = VaspInput.from_directory(".")
        content = "LSTOP = .TRUE."
        algo = vi["INCAR"].get("ALGO", "Normal")
        time = vi["INCAR"].get("TIME", "0.4")
        actions = []
        if self.change_algo:
            if algo == "Fast":
                backup(VASP_BACKUP_FILES)
                actions.append({"file": "STOPCAR",
                                "action": {"_file_create": {'content': content}}})
                actions.append({"dict": "INCAR",
                                "action": {"_set": {"ALGO": "Normal"}}})

            elif algo == "Normal":
                backup(VASP_BACKUP_FILES)
                actions.append({"file": "STOPCAR",
                                "action": {"_file_create": {'content': content}}})
                actions.append({"dict": "INCAR",
                                "action": {"_set": {"ALGO": "Damped", "TIME" : 0.1}}},
                               )

            elif algo == "Damped" and time <= 0.5 :
                backup(VASP_BACKUP_FILES)
                actions.append({"file": "STOPCAR",
                                "action": {"_file_create": {'content': content}}})
                actions.append({"dict": "INCAR",
                                "action": {"_set": {"ALGO": "Damped", "TIME" : time+0.05}}})

        if actions:
            VaspModder(vi=vi).apply_actions(actions)
            return {"errors": ["Non-converging job"], "actions": actions}

        # Unfixable error. Just return None for actions.
        else:

            return {"errors": ["Non-converging job"], "actions": None}