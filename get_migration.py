# TODO : Make work with structures including H

from pymatgen import Structure, Element, PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.local_env import VoronoiNN
import numpy as np
from Vis import view, open_in_VESTA
from pymatgen.analysis.defects.generators import VoronoiInterstitialGenerator
from pymatgen.analysis.defects.core import create_saturated_interstitial_structure
from Classes_Pymatgen import Poscar
import time
from pymatgen.core.structure import StructureError
from pymatgen.symmetry.structure import SymmetrizedStructure
import itertools


def get_atom_i(s, target_atoms):
    if type(target_atoms) != list and type(target_atoms) != set:
        target_atoms = [target_atoms]
    i = 0
    for a in s:
        if a.specie in target_atoms:
            yield i
        i = i+1


def get_center_i(structure : Structure, element : Element, skew_positive=True, delta=0.05):
    center_coords = structure.lattice.get_cartesian_coords([0.5, 0.5, 0.5])
    sites = structure.get_sites_in_sphere(center_coords, 4, include_index=True)
    sites.sort(key=lambda x : x[1])
    best_i = None
    best_dist = 999999
    best_location = 3
    for (site, dist, i) in sites: #type: PeriodicSite
        if site.specie == element:
            if dist < best_dist+delta:
                if sum(1 - (site.frac_coords % 1)) < best_location:
                    best_i = i
                    best_dist = best_dist
                    best_location = sum(1 - site.frac_coords)
    if best_i:
        return best_i
    raise Exception('Could not find specified {}'.format(element))


def get_vacancy_diffusion_pathways_from_cell(structure : Structure, atom_i : int, vis=False, get_midpoints=False):
    """

    Find Vacancy Strucutres for diffusion into and out of the specified atom_i site.

    :param structure: Structure
        Structure to calculate diffusion pathways
    :param atom_i: int
        Atom to get diffion path from
    :return: [ Structure ]
    """

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
                                                  get_midpoints=False, dummy='He', min_dist=0.5, weight_cutoff=0.0001,
                                                  is_interstitial_structure=False):
    """

    Find Vacancy Strucutres for diffusion into and out of the specified atom_i site.

    :param structure: Structure
        Structure to calculate diffusion pathways
    :param atom_i: int
        Atom to get diffion path from
    :return: [ Structure ]
    """

    vnn = VoronoiNN(targets=[interstitial_atom])
    # To Find Pathway, look for voronoi edges
    if not is_interstitial_structure:
        orig_structure = structure.copy()
        structure = structure.copy() # type: Structure
        interstitial_structure = structure.copy()
        interstitial_structure.DISTANCE_TOLERANCE = 0.01

        if vis:
            Poscar(structure).write_file(vis)
            open_in_VESTA(vis)
        inter_gen = list(VoronoiInterstitialGenerator(orig_structure, interstitial_atom))
        if vis:
            print(len(inter_gen))
        for interstitial in inter_gen:
            sat_structure = None
            for dist_tol in [0.2, 0.15, 0.1, 0.05, 0.01, 0.001]:
                try:
                    sat_structure = create_saturated_interstitial_structure(interstitial, dist_tol=dist_tol) # type: Structure
                    break
                except ValueError:
                    continue
                except TypeError:
                    continue
            if not sat_structure:
                continue
            sat_structure.remove_site_property('velocities')
            if vis:
                Poscar(sat_structure).write_file(vis)
                open_in_VESTA(vis)
                time.sleep(0.5)
            for site in sat_structure: # type: PeriodicSite
                if site.specie == interstitial_atom:
                    try:
                        interstitial_structure.append(site.specie, site.coords, coords_are_cartesian=True, validate_proximity=True)
                    except StructureError:
                        pass

        # combined_structure.merge_sites(mode='delete')
        interstitial_structure.remove_site_property('velocities')
        if vis:
            Poscar(interstitial_structure).write_file(vis)
            open_in_VESTA(vis)
    else:
        interstitial_structure = structure.copy()

    # edges = vnn.get_nn_info(structure, atom_i)
    # base_coords = structure[atom_i].coords
    pathway_structure = interstitial_structure.copy() # type: Structure
    pathway_structure.DISTANCE_TOLERANCE = 0.01
    # Add H for all other diffusion atoms, so symmetry is preserved
    for i in get_atom_i(interstitial_structure, interstitial_atom):
        sym_edges = vnn.get_nn_info(interstitial_structure, i)
        base = pathway_structure[i] # type: PeriodicSite
        for edge in sym_edges:
            dest = edge['site']
            if base.distance(dest) > min_dist and edge['weight'] > weight_cutoff:
                coords = (base.coords + dest.coords) / 2
                try:
                    neighbors = [i, edge['site_index']]
                    # neighbors.sort()
                    pathway_structure.append(dummy, coords, True, validate_proximity=True, properties={'neighbors': neighbors, 'image' : edge['image']})
                except StructureError:
                    pass
                except ValueError:
                    pass
    if vis:
        Poscar(pathway_structure).write_file(vis)
        open_in_VESTA(vis)



    # Remove symmetrically equivalent pathways:
    # sga = SpacegroupAnalyzer(pathway_structure, 0.1, angle_tolerance=10)
    # ss = sga.get_symmetrized_structure()
    return interstitial_structure, pathway_structure

