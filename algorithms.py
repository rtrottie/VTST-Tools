from Classes_Pymatgen import Vasprun, Structure, Poscar, Incar
from custodian.custodian import Custodian
from Classes_Custodian import StandardJob
import os
import shutil
import logging
from Neb_Make import nebmake

def get_energy(i, structure : Structure):
    cwd = os.path.abspath('.')
    handlers = []
    settings = [
        {'dict': 'INCAR',
         'action': {'_set': {'NSW': 0,
                             'IOPT': 0,
                             'IBRION': -1,
                             'EDIFFG': -1000},
                    }}
    ]
    folder = os.path.join(cwd, str(i).zfill(4))
    if os.path.exists(folder):
        Poscar(structure).write_file(os.path.join(folder, 'POSCAR'))
        try:
            vasprun_above = Vasprun(os.path.join(folder, 'above', 'vasprun.xml'))
            vasprun_below = Vasprun(os.path.join(folder, 'below', 'vasprun.xml'))
            if vasprun_above.converged and vasprun_below.converged:
                with open(os.path.join(folder, 'energy.txt'), 'w') as f:
                    f.write(str(min(vasprun_above.final_energy, vasprun_below.final_energy)))
                return min(vasprun_above.final_energy, vasprun_below.final_energy)
        except:
            try:
                vasprun = Vasprun(os.path.join(folder, 'vasprun.xml'))
                if vasprun.converged:
                    with open(os.path.join(folder, 'energy.txt'), 'w') as f:
                        f.write(str(vasprun.final_energy))
                    return vasprun.final_energy
            except:
                pass
    else:
        os.mkdir(folder)
    above = None
    below = None
    for dir in [dir for dir in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, dir))]:
        try:
            dir_i = int(dir)
            if i == dir_i:
                pass
            if dir_i > i:
                if above == None:
                    above = dir_i
                elif dir_i - i < above - i:
                    above = dir_i
            elif dir_i < i:
                if below == None:
                    below = dir_i
                elif dir_i - i < below - i:
                    below = dir_i

            elif closest == None:
                closest = dir
            elif abs(i - int(closest)) >= abs(i - int(dir)):
                closest = dir
        except:
            pass
    for dir_i, dir in [(str(above).zfill(4), 'above'), (str(below).zfill(4), 'below')]:
        try:
            vasprun = Vasprun(os.path.join(folder, dir, 'vasprun.xml'))
            if vasprun.converged:
                pass
            else:
                raise Exception('Not Converged')
        except:
            os.makedirs(os.path.join(folder, dir), exist_ok=True)
            if not os.path.exists(os.path.join(folder, dir, 'WAVECAR')):
                try:
                    shutil.copy(os.path.join(dir_i, 'WAVECAR'), os.path.join(folder, dir, 'WAVECAR'))
                    shutil.copy(os.path.join(dir_i, 'CHGCAR'), os.path.join(folder, dir, 'CHGCAR'))
                except:
                    vasprun_above = Vasprun(os.path.join(dir_i, 'above', 'vasprun.xml'))
                    vasprun_below = Vasprun(os.path.join(dir_i, 'below', 'vasprun.xml'))
                    if vasprun_above.final_energy < vasprun_below.final_energy:
                        lowest_dir = 'above'
                    else:
                        lowest_dir = 'below'
                    shutil.copy(os.path.join(dir_i, lowest_dir, 'WAVECAR'), os.path.join(folder, dir, 'WAVECAR'))
                    shutil.copy(os.path.join(dir_i, lowest_dir, 'CHGCAR'), os.path.join(folder, dir, 'CHGCAR'))


            shutil.copy('INCAR', os.path.join(folder, dir, 'INCAR'))
            shutil.copy('KPOINTS', os.path.join(folder, dir, 'KPOINTS'))
            shutil.copy('POTCAR', os.path.join(folder, dir, 'POTCAR'))
            os.chdir(folder)
            os.chdir(dir)
            Poscar(structure).write_file('POSCAR')
            incar = Incar.from_file('INCAR')
            if ('AUTO_GAMMA' in incar and incar['AUTO_GAMMA']):
                vasp = os.environ['VASP_GAMMA']
            else:
                vasp = os.environ['VASP_KPTS']
            j = StandardJob([os.environ['VASP_MPI'], '-np', os.environ['PBS_NP'], vasp], 'vasp.log', auto_npar=False, final=True, settings_override=settings)
            c = Custodian(handlers, [j], max_errors=10)
            c.run()
            os.chdir(cwd)
    return get_energy(i, structure)

def get_ts(low, mp, high, target=0.01):
    logging.info('Finding Max from locations : {} {} {}'.format(low, mp, high))
    if mp == low or mp == high:
        logging.info('Found Max at : {} with E= {:.10}'.format(mp, ))
        return mp

    start_struct = Structure.from_file(os.path.join(str(low).zfill(4), 'POSCAR'))
    final_struct = Structure.from_file(os.path.join(str(high).zfill(4), 'POSCAR'))
    if os.path.exists(os.path.join(str(mp).zfill(4), 'POSCAR')):
        mp_struct = Structure.from_file(os.path.join(str(mp).zfill(4), 'POSCAR'))
    else:
        mp_struct = nebmake('.', start_struct, final_struct, 2, write=False)[1]

    low_e = get_energy(low, start_struct)
    high_e = get_energy(high, final_struct)
    logging.info('Converging Midpoint')
    mp_e = get_energy(mp, mp_struct)

    if abs(mp_e - high_e) < target and abs(mp_e - low_e) < target:
        logging.info('Found Max at : {} with E= {:.10}'.format(mp, ))
        return mp
    q1_struct = nebmake('.', start_struct, mp_struct, 2, write=False)[1]
    q3_struct = nebmake('.', mp_struct, final_struct, 2, write=False)[1]

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
        raise Exception('WHHHHYYY')