#!/usr/bin/env python
#TODO: Make more general, currently only cuts on 010
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
import Vis

def Generate_Surfaces(material, depth_min, depth_max, width_min, width_max, freeze_step, incar, kpoints, vis=False):
    Poscar.get_string = get_string_more_sigfig
    Incar.get_string = pretty_incar_string
    with pmg.matproj.rest.MPRester(cfg.MAT_PROJ_KEY) as m:
        for depth in range(depth_min, depth_max+1):
            for width in range(width_min, width_max+1):
                freeze = 0.5
                s = Poscar.from_file(material).structure
                frozen_depth = s.lattice.b * freeze
                s.make_supercell([width, width, depth])
                surface_depth = s.lattice.b
                sf = surf.SlabGenerator(s, [1,1,1], 4, 15, primitive=False)
                folder = unicode('d' + str(depth) + '-w' + str(width) + '-f' + str(freeze))
                i=0
                for poscar in sf.get_slabs():
                    folder = unicode('d' + str(depth) + '-w' + str(width) + '-f' + str(freeze) + '-s' + str(i))
                    i+=1
                    poscar = Poscar(poscar)
                    sd = []
                    for site in poscar.structure.sites:
                        if site.c * site.lattice.c < frozen_depth:
                            sd.append([False, False, False])
                        else:
                            sd.append([True, True, True])
                    if vis:
                        Vis.open_in_VESTA(poscar.structure)
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

