# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 14:48:11 2023

@author: johan
"""



import pandas as pd
import pvlib
import numpy as np
import altair as alt

from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from typing import Tuple



class SystemModule:
    """
    Saves the parameters of a PV module.
    
    Parameters
    ----------
    name : str
        The name of the PV module model.
    celltype : int
        Technology type of the solar cells. Value is one of 'monoSi', 'multiSi', 'polySi', 'cis', 'cigs', 'cdte', 'amorphous'.
    pdc0 : float or int
        The rated power of the module in [W].
    v_mp : float
        Voltage at maximum power point [W].
    i_mp : float
        Current at maximum power point [A].
    v_oc : float
        Open circuit voltage [V].
    i_sc : float
        Short circuit current [A].
    alpha_sc : float
        Temperature coefficient of short circuit current. A number between 0 and 1 [A/degree C].
    beta_voc : float
        Temperature coefficient of open circuit voltage. A number between 0 and 1 [V/degree C].
    gamma_pdc : float
        Temperature coefficient of DC power at maximum point point [%/C].
    cells_in_series : int
        Number of cells in series. Number of series multiplied by cells in series, e.g. 3*20 or 6*10.
    temp_ref : float, default 25
        Reference temperature condition [C].
    
    """
    def __init__(self, name, celltype, pdc0, v_mp, i_mp, v_oc, i_sc, alpha_sc, beta_voc, gamma_pdc, cells_in_series, temp_ref = 25):
        self.name = name                             
        self.celltype = celltype                     
        self.pdc0 = pdc0                             
        self.v_mp = v_mp                             
        self.i_mp = i_mp                             
        self.v_oc = v_oc                             
        self.i_sc = i_sc                             
        self.alpha_sc = alpha_sc * i_sc              
        self.beta_voc = beta_voc * v_oc              
        self.gamma_pdc = gamma_pdc                   
        self.cells_in_series = cells_in_series       
        self.temp_ref = temp_ref           

 

class SystemParameters:
    """
    Saves the parameters of a PV system.
    
    Parameters
    ----------
    name : str
        The name of the system.
    strings_per_inverter : int
        The number of strings per inverter.
    modules_per_string : int
        The number of modulers per string.
    surface_tilt : int
        The surface tilt of the PV array. Positive values indicate a tilt towards solar zenith.
    surface_azimuth : int
        The azimuth angle of the PV array. 0 points directly north, 90 east, 180 south, 270 west.
    date_start : t
        Starting point of the dataset. 'YYYY-MM-DD hh:mm'
    date_end : t
        End point of the dataset. 'YYYY-MM-DD hh:mm'
    
    """
    def __init__(self, name, strings_per_inverter, modules_per_string, surface_tilt, surface_azimuth, date_start, date_end):
        self.name = name                                    
        self.strings_per_inverter = strings_per_inverter    
        self.modules_per_string = modules_per_string  
        self.surface_tilt = surface_tilt              
        self.surface_azimuth = surface_azimuth
        self.date_start = date_start
        self.date_end = date_end
        
        

class SystemInverter:
    """
    Saves the parameters of an inverter. Includes some standard inverter types.
    
    Parameters
    ----------
    name : str
        The name of the inverter model.
    pdc0 : float
        Maximum inverter capacity [W].
    eta_inv_nom : float
        Nominal efficiency of the inverter as a number from 0 to 1. Usually euro-eta.
    eta_inv_ref : float, default 0.9637
        Reference efficiency as a number from 0 to 1.
    
    """
    def __init__(self, name, pdc0, eta_inv_nom, eta_inv_ref = 0.9637):
        self.name = name                                
        self.pdc0 = pdc0                                
        self.eta_inv_nom = eta_inv_nom                  
        self.eta_inv_ref = eta_inv_ref    



def pv_model(system_parameters: SystemParameters, system_module: SystemModule, system_inverter: SystemInverter, data: pd.DataFrame, location: Location) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Models the output of a PV system using its parameters and weather data.

    Parameters
    ----------
    system_parameters : Class
        Class containing the following system parameters: 
            name, 
            strings_per_SystemInverter, 
            SystemModules_per_string, 
            surface_tilt, 
            surface_azimuth
            date_start
            date_end
    system_module : Class
        Class containing the following module parameters: 
            name, 
            celltype, 
            pdc0, 
            v_mp, 
            i_mp, 
            v_oc, 
            i_sc, 
            alpha_sc, 
            beta_voc, 
            gamma_pdc, 
            cells_in_series, 
            temp_ref
    system_inverter : Class
        Class containing the following inverter parameters:
            name, 
            pdc0, 
            eta_inv_nom, 
            eta_inv_ref
    data : df
        Dataframe containing the weather parameters. Must contain:
            temp_air,
            G_tc,
            wind_speed
    location : Class
        Class defined by the pvlib library. Contains the following parameters:
            latitude,
            longitude,
            timezone,
            altitude,
            name

    Returns
    -------
    model_results : df
        Dataframe containing the following results per hour:
            'i_mp', 
            'v_mp', 
            'p_mp_dc', 
            'p_mp_ac', 
            'inverter_power_loss'
    model_results_maxhour : df
        The model_results dataframe resampled to contain the hour with the largest average value per day
    model_results_month : df
        The model_results dataframe resampled to the average value per month
    """
    
    # Drop unecessary data and resample to hourly average
    weather_parameters = data.loc[system_parameters.date_start:system_parameters.date_end, 
                                  ['temp_air', 'G_tc', 'wind_speed']].resample('h').mean()
    
    # Calculate cell temperature based on the Faiman model
    temp_cell = pvlib.temperature.faiman(weather_parameters['G_tc'], 
                                         weather_parameters['temp_air'], 
                                         weather_parameters['wind_speed'])
    
    # Estimate parameters for use in the CEC single diode model used below
    I_L_ref, I_o_ref, R_s, R_sh_ref, a_ref, Adjust \
        = pvlib.ivtools.sdm.fit_cec_sam(celltype = system_module.celltype, 
                                        v_mp = system_module.v_mp, 
                                        i_mp = system_module.i_mp, 
                                        v_oc = system_module.v_oc, 
                                        i_sc = system_module.i_sc, 
                                        alpha_sc = system_module.alpha_sc, 
                                        beta_voc = system_module.beta_voc, 
                                        gamma_pmp = system_module.gamma_pdc, 
                                        cells_in_series = system_module.cells_in_series, 
                                        temp_ref = system_module.temp_ref)
    
    # Calculate necessary for calculating the MPP
    cec_parameters = pvlib.pvsystem.calcparams_cec(weather_parameters['G_tc'], 
                                                   temp_cell, 
                                                   system_module.alpha_sc, 
                                                   a_ref, 
                                                   I_L_ref, 
                                                   I_o_ref, 
                                                   R_sh_ref, 
                                                   R_s, 
                                                   Adjust)
    
    # Calculate maximum power point
    mpp = pvlib.pvsystem.max_power_point(*cec_parameters,
                                         method = 'newton')
    
    # Define PV system
    system = PVSystem(modules_per_string = system_parameters.modules_per_string, 
                      strings_per_inverter = system_parameters.strings_per_inverter)
    
    # Calculate power into the inverter
    dc_scaled = system.scale_voltage_current_power(mpp)
    
    # Calculate power out of the inverter
    resulting_ac = pvlib.inverter.pvwatts(pdc = dc_scaled.p_mp, 
                                          pdc0 = system_inverter.pdc0,
                                          eta_inv_nom = system_inverter.eta_inv_nom,
                                          eta_inv_ref = system_inverter.eta_inv_ref)
    
    # Colculate losses in inverter
    inverter_power_loss = dc_scaled['p_mp'] - resulting_ac
    
    # Combine results in dataframe and change column names
    model_results = pd.concat([dc_scaled, resulting_ac, inverter_power_loss, temp_cell], axis=1)
    model_results.columns = ['i_mp', 'v_mp', 'dc_power', 'ac_power', 'inverter_power_loss', 'temp_cell']
    
    # Resample dataset
    model_results_maxhour = model_results.resample('d').max()
    model_results_month = model_results.resample('m').mean()
    
    # Add time column to make altair able to interpret data
    model_results['time'] = model_results.index
    model_results_maxhour['time'] = model_results_maxhour.index
    model_results_month['time'] = model_results_month.index
    
    return model_results, model_results_maxhour, model_results_month



