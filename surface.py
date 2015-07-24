import pymatgen as pmg
import pymatgen.core.structure as struc
import pymatgen.core.surface as surf
from pymatgen.io.vaspio.vasp_input import Poscar
import Vis
import os

os.chdir('/home/ryan/scratch/surface')

with pmg.matproj.rest.MPRester('gA8Qtx7mbPhwUiIJ') as m:
    for depth in range(2, 8):
        for width in range(2, 5):
            for freeze in range(1, depth):
                s = m.get_structure_by_material_id('mp-31801')
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

