import subprocess

INCAR = {

    'LDAUL': {'default': -1,
              'Fe': 2,
              'Co': 2},

    'LDAUU': {'default': 0,
              'Fe': 3,
              'Co': 2}
}

VTST_DIR = subprocess.check_output('echo $VTST_DIR', shell=True).strip()