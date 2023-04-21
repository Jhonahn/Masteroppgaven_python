# -*- coding: utf-8 -*-
'''
Created on Thu Feb 16 14:10:48 2023

@author: johan
'''

# Importing libraries
import pandas as pd
import pvlib
import os
import pyarrow.feather as feather

from pvlib.location import Location

# Define system orientation
surface_tilt = 20
surface_azimuth = 0

# Define time period
iotools_start = 2016
iotools_end = 2020
date_start = '2016-07-03 00:00'
date_end = '2022-12-31 23:59'

# Define system location
location = Location(name='Alice Springs', 
                    latitude=-23.761971597764013, 
                    longitude=133.87473061882616, 
                    tz='Australia/Darwin', 
                    altitude=95)

# Define file path
dkasc_path = os.path.join('C:', os.sep, 'Users', 'johan', 
                          'OneDrive', 'Dokumenter', 'NMBU', 'Master', 
                          'databehandling_og_modellering', 'alice_springs')

# Importing datasets
dkasc_24 = pd.read_csv('alice_springs/csv/213-Site_24-Q-CELLS.csv',
                       index_col='timestamp')

dkasc_25 = pd.read_csv('alice_springs/csv/212-Site_25-Hanwha-Solar.csv', 
                       usecols=['timestamp',
                                'Active_Energy_Delivered_Received', 
                                'Current_Phase_Average', 
                                'Performance_Ratio', 
                                'Active_Power'], 
                       index_col='timestamp')

# Ensure correct interpretation of time index
dkasc_24.index = pd.date_range(start=date_start,
                                periods=len(dkasc_24),
                                freq='5min',
                                tz=location.tz)

dkasc_25.index = pd.date_range(start=date_start,
                                periods=len(dkasc_25),
                                freq='5min',
                                tz=location.tz)

# Changing the unit of power from kilowatt to watt
dkasc_24['Active_Power'] = dkasc_24['Active_Power'] * 1000
dkasc_25['Active_Power'] = dkasc_25['Active_Power'] * 1000

# Rename columns
dkasc_24.rename(columns={'Weather_Temperature_Celsius': 'temp_air', 
                         'Global_Horizontal_Radiation': 'G_th',
                         'Diffuse_Horizontal_Radiation': 'G_dh',
                         'Radiation_Global_Tilted': 'G_tc',
                         'Radiation_Diffuse_Tilted': 'G_dc',
                         'Weather_Daily_Rainfall': 'precipitation',
                         'Wind_Direction': 'wind_direction',
                         'Weather_Relative_Humidity': 'humidity',
                         'Wind_Speed':'wind_speed_faulty', # The measured wind speed data is insufficient
                         'Active_Energy_Delivered_Received': 'accumulated_energy_1', 
                         'Current_Phase_Average': 'current_phase_average_1', 
                         'Performance_Ratio': 'performance_ratio_1', 
                         'Active_Power': 'ac_power_1'}, inplace=True)

dkasc_25.rename(columns={'Active_Energy_Delivered_Received': 'accumulated_energy_2', 
                         'Current_Phase_Average': 'current_phase_average_2', 
                         'Performance_Ratio': 'performance_ratio_2', 
                         'Active_Power': 'ac_power_2'}, inplace=True)



#%% Collect wind data from PVGIS

# PVGIS data
poa_data_2016_to_2020, meta, inputs \
    = pvlib.iotools.get_pvgis_hourly(latitude=location.latitude, 
                                     longitude=location.longitude, 
                                     start=iotools_start, 
                                     end=iotools_end, 
                                     raddatabase='PVGIS-ERA5', 
                                     surface_tilt=surface_tilt, 
                                     surface_azimuth=surface_azimuth-180, # PVGIS har azimuth=0 som sør, mens pvlib har a=180 som sør
                                     url='https://re.jrc.ec.europa.eu/api/v5_2/')

# Rename columns
poa_data_2016_to_2020.rename(columns={'poa_global': 'G_tc',
                                      'poa_direct': 'G_bc',
                                      'poa_sky_diffuse': 'G_sky',
                                      'poa_ground_diffuse': 'G_ground'}, inplace=True)

