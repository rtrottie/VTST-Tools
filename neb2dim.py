#!/usr/bin/env python
# attempts to Fully initialize (changes ICHAIN) from an NEB run, still has a few issues

# Usage: neb2dim.py NEB_dir [Dim_dir]

from Helpers import *
import sys
import os

if len(sys.argv) < 3:
    sys.argv.append(os.path.abspath('.'))

neb2dim(sys.argv[1], sys.argv[2])