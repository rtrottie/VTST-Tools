# a general cfg file if you use scripts which change atoms, make sure these values fit your own i.e. have a
# cfg.py file before this one on your python path.  If an atom you want to use is missing just let me know
# and I can add it.  Variables at the end of this file should be declared in your .bashrc (or .my.bashrc on janus)

import os

INCAR = {

    'LDAUL': {'default': -1,
              'Fe': 2,
              'Co': 2,
              'Ni': 2,
              'Cu': 2,
              'Mn': 2
              },
    'LDAUU': {'default': 0,
              'Fe': 3,
              'Co': 3,
              'Ni': 3,
              'Cu': 5,
              'Mn': 3
              },
    'MAGMOM' : {'default': 0,
                'Fe': 4,
                'Co': 5,
                'Ni': 4,
                'Cu': 3,
                'Mn': 5
                }
}

INCAR_format = [
    ('ALGORITHM - GENERAL', ['NPAR', 'KPAR', 'LREAL']),
    ('ALGORITHM - ELECTRONIC', ['ALGO', 'IALGO', 'PREC', 'ENCUT', 'NELMIN', 'NELM', 'NELMDL',  'EDIFF', 'NELECT']),
    ('ALGORITHM - IONIC', ['IBRION', 'NSW', 'POTIM', 'EDIFFG', 'ISIF']),
    ('INPUT', ['ISTART', 'ICHARG', 'KSPACING']),
    ('OUTPUT', ['NWRITE', 'LORBIT', 'LAECHG', 'LWAVE', 'LCHARG']),
    ('ELECTRONIC STRUCTURE', ['ISPIN', 'MAGMOM', 'NBANDS', 'ISMEAR', 'SIGMA']),
    ('DFT+U', ['LDAU', 'LDAUTYPE', 'LDAUL', 'LDAUU', 'LMAXMIX', 'LDAUPRINT']),
    ('NEB', ['IMAGES', 'SPRING']),
    ('VTST', ['ICHAIN', 'IOPT', 'LCLIMB']),
    ('SETUP', ['AUTO_TIME', 'AUTO_NODES', 'AUTO_MEM', 'STAGE_NUMBER', 'STAGE_NAME', 'STAGE_FILE']) # must be last

]

VTST_DIR = os.environ['VTST_DIR']
GSM_DIR = os.environ['GSM_DIR']
TEMPLATE_DIR = os.environ['TEMPLATE_DIR'].split(':')