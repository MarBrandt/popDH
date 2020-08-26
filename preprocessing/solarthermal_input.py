# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 10:02:48 2020

@author: Markus Brandt
Calculate Solarthermal input
"""

import os.path as path

import pandas as pd
import numpy as np

from ratipl import calculate_radiation


# %% read data
# radiation 2012
dirpath = path.abspath(path.join(__file__, "../.."))
readpath = path.join(dirpath, 'Eingangsdaten', 'solar_weather_data_2012.csv')
weather_data = pd.read_csv(readpath, sep=",")
e_global = weather_data['DEF0_radiation_diffuse_horizontal'] + weather_data['DEF0_radiation_direct_horizontal']
weather_data['utc_timestamp'] = pd.to_datetime(weather_data['utc_timestamp'])

# ambient temperature
readpath = path.join(dirpath, 'Eingangsdaten', 'ninja_weather_54.7986_9.4327_uncorrected2019.csv')
amb_data = pd.read_csv(readpath, sep=",")
amb_temp = np.array(amb_data['temperature'])

# feed and return flow temperature
readpath = path.join(dirpath, 'Eingangsdaten', 'swfl_data.csv')
swfl_data = pd.read_csv(readpath, sep=";")
feed_temp = np.array(swfl_data['feed flow temperature'])
return_temp = np.array(swfl_data['average return flow'])

# collector data
readpath = path.join(dirpath, 'Eingangsdaten', 'collector_data.csv')
collector_data = pd.read_csv(readpath, sep=",")


# %% determine the radiation on tilted plane 
latitude = 54.7986
longitude = 9.4327
inclination = 37
south = 0
albedo = 0.2

total_radiation = []
radiation = calculate_radiation(phi=latitude, lam=longitude, gamma_e=inclination,
                                alpha_e=south, albedo=albedo,
                                datetime=weather_data['utc_timestamp'].values,
                                e_dir_hor=weather_data['DEF0_radiation_direct_horizontal'].values,
                                e_diff_hor=weather_data['DEF0_radiation_diffuse_horizontal'].values,
                                e_g_hor=e_global.values
                                )
total_radiation = radiation["global"]           # value in kWh/m²

print(max(total_radiation))

# %% calculate solar collector efficiency

eta_opt = collector_data.iloc[0][1]
alpha1 = collector_data.iloc[0][2]
alpha2 = collector_data.iloc[0][3]

col_temp = (feed_temp - return_temp) / 2

eta = eta_opt - alpha1 * (col_temp - amb_temp)/total_radiation - alpha2 * (col_temp - amb_temp)**2/total_radiation

i=0
for x in eta:
    if x == '-inf':
        eta[i] = 0
    elif x<0:
        eta[i] = 0
    i += 1
    
# %% calculate solar thermal heat per m² -> MWh / m²

q_solar = eta * total_radiation / 1e3

dirpath = path.abspath(path.join(__file__, "../.."))
writepath = path.join(dirpath, 'Eingangsdaten', 'solarthermal_input.csv')
q_solar.to_csv(writepath, sep=';', na_rep='#N/A', index=False)