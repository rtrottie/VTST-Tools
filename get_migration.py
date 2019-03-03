# TODO : Make work with structures including H

from pymatgen import Structure, Element, PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.local_env import VoronoiNN
import numpy as np
from Vis import view, open_in_VESTA
from pymatgen.analysis.defects.generators import InterstitialGenerator, VoronoiInterstitialGenerator
from pymatgen.analysis.defects.core import create_saturated_interstitial_structure
from Classes_Pymatgen import Poscar
import time
from pymatgen.core.structure import StructureError

def get_atom_i(s, target_atoms):
    if type(target_atoms) != list and type(target_atoms )!= set:
        target_atoms = [target_atoms]
    i = 0
    for a in s:
        if a.specie in target_atoms:
            yield i
        i = i+1

def get_center_i(structure : Structure, element : Element):
    center_coords = structure.lattice.get_cartesian_coords([0.5, 0.5, 0.5])
    sites = structure.get_sites_in_sphere(center_coords, 4)
    sites.sort(key=lambda x : x[1])
    for (site, _) in sites:
        if site.specie == element:
            return structure.index(site)
    raise Exception('Could not find specified {}'.format(element))

def get_vacancy_diffusion_pathways_from_cell(structure : Structure, atom_i : int, vis=False, get_midpoints=False):
    '''

    Find Vacancy Strucutres for diffusion into and out of the specified atom_i site.

    :param structure: Structure
        Structure to calculate diffusion pathways
    :param atom_i: int
        Atom to get diffion path from
    :return: [ Structure ]
    '''

    # To Find Pathway, look for voronoi edges
    orig_structure = structure.copy()
    structure = structure.copy() # type: Structure
    target_atom = structure[atom_i].specie
    vnn = VoronoiNN(targets=[target_atom])
    edges = vnn.get_nn_info(structure, atom_i)
    base_coords = structure[atom_i].coords

    # Add H in middle of the discovered pathways.  Use symmetry analysis to elminate equivlent H and therfore
    # equivalent pathways
    site_dir = {}
    for edge in edges:
        coords = np.round((base_coords + edge['site'].coords)/2,3)
        structure.append('H', coords, True)
       # site_dir[tuple(np.round(coords))] = structure.index(edge['site']) # Use Tuple for indexing dict, need to round
        site_dir[tuple(np.round(coords))] =  [list(x) for x in np.round(structure.frac_coords % 1,2) ].index(list(np.round(edge['site'].frac_coords % 1, 2))) # Use Tuple for indexing dict, need to round
    # Add H for all other diffusion atoms, so symmetry is preserved
    for i in get_atom_i(orig_structure, target_atom):
        sym_edges = vnn.get_nn_info(orig_structure, i)
        base_coords = structure[i].coords
        for edge in sym_edges:
            coords = (base_coords + edge['site'].coords) / 2
            try:
                structure.append('H', coords, True, True)
            except:
                pass

    # Remove symmetrically equivalent pathways:
    sga = SpacegroupAnalyzer(structure, 0.5, angle_tolerance=20)
    ss = sga.get_symmetrized_structure()

    final_structure = structure.copy()
    indices = []
    for i in range(len(orig_structure), len(orig_structure)+len(edges)): # get all 'original' edge sites
        sites = ss.find_equivalent_sites(ss[i])
        new_indices = [ss.index(site) for site in sites if ss.index(site) < len(orig_structure) + len(edges)] # Check if symmetrically equivalent to other original edge sites
        new_indices.remove(i)
        if i not in indices: # Don't duplicate effort
            indices = indices + new_indices
            indices.sort()
    indices = indices + list(range(len(orig_structure)+len(edges), len(final_structure)))
    final_structure.remove_sites(indices)
    diffusion_elements = [ site_dir[tuple(np.round(h.coords))] for h in final_structure[len(orig_structure):] ]
    if vis:
        view(final_structure, 'VESTA')
        print(diffusion_elements)

    if get_midpoints:
        centers = [h.frac_coords for h in final_structure[len(orig_structure):]]
        return (diffusion_elements, centers)


    return diffusion_elements

