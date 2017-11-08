from Classes_ASE import InMPPlane
from ase.io import read

a=read('D:\\Users\\RyanTrottier\\Documents\\Scrap\\POSCAR')
ip = InMPPlane(48, [102, 32])
pos = a.get_positions()
a.set_constraint(ip)
a.set_positions(pos)
a.write('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR')
