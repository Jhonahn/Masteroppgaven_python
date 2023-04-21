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
figure_path = 'figures/dkasc'

# Import data
data_hour = feather.read_feather('data/dkasc_data_hour')
data_maxhour = feather.read_feather('data/dkasc_data_maxhour')

# Define system parameters
system_parameters_dkasc = pv_modelling.SystemParameters(name = 'DKASC', 
                                                        strings_per_inverter = 1, 
                                                        modules_per_string = 22, 
                                                        surface_tilt = -20, 
                                                        surface_azimuth = 0,
                                                        date_start = '2016-07-03 00:00',
                                                        date_end = '2022-12-31 23:00')

# Define system location
location_dkasc = Location(name='DKASC',
                          latitude=-23.762696775405107, 
                          longitude=133.8765594850012, 
                          tz='Australia/Darwin', 
                          altitude=95)

# Define module parameters
modules_dkasc_24 = pv_modelling.SystemModule(name = 'Qcells Q.PLUS BFR-G4.1 275',
                                             celltype = 'multiSi',
                                             pdc0 = 275,           
                                             v_mp = 31.36,              
                                             i_mp = 8.77,              
                                             v_oc = 38.72,                
                                             i_sc = 9.41,         
                                             alpha_sc = 0.0004,      
                                             beta_voc = -0.0029,   
                                             gamma_pdc = -0.40,          
                                             cells_in_series = 6*10)              

modules_dkasc_25 = pv_modelling.SystemModule(name = 'Hanwha Solar HSL 60S',
                                             celltype = 'multiSi',
                                             pdc0 = 250,             
                                             v_mp = 30.5,               
                                             i_mp = 8.20,             
                                             v_oc = 37.6,                 
                                             i_sc = 8.72,          
                                             alpha_sc = 0.00055,          
                                             beta_voc = -0.0031,          
                                             gamma_pdc = -0.41,          
                                             cells_in_series = 6*10)            


# Define inverter parameters
inverter_dkasc = pv_modelling.SystemInverter(name = 'SMA SMC 6000A',
                                             pdc0 = 6300,               
                                             eta_inv_nom = 0.953)  

# Model systems
model_hour_24, model_maxhour_24, model_month_24 \
    = pv_modelling.pv_model(system_parameters_dkasc, 
                            modules_dkasc_24, 
                            inverter_dkasc, 
                            data_hour, 
                            location_dkasc)

model_hour_25, model_maxhour_25, model_month_25 \
    = pv_modelling.pv_model(system_parameters_dkasc, 
                            modules_dkasc_25, 
                            inverter_dkasc, 
                            data_hour, 
                            location_dkasc)

clear_sky, clear_sky_maxhour, clear_sky_month \
    = pv_modelling.get_clear_sky_parameters(system_parameters_dkasc, 
                                            location_dkasc)

# Find RMSE values of modelled and measured data
RMSE_values = pv_modelling.model_RMSE(model_hour_24['ac_power'], 
                                      model_hour_25['ac_power'], 
                                      inverter_dkasc.pdc0,
                                      inverter_dkasc.pdc0,
                                      data_hour['ac_power_1'],
                                      data_hour['ac_power_2'])

# Calculate difference from model
data_maxhour['difference_1'] = model_maxhour_24['ac_power'] - data_maxhour['ac_power_1']
data_maxhour['difference_2'] = model_maxhour_25['ac_power'] - data_maxhour['ac_power_2']

# Use plotting function to make plots
pv_modelling.plot_results(figure_path, 
                          model_maxhour_24, 
                          model_maxhour_25, 
                          clear_sky_maxhour, 
                          data_maxhour)

#%% Analyse wind data

# Define interval selection
interval = alt.selection_interval(encodings=['x'])

# Plot PVGIS wind speeds
base = alt.Chart(data_maxhour.rename(columns={'wind_speed':'Vindhastighet'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Vindhastighet (m/s)'),
    # color=alt.Color('key:N', title='Anlegg'),
    tooltip=['time:T','value:Q'],
    ).transform_fold(['Vindhastighet']
                     )
                                                           
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Vindhastigheter fra PVGIS', width=800, height=300)
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/vindhastigheter.html')

# Plot measured wind speeds
base = alt.Chart(data_maxhour.rename(columns={'wind_speed_faulty':'Vindhastighet'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Vindhastighet (m/s)'),
    # color=alt.Color('key:N', title='Anlegg'),
    tooltip=['time:T','value:Q'],
    ).transform_fold(['Vindhastighet']
                     )
                                                           
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Målte vindhastigheter', width=800, height=300)
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/vindhastigheter_originale.html')