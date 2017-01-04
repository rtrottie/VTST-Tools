import os
from Classes_Custodian import *
import Generate_Surface
import AddDB

i = 25

folder = '/home/ryan/globus/defect_migration/Al-Fe-1/neb/67'

dir(folder)


p = Poscar.from_file('/home/ryan/scrap/POSCAR.bpa.tri.2.perp.larger.vasp')

AddDB.add_NEB('database', ['hercynite', 'feal2o4', folder])



Poscar(p.structure, selective_dynamics=sd).write_file('/home/ryan/scrap/POSCAR.sd.vasp')