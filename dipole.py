#!/usr/bin/env python
import argparse
import subprocess

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('axis', help='Axis to average along (1,2, or 3)',
                        type=int)
    parser.add_argument('atoms', help='Atoms to add up',
                        type=int, nargs='*')
    args = parser.parse_args()

    p = subprocess.Popen('chgsum.pl AECCAR0 AECCAR2')
    p.wait()
    p = subprocess.Popen('bader CHGCAR_sum')