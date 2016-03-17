#!/usr/bin/env python
# A general catch all function that runs VASP with just one command.  Automatically determines number of nodes to run on,
# based on NPAR and KPAR what type (NEB,Dimer,Standard) to run and sets up a submission script and runs it
#TODO: make silent work


from jinja2 import Environment, FileSystemLoader
from Classes_Pymatgen import *
from Helpers import *
import sys
import os
import shutil
import fnmatch
import cfg
import socket
import random
import argparse

def get_instructions_for_backup(jobtype, incar='INCAR'):
    '''

    Args:
        jobtype:
        incar:

    Returns: A dictionary that contains lists to backup, move, and execute in a shell

    '''
    instructions = {}
    instructions["commands"] = ['rm *.sh *.log *.out *.err STOPCAR *.e[0-9][0-9][0-9]* *.o[1-9][1-9][1-9]* *.log* &> /dev/null']
    instructions['backup'] = []
    instructions['move'] = []
    if jobtype == 'Standard':
        instructions['backup'] = ['OUTCAR', 'POSCAR', 'INCAR', 'KPOINTS']
        instructions['move'] = [('CONTCAR', 'POSCAR')]
    elif jobtype == 'NEB':
        if os.path.isfile(incar):
            incar = Incar.from_file(incar)
            instructions['commands'].extend(['nebmovie.pl', 'nebbarrier.pl', 'nebef.pl > nebef.dat'])
            instructions['backup'] = ['INCAR', 'KPOINTS', 'neb.dat', 'nebef.dat', 'movie.xyz']
            for i in range(1, int(incar["IMAGES"]) + 1):
                instructions['move'].append((os.path.join(str(i).zfill(2), 'CONTCAR'),
                                           os.path.join(str(i).zfill(2), 'POSCAR')))
                for f in ['OUTCAR', 'POSCAR']:
                    instructions['backup'].append(os.path.join(str(i).zfill(2), f))
        else:
            raise Exception('Need valid INCAR')
    elif jobtype == 'Dimer':
        instructions['backup'] = ['OUTCAR', 'POSCAR', 'INCAR', 'KPOINTS', 'MODECAR', 'DIMCAR']
        instructions['move'] = [('CENTCAR', 'POSCAR'), ('NEWMODECAR', 'MODECAR')]
    elif jobtype == 'GSM' or jobtype == 'SSM':
        instructions['backup'] = ['stringfile.xyz0000', 'inpfileq', 'scratch/initial0000.xyz', 'scratch/paragsm0000',
                                  'INCAR']
        if jobtype == 'SSM':
            instructions['backup'].append('scratch/ISOMERS0000')
    else:
        raise Exception('Jobtype Not recognized:  ' + jobtype)
    return instructions

def backup_vasp(dir, backup_dir='backup'):
    '''
    Do backup of given directory

    Args:
        dir: VASP directory to backup
        backup_dir: directory files will be backed up to

    Returns: None

    '''
    jobtype = getJobType(dir)

    if os.path.isdir(backup_dir):  # Find what directory to backup to
        last_run = -1
        backups = os.listdir(backup_dir)
        for backup in backups:
            try:
                if int(backup) > last_run:
                        last_run = int(backup)
            except:
                pass
        this_run = last_run+1
    else:
        this_run = 0
    backup_dir = os.path.join(backup_dir, str(this_run))

    instructions = get_instructions_for_backup(jobtype, os.path.join(dir, 'INCAR'))
    for command in instructions["commands"]:
        try:
            os.system(command)
        except:
            print('Could not execute command:  ' + command)
    for original_file in instructions["backup"]:
        try:
            backup_file = os.path.join(backup_dir, original_file)
            if not os.path.exists(os.path.dirname(backup_file)):
                os.makedirs(os.path.dirname(backup_file))
            shutil.copy(original_file, backup_file)
        except:
            print('Could not backup file at:  ' + original_file)

    return

def restart_vasp(dir):
    '''

    Args:
        dir:

    Returns:

    '''
    jobtype = getJobType(dir)
    instructions = get_instructions_for_backup(jobtype, os.path.join(dir, 'INCAR'))
    for (old_file, new_file) in instructions["move"]:
        try:
            if os.path.getsize(old_file) > 0:
                shutil.move(old_file, new_file)
                print('Moved ' + old_file + ' to ' + new_file)
            else:
                raise Exception()
        except:
            print('Unable to move ' + old_file + ' to ' + new_file)
    if jobtype == 'SSM':
        raise Exception('Make SSM run into GSM run')
    elif jobtype == 'GSM':
        with open('inpfileq') as inpfileq:
            lines = inpfileq.readlines()
            gsm_settings = list(map(lambda x: (x + ' 1').split()[0], lines))
        if 'RESTART' not in gsm_settings:
            lines.insert(len(lines)-1,'RESTART                 1\n')
            with open('inpfileq', 'w') as inpfileq:
                inpfileq.writelines(lines)
            print('RESTART added to inpfileq')

def get_queue(computer, jobtype, time, nodes):
    if computer == "janus":
        if time <= 24:
            return 'janus'
        elif time > 24:
            return 'janus-long'
    elif computer == "peregrine":
        if time <= 1 and nodes <= 4 and False:
            return 'debug'
        elif time <= 4 and nodes <= 8:
            return 'short'
        elif time <= 24 and nodes >= 16 and nodes <= 296:
            return 'large'
        elif time <= 48 and nodes <= 296:
            return 'batch-h'
        elif time > 48 and time <= 240 and nodes <= 120:
            return'long'
        else:
            raise Exception('Peregrine Queue Configuration not Valid: ' + time + ' hours ' + nodes + ' nodes ')
    elif computer == "psiops":
        if nodes <= 2:
            return 'gb'
        else:
            return 'ib'
    elif computer == "rapunzel":
        return 'batch'
    else:
        raise Exception('Unrecognized Computer')

