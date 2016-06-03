#!/usr/bin/env python
import subprocess
import re
import numpy

#times = [i for i in subprocess.check_output(['grep', 'LOOP:', 'OUTCAR']).split('\n')]
time_lines = [s.split() for s in subprocess.check_output(['grep', 'LOOP:', 'OUTCAR']).split('\n')]
times = [float(l[6]) for l in time_lines if (len(l) == 7 and re.match("^\d+?\.\d+?$", l[6]) != None)]

if len(times) > 8:
    times = times[5:]

print('MEAN:  ' + str(numpy.mean(times)) + '\nSTDV:  ' + str(numpy.std(times)))

pass
