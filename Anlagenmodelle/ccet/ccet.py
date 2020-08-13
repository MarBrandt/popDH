# -*- coding: utf-8 -*-
"""
Created on Thu Jul 27 09:13:46 2019

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


# %% functions

def alpha(Q_dh, Q_cc):
    alpha = abs(Q_dh)/Q_cc
    return alpha

def beta(P_ges, Q_cc):
    beta = abs(P_ges)/Q_cc
    return beta

# %% network
fluid_list = ['Ar', 'N2', 'O2', 'CO2', 'CH4', 'H2O']

nw = network(fluids=fluid_list, p_unit='bar', T_unit='C', h_unit='kJ / kg',
                 p_range=[1, 15], T_range=[10, 1200], h_range=[500, 4000])

t_dh_in = 50        
t_dh_out = 124      # might change due to 4GDH

# %% components
# gas turbine part
compressor_gtp = compressor('compressor')
combustion_chamber = combustion_chamber('combustion')
gas_turbine = turbine('gas turbine')

fuel_source = source('fuel source')
combustion_air_source = source('ambient air')

rauchgas = sink('Rauchgas')
steam_generator_gas = heat_exchanger('Abhitzekessel')

# steam turbine part
fs_source = source('Frischdampf')
hp_turbine = turbine('Hochdruck Turbine')
splitter_1 = splitter('splitter hp-extraction')

lp_turbine = turbine('low pressure turbine')
merge = merge('Merge vor Kondensator')
condenser_stp = condenser('Kondensator')
pump = pump('Speisewasserpumpe')

# DH Network
dh_source = source('District Heating source')
dh_sink = sink('dh sink')

valve_1 = valve('valve 1')
dh_heater_2 = heat_exchanger('Dh_heater_2')
valve_2 = valve('valve 2')

dh_heater = condenser('dh heater 1')

# Kuehlwasser
cw_source = source('Kuehlwasser Einlass')
cw_sink = sink('Kuehlwasser Austritt')

# vorläufige ZU Source und Sink
w = source('ZU Dampf Kalt')
z = sink('ZU Dampf Warm')

# Frischdampf-Senke
fs_sink = sink('Frischdampf Senke')

# %% Connections
# Gasturbine
combustion_air_source.compressor_gtp = connection(combustion_air_source, 'out1',
                                                  compressor_gtp, 'in1')
compressor_gtp.combustion_chamber = connection(compressor_gtp, 'out1',
                                                combustion_chamber, 'in1')

fuel_source.combustion_chamber = connection(fuel_source, 'out1',
                                                combustion_chamber, 'in2')

combustion_chamber.gas_turbine = connection(combustion_chamber, 'out1',
                                                gas_turbine, 'in1')
gas_turbine.steam_generator_gas = connection(gas_turbine, 'out1',
                                                  steam_generator_gas, 'in1')

steam_generator_gas.rauchgas = connection(steam_generator_gas, 'out1',
                                              rauchgas, 'in1')

nw.add_conns(combustion_air_source.compressor_gtp, compressor_gtp.combustion_chamber,
              fuel_source.combustion_chamber, combustion_chamber.gas_turbine,
              gas_turbine.steam_generator_gas, steam_generator_gas.rauchgas)

# Dampfkreislauf
fs_source.steam_generator_gas = connection(fs_source, 'out1',
                                                steam_generator_gas, 'in2')
steam_generator_gas.hp_turbine = connection(steam_generator_gas, 'out2',
                                                hp_turbine, 'in1')
hp_turbine.splitter_1 = connection(hp_turbine, 'out1', splitter_1, 'in1')
splitter_1.lp_turbine = connection(splitter_1, 'out1', lp_turbine, 'in1')
lp_turbine.merge = connection(lp_turbine, 'out1', merge, 'in1')
merge.condenser_stp = connection(merge, 'out1', condenser_stp, 'in1')
condenser_stp.pump = connection(condenser_stp, 'out1', pump, 'in1',
                                fluid0={'H2O': 1})
pump.fs_sink = connection(pump, 'out1', fs_sink, 'in1', fluid0={'H2O': 1})

splitter_1.valve_1 = connection(splitter_1, 'out2', valve_1, 'in1',
                                    fluid0={'H2O': 1})
valve_1.dh_heater = connection(valve_1, 'out1', dh_heater, 'in1')
dh_heater.valve_2 = connection(dh_heater, 'out1', valve_2, 'in1')

valve_2.merge = connection(valve_2, 'out1', merge, 'in2')

nw.add_conns(fs_source.steam_generator_gas, steam_generator_gas.hp_turbine,
              hp_turbine.splitter_1, splitter_1.lp_turbine, lp_turbine.merge,
              merge.condenser_stp, condenser_stp.pump, pump.fs_sink, splitter_1.valve_1,
              valve_1.dh_heater, dh_heater.valve_2, valve_2.merge)

# cooling water
cw_source.condenser_stp = connection(cw_source, 'out1', condenser_stp, 'in2')
condenser_stp.cw_sink = connection(condenser_stp, 'out2', cw_sink, 'in1')

nw.add_conns(cw_source.condenser_stp, condenser_stp.cw_sink)

# district heating
dh_source.dh_heater = connection(dh_source, 'out1', dh_heater, 'in2')
dh_heater.dh_sink = connection(dh_heater, 'out2', dh_sink, 'in1')

nw.add_conns(dh_source.dh_heater, dh_heater.dh_sink)

# %% Parameterization Connections
# Connections Gas
combustion_air_source.compressor_gtp.set_attr(T=20, p=1,
                                          fluid={'Ar': 0.0093, 'N2': 0.7808,
                                                  'H2O': 0, 'CH4': 0,
                                                  'CO2': 0.0004, 'O2': 0.2095})

fuel_source.combustion_chamber.set_attr(T=20, h0=885,
                                        fluid={'Ar': 0, 'N2': 0, 'H2O': 0,
                                                'CH4': 1, 'CO2': 0, 'O2': 0})

compressor_gtp.combustion_chamber.set_attr(h0=659.83)
combustion_chamber.gas_turbine.set_attr(T=1500)
gas_turbine.steam_generator_gas.set_attr(p=1)
steam_generator_gas.rauchgas.set_attr(T=150)

# Connections Steam
fs_source.steam_generator_gas.set_attr(T=ref(pump.fs_sink, 1, 0),
                                        fluid={'Ar': 0, 'N2': 0, 'H2O': 1,
                                              'CH4': 0, 'CO2': 0, 'O2': 0})
steam_generator_gas.hp_turbine.set_attr(T=600, p=100, design=['p'])
hp_turbine.splitter_1.set_attr(p=3, design=['p'])
lp_turbine.merge.set_attr(p=0.04)
pump.fs_sink.set_attr(p=ref(fs_source.steam_generator_gas, 1, 0))



# Connections Cooling Water
cw_source.condenser_stp.set_attr(T=20, p=10, fluid={'Ar': 0, 'N2': 0, 'H2O': 1,
                                                'CH4': 0, 'CO2': 0, 'O2': 0})

# Connections District Heating
dh_source.dh_heater.set_attr(p=10, T=t_dh_in,
                              fluid={'Ar': 0, 'N2': 0, 'H2O': 1,
                                    'CH4': 0, 'CO2': 0, 'O2': 0})
dh_heater.dh_sink.set_attr(T=t_dh_out)

# Components
# Gasturbine
compressor_gtp.set_attr(pr=14, eta_s=0.91, design=['pr', 'eta_s'],
                    offdesign=['eta_s_char'])
#combustion_chamber.set_attr(fuel='CH4')
gas_turbine.set_attr(eta_s=0.9, design=['eta_s'],
                      offdesign=['eta_s_char', 'cone'])

steam_generator_gas.set_attr(pr1=1, pr2=1)

# Dampfturbine
hp_turbine.set_attr(eta_s=0.9, design=['eta_s'],
                    offdesign=['eta_s_char', 'cone'])
lp_turbine.set_attr(eta_s=0.9, design=['eta_s'],
                    offdesign=['eta_s_char', 'cone'])
condenser_stp.set_attr(pr1=1, pr2=1, ttd_u=5, design=['ttd_u', 'pr1', 'pr2'],
                    offdesign=['kA', 'zeta1', 'zeta2'])
pump.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

# valve_1.set_attr(pr=1)

# District Heating
dh_heater.set_attr(pr1=0.99, pr2=0.99, ttd_u=5, design=['ttd_u', 'pr1', 'pr2'],
                    offdesign=['kA', 'zeta1', 'zeta2'])


# %% Busses

# characteristic function for generator efficiency
x = np.array([0, 0.2, 0.4, 0.6, 0.8, 1, 1.2])
y = np.array([0, 0.86, 0.9, 0.93, 0.95, 0.96, 0.95])
gen = char_line(x=x, y=y)

gas_turbine_bus = bus('gas_turbine_bus')
gas_turbine_bus.add_comps({'c': compressor_gtp, 'char': gen},
                          {'c': gas_turbine, 'char': gen})

steam_turbine_bus = bus('steam_turbine_bus')
steam_turbine_bus.add_comps({'c': hp_turbine, 'char': gen},
                            {'c': lp_turbine, 'char': gen},
                            {'c': pump, 'char': gen})

heat_bus = bus('heat')
heat_bus.add_comps({'c': dh_heater, 'p': 'Q'})

total_power_bus = bus('total power')
total_power_bus.add_comps({'c': compressor_gtp, 'char': gen},
                          {'c': gas_turbine, 'char': gen},
                          {'c': hp_turbine, 'char': gen},
                          {'c': lp_turbine, 'char': gen},
                          {'c': pump, 'char': gen})

nw.add_busses(gas_turbine_bus, steam_turbine_bus, heat_bus, total_power_bus)


# %% Key Parameter
# Brennstoffmassenstrom für 300MW aus vorheriger Simulation
m_fuel = 11.575780608577949
fuel_source.combustion_chamber.set_attr(m=m_fuel) # ansonsten P_el

Q = -145
dh_heater.set_attr(Q=-20e6)


# %% solving

print('### Design ###')
print()
nw.solve(mode='design')
nw.save('ccet')

P_ges = steam_turbine_bus.P.val + gas_turbine_bus.P.val
Q_dh = heat_bus.P.val
Q_cc = combustion_chamber.ti.val


# # print(steam_turbine_bus + gas_turbine_bus)
# print('Leistung Gasturbine: ' + str(gas_turbine_bus.P.val/1e6) + ' MW')
# print('Leistung Dampfturbine: ' + str(steam_turbine_bus.P.val/1e6) + ' MW')
# print('Gesamtleistung: ' + str(total_power_bus.P.val/1e6) + ' MW')
# a = total_power_bus.P.val/1e6
# print('Leistung der Brennkammer: '+str(combustion_chamber.ti.val/1e6) + ' MW')
# print('Leistung Dampferzeuger: ' + str(steam_generator_gas.Q.val/1e6) + ' MW')
# print('Stromausbeute: '+str(beta(total_power_bus.P.val,
#                                  combustion_chamber.ti.val)))


# print()
# print('### power loss index ###')
# print()
# dh_heater.set_attr(Q=-0.01e6)
# nw.solve(mode='design')
# b = total_power_bus.P.val/1e6
# power_loss_index = 1

# print('Q: ' + str(Q) + ' MW')
# print('P(Q): ' + str(a) + ' MW')
# print('P_wo_DH: ' + str(b) + ' MW')
# print('power loss index: ' + str((b - a)/Q))


# print()
# print('### H_L_FG_share_max ###')
# print()
# flue_loss = ((steam_generator_gas.rauchgas.h.val -
#               combustion_air_source.compressor_gtp.h.val) *
#              steam_generator_gas.rauchgas.m.val)
# print(flue_loss)
# fuel = ((fuel_source.combustion_chamber.h.val -
#         combustion_air_source.compressor_gtp.h.val) *
#         fuel_source.combustion_chamber.m.val)
# print(fuel)
# print(fuel/flue_loss)
# print('-> H_L_FG_share_max ist in dem Solph-Modell auf  0.19 gesetzt worden,'
#       'um eine maximale Wärmeauskopplung von 160 MW zu realisieren')
# print()

# print('Offdesign')
# print('### P_max_woDH / Eta_el_max_woDH ###')
# print()
# load = 1.2 * m_fuel
# fuel_source.combustion_chamber.set_attr(m=load)
# dh_heater.set_attr(Q=0.01 * -145e6)
# nw.solve(mode='offdesign', init_path='GuD', design_path='GuD')
# print('Maximale Brennkammerleistung: ' + str(combustion_chamber.ti.val/1e6) + ' MW')
# print('P_max_woDH: ' + str(total_power_bus.P.val/1e6) + ' MW')
# print('Eta_el_max_woDH: '+str(beta(total_power_bus.P.val,
#                                    combustion_chamber.ti.val)))

# print()
# print('### P_min_woDH / Eta_el_min_woDH ###')
# print()
# load = 0.5 * m_fuel
# fuel_source.combustion_chamber.set_attr(m=load)
# dh_heater.set_attr(Q=0.01 * -145e6)
# nw.solve(mode='offdesign', init_path='GuD', design_path='GuD')
# print('P_min_woDH: ' + str(total_power_bus.P.val/1e6) + ' MW')
# print('Eta_el_min_woDH: '+str(beta(total_power_bus.P.val,
#                                    combustion_chamber.ti.val)))
