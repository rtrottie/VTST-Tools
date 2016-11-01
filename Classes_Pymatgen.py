# functions to improve Pymatgen Classes and output setup
# Not meant to be called from command line
from pymatgen.io.vasp.inputs import *
from pymatgen.io.vasp.outputs import *
import pymatgen as pmg
import numpy as np
import cfg

def get_string_more_sigfig(self, direct=True, vasp4_compatible=False, significant_figures=20):
    """
    Returns a string to be written as a POSCAR file. By default, site
    symbols are written, which means compatibility is for vasp >= 5.

    Args:
        direct (bool): Whether coordinates are output in direct or
            cartesian. Defaults to True.
        vasp4_compatible (bool): Set to True to omit site symbols on 6th
            line to maintain backward vasp 4.x compatibility. Defaults
            to False.
        significant_figures (int): No. of significant figures to
            output all quantities. Defaults to 6. Note that positions are
            output in fixed point, while velocities are output in
            scientific format.

    Returns:
        String representation of POSCAR.
    """

    # This corrects for VASP really annoying bug of crashing on lattices
    # which have triple product < 0. We will just invert the lattice
    # vectors.
    latt = self.structure.lattice
    if np.linalg.det(latt.matrix) < 0:
        latt = Lattice(-latt.matrix)
    fl = "%."+str(significant_figures)+"f"
    str_latt = "\n".join([" ".join([fl % i for i in row])
                          for row in latt._matrix])
    lines = [self.comment, "1.0", str_latt]
    if self.true_names and not vasp4_compatible:
        lines.append(" ".join(self.site_symbols))
    lines.append(" ".join([str(x) for x in self.natoms]))
    if self.selective_dynamics:
        lines.append("Selective dynamics")
    lines.append("direct" if direct else "cartesian")

    format_str = "{{:.{0}f}}".format(significant_figures)

    for (i, site) in enumerate(self.structure):
        coords = site.frac_coords if direct else site.coords
        line = " ".join([format_str.format(c) for c in coords])
        if self.selective_dynamics is not None:
            sd = ["T" if j else "F" for j in self.selective_dynamics[i]]
            line += " %s %s %s" % (sd[0], sd[1], sd[2])
        line += " " + site.species_string
        lines.append(line)

    if self.velocities:
        lines.append("")
        for v in self.velocities:
            lines.append(" ".join([format_str.format(i) for i in v]))

    if self.predictor_corrector:
        lines.append("")
        lines.append(str(self.predictor_corrector[0][0]))
        lines.append(str(self.predictor_corrector[1][0]))
        for v in self.predictor_corrector[2:]:
            lines.append(" ".join([format_str.format(i) for i in v]))

    return "\n".join(lines) + "\n"

def pretty_incar_string(self, sort_keys=True, pretty=False):
    set_keywords = set(self.keys())
    s = ''
    for section_tup in cfg.INCAR_format:
        (section, section_keywords) = section_tup
        if bool(set(section_keywords) & set_keywords):
            s = s + ('#' * (4 + len(section))) + '\n' +'# ' + section.upper() + ' #' + '\n' + ('#' * (4 + len(section))) + '\n'
            for key in section_keywords:
                if key.upper() in set_keywords:
                    if key == "MAGMOM" and isinstance(self[key], list):
                        value = []
                        for m, g in itertools.groupby(self[key]):
                            value.append("{}*{}".format(len(tuple(g)), m))
                        s = s + key.upper() + ' = ' + " ".join(value) + '\n'
                    elif isinstance(self[key], list):
                        s = s + key.upper() + ' = ' + " ".join([str(i) for i in self[key]]) + '\n'
                    else:
                        s = s + key.upper() + ' = ' + str(self[key]) + '\n'
                    set_keywords.remove(key)
        s = s + '\n'
    s = s + ('#' * 9) + '\n' +'# OTHER #' + '\n' + ('#' * 9) + '\n'
    for key in set_keywords:
        if isinstance(self[key], list):
            s = s + key.upper() + ' = ' + " ".join([str(i) for i in self[key]]) + '\n'
        else:
            s = s + key.upper() + ' = ' + str(self[key]) + '\n'
    return s

