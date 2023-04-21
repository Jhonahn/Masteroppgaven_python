# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 09:45:16 2023

@author: johan
"""

import pyodbc
import pandas as pd
import os
import pyarrow.feather as feather
from pathlib import Path

def read_system_data(system_name, year, main_path):
    path = Path(f'{main_path}\\ms_access\\PVsoras{year}.accdb')
    conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};'
    with pyodbc.connect(conn_str) as conn:
        df_north = pd.read_sql(sql=f'select * from PVN{year}', con=conn, index_col='TIMESTAMP')
        df_south = pd.read_sql(sql=f'select * from PVS{year}', con=conn, index_col='TIMESTAMP')
    date_start = f'{year}-01-01 00:00'
    date_end = f'{year}-12-31 23:59'
    df_north = df_north[date_start:date_end]
    df_south = df_south[date_start:date_end]
    print(f'{system_name} data for {year} converted')
    return df_north, df_south

# Define main path
soras_path = os.path.join('C:', os.sep, 'Users', 'johan', 
                          'OneDrive', 'Dokumenter', 'NMBU', 'Master', 
                          'databehandling_og_modellering', 'soras')

# Import data for each year
system_names = ['PV_2018', 'PV_2019', 'PV_2020', 'PV_2021', 'PV_2022']
years = range(2018, 2023)
dfs_north, dfs_south = [], []
for system_name, year in zip(system_names, years):
    df_north, df_south = read_system_data(system_name, year, soras_path)
    dfs_north.append(df_north)
    dfs_south.append(df_south)

# Combine data into dataframes
soras_north = pd.concat(dfs_north)
soras_south = pd.concat(dfs_south)

# Keep the required data and rename columns
soras_north['dc_power_north'] = soras_north['Udc_N_Med'] * soras_north['Idc_N_Med']
soras_south['dc_power_south'] = soras_south['Udc_S_Med'] * soras_south['Idc_S_Med']

# Define conversion factor for DC power
modules_per_string = 12

# Scale DC power
soras_north['dc_power_north'] = soras_north['dc_power_north'] * modules_per_string
soras_south['dc_power_south'] = soras_south['dc_power_south'] * modules_per_string

# Drop unnecessary columns
soras_north = soras_north[['LT', 'GLOB', 'GLOB_PV', 'DIFF', 'BAL', 'UV', 
                           'IR', 'VH', 'VR', 'T_N_Med', 'dc_power_north', 
                           'Pac_N_Med', 'VA_N_Med', 'VAr_N_Med']]

soras_south = soras_south[['T_S_Med', 'dc_power_south', 
                           'VA_S_Med', 'Pac_S_Med']]

# Rename columns
soras_north.rename(columns={'LT': 'temp_air', 
                            'GLOB': 'G_th',
                            'GLOB_PV': 'G_tc',
                            'DIFF': 'G_dh',
                            'BAL': 'radiation_balance',
                            'UV': 'UV_radiation',
                            'IR': 'IR_radiation',
                            'VH': 'wind_speed',
                            'VR': 'wind_direction',
                            'T_N_Med': 'temp_module_1',
                            'Pac_N_Med': 'active_power_1',
                            'VA_N_Med': 'ac_power_1',
                            'VAr_N_Med': 'reactive_power_1'}, inplace=True)

soras_south.rename(columns={'T_S_Med': 'temp_module_2',
                            'Pac_S_Med': 'active_power_2',
                            'VA_S_Med': 'ac_power_2',
                            'VAr_S_Med': 'reactive_power_2'}, inplace=True)

#%% Make final dataframes and save as feather files

# Concatonate datasets
soras_data = pd.concat([soras_north, soras_south])

# Resample the datasets
soras_data_hour = soras_data.resample('h').mean()
soras_data_maxhour = soras_data_hour.resample('d').max()
soras_data_month = soras_data.resample('m').mean()

# Add time, month and year columns to make altair able to interpret data
soras_data['time'] = soras_data.index
soras_data['month'] = soras_data.index.month
soras_data['year'] = soras_data.index.year

soras_data_hour['time'] = soras_data_hour.index
soras_data_hour['month'] = soras_data_hour.index.month
soras_data_hour['year'] = soras_data_hour.index.year

soras_data_maxhour['time'] = soras_data_maxhour.index
soras_data_maxhour['month'] = soras_data_maxhour.index.month
soras_data_maxhour['year'] = soras_data_maxhour.index.year

soras_data_month['time'] = soras_data_month.index
soras_data_month['month'] = soras_data_month.index.month
soras_data_month['year'] = soras_data_month.index.year

# Save dataframes as feather format
feather.write_feather(soras_data, f'{soras_path}\\feather\\soras_data')
feather.write_feather(soras_data_hour, f'{soras_path}\\feather\\soras_data_hour')
feather.write_feather(soras_data_maxhour, f'{soras_path}\\feather\\soras_data_maxhour')
feather.write_feather(soras_data_month, f'{soras_path}\\feather\\soras_data_month')

print('Dataframes saved as feather format')
