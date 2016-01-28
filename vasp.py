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
    if jobtype == 'Standard':
        instructions['backup'] = ['OUTCAR', 'POSCAR', 'INCAR', 'KPOINTS']
        instructions['move'] = [('CONTCAR', 'POSCAR')]
    elif jobtype == 'NEB':
        if os.path.isfile(incar):
            incar = Incar.from_file(incar)
            instructions['commands'] = ['nebmovie.pl', 'nebbarrier.pl', 'nebef.pl > nebef.dat']
            instructions['backup'] = ['INCAR', 'KPOINTS', 'neb.dat', 'nebef.dat', 'movie.xyz']
            instructions['move'] = []
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
        pass
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
        except:
            pass
    if last_run == -1:
        raise Exception("backup setup is invalid")
    this_run = last_run+1
    if job == "NEB":
        os.system(os.path.join(os.environ['VTST_DIR'], 'nebbarrier.pl') + ';'+
                  os.path.join(os.environ['VTST_DIR'], 'nebef.pl > nebef.dat')) # do some post-processing only if this is not the first run
else:
    this_run = 0
os.makedirs(os.path.join(backup_dir, str(this_run))) # make backup directory

    instructions = get_instructions_for_backup(job, os.path.join(dir, 'INCAR'))
    for command in instructions["commands"]:
        os.system(command)

    return



parser = argparse.ArgumentParser()
parser.add_argument('-t', '--time', help='walltime for run (hours)',
                    type=int)
parser.add_argument('-n', '--nodes', help='nodes per run (default : KPAR*NPAR)',
                    type=int)
parser.add_argument('-b', '--backup', help='backup files, but don\'t execute vasp ',
                    action='store_true')


#########################################################################################3
## ABOVE THIS LINE IS REDONE, BELOW NEEDS TO BE REDONE, WOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO ##
##########################################################################################

# Backup Previous Run

job = getJobType(os.getcwd())
instructions = get_instructions_for_backup(job, 'INCAR')

print('Setting up ' + job + ' Job')

if os.path.isdir(backup_dir):  # Find what directory to backup to
    last_run = -1
    backups = os.listdir(backup_dir)
    for backup in backups:
        try:
            if int(backup) > last_run:
                last_run = int(backup)
        except:
            pass
    if last_run == -1:
        raise Exception("backup setup is invalid")
    this_run = last_run+1
    if job == "NEB":
        os.system(os.path.join(os.environ['VTST_DIR'], 'nebbarrier.pl') + ';'+
                  os.path.join(os.environ['VTST_DIR'], 'nebef.pl > nebef.dat')) # do some post-processing only if this is not the first run
else:
    this_run = 0
os.makedirs(os.path.join(backup_dir, str(this_run))) # make backup directory

#TODO actually backup files
#TODO keep timing data?
#TODO Template dir stuf
#   template_dir = os.environ['TEMPLATE_DIR']
#    template = 'VTST_Custodian.sh.jinja2'

if job == 'Dimer':

    keywords = {}
    if os.path.exists('CENTCAR') and os.path.getsize('CENTCAR') > 0:
        shutil.move('CENTCAR', 'POSCAR')
        shutil.copy('OUTCAR', os.path.join(backup_dir, str(this_run)))
    if os.path.exists('NEWMODECAR') and os.path.getsize('NEWMODECAR') > 0:
        shutil.move('NEWMODECAR', 'MODECAR')
    shutil.copy('POSCAR', os.path.join(backup_dir, str(this_run)))
    shutil.copy('INCAR', os.path.join(backup_dir, str(this_run)))
    shutil.copy('MODECAR', os.path.join(backup_dir, str(this_run)))
    try:
        shutil.copy('DIMCAR', os.path.join(backup_dir, str(this_run)))
        time = sum(getLoopPlusTimes('OUTCAR'))
    except:
        time = 0
elif job == 'Standard':
    template_dir = os.environ['TEMPLATE_DIR']
    template = 'VTST_Custodian.sh.jinja2'
    keywords = {}
    if os.path.exists('CONTCAR') and os.path.getsize('CONTCAR') > 0:
        shutil.move('CONTCAR', 'POSCAR')
    if os.path.exists('OUTCAR'):
        shutil.copy('OUTCAR', os.path.join(backup_dir, str(this_run)))
    shutil.copy('POSCAR', os.path.join(backup_dir, str(this_run)))
    shutil.copy('INCAR', os.path.join(backup_dir, str(this_run)))
    try:
        time = sum(getLoopPlusTimes('OUTCAR'))
    except:
        time = 0
elif job == 'GSM':
    template_dir = os.environ['TEMPLATE_DIR']
    template = 'submit.sh.jinja2'
    keywords = load_variables(os.path.join(os.environ['GSM_DIR'], 'VARS.jinja2'))
    string_files = filter(lambda s: s.startswith('stringfile.xyz') and s[-1].isdigit() and s[-2].isdigit(),  os.listdir('.'))
    keywords['iteration'] = 0
    if len(string_files) > 0:
        shutil.copy('stringfile.xyz0000', 'restart.xyz0000' )
        os.system('mkdir ' + os.path.join(backup_dir, str(this_run), 'scratch'))
        os.system('cp stringfile* ' + os.path.join(backup_dir, str(this_run)))
        for f in ['scratch/initial.xyz0000', 'scratch/paragsm0000', 'POSCAR.final', 'POSCAR.start', 'INCAR', 'KPOINTS']:
            try:
                shutil.copy(f, os.path.join(backup_dir, str(this_run), f))
            except:
                print(f + ' Not Copied')
        #os.system('find *' + '* -exec mv {} ' + os.path.join(backup_dir, str(this_run))  + '/ \;')
        #os.system('find scratch/*' + '* -exec mv {} ' + os.path.join(backup_dir, str(this_run), 'scratch')  + '/ \;')
        keywords['iteration'] = 0
        with open('inpfileq') as inpfileq:
            lines = inpfileq.readlines()
            gsm_settings = list(map(lambda x: (x + ' 1').split()[0], lines))
        if 'RESTART' not in gsm_settings:
            lines.insert(len(lines)-1,'RESTART                 1\n')
            with open('inpfileq', 'w') as inpfileq:
                inpfileq.writelines(lines)
    time = 'NOT APPLICABLE'
else:
    raise Exception('Not Yet Implemented Jobtype is:  ' + str(job))

with open(os.path.join(backup_dir, str(this_run), 'run_info'), 'w+') as f:
    f.write('time,'+str(time))

os.system('rm *.out *.err STOPCAR *.log.e* *.log.o*') # Clean directory and do basic-postprocessing
# Setup Templating for submit script

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
