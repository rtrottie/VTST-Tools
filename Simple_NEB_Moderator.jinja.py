#!/usr/bin/env python
#SBATCH -J {{ J }}
#SBATCH --time={{ hours }}:00:00
#SBATCH -N {{ nodes }}
#SBATCH --ntasks-per-node {{ nntasks_per_node }}
#SBATCH -o {{ logname }}-%j.out
#SBATCH -e {{ logname }}-%j.err
#SBATCH --qos=normal

import sys
import os
import shutil
from custodian.vasp.jobs import *
from custodian.vasp.handlers import *
from custodian.custodian import *
import pymatgen
from pymatgen.io.vaspio.vasp_input import *
from pymatgen.io.vaspio_set import *
from Classes import *

modules = '''module load intel/intel-12.1.6;
module load openmpi/openmpi-1.4.5_intel-12.1.6_ib;
module load fftw/fftw-3.3.3_openmpi-1.4.5_intel-12.1.0_double_ib'''
os.system(modules)

vaspjob = [NEBJob(['mpirun', '-np', '{{ tasks }}', '-d' '/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/kpts/vasp.5.3/vasp'],
                  {{ logname }}, gamma_vasp_cmd='/projects/musgravc/apps/red_hat6/vasp5.3.3/tst/gamma/vasp.5.3/vasp',auto_npar=False)]
handlers = [WalltimeHandler({{ hours }}*60*60,15*60)]
c = Custodian(handlers, vaspjob, max_errors=10)
c.run()
