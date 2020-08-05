# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 17:09:33 2020

@author: Markus Brandt

TESPy model of an water electrolyzer for district heating
"""

# %% imports

import matplotlib.pyplot as plt

import numpy as np

import pandas as pd

from scipy.stats import linregress

from tespy.components import (sink, source, compressor,
                              water_electrolyzer)
from tespy.connections import connection, bus
from tespy.networks import network
from tespy.tools.characteristics import char_line

import os.path as path

# %% boundaries

Hu      = 141.873524        # Energy content Hydrogen in MJ/kg
                            # Q_hydro = P_design * 0.8
                            # Hu = Q_hydro / comp_hydro.m.val
Q_hydro = 30                # Hydrogen in MW
eta_e   = 0.8               # Efficiency of the electrolyzer
T_cw_cold = 50              # Temperature of cold cooling water
T_cw_hot = 80               # Temperature of hot cooling water

# %% network

fluid_list = ['O2', 'H2O', 'H2']

nw = network(fluids=fluid_list, T_unit='C', p_unit='bar',
             v_unit='l / s', iterinfo=False)


# %% components

fw = source('feed water')
oxy = sink('oxygen sink')
hydro = sink('hydrogen sink')
cw_cold = source('cooling water source')
cw_hot = sink('cooling water sink')
comp = compressor('compressor', eta_s=0.9)
el = water_electrolyzer('electrolyzer')


# %% connections

fw_el = connection(fw, "out1", el, "in2")
el_comp = connection(el, 'out3', comp, 'in1')
comp_hydro = connection(comp, 'out1', hydro, 'in1')
el_oxy = connection(el, 'out2', oxy, 'in1')

cw_cold_el = connection(cw_cold, 'out1', el, 'in1')
el_cw_hot = connection(el, 'out1', cw_hot, 'in1')

nw.add_conns(fw_el, el_comp, comp_hydro, el_oxy, cw_cold_el, el_cw_hot)


# %% busses

# create characteristic line for the compressor motor
x = np.array([0.2, 0.4, 0.6, 0.8, 1.0, 1.1])
y = np.array([0.85, 0.93, 0.95, 0.96, 0.97, 0.96])
mot1 = char_line(x=x, y=y)

power = bus('total power bus')
power.add_comps({'comp': el, 'param': 'P'},
                {'comp': comp, 'char': mot1})
nw.add_busses(power)


# %% parameters

comp.set_attr(eta_s=0.9)
el.set_attr(P=Q_hydro*1e6 / 0.8, eta=eta_e, pr_c=0.99, design=['eta', 'pr_c'],
            offdesign=['eta_char', 'zeta'])

fw_el.set_attr(p=10, T=15)
cw_cold_el.set_attr(p=5, T=T_cw_cold, fluid={'H2O': 1, 'H2': 0, 'O2': 0})
el_cw_hot.set_attr(T=T_cw_hot)

comp_hydro.set_attr(p=25)
el_comp.set_attr(T=50)

comp.char_warnings=False
el.char_warnings=False


# %% solving

# Design - Mode

nw.solve('design')
nw.print_results()
nw.save('water_electrolyzer')
P_design = el.P.val
P_max = power.P.val

# Offdesign - Mode

Hydro_nutz = []
Q_nutz = []
E_zu = []
eta = []

for P in np.linspace(0.2,1,9)*P_design:
    el.set_attr(P=P)
    
    nw.solve('offdesign', init_path='water_electrolyzer',
              design_path='water_electrolyzer')
    
    Hydro_nutz  += [comp_hydro.m.val * Hu]
    Q_nutz      += [el.Q.val]
    E_zu        += [power.P.val/1e6]
    eta         += [(comp_hydro.m.val * Hu) / (power.P.val/1e6)]

# # Temperature influence

# el_cw_hot.set_attr(T=np.nan)

# T_range = np.linspace(80,120,40)

# for T in T_range:
#     el_cw_hot.set_attr(T=T)
    
#     nw.solve('offdesign', init_path='water_electrolyzer',
#              design_path='water_electrolyzer')
    
#     print('Systemwirkungsgrad: ' + str(comp_hydro.m.val * Hu /(power.P.val/1e6)))

# %% analysis

# determining c0, c1 for the oemof OffsetTransformer
# Linear regression: Hydro_nutz = a + b * E_zu
c1, c0, r, p, std = linregress(E_zu, Hydro_nutz)

solph_komp = {'P_in_max / MW': E_zu[-1], 'P_in_min / MW': E_zu[0],
              'c_1': c1, 'c_0': c0}
df = pd.DataFrame([solph_komp])

dirpath = path.abspath(path.join(__file__, "../../.."))
writepath = path.join(dirpath, 'Eingangsdaten', 'electrolyzer.csv')
df.to_csv(writepath, sep=';', na_rep='#N/A', index=False)

# Plot of linear regression
plt.scatter(E_zu, Hydro_nutz)
plt.plot([0,P_max],[c0,c0+P_max*c1],c="red",alpha=0.5)
plt.plot()

plt.xlim(E_zu[0],E_zu[-1])
plt.ylim(0,Hydro_nutz[-1])

plt.text(20, 14, r'y = {0} + {1}x (r=0.999)'.format(round(c0,3), round(c1,3)), fontsize=10)
plt.xlabel("E$_{el,input}$ (MW)")
plt.ylabel("H$_2$-Output (MW)")
plt.grid(alpha=0.4)

plt.show()

writepath = path.join(dirpath,
                      'Abbildungen', 'LinearRegression_Electrolyzer.pdf')
plt.savefig(writepath)