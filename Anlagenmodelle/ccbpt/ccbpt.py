# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 11:24:02 2020

@author: Markus Brandt
"""

# %% imports

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
steam_generator.fs_sink = connection(steam_generator, 'out2', fs_sink, 'in1')

nw.add_conns(fs_source.steam_generator, steam_generator.fs_sink)


# %% parameterisation

# components
# gas turbine part
air_compressor.set_attr(pr=14, eta_s=0.91, design=['eta_s'],
                        offdesign=['char_map'])
gas_turbine.set_attr(eta_s=0.9, design=['eta_s'],
                     offdesign=['eta_s_char', 'cone'])
steam_generator.set_attr(pr1=0.99, pr2=0.99,  ttd_u=50)

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


#key parameter
combustion_chamber.set_attr(ti=50e6) # 50 MW combustion chamber

# %% solving

nw.solve('design') 
print(steam_generator.fs_sink.T.val)