def get_interstitial_diffusion_pathways_from_cell(structure : Structure, interstitial_atom : str, vis=False,
                                                  get_midpoints=False, dummy='He', min_dist=0.5):
    '''

    Find Vacancy Strucutres for diffusion into and out of the specified atom_i site.

    :param structure: Structure
        Structure to calculate diffusion pathways
    :param atom_i: int
        Atom to get diffion path from
    :return: [ Structure ]
    '''

    # To Find Pathway, look for voronoi edges
    orig_structure = structure.copy()
    structure = structure.copy() # type: Structure
    combined_structure = structure.copy()
    combined_structure.DISTANCE_TOLERANCE = 0.01
    vnn = VoronoiNN(targets=[interstitial_atom])

    if vis:
        Poscar(structure).write_file(vis)
        open_in_VESTA(vis)
    inter_gen = list(VoronoiInterstitialGenerator(orig_structure, interstitial_atom))
    if vis:
        print(len(inter_gen))
    for interstitial in inter_gen:
        sat_structure = create_saturated_interstitial_structure(interstitial) # type: Structure
        sat_structure.remove_site_property('velocities')
        if vis:
            Poscar(sat_structure).write_file(vis)
            open_in_VESTA(vis)
            time.sleep(0.5)
        for site in sat_structure: # type: PeriodicSite
            if site.specie == interstitial_atom:
                try:
                    combined_structure.append(site.specie, site.coords, coords_are_cartesian=True, validate_proximity=True)
                except StructureError:
                    pass

    # combined_structure.merge_sites(mode='delete')
    combined_structure.remove_site_property('velocities')
    if vis:
        Poscar(combined_structure).write_file(vis)
        open_in_VESTA(vis)




    # edges = vnn.get_nn_info(structure, atom_i)
    # base_coords = structure[atom_i].coords
    pathway_structure = combined_structure.copy()
    # Add H for all other diffusion atoms, so symmetry is preserved
    for i in get_atom_i(combined_structure, interstitial_atom):
        sym_edges = vnn.get_nn_info(combined_structure, i)
        base = pathway_structure[i] # type: PeriodicSite
        for edge in sym_edges:
            dest = edge['site']
            if base.distance(dest) > min_dist:
                coords = (base.coords + dest.coords) / 2
                try:
                    neighbors = [i, edge['site_index']]
                    neighbors.sort()
                    pathway_structure.append(dummy, coords, True, False, properties={'neighbors': neighbors})
                except StructureError:
                    pass
    if vis:
        Poscar(pathway_structure).write_file(vis)
        open_in_VESTA(vis)



    # Remove symmetrically equivalent pathways:
    sga = SpacegroupAnalyzer(pathway_structure, 0.5, angle_tolerance=20)
    ss = sga.get_symmetrized_structure()
    Poscar(ss).write_file('testing.vasp')
    return
    '''
    final_structure = structure.copy()
    indices = []
    for i in range(len(orig_structure), len(orig_structure)+len(edges)): # get all 'original' edge sites
        sites = ss.find_equivalent_sites(ss[i])
        new_indices = [ss.index(site) for site in sites if ss.index(site) < len(orig_structure) + len(edges)] # Check if symmetrically equivalent to other original edge sites
        new_indices.remove(i)
        if i not in indices: # Don't duplicate effort
            indices = indices + new_indices
            indices.sort()
    indices = indices + list(range(len(orig_structure)+len(edges), len(final_structure)))
    final_structure.remove_sites(indices)
    diffusion_elements = [ site_dir[tuple(np.round(h.coords))] for h in final_structure[len(orig_structure):] ]
    if vis:
        view(final_structure, 'VESTA')
        print(diffusion_elements)

    if get_midpoints:
        centers = [h.frac_coords for h in final_structure[len(orig_structure):]]
        return (diffusion_elements, centers)

    '''
    return diffusion_elements

def get_midpoint(structure : Structure, atom_1, atom_2):
    a = structure.lattice.a
    b = structure.lattice.b
    c = structure.lattice.c
    d = 999
    for x in [0,1,-1]:
        for y in [0,1,-1]:
            for z in [0,1,-1]:
                jimage = np.array([x,y,z])
                temp_d = structure.get_distance(atom_1, atom_2, jimage=jimage)
                if temp_d < d:
                    d = temp_d
                    coord = structure[atom_1].frac_coords + structure[atom_2].frac_coords - jimage
                    coord /= 2
                    if d < a*0.5 and d < b*0.5 and d < c*0.5:
                        return coord
    return coord

def is_equivalent(structure : Structure, atoms_1 : tuple, atoms_2 : tuple , eps=0.05):
    '''

    Find Vacancy Strucutres for diffusion into and out of the specified atom_i site.

    :param structure: Structure
        Structure to calculate diffusion pathways
    :param atom_i: int
        Atom to get diffion path from
    :return: [ Structure ]
    '''

    # To Find Pathway, look for voronoi edges
    structure = structure.copy() # type: Structure

    coords = get_midpoint(structure, atoms_1[0], atoms_1[1])
    structure.append('H', coords)
    coords = get_midpoint(structure, atoms_2[0], atoms_2[1])
    structure.append('H', coords)

    dist_1 = structure.get_neighbors(structure[-2], 3)
    dist_2 = structure.get_neighbors(structure[-1], 3)
    dist_1.sort(key=lambda x: x[1])
    dist_2.sort(key=lambda x: x[1])
    for (site_a, site_b) in zip(dist_1, dist_2):
        if abs(site_a[1] - site_b[1]) > eps:
            return False
        elif site_a[0].specie != site_b[0].specie:
            return False
    return True
