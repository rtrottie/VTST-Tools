# functions to improve  ASE and output setup
# Not meant to be called from command line
from ase.calculators.vasp import Vasp
from ase.calculators.gulp import GULP
from ase.io import read
from ase.vibrations import Vibrations
from copy import copy
import os
import shutil
import numpy as np
from ase.calculators.calculator import FileIOCalculator
from ase.geometry import wrap_positions
from ase import Atoms

class StandardVasp(Vasp):
    def set_results(self, atoms):
        self.get_spin_polarized()
        return super().set_results(atoms)
    def initialize(self, atoms):
        self.resort = list(range(len(atoms)))
        return
    def write_input(self, atoms : Atoms, directory='./'):
        atoms.write(os.path.join(directory, 'POSCAR'))

class InPlane:
    '''
    Keeps Atoms in Plane between 3 atoms
    '''
    def __init__(self, diffusing_i, plane_i):
        self.diffusing_i = diffusing_i
        self.plane_i = plane_i

    def adjust_positions(self, atoms : Atoms, newpositions):
        # get Normal Vector
        atoms.wrap(atoms.get_scaled_positions()[self.diffusing_i])
        p1 = newpositions[self.plane_i[0]] # type: np.array
        p2 = newpositions[self.plane_i[1]] # type: np.array
        p3 = newpositions[self.plane_i[2]] # type: np.array
        v1 = p2 - p1
        v2 = p3 - p1

        # Get equation of plane ax+by+cz+d = 0
        normal = np.cross(v1, v2) / np.linalg.norm(np.cross(v1,v2))
        d = np.dot(normal, p1)
        a=normal[0]
        b=normal[1]
        c=normal[2]

        # Get closest point on plane
        p = newpositions[self.diffusing_i]
        k = (a*p[0] + b*p[1] + c*p[2] - d) / (a**2 + b**2 + c**2) # distance between point and plane
        position = [p[0] - k*a, p[1] - k*b, p[2] - k*c]
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

class LockedTo3AtomPlane(InPlane):
    '''
    Keeps Atoms in Plane between 3 atoms.  Keeps atom in same parrallel plane it starts in
    '''

    def __init__(self, diffusing_i, plane_i, orig_point):
        self.diffusing_i = diffusing_i
        self.plane_i = plane_i
        self.orig_point = orig_point

    def adjust_positions(self, atoms : Atoms, newpositions):
        # get Normal Vector
        print(newpositions)
        p1 = newpositions[self.plane_i[0]]  # type: np.array
        p2 = newpositions[self.plane_i[1]]  # type: np.array
        p3 = newpositions[self.plane_i[2]]  # type: np.array
        v1 = p2 - p1
        v2 = p3 - p1

        # Get equation of plane ax+by+cz+d = 0
        normal = np.cross(v1, v2) / np.linalg.norm(np.cross(v1, v2))
        d = np.dot(normal, self.orig_point)
        a = normal[0]
        b = normal[1]
        c = normal[2]

        # Get closest point on plane
        p = newpositions[self.diffusing_i]
        k = (a*p[0] + b*p[1] + c*p[2] - d) / (a**2 + b**2 + c**2) # distance between point and plane
        position = [p[0] - k*a, p[1] - k*b, p[2] - k*c]
        newpositions[self.diffusing_i] = position


class InMPPlane:
    def __init__(self, diffusing_i, plane_i):
        self.diffusing_i = diffusing_i
        self.plane_i = plane_i

    def get_plane(self, atoms : Atoms):
        # Make sure to get nearest images
        pos_1 = atoms.get_positions()[self.plane_i[0]]
        pos_2 = atoms.get_positions()[self.plane_i[1]]
        # get Normal Vector
        normal = pos_1 - pos_2
        # get Midpoint
        mp = (pos_1 + pos_2) / 2
        # get constant
        d = np.dot(normal, mp)
        # return constants
        return (normal[0], normal[1], normal[2], d)


    def adjust_positions(self, atoms : Atoms, newpositions):
        # get plane
        atoms.wrap(atoms.get_scaled_positions()[self.diffusing_i])
        (a, b, c, d) = self.get_plane(atoms) # ax + by + cz = d
        # Get closest point on plane
        p = atoms.positions[self.diffusing_i]
        k = (a*p[0] + b*p[1] + c*p[2] - d) / (a**2 + b**2 + c**2) # distance between point and plane
        position = [p[0] - k*a, p[1] - k*b, p[2] - k*c]
        newpositions[self.diffusing_i] = position

    def adjust_forces(self, atoms, forces):
        # get plane
        (a, b, c, d) = self.get_plane(atoms)
        normal = np.array([a,b,c]) / np.linalg.norm(np.array([a,b,c]))

        # project forces onto surface normal
        perp_projection = np.dot(normal, forces[self.diffusing_i] ) * normal
        forces[self.diffusing_i] = forces[self.diffusing_i] - perp_projection

