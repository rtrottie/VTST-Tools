#!/usr/bin/env python
# A general catch all function that runs VASP with just one command.  Automatically determines number of nodes to run on,
# based on NPAR and KPAR what type (NEB,Dimer,Standard) to run and sets up a submission script and runs it

from jinja2 import Environment, FileSystemLoader
from Classes_Pymatgen import *
from pymatgen.io.vasp.outputs import *
from Helpers import *
import sys
import os
import shutil
import fnmatch
import cfg
import socket
import random
import argparse
import subprocess

def get_instructions_for_backup(incar='INCAR'):
    '''

    Args:
        jobtype:
        incar:

    Returns: A dictionary that contains lists to backup, move, and execute in a shell

    '''
    instructions = {}
    instructions["commands"] = ['rm *.sh *.out *.err STOPCAR *.e[0-9][0-9][0-9]* *.o[1-9][1-9][1-9]* *.log* &> /dev/null']
    instructions['backup'] = []
    instructions['move'] = []

    for f in os.listdir('.'):
        if '.log' in f:
            instructions['backup'].append(f)

    return instructions

def backup_gauss(dir, backup_dir='backup'):
    '''
    Do backup of given directory

    Args:
        dir: VASP directory to backup
        backup_dir: directory files will be backed up to

    Returns: None

    '''

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

    instructions = get_instructions_for_backup()
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

def restart_gauss(dir):
    '''

    Args:
        dir:

    Returns:

    '''
    instructions = get_instructions_for_backup()
    for (old_file, new_file) in instructions["move"]:
        try:
            if os.path.getsize(old_file) > 0:
                shutil.copy(old_file, new_file)
                print('Moved ' + old_file + ' to ' + new_file)
            else:
                raise Exception()
        except:
            print('Unable to move ' + old_file + ' to ' + new_file)

def get_queue(computer, jobtype, time, nodes):
    if computer == "janus":
        if time <= 24:
            return 'janus'
        elif time > 24:
            return 'janus-long'
    elif computer == "summit":
        if time <= 1:
            return 'debug'
        elif time <= 24:
            return 'normal'
        elif time > 24:
            return 'long'
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
        if nodes <= 1:
            return 'gb'
        else:
            return 'ib'
    elif computer == "rapunzel":
        return 'batch'
    else:
        raise Exception('Unrecognized Computer')

def get_template(computer, jobtype, special=None):
    if special == 'multi':
        return (os.environ["VASP_TEMPLATE_DIR"], 'VASP.multistep.jinja2.py')
    else:
        return (os.environ["VASP_TEMPLATE_DIR"], 'gauss.peregrine.sh.jinja2')

parser = argparse.ArgumentParser()
parser.add_argument('name', help='name of run (Default is *.gjf',
                    nargs='?', default=None)
parser.add_argument('-t', '--time', help='walltime for run (integer number of hours)',
                    type=int, default=0)
parser.add_argument('-o', '--nodes', help='nodes per run (default : 1',
                    type=int, default=1)
parser.add_argument('-c', '--cores', help='cores per run (default : max allowed per system)',
                    type=int)
parser.add_argument('-q', '--queue', help='manually specify queue instead of auto determining')
parser.add_argument('-b', '--backup', help='backup files, but don\'t execute vasp ',
                    action='store_true')
parser.add_argument('-s', '--silent', help='display less information',
                    action='store_true')
parser.add_argument('-i', '--inplace', help='Run VASP without moving files to continue run',
                    action='store_true')

args = parser.parse_args()

if __name__ == '__main__':

    jobtype = 'gauss'
    computer = getComputerName()
    print('Running Gauss.py for ' +' on ' + computer)
    print('Backing up previous run')
    backup_gauss('.')
    if args.backup:
        exit(0)
    if not args.inplace:
        print('Setting up next run')
        restart_gauss('.')
    print('Determining settings for run')
    if args.time == 0:
        if 'VASP_DEFAULT_TIME' in os.environ:
            time = int(os.environ['VASP_DEFAULT_TIME'])
        else:
            time = 24
    else:
        time = args.time

    nodes = args.nodes
    if not args.name:
        for f in os.listdir('.'):
            if '.gjf' in f:
                name = f
    else:
        name = args.name
    if '.gjf' in f:
        name = name[:-4]

    if args.cores:
        cores = args.cores
    elif 'VASP_MPI_PROCS' in os.environ:
        cores = int(os.environ["VASP_MPI_PROCS"])
    else:
        cores = int(os.environ["VASP_NCORE"])

    if 'VASP_DEFAULT_ALLOCATION' in os.environ:
        account = os.environ['VASP_DEFAULT_ALLOCATION']
    else:
        account = ''

    if 'VASP_OMP_NUM_THREADS' in os.environ:
        openmp = int(os.environ['VASP_OMP_NUM_THREADS'])
    else:
        openmp = 1

    if computer == 'janus' or computer == 'rapunzel' or computer=='summit':
        queue_type = 'slurm'
        submit = 'sbatch'
    else:
        queue_type = 'pbs'
        submit = 'qsub'

    if args.queue:
        queue = args.queue
    else:
        queue = get_queue(computer, jobtype, time, nodes)

    additional_keywords = {}
    special = None

    (template_dir, template) = get_template(computer, jobtype, special)
    script = 'gauss_standard.sh'

    keywords = {'queue_type'    : queue_type,
                'queue'         : queue,
                'nodes'         : nodes,
                'computer'      : computer,
                'time'          : time,
                'nodes'         : nodes,
                'name'          : name,
                'ppn'           : cores,
                'cores'         : cores,
                'logname'       : name + '.log',
                'account'       : account,
                'gauss_bashrc'   : os.environ['GAUSS_BASHRC'] if 'GAUSS_BASHRC' in os.environ else '~/.bashrc_gauss',
                'jobtype'       : jobtype,
                'tasks'         : int(nodes*cores/openmp),
                'openmp'        : openmp}
    keywords.update(additional_keywords)

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template)
    with open(script, 'w+') as f:
        f.write(template.render(keywords))
    subprocess.call([submit, script])
    print('Submitted ' + name + ' to ' + queue)




