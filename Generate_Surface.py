#!/usr/bin/env python
import pymatgen as pmg
import pymatgen.core.structure as struc
import pymatgen.core.surface as surf
import os
import sys
import cfg
from pymatgen.io.vaspio.vasp_input import Poscar
from Helpers import *
from Classes_Pymatgen import *
import Vis

def Generate_Surfaces(material, depth_min, depth_max, width_min, width_max, freeze_step, incar, kpoints):
    Poscar.get_string = get_string_more_sigfig
    Incar.get_string = pretty_incar_string
    with pmg.matproj.rest.MPRester(cfg.key) as m:
        for depth in range(depth_min, depth_max+1):
            for width in range(width_min, width_max+1):
                for freeze in xfrange(0, depth+.1, freeze_step):
                    s = Poscar.from_file('POSCAR').structure
                    frozen_depth = s.lattice.b * freeze
                    s.make_supercell([width, depth, width])
                    surface_depth = s.lattice.b
                    sf = surf.SlabGenerator(s, [0,1,0], 2, 10, primitive=False)
                    folder = 'd' + str(depth) + '-w' + str(width) + '-f' + str(freeze)
                    poscar = Poscar(sf.get_slab())
                    sd = []
                    for site in poscar.structure.sites:
                        if site.c * site.lattice.c < frozen_depth:
                            sd.append([False, False, False])
                        else:
                            sd.append([True, True, True])
                    poscar.selective_dynamics = sd
                    update_incar(s, incar)
                    potcar = Potcar(poscar.site_symbols)
                    vasp = VaspInput(incar, kpoints, poscar, potcar)
                    vasp.write_input(folder)


if os.path.basename(sys.argv[0]) == 'Generate_Surface.py':
    if len(sys.argv) < 6:
        raise Exception('Not Enough Arguments Provided\n need: depth_min, depth_max, width_min, width_max, freeze_step')
    Generate_Surfaces('POSCAR', int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]),
                      int(sys.argv[4]), float(sys.argv[5]), Incar.from_file('INCAR'), Kpoints.from_file('KPOINTS') )