def perturb_sites(self, distance, sites):
    """
    Performs a random perturbation of the sites in a structure to break
    symmetries.
    Args:
    distance (float): Distance in angstroms by which to perturb each
        site.
    sites (list : int):  Sites to perturb
    """
    def get_rand_vec():
        #deals with zero vectors.
        vector = np.random.randn(3)
        vnorm = np.linalg.norm(vector)
        return vector / vnorm * distance if vnorm != 0 else get_rand_vec()

    for i in sites:
        self.translate_sites([i], get_rand_vec())

def perturb_Poscar(self, distance):
    """

    Args:
        distance:

    Returns:

    :type self: Poscar

    """
    if self.selective_dynamics:
        sites = zip(self.selective_dynamics, range(len(self.selective_dynamics)))
        sites = map(lambda x: x[1], filter(lambda x : x[0][0], sites))
        self.structure.perturb_sites(distance, sites)
    else:
        self.structure.perturb(distance)



class VaspNEBInput(VaspInput):
    def __init__(self, incar, kpoints, poscars, potcar, optional_files=None,
                 **kwargs):
        super(VaspInput, self).__init__(**kwargs)
        self.update({'INCAR': incar,
                     'KPOINTS': kpoints,
                     'POSCARs': poscars,
                     'POTCAR': potcar})
        if optional_files is not None:
            self.update(optional_files)

    def write_input(self, output_dir=".", make_dir_if_not_present=True):
        """
        Write VASP input to a directory.

        Args:
            output_dir (str): Directory to write to. Defaults to current
                directory (".").
            make_dir_if_not_present (bool): Create the directory if not
                present. Defaults to True.
        """
        if make_dir_if_not_present and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for k, v in self.items():
            if k == 'POSCARs':
                for i in range(len(v)):
                    if not os.path.exists(os.path.join(output_dir, str(i).zfill(2))):
                        os.mkdir(os.path.join(output_dir, str(i).zfill(2)))
                    with zopen(os.path.join(output_dir, str(i).zfill(2), 'POSCAR'), "wt") as f:
                        f.write(v[i].get_string())
            else:
                with zopen(os.path.join(output_dir, k), "wt") as f:
                    f.write(v.__str__())

    @staticmethod
    def from_directory(input_dir, check_CONTCAR=False, optional_files=None):
        """
        Read in a set of VASP NEB input from a directory. Note that only the
        standard INCAR, POSCARs, POTCAR and KPOINTS files are read unless
        optional_filenames is specified.

        Args:
            input_dir (str): Directory to read VASP input from.
            check_CONTCAR : uses CONTCARs instead of POSCARS if they are available
            optional_files (dict): Optional files to read in as well as a
                dict of {filename: Object type}. Object type must have a
                static method from_file.
        """
        sub_d = {}
        for fname, ftype in [("INCAR", Incar), ("KPOINTS", Kpoints),
                             ("POTCAR", Potcar)]:
            fullzpath = zpath(os.path.join(input_dir, fname))
            sub_d[fname.lower()] = ftype.from_file(fullzpath)

        neb_dirs = []

        for d in os.listdir(input_dir):
            pth = os.path.join(input_dir, d)
            if os.path.isdir(pth) and d.isdigit():
                image = int(d)
                neb_dirs.append((image, pth))
        neb_dirs = sorted(neb_dirs, key=lambda d: d[0])

        poscars = []
        for image in neb_dirs:
            if check_CONTCAR:
                try:
                    poscars.append(PoscarNEB.from_file(os.path.join(image[1], 'CONTCAR')))
                except:
                    print('CONTCAR not valid in ' + os.path.basename(image[1]) + ' using POSCAR')
                    poscars.append(PoscarNEB.from_file(os.path.join(image[1], 'POSCAR')))
            else:
                poscars.append(PoscarNEB.from_file(os.path.join(image[1], 'POSCAR')))
        sub_d['poscars'] = poscars
        sub_d["optional_files"] = {}
        if optional_files is not None:
            for fname, ftype in optional_files.items():
                sub_d["optional_files"][fname] = \
                    ftype.from_file(os.path.join(input_dir, fname))
        return VaspNEBInput(**sub_d)

