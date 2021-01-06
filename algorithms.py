from Classes_Pymatgen import Vasprun, Structure, Poscar, Incar
from custodian.custodian import Custodian
from Classes_Custodian import StandardJob
import os
import shutil
import logging
from Neb_Make import nebmake
from custodian.vasp.handlers import *


def get_energy(i, structure: Structure, target=0.01):
    """
    get_energy finds the energy of the structure at location i along the interpolated pathway

    :param i: folder for structure to be placed in (i >=0 and i < 1000)
    :param structure: Structure
    :param target: energy convergence criteria
    :return: energy in eV
    """

    # Setup Run
    cwd = os.path.abspath('.')
    handlers = [VaspErrorHandler('vasp.log'), PositiveEnergyErrorHandler(), NonConvergingErrorHandler(nionic_steps=10)]
    settings = [
        {'dict': 'INCAR',
         'action': {'_set': {'NSW': 5000,
                             'IOPT': 0,
                             'IBRION': 3,
                             'EDIFFG': 1e-3,
                             'POTIM' : 0},
                    }}
    ]
    folder = os.path.join(cwd, str(i).zfill(4))

    # Check if Run has occured
    if os.path.exists(folder): # if it has
        Poscar(structure).write_file(os.path.join(folder, 'POSCAR'))
        try: # attempt to get data from completed run
            vasprun_above = Vasprun(os.path.join(folder, 'above', 'vasprun.xml'))
            vasprun_below = Vasprun(os.path.join(folder, 'below', 'vasprun.xml'))
            if vasprun_above.converged and vasprun_below.converged:

                with open(os.path.join(folder, 'energy.txt'), 'w') as f:
                    f.write(str(min(vasprun_above.final_energy, vasprun_below.final_energy)))
                return min(vasprun_above.final_energy, vasprun_below.final_energy)
        except: # TODO: Determine errors to be caught here
            try: # If run is not completed, see if override is provided
                if os.path.exists(os.path.join(folder, 'energy.txt')):
                    with open(os.path.join(folder, 'energy.txt'), 'r') as f:
                        energy = float(f.read().split()[0])
                    return energy
                else: # see if simple run was performed and check for energy
                    shutil.copy('INCAR', os.path.join(folder, 'INCAR'))
                    vasprun = Vasprun(os.path.join(folder, 'vasprun.xml'))
                    with open(os.path.join(folder, 'energy.txt'), 'w') as f:
                        f.write(str(vasprun.final_energy))
                    return vasprun.final_energy
            except: # TODO: Determine errors to be caught here
                pass
    # If the run was not performed, restart calculation
    else:
        os.mkdir(folder)
    above = None
    below = None

    # Initialize from previous runs
    for dir in [dir for dir in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, dir))]: # determine closest runs
        try:
            dir_i = int(dir)
            if i == dir_i:
                pass
            if dir_i > i:
                if above is None:
                    above = dir_i
                elif dir_i - i < above - i:
                    above = dir_i
            elif dir_i < i:
                if below is None:
                    below = dir_i
                elif abs(dir_i - i) < abs(below - i):
                    below = dir_i

            elif closest is None:
                closest = dir
            elif abs(i - int(closest)) >= abs(i - int(dir)):
                closest = dir
        except:
            pass
    same_wfxns = 0
    for dir_i, dir in [(str(above).zfill(4), 'above'), (str(below).zfill(4), 'below')]:
        try: # Load vasprun and check if individual folders have converged
            vasprun = Vasprun(os.path.join(folder, dir, 'vasprun.xml'))
            if vasprun.converged:
                pass
            else:
                raise Exception('Not Converged')
        except: # if the run has not converged, setup a calculation
            os.makedirs(os.path.join(folder, dir), exist_ok=True)
            if not os.path.exists(os.path.join(folder, dir, 'WAVECAR')): # check if files exist to initialize run
                try: # copy them if provided
                    shutil.copy(os.path.join(dir_i, 'WAVECAR'), os.path.join(folder, dir, 'WAVECAR'))
                    shutil.copy(os.path.join(dir_i, 'CHGCAR'), os.path.join(folder, dir, 'CHGCAR'))
                    logging.info('Copied from {} to {} (in main dir)'.format(dir_i, os.path.join(folder, dir)))
                except: # if not, see if initialization exists in other folders
                    if os.path.exists(os.path.join(dir_i, 'above', 'vasprun.xml')) and \
                            os.path.exists(os.path.join(dir_i, 'below', 'vasprun.xml')):
                        vasprun_above = Vasprun(os.path.join(dir_i, 'above', 'vasprun.xml'))
                        vasprun_below = Vasprun(os.path.join(dir_i, 'below', 'vasprun.xml'))
                        if vasprun_above.final_energy < vasprun_below.final_energy:
                            lowest_dir = 'above'
                        else:
                            lowest_dir = 'below'
                        shutil.copy(os.path.join(dir_i, lowest_dir, 'WAVECAR'), os.path.join(folder, dir, 'WAVECAR'))
                        shutil.copy(os.path.join(dir_i, lowest_dir, 'CHGCAR'), os.path.join(folder, dir, 'CHGCAR'))
                        logging.info('Copied from {} to {}'.format(os.path.join(dir_i, lowest_dir), os.path.join(folder, dir)))
                        if vasprun_above.final_energy - vasprun_below.final_energy < target:
                            same_wfxns += 1

            if same_wfxns == 2: # If above and below are the same, we do not need to do above and below differently:
                logging.info('Wavefunctions are the same')
                if os.path.exists(os.path.join(folder, 'below')):
                    shutil.rmtree(os.path.join(folder, 'below'))
                shutil.copytree(os.path.join(folder, 'above'), os.path.join(folder, 'below'))
                os.chdir(folder)
                os.chdir(dir)
            else: # Otherwise don't copy anything between above and below
                shutil.copy('INCAR', os.path.join(folder, dir, 'INCAR'))
                shutil.copy('KPOINTS', os.path.join(folder, dir, 'KPOINTS'))
                shutil.copy('POTCAR', os.path.join(folder, dir, 'POTCAR'))
                os.chdir(folder)
                os.chdir(dir)
                Poscar(structure).write_file('POSCAR')
                incar = Incar.from_file('INCAR')
                if 'AUTO_GAMMA' in incar and incar['AUTO_GAMMA']:
                    vasp = os.environ['VASP_GAMMA']
                else:
                    vasp = os.environ['VASP_KPTS']
                incar.write_file('INCAR')

                if os.environ['VASP_MPI'] == 'srun':
                    j = StandardJob([os.environ['VASP_MPI'], vasp], 'vasp.log', auto_npar=False, final=True, settings_override=settings)
                else:
                    j = StandardJob([os.environ['VASP_MPI'], '-np', os.environ['PBS_NP'], vasp], 'vasp.log', auto_npar=False, final=True, settings_override=settings)
                c = Custodian(handlers, [j], max_errors=10)
                c.run()
            os.chdir(cwd)
    return get_energy(i, structure)


