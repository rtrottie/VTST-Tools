#!/usr/bin/env python
#SBATCH -J {{ J }}
#SBATCH --time={{ hours }}:00:00
#SBATCH -N {{ nodes }}
#SBATCH --ntasks-per-node {{ nntasks_per_node }}
#SBATCH -o {{ logname }}-%j.out
#SBATCH -e {{ logname }}-%j.err
#SBATCH --qos=normal

# Load important modules and ensure environemnt variables are correctly set up

module load python/anaconda-2.0.1
module load fftw/fftw-3.3.3_openmpi-1.4.5_intel-12.1.0_double_ib
module load intel/intel-12.1.6;
module load openmpi/openmpi-1.4.5_intel-12.1.6_ib;
PYTHONPATH=$PYTHONPATH:/home/rytr1806/NEB-Tools
export OMP_NUM_THREADS=1

# Execute python commands, could be separated into a separate file, but 1 file is easier to template.

python -c "

import sys
import os
import shutil
from custodian.vasp.jobs import *
from custodian.vasp.handlers import *
from custodian.custodian import *
import pymatgen
from pymatgen.io.vaspio.vasp_input import *
from pymatgen.io.vaspio_set import *
from Classes_Custodian import *


vaspjob = [NEBJob(['mpirun', '-np', '{{ tasks }}', '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/kpts/vasp.5.3/vasp', '-t', '/lustre/janus_scratch/{{ user }}', '-d'], '{{ logname }}', gamma_vasp_cmd=['mpirun', '-np', '{{ tasks }}', '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/gamma/vasp.5.3/vasp', '-t', '/lustre/janus_scratch/{{ user }}', '-d'],auto_npar=False)]
handlers = [WalltimeHandler({{ hours }}*60*60), NEBNotTerminating({{ logname }}, 15*60)]
c = Custodian(handlers, vaspjob, max_errors=10)
c.run()"
