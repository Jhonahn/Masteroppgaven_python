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

# Relative paths to figures
# figure_path = 'figures/soras_hele'
figure_path = 'figures/soras'

# Import data
data = feather.read_feather('soras/feather/soras_data')
data_hour = feather.read_feather('data/soras_data_hour')
data_maxhour = feather.read_feather('data/soras_data_maxhour')

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
data_hour = data_hour.loc[system_parameters_soras.date_start:system_parameters_soras.date_end]
data_maxhour = data_maxhour.loc[system_parameters_soras.date_start:system_parameters_soras.date_end]

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
                                              pdc0 = 4500,             
                                              eta_inv_nom = 0.961)

# For checking uncertainties
# data_hour['G_tc'] = data_hour['G_tc'] * 1.10 # Measured irradiance up 
# data_maxhour['G_tc'] = data_maxhour['G_tc'] * 1.10

# data_hour['G_tc'] = data_hour['G_tc'] * 0.90 # Measured irradiance down
# data_maxhour['G_tc'] = data_maxhour['G_tc'] * 0.90

# data_hour['wind_speed'] = data_hour['wind_speed'] * 1.015 # Wind speed up
# data_maxhour['wind_speed'] = data_maxhour['wind_speed'] * 1.015

# data_hour['wind_speed'] = data_hour['wind_speed'] * 0.985 # Wind speed down
# data_maxhour['wind_speed'] = data_maxhour['wind_speed'] * 0.985

# data_hour['temp_air'] = data_hour['temp_air'] + 0.1 # Air temperature up
# data_maxhour['temp_air'] = data_maxhour['temp_air'] + 0.1

# data_hour['temp_air'] = data_hour['temp_air'] - 0.1 # Air temperature down
# data_maxhour['temp_air'] = data_maxhour['temp_air'] - 0.1

# Model systems
model_hour, model_maxhour, model_month \
    = pv_modelling.pv_model(system_parameters_soras, 
                            modules_soras, 
                            inverter_soras, 
                            data_hour, 
                            location_soras)

clear_sky, clear_sky_maxhour, clear_sky_month \
    = pv_modelling.get_clear_sky_parameters(system_parameters_soras, 
                                            location_soras)


# Find RMSE values of modelled and measured power data
RMSE_values_power = pv_modelling.normalized_RMSE_values(model_hour['ac_power'], 
                                                        model_hour['ac_power'], 
                                                        3000,
                                                        3000,
                                                        data_hour['ac_power_1'],
                                                        data_hour['ac_power_2'])

RMSE_values_active_power = pv_modelling.normalized_RMSE_values(model_hour['ac_power'], 
                                                               model_hour['ac_power'],
                                                               3000,
                                                               3000,
                                                               -data_hour['active_power_1'],
                                                               -data_hour['active_power_2'])

# Calculate difference from model
data_hour['difference_1'] = model_hour['ac_power'] - data_hour['ac_power_1']
data_hour['difference_2'] = model_hour['ac_power'] - data_hour['ac_power_2']

data_maxhour['difference_1'] = data_hour['difference_1'].resample('d').mean()
data_maxhour['difference_2'] = data_hour['difference_2'].resample('d').mean()

# Calculate energies produced
energies = pv_modelling.pv_energy(model_hour['ac_power'], 
                                  model_hour['ac_power'], 
                                  data_hour['ac_power_1'], 
                                  data_hour['ac_power_2'])

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