# Calculate diffuse and total irradiance on the collector surface
poa_data_2016_to_2020['G_dc'] = poa_data_2016_to_2020['G_sky'] + poa_data_2016_to_2020['G_ground']
poa_data_2016_to_2020['G_tc'] = poa_data_2016_to_2020['G_dc'] + poa_data_2016_to_2020['G_bc']

# Read TMY data
tmy_year = pd.read_csv('alice_springs/tmy_alice_springs.csv', 
                       skiprows=16,     # Dataset contains 16 rows of explanation
                       nrows=8760,      # Reselution of one hour. 8760 hours in a year
                       usecols=['time(UTC)', 'T2m', 'G(h)', 'Gb(n)', 'Gd(h)', 'WS10m'],
                       index_col='time(UTC)')

# Change column names
tmy_year.rename(columns={'T2m': 'temp_air', 
                         'G(h)': 'G_th', 
                         'Gb(n)': 'G_b*', 
                         'Gd(h)': 'G_dh', 
                         'WS10m': 'wind_speed'}, inplace=True)

# Make dataframe for each year
tmy_2021 = tmy_year
tmy_2021.index = pd.date_range(start='2021-01-01 00:00',
                               periods=len(tmy_2021),
                               freq='h',
                               tz=location.tz)

tmy_2022 = tmy_year
tmy_2022.index = pd.date_range(start='2022-01-01 00:00',
                               periods=len(tmy_2022),
                               freq='h',
                               tz=location.tz)

tmy_2023 = tmy_year
tmy_2023.index = pd.date_range(start='2023-01-01 00:00',
                               periods=len(tmy_2023),
                               freq='h',
                               tz=location.tz)

# Make unified PVGIS and TMY dataframe
poa_data = pd.concat([poa_data_2016_to_2020, tmy_2021, tmy_2022, tmy_2023])

# Ensure that the time series has no holes
poa_data.index = pd.date_range(start='2016-01-01 00:00',
                                    periods=len(poa_data),
                                    freq='h',
                                    tz=location.tz)

# Start and stop dataset at wanted times
poa_data = poa_data[date_start:date_end]


#%% Make final dataframes and save as feather files

# Concatonate to one dataframe
dkasc_data = pd.concat([dkasc_24, dkasc_25])
dkasc_data = dkasc_data.loc[date_start:date_end]

# Resample to hourly, daily and monthly timescales
dkasc_data_hour = dkasc_data.resample('h').mean()
dkasc_data_hour['wind_speed'] = poa_data['wind_speed']

dkasc_data_maxhour = dkasc_data_hour.resample('d').max()

dkasc_data_month = dkasc_data.resample('m').mean()
dkasc_data_month['wind_speed'] = dkasc_data_hour['wind_speed'].resample('m').mean()

# Add time, month and year columns to make altair able to interpret data
dkasc_data['time'] = dkasc_data.index
dkasc_data['month'] = dkasc_data.index.month
dkasc_data['year'] = dkasc_data.index.year

dkasc_data_hour['time'] = dkasc_data_hour.index
dkasc_data_hour['month'] = dkasc_data_hour.index.month
dkasc_data_hour['year'] = dkasc_data_hour.index.year

dkasc_data_maxhour['time'] = dkasc_data_maxhour.index
dkasc_data_maxhour['month'] = dkasc_data_maxhour.index.month
dkasc_data_maxhour['year'] = dkasc_data_maxhour.index.year

dkasc_data_month['time'] = dkasc_data_month.index
dkasc_data_month['month'] = dkasc_data_month.index.month
dkasc_data_month['year'] = dkasc_data_month.index.year

# Save dataframes as feather format
# feather.write_feather(dkasc_data, f'{dkasc_path}\\feather\\dkasc_data')
feather.write_feather(dkasc_data_hour, 'data/dkasc_data_hour')
feather.write_feather(dkasc_data_maxhour, 'data/dkasc_data_maxhour')
# feather.write_feather(dkasc_data_month, f'{dkasc_path}\\feather\\dkasc_data_month')

print('Dataframes saved as feather format')