# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 11:24:02 2020

@author: Markus Brandt
"""

# %% imports

from fluprodia import FluidPropertyDiagram

import numpy as np

from tespy.networks import network
from tespy.components import (
    sink, source, splitter, compressor, condenser, pump,
    valve, heat_exchanger, cycle_closer, combustion_chamber, turbine,
    merge
)
from tespy.connections import bus, connection, ref
from tespy.tools.characteristics import char_line
from tespy.tools.characteristics import load_default_char as ldc


# %% network

fluid_list = ['Ar', 'N2', 'O2', 'CO2', 'CH4', 'BICUBIC::H2O']

nw = network(fluids=fluid_list,  p_unit='bar', T_unit='C',
             h_unit='kJ / kg', v_unit='l / s', iterinfo=False)

t_dh_in = 50
t_dh_out = 124          # might change due to 4GDH


# %% components

# gas turbine part
air_source = source('air source')
air_compressor = compressor('air compressor')

combustion_chamber = combustion_chamber('combustion chamber')
fuel_source = source('fuel source')

gas_turbine = turbine('gas turbine')
steam_generator = heat_exchanger('steamgenerator') 
exhaust_gas = sink('exhaust gas')

# steam turbine part
fs_source = source('steam source')
steam_turbine = turbine('steam turbine')
dh_heat_exchanger = heat_exchanger('district heating heat exchanger')
pump = pump('pump')
fs_sink = sink('steam sink')

steam_cycle_closer = cycle_closer('steam cycle closer')

# district heating part
dh_source = source('district heating source')
dh_sink = sink('district heating sink')


# %% connections

# gas turbine part
air_source.air_compressor = connection(air_source, 'out1',
                                       air_compressor, 'in1')
air_compressor.combustion_chamber = connection(air_compressor, 'out1',
                                               combustion_chamber, 'in1')
combustion_chamber.gas_turbine = connection(combustion_chamber, 'out1',
                                            gas_turbine, 'in1') 
gas_turbine.steam_generator = connection(gas_turbine, 'out1',
                                         steam_generator, 'in1')
steam_generator.exhaust_gas = connection(steam_generator, 'out1',
                                        exhaust_gas, 'in1')

fuel_source.combustion_chamber = connection(fuel_source, 'out1',
                                            combustion_chamber, 'in2')

nw.add_conns(air_source.air_compressor, air_compressor.combustion_chamber,
             fuel_source.combustion_chamber,combustion_chamber.gas_turbine,
             gas_turbine.steam_generator, steam_generator.exhaust_gas)

# steam turbine part
fs_source.steam_generator = connection(fs_source, 'out1', 
                                       steam_generator, 'in2')
steam_generator.steam_turbine = connection(steam_generator, 'out2',
                                           steam_turbine, 'in1')
steam_turbine.dh_heat_exchanger = connection(steam_turbine, 'out1',
                                             dh_heat_exchanger, 'in1')
dh_heat_exchanger.pump = connection(dh_heat_exchanger, 'out1', pump, 'in1')
pump.fs_sink = connection(pump, 'out1', fs_sink, 'in1')

nw.add_conns(fs_source.steam_generator, steam_generator.steam_turbine,
             steam_turbine.dh_heat_exchanger, dh_heat_exchanger.pump,
             pump.fs_sink)

# district heating part
dh_source.dh_heat_exchanger = connection(dh_source, 'out1',
                                         dh_heat_exchanger, 'in2')
dh_heat_exchanger.dh_sink = connection(dh_heat_exchanger, 'out2',
                                       dh_sink, 'in1')

nw.add_conns(dh_source.dh_heat_exchanger, dh_heat_exchanger.dh_sink)


# %% parameterisation

# components
# gas turbine part
air_compressor.set_attr(pr=14, eta_s=0.91, design=['eta_s'],
                        offdesign=['char_map'])
gas_turbine.set_attr(eta_s=0.9, design=['eta_s'],
                     offdesign=['eta_s_char', 'cone'])
steam_generator.set_attr(pr1=0.99, pr2=0.99, design=['pr2'],
             offdesign=['zeta2', 'kA_char'])

# steam turbine part
steam_turbine.set_attr(eta_s=0.9, design=['eta_s'], offdesign=['eta_s_char',
                                                               'cone'])
pump.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

# district heating
dh_heat_exchanger.set_attr(pr1=0.99, pr2=0.99, ttd_u=5,
                           design=['pr2', 'ttd_u'],
                           offdesign=['zeta2', 'kA_char'])

# connections
# gas turbine part
air_source.air_compressor.set_attr(T=20, p=1, 
                                   fluid={'Ar': 0.0093, 'N2': 0.7808,
                                          'H2O': 0, 'CH4': 0, 'CO2': 0.0004,
                                          'O2': 0.2095})
fuel_source.combustion_chamber.set_attr(T=20,fluid={'Ar': 0, 'N2': 0, 'H2O': 0,
                                                    'CH4': 1, 'CO2': 0, 'O2': 0})
combustion_chamber.gas_turbine.set_attr(T=1200)
steam_generator.exhaust_gas.set_attr(p=1, T=150)

# steam turbine part
fs_source.steam_generator.set_attr(p=100, T=35, 
                                   fluid={'Ar': 0, 'N2': 0, 'H2O': 1,
                                          'CH4': 0, 'CO2': 0, 'O2': 0})
steam_generator.steam_turbine.set_attr(T=500)
dh_heat_exchanger.pump.set_attr(x=0)
pump.fs_sink.set_attr(p=ref(fs_source.steam_generator, 1, 0))

# district heating part
dh_source.dh_heat_exchanger.set_attr(T=t_dh_in, p=10,
                                     fluid={'Ar': 0, 'N2': 0,'H2O': 1,
                                            'CH4': 0, 'CO2': 0, 'O2': 0})
dh_heat_exchanger.dh_sink.set_attr(T=t_dh_out)


# %% Busses

# power bus
power = bus('power output')
x = np.array([0.2, 0.4, 0.6, 0.8, 1.0, 1.1])
y = np.array([0.85, 0.93, 0.95, 0.96, 0.97, 0.96])
# create a characteristic line for a generator
gen1 = char_line(x=x, y=y)

power.add_comps(
    {'comp': gas_turbine, 'char': gen1},
    {'comp': steam_turbine, 'char': gen1},
    {'comp': air_compressor})
nw.add_busses(power)

# heat bus
heat = bus('heat output')
heat.add_comps({'comp': dh_heat_exchanger})
nw.add_busses(heat)


# %% key parameter
# combustion_chamber.set_attr(ti=50e6) # 50 MW combustion chamber
# power.set_attr(P=-50e6)
heat.set_attr(P=-30e6)

# %% solving

nw.solve('design')
print(power.P.val/1e6)
print(heat.P.val/1e6)
print(-(power.P.val + heat.P.val)/combustion_chamber.ti.val)

print("Brennkammer Qzu: {0} MW".format(round(combustion_chamber.ti.val/1e6,2)))
print("Frischdampfmassenstrom: {0} kg/s".format(round(steam_generator.steam_turbine.m.val,2)))
