#!/usr/bin/env python
#SBATCH -J {{ J }}
#SBATCH --time={{ time }}
#SBATCH -N {{ nodes }}
#SBATCH --ntasks-per-node {{ nntasks-per-node }}
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

digits = 3
prefix = 'rep_'
runtime = 8

nodes_per_image = sys.argv[1]
jobname = sys.argv[2]
logname = jobname + '.log'
script = jobname + '.log.sh'

incar = Incar.from_file('INCAR')

images = incar['IMAGES']
with open(script,'w+') as f:
    f.write(
"""#!/bin/bash


module load intel/intel-12.1.6
module load openmpi/openmpi-1.4.5_intel-12.1.6_ib
module load fftw/fftw-3.3.3_openmpi-1.4.5_intel-12.1.0_double_ib

mpirun -np """ + str(nodes_per_image*images*12) + """ /projects/musgravc/apps/red_hat6/vasp5.3.3/tst/gamma/vasp.5.3/vasp -d > """ + logname + """
exit 0""")

vaspjob = [NEBJob(['sbatch',script],script,auto_gamma=False)]
handlers = [WalltimeHandler(runtime*60*60,15*60)]
c = Custodian(handlers, vaspjob, max_errors=10)
c.run()