def get_ts(low, mp, high, target=0.01):
    """
    Find TS from string of structures using a ternary search
    :param low: low end index
    :param mp: midpoint index
    :param high: high ened index
    :param target: Convergence criteria
    :return: ts Structure
    """
    logging.info('Finding Max from locations : {} {} {}'.format(low, mp, high))

    # Initialize the high and low points
    start_struct = Structure.from_file(os.path.join(str(low).zfill(4), 'POSCAR'))
    final_struct = Structure.from_file(os.path.join(str(high).zfill(4), 'POSCAR'))
    if os.path.exists(os.path.join(str(mp).zfill(4), 'POSCAR')):
        mp_struct = Structure.from_file(os.path.join(str(mp).zfill(4), 'POSCAR'))
    else:
        mp_struct = nebmake('.', start_struct, final_struct, 2, write=False)[1]

    # Get energy of high and low structures
    low_e = get_energy(low, start_struct)
    high_e = get_energy(high, final_struct)
    logging.info('Converging Midpoint')
    mp_e = get_energy(mp, mp_struct)

    # Check if converged due to lack of resolution
    if mp == low or mp == high:
        logging.info('Found Max at : {} with E= {:.10}'.format(mp, mp_e))
        return mp
    # Check if converged due to reaching convergence criteria
    if abs(mp_e - high_e) < target and abs(mp_e - low_e) < target:
        logging.info('Found Max at : {} with E= {:.10}'.format(mp, mp_e))
        return mp
    q1_struct = nebmake('.', start_struct, mp_struct, 2, write=False)[1]
    q3_struct = nebmake('.', mp_struct, final_struct, 2, write=False)[1]

    # If not eliminate highest energy quartile and search again
    q1 = int((low+mp)/2)
    q3 = int((high+mp)/2)
    logging.info('Converging Q1')
    q1_e = get_energy(q1, q1_struct)
    logging.info('Converging Q3')
    q3_e = get_energy(q3, q3_struct)
    logging.info('Locations : {:<12} {:<12} {:<12}'.format(q1, mp, q3))
    logging.info('Energies  : {:.10} {:.10} {:.10}'.format(q1_e, mp_e, q3_e))
    if q3_e >= mp_e and q3_e >= q1_e:
        return get_ts(mp, q3, high)
    elif mp_e >= q1_e and mp_e >= q3_e:
        return get_ts(q1, mp, q3)
    elif q1_e >= mp_e and q1_e >= q3_e:
        return get_ts(low, q1, mp)
    else:
        raise Exception('Unknown error occured, check algorithms.py file')