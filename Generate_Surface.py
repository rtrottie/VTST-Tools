#!/usr/bin/env python
#TODO: Make more general, currently only cuts on 010
import pymatgen.core.surface as surf
from Helpers import *
from Classes_Pymatgen import *
import Vis
import argparse

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

def Generate_Surface(material, miller, width, length, depth, freeze=0, vacuum=10, incar=None, kpoints=None, vis=False, orth=False):
    """

    Args:
        material:
        miller:
        width:
        length:
        depth:
        freeze:
        vacuum:
        incar:
        kpoints:
        vis:

    Returns:

    :type material: str
    :type miller: list
    :type width: int
    :type depth: int
    :rtype: Structure
    """
    Poscar.get_string = get_string_more_sigfig
    Incar.get_string = pretty_incar_string
    surfs = []
    s = Poscar.from_file(material).structure
    sf = surf.SlabGenerator(s, miller, depth, 1, primitive=True)
    i=0
    for s in sf.get_slabs():
        if orth:
            s = s.get_orthogonal_c_slab()
        s = Add_Vac(s, 2, vacuum)
        s.make_supercell([width,length,1])
        s.sort(key=lambda x: x.specie.number*1000000000000 + x.c*100000000 + x.a*10000 + x.b)
        if vis:
            Vis.view(s, program=vis)
            use = raw_input('Use this structure (y/n) or break:  ')
            if use == 'n':
                continue
            elif use =='y':
                surfs.append(s)
                i+=1
            elif use == 'break':
                break
            else:
                i+=1
                print('Bad input, assuming yes')
        else:
            surfs.append(s)
            i+=1
    return surfs

def Add_Vac(structure, vector, vacuum):
    """

    Args:

        structure: Structure to add vacuum at cell border
        vector: Which lattice vector to add vacuum to
        vacuum: How much vacuum to add

    Returns:

    :type structure: Structure
    :type vector: int
    :type vacuum: np.float64
    :rtype: Structure
    """
    lattice = structure.lattice.matrix
    vector_len = np.linalg.norm(lattice[vector])
    lattice[vector] = lattice[vector] * (1 + vacuum / vector_len)
    s = Structure(lattice, structure.atomic_numbers, structure.cart_coords, coords_are_cartesian=True)
    s.translate_sites(range(0, len(s.atomic_numbers)), [0,0,0.5-(vector_len/(vector_len+vacuum)/2)])
    return s

def get_SD_along_vector(structure, vector, range):
    """

    Args:
        structure:
        vector:
        range:

    Returns:

    :type structure: Structure
    :type vector: int
    :type range: list
    :rtype: list
    """
    sd = []
    for site in structure.sites:
        if range[0] <= site.frac_coords[vector] and site.frac_coords[vector] <= range[1]:
            sd.append([False, False, False])
        else:
            sd.append([True, True, True])

    return sd


parser = argparse.ArgumentParser()
parser.add_argument('-m', '--miller', help='Miller indecies of desired surface',
                    type=int, nargs=3, required='True')
parser.add_argument('-b', '--bulk', help='Bulk structure of surface',
                    type=str, default='', nargs='?', required='True')
parser.add_argument('-w', '--width', help='width of supercell (in # of unit cells) (default is 1)',
                    type=int, default=1)
parser.add_argument('-l', '--length', help='length of supercell (defaults to width)',
                    type=int, default=0)
parser.add_argument('-d', '--depth', help='minimum depth of slab (in Angstroms) (default = 6) Note:  cell will be larger to ensure stoichiometry is preserved',
                    type=float, default=6)
parser.add_argument('-v', '--vacuum', help='vacuum above slab (in Angstroms) (default = 12)',
                    type=float, default=12)
parser.add_argument('-s', '--selective_dynamics', help='Freezes all atoms along the c vector with cordinates in between or equal to the two provided fractional coordinates',
                    type=float, nargs=2)
parser.add_argument('--vis', help='Visualize structures and determine which ones to save (only doable on a local computer with proper environment set up)',
                    action='store_true')
parser.add_argument('-o', '--no_orthogonal', help='does not attempt to orthogonalize cell.  Not recommended (less efficient, marginally harder to visualize)',
                    action='store_false')


args = parser.parse_args()

if __name__ == '__main__':
    if args.width == 0:
        args.width = -1
    surfs = Generate_Surface(args.bulk, args.miller, args.width, args.length, args.depth, vacuum=args.vacuum, vis=args.vis, orth=args.no_orthogonal)
    i = 0
    path_base = args.miller.join('_')
    for surf in surfs:
        path = os.path.join(path_base, str(i).zfill(2))
        if args.selective_dynamics:
            sd = get_SD_along_vector(surf, 2, args.selective_dynamics)
        else:
            sd = None
        p = Poscar(surf, selective_dynamics=sd)
        if not os.path.exists():
            os.makedirs(path)
        p.write_file(os.path.join(path, 'POSCAR'))