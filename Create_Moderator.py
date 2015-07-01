#!/usr/bin/env python
from jinja2 import Environment, FileSystemLoader
from pymatgen.io.vaspio.vasp_input import Incar
import sys
import os
import shutil
import fnmatch

# Backup Previous Run

backup_dir = "backup"
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
    os.system('nebbarrier.pl') # do some post-processing only if this is not the first run
else:
    this_run = 0
os.makedirs(os.path.join(backup_dir, str(this_run))) # make backup directory

for dir in os.listdir('.'): # Move over CONTCARs from previous run, and stor POSCARs in backup folder
    if os.path.exists(os.path.join(dir,'CONTCAR')) and os.path.getsize(os.path.join(dir,'CONTCAR')) > 0:
        os.makedirs(os.path.join(backup_dir, str(this_run), dir))
        shutil.move(os.path.join(dir,'CONTCAR'), os.path.join(dir, 'POSCAR'))
        shutil.copy(os.path.join(dir,'POSCAR'), os.path.join(backup_dir, str(this_run), dir))
os.system('nebmovie.pl; rm *.out *.err *.sh *.py STOPCAR') # Clean directory and do basic-postprocessing
shutil.copy('INCAR', os.path.join(backup_dir, str(this_run)))
shutil.copy('movie.xyz', os.path.join(backup_dir, str(this_run)))
try:
    shutil.copy('neb.dat', os.path.join(backup_dir, str(this_run)))
except:
    pass

# Setup Templating for submit script

template_location = ('/home/rytr1806/NEB-Tools')
template = 'Simple_NEB_Moderator.jinja.py'
env = Environment(loader=FileSystemLoader(template_location))
template = env.get_template(template)

# Use default arguments if not enough are provided

if len(sys.argv) < 2:
    sys.argv.append(1)
if len(sys.argv) < 3:
    sys.argv.append('NEB_' + os.path.basename(os.getcwd()))
    for file in os.listdir('.'):
        if fnmatch.fnmatch(file, '*.log'):
            sys.argv[2] = file
            break
if len(sys.argv) < 4:
    sys.argv.append(16)

# initialize variables for template

nodes_per_image = int(sys.argv[1])
jobname = sys.argv[2]
time = int(sys.argv[3])
incar = Incar.from_file('INCAR')
images = int(incar['IMAGES'])
script = jobname + '.py'

keywords = {'J' : jobname,
            'hours' : time,
            'nodes' : images*nodes_per_image,
            'nntasks_per_node' : 12,
            'logname' : jobname,
            'tasks' : images*nodes_per_image*12,
            'user' : os.environ['USER']}

with open(script, 'w+') as f:
    f.write(template.render(keywords))

os.system('sbatch ' + script) 
