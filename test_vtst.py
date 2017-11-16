from Classes_ASE import InMPPlaneXY
from ase.io import read
from Vis import view

a=read('D:\\Users\\RyanTrottier\\Documents\\Scrap\\POSCAR')
ip = InMPPlaneXY(48, [102, 32])
pos = a.get_positions()
a.set_constraint(ip)
a.set_positions(pos)
a.write('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR')
view('D:\\Users\\RyanTrottier\\Documents\\Scrap\\CONTCAR', 'vesta')
