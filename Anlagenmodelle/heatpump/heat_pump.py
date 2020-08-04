# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 09:32:11 2019

@author: Markus Brandt
"""

from tespy import nwk, con, cmp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

T_amb = 9.188
t_dh_in = 50
t_dh_out = 91.12

fluids = ['water', 'air', 'NH3']
nw = nwk.network(fluids=fluids, T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s')

# %% Components
# main cycle
hp_source = cmp.source('heat pump cycle opener')
hp_sink = cmp.sink('heat pump cycle close')

superheater = cmp.heat_exchanger('superheater')
compressor_1 = cmp.compressor('Verdichter 1')
cooler = cmp.heat_exchanger('Zwischenkühler')
compressor_2 = cmp.compressor('Verdichter 2')
condenser = cmp.condenser('Kondensator')
valve = cmp.valve('Drossel')
evaporator = cmp.heat_exchanger('Verdampfer')

# Zwischenkühlung
ambient_source_1 = cmp.source('ambient source 1')
fan_1 = cmp.compressor('fan_1')
ambient_sink_1 = cmp.sink('ambient sink 1')

# District Heating
dh_source = cmp.source('Return Flow')
dh_sink = cmp.sink('Feed Flow')

# Verdampfung
ambient_source_2 = cmp.source('ambient source verdampfung')
fan_2 = cmp.compressor('fan_2')
ambient_sink_2 = cmp.sink('ambient sink verdampfung')


# %% Connections
# main cycle
hp_source.superheater = con.connection(hp_source, 'out1', superheater, 'in2')
superheater.compressor_1 = con.connection(superheater, 'out2', compressor_1, 'in1')
compressor_1.cooler = con.connection(compressor_1, 'out1', cooler, 'in1')
cooler.compressor_2 = con.connection(cooler, 'out1', compressor_2, 'in1')
compressor_2.condenser = con.connection(compressor_2, 'out1', condenser, 'in1')
condenser.superheater = con.connection(condenser, 'out1', superheater, 'in1')
superheater.valve = con.connection(superheater, 'out1', valve, 'in1')
valve.evaporator = con.connection(valve, 'out1', evaporator, 'in2')
evaporator.hp_sink = con.connection(evaporator, 'out2', hp_sink, 'in1')
nw.add_conns(hp_source.superheater, superheater.compressor_1, compressor_1.cooler, cooler.compressor_2,
             compressor_2.condenser, condenser.superheater, superheater.valve, valve.evaporator, evaporator.hp_sink)

# Zwischenkühlung
ambient_source_1.fan_1 = con.connection(ambient_source_1, 'out1', fan_1, 'in1')
fan_1.cooler = con.connection(fan_1, 'out1', cooler, 'in2')
cooler.ambient_sink_1 = con.connection(cooler, 'out2', ambient_sink_1, 'in1')
nw.add_conns(ambient_source_1.fan_1, fan_1.cooler, cooler.ambient_sink_1)

# District Heating
dh_source.condenser = con.connection(dh_source, 'out1', condenser, 'in2')
condenser.dh_sink = con.connection(condenser, 'out2', dh_sink, 'in1')
nw.add_conns(dh_source.condenser, condenser.dh_sink)

# Verdampfung
ambient_source_2.fan_2 = con.connection(ambient_source_2, 'out1', fan_2, 'in1')
fan_2.evaporator = con.connection(fan_2, 'out1', evaporator, 'in1')
evaporator.ambient_sink_2 = con.connection(evaporator, 'out1', ambient_sink_2, 'in1')
nw.add_conns(ambient_source_2.fan_2, fan_2.evaporator, evaporator.ambient_sink_2)

# %% Busses
power_bus = con.bus('power')
power_bus.add_comps({'c': compressor_1, 'p': 'P'},
                    {'c': compressor_2, 'p': 'P'},
                    {'c': fan_1, 'p': 'P'})

heat_bus = con.bus('heat')
heat_bus.add_comps({'c': condenser, 'p': 'P'})

nw.add_busses(power_bus, heat_bus)

# %% Parametrisation Components
# Main Cycle
compressor_1.set_attr(eta_s=0.8, pr=3.3, design=['eta_s'], offdesign=['eta_s_char'])
cooler.set_attr(pr1=0.98, pr2=0.98, design=['pr1', 'pr2', 'kA'], offdesign=['zeta1', 'zeta2', 'kA_char1'])
compressor_2.set_attr(eta_s=0.8, pr=3.3, design=['eta_s'], offdesign=['eta_s_char'])
condenser.set_attr(pr1=0.98, pr2=0.98, design=['pr1', 'pr2', 'kA'], offdesign=['zeta1', 'zeta2', 'kA_char1'])

superheater.set_attr(pr1=0.98, pr2=0.98, design=['pr1', 'pr2'], offdesign=['zeta1', 'zeta2'])

# Zwischenkühlung
fan_1.set_attr(eta_s=0.6, design=['eta_s'], offdesign=['eta_s_char'])

# Verdampfung
evaporator.set_attr(pr1=0.98 , design=['pr1'], offdesign=['zeta1'])
fan_2.set_attr(eta_s=0.6, design=['eta_s'], offdesign=['eta_s_char'])

# %% Parametrisation Connections
# Main cycle
hp_source.superheater.set_attr(p=6, x=1, fluid={'water': 0, 'NH3': 1, 'air': 0})
superheater.compressor_1.set_attr(p0=6, T=16)
cooler.compressor_2.set_attr(T=60)
valve.evaporator.set_attr(p=con.ref(hp_source.superheater, 1, 0))
evaporator.hp_sink.set_attr(p=con.ref(hp_source.superheater, 1, 0), x=1)

#superheater.hp_sink.set_attr(p=100)

# Zwischenkühlung
ambient_source_1.fan_1.set_attr(T=T_amb, p=1, fluid={'air': 1, 'water': 0, 'NH3': 0})
cooler.ambient_sink_1.set_attr(p=1, T=30)

# District Heating
dh_source.condenser.set_attr(T=t_dh_in, p=10, fluid={'water': 1, 'air': 0, 'NH3': 0})
condenser.dh_sink.set_attr(T=t_dh_out)

# Verdampfung
ambient_source_2.fan_2.set_attr(T=T_amb, p=1, fluid={'air': 1, 'water': 0, 'NH3': 0})
evaporator.ambient_sink_2.set_attr(T=10, p=1)

# Keyparameter
Q = -25e6
condenser.set_attr(Q=Q)

# %% Solving

# design
mode = 'design'
nw.set_printoptions(print_level='none')
nw.solve(mode=mode)
nw.save('heat_pump')
cop = abs(heat_bus.P.val)/power_bus.P.val
cop_c = (273.15 + t_dh_out)/(t_dh_out - T_amb)
print('### Ergebnisse im Nennbetrieb: ###')
print("Leistungszahl: " + str(round(cop,2)))
print("Carnot-Leistungszahl: " + str(round(cop_c,2)))
print("Gütegrad: " + str(round(cop/cop_c,2)))

# offdesign

#p_load = 0.4
#eta_g = []
#p_l = []
#cop_hp = []
#while p_load <= 1.05:
#    Q = -25e6 * p_load
#    p_l += [p_load]
#    condenser.set_attr(Q=Q)
#    nw.solve(mode='offdesign', init_path='heat_pump', design_path='heat_pump')
#    
#    cop = abs(heat_bus.P.val)/power_bus.P.val
#    cop_hp += [cop]
#    cop_c = (273.15 + t_dh_out)/(t_dh_out - T_amb)
#    eta_g += [cop/cop_c]
#    print("Last: " + str(round(p_load * 100)) + "%" + "  ->  " "Gütegrad: " + str(round(cop/cop_c,2)))
#        
#    p_load = p_load + 0.05
#print(eta_g)
#print(p_l)
#
#plt.plot(p_l, eta_g)
#plt.xlabel('Heatload')
#plt.ylabel("Leistungszahl der Wärmepumpe")
#
#plt.show

'''
Bei der Erstellung des oberen Verhaltens ist als Vereinfachung davon ausgegangen, 
dass die Vorlauftemperatur der Wärmepumpe immer gleich bleibt.
'''
power = []
heat = []
cop = []
load = []
eta_g = []
eta_g_lin = [0.46568,0.4698,0.47392,0.47804,0.48216,0.48628,0.4904]

T_range = [91.12]
Q_range = np.array([10e6, 12.5e6, 15e6, 17.5e6, 20e6, 22.5e6, 25e6])
df = pd.DataFrame(columns=Q_range / -condenser.Q.val)

for T in T_range:
    condenser.dh_sink.set_attr(T=T)


    for Q in Q_range:
        condenser.set_attr(Q=-Q)
        try:
            nw.solve('offdesign',
                     init_path='OD_' + str(Q/1e6),
                     design_path='heat_pump')
        except FileNotFoundError:
            nw.solve('offdesign', init_path='heat_pump',
                     design_path='heat_pump')
            
        cop_c = (273.15 + T) / (T - T_amb)

        if nw.lin_dep:
            eta_g += [np.nan]

        else:
            nw.save('OD_' + str(Q/1e6))
            eta_g += [abs(condenser.Q.val) / (power_bus.P.val)/cop_c]
            power += [power_bus.P.val/1e6]
            heat += [abs(heat_bus.P.val)/1e6]
            cop += [heat_bus.P.val/power_bus.P.val]
            load += [Q/25e6]
            
    df.loc[T] = eta_g
    
data = {'Gütegrad (real)': eta_g, 'Wärmestrom': heat, 'Gütegrad (linear)': eta_g_lin, 'Leistung': power, 'Auslastung': load}
df2 = pd.DataFrame(data, columns=['Gütegrad (real)','Gütegrad (linear)'], index=data['Auslastung'])
print('### Elektrische Leistung und Wärmestrom ###')
print(df2)
print()
print('### Gütegrad über Auslastung bei 91.12°C Vorlauftermperatur ###')
print(df)
df.to_csv('eta_g.csv')
#
print('Abbildung')
#
f, ax = plt.subplots()
ax = df2.plot(kind='line', grid=False, legend=True, colormap='Spectral')
ax.set_xlabel('relative Auslastung $x$')
ax.set_ylabel('Gütegrad')
ax.legend(loc="lower right")
plt.show()

