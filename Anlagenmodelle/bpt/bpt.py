# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 09:53:20 2020

@author: Markus Brandt
"""

# %% imports

from fluprodia import FluidPropertyDiagram

import numpy as np

from tespy.networks import Network
from tespy.components import (
    Sink, Source, Compressor, Condenser, Pump,
    HeatExchangerSimple, CycleCloser, Turbine,    
)
from tespy.connections import Bus, Connection
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc


# %% useful functions

def plot_Ts(tespy_results):
    diagram = FluidPropertyDiagram('H2O')
    diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')

    iso_T = np.arange(0, 550, 25)
    diagram.set_isolines(T=iso_T)
    diagram.calc_isolines()
    
    diagram.set_limits(x_min=0, x_max=8000, y_min=0, y_max=550)
    diagram.draw_isolines('Ts')
    diagram.ax.scatter(tespy_results['s'], tespy_results['T'])
    diagram.ax.plot(tespy_results['s'], tespy_results['T'])
    diagram.save('Ts_diagram.svg')

def results():
    results = {'T': [cc_st.T.val,
                       st_con.T.val,
                       con_pu.T.val,
                       pu_sg1.T.val,
                       sg1_sg2.T.val,
                       sg2_sg3.T.val,
                       sg3_cc.T.val],
                 's': [cc_st.s.val,
                       st_con.s.val,
                       con_pu.s.val,
                       pu_sg1.s.val,
                       sg1_sg2.s.val,
                       sg2_sg3.s.val,
                       sg3_cc.s.val]}
    return results

# %% network

fluid_list = ['BICUBIC::H2O']

nw = Network(fluids=fluid_list,  p_unit='bar', T_unit='C',
             h_unit='kJ / kg', v_unit='l / s', iterinfo=False)

T_dh_in = 50
T_dh_out = 124          # might change due to 4GDH


# %% components

st = Turbine('steam Turbine')
con = Condenser('Condenser')
pu = Pump('feed water Pump')
sg1 = HeatExchangerSimple('steam generator: feed water heater')
sg2 = HeatExchangerSimple('steam generator: evaporater')
sg3 = HeatExchangerSimple('steam generator: superheater')
cc = CycleCloser('cycle closer')

dh_Source = Source('district heating Source')
dh_Sink = Sink('district heating Sink')


# %% Connection

# steam part
cc_st = Connection(cc, 'out1', st, 'in1')
st_con = Connection(st, 'out1', con, 'in1')
con_pu = Connection(con, 'out1', pu, 'in1')
pu_sg1 = Connection(pu, 'out1', sg1, 'in1')
sg1_sg2 = Connection(sg1, 'out1', sg2, 'in1')
sg2_sg3 = Connection(sg2, 'out1', sg3, 'in1')
sg3_cc = Connection(sg3, 'out1', cc, 'in1')

nw.add_conns(cc_st, st_con, con_pu, pu_sg1, sg1_sg2, sg2_sg3, sg3_cc)

# district heating
dh_Source_con = Connection(dh_Source, 'out1', con, 'in2')
con_dh_Sink = Connection(con, 'out2', dh_Sink, 'in1')

nw.add_conns(dh_Source_con, con_dh_Sink)


# %% Busses

# power Bus
power = Bus('power output')
x = np.array([0.2, 0.4, 0.6, 0.8, 1.0, 1.1])
y = np.array([0.85, 0.93, 0.95, 0.96, 0.97, 0.96])
# create a characteristic line for a generator
gen = CharLine(x=x, y=y)

power.add_comps(
    {'comp': st, 'char': gen},
    {'comp': pu, 'char': gen})
nw.add_busses(power)


# %% parameterisation

# components
st.set_attr(eta_s=0.9, design=['eta_s'], offdesign=['eta_s_char', 'cone'])
con.set_attr(pr1=0.99, pr2=0.99, ttd_u=5, design=['pr2', 'ttd_u'],
             offdesign=['kA_char'])
pu.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
sg1.set_attr(pr=0.99)
sg2.set_attr(pr=0.99)
sg3.set_attr(pr=.99)

sg1_sg2.set_attr(x=0)
sg2_sg3.set_attr(x=1)
# Connections
cc_st.set_attr(T=500, p=100, fluid={'H2O': 1})

dh_Source_con.set_attr(T=T_dh_in, p=10, fluid={'H2O': 1})
con_dh_Sink.set_attr(T=T_dh_out)


# %% keyparameter
con.set_attr(Q=-30e6)


# %% solving design mode
nw.solve('design')
nw.save('bpt')

print(power.P.val)

# plotting Ts-Diagram
results = results()
plot_Ts(results)


# %% offdesign

con.set_attr(Q=np.nan)
power.set_attr(P=-10263542)

nw.solve('offdesign', init_path='bpt', design_path='bpt')
print(power.P.val)

