#!/usr/bin/env python

import argparse
import pyamtgen

parser = argparse.ArgumentParser()

parser.add_argument('initial', help='Structure or VASP run folder of initial state')
parser.add_argument('final', help='Structure or VASP run folder of final state')