def get_template(computer, jobtype):
    if jobtype == 'GSM' or jobtype == 'SSM':
        return(os.environ["VASP_TEMPLATE_DIR"], 'VASP.gsm.sh.jinja2')
    else:
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.standard.sh.jinja2')



parser = argparse.ArgumentParser()
parser.add_argument('-t', '--time', help='walltime for run (integer number of hours)',
                    type=int, default=0)
parser.add_argument('-o', '--nodes', help='nodes per run (default : KPAR*NPAR)',
                    type=int, default=0)
parser.add_argument('-q', '--queue', help='manually specify queue instead of auto determining')
parser.add_argument('-b', '--backup', help='backup files, but don\'t execute vasp ',
                    action='store_true')
parser.add_argument('-s', '--silent', help='display less information',
                    action='store_true')
parser.add_argument('-i', '--inplace', help='Run VASP without moving files to continue run',
                    action='store_true')
parser.add_argument('-n', '--name', help='name of run (Default is SYSTEM_Jobtype')
parser.add_argument('-g', '--gamma', help='force a gamma point run',
                    action='store_true')

args = parser.parse_args()

if __name__ == '__main__':
    jobtype = getJobType('.')
    incar = Incar.from_file('INCAR')
    computer = getComputerName()
    print('Running vasp.py for ' + jobtype +' on ' + computer)
    print('Backing up previous run')
    backup_vasp('.')
    if args.backup:
        exit(0)
    if not args.inplace:
        print('Setting up next run')
        restart_vasp('.')
    print('Determining settings for run')
    if args.time == 0:
        if 'AUTO_TIME' in incar:
            time = int(incar["AUTO_TIME"])
        elif 'VASP_DEFAULT_TIME' in os.environ:
            time = int(os.environ['VASP_DEFAULT_TIME'])
        else:
            time = 20
    else:
        time = args.time
    if args.nodes == 0:
        if 'AUTO_NODES' in incar:
            nodes = incar['AUTO_NODES']
        elif 'NPAR' in incar:
            nodes = int(incar['NPAR']) * int(incar['KPAR']) if 'KPAR' in incar else int(incar['NPAR'])
            if jobtype == 'NEB':
                nodes = nodes * int(incar["IMAGES"])
        else:
            raise Exception('No Nodes specifying need 1 of the following (in order of decreasing priority): \n-o option, AUTO_NODES in INCAR, or NPAR in INCAR')
    else:
        nodes = args.nodes

    if args.name:
        name = args.name
    elif 'SYSTEM' in incar:
        name = incar['SYSTEM'].strip().replace(' ', '_')
    elif 'System' in incar:
        name = incar['System'].strip().replace(' ', '_')
    elif 'system' in incar:
        name = incar['system'].strip().replace(' ', '_')

    if 'AUTO_MEM' in incar:
        mem = incar['AUTO_MEM']
    else:
        mem = 0

    if 'AUTO_GAMMA' in incar:
        auto_gamma = incar['AUTO_GAMMA']
    else:
        auto_gamma = 'True'

    if args.gamma:
        vasp_kpts = os.environ["VASP_GAMMA"]
    else:
        vasp_kpts = os.environ["VASP_KPTS"]


    if 'AUTO_CORES' in incar:
        cores = incar['AUTO_CORES']
    elif 'VASP_MPI_PROCS' in os.environ:
        cores = os.environ["VASP_MPI_PROCS"]
    else:
        cores = os.environ["VASP_NCORE"]

    if 'VASP_DEFAULT_ALLOCATION' in os.environ:
        account = os.environ['VASP_DEFAULT_ALLOCATION']
    else:
        account = ''

    if 'VASP_OMP_NUM_THREADS' in os.environ:
        openmp = os.environ['VASP_OMP_NUM_THREADS']
    else:
        openmp = 1

    if computer == 'janus' or computer == 'rapunzel':
        queue_type = 'slurm'
        submit = 'sbatch'
    else:
        queue_type = 'pbs'
        submit = 'qsub'

    if args.queue:
        queue = args.queue
    else:
        queue = get_queue(computer, jobtype, time, nodes)
    (template_dir, template) = get_template(computer, jobtype)
    script = 'vasp_standard.sh'

    keywords = {'queue_type'    : queue_type,
                'queue'         : queue,
                'nodes'         : nodes,
                'computer'      : computer,
                'time'          : time,
                'nodes'         : nodes,
                'name'          : name,
                'ppn'           : os.environ["VASP_NCORE"],
                'cores'         : cores,
                'logname'       : name + '.log',
                'mem'           : mem,
                'auto_gamma'    : auto_gamma,
                'account'       : account,
                'mpi'           : os.environ["VASP_MPI"],
                'vasp_kpts'     : vasp_kpts,
                'vasp_gamma'    : os.environ["VASP_GAMMA"],
                'jobtype'       : jobtype,
                'tasks'         : nodes*int(os.environ["VASP_NCORE"]),
                'openmp'        : openmp}

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template)
    with open(script, 'w+') as f:
        f.write(template.render(keywords))
    os.system(submit + ' ' + script)
    print('Submitted ' + name + ' to ' + queue)




