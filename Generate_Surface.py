#!/usr/bin/env python
#TODO: Make more general, currently only cuts on 010
import pymatgen.core.surface as surf
from pymatgen.core.surface import Slab, generate_all_slabs
from Helpers import *
from Classes_Pymatgen import *
import Vis
import argparse
from tempfile import NamedTemporaryFile

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

def Generate_Surface(structure, miller, width, length, depth, freeze=0, vacuum=10, incar=None, kpoints=None, vis=False, orth=False, cancel_dipole=False):
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
    :type miller: int
    :type width: int
    :type depth: int
    :rtype: Structure
    """
    Poscar.get_string = get_string_more_sigfig
    Incar.get_string = pretty_incar_string
    surfs = []
    # sf = surf.SlabGenerator(structure, miller, depth, 1,)
    i=0
    for s in generate_all_slabs(structure, miller, depth, 1, tol=0.2, center_slab=True, max_normal_search=miller*2):
        # if orth:
        #     s = s.get_orthogonal_c_slab()
        s = Add_Vac(s, 2, vacuum, cancel_dipole=cancel_dipole)
#         miller = s.miller_index
        s.make_supercell([width,length,1])
        site_symbols = Poscar(s).site_symbols
        s.sort(key=lambda x: site_symbols.index(x.specie.symbol)*1000000000000 + x.c*100000000 + x.a*10000 + x.b)
        if vis:
            Vis.view(s, program=vis)
            use = input('Use this structure (y/n) or break:  ')
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

def Add_Vac(structure, vector, vacuum, cancel_dipole=False):
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
    max_height = max([x[vector] for x in structure.frac_coords]) * structure.lattice.matrix[vector]
    min_height = min([x[vector] for x in structure.frac_coords]) * structure.lattice.matrix[vector]
    lattice = structure.lattice.matrix
    vector_len = np.linalg.norm(lattice[vector])
    avg_height = (max_height + min_height) / 2
    if cancel_dipole:
        separation = vacuum
        lattice[vector] = lattice[vector] * (1 + (vacuum+separation) / vector_len)
        vector_len = np.linalg.norm(lattice[vector])

        displacement = -lattice[vector] / 2 + 2* avg_height
        atomic_numbers = list(structure.atomic_numbers) + list(structure.atomic_numbers)
        flipped_coords = [ np.array(x) - 2 * structure.frac_coords[i][vector] * structure.lattice.matrix[2] + displacement for i, x in enumerate(structure.cart_coords)]
        # coords = list(structure.cart_coords) + [(x + displacement) for x in structure.cart_coords]
        coords = list(structure.cart_coords) + list(flipped_coords)

        s = Structure(lattice,
                      atomic_numbers,
                      coords, coords_are_cartesian=True)
        translation = 0.5 - (np.linalg.norm(avg_height) / vector_len)
        s.translate_sites(range(0, len(s.atomic_numbers)), [0,0,translation])

        # displacement = lattice[vector] * separation / np.linalg.norm(lattice[vector]) + 2* max_height
        # atomic_numbers = list(structure.atomic_numbers) + list(structure.atomic_numbers)
        # flipped_coords = [ np.array(x) - 2 * structure.frac_coords[i][vector] * structure.lattice.matrix[2] + displacement for i, x in enumerate(structure.cart_coords)]
        # # coords = list(structure.cart_coords) + [(x + displacement) for x in structure.cart_coords]
        # coords = list(structure.cart_coords) + list(flipped_coords)
        # ss.append(Structure(lattice,
        #               atomic_numbers,
        #               coords, coords_are_cartesian=True))
    else:
        lattice[vector] = lattice[vector] * (1 + vacuum / vector_len)
        s = Structure(lattice, structure.atomic_numbers, structure.cart_coords, coords_are_cartesian=True)
        translation = 0.5 - vector_len / np.linalg.norm(lattice[vector])
        s.translate_sites(range(0, len(s.atomic_numbers)), [0,0,translation], frac_coords=True)
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
        if min(range) <= site.frac_coords[vector] and site.frac_coords[vector] <= max(range):
            sd.append([False, False, False])
        else:
            sd.append([True, True, True])

    return sd

def get_bottom(structure, length=4, region='bot'):
    c_dist = length/structure.lattice.c
    if region == 'bot' or region == 'bottom':
        bot = min(structure.frac_coords[:,2])
        top = bot + c_dist
    elif region == 'top' :
        top = max(structure.frac_coords[:,2])
        bot = top - c_dist
    elif region == 'bot_cd':
        top = min(coord for coord in structure.frac_coords[:,2] if coord > 0.25)
        top += c_dist
        bot = max(coord for coord in structure.frac_coords[:,2] if coord < 0.25)
        bot -= c_dist
    elif region == 'top_cd':
        top = min(coord for coord in structure.frac_coords[:,2] if coord > 0.75)
        top += c_dist
        bot = max(coord for coord in structure.frac_coords[:,2] if coord < 0.75)
        bot -= c_dist
    else:
        raise Exception('Region Does not exist, should be bot or top')

    return [bot, top]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--miller', help='Miller indecies of desired surface',
                        type=int, default=1)
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
    parser.add_argument('--cd', '--cancel dipole', help='make two cells to cancel out dipole moment',
                        action='store_true')
    parser.add_argument('--freeze', help='Freeze top and bottom set distance',
                        type=float, default=0)
    args = parser.parse_args()
    if args.length == 0:
        args.length = args.width
    surfs = Generate_Surface(Structure.from_file(args.bulk), args.miller, args.width, args.length, args.depth, vacuum=args.vacuum, vis=args.vis, orth=args.no_orthogonal, cancel_dipole=args.cd)
    Structure.from_file(args.bulk).to('poscar', 'POSCAR')
    i = 0
    # path_base = '_'.join(list(map(str, args.miller)))
    path_base = 'surfaces'
    for surf in surfs:
        path = os.path.join(path_base, str(i).zfill(2))
        if args.selective_dynamics:
            sd = get_SD_along_vector(surf, 2, args.selective_dynamics)
        else:
            sd = None
        p = Poscar(surf, selective_dynamics=sd)
        if not os.path.exists(path):
            os.makedirs(path)
        p.write_file(os.path.join(path, 'POSCAR'))
        if args.freeze:
            for region in ['bot', 'top']:
                dir = os.path.join(path, 'frozen_{}'.format(region))
                sd = get_SD_along_vector(surf, 2, get_bottom(surf, args.freeze, region))
                os.makedirs(dir, exist_ok=True)
                Poscar(surf, selective_dynamics=sd).write_file(os.path.join(dir, 'POSCAR'))

        i += 1
