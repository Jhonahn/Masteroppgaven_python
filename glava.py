# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 16:52:16 2023

@author: johan
"""

import pyarrow.feather as feather
import pv_modelling
import altair as alt
import numpy as np
import pandas as pd

from pvlib.location import Location

# Relative paths to figures
figure_path = 'figures/glava'

# Import data
data_hour = feather.read_feather('data/glava_data_hour')
data_maxhour = feather.read_feather('data/glava_data_maxhour')

# Define system parameters
system_parameters_SMA = pv_modelling.SystemParameters(name = 'Glava Energy Center SMA', 
                                                      strings_per_inverter = 2, 
                                                      modules_per_string = 10, 
                                                      surface_tilt = 40, 
                                                      surface_azimuth = 180,
                                                      date_start = '2019-01-01 00:00',
                                                      date_end = '2022-12-31 23:00')

system_parameters_Eltek = pv_modelling.SystemParameters(name = 'Glava Energy Center Eltek', 
                                                        strings_per_inverter = 4, 
                                                        modules_per_string = 20, # Different modules per string
                                                        surface_tilt = 40, 
                                                        surface_azimuth = 180,
                                                        date_start = '2019-01-01 00:00',
                                                        date_end = '2022-12-31 23:00')

system_parameters_ABB = pv_modelling.SystemParameters(name = 'Glava Energy Center ABB', 
                                                      strings_per_inverter = 20, 
                                                      modules_per_string = 20, 
                                                      surface_tilt = 40, 
                                                      surface_azimuth = 180,
                                                      date_start = '2019-01-01 00:00',
                                                      date_end = '2022-12-31 23:00')

# Define system location
location_glava = Location(name='Glava Energy Center',
                          latitude=59.53130566557184, 
                          longitude=12.620588050814765, 
                          tz='Europe/Stockholm', 
                          altitude=95)

# Define module parameters
modules_SMA = pv_modelling.SystemModule(name = 'REC Solar SMC210 220 W',
                                             celltype = 'multiSi',
                                             pdc0 = 220,             
                                             v_mp = 28.33,               
                                             i_mp = 7.71,             
                                             v_oc = 36.51,                 
                                             i_sc = 8.32,          
                                             alpha_sc = 0.0004 / 8.32,          
                                             beta_voc = -0.104 / 36.51,          
                                             gamma_pdc = -0.43,          
                                             cells_in_series = 3*20)            

modules_ABB = pv_modelling.SystemModule(name = 'REC Solar REC225PE',
                                             celltype = 'multiSi',
                                             pdc0 = 225,           
                                             v_mp = 28.9,              
                                             i_mp = 7.79,              
                                             v_oc = 36.2,                
                                             i_sc = 8.34,         
                                             alpha_sc = 0.00074,      
                                             beta_voc = -0.0033,   
                                             gamma_pdc = -0.43,          
                                             cells_in_series = 3*20)

# Define inverter parameters
inverter_SMA = pv_modelling.SystemInverter(name = 'SMA Sunny Boy 4000TL',
                                             pdc0 = 4200,               
                                             eta_inv_nom = 0.964)  

inverter_ABB = pv_modelling.SystemInverter(name = 'ABB PVS800-57-0100kW-A',
                                             pdc0 = 100_000,               
                                             eta_inv_nom = 0.975)  

# Model systems
model_hour_SMA, model_maxhour_SMA, model_month_SMA \
    = pv_modelling.pv_model(system_parameters_SMA, 
                            modules_SMA, 
                            inverter_SMA, 
                            data_hour, 
                            location_glava)

model_hour_ABB, model_maxhour_ABB, model_month_ABB \
    = pv_modelling.pv_model(system_parameters_ABB, 
                            modules_ABB, 
                            inverter_ABB, 
                            data_hour, 
                            location_glava)


clear_sky, clear_sky_maxhour, clear_sky_month \
    = pv_modelling.get_clear_sky_parameters(system_parameters_ABB, 
                                            location_glava)

# Find RMSE values of modelled and measured data
RMSE_values = pv_modelling.model_RMSE(model_hour_SMA['ac_power'], 
                                      model_hour_ABB['ac_power'],
                                      inverter_SMA.pdc0,
                                      inverter_ABB.pdc0,
                                      data_hour['ac_power_1'],
                                      data_hour['ac_power_2'])

# Calculate difference from model
data_maxhour['difference_1'] = model_maxhour_SMA['ac_power'] - data_maxhour['ac_power_1']
data_maxhour['difference_2'] = model_maxhour_ABB['ac_power'] - data_maxhour['ac_power_2']

# Use plotting function to make plots
pv_modelling.plot_results(figure_path, 
                          model_maxhour_SMA, 
                          model_maxhour_ABB, 
                          clear_sky_maxhour, 
                          data_maxhour)

#%% Analyse wind data

# Define interval selection
interval = alt.selection_interval(encodings=['x'])

# Plot measured wind speeds
base = alt.Chart(data_maxhour.rename(columns={'wind_speed':'Vindhastighet'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Vindhastighet (m/s)'),
    # color=alt.Color('key:N', title='Anlegg'),
    tooltip=['time:T','value:Q'],
    ).transform_fold(['Vindhastighet']
                     )
                                                           
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Målte vindhastigheter', width=800, height=300)
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/vindhastigheter.html')