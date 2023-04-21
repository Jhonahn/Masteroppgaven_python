# -*- coding: utf-8 -*-
"""
Created on Wed Feb  8 10:04:27 2023

@author: johan
"""

# import matplotlib.pyplot as plt
import pyarrow.feather as feather
import pv_modelling
import altair as alt
import numpy as np
import pandas as pd

from pvlib.location import Location

# Relative paths to datasets and figures
data_path = 'soras/feather'
# figure_path = 'figurer_soras_hele'
figure_path = 'figurer_soras'

# Import data
data = feather.read_feather(f'{data_path}/soras_data')
data_hour = feather.read_feather(f'{data_path}/soras_data_hour')
data_maxhour = feather.read_feather(f'{data_path}/soras_data_maxhour')
data_month = feather.read_feather(f'{data_path}/soras_data_month')

# Define system parameters
system_parameters_soras = pv_modelling.SystemParameters(name = 'Søråsjordet', 
                                                        strings_per_inverter = 1, 
                                                        modules_per_string = 12, 
                                                        surface_tilt = 42, 
                                                        surface_azimuth = 182,
                                                        # date_start = '2018-07-01 08:00', # Datasett start
                                                        date_start = '2020-02-16 00:00', # Strenginverter start
                                                        date_end = '2022-12-31 23:59')

# Implement dataset boundries
data = data.loc[system_parameters_soras.date_start:system_parameters_soras.date_end]
data_hour = data_hour.loc[system_parameters_soras.date_start:system_parameters_soras.date_end]
data_maxhour = data_maxhour.loc[system_parameters_soras.date_start:system_parameters_soras.date_end]
data_month = data_month.loc[system_parameters_soras.date_start:system_parameters_soras.date_end]

# Define system location
location_soras = Location(name='Søråsjordet', 
                          latitude=59.660213840018486, 
                          longitude=10.783026609535117, 
                          tz='Europe/Oslo', 
                          altitude=95)

# Define module parameters
modules_soras = pv_modelling.SystemModule(name = 'SweModule Inceptio 250F',
                                          celltype = 'multiSi',
                                          pdc0 = 250,
                                          v_mp = 30.6,             
                                          i_mp = 8.20,              
                                          v_oc = 37.7,                  
                                          i_sc = 8.8,                   
                                          alpha_sc = 0.0007,     
                                          beta_voc = -0.0032,   
                                          gamma_pdc = -0.382,          
                                          cells_in_series = 3*20)              

# Define inverter parameters
inverter_soras = pv_modelling.SystemInverter(name = 'Fronius Primo 3.0',
                                              pdc0 = 3000,             
                                              eta_inv_nom = 0.961)

# Model systems
model_hour, model_maxhour, model_month \
    = pv_modelling.pv_model(system_parameters_soras, 
                            modules_soras, 
                            inverter_soras, 
                            data, 
                            location_soras)

clear_sky, clear_sky_maxhour, clear_sky_month \
    = pv_modelling.get_clear_sky_parameters(system_parameters_soras, 
                                            location_soras)


# Find RMSE values of modelled and measured power data
RMSE_values_power = pv_modelling.model_RMSE(model_hour['ac_power'], 
                                      model_hour['ac_power'], 
                                      inverter_soras.pdc0,
                                      inverter_soras.pdc0,
                                      data_hour['ac_power_1'],
                                      data_hour['ac_power_2'])

# Calculate difference from model
data_maxhour['difference_1'] = model_maxhour['ac_power'] - data_maxhour['ac_power_1']
data_maxhour['difference_2'] = model_maxhour['ac_power'] - data_maxhour['ac_power_2']

# Use plotting function to make plots
pv_modelling.plot_results(figure_path, 
                          model_maxhour, 
                          model_maxhour, 
                          clear_sky_maxhour, 
                          data_maxhour)

#%% Plots specific to Sørås

