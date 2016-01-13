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

def Generate_Surface(material, miller, width, depth, freeze=0, vacuum=10, incar=None, kpoints=None, vis=False, orth=False):
    """

    Args:
        material:
        miller:
        width:
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
    with pmg.matproj.rest.MPRester(os.environ['MAT_PROJ_KEY']) as m:
        s = Poscar.from_file(material).structure
        sf = surf.SlabGenerator(s, miller, depth, 0, primitive=False)
        i=0
        for s in sf.get_slabs():
            if orth:
                s = s.get_orthogonal_c_slab()
            s = Add_Vac(s, 2, vacuum)
            s.make_supercell([width,width,1])
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
                '''
            if freeze > 0:
                sd = []
                for site in s.sites:
                    if s.lattice.c - (site.frac_coords[2] * site.lattice.c) < freeze:
                        sd.append([False, False, False])
                    else:
                        sd.append([True, True, True])
                poscar = Poscar(s, selective_dynamics=sd)
            else:
                poscar = Poscar(s)
            if incar and kpoints:
                update_incar(s, incar)
                potcar = Potcar(poscar.site_symbols)
                vasp = VaspInput(incar, kpoints, poscar, potcar)
                vasp.write_input(folder)
            else:
                os.makedirs(folder)
                poscar.write_file(os.path.join(folder, 'POSCAR'))
                '''
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

if os.path.basename(sys.argv[0]) == 'Generate_Surface.py':
    if len(sys.argv) < 6:
        raise Exception('Not Enough Arguments Provided\n need: depth_min, depth_max, width_min, width_max, freeze_step')
    Generate_Surfaces('POSCAR', int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]),
                      int(sys.argv[4]), float(sys.argv[5]), Incar.from_file('INCAR'), Kpoints.from_file('KPOINTS') )

