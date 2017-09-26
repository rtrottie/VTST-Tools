# functions to improve  ASE and output setup
# Not meant to be called from command line
from ase.calculators.vasp import Vasp
import os
import numpy as np

class StandardVasp(Vasp):
    def write_input(self, atoms, directory='./'):
        from ase.io.vasp import write_vasp
        write_vasp(os.path.join(directory, 'POSCAR'), self.atoms_sorted, symbol_count = self.symbol_count)
        self.write_sort_file(directory=directory)

class InPlane:
    def __init__(self, diffusing_i, plane_i):
        self.diffusing_i = diffusing_i
        self.plane_i = plane_i

    def adjust_positions(self, oldpositions, newpositions):
        # get Normal Vector
        p1 = newpositions[self.plane_i[0]] # type: np.array
        p2 = newpositions[self.plane_i[1]] # type: np.array
        p3 = newpositions[self.plane_i[2]] # type: np.array
        v1 = p2 - p1
        v2 = p3 - p1

        # Get equation of plane ax+by+cz+d = 0
        normal = np.cross(v1, v2)
        a = normal[0]
        b = normal[1]
        c = normal[2]
        d = -(a*p1[0] + b*p1[1] + c*p1[2])

        # Get closest point on plane
        p = newpositions[self.diffusing_i]
        x = - (d + a*p[0] + b*p[1] + c*p[2]) / (a**2 + b**2 + c**2)
        position = [p[0] + x*a, p[1] + x*b, p[2] + x*c]
        newpositions[self.diffusing_i] = position

    def adjust_forces(self, atoms, forces):
        # get Normal Vector
        p1 = atoms.positions[self.plane_i[0]] # type: np.array
        p2 = atoms.positions[self.plane_i[1]] # type: np.array
        p3 = atoms.positions[self.plane_i[2]] # type: np.array
        v1 = p2 - p1
        v2 = p3 - p1
        normal = np.cross(v1, v2) / np.linalg.norm(np.cross(v1,v2))

        # Get equation of plane ax+by+cz+d = 0
        perp_projection = np.dot(normal, forces[self.diffusing_i] ) * normal
        forces[self.diffusing_i] = forces[self.diffusing_i] - perp_projection

class InvertPlane:
    def __init__(self, diffusing_i, plane_i):
        self.diffusing_i = diffusing_i
        self.plane_i = plane_i

    def adjust_positions(self, oldpositions, newpositions):
        return

    def adjust_forces(self, atoms, forces):
        # get Normal Vector
        p1 = atoms.positions[self.plane_i[0]] # type: np.array
        p2 = atoms.positions[self.plane_i[1]] # type: np.array
        p3 = atoms.positions[self.plane_i[2]] # type: np.array
        v1 = p2 - p1
        v2 = p3 - p1
        normal = np.cross(v1, v2) / np.linalg.norm(np.cross(v1,v2))

        # Get equation of plane ax+by+cz+d = 0
        perp_projection = 2 * np.dot(normal, forces[self.diffusing_i] ) * normal # Invert Forces
        forces[self.diffusing_i] = forces[self.diffusing_i] - perp_projection