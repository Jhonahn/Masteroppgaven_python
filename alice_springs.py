# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 16:52:16 2023

@author: johan
"""

import pyarrow.feather as feather
import pv_modelling
import altair as alt

from pvlib.location import Location

# Relative paths to figures
figure_path = 'figures/dkasc/Modultemperatur ned'

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
RMSE_values_power = pv_modelling.normalized_RMSE_values(model_hour_24['ac_power'], 
                                                        model_hour_25['ac_power'], 
                                                        inverter_dkasc.pdc0,
                                                        inverter_dkasc.pdc0,
                                                        data_hour['ac_power_1'],
                                                        data_hour['ac_power_2'])

# Calculate difference from model
data_hour['difference_1'] = model_hour_24['ac_power'] - data_hour['ac_power_1']
data_hour['difference_2'] = model_hour_25['ac_power'] - data_hour['ac_power_2']

data_maxhour['difference_1'] = data_hour['difference_1'].resample('d').mean()
data_maxhour['difference_2'] = data_hour['difference_2'].resample('d').mean()

# Calculate energies produced
energies = pv_modelling.pv_energy(model_hour_24['ac_power'], 
                                  model_hour_25['ac_power'], 
                                  data_hour['ac_power_1'], 
                                  data_hour['ac_power_2'])

# Use plotting function to make plots
pv_modelling.plot_results(figure_path, 
                          model_maxhour_24, 
                          model_maxhour_25, 
                          clear_sky_maxhour, 
                          data_maxhour)

#%% Analyse wind data

# RMSE values
RMSE_values_wind = pv_modelling.RMSE_values(data_hour.loc['2016-07-01':'2016-10-15','wind_speed'], 
                                            data_hour.loc['2016-07-01':'2016-10-15','wind_speed'],
                                            data_hour.loc['2016-07-01':'2016-10-15','wind_speed_orig'],
                                            data_hour.loc['2016-07-01':'2016-10-15','wind_speed_orig'])

# Define interval selection
interval = alt.selection_interval(encodings=['x'])

# Plot measured wind speeds
base = alt.Chart(data_maxhour.rename(columns={'wind_speed_orig':'Vindhastighet'})).mark_line().encode(
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

# Measured and PVGIS wind data
measured = alt.Chart(data_hour[:'2016-10-15'].rename(columns={'wind_speed_orig':'Vindhastighet målt'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Vindhastighet (m/s)'),
    color=alt.Color('key:N', title='Anlegg'),
    tooltip=['time:T','value:Q'],
    ).transform_fold(['Vindhastighet målt']
                     )
                     
pvgis = alt.Chart(data_hour[:'2016-10-15'].rename(columns={'wind_speed':'Vindhastighet PVGIS'})).mark_line().encode(
    x=alt.X('time:T', title='Tid'),
    y=alt.Y('value:Q', title='Vindhastighet (m/s)'),
    color=alt.Color('key:N', title='Anlegg'),
    tooltip=['time:T','value:Q'],
    ).transform_fold(['Vindhastighet PVGIS']
                     )

base = measured + pvgis
chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                    ).properties(title='Målte vindhastigheter', width=800, height=300)
view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
graph = alt.vconcat(chart, view).save(f'{figure_path}/vindhastigheter_sammenliknet.html')        

#%% Restricted point diagram

# layer_1 = alt.Chart(data_maxhour.rename(columns={'year': 'År'})).mark_point().encode(
#     x=alt.X('wind_speed:Q', title='Vindhastighet'),
#     y=alt.Y('difference_1:Q', title='Størrelse på avvik'),
#     color='År:N',
#     tooltip=['time:T', 'value:Q', 'wind_speed:Q']
#     ).transform_filter('-1000 < datum.difference_1 & datum.difference_1 < 1500')

# layer_2 = alt.Chart(data_maxhour.rename(columns={'year': 'År'})).mark_point().encode(
#     x=alt.X('wind_speed:Q', title='Vindhastighet'),
#     y=alt.Y('difference_2:Q', title='Størrelse på avvik'),
#     color='År:N',
#     tooltip=['time:T', 'value:Q', 'wind_speed:Q']
#     ).transform_filter('-1000 < datum.difference_2 & datum.difference_2 < 1500')

# graph = layer_1 + layer_2 

base = alt.Chart(data_maxhour.rename(columns={'year': 'År'})).encode(
    x=alt.X('wind_speed:Q', title='Vindhastighet (m/s)'),
    y=alt.Y('value:Q', title='Størrelse på avvik (W)'),
    color='År:N'
    ).transform_fold(['difference_1', 'difference_2']
                     ).transform_filter('-1000 < datum.value & datum.value < 900')

figure = base.mark_point().encode(
    tooltip=['time:T', 'value:Q', 'wind_speed:Q']
    )

graph = figure + figure.transform_regression('wind_speed', 'value').mark_line()

# reg_params = chart.transform_regression('wind_speed', 'value',
#                                      params=True   
# ).mark_text(align='left', lineBreak='\n'
# ).encode(
#     x=alt.value(150),  # pixels from left
#     y=alt.value(250),  # pixels from top
#     text='params:N'
# ).transform_calculate(
#     params='"a = " + round(datum.coef[-0]) + \
#     "      b = " + round(datum.coef[-1] - datum.coef[-0]/100 )')

# graph = figure + reg_line # + reg_params


graph.save(f'{figure_path}/differanse_punktdiagram_begrenset.html')      

# Wind restricted and power produced
base = alt.Chart(data_maxhour.rename(columns={'year': 'År'})).encode(
    x=alt.X('wind_speed:Q', title='Vindhastighet (m/s)'),
    y=alt.Y('value:Q', title='Effekt (W)'),
    color='År:N'
    ).transform_fold(['ac_power_1', 'ac_power_2']).transform_filter('datum.wind_speed < 30 & datum.value > 500')

figure = base.mark_point().encode(
    tooltip=['time:T', 'value:Q', 'wind_speed:Q']
    )

graph = figure + figure.transform_regression('wind_speed', 'value').mark_line()

graph.save(f'{figure_path}/effekter_punktdiagram_begrenset.html')