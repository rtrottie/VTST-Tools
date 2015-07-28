#!/usr/bin/env python
from jinja2 import Environment, FileSystemLoader
from pymatgen.io.vaspio.vasp_input import Incar
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

if job == 'NEB':
    times = []
    for dir in os.listdir('.'): # Move over CONTCARs from previous run, and store POSCARs in backup folder
        if os.path.exists(os.path.join(dir,'CONTCAR')) and os.path.getsize(os.path.join(dir,'CONTCAR')) > 0:
            os.makedirs(os.path.join(backup_dir, str(this_run), dir))
            shutil.move(os.path.join(dir,'CONTCAR'), os.path.join(dir, 'POSCAR'))
            shutil.copy(os.path.join(dir,'POSCAR'), os.path.join(backup_dir, str(this_run), dir))
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
    if os.path.exists('CONTCAR') and os.path.getsize('CONTCAR') > 0:
        shutil.move('CONTCAR', 'POSCAR')
    if os.path.exists('NEWMODECAR') and os.path.getsize('NEWMODECAR') > 0:
        shutil.move('NEWMODECAR', 'MODECAR')
    shutil.copy('POSCAR', os.path.join(backup_dir, str(this_run)))
    shutil.copy('INCAR', os.path.join(backup_dir, str(this_run)))
    try:
        shutil.copy('DIMCAR', os.path.join(backup_dir, str(this_run)))
        time = sum(getLoopPlusTimes('OUTCAR'))
    except:
        time = 0
else:
    raise Exception('Not Yet Implemented Jobtype is:  ' + str(job))

with open(os.path.join(backup_dir, str(this_run), 'run_info'), 'w+') as f:
    f.write('time,'+str(time))

os.system('rm *.out *.err *.sh *.py STOPCAR') # Clean directory and do basic-postprocessing
# Setup Templating for submit script

template_dir = cfg.TEMPLATE_DIR
template = 'VTST_Custodian.sh.jinja2'
env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template(template)

# Use default arguments if not enough are provided

incar = Incar.from_file('INCAR')
if len(sys.argv) < 2:
    sys.argv.append(incar['NPAR'])

if len(sys.argv) < 3:
    sys.argv.append(job + '_' + os.path.basename(os.getcwd()))
    for file in os.listdir('.'):
        if fnmatch.fnmatch(file, '*.log'):
            sys.argv[2] = file
            break
if len(sys.argv) < 4:
    sys.argv.append(24)

# initialize variables for template

nodes_per_image = int(sys.argv[1])
jobname = sys.argv[2]
time = int(sys.argv[3])
if job == 'NEB':
    images = int(incar['IMAGES'])
else:
    images = 1
script = jobname + '.sh'

if 'psiops' in socket.gethostname():
    raise Exception('Haven\'t implemented psiops script yet')
elif '.rc.' in socket.gethostname():
    vasp_tst_gamma = '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/gamma/vasp.5.3/vasp'
    vasp_tst_kpts = '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/kpts/vasp.5.3/vasp'
    host = 'janus'
elif 'rapunzel' in socket.gethostname():
    raise Exception('Haven\'t implemented psiops script yet')
else:
    raise Exception('Don\'t recognize host: ' + socket.gethostname())

keywords = {'J' : jobname,
            'hours' : time,
            'nodes' : images*nodes_per_image,
            'nntasks_per_node' : 12,
            'logname' : jobname,
            'tasks' : images*nodes_per_image*12,
            'user' : os.environ['USER'],
            'jobtype' : job,
            'vasp_tst_gamma' : vasp_tst_gamma,
            'vasp_tst_kpts' : vasp_tst_kpts,
            'host' : host}

with open(script, 'w+') as f:
    f.write(template.render(keywords))

os.system('sbatch ' + script) 
