#!/usr/bin/env python
# A general catch all function that runs VASP with just one command.  Automatically determines number of nodes to run on,
# based on NPAR and KPAR what type (NEB,Dimer,Standard) to run and sets up a submission script and runs it
#TODO: fix how the time is setup

# Usage: VASP.py [time] [nodes] [log_file]

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
    instructions["commands"] = ['rm *.out *.err STOPCAR *.log.e* *.log.o* > /dev/null']
    instructions['backup'] = []
    instructions['move'] = []
    instructions['']
    if jobtype == 'Standard':
        instructions['backup'] = ['OUTCAR', 'POSCAR', 'INCAR', 'KPOINTS']
        instructions['move'] = [('CONTCAR', 'POSCAR')]
    elif jobtype == 'NEB':
        if os.path.isfile(incar):
            incar = Incar.from_file(incar)
            instructions['commands'].append(['nebmovie.pl', 'nebbarrier.pl', 'nebef.pl > nebef.dat'])
            instructions['backup'] = ['INCAR', 'KPOINTS', 'neb.dat', 'nebef.dat', 'movie.xyz']
            for i in range(int(incar["IMAGES"]) + 2):
                for f in ['OUTCAR', 'POSCAR']:
                    instructions['backup'].append(os.path.join(str(i).zfill(2), f))
                    instructions['move'].append((os.path.join(str(i).zfill(2), 'CONTCAR'),
                                               os.path.join(str(i).zfill(2), 'POSCAR')))
        else:
            raise Exception('Need valid INCAR')
    elif jobtype == 'Dimer':
        instructions['backup'] = ['OUTCAR', 'POSCAR', 'INCAR', 'KPOINTS', 'MODECAR', 'DIMCAR']
        instructions['move'] = [('CENTCAR', 'POSCAR'), ('NEWMODECAR', 'MODECAR')]
    elif jobtype == 'GSM':
        instructions['backup'] = ['stringfile.xyz0000', 'inpfileq', 'scratch/initial0000.xyz', 'scratch/paragsm0000',
                                  'INCAR']
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
            if int(backup) > last_run:
                    last_run = int(backup)
        if last_run == -1:
            raise Exception("backup setup is invalid")
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
            print('Could not backup file at:  ' + backup_file)

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
            shutil.move(old_file, new_file)
            print('Moved ' + old_file + ' to ' + new_file)
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



parser = argparse.ArgumentParser()
parser.add_argument('-t', '--time', help='walltime for run (hours)',
                    type=int)
parser.add_argument('-n', '--nodes', help='nodes per run (default : KPAR*NPAR)',
                    type=int)
parser.add_argument('-b', '--backup', help='backup files, but don\'t execute vasp ',
                    action='store_true')

parser.add_argument('-s', '--silent', help='display less information',
                    action='store_true')


#########################################################################################3
## ABOVE THIS LINE IS REDONE, BELOW NEEDS TO BE REDONE, WOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO ##
##########################################################################################

env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template(template)

# Use default arguments if not enough are provided
incar = Incar.from_file('INCAR')

if len(sys.argv) < 2:
    if 'AUTO_TIME' in incar:
        sys.argv.append(incar['AUTO_TIME'])
    elif 'psiops' in socket.gethostname():
        sys.argv.append(200)
    elif 'rapunzel' in socket.gethostname():
        sys.argv.append(500)
    else:
        sys.argv.append(20)

if len(sys.argv) < 3:
    if 'AUTO_NODES' in incar:
        nodes = incar['AUTO_NODES']
    else:
        if 'NPAR' in incar:
            nodes = incar['NPAR'] if 'KPAR' not in incar else int(incar['NPAR']) * int(incar['KPAR'])
        else:
            nodes = 1
    sys.argv.append(nodes)

if len(sys.argv) < 4:
    sys.argv.append(job + '_' + os.path.basename(os.getcwd()) + '.log')
    for file in os.listdir('.'):
        if fnmatch.fnmatch(file, '*.log'):
            sys.argv[3] = file
            break

# initialize variables for template

nodes_per_image = int(sys.argv[2])
jobname = sys.argv[3]
time = int(sys.argv[1])
if job == 'NEB':
    images = int(incar['IMAGES'])
else:
    images = 1
script = jobname + '.sh'

