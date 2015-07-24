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

key = 'gA8Qtx7mbPhwUiIJ'