def get_unique_diffusion_pathways(structure: SymmetrizedStructure, dummy_atom: Element, site_i: int = -1,
                                  only_positive_direction=False, positive_weight=10, abreviated_search=1e6):

    if type(structure) != SymmetrizedStructure:
        sga = SpacegroupAnalyzer(structure, symprec=0.1)
        structure = sga.get_symmetrized_structure()
    equivalent_dummies = [ x for x in structure.equivalent_indices if structure[x[0]].specie == dummy_atom]
    combinations_to_check = np.prod([ float(len(x)) for x in equivalent_dummies])
    if combinations_to_check > abreviated_search:
        new_eq_dummies = [ [] for _ in equivalent_dummies ]
        radius = 0.5
        pt = structure.lattice.get_cartesian_coords([0.75,0.75,0.75])
        while not all( new_eq_dummies ):
            sites_in_sphere = structure.get_sites_in_sphere(pt, radius, include_index=True, include_image=True)
            sites = [ i for _,_,i,image in sites_in_sphere if all(image == (0,0,0)) ]
            new_eq_dummies = [ [y for y in x if y in sites] for x in equivalent_dummies ]
            radius = radius + 0.1
        equivalent_dummies = new_eq_dummies
        print(np.prod([ float(len(x)) for x in equivalent_dummies]))
    best_sites = equivalent_dummies*2 + [[]] + [[]]
    best_pathway = None
    most_overlap = 0
    best_weight = 9e9
    path_count = 0
    for dummy_is in itertools.product(*equivalent_dummies):
        break_early = False
        path_count = path_count + 1
        sites = {(site_i, (0,0,0)): 0}
        pathway = []
        for i in dummy_is:
            neighbors = structure[i].properties['neighbors'].copy()
            image = structure[i].properties['image']
            if only_positive_direction and (-1 in image or -2 in image):
                break_early = True
                break
            neighbors[0] = (neighbors[0], (0,0,0))
            neighbors[1] = (neighbors[1], image)
            pathway.append(neighbors)
            for neighbor_i in neighbors:
                if neighbor_i in sites:
                    sites[neighbor_i] = sites[neighbor_i] + 1
                else:
                    sites[neighbor_i] = 1
        if only_positive_direction:
            if break_early:
                break_early = False
                continue
        cell_directions = [None,None,None]
        weight = 0
        for _, direction in sites.keys(): # make sure directions are consistent
            for i, d in enumerate(direction):
                if d: # if it is in a cell outside unit
                    if d > 0:
                        weight = weight + 1
                    elif d < 0:
                        weight = weight + positive_weight
                    if not cell_directions[i]: # haven't looked outside unit cell in this direction yet
                        cell_directions[i] = d
                    elif cell_directions[i] != d: # if the directions dont match
                        break_early = True
                        break
                else:
                    weight = weight - positive_weight
            if break_early:
                break
        if break_early:
            continue
        if len(sites) < len(best_sites) or (len(sites) == len(best_sites) and most_overlap < sites[(site_i, (0,0,0))]):
            if weight <= best_weight:
                best_sites = sites
                best_pathway = pathway
                most_overlap = sites[(site_i, (0,0,0))]
                best_weight = weight

    return best_pathway

def get_supercell_site(unit: Structure, supercell: Structure, site_i: int, image: tuple):
    coords = unit[site_i].frac_coords # get coords from unit_cell
    scale = np.array(unit.lattice.abc) / supercell.lattice.abc
    coords = coords * scale # Scale coords from supercell
    coords = coords + (scale * image) # scale coords to image
    sites = supercell.get_sites_in_sphere(supercell.lattice.get_cartesian_coords(coords), 0.001, include_index=True)
    if len(sites) != 1:
        raise Exception('Wrong number of sites at supercell destination {}'.format(sites))
    new_site = sites[0][2]
    return new_site

def get_supercell_for_diffusion(decorated_unit: Structure, unit_pathways, min_size=7.5):
    supercell_pathways = []
    supercell = decorated_unit * np.ceil(min_size / np.array(decorated_unit.lattice.abc))
    origin = np.array([0,0,0])
    for unit_pathway in unit_pathways:
        for (_, image) in unit_pathway:
            for i in range(len(origin)):
                origin[i] = min(origin[i], image[i])

    for unit_pathway in unit_pathways:
        new_pathway = []
        for (i, image) in unit_pathway:
            new_pathway.append(get_supercell_site(decorated_unit, supercell, i, image - origin))
        supercell_pathways.append(new_pathway)
    return supercell, supercell_pathways

def get_supercell_and_path_interstitial_diffusion(structure, interstitial=Element('H'), dummy=Element('He'),
                                                  min_size=7.5, vis=False, is_interstitial_structure=False):
    interstitial_structure, pathway_structure = get_interstitial_diffusion_pathways_from_cell(structure, interstitial,
                                                                                              dummy=dummy, vis=vis, is_interstitial_structure=is_interstitial_structure)
    # paths = get_unique_diffusion_pathways(pathway_structure, dummy, get_center_i(interstitial_structure, interstitial), only_positive_direction=True)
    paths = get_unique_diffusion_pathways(pathway_structure, dummy, only_positive_direction=False)
    supercell, paths = get_supercell_for_diffusion(interstitial_structure, paths, min_size=min_size)
    return supercell, paths


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

def remove_unstable_interstitials(structure: Structure, relaxed_interstitials: list, dist=0.2, site_indices=None):
    """

    :param structure: Structure decorated with all interstitials
    :param relaxed_interstitials: list of structures with interstitial as last index
    :param dist: tolerance for determining if site belongs to another site
    :return:
    """
    to_keep = list(range(len(relaxed_interstitials[0])-1))
    sga = SpacegroupAnalyzer(structure, symprec=0.1)
    structure = sga.get_symmetrized_structure()
    for ri in relaxed_interstitials:  #type:  Structure
        sites=structure.get_sites_in_sphere(ri.cart_coords[-1], dist, include_index=True)
        if len(sites) != 1: # make sure only one site is found
            okay = False
            if len(sites) > 1:
                if all([ x[0] in structure.find_equivalent_sites(sites[0][0]) for x in sites[1:]]):
                    okay = True
            if not okay:
                if site_indices:
                    raise Exception('Found {} sites for {}'.format(len(sites), site_indices[relaxed_interstitials.index(ri)]))
                raise Exception('Found {} sites'.format(len(sites)))
        index = sites[0][2]
        if index in to_keep: # Already keeping this index
            continue
        for indices in structure.equivalent_indices:  #look at all sets of equivalent indices
            if index in indices:
                to_keep = to_keep + indices  #keep equivalent indices
                break
    to_remove = [i for i in range(len(structure)) if i not in to_keep]
    structure.remove_sites(to_remove)
    return structure

def is_equivalent(structure : Structure, atoms_1 : tuple, atoms_2 : tuple , eps=0.05):
    """

    Find Vacancy Strucutres for diffusion into and out of the specified atom_i site.

    :param structure: Structure
        Structure to calculate diffusion pathways
    :param atom_i: int
        Atom to get diffion path from
    :return: [ Structure ]
    """

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
