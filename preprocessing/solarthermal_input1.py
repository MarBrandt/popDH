# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 14:01:44 2020

@author: Markus Brandt
"""

import os.path as path

import pandas as pd
import numpy as np



# %% read data
# ambient temperature
dirpath = path.abspath(path.join(__file__, "../.."))
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

# radiation
readpath = path.join(dirpath, 'Eingangsdaten', 'radiation_on_tilted_plane.csv')
total_radiation = np.array(pd.read_csv(readpath, sep=";"))

# %% calculate solar collector efficiency

eta_opt = collector_data.iloc[0][1]
alpha1 = collector_data.iloc[0][2]
alpha2 = collector_data.iloc[0][3]

col_temp = (feed_temp - return_temp) / 2

eta1 = eta_opt - alpha1 * (col_temp - amb_temp)/total_radiation - alpha2 * (col_temp - amb_temp)**2/total_radiation

# i=0
# for x in eta:
#     if x == '-inf':
#         eta[i] = 0
#     elif x<0:
#         eta[i] = 0
#     i += 1
    
# # %% calculate solar thermal heat per m² -> MWh / m²

# Q_solar = eta * total_radiation / 1e3