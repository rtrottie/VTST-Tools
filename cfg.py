# a general cfg file if you use scripts which change atoms, make sure these values fit your own i.e. have a
# cfg.py file before this one on your python path.  If an atom you want to use is missing just let me know
# and I can add it.  Variables at the end of this file should be declared in your .bashrc (or .my.bashrc on janus)

import subprocess

INCAR = {

    'LDAUL': {'default': -1,
              'Fe': 2,
              'Co': 2
              },
    'LDAUU': {'default': 0,
              'Fe': 3,
              'Co': 3
              },
    'MAGMOM' : {'default': 0,
                'Fe': 4,
                'Co': 5
                }
}

INCAR_format = [

    ('ALGORITHM - ELECTRONIC', ['ALGO', 'IALGO', 'NPAR', 'ENCUT', 'NELMIN', 'NELM', 'NELMDL',  'EDIFF']),
    ('ALGORITHM - IONIC', ['IBRION', 'NSW', 'POTIM', 'EDIFFG']),
    ('ALGORITHM - GENERAL', ['LREAL']),
    ('INPUT', ['ISTART', 'ICHARG']),
    ('OUTPUT', ['NWRITE', 'LORBIT', 'LAECHG']),
    ('ELECTRONIC STRUCTURE', ['ISPIN', 'MAGMOM', 'NBANDS', 'ISMEAR', 'SIGMA']),
    ('DFT+U', ['LDAU', 'LDAUTYPE', 'LDAUL', 'LDAUU', 'LMAXMIX', 'LDAUPRINT']),
    ('NEB', ['IMAGES', 'SPRING']),
    ('VTST', ['ICHAIN', 'IOPT'])

]

VTST_DIR = subprocess.check_output('echo $VTST_DIR', shell=True).strip()
TEMPLATE_DIR = subprocess.check_output('echo $TEMPLATE_DIR', shell=True).strip()
MAT_PROJ_KEY = subprocess.check_output('echo $MAT_PROJ_KEY', shell=True).strip()