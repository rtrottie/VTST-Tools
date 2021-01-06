#!/usr/bin/env python

from Classes_Pymatgen import *
import argparse
import numpy as np
from pymatgen.core.operations import SymmOp
from pymatgen.transformations.standard_transformations import RotationTransformation
import matplotlib.pyplot as plt


def align_a_to_vector(structure: Structure, vector: list):
    """
    aligns the a vector of the provided structure to the provided vector
    :param structure: structure to be aligned
    :param vector: vector to align to
    :return: Strucutre aligned to given vector
    """
    s = structure.copy()  # type: Structure
    a = s.lattice.matrix[0]
    b = s.lattice.matrix[1]

    normal = np.cross(a, b)  # Eq'n from http://www.euclideanspace.com/maths/geometry/elements/plane/lineOnPlane/
    normal = normal / np.linalg.norm(normal)
    perp_projection = np.dot(normal, vector) * normal
    plane_projection = vector - perp_projection

    angle = np.arctan2(np.dot(np.cross(plane_projection, a), normal), np.dot(plane_projection, a))
    rot = SymmOp.from_origin_axis_angle([0, 0, 0], normal, angle, angle_in_radians=True)
    s.apply_operation(rot)
    return Structure(structure.lattice, s.species, s.cart_coords, coords_are_cartesian=True, site_properties=s.site_properties)


def intersection(v, p, bv):
    """
    Finds the intersection
    :param v: vector starting at origin
    :param p: point for starting bounding vector
    :param bv: bounding vector
    :return: the intersection point
    """
    a = bv[0]
    b = bv[1]
    c = bv[2]
    A = v[0]
    B = v[1]
    C = v[2]
    x0 = p[0]
    y0 = p[1]
    z0 = p[2]
    y = (x0*b*B - y0*a*B) / (b*A - a*B)
    x = y*A/B
    z = y*C/B
    return x, y, z


def set_vector_as_boundary(structure: Structure, vector: list):
    """

    :param structure: structure to be relaxed
    :param vector: vector to restrain relaxation
    :return: structure unable to relax along given vector
    """
    s = structure.copy()  # type: Structure
    a = s.lattice.matrix[0]
    b = s.lattice.matrix[1]
    c = s.lattice.matrix[2]

    normal = np.cross(a, b)  # Eq'n from http://www.euclideanspace.com/maths/geometry/elements/plane/lineOnPlane/
    normal = normal / np.linalg.norm(normal)
    perp_projection = np.dot(normal, vector) * normal
    plane_projection = vector - perp_projection

    as_a = intersection(plane_projection, a, b)
    as_b = intersection(plane_projection, b, a)

    if np.linalg.norm(as_a) < np.linalg.norm(as_b):
        lattice = Lattice([as_a, b, c])
    else:
        lattice = Lattice([a, as_b, c])

    return Structure(lattice, s.species, s.cart_coords, coords_are_cartesian=True, site_properties=s.site_properties)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('structure', help='Structure to Rotate',
                        type=str)
    parser.add_argument('atoms', help='Atoms to align along Vector A',
                        type=int, nargs='*')
    parser.add_argument('-o', '--output', help='Output file (Default aligned.vasp)',
                        default='aligned.vasp')
    parser.add_argument('-m', '--modecar', help='get vector from modecar (provide single atom)')
    args = parser.parse_args()

    # Load files
    structure = Poscar.from_file(args.structure).structure
    if args.modecar: # if constrained vector is provided (as MODECAR)
        with open(args.modecar) as modecar:
            vector = np.array([float(x) for x in modecar.readlines()[args.atoms[0]].split()])
    else: # otherwise make it from the structure
        vector = structure[args.atoms[0]].coords - structure[args.atoms[1]].coords
    structure = set_vector_as_boundary(structure, vector)
    Poscar(structure).write_file(args.output)