def get_clear_sky_parameters(system_parameters: SystemParameters, location: Location) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Models the clear sky irradiance for a system.

    Parameters
    ----------
    system_parameters : Class
        Class containing the following system parameters: 
            name, 
            strings_per_SystemInverter, 
            SystemModules_per_string, 
            surface_tilt, 
            surface_azimuth
            date_start
            date_end
    location : Class
        Class defined by the pvlib library. Contains the following parameters:
            latitude,
            longitude,
            timezone,
            altitude,
            name

    Returns
    -------
    clear_sky : df
        Dataframe containing the following results:
            'clear_sky_G_th', 
            'clear_sky_G_b*', 
            'clear_sky_G_dh', 
            'clear_sky_G_t*', 
            'clear_sky_G_tc'
    clear_sky_maxhour : df
        The clear_sky dataframe resampled to contain the hour with the largest average value per day
    clear_sky_month : df
        The clear_sky dataframe resampled to the average value per month
    """
    
    # Define when to get clear sky data
    times = pd.date_range(start=system_parameters.date_start, 
                          end=system_parameters.date_end, 
                          freq='h', 
                          tz=location.tz)
    
    # Collect raw clear sky data
    clear_sky = location.get_clearsky(times)

    # Calculate total direct irradiance (G_t*)
    clear_sky['global'] = clear_sky['dni'] + clear_sky['dhi']

    clear_sky.index = pd.date_range(start=system_parameters.date_start,
                                    periods=len(clear_sky),
                                    freq="h",
                                    tz=location.tz)
    
    # Find collector values for clear sky irradiance
    # Find the suns position
    solar_position = location.get_solarposition(times=times)

    # Retreive angle of incidence: angle between beam and collector normal (theta)
    angle_of_incidence = pvlib.irradiance.aoi(system_parameters.surface_tilt, 
                                              system_parameters.surface_azimuth, 
                                              solar_position.apparent_zenith, 
                                              solar_position.azimuth)
    
    # Calculate mathematical effect of the angle of incidence
    incident_angle_modifier = pvlib.iam.ashrae(angle_of_incidence)
    
    # Calculate clear sky total irradiation at the slope of the collector
    clear_sky['G_tc'] = clear_sky['dni'] * incident_angle_modifier + clear_sky['dhi']
    
    # Rename columns
    clear_sky.rename(columns={'ghi': 'clear_sky_G_th', 
                              'dni': 'clear_sky_G_b*', 
                              'dhi': 'clear_sky_G_dh', 
                              'global': 'clear_sky_G_t*', 
                              'G_tc': 'clear_sky_G_tc'}, inplace=True)
    
    # Resample dataset
    clear_sky_maxhour = clear_sky.resample('d').max()
    clear_sky_month = clear_sky.resample('m').mean()
    
    # Add time column to make altair able to interpret data
    clear_sky['time'] = clear_sky.index
    clear_sky_maxhour['time'] = clear_sky_maxhour.index
    clear_sky_month['time'] = clear_sky_month.index
    
    return clear_sky, clear_sky_maxhour, clear_sky_month



def model_RMSE(model_data_1: pd.Series, model_data_2: pd.Series, system_size_1: float, system_size_2: float, measured_data_1: pd.Series, measured_data_2: pd.Series) -> Tuple[pd.DataFrame]:
    """
    Calculates the root mean squared error (RMSE) of two model series with respect to a measured dataframe.

    Args:
        model_data_1 (pandas.Series): The first model series.
        model_data_2 (pandas.Series): The second model seires.
        system_size_1 (float): The first system size. E.g. rated inverter size.
        system_size_2 (float): The second system size. E.g. rated inverter size.
        measured_data_1 (pandas.Series): The first measured data.
        measured_data_2 (pandas.Series): The second measured data.

    Returns:
        Tuple[pandas.DataFrame]: A dataframe containing the RMSE and normalized RMSE of each model dataframe. 
        The first two values correspond to model_data_1 and the last two values corresponds to model_data_2.
    """
    
    # Calculate the squared differences between the models and the measured data
    diff_1 = model_data_1 - measured_data_1
    diff_2 = model_data_2 - measured_data_2
    
    # Calculate the MSE values
    MSE_1 = (np.square(diff_1)).mean()
    MSE_2 = (np.square(diff_2)).mean()
    
    # Calculate the RMSE values
    RMSE_1 = np.sqrt(MSE_1)
    RMSE_2 = np.sqrt(MSE_2)
    
    # Normalize RMSE values
    RMSE_1_normalized = RMSE_1 / system_size_1
    RMSE_2_normalized = RMSE_2 / system_size_2
    
    # Make dataframe
    RMSE_df = pd.DataFrame({'RMSE_1': [RMSE_1], 
                            'RMSE_1_normalized': [RMSE_1_normalized], 
                            'RMSE_2': [RMSE_2], 
                            'RMSE_2_normalized': [RMSE_2_normalized]})
    
    return RMSE_df




def plot_results(path: str, model_results_1: pd.DataFrame, model_results_2: pd.DataFrame, clear_sky: pd.DataFrame, measured_results: pd.DataFrame) -> Tuple:
    """
    Generate Altair plots for two different solar panel installations based on four pandas DataFrames: 
    `model_results_1`, `model_results_2`, `clear_sky`, and `measured_results`. 

    Parameters:
    -----------
    path : str
        The relative directory path where the resulting plots will be saved.
    model_results_1 : pd.DataFrame
        A pandas DataFrame containing simulated model results for solar panel installation 1.
    model_results_2 : pd.DataFrame
        A pandas DataFrame containing simulated model results for solar panel installation 2.
    clear_sky : pd.DataFrame
        A pandas DataFrame containing clear-sky irradiance data.
    measured_results : pd.DataFrame
        A pandas DataFrame containing measured results from the solar panel installations.

    Returns:
    --------
    Tuple
        A tuple of Altair plots saved as HTML files in the specified `path`. 
    """
    
    # Define interval for plotting in altair
    interval = alt.selection_interval(encodings=['x'])
    
    # All model results
    graph_1 = alt.Chart(model_results_1.rename(columns={'i_mp':'Strøm ved MPP (A)', 
                          'v_mp':'Spenning ved MPP (V)', 
                          'dc_power':'Uomformet effekt (W)',
                          'ac_power': 'Omformet effekt (W)', 
                          'inverter_power_loss':'Omformertap (W)'}
                         )).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Verdi'),
        color=alt.Color('key:N', title='Målepunkt (Enhet)'),
        ).transform_fold(['Strøm ved MPP (A)',
                          'Spenning ved MPP (V)',
                          'Uomformet effekt (W)',
                          'Omformet effekt (W)',
                          'Omformertap (W)']
                         )
                          
    graph_2 = alt.Chart(model_results_2.rename(columns={'i_mp':'Strøm ved MPP (A)', 
                          'v_mp':'Spenning ved MPP (V)', 
                          'dc_power':'Uomformet effekt (W)',
                          'ac_power': 'Omformet effekt (W)', 
                          'inverter_power_loss':'Omformertap (W)'}
                         )).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Verdi'),
        color=alt.Color('key:N', title='Målepunkt (Enhet)'),
        ).transform_fold(['Strøm ved MPP (A)',
                          'Spenning ved MPP (V)',
                          'Uomformet effekt (W)',
                          'Omformet effekt (W)',
                          'Omformertap (W)']
                         )
    
    graph_3 = alt.Chart(clear_sky.rename(columns={'clear_sky_G_th':'G_th skyfritt (w/m^2)', 
                      'clear_sky_G_b*':'G_b* skyfritt (w/m^2)', 
                      'clear_sky_G_dh':'G_dh skyfritt (w/m^2)', 
                      'clear_sky_G_t*':'G_t* skyfritt (w/m^2)'})).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Verdi'),
        color=alt.Color('key:N', title='Målepunkt (Enhet)'),
        ).transform_fold(['G_th skyfritt (w/m^2)', 
                          'G_b* skyfritt (w/m^2)', 
                          'G_dh skyfritt (w/m^2)', 
                          'G_t* skyfritt (w/m^2)']
                         )
    
    base = graph_1 + graph_3
    chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()))
                        ).properties(title='Alle modellresultater anlegg 1', width=800, height=300)
    view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
    graph = alt.vconcat(chart, view).save(f'{path}/modellresultater_1.html')
    
    base = graph_2 + graph_3
    chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()))
                        ).properties(title='Alle modellresultater anlegg 2', width=800, height=300)
    view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
    graph = alt.vconcat(chart, view).save(f'{path}/modellresultater_2.html')
    
    # All measurements
    base = alt.Chart(measured_results.rename(columns={'ac_power_1': 'Omformet effekt (W)', 
                          'G_dc': 'Diffus innstråling på kollektor (W/m^2)', 
                          'G_tc': 'Innstråling på kollektor (W/m^2)', 
                          'wind_speed': 'Vindhastighet (m/s)', 
                          'temp_air': 'Lufttemperatur (grader Celsius)'}
                          )).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Verdi'),
        color=alt.Color('key:N', title='Målepunkt (Enhet)'),
        ).transform_fold(['Omformet effekt (W)', 
                          'Diffus innstråling på kollektor (W/m^2)', 
                          'Innstråling på kollektor (W/m^2)', 
                          'Vindhastighet (m/s)', 
                          'Lufttemperatur (grader Celsius)']
                          )
                             
    chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                        ).properties(title='Alle måleresultater anlegg 1', width=800, height=300)
    view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
    graph = alt.vconcat(chart, view).save(f'{path}/maleresultater_1.html')
    
             
    base = alt.Chart(measured_results.rename(columns={'ac_power_2': 'Omformet effekt (W)', 
                          'G_dc': 'Diffus innstråling på kollektor (W/m^2)', 
                          'G_tc': 'Innstråling på kollektor (W/m^2)', 
                          'wind_speed': 'Vindhastighet (m/s)', 
                          'temp_air': 'Lufttemperatur (grader Celsius)'}
                          )).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Verdi'),
        color=alt.Color('key:N', title='Målepunkt (Enhet)'),
        ).transform_fold(['Omformet effekt (W)', 
                          'Diffus innstråling på kollektor (W/m^2)', 
                          'Innstråling på kollektor (W/m^2)', 
                          'Vindhastighet (m/s)', 
                          'Lufttemperatur (grader Celsius)']
                          )
                           
    chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                        ).properties(title='Alle måleresultater anlegg 2', width=800, height=300)
    view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
    graph = alt.vconcat(chart, view).save(f'{path}/maleresultater_2.html')
    
    # Irradiance values
    layer_1 = alt.Chart(measured_results.rename(columns={'G_tc':'Målt G_tc'})).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Effekt (W)'),
        color=alt.Color('key:N', title='Innstrålingsverdi'),
        tooltip=['time:T','value:Q']
        ).transform_fold(['Målt G_tc'])
    
    layer_2 = alt.Chart(clear_sky.rename(columns={'clear_sky_G_tc':'Skyfri G_tc'})).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Effekt (W)'),
        color=alt.Color('key:N', title='Innstrålingsverdi'),
        tooltip=['time:T','value:Q']
        ).transform_fold(['Skyfri G_tc'])
                         
    base = layer_1 + layer_2
    chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                        ).properties(title='Innstrålingsverdier', width=800, height=300)
    view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
    graph = alt.vconcat(chart, view).save(f'{path}/innstraling.html')
    
    # Measured powers
    layer_1 = alt.Chart(measured_results.rename(columns={'ac_power_1':'Anlegg 1', 'ac_power_2':'Anlegg 2'})).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Effekt (W)'),
        color=alt.Color('key:N', title='Forklaring'),
        ).transform_fold(['Anlegg 1', 'Anlegg 2'])
    
    layer_2 = alt.Chart(measured_results.rename(columns={'G_tc':'Målt G_tc'})).mark_line(opacity=0.5).encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Innstrålt effekt (W/m^2)'),
        color=alt.Color('key:N', title='Forklaring'),
        ).transform_fold(['Målt G_tc'])
    
    base = layer_1 + layer_2            
    chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                        ).properties(title='Målte effekter', width=800, height=300
                                     ).resolve_scale(y='independent')
    view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
    graph = alt.vconcat(chart, view).save(f'{path}/malte_effekter.html')
    
    # Produced powers
    graph_1 = alt.Chart(measured_results.rename(columns={'ac_power_1':'Målt'})).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Effekt (W)'),
        color=alt.Color('key:N', title='Effekt'),
        ).transform_fold(['Målt'])
    
    graph_2 = alt.Chart(model_results_1.rename(columns={'ac_power':'Modellert'})).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Effekt (W)'),
        color=alt.Color('key:N', title='Effekt'),
        ).transform_fold(['Modellert'])
    
    base = graph_2 + graph_1
    chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()), title='Tid')
                        ).properties(title='Produserte effekter anlegg 1', width=800, height=300)
    view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
    graph = alt.vconcat(chart, view).save(f'{path}/produserte_effekter_1.html')
    
    graph_1 = alt.Chart(measured_results.rename(columns={'ac_power_2':'Målt'})).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Effekt (W)'),
        color=alt.Color('key:N', title='Effekt'),
        ).transform_fold(['Målt'])
                                         
    graph_2 = alt.Chart(model_results_2.rename(columns={'ac_power':'Modellert'})).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Effekt (W)'),
        color=alt.Color('key:N', title='Effekt'),
        ).transform_fold(['Modellert'])
    
    base = graph_2 + graph_1
    chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()))
                        ).properties(title='Produserte effekter anlegg 2', width=800, height=300)
    view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
    graph = alt.vconcat(chart, view).save(f'{path}/produserte_effekter_2.html')
    
    # Measured power and wind speed
    graph_1 = alt.Chart(measured_results.rename(columns={'ac_power_1':'Anlegg 1', 'ac_power_2':'Anlegg 2'})).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Effekt (W)'),
        color='key:N'
        ).transform_fold(['Anlegg 1', 'Anlegg 2'])
    
    graph_2 = alt.Chart(measured_results.rename(columns={'wind_speed':'Vindhastighet'})).mark_line(opacity=0.5).encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Vindhastighet (m/s)'),
        color=alt.Color('key:N', title='Forklaring'),
        ).transform_fold(['Vindhastighet'])

    base = graph_1 + graph_2
    chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()))
                        ).properties(title='Vind og produsert effekt', width=800, height=300
                                     ).resolve_scale(y='independent')
    view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
    graph = alt.vconcat(chart, view).save(f'{path}/vind_og_effekter.html')
    
    # Difference and wind speed as line
    graph_1 = alt.Chart(measured_results.rename(columns={'difference_1':'Anlegg 1', 'difference_2':'Anlegg 2'})).mark_line().encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Avvik fra modell (W)'),
        color=alt.Color('key:N', title='Forklaring'),
        ).transform_fold(['Anlegg 1', 'Anlegg 2'])
    
    graph_2 = alt.Chart(measured_results.rename(columns={'wind_speed':'Vindhastighet'})).mark_line(opacity=0.5).encode(
        x=alt.X('time:T', title='Tid'),
        y=alt.Y('value:Q', title='Vindhastighet (m/s)'),
        color=alt.Color('key:N', title='Forklaring'),
        ).transform_fold(['Vindhastighet'])
    
    base = graph_1 + graph_2
    chart = base.encode(x=alt.X('time:T', scale=alt.Scale(domain=interval.ref()))
                        ).properties(title='Differanse modellert og målt effekt', width=800, height=300
                                     ).resolve_scale(y='independent')
    view = base.add_selection(interval).properties(title='Valgvindu', width=800, height=50)
    graph = alt.vconcat(chart, view).save(f'{path}/differanse_linje.html')
    
    # Difference and wind speed as histogram
    graph = alt.Chart(measured_results).mark_bar().encode(
        x=alt.X('value:Q', bin=alt.BinParams(maxbins=100), title='Avvik fra modell (W)'),
        y=alt.Y('count():Q', title='Antall hendelser'), # scale=alt.Scale(type='log', base=10) optimalt hadde dette fungert
        color=alt.Color('wind_speed', bin=alt.BinParams(step=3, extent=[0,15]), title='Vindhastighet (m/s)'),
        tooltip=['time:T', 'value:Q', 'wind_speed:Q']
        # order=alt.Order(field='wind_speed', sort='descending', bin=alt.BinParams(step=3, extent=[0,12])) # 'color_wind_speed_sort_index:Q'
        ).transform_fold(['difference_1', 'difference_2']
                          ).transform_filter('datum.wind_speed<=15'
                              ).interactive().properties(title='Differanse modellert og målt effekt med vindhastighet')
    
    graph.save(f'{path}/differanse_histogram.html')
    
    # Difference and wind speed as histogram monthly
    graph = alt.Chart(measured_results).mark_bar(opacity=0.5).encode(
        x=alt.X('value:Q', 
                bin=alt.BinParams(maxbins=100), 
                title='Avvik fra modell (W)'
                ),
        y=alt.Y('count():Q', 
                # scale=alt.Scale(type='log', base=10), 
                title='Antall hendelser',
                stack=None
                ), 
        color=alt.Color('year:N', 
                        # scale=alt.Scale(scheme='category10'), 
                        title='År'
                        ),
        tooltip=['time:T', 'value:Q', 'wind_speed:Q']
        ).transform_fold(['difference_1', 'difference_2']
                          ).interactive(
                              ).properties(title='Differanse modellert og målt effekt med vindhastighet'
                                                    ).facet(facet='month:N', columns=4)
                                           
    graph.save(f'{path}/differanse_histogram_manedlig.html')
    
    # base = alt.Chart(dkasc_data_maxhour)
    
    # hist_24 = base.mark_bar(opacity=0.5).encode(
    #     x=alt.X('difference_1:Q', 
    #             bin=alt.BinParams(maxbins=100), 
    #             title='Avvik fra modell (W)'
    #             ),
    #     y=alt.Y('count():Q', 
    #                 title='Antall hendelser',
    #                 ), 
    #     color=alt.Color('year:N', 
    #                     title='År'
    #                     )
    #     )
    
    # hist_25 = base.mark_bar(opacity=0.5).encode(
    #     x=alt.X('difference_2:Q', 
    #             bin=alt.BinParams(maxbins=100), 
    #             title='Avvik fra modell (W)'
    #             ),
    #     y=alt.Y('count():Q', 
    #                 title='Antall hendelser',
    #                 ), 
    #     color=alt.Color('year:N', 
    #                     title='År'
    #                     )
    #     )
                                                        
    # lines_24 = base.mark_line(color='red').encode(
    #     x=alt.X('mean(difference_1):Q'),
    #     tooltip=['mean(difference_1):Q', 'ci0(difference_1):Q']
    #     )
    
    # lines_25 = base.mark_line(color='orange').encode(
    #     x=alt.X('mean(difference_2):Q'),
    #     tooltip=['mean(difference_2):Q', 'ci0(difference_2):Q']
    #     )
    
    # mean_24 = base.mark_text(align='left', baseline='top', dx=1, dy=10).encode(
    #     text='label:N',
    #     tooltip=['mean(difference_1):Q', 'ci0(difference_1):Q']
    #     ).transform_joinaggregate(mean='mean(difference_1)'
    #         ).transform_calculate(
    #         label='"Snitt: " + format(datum.mean, ".2f")')
    
    # text_24 = base.mark_text(align='left', baseline='top', dx=1, dy=0).encode(
    #     text=alt.Text('mean(difference_1):Q', format='.2f'),
    #     tooltip=['mean(difference_1):Q', 'ci0(difference_1):Q']
    #     )
                
    # text_25 = base.mark_text(align='left', baseline='top', dx=1, dy=0).encode(
    #     text=alt.Text('mean(difference_2):Q', format='.2f'),
    #     tooltip=['mean(difference_2):Q', 'ci0(difference_2):Q']
    #     )
    
    
    
    # graph = alt.layer(hist_24, hist_24, lines_24, lines_25, text_24, text_25, data=dkasc_data_maxhour
    #                     ).facet(facet='month:N', columns=4
    #                             ).interactive().properties(title='Differanse modellert og målt effekt DKASC med vindhastighet')
    
    # graph.save('Figurer/DKASC/dkasc_differanse_histogram_maned.html')
    
    
    # Point diagram with density charts
    brush = alt.selection_interval()
    
    base = alt.Chart(measured_results.rename(columns={'year': 'År'})).encode(
        x=alt.X('wind_speed:Q', title='Vindhastighet'),
        y=alt.Y('value:Q', title='Størrelse på avvik'),
        color='År:N'
    ).transform_fold(
        ['difference_1', 'difference_2']
    ).transform_filter(
        'datum.wind_speed<=15'
    )
    
    points = base.mark_point().encode(
        color=alt.condition(brush, 'År:N', alt.value('lightgray')),
        tooltip=['time:T', 'value:Q', 'wind_speed:Q']
    ).add_selection(
        brush
    )
    
    density_x = base.transform_density(
        density='wind_speed',
        extent=[0,16],
        groupby=['År'],
        steps=200,
        as_=['Vindhastighet', 'Tetthet']
    ).mark_area(
        orient='vertical', 
        opacity=0.5
    ).encode(
        y='Tetthet:Q',
        x=alt.X('Vindhastighet:Q', title='Vindhastighet')
    ).transform_filter(
        brush
    ).properties(
        height=100
    )
    
    density_y = base.transform_density(
        density='value',
        groupby=['År'],
        steps=200,
        as_=['Avvik', 'Tetthet']
    ).mark_area(
        orient='horizontal', 
        opacity=0.5
    ).encode(
        x='Tetthet:Q',
        y=alt.Y('Avvik:Q', title='Størrelse på avvik')
    ).transform_filter(
        brush
    ).properties(
        width=100
    )
        
    graph = alt.vconcat(
        density_x,
        alt.hconcat(
            points,
            density_y),
        data=measured_results
    ).properties(title='Differanse modellert og målt effekt med vindhastighet')
    
    graph.save(f'{path}/differanse_punktdiagram.html')
    
    # Point diagram with density charts
    # brush = alt.selection_interval()
    
    # base = alt.Chart(measured_results.rename(columns={'year': 'År'})).encode(
    #     x=alt.X('wind_speed:Q', title='Vindhastighet'),
    #     y=alt.Y('value:Q', title='Størrelse på avvik'),
    #     color='År:N'
    #     ).transform_fold(['difference_1', 'difference_2']).add_selection(
    #         brush
    #     )
    
    # points = base.mark_point().encode(
    #     color=alt.condition(brush, 'År:N', alt.value('lightgray')),
    #     tooltip=['time:T', 'value:Q', 'wind_speed:Q']
    #     )
    
    # # Filter the original dataset with brush selection
    # filtered_data = alt.selection(
    #     type='interval', encodings=['x', 'y']
    # )
    
    # filtered = base.transform_filter(
    #     filtered_data
    # )
    
    # density_x = filtered.transform_density(
    #     density='wind_speed',
    #     groupby=['År'],
    #     steps=200,
    #     as_=['Vindhastighet', 'Tetthet']
    # ).mark_area(
    #     orient='vertical', 
    #     opacity=0.5
    # ).encode(
    #     y='Tetthet:Q',
    #     x=alt.X('Vindhastighet:Q', title='Vindhastighet')
    # ).properties(
    #     height=100
    # )
    
    # density_y = filtered.transform_density(
    #     density='value',
    #     groupby=['År'],
    #     steps=200,
    #     as_=['Avvik', 'Tetthet']
    # ).mark_area(
    #     orient='horizontal', 
    #     opacity=0.5
    # ).encode(
    #     x='Tetthet:Q',
    #     y=alt.Y('Avvik:Q', title='Størrelse på avvik')
    # ).properties(
    #     width=100
    # )
        
    # graph = alt.vconcat(
    #     density_x,
    #     alt.hconcat(
    #         points,
    #         density_y)
    # ).properties(title='Differanse modellert og målt effekt med vindhastighet')
    
    # graph.save(f'{path}/differanse_punktdiagram.html')
    
    # Point diagram with histograms
    brush = alt.selection_interval()
    
    base = alt.Chart(measured_results.rename(columns={'year': 'År'})).encode(
        x=alt.X('wind_speed:Q', title='Vindhastighet'),
        y=alt.Y('value:Q', title='Størrelse på avvik'),
        color='År:N'
        ).transform_fold(['difference_1', 'difference_2'])
    
    points = base.mark_point().encode(
        # color=alt.condition(brush, 'År:N', alt.value('lightgray')),
        tooltip=['time:T', 'value:Q', 'wind_speed:Q']
        )
    
    # .add_selection(
    #         brush
    #     )
    # .transform_filter(
    #     brush
    # )
    
    hist_x = base.mark_bar(opacity=0.5).encode(
        y='count()',
        x=alt.X('Vindhastighet:Q', 
                bin=alt.BinParams(maxbins=20),
                title='Vindhastighet')
    ).properties(
        height=100
    )
    
    hist_y = base.mark_bar(opacity=0.5).encode(
        x='count()',
        y=alt.Y('Avvik:Q', 
                bin=alt.BinParams(maxbins=100),
                title='Størrelse på avvik')
    ).properties(
        width=100
    )
        
    graph = alt.vconcat(
        hist_x,
        alt.hconcat(
            points,
            hist_y)
    ).properties(title='Differanse modellert og målt effekt med vindhastighet')
    
    graph.save(f'{path}/differanse_punktdiagram_histogram.html')
    