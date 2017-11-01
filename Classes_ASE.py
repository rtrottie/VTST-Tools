# functions to improve  ASE and output setup
# Not meant to be called from command line
from ase.calculators.vasp import Vasp
from ase.calculators.gulp import GULP
import os
import numpy as np
from ase.calculators.calculator import FileIOCalculator

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

        # Find vectors in plane
        v1 = p2 - p1
        v2 = p3 - p1

        # find unit vector normal to vectors in plane
        normal = np.cross(v1, v2) / np.linalg.norm(np.cross(v1,v2))

        # project forces onto surface normal
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

class HookeanPlane:
    def __init__(self, diffusing_i, plane_i, spring=1):
        self.diffusing_i = diffusing_i
        self.plane_i = plane_i
        self.spring = spring

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
        perp_projection = np.dot(normal, forces[self.diffusing_i] ) * normal

        # Update Forces to remove perp_projection
        forces[self.diffusing_i] = forces[self.diffusing_i] - perp_projection


        # Add Hookean Perp_projection
        # get Normal Vector

        # Get equation of plane ax+by+cz+d = 0
        normal = np.cross(v1, v2)
        a = normal[0]
        b = normal[1]
        c = normal[2]
        d = -(a*p1[0] + b*p1[1] + c*p1[2])

        # Get closest point on plane
        p = atoms.positions[self.diffusing_i]
        x = - (d + a*p[0] + b*p[1] + c*p[2]) / (a**2 + b**2 + c**2)
        position = [p[0] + x*a, p[1] + x*b, p[2] + x*c]

        # Add restoring Force
        forces[self.diffusing_i] -= (np.linalg.norm(atoms.positions[self.diffusing_i] - position) * self.spring)

class GULP_fixed_io(GULP):
    def write_input(self, atoms, properties=None, system_changes=None):
        FileIOCalculator.write_input(self, atoms, properties, system_changes)
        p = self.parameters

        # Build string to hold .gin input file:
        s = p.keywords
        s += '\ntitle\nASE calculation\nend\n\n'

        if all(self.atoms.pbc) and 'scell' not in self.keywords:
            cell_params = self.atoms.get_cell_lengths_and_angles()
            s += 'cell\n{0} {1} {2} {3} {4} {5}\n'.format(*cell_params)
            s += 'frac\n'
            coords = self.atoms.get_scaled_positions()
        elif all(self.atoms.pbc) and 'scell' in self.keywords:
            cell_params = self.atoms.get_cell_lengths_and_angles()
            s += 'cell\n{0} {1} {5}\n'.format(*cell_params)
            s += 'cart\n'
            coords = self.atoms.get_positions()
        else:
            s += 'cart\n'
            coords = self.atoms.get_positions()

        if self.conditions is not None:
            c = self.conditions
            labels = c.get_atoms_labels()
            self.atom_types = c.get_atom_types()
        else:
            labels = self.atoms.get_chemical_symbols()
        if 'scell' not in self.keywords:
            for xyz, symbol in zip(coords, labels):
                s += ' {0:2} core {1}  {2}  {3}\n'.format(symbol, *xyz)
                if symbol in p.shel:
                    s += ' {0:2} shel {1}  {2}  {3}\n'.format(symbol, *xyz)
        elif 'scell' not in self.keywords:
            for xyz, symbol in zip(coords, labels):
                s += ' {0:2} core {1}  {2}  {3}\n'.format(symbol, *xyz)
                if symbol in p.shel:
                    s += ' {0:2} shel {1}  {2}  {3}\n'.format(symbol, *xyz)


        s += '\nlibrary {0}\n'.format(p.library)
        if p.options:
            for t in p.options:
                s += '%s\n' % t
        with open(self.prefix + '.gin', 'w') as f:
            f.write(s)
