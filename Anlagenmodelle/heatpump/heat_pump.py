# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 13:41:41 2020

@author: TESPy-Example, Markus Brandt
"""

# %% imports

import matplotlib.pyplot as plt

import numpy as np

import pandas as pd

from scipy.stats import linregress

from tespy.networks import network
from tespy.components import (
    sink, source, splitter, compressor, condenser, pump, heat_exchanger_simple,
    valve, drum, heat_exchanger, cycle_closer
)
from tespy.connections import bus, connection, ref
from tespy.tools.characteristics import char_line
from tespy.tools.characteristics import load_default_char as ldc

import os.path as path


# %% importing data

dirpath = path.abspath(path.join(__file__, "../../.."))
readpath = path.join(dirpath, 'Eingangsdaten', 'fake_environmental_data.csv')
data = pd.read_csv(readpath, sep=";")


# %% boundaries

workload = np.linspace(0.5, 1, 5)
print(workload)


# %% network

nw = network(
    fluids=['water', 'NH3', 'air'], T_unit='C', p_unit='bar', h_unit='kJ / kg',
    m_unit='kg / s'
)


# %% components

# sources & sinks
cc = cycle_closer('coolant cycle closer')
cb = source('consumer back flow')
cf = sink('consumer feed flow')
amb = source('ambient air')
amb_out1 = sink('sink ambient 1')
amb_out2 = sink('sink ambient 2')

# ambient air system
sp = splitter('splitter')
pu = pump('pump')

# consumer system

cd = condenser('condenser')
dhp = pump('district heating pump')
cons = heat_exchanger_simple('consumer')

# evaporator system

ves = valve('valve')
dr = drum('drum')
ev = heat_exchanger('evaporator')
su = heat_exchanger('superheater')
erp = pump('evaporator reciculation pump')

# compressor-system

cp1 = compressor('compressor 1')
cp2 = compressor('compressor 2')
ic = heat_exchanger('intercooler')


# %% connections

# consumer system

c_in_cd = connection(cc, 'out1', cd, 'in1')

cb_dhp = connection(cb, 'out1', dhp, 'in1')
dhp_cd = connection(dhp, 'out1', cd, 'in2')
cd_cons = connection(cd, 'out2', cons, 'in1')
cons_cf = connection(cons, 'out1', cf, 'in1')

nw.add_conns(c_in_cd, cb_dhp, dhp_cd, cd_cons, cons_cf)

# connection condenser - evaporator system

cd_ves = connection(cd, 'out1', ves, 'in1')

nw.add_conns(cd_ves)

# evaporator system

ves_dr = connection(ves, 'out1', dr, 'in1')
dr_erp = connection(dr, 'out1', erp, 'in1')
erp_ev = connection(erp, 'out1', ev, 'in2')
ev_dr = connection(ev, 'out2', dr, 'in2')
dr_su = connection(dr, 'out2', su, 'in2')

nw.add_conns(ves_dr, dr_erp, erp_ev, ev_dr, dr_su)

amb_p = connection(amb, 'out1', pu, 'in1')
p_sp = connection(pu, 'out1', sp, 'in1')
sp_su = connection(sp, 'out1', su, 'in1')
su_ev = connection(su, 'out1', ev, 'in1')
ev_amb_out = connection(ev, 'out1', amb_out1, 'in1')

nw.add_conns(amb_p, p_sp, sp_su, su_ev, ev_amb_out)

# connection evaporator system - compressor system

su_cp1 = connection(su, 'out2', cp1, 'in1')

nw.add_conns(su_cp1)

# compressor-system

cp1_he = connection(cp1, 'out1', ic, 'in1')
he_cp2 = connection(ic, 'out1', cp2, 'in1')
cp2_c_out = connection(cp2, 'out1', cc, 'in1')

sp_ic = connection(sp, 'out2', ic, 'in2')
ic_out = connection(ic, 'out2', amb_out2, 'in1')

nw.add_conns(cp1_he, he_cp2, sp_ic, ic_out, cp2_c_out)


# %% busses

# create characteristic line for the compressor motor
x = np.array([0.2, 0.4, 0.6, 0.8, 1.0, 1.1])
y = np.array([0.85, 0.93, 0.95, 0.96, 0.97, 0.96])
mot1 = char_line(x=x, y=y)

power = bus('total power bus')
power.add_comps({'comp': pu, 'char': mot1},
                {'comp': erp, 'char': mot1},
                {'comp': cp1, 'char': mot1},
                {'comp': cp2, 'char': mot1},
                {'comp': dhp, 'char': mot1})
nw.add_busses(power)


# %% component parametrization

# condenser system

cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=5, design=['pr2', 'ttd_u'],
            offdesign=['zeta2', 'kA_char'])
dhp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
cons.set_attr(pr=0.99, design=['pr'], offdesign=['zeta'])

# water pump

pu.set_attr(eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char'])

# evaporator system

kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', char_line)
kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', char_line)

ev.set_attr(pr1=0.98, pr2=0.99, ttd_l=5,
            kA_char1=kA_char1, kA_char2=kA_char2,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
su.set_attr(pr1=0.98, pr2=0.99, ttd_u=2, design=['pr1', 'pr2', 'ttd_u'],
            offdesign=['zeta1', 'zeta2', 'kA_char'])
erp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

# compressor system

cp1.set_attr(eta_s=0.85, design=['eta_s'], offdesign=['eta_s_char'])
cp2.set_attr(eta_s=0.9, pr=3, design=['eta_s'], offdesign=['eta_s_char'])
ic.set_attr(pr1=0.99, pr2=0.98, design=['pr1', 'pr2'],
            offdesign=['zeta1', 'zeta2', 'kA_char'])


# %% connection parametrization

# condenser system

c_in_cd.set_attr(fluid={'air': 0, 'NH3': 1, 'water': 0})
cb_dhp.set_attr(T=60, p=10, fluid={'air': 0, 'NH3': 0, 'water': 1})
cd_cons.set_attr(T=100)
cons_cf.set_attr(h=ref(cb_dhp, 1, 0), p=ref(cb_dhp, 1, 0))

# evaporator system cold side

erp_ev.set_attr(m=ref(ves_dr, 1.25, 0), p0=5)
su_cp1.set_attr(p0=5, state='g')

# evaporator system hot side

# pumping at constant rate in partload
amb_p.set_attr(T=12, p=2, fluid={'air': 0, 'NH3': 0, 'water': 1},
               offdesign=['v'])
sp_su.set_attr(offdesign=['v'])
ev_amb_out.set_attr(p=2, T=9, design=['T'])

# compressor-system

he_cp2.set_attr(Td_bp=5, p0=20, design=['Td_bp'])
ic_out.set_attr(T=30, design=['T'])


# %% key paramter

Q_design = -30*1e6
cons.set_attr(Q=Q_design)


# %% calculation

nw.solve('design')
nw.print_results()
nw.save('heat_pump')

P_design = power.P.val
print(P_design)

# cons.set_attr(Q=np.nan)
# cd_cons.set_attr(T=66)
# amb_p.set_attr(T=25)
# power.set_attr(P=16847531.92616716 * 0.5)
# nw.solve('offdesign', init_path='heat_pump', design_path='heat_pump')

df = pd.DataFrame()

# Temperatur muss in gewissen Grenzen bleiben!
i = 0
for T_VL in data['T_VL']:
    T_water_amb = data['T_water_amb'][i]

    cons.set_attr(Q=np.nan)
    
    P = []
    Q = []
    
    for wl in workload:
        power.set_attr(P=P_design * wl)
        cd_cons.set_attr(T=T_VL)
        amb_p.set_attr(T=T_water_amb)
             
        nw.solve('offdesign', init_path='heat_pump', design_path='heat_pump')
        
        P += [power.P.val/1e6]
        Q += [-cons.Q.val/1e6]
        
    c1, c0, r, p, std = linregress(P, Q)  
    
    solph_komp = pd.DataFrame([{'P_in_max / MW': max(P),
                                'P_in_min / MW': min(P),
                                'c_1': c1, 'c_0': c0}])
    df = pd.concat([df, solph_komp])
    
    
    plt.plot(P, Q)
    plt.plot([0,max(P)],[c0,c0+max(P)*c1],c="red",alpha=0.5)
    plt.plot()
    
    plt.xlim(min(P),max(P))
    plt.ylim(0,max(Q))
    
    plt.text(8, 14, r'y = {0} + {1}x (r={2})'.format(round(c0,3),
                                                      round(c1,3),
                                                      round(r,3)), fontsize=10)
    plt.xlabel("P (MW)")
    plt.ylabel("$\dot{Q}$ (MW)")
    plt.grid(alpha=0.4)
    
    plt.show()
    
    i += 1

writepath = path.join(dirpath, 'Eingangsdaten', 'heat_pump.csv')
df.to_csv(writepath, sep=';', na_rep='#N/A', index=False)