from align_bond_along_a import align_a_to_vector, set_vector_as_boundary
from Classes_Pymatgen import *
from pymatgen.analysis.local_env import solid_angle
from get_migration import get_center_i
from bisect import bisect_left
from scipy.spatial import Voronoi

structure = Poscar.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR').structure
n = get_center_i(structure, Element('O'))
# ss = Generate_Surface(structure, [1,1,0], 1, 1, 8, vacuum=12, cancel_dipole=True, vis='vesta', orth=True)
cutoff = 10
targets = structure.composition.elements
center = structure[n]
neighbors = structure.get_sites_in_sphere(
            center.coords, cutoff)
neighbors = [i[0] for i in sorted(neighbors, key=lambda s: s[1])]
qvoronoi_input = [s.coords for s in neighbors]
voro = Voronoi(qvoronoi_input)
all_vertices = voro.vertices
results = {}
for nn, vind in voro.ridge_dict.items():
    if 0 in nn:
        if -1 in vind:
            if self.allow_pathological:
                continue
            else:
                raise RuntimeError("This structure is pathological,"
                                   " infinite vertex in the voronoi "
                                   "construction")

        facets = [all_vertices[i] for i in vind]
        results[neighbors[sorted(nn)[1]]] = solid_angle(
            center.coords, facets)
maxangle = max(results.values())

resultweighted = {}
for nn, angle in results.items():
    # is nn site is ordered use "nn.specie" to get species, else use "nn.species_and_occu" to get species
    if nn.is_ordered:
        if nn.specie in targets:
            resultweighted[nn] = angle / maxangle
    else:  # is nn site is disordered
        for disordered_sp in nn.species_and_occu.keys():
            if disordered_sp in targets:
                resultweighted[nn] = angle / maxangle















pass
