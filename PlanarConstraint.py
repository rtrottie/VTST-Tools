class InPlane:
    """
    Keeps Atoms in Plane between 3 atoms
    """
    def __init__(self, diffusing_i: int, plane_i: list):
        """

        :param diffusing_i: diffuing atom
        :param plane_i: list of plane atoms
        """
        self.diffusing_i = diffusing_i
        self.plane_i = plane_i

    def adjust_positions(self, atoms: Atoms, newpositions):
        """

        :param atoms: structure to be adjusted
        :param newpositions: positions from dft code
        :return:
        """
        # get Normal Vector
        atoms.wrap(atoms.get_scaled_positions()[self.diffusing_i])
        p1 = newpositions[self.plane_i[0]]  # type: np.array
        p2 = newpositions[self.plane_i[1]]  # type: np.array
        p3 = newpositions[self.plane_i[2]]  # type: np.array
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

class MaintainPlane(InPlane):
    """
    Keeps Atoms in Plane defined by 3 atoms.  Keeps atom in same parallel plane it starts in
    """

    def __init__(self, diffusing_i, plane_i, orig_point):
        self.diffusing_i = diffusing_i
        self.plane_i = plane_i
        self.orig_point = orig_point
        self.distance = None

    def adjust_positions(self, atoms : Atoms, newpositions):
        # get Normal Vector
        p1 = newpositions[self.plane_i[0]]  # type: np.array
        p2 = newpositions[self.plane_i[1]]  # type: np.array
        p3 = newpositions[self.plane_i[2]]  # type: np.array
        v1 = p2 - p1
        v2 = p3 - p1

        # Get equation of plane ax+by+cz+d = 0
        normal = np.cross(v1, v2) / np.linalg.norm(np.cross(v1, v2))
        a = normal[0]
        b = normal[1]
        c = normal[2]
        d = np.dot(normal, p1)
        if self.distance == None:
            p = atoms.get_positions()[self.diffusing_i]
            self.distance = (a*p[0] + b*p[1] + c*p[2] - d) / (a**2 + b**2 + c**2) # distance between point and plane

        # Get closest point on plane
        p = newpositions[self.diffusing_i]
        k = (a*p[0] + b*p[1] + c*p[2] - d) / (a**2 + b**2 + c**2) # distance between point and plane
        k -= self.distance # point should be displaced from plane
        position = [p[0] - k*a, p[1] - k*b, p[2] - k*c]
        newpositions[self.diffusing_i] = position