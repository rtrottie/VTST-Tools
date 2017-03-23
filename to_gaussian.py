import Vis
from Classes_Pymatgen import Structure
import pymatgen.core
from math import gcd
from pymatgen.core import Molecule
import Generate_Surface
type = 'xyz'

# s = Structure.from_file('D:\\Users\\RyanTrottier\\Downloads\\Al2FeO4_mvc-16241_computed.cif')
# surf = Generate_Surface.Generate_Surface(s, [1,1,1], 5, 5, 15, vacuum=30)
# surf = surf[3] # pymatgen.core.Structure
# surf = Molecule.from_sites(surf.sites)
#
# surf = surf.to(type, 'D:\\Users\\RyanTrottier\\Documents\\Scrap\\tmp.'+type)

def get_elements_count(structure: pymatgen.Molecule):
    '''

    :param structure: gets count of all element in structure
    :return: Dict
    '''
    element_dict = {}
    for element in structure.types_of_specie: # Make dictionary with all elements
        element_dict[element] = 0
    for site in structure: # type: pymatgen.Site
        element_dict[site.specie] = element_dict[site.specie] + 1
    return element_dict

def get_stoichiometry(structure: pymatgen.Molecule):
    '''
        Gets Stoichiometry of all element in structure
    :param structure:
    :return: Dict
        Dictionary of stoichiometric ratios
    '''
    element_dict = get_elements_count(structure)
    if len(element_dict) < 2:
        for element, count in element_dict.items():
            element_dict[element] = 1
    else:
        current_gcd = 0
        for element, count in element_dict.items():
            current_gcd = gcd(current_gcd, count)
        for element, count in element_dict.items():
            element_dict[element] = int(count / current_gcd)

    return element_dict

def get_weight(stoich: dict):
    '''
    Inverts stoichiometric ratios, maintains integers, does not consider lcm
    :param stoich: dict
    :return: dict
    '''
    weights = {}
    common_multiple = 1
    for key,count in stoich.items():  # Find common multiple
        common_multiple = common_multiple*count

    for key,count in stoich.items():  # Get Weights
        weights[key] = int(common_multiple / count)

    return weights

def lcm_pair(x, y):
   """This function takes two
   integers and returns the L.C.M."""

   lcm = (x*y)//gcd(x,y)
   return lcm

def lcm_list(values):
    lcm = values[0]
    for value in values:
        lcm = lcm_pair(lcm, value)
    return lcm

def get_remainder(structure: pymatgen.Molecule, stoich: dict):
    '''
    Gets number of atoms that must be added to match stoichiometry
    :param structure: Strcutre to find additional atoms that must be added
    :param stoich: Desired Stoichiometry
    :return: dict of number of atoms to add
    '''
    remainder = {}
    count_dict = get_elements_count(structure)
    weights = get_weight(stoich)
    scaled_max = max([count_dict[ele]*weights[ele] for ele in stoich.keys() ]) #determine the scaled maximum neded

    while scaled_max % lcm_list(list(weights.values())): # increase scaled max until it can accomodate correct stoichiometry
        scaled_max = scaled_max + 1

    for ele, count in count_dict.items():
        remainder[ele] = int((scaled_max - count_dict[ele]*weights[ele]) / (weights[ele]))

    return remainder


surf = Molecule.from_file('D:\\Users\\RyanTrottier\\Documents\\Scrap\\tmp.'+type)

center_i = 787
center = surf[center_i] # pymatgen.core.sites.Site
for radius in [4,5,6,7,8,9,10,5.5]:
    dr = 4

    stoich = get_stoichiometry(surf)

    sites = [center] + [ x[0] for x in surf.get_neighbors(center, radius)]

    mol = Molecule.from_sites(sites)
    remainder = get_remainder(mol, stoich)

    i = 0 # going to iterate over all sites, starting with the closest
    add_sites = surf.get_neighbors_in_shell(center.coords, radius+dr, dr)
    add_sites.sort(key=lambda a: a[1])

    while max(remainder.values()) > 0: # while atoms still need to be added
        (site, distance) = add_sites[i] # type: pymatgen.Site
        if remainder[site.specie] > 0 : # if site should be added
            mol.append(site.specie, site.coords, properties=site.properties) # Add site
            remainder[site.specie] = remainder[site.specie] - 1
        i = i + 1
    type='xyz'
    mol.to(type, 'D:\\Users\\RyanTrottier\\Documents\\Scrap\\feal2o4_{}.{}'.format(radius, type))
