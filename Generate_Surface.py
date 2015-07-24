import pymatgen as pmg
import pymatgen.core.structure as struc
import pymatgen.core.surface as surf
import os
import cfg
from pymatgen.io.vaspio.vasp_input import Poscar
from Classes_Pymatgen import *

os.chdir('/home/ryan/scratch/surface')

def Generate_Surfaces(material, depth_min, depth_max, depth_step, width_min, width_max):
    Poscar.get_string = get_string_more_sigfig
    Incar.get_string = pretty_incar_string
    with pmg.matproj.rest.MPRester(cfg.key) as m:
        for depth in range(depth_min, depth_max, depth_step):
            for width in range(width_min, width_max):
                for freeze in range(1, depth+1):
                    s = m.get_structure_by_material_id(material)
                    frozen_depth = s.lattice.b
                    s.make_supercell([width, depth, width])
                    sf = surf.SlabGenerator(s, [0,1,0], 2, 10, primitive=False)

                    folder = 'd' + str(depth) + '-f' + str(freeze) + '-w' + str(width)
                    p = Poscar(sf.get_slab())
                    sd = []
                    for site in p.structure.sites:
                        if site.b * site.lattice.b < frozen_depth:
                            sd.append([False, False, False])
                        else:
                            sd.append([True, True, True])
                    p.selective_dynamics = sd
                    os.makedirs(folder,exist_ok=True)
                    p.write_file(os.path.join(folder, "POSCAR"))

