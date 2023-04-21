# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 09:57:45 2023

@author: johan
"""

import pyarrow.feather as feather
import pandas as pd
import os

# Define paths
soras_path = os.path.join('C:', os.sep, 'Users', 'johan', 
                          'OneDrive', 'Dokumenter', 'NMBU', 'Master', 
                          'databehandling_og_modellering', 'soras')

dkasc_path = os.path.join('C:', os.sep, 'Users', 'johan', 
                          'OneDrive', 'Dokumenter', 'NMBU', 'Master', 
                          'databehandling_og_modellering', 'alice_springs')

glava_path = os.path.join('C:', os.sep, 'Users', 'johan', 
                          'OneDrive', 'Dokumenter', 'NMBU', 'Master', 
                          'databehandling_og_modellering', 'glava')


# Collect datasets
soras_data = feather.read_feather(f'{soras_path}\\feather\\soras_data')
soras_data_hour = feather.read_feather(f'{soras_path}\\feather\\soras_data_hour')
soras_data_maxhour = feather.read_feather(f'{soras_path}\\feather\\soras_data_maxhour')
soras_data_month = feather.read_feather(f'{soras_path}\\feather\\soras_data_month')


dkasc_data = feather.read_feather(f'{dkasc_path}\\feather\\dkasc_data')
dkasc_data_hour = feather.read_feather(f'{dkasc_path}\\feather\\dkasc_data_hour')
dkasc_data_maxhour = feather.read_feather(f'{dkasc_path}\\feather\\dkasc_data_maxhour')
dkasc_data_month = feather.read_feather(f'{dkasc_path}\\feather\\dkasc_data_month')


glava_data = feather.read_feather(f'{glava_path}\\feather\\glava_data')
glava_data_hour = feather.read_feather(f'{glava_path}\\feather\\glava_data_hour')
glava_data_maxhour = feather.read_feather(f'{glava_path}\\feather\\glava_data_maxhour')
glava_data_month = feather.read_feather(f'{glava_path}\\feather\\glava_data_month')


# Rename column
soras_data.rename(columns={'apparent_power_north': 'ac_power_1',
                           'apparent_power_south': 'ac_power_2'}, inplace=True)
soras_data_hour.rename(columns={'apparent_power_north': 'ac_power_1',
                                'apparent_power_south': 'ac_power_2'}, inplace=True)
soras_data_maxhour.rename(columns={'apparent_power_north': 'ac_power_1',
                                   'apparent_power_south': 'ac_power_2'}, inplace=True)
soras_data_month.rename(columns={'apparent_power_north': 'ac_power_1',
                                 'apparent_power_south': 'ac_power_2'}, inplace=True)


dkasc_data.rename(columns={'active_power_24': 'ac_power_1',
                           'active_power_25': 'ac_power_2'}, inplace=True)
dkasc_data_hour.rename(columns={'active_power_24': 'ac_power_1',
                                'active_power_25': 'ac_power_2'}, inplace=True)
dkasc_data_maxhour.rename(columns={'active_power_24': 'ac_power_1',
                                   'active_power_25': 'ac_power_2'}, inplace=True)
dkasc_data_month.rename(columns={'active_power_24': 'ac_power_1',
                                 'active_power_25': 'ac_power_2'}, inplace=True)


glava_data.rename(columns={'active_power_SMA': 'ac_power_1',
                           'active_power_ABB': 'ac_power_2'}, inplace=True)
glava_data_hour.rename(columns={'active_power_SMA': 'ac_power_1',
                                'active_power_ABB': 'ac_power_2'}, inplace=True)
glava_data_maxhour.rename(columns={'active_power_SMA': 'ac_power_1',
                                   'active_power_ABB': 'ac_power_2'}, inplace=True)
glava_data_month.rename(columns={'active_power_SMA': 'ac_power_1',
                                 'active_power_ABB': 'ac_power_2'}, inplace=True)











# Save dataframes as feather format
feather.write_feather(soras_data, f'{soras_path}\\feather\\soras_data')
feather.write_feather(soras_data_hour, f'{soras_path}\\feather\\soras_data_hour')
feather.write_feather(soras_data_maxhour, f'{soras_path}\\feather\\soras_data_maxhour')
feather.write_feather(soras_data_month, f'{soras_path}\\feather\\soras_data_month')

feather.write_feather(dkasc_data, f'{dkasc_path}\\feather\\dkasc_data')
feather.write_feather(dkasc_data_hour, f'{dkasc_path}\\feather\\dkasc_data_hour')
feather.write_feather(dkasc_data_maxhour, f'{dkasc_path}\\feather\\dkasc_data_maxhour')
feather.write_feather(dkasc_data_month, f'{dkasc_path}\\feather\\dkasc_data_month')

feather.write_feather(glava_data, f'{glava_path}\\feather\\glava_data')
feather.write_feather(glava_data_hour, f'{glava_path}\\feather\\glava_data_hour')
feather.write_feather(glava_data_maxhour, f'{glava_path}\\feather\\glava_data_maxhour')
feather.write_feather(glava_data_month, f'{glava_path}\\feather\\glava_data_month')