if 'AUTO_MEM' in incar:
    mem = incar['AUTO_MEM']
else:
    mem = 8000
if 'AUTO_GAMMA' in incar:
    auto_gamma = incar['AUTO_GAMMA']
else:
    auto_gamma = 'True'

connection = ''
queue = ''
if 'psiops' in socket.gethostname():
    host = 'psiops'
    mpi = '/home/apps/openmpi/openmpi-1.10.1/bin/mpirun'
    queue_sub = 'qsub'
    nntasks_per_node = 12
    if nodes_per_image == 1:
        connection = 'gb'
        vasp_tst_gamma = '/home/apps/vasp_tst/vasp.5.3/vasp'
        vasp_tst_kpts  = '/home/apps/vasp_tst/vasp.5.3/vasp'
    else:
        connection = 'ib'
        vasp_tst_gamma = '/home/apps/vasp_tst/vasp.5.3/vasp'
        vasp_tst_kpts  = '/home/apps/vasp_tst/vasp.5.3/vasp'
    if job == 'Standard':
        mpi = '/home/dummy/open_mpi_intel/openmpi-1.6/bin/mpiexec'
        vasp_tst_kpts = '/home/dummy/vasp5.12/stacked_cache/vasp.5.2/vasp'
        vasp_tst_gamma = '/home/dummy/vasp5.12/stacked_cache_gamma/vasp.5.2/vasp'
elif '.rc.' in socket.gethostname():
    vasp_tst_gamma = '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/gamma/vasp.5.3/vasp'
    vasp_tst_kpts = '/projects/musgravc/apps/vasp.5.3.3_vtst/kpts/vasp'
    host = 'janus'
    mpi = 'mpirun'
    queue_sub = 'sbatch'
    queue = 'janus' if time <= 24 else 'janus-long'
    nntasks_per_node = 12
elif 'rapunzel' in socket.gethostname():
    vasp_tst_gamma = '/export/home/apps/VASP/VTST.gamma/vasp'
    vasp_tst_kpts = '/export/home/apps/VASP/VTST/vasp.kpts'
    host = 'rapunzel'
    mpi = 'mpirun'
    queue_sub = 'sbatch'
    nntasks_per_node = 7
elif 'ryan-VirtualBox' in socket.gethostname():
    vasp_tst_gamma = '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/gamma/vasp.5.3/vasp'
    vasp_tst_kpts = '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/kpts/vasp.5.3/vasp'
    host = 'janus'
    nntasks_per_node = 1
    mpi = 'please dont run'
    queue_sub = 'sbatch'
elif 'login' in socket.gethostname():
    vasp_tst_gamma = 'vasp.gamma'
    vasp_tst_kpts = 'vasp.realk'
    host = 'peregrine'
    nntasks_per_node = 24
    mpi = 'mpirun'
    queue_sub = 'qsub'
    keywords['account'] = os.environ['DEFAULT_ALLOCATION']
    nodes = images*nodes_per_image
    if time <= 1 and nodes <= 4 and False:
        queue = 'debug'
    elif time <= 4 and nodes <= 8:
        queue = 'short'
    elif time <= 24 and nodes >= 16 and nodes <= 296:
        queue = 'large'
    elif time <= 48 and nodes <= 296:
        if random.random() < 0.5:
            queue = 'batch'
        else:
            queue = 'batch-h'
    else:
        raise Exception('Queue Configuration not Valid: ' + time + ' hours ' + nodes + ' nodes ')
else:
    raise Exception('Don\'t recognize host: ' + socket.gethostname())


keywords.update( {'J' : jobname,
            'hours' : time,
            'nodes' : images*nodes_per_image,
            'nntasks_per_node' : nntasks_per_node,
            'logname' : jobname,
            'tasks' : images*nodes_per_image*nntasks_per_node,
            'user' : os.environ['USER'],
            'jobtype' : job,
            'vasp_tst_gamma' : vasp_tst_gamma,
            'vasp_tst_kpts' : vasp_tst_kpts,
            'host' : host,
            'connection' : connection,
            'mpi' : mpi,
            'queue': queue,
            'mem': mem,
            'currdir': os.path.abspath('.'),
            'auto_gamma' : auto_gamma} )

with open(script, 'w+') as f:
    f.write(template.render(keywords))

os.system(queue_sub + ' ' + script)