class PoscarNEB(Poscar):

    def __init__(self, structure, comment=None, selective_dynamics=None,
                 true_names=True, velocities=None, predictor_corrector=None):
        if structure.is_ordered:
            self.structure = structure
            self.true_names = true_names
            self.selective_dynamics = selective_dynamics
            self.comment = structure.formula if comment is None else comment
            self.velocities = velocities
            self.predictor_corrector = predictor_corrector
        else:
            raise ValueError("Structure with partial occupancies cannot be "
                             "converted into POSCAR!")

        self.temperature = -1

    @staticmethod
    def from_file(filename, check_for_POTCAR=True):
        """
        Reads a Poscar from a file.

        The code will try its best to determine the elements in the POSCAR in
        the following order:
        1. If check_for_POTCAR is True, the code will try to check if a POTCAR
        is in the same directory as the POSCAR and use elements from that by
        default. (This is the VASP default sequence of priority).
        2. If the input file is Vasp5-like and contains element symbols in the
        6th line, the code will use that if check_for_POTCAR is False or there
        is no POTCAR found.
        3. Failing (2), the code will check if a symbol is provided at the end
        of each coordinate.

        If all else fails, the code will just assign the first n elements in
        increasing atomic number, where n is the number of species, to the
        Poscar. For example, H, He, Li, ....  This will ensure at least a
        unique element is assigned to each site and any analysis that does not
        require specific elemental properties should work fine.

        Args:
            filename (str): File name containing Poscar data.
            check_for_POTCAR (bool): Whether to check if a POTCAR is present
                in the same directory as the POSCAR. Defaults to True.

        Returns:
            Poscar object.
        """
        dirname = os.path.dirname(os.path.dirname(os.path.abspath(filename)))
        names = None
        if check_for_POTCAR:
            for f in os.listdir(dirname):
                if f == "POTCAR":
                    try:
                        potcar = Potcar.from_file(os.path.join(dirname, f))
                        names = [sym.split("_")[0] for sym in potcar.symbols]
                        [get_el_sp(n) for n in names] # ensure valid names
                    except:
                        names = None
        with zopen(filename, "rt") as f:
            return PoscarNEB.from_string(f.read(), names)

    @staticmethod
    def from_string(data, default_names=None):
        """
        Reads a Poscar from a string.

        The code will try its best to determine the elements in the POSCAR in
        the following order:
        1. If default_names are supplied and valid, it will use those. Usually,
        default names comes from an external source, such as a POTCAR in the
        same directory.
        2. If there are no valid default names but the input file is Vasp5-like
        and contains element symbols in the 6th line, the code will use that.
        3. Failing (2), the code will check if a symbol is provided at the end
        of each coordinate.

        If all else fails, the code will just assign the first n elements in
        increasing atomic number, where n is the number of species, to the
        Poscar. For example, H, He, Li, ....  This will ensure at least a
        unique element is assigned to each site and any analysis that does not
        require specific elemental properties should work fine.

        Args:
            data (str): String containing Poscar data.
            default_names ([str]): Default symbols for the POSCAR file,
                usually coming from a POTCAR in the same directory.

        Returns:
            Poscar object.
        """
        # "^\s*$" doesn't match lines with no whitespace
        chunks = re.split("\n\s*\n", data.rstrip(), flags=re.MULTILINE)
        try:
            if chunks[0] == "":
                chunks.pop(0)
                chunks[0] = "\n" + chunks[0]
        except IndexError:
            raise ValueError("Empty POSCAR")
            #Parse positions
        lines = tuple(clean_lines(chunks[0].split("\n"), False))
        comment = lines[0]
        scale = float(lines[1])
        lattice = np.array([[float(i) for i in line.split()]
                            for line in lines[2:5]])
        if scale < 0:
            # In vasp, a negative scale factor is treated as a volume. We need
            # to translate this to a proper lattice vector scaling.
            vol = abs(det(lattice))
            lattice *= (-scale / vol) ** (1 / 3)
        else:
            lattice *= scale

        vasp5_symbols = False
        try:
            natoms = [int(i) for i in lines[5].split()]
            ipos = 6
        except ValueError:
            vasp5_symbols = True
            symbols = lines[5].split()
            natoms = [int(i) for i in lines[6].split()]
            atomic_symbols = list()
            for i in range(len(natoms)):
                atomic_symbols.extend([symbols[i]] * natoms[i])
            ipos = 7

        postype = lines[ipos].split()[0]

        sdynamics = False
        # Selective dynamics
        if postype[0] in "sS":
            sdynamics = True
            ipos += 1
            postype = lines[ipos].split()[0]

        cart = postype[0] in "cCkK"
        nsites = sum(natoms)

        # If default_names is specified (usually coming from a POTCAR), use
        # them. This is in line with Vasp"s parsing order that the POTCAR
        # specified is the default used.
        if default_names:
            try:
                atomic_symbols = []
                for i in range(len(natoms)):
                    atomic_symbols.extend([default_names[i]] * natoms[i])
                vasp5_symbols = True
            except IndexError:
                pass

        if not vasp5_symbols:
            ind = 3 if not sdynamics else 6
            try:
                # Check if names are appended at the end of the coordinates.
                atomic_symbols = [l.split()[ind]
                                  for l in lines[ipos + 1:ipos + 1 + nsites]]
                # Ensure symbols are valid elements
                if not all([Element.is_valid_symbol(sym)
                            for sym in atomic_symbols]):
                    raise ValueError("Non-valid symbols detected.")
                vasp5_symbols = True
            except (ValueError, IndexError):
                # Defaulting to false names.
                atomic_symbols = []
                for i in range(len(natoms)):
                    sym = Element.from_Z(i + 1).symbol
                    atomic_symbols.extend([sym] * natoms[i])
                warnings.warn("Elements in POSCAR cannot be determined. "
                              "Defaulting to false names {}."
                    .format(" ".join(atomic_symbols)))

        # read the atomic coordinates
        coords = []
        selective_dynamics = list() if sdynamics else None
        for i in range(nsites):
            toks = lines[ipos + 1 + i].split()
            crd_scale = scale if cart else 1
            coords.append([float(j) * crd_scale for j in toks[:3]])
            if sdynamics:
                selective_dynamics.append([tok.upper()[0] == "T"
                                           for tok in toks[3:6]])

        struct = Structure(lattice, atomic_symbols, coords,
                           to_unit_cell=False, validate_proximity=False,
                           coords_are_cartesian=cart)

        # Parse velocities if any
        velocities = []
        if len(chunks) > 1:
            for line in chunks[1].strip().split("\n"):
                velocities.append([float(tok) for tok in line.split()])

        predictor_corrector = []
        if len(chunks) > 2:
            lines = chunks[2].strip().split("\n")
            predictor_corrector.append([int(lines[0])])
            for line in lines[1:]:
                predictor_corrector.append([float(tok)
                                            for tok in line.split()])

        return PoscarNEB(struct, comment, selective_dynamics, vasp5_symbols,
                      velocities=velocities,
                      predictor_corrector=predictor_corrector)

    def get_string(self, direct=True, vasp4_compatible=False,
                   significant_figures=20):
        return get_string_more_sigfig(self, direct=True, vasp4_compatible=False,significant_figures=20)

    def __str__(self):
        """
        String representation of Poscar file.
        """
        return self.get_string(significant_figures=20)

class Modecar(MSONable):

    def __init__(self, contents):
        self.contents = contents

    def __str__(self):
        return unicode(self.contents)

    @staticmethod
    def from_file(modecar_file):
        with open(modecar_file, "r") as f:
            return Modecar(f.read())

    def as_dict(self):
        d = {'contents': self}
        return d

    @classmethod
    def from_dict(cls, d):
        return (d['contents'])



Poscar.get_string = get_string_more_sigfig
Poscar.perturb = perturb_Poscar
Incar.get_string = pretty_incar_string
pmg.Structure.perturb_sites = perturb_sites
