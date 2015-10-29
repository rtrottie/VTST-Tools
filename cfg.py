# a general cfg file if you use scripts which change atoms, make sure these values fit your own i.e. have a
# cfg.py file before this one on your python path.  If an atom you want to use is missing just let me know
# and I can add it.  Variables at the end of this file should be declared in your .bashrc (or .my.bashrc on janus)

import subprocess

INCAR = {

    'LDAUL': {'default': -1,
              'Fe': 2,
              'Co': 2,
              'Ni': 2,
              'Cu': 2
              },
    'LDAUU': {'default': 0,
              'Fe': 3,
              'Co': 3,
              'Ni': 3,
              'Cu': 5
              },
    'MAGMOM' : {'default': 0,
                'Fe': 4,
                'Co': 5,
                'Ni': 4,
                'Cu': 3
                }
}

INCAR_format = [
    ('ALGORITHM - ELECTRONIC', ['ALGO', 'IALGO', 'NPAR', 'KPAR', 'PREC', 'ENCUT', 'NELMIN', 'NELM', 'NELMDL',  'EDIFF', 'NELECT']),
    ('ALGORITHM - IONIC', ['IBRION', 'NSW', 'POTIM', 'EDIFFG', 'ISIF']),
    ('ALGORITHM - GENERAL', ['LREAL']),
    ('INPUT', ['ISTART', 'ICHARG']),
    ('OUTPUT', ['NWRITE', 'LORBIT', 'LAECHG', 'LWAVE']),
    ('ELECTRONIC STRUCTURE', ['ISPIN', 'MAGMOM', 'NBANDS', 'ISMEAR', 'SIGMA']),
    ('DFT+U', ['LDAU', 'LDAUTYPE', 'LDAUL', 'LDAUU', 'LMAXMIX', 'LDAUPRINT']),
    ('NEB', ['IMAGES', 'SPRING']),
    ('VTST', ['ICHAIN', 'IOPT', 'LCLIMB']),
    ('SETUP', ['AUTO_TIME', 'AUTO_NODES', 'STAGE_NUMBER', 'STAGE_NAME'])

]

VTST_DIR = subprocess.check_output('echo $VTST_DIR', shell=True).strip()
TEMPLATE_DIR = subprocess.check_output('echo $TEMPLATE_DIR', shell=True).strip()
MAT_PROJ_KEY = subprocess.check_output('echo $MAT_PROJ_KEY', shell=True).strip()