class InMPPlaneXY:
    def __init__(self, diffusing_i, plane_i, alignment_vector=[0,0,1]):
        self.diffusing_i = diffusing_i
        self.plane_i = plane_i
        self.alignment_vector = alignment_vector
        self.a = None
        self.b = None
        self.c = None
        self.d = None
        self.iter = 9999

    def get_plane(self, atoms : Atoms):
        if self.iter < 50:
            self.iter += 1
            return (self.a, self.b, self.c, self.d)
        self.iter = 0
        # Make sure to get nearest images
        pos_1 = atoms.get_positions()[self.plane_i[0]]
        pos_2 = atoms.get_positions()[self.plane_i[1]]
        # get Normal Vector
        bond_vector = pos_1 - pos_2
        normal = np.cross(self.alignment_vector, (np.cross(bond_vector, self.alignment_vector) / np.linalg.norm(self.alignment_vector))) / np.linalg.norm(self.alignment_vector) # Eq'n from http://www.euclideanspace.com/maths/geometry/elements/plane/lineOnPlane/
        # get Midpoint
        mp = (pos_1 + pos_2) / 2
        # get constant
        d = np.dot(normal, mp)
        # return constants
        self.a = normal[0]
        self.b = normal[1]
        self.c = normal[2]
        self.d = d
        return (normal[0], normal[1], normal[2], d)


    def adjust_positions(self, atoms : Atoms, newpositions):
        # get plane
        atoms.wrap(atoms.get_scaled_positions()[self.diffusing_i])
        (a, b, c, d) = self.get_plane(atoms) # ax + by + cz = d
        # Get closest point on plane
        p = atoms.positions[self.diffusing_i]
        k = (a*p[0] + b*p[1] + c*p[2] - d) / (a**2 + b**2 + c**2) # distance between point and plane
        position = [p[0] - k*a, p[1] - k*b, p[2] - k*c]
        newpositions[self.diffusing_i] = position

    def adjust_forces(self, atoms, forces):
        # get plane
        (a, b, c, d) = self.get_plane(atoms)
        normal = np.array([a,b,c]) / np.linalg.norm(np.array([a,b,c]))

        # project forces onto surface normal
        perp_projection = np.dot(normal, forces[self.diffusing_i] ) * normal
        forces[self.diffusing_i] = forces[self.diffusing_i] - perp_projection

class InMPPlane_SurfaceReference:
    def __init__(self, diffusing_i, plane_i, surface_reference):
        self.diffusing_i = diffusing_i
        self.plane_i = plane_i
        surface_reference = read(surface_reference, format='vasp')
        self.surface_reference = surface_reference

    def get_plane(self):
        # Make sure to get nearest images
        atoms = self.surface_reference
        pos_1 = atoms.get_positions()[self.plane_i[0]]
        pos_2 = atoms.get_positions()[self.plane_i[1]]
        # get Normal Vector
        normal = pos_1 - pos_2
        # get Midpoint
        mp = (pos_1 + pos_2) / 2
        # get constant
        d = np.dot(normal, mp)
        # return constants
        return (normal[0], normal[1], normal[2], d)


    def adjust_positions(self, atoms : Atoms, newpositions):
        # get plane
        self.surface_reference.wrap(atoms.get_scaled_positions()[self.diffusing_i])
        (a, b, c, d) = self.get_plane() # ax + by + cz = d
        # Get closest point on plane
        p = atoms.positions[self.diffusing_i]
        k = (a*p[0] + b*p[1] + c*p[2] - d) / (a**2 + b**2 + c**2) # distance between point and plane
        position = [p[0] - k*a, p[1] - k*b, p[2] - k*c]
        newpositions[self.diffusing_i] = position

    def adjust_forces(self, atoms, forces):
        # get plane
        self.surface_reference.wrap(atoms.get_scaled_positions()[self.diffusing_i])
        (a, b, c, d) = self.get_plane()
        normal = np.array([a,b,c]) / np.linalg.norm(np.array([a,b,c]))

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

def write_input_scell(self, atoms, properties=None, system_changes=None):
    FileIOCalculator.write_input(self, atoms, properties, system_changes)
    p = self.parameters

    # Build string to hold .gin input file:
    s = p.keywords
    s += '\ntitle\nASE calculation\nend\n\n'

    if all(self.atoms.pbc) and 'scell' not in p.keywords:
        cell_params = self.atoms.get_cell_lengths_and_angles()
        s += 'cell\n{0} {1} {2} &\n {3} {4} {5}\n'.format(*cell_params)
        s += 'frac\n'
        coords = self.atoms.get_scaled_positions()
    elif all(self.atoms.pbc) and 'scell' in p.keywords:
        cell_params = self.atoms.get_cell_lengths_and_angles()
        s += 'scell\n{0} {1} {5}\n'.format(*cell_params)
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
    if 'scell' not in p.keywords:
        for xyz, symbol in zip(coords, labels):
            s += ' {0:2} core {1}  {2}  {3}\n'.format(symbol, *xyz)
            if symbol in p.shel:
                s += ' {0:2} shel {1}  {2}  {3}\n'.format(symbol, *xyz)
    elif 'scell' in p.keywords:
        for xyz, symbol in zip(coords, labels):
            s += ' {0:2} core {1}  {2}  {3}\n'.format(symbol, *xyz)
            if symbol in p.shel:
                s += ' {0:2} shel {1}  {2}  {3}\n'.format(symbol, *xyz)


    s += '\nlibrary {0}\n'.format(p.library)
    if p.options:
        for t in p.options:
            s += '%s\n' % t
    lines = s.split('\n')
    for line in lines:
        if len(line) > 80:
            raise Exception('Line length is to long, modify source code')
    with open(self.prefix + '.gin', 'w') as f:
        f.write(s)

def converged_fmax_or_emax(self, forces=None):
    try:
        convergedP = abs(self.previous_energy - self.atoms.get_potential_energy()) < (self.fmax / 10000)
        self.previous_energy = self.atoms.get_potential_energy()
        if not convergedP:
            if forces is None:
                forces = self.atoms.get_forces()
            if hasattr(self.atoms, 'get_curvature'):
                return ((forces ** 2).sum(axis=1).max() < self.fmax ** 2 and
                        self.atoms.get_curvature() < 0.0)
            return (forces ** 2).sum(axis=1).max() < self.fmax ** 2
        return convergedP
    except:
        self.previous_energy = self.atoms.get_potential_energy()
        if forces is None:
            forces = self.atoms.get_forces()
        if hasattr(self.atoms, 'get_curvature'):
            return ((forces ** 2).sum(axis=1).max() < self.fmax ** 2 and
                    self.atoms.get_curvature() < 0.0)
        return (forces ** 2).sum(axis=1).max() < self.fmax ** 2

class Vibration_Initializer(Vibrations):
    def setup(self):
        for filename, a, i, disp in self.displacements():
            dirname = copy(filename) # type: str
            dirname.replace('+', 'p')
            dirname.replace('-', 'm')
            atoms = self.atoms.copy() # type: Atoms
            atoms.positions[a, i] = atoms.positions[a, i] + disp
            os.makedirs(dirname, exist_ok=True)
            atoms.write(os.path.join(dirname, 'POSCAR'))
            for f in ['INCAR', 'KPOINTS', 'POTCAR', 'WAVECAR', 'CHG', 'CHGCAR']:
                shutil.copy(f, os.path.join(dirname,f))

GULP.write_input = write_input_scell