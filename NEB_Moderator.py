#!/usr/bin/env python

import sys
import os
from custodian.vasp.jobs import *
from custodian.vasp.handlers import *

digits = 3
prefix = 'rep_'
runtime = 8

nodes_per_image = sys.argv[1]
jobname = sys.argv[2]
logname = jobname + '.log'
script = jobname + '.log.sh'

# Determine which folder to run from

def find_last_dir(accum_value,x):
    if len(x) != (len(prefix)+digits):
        return accum_value
    elif x[:len(prefix)] != prefix:
        return accum_value
    elif int(x[len(prefix):len(prefix)+digits]) < accum_value[1]:
        return accum_value
    else:
        return (x[len(prefix):len(prefix)+digits],int(x[len(prefix):len(prefix)+digits]))

current_dir_tup = reduce(find_last_dir, next(os.walk('.'))[1],('',-1))
current_dir = prefix + current_dir_tup[0]

os.chdir(os.path.join(os.path.abspath(os.curdir), current_dir))
print os.path.abspath('.')

print current_dir

with open(script,'w+') as f:
    f.write(
"""#!/bin/bash"
#SBATCH -J """ + jobname + """
#SBATCH --time= + """ + runtime + """:00:00
#SBATCH -N """ + str(nodes_per_image) + """
#SBATCH --ntasks-per-node 12
#SBATCH -o """ + logname + """-%j.out
#SBATCH -e """ + logname + """-%j.err
#SBATCH --qos=normal

module load intel/intel-12.1.6
module load openmpi/openmpi-1.4.5_intel-12.1.6_ib
module load fftw/fftw-3.3.3_openmpi-1.4.5_intel-12.1.0_double_ib

mpirun -np """ + nodes_per_image + """ /export/home/tester/VASP/vasp.5.3/vasp -d > """ + logname + """
exit 0""")
 
vaspjob = VaspJob(['sbatch',script],script,auto_gamma=False)
handlers = WalltimeHandler(runtime*60*60,15*60)