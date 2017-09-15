# TODO : Make work with structures including H

from pymatgen import Structure, Element, PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.local_env import VoronoiNN
import numpy as np
from Vis import view

def get_atom_i(s, target_atom):
    i = 0
    for a in s:
        if a.specie == target_atom:
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


def get_vacancy_diffusion_pathways_from_cell(structure : Structure, atom_i : int):
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
    structure = structure.copy()
    target_atom = structure[atom_i].specie
    vnn = VoronoiNN(targets=[target_atom])
    edges = vnn.get_nn_info(structure, atom_i)
    base_coords = structure[atom_i].coords

    # Add H in middle of the discovered pathways.  Use symmetry analysis to elminate equivlent H and therfore
    # equivalent pathways
    site_dir = {}
    for edge in edges:
        coords = (base_coords + edge['site'].coords)/2
        structure.append('H', coords, True)
        site_dir[tuple(np.round(coords))] = structure.index(edge['site']) # Use Tuple for indexing dict, need to round

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
    sga = SpacegroupAnalyzer(structure, 0.5, angle_tolerance=20)
    ss = sga.get_symmetrized_structure()

    # Remove symmetrically equivalent pathways:
    final_structure = structure.copy()
    indices = []
    for i in range(len(orig_structure), len(orig_structure)+len(edges)):
        sites = ss.find_equivalent_sites(ss[i])
        new_indices = [ss.index(site) for site in sites if ss.index(site) < len(orig_structure) + len(edges)]
        new_indices.remove(i)
        if i not in indices:
            indices = indices + new_indices
            indices.sort()
    indices = indices + list(range(len(orig_structure)+len(edges), len(final_structure)))
    final_structure.remove_sites(indices)
    view(final_structure, 'VESTA')

    diffusion_elements = [ site_dir[tuple(np.round(h.coords))] for h in final_structure[len(orig_structure):] ]
    print(diffusion_elements)

    return diffusion_elements


structure = Structure.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR')
sga = SpacegroupAnalyzer(structure, 2, 20)
s = sga.get_conventional_standard_structure() * (1,1,1)
# s = structure *(1,1,1)
view(s, 'VESTA')
# get_vacancy_diffusion_pathways_from_cell(s, 73)
get_vacancy_diffusion_pathways_from_cell(s, get_center_i(s, Element('O')))

pass