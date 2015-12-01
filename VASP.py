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

backup_dir = "backup"

# Backup Previous Run

job = getJobType(os.getcwd())

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
        os.system(os.path.join(cfg.VTST_DIR, 'nebbarrier.pl') + ';'+
                  os.path.join(cfg.VTST_DIR, 'nebef.pl > nebef.dat')) # do some post-processing only if this is not the first run
else:
    this_run = 0
os.makedirs(os.path.join(backup_dir, str(this_run))) # make backup directory

if job == 'NEB':  #backuping up files and setting up the templates for the jobs as well as setting template variables
    template_dir = cfg.TEMPLATE_DIR
    template = 'VTST_Custodian.sh.jinja2'
    keywords = {}
    times = []
    for dir in os.listdir('.'): # Move over CONTCARs from previous run, and store POSCARs in backup folder
        if os.path.exists(os.path.join(dir,'CONTCAR')) and os.path.getsize(os.path.join(dir,'CONTCAR')) > 0:
            os.makedirs(os.path.join(backup_dir, str(this_run), dir))
            shutil.move(os.path.join(dir,'CONTCAR'), os.path.join(dir, 'POSCAR'))
            shutil.copy(os.path.join(dir,'POSCAR'), os.path.join(backup_dir, str(this_run), dir))
            shutil.copy(os.path.join(dir,'OUTCAR'), os.path.join(backup_dir, str(this_run), dir))
            times.append(getLoopPlusTimes(os.path.join(dir, 'OUTCAR')))
        elif os.path.exists(os.path.join(dir,'POSCAR')):
            os.makedirs(os.path.join(backup_dir, str(this_run), dir))
            shutil.copy(os.path.join(dir,'POSCAR'), os.path.join(backup_dir, str(this_run), dir))
    shutil.copy('INCAR', os.path.join(backup_dir, str(this_run)))
    os.system('nebmovie.pl') # Clean directory and do basic-postprocessing
    shutil.copy('movie.xyz', os.path.join(backup_dir, str(this_run)))
    time = getMaxLoopTimes(times)
    try:
        shutil.copy('neb.dat', os.path.join(backup_dir, str(this_run)))
        shutil.copy('nebef.dat', os.path.join(backup_dir, str(this_run)))
    except:
        pass

elif job == 'Dimer':
    template_dir = cfg.TEMPLATE_DIR
    template = 'VTST_Custodian.sh.jinja2'
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
    template_dir = cfg.TEMPLATE_DIR
    template = 'VTST_Custodian.sh.jinja2'
    keywords = {}
    if os.path.exists('CONTCAR') and os.path.getsize('CONTCAR') > 0:
        shutil.move('CONTCAR', 'POSCAR')
        shutil.copy('OUTCAR', os.path.join(backup_dir, str(this_run)))
    shutil.copy('POSCAR', os.path.join(backup_dir, str(this_run)))
    shutil.copy('INCAR', os.path.join(backup_dir, str(this_run)))
    try:
        time = sum(getLoopPlusTimes('OUTCAR'))
    except:
        time = 0
elif job == 'GSM':
    template_dir = os.environ['GSM_DIR']
    template = 'submit.sh.jinja2'
    keywords = load_variables(os.path.join(os.environ['GSM_DIR'], 'VARS.jinja2'))
else:
    raise Exception('Not Yet Implemented Jobtype is:  ' + str(job))

with open(os.path.join(backup_dir, str(this_run), 'run_info'), 'w+') as f:
    f.write('time,'+str(time))

os.system('rm *.out *.err STOPCAR') # Clean directory and do basic-postprocessing
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

connection = ''
queue = ''
if job == 'Dimer' or job == 'NEB':
    if 'psiops' in socket.gethostname():
        host = 'psiops'
        mpi = '/home/dummy/open_mpi_intel/openmpi-1.6/bin/mpiexec'
        queue_sub = 'qsub'
        nntasks_per_node = 12
        if nodes_per_image == 1:
            connection = 'gb'
            vasp_tst_gamma = '/home/dummy/vasp5.12/tst/gamma/vasp.5.2/vasp'
            vasp_tst_kpts = '/home/dummy/vasp5.12/tst/kpoints/vasp.5.2/vasp'
        else:
            connection = 'ib'
            vasp_tst_gamma = '/home/dummy/vasp5.12/tst/gamma/vasp.5.2/vasp'
            vasp_tst_kpts = '/home/dummy/vasp5.12/tst/kpoints/vasp.5.2/vasp'
    elif '.rc.' in socket.gethostname():
        vasp_tst_gamma = '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/gamma/vasp.5.3/vasp'
        vasp_tst_kpts = '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/kpts/vasp.5.3/vasp'
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

    else:
        raise Exception('Don\'t recognize host: ' + socket.gethostname())
elif job == 'Standard':
    if 'psiops' in socket.gethostname():
        host = 'psiops'
        mpi = '/home/dummy/open_mpi_intel/openmpi-1.6/bin/mpiexec'
        queue_sub = 'qsub'
        vasp_tst_gamma = '/home/dummy/vasp.5.3.3/kpts/vasp.5.3/vasp'
        vasp_tst_kpts = '/home/dummy/vasp.5.3.3/kpts/vasp.5.3/vasp'
        nntasks_per_node = 12
        if nodes_per_image == 1:
            connection = 'gb'
        else:
            connection = 'ib'
    elif '.rc.' in socket.gethostname():
        vasp_tst_gamma = '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/gamma/vasp.5.3/vasp'
        vasp_tst_kpts = '/projects/musgravc/apps/vasp.5.3.3_vtst/kpts/vasp'
        host = 'janus'
        mpi = 'mpirun'
        queue_sub = 'sbatch'
        queue = 'janus' if time < 24 else 'janus-long'
        nntasks_per_node = 12
    elif 'rapunzel' in socket.gethostname():
        vasp_tst_gamma = '/export/home/apps/VASP/VTST/vasp.gamma'
        vasp_tst_kpts = '/export/home/apps/VASP/VTST/vasp.kpts'
        host = 'rapunzel'
        mpi = 'mpirun'
        queue_sub = 'sbatch'
        nntasks_per_node = 7
    elif 'ryan-VirtualBox' in socket.gethostname():
        vasp_tst_gamma = '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/gamma/vasp.5.3/vasp'
        vasp_tst_kpts = '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/kpts/vasp.5.3/vasp'
        host = 'janus'

    else:
        raise Exception('Don\'t recognize host: ' + socket.gethostname())
else:
    raise Exception('Don\'t recognize jobtype: ' + job)

keywords.update( {'J' : jobname,
            'hours' : time,
            'nodes' : images*nodes_per_image,
            'nntasks_per_node' : nntasks_per_node,
            'logname' : jobname,
            'tasks' : images*nodes_per_image*12,
            'user' : os.environ['USER'],
            'jobtype' : job,
            'vasp_tst_gamma' : vasp_tst_gamma,
            'vasp_tst_kpts' : vasp_tst_kpts,
            'host' : host,
            'connection' : connection,
            'mpi' : mpi,
            'queue': queue,
            'mem': mem,
            'currdir': os.path.abspath('.')} )

with open(script, 'w+') as f:
    f.write(template.render(keywords))

os.system(queue_sub + ' ' + script)