graph = alt.Chart(data_hour.rename(columns={'ac_power_2':'Tilsynelatende', 
                                               'active_power_2':'Aktiv', 
                                               'reactive_power_2':'Reaktiv'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Effekt (W)'),
    color=alt.Color('key:N', title='Effekt'),
    ).transform_fold(['Tilsynelatende', 'Aktiv', 'Reaktiv']
                     ).properties(title='Alle målte effekter ved søndre anlegg på Søråsjordet', width=800, height=300)
                                                           
graph.save(f'{figure_path}/alle_effekter_sondre_timesvedier.html')

#%% Analyse temperature data

# Define interval selection
interval = alt.selection_interval(encodings=['x'])

# Plot measured temperatures
layer_1 = alt.Chart(data_maxhour.rename(columns={'temp_module_1':'Nordre', 
                                                 'temp_module_2':'Søndre',
                                                 'temp_air':'Lufttemperatur'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Temperatur (grader Celsius)'),
    color=alt.Color('key:N', title='Anlegg'),
    tooltip=['time:T','value:Q'],
    ).transform_fold(['Nordre', 'Søndre', 'Lufttemperatur']
                     )

# layer_2 =  alt.Chart(model_maxhour.rename(columns={'temp_cell':'Modellert'})).mark_line().encode(
#     x=alt.X('time:T', title='Tid'),
#     y=alt.Y('value:Q', title='Temperatur (grader Celsius)'),
#     color=alt.Color('key:N', title='Anlegg'),
#     tooltip=['time:T','value:Q'],
#     )

base = layer_1 # + layer_2                                    
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Målte temperaturer på Søråsjordet', width=800, height=300)
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/temperaturer.html')

# Calculate model and measurement difference
data_hour['temp_diff_1'] = data_hour['temp_module_1'] - model_hour['temp_cell']
data_hour['temp_diff_2'] = data_hour['temp_module_2'] - model_hour['temp_cell']

data_maxhour['temp_diff_1'] = data_hour['temp_diff_1'].resample('d').mean()
data_maxhour['temp_diff_2'] = data_hour['temp_diff_2'].resample('d').mean()

# Find RMSE values of modelled and measured temperature data
RMSE_values_temperature = pv_modelling.RMSE_values(model_hour['temp_cell'], 
                                                   model_hour['temp_cell'], 
                                                   data_hour['temp_module_1'],
                                                   data_hour['temp_module_2'])

# Find RMSE values without faulty measurements
model_hour_cut = pd.concat([model_hour.loc['2020-03-20':'2021-05-19'], model_hour.loc['2021-08-26':]])
data_hour_cut = pd.concat([data_hour.loc['2020-03-20':'2021-05-19'], data_hour.loc['2021-08-26':]])

RMSE_values_temperature_cut = pv_modelling.RMSE_values(model_hour_cut['temp_cell'], 
                                                       model_hour_cut['temp_cell'], 
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
base = alt.Chart(data_maxhour.loc['2020-03-20':'2021-05-19'].rename(columns={'temp_diff_1':'Nordre', 
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

# Sum values of storm magnitude
severe_winds = pd.DataFrame({'Severe Gales', 'Storms', 'Violent storms', 'Hurricanes'})
amount_severe_gale = []     # Liten storm
amount_storm = []           # Full storm
amount_violent_storm = []   # Sterk storm
amount_hurricane = []       # Orkan

for wind_speed in data_maxhour['wind_speed']:
    if 20.8 < wind_speed < 24.4:
        amount_severe_gale.append(wind_speed)
    elif 24.5 < wind_speed < 28.4:
        amount_storm.append(wind_speed)
    elif 28.5 < wind_speed < 32.6:
        amount_violent_storm.append(wind_speed)
    elif wind_speed > 32.7:
        amount_hurricane.append(wind_speed)

# Define interval selection
interval = alt.selection_interval(encodings=['x'])

# Plot measured wind speeds lower than 30
base = alt.Chart(data_maxhour.rename(columns={'wind_speed':'Vindhastighet'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Vindhastighet (m/s)'),
    # color=alt.Color('key:N', title='Anlegg'),
    tooltip=['time:T','value:Q'],
    ).transform_fold(['Vindhastighet']
                     ).transform_filter('datum.Vindhastighet < 30')
                                                           
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Målte vindhastigheter', width=800, height=300)
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/vindhastigheter_begrenset.html')  
        
#%% Point diagrams difference and wind

# Wind restricted daily values
base = alt.Chart(data_maxhour.rename(columns={'year': 'År'})).encode(
    x=alt.X('wind_speed:Q', title='Vindhastighet (m/s)'),
    y=alt.Y('value:Q', title='Størrelse på avvik (W)'),
    color='År:N'
    ).transform_fold(['difference_1', 'difference_2']
                     ).transform_filter('datum.wind_speed < 30') #  & -500 < datum.value & datum.value < 1000

figure = base.mark_point().encode(
    tooltip=['time:T', 'value:Q', 'wind_speed:Q']
    )

graph = figure + figure.transform_regression('wind_speed', 'value').mark_line()

graph.save(f'{figure_path}/differanse_punktdiagram_begrenset.html')

# Wind restricted hourly values
base = alt.Chart(data_hour.rename(columns={'year': 'År'})).encode(
    x=alt.X('wind_speed:Q', title='Vindhastighet (m/s)'),
    y=alt.Y('value:Q', title='Størrelse på avvik (W)'),
    color='År:N'
    ).transform_fold(['difference_1', 'difference_2']
                     ).transform_filter('datum.wind_speed < 30') #  & -500 < datum.value & datum.value < 1000

figure = base.mark_point().encode(
    tooltip=['time:T', 'value:Q', 'wind_speed:Q']
    )

graph = figure + figure.transform_regression('wind_speed', 'value').mark_line()

graph.save(f'{figure_path}/differanse_punktdiagram_begrenset_timesverdier.html')

#%% Point diagram power and wind

# Wind restricted daily values
base = alt.Chart(data_maxhour.rename(columns={'year': 'År'})).encode(
    x=alt.X('wind_speed:Q', title='Vindhastighet (m/s)'),
    y=alt.Y('value:Q', title='Effekt (W)'),
    color='År:N'
    ).transform_fold(['ac_power_1', 'ac_power_2']).transform_filter('datum.wind_speed < 30')

figure = base.mark_point().encode(
    tooltip=['time:T', 'value:Q', 'wind_speed:Q']
    )

graph = figure + figure.transform_regression('wind_speed', 'value').mark_line()

graph.save(f'{figure_path}/effekter_punktdiagram.html')

# Wind restricted hourly values
base = alt.Chart(data_hour.rename(columns={'year': 'År'})).encode(
    x=alt.X('wind_speed:Q', title='Vindhastighet (m/s)'),
    y=alt.Y('value:Q', title='Effekt (W)'),
    color='År:N'
    ).transform_fold(['ac_power_1', 'ac_power_2']).transform_filter('datum.wind_speed < 30')

figure = base.mark_point().encode(
    tooltip=['time:T', 'value:Q', 'wind_speed:Q']
    )

graph = figure + figure.transform_regression('wind_speed', 'value').mark_line()

graph.save(f'{figure_path}/effekter_punktdiagram_timesverdier.html')

# Wind restricted and power produced daily values
base = alt.Chart(data_maxhour.rename(columns={'year': 'År'})).encode(
    x=alt.X('wind_speed:Q', title='Vindhastighet (m/s)'),
    y=alt.Y('value:Q', title='Effekt (W)'),
    color='År:N'
    ).transform_fold(['ac_power_1', 'ac_power_2']).transform_filter('datum.wind_speed < 30 & datum.value > 50')

figure = base.mark_point().encode(
    tooltip=['time:T', 'value:Q', 'wind_speed:Q']
    )

graph = figure + figure.transform_regression('wind_speed', 'value').mark_line()

graph.save(f'{figure_path}/effekter_punktdiagram_begrenset.html')

# Wind restricted and power produced hourly values
base = alt.Chart(data_hour.rename(columns={'year': 'År'})).encode(
    x=alt.X('wind_speed:Q', title='Vindhastighet (m/s)'),
    y=alt.Y('value:Q', title='Effekt (W)'),
    color='År:N'
    ).transform_fold(['ac_power_1', 'ac_power_2']).transform_filter('datum.wind_speed < 30 & datum.value > 500')

figure = base.mark_point().encode(
    tooltip=['time:T', 'value:Q', 'wind_speed:Q']
    )

graph = figure + figure.transform_regression('wind_speed', 'value').mark_line()

graph.save(f'{figure_path}/effekter_punktdiagram_begrenset_timesverdier.html')

#%% Measurements used 

layer_1 = alt.Chart(data_maxhour.rename(columns={'ac_power_1':'Anlegg 1', 
                                                 'ac_power_2':'Anlegg 2'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Effekt (W)'),
    color=alt.Color('key:N', title='Forklaring'),
    tooltip=['time:T','value:Q']
    ).transform_fold(['Anlegg 1', 'Anlegg 2'])

layer_2 = alt.Chart(data_maxhour.rename(columns={'G_tc':'Målt G_tc (W/m^2)',
                                                 'wind_speed':'Vindhastighet (m/s)',
                                                 'temp_air':'Lufttemperatur (degC)'})).mark_line(opacity=0.5).encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Måleverdi'),
    color=alt.Color('key:N', title='Forklaring'),
    tooltip=['time:T','value:Q']
    ).transform_fold(['Målt G_tc (W/m^2)', 'Vindhastighet (m/s)', 'Lufttemperatur (degC)'])

base = layer_1 + layer_2            
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Målte effekter', width=800, height=300
                                 ).resolve_scale(y='independent')
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/maleverdier_til_modellering.html')

#%% DC and AC power

# Daily values
base = alt.Chart(data_maxhour.rename(columns={'ac_power_1':'AC 1', 
                                              'ac_power_2':'AC 2',
                                              'dc_power_1':'DC 1',
                                              'dc_power_2':'DC 2'},)).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Effekt (W)'),
    color=alt.Color('key:N', title='Effekt'),
    tooltip=['time:T','value:Q']
    ).transform_fold(['AC 1', 'AC 2', 'DC 1', 'DC 2'])

      
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Målte effekter', width=800, height=300
                                 ).resolve_scale(y='independent')
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/effekter_ac_dc.html')
