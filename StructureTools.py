from Classes_Pymatgen import *
from pymatgen import Structure
import numpy as np
from pymatgen.io.ase import AseAtomsAdaptor
from ase import Atoms
import copy

def get_distance_from_plane(structure : Structure, i,  x,y,z):
    '''
    Get distance of atom i from the plane formed by atoms x, y, and z
    :param structure:
    :param i:
    :param x:
    :param y:
    :param z:
    :return:
    '''
    atoms = AseAtomsAdaptor.get_atoms(structure)
    atoms.wrap(atoms.get_scaled_positions()[i])
    positions = atoms.get_positions()

    x = positions[x]
    y = positions[y]
    z = positions[z]

    p = positions[i]

    # get Normal Vector
    v1 = y - x
    v2 = z - x

    # Get equation of plane ax+by+cz+d = 0
    normal = np.cross(v1, v2) / np.linalg.norm(np.cross(v1, v2))
    d = np.dot(normal, x)
    a = normal[0]
    b = normal[1]
    c = normal[2]

    # Get closest point on plane
    return abs((a * p[0] + b * p[1] + c * p[2] - d) / (a ** 2 + b ** 2 + c ** 2))  # distance between point and plane

def get_angle_from_plane(structure : Structure, i, i1, i2, x, y, z):
    '''
    Get distance of atom i from the plane formed by atoms x, y, and z
    :param structure:
    :param i:
    :param x:
    :param y:
    :param z:
    :return:
    '''
    atoms = AseAtomsAdaptor.get_atoms(structure)
    atoms.wrap(atoms.get_scaled_positions()[i])
    positions = atoms.get_positions()

    x = positions[x]
    y = positions[y]
    z = positions[z]

    v = positions[i1] - positions[i2]

    # get Normal Vector
    v1 = y - x
    v2 = z - x

    # Get equation of plane ax+by+cz+d = 0
    normal = np.cross(v1, v2) / np.linalg.norm(np.cross(v1, v2))
    a = normal[0]
    b = normal[1]
    c = normal[2]
    plane = np.array([a,b,c])

    return np.arcsin(abs(np.dot(v, plane)) / (np.linalg.norm(v)*np.linalg.norm(plane)))*180/np.pi


def check_distances_from_plane(structure, atom_i, angle_is, exclude_element=[Element('O')], min_distance=0.002, min_angle=58
                               ):
    metal_atoms = [i for i, a in enumerate(structure) if a.specie not in exclude_element]
    metal_atoms.remove(atom_i)
    best = None
    for i in copy.deepcopy(metal_atoms):
        metal_atoms.remove(i)
        for j in metal_atoms:
            for k in metal_atoms:
                d = get_distance_from_plane(structure, atom_i, i, j, k)
                print(d)
                if d < min_distance:
                    angle = get_angle_from_plane(structure, atom_i, angle_is[0], angle_is[1], i,j,k)
                    if angle > min_angle:
                        min_angle = angle
                        best = (i,j,k)
    if best:
        return best
    atoms = list(range(len(structure)))
    print('Could not find Metal Bounding Atoms, checking Oxygen')
    for i in copy.deepcopy(atoms):
        atoms.remove(i)
        for j in atoms:
            for k in atoms:
                d = get_distance_from_plane(structure, atom_i, i, j, k)
                if d < min_distance:
                    angle = get_angle_from_plane(structure, atom_i, angle_is[0], angle_is[1], i,j,k)
                    if angle > min_angle:
                        min_angle = angle
                        best = (i,j,k)
    if best:
        return best
    print('Could Not Find Bounding Atoms')
