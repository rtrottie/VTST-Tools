#!/usr/bin/env python
import subprocess
import re
import numpy
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('OUTCAR', help='OUTCAR file (default = "OUTCAR")',
                    default='OUTCAR', nargs='?')
args = parser.parse_args()
#times = [i for i in subprocess.check_output(['grep', 'LOOP:', 'OUTCAR']).split('\n')]
time_lines = [s.split() for s in subprocess.check_output(['grep', 'LOOP:', args.OUTCAR]).decode().split('\n')]
times = [float(l[6]) for l in time_lines if (len(l) == 7 and re.match("^\d+?\.\d+?$", l[6]) != None)]

if len(times) > 6:
    times = times[5:]

print('MEAN:  ' + str(numpy.mean(times)) + '\nSTDV:  ' + str(numpy.std(times)))

pass