# All measured powers
graph = alt.Chart(data_maxhour.rename(columns={'ac_power_1':'Tilsynelatende', 
                                                       'active_power_1':'Aktiv', 
                                                       'reactive_power_1':'Reaktiv'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Effekt (W)'),
    color=alt.Color('key:N', title='Effekt'),
    ).transform_fold(['Tilsynelatende', 'Aktiv', 'Reaktiv']
                     ).properties(title='Alle målte effekter ved nordre anlegg på Søråsjordet', width=800, height=300)
                                                           
graph.save(f'{figure_path}/alle_effekter_nordre.html')


graph = alt.Chart(data_maxhour.rename(columns={'ac_power_2':'Tilsynelatende', 
                                                       'active_power_2':'Aktiv', 
                                                       'reactive_power_2':'Reaktiv'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Effekt (W)'),
    color=alt.Color('key:N', title='Effekt'),
    ).transform_fold(['Tilsynelatende', 'Aktiv', 'Reaktiv']
                     ).properties(title='Alle målte effekter ved søndre anlegg på Søråsjordet', width=800, height=300)
                                                           
graph.save(f'{figure_path}/alle_effekter_sondre.html')

#%% Analyse temperature data

# Define interval selection
interval = alt.selection_interval(encodings=['x'])

# Plot measured temperatures
base = alt.Chart(data_maxhour.rename(columns={'temp_module_1':'Nordre', 
                                                     'temp_module_2':'Søndre',
                                                     'temp_air':'Lufttemperatur'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Temperatur (grader Celsius)'),
    color=alt.Color('key:N', title='Anlegg'),
    tooltip=['time:T','value:Q'],
    ).transform_fold(['Nordre', 'Søndre', 'Lufttemperatur']
                     )
                                                           
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Målte temperaturer på Søråsjordet', width=800, height=300)
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/temperaturer.html')

# Calculate model and measurement difference
data_maxhour['temp_diff_1'] = data_maxhour['temp_module_1'] - model_maxhour['temp_cell']
data_maxhour['temp_diff_2'] = data_maxhour['temp_module_2'] - model_maxhour['temp_cell']

# Find RMSE values of modelled and measured temperature data
RMSE_values_temperature = pv_modelling.model_RMSE(model_hour['temp_cell'], 
                                                  model_hour['temp_cell'], 
                                                  inverter_soras.pdc0,
                                                  inverter_soras.pdc0,
                                                  data_hour['temp_module_1'],
                                                  data_hour['temp_module_2'])

# Find RMSE values without faulty measurements
model_hour_cut = pd.concat([model_hour.loc['2020-03-19':'2021-05-19'], model_hour.loc['2021-08-25':]])
data_hour_cut = pd.concat([data_hour.loc['2020-03-19':'2021-05-19'], data_hour.loc['2021-08-25':]])

RMSE_values_temperature_cut = pv_modelling.model_RMSE(model_hour_cut['temp_cell'], 
                                                      model_hour_cut['temp_cell'], 
                                                      inverter_soras.pdc0,
                                                      inverter_soras.pdc0,
                                                      data_hour_cut['temp_module_1'],
                                                      data_hour_cut['temp_module_2'])

# Plot difference curves
base = alt.Chart(data_maxhour.rename(columns={'temp_diff_1':'Nordre', 
                                                     'temp_diff_2':'Søndre',
                                                     'temp_air':'Lufttemperatur'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Temperatur (grader Celsius)'),
    color=alt.Color('key:N', title='Anlegg'),
    tooltip=['time:T','value:Q'],
    ).transform_fold(['Nordre', 'Søndre']
                     )
                                                           
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Forskjell mellom målte og modellerte temperaturer på Søråsjordet', width=800, height=300)
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/temperaturer_forskjell.html')

# Plot difference 2020--2021
base = alt.Chart(data_maxhour.loc['2020-03-19':'2021-05-19'].rename(columns={'temp_diff_1':'Nordre', 
                                                     'temp_diff_2':'Søndre',
                                                     'temp_air':'Lufttemperatur'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Temperatur (grader Celsius)'),
    color=alt.Color('key:N', title='Anlegg'),
    tooltip=['time:T','value:Q'],
    ).transform_fold(['Nordre', 'Søndre']
                     )
                                                           
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Forskjell mellom målte og modellerte temperaturer på Søråsjordet', width=800, height=300)
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/temperaturer_forskjell_2020_2021.html')

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

# Sum values of storm magnitude
amount_severe_gale = 0 # Liten storm
amount_storm = 0  # Full storm
amount_violent_storm = 0 # Sterk storm
amount_hurricane = 0 # Orkan

for wind_speed in data_maxhour['wind_speed']:
    if 20.8 < wind_speed < 24.4:
        amount_severe_gale += 1 
    elif 24.5 < wind_speed < 28.4:
        amount_storm += 1
    elif 28.5 < wind_speed < 32.6:
        amount_violent_storm += 1
    elif wind_speed > 32.7:
        amount_hurricane += 1

amount_strong_wind = amount_severe_gale + amount_storm + amount_violent_storm + amount_hurricane