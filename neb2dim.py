#!/usr/bin/env python
from Helpers import *
import sys
import os

if len(sys.argv) < 3:
    sys.argv.append(os.path.abspath('.'))

neb2dim(sys.argv[1], sys.argv[2])