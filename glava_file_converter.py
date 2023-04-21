# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 10:37:30 2023

@author: johan
"""

import pandas as pd
import os
import pyarrow.feather as feather
import time

def read_glava_data(directory_path, system_folder):
    """
    Reads in Glava data from a given directory path and returns a Pandas DataFrame.

    Args:
        directory_path (str): Path to directory containing Glava data.
        system (str): Name of the folder containing the system Excel files

    Returns:
        pandas.DataFrame: DataFrame containing Glava data.
    """
    start_time = time.time()
    
    # Define system_path
    system_path = os.path.join(directory_path, system_folder)

    # Make an empty dataframe
    glava_dataframes = []

    # Iterate over files in the directory
    for filename in os.listdir(system_path):
        # Read Excel file, parse datetime column, and resample to minute frequency
        excel_file = pd.ExcelFile(os.path.join(system_path, filename))
        df_ptot = pd.read_excel(excel_file,
                                sheet_name='Totaleffekt',
                                parse_dates={'datetime': ['Tidpunkt']},
                                index_col='datetime').resample('min').median()
        df_ginn = pd.read_excel(excel_file,
                                sheet_name='Generella ingångar',
                                parse_dates={'datetime': ['Tidpunkt']},
                                index_col='datetime').resample('min').median()
        # Combine dictionary to a dataframe
        df_temp = pd.concat([df_ptot, df_ginn])
        # Append the resampled dataframe to the main dataframe
        glava_dataframes.append(df_temp)

        # Print status message
        print(f"{filename} added to the dataframe")
    
    glava_data = pd.concat(glava_dataframes)


    # Report elapsed time
    end_time = time.time()
    elapsed_time = round(end_time - start_time)
    print(f"It took {elapsed_time} seconds to read the {system_folder} Excel files")

    return glava_data

# Define file path
glava_path = os.path.join('C:', os.sep, 'Users', 'johan', 
                          'OneDrive', 'Dokumenter', 'NMBU', 'Master', 
                          'databehandling_og_modellering', 'glava')

# Use the function to collect data, then rename columns and store raw data files
glava_ABB = read_glava_data(glava_path, 'ABB')
glava_ABB.rename(columns={'Ptot (W)': 'ac_power_2',
                          'GI1': 'wind_direction',
                          'GI2': 'precipitation',
                          'GI3': 'Ukjent ABB 1',
                          'GI4': 'Ukjent ABB 2'}, inplace=True)
feather.write_feather(glava_ABB, f'{glava_path}\\feather\\glava_ABB')

# Eltek
glava_Eltek = read_glava_data(glava_path, 'Eltek')
glava_Eltek.rename(columns={'Ptot (W)': 'ac_power_Eltek',
                            'GI1': 'temp_air',
                            'GI2': 'humidity',
                            'GI3': 'barometric_pressure',
                            'GI4': 'wind_speed'}, inplace=True)
feather.write_feather(glava_Eltek, f'{glava_path}\\feather\\glava_Eltek')

# Laddstolpe
glava_laddstolpe = read_glava_data(glava_path, 'laddstolpe')
glava_laddstolpe.rename(columns={'Ptot (W)': 'active_power_laddstolpe',
                                 'GI1': 'G_th',
                                 'GI2': 'G_tc',
                                 'GI3': 'G_t_30_deg',
                                 'GI4': 'G_dh'}, inplace=True)
feather.write_feather(glava_laddstolpe, f'{glava_path}\\feather\\glava_laddstolpe')

# SMA
glava_SMA = read_glava_data(glava_path, 'SMA')
glava_SMA.rename(columns={'Ptot (W)': 'ac_power_1',
                          'GI1': 'G_bh',
                          'GI2': 'temp_tracker',
                          'GI3': 'G_t_90_deg',
                          'GI4': 'G_ground'}, inplace=True)
feather.write_feather(glava_SMA, f'{glava_path}\\feather\\glava_SMA')


#%% Make final dataframes and save as feather files

# Dataframe for all weather and power data
glava_data = pd.concat([glava_ABB, glava_SMA, glava_Eltek, glava_laddstolpe])

# Resample the dataframe to minute frequency
glava_data = glava_data.resample('min').median()
glava_data_hour = glava_data.resample('h').mean()
glava_data_maxhour = glava_data_hour.resample('d').max()
glava_data_month = glava_data.resample('m').mean()

# Add time, month and year columns to make altair able to interpret data
glava_data['time'] = glava_data.index
glava_data['month'] = glava_data.index.month
glava_data['year'] = glava_data.index.year

glava_data_hour['time'] = glava_data_hour.index
glava_data_hour['month'] = glava_data_hour.index.month
glava_data_hour['year'] = glava_data_hour.index.year

glava_data_maxhour['time'] = glava_data_maxhour.index
glava_data_maxhour['month'] = glava_data_maxhour.index.month
glava_data_maxhour['year'] = glava_data_maxhour.index.year

glava_data_month['time'] = glava_data_month.index
glava_data_month['month'] = glava_data_month.index.month
glava_data_month['year'] = glava_data_month.index.year

# Save files in feather format
# feather.write_feather(glava_data, f'{glava_path}\\feather\\glava_data')
feather.write_feather(glava_data_hour, 'data/glava_data_hour')
feather.write_feather(glava_data_maxhour, 'data/glava_data_maxhour')
# feather.write_feather(glava_data_month, f'{glava_path}\\feather\\glava_data_month')




#%% Old useless code


# Different function. Forgot the difference from the new one...
# def read_glava_data_old(directory_path, system_folder):
#     """
#     Reads in Glava data from a given directory path and returns a Pandas DataFrame.

#     Args:
#         directory_path (str): Path to directory containing Glava data.
#         system (str): Name of the folder containing the system Excel files

#     Returns:
#         pandas.DataFrame: DataFrame containing Glava data.
#     """
#     start_time = time.time()
    
#     # Define system_path
#     system_path = os.path.join(directory_path, system_folder)

#     # Make an empty dataframe
#     glava_dataframes = []

#     # Iterate over files in the directory
#     for filename in os.listdir(system_path):
#         # Read Excel file, parse datetime column, and resample to minute frequency
#         dict_temp = pd.read_excel(os.path.join(system_path, filename),
#                                 sheet_name=['Totaleffekt', 'Generella ingångar'],
#                                 parse_dates={'datetime': ['Tidpunkt']},
#                                 index_col='datetime')
#         # Combine dictionary to a dataframe and resample
#         df_temp = pd.concat(dict_temp.values()).resample('min').median()
#         # Append the resampled dataframe to the main dataframe
#         glava_dataframes.append(df_temp)

#         # Print status message
#         print(f"{filename} added to the dataframe")
    
#     glava_data = pd.concat(glava_dataframes)


#     # Report elapsed time
#     end_time = time.time()
#     elapsed_time = round(end_time - start_time)
#     print(f"It took {elapsed_time} seconds to read the {system_folder} Excel files")

#     return glava_data


# Using a smaller set of data to test function
# glava_ABB_temp = read_glava_data_test(glava_path, 'ABB_temp')
# glava_ABB_temp.rename(columns={'Ptot (W)': 'active_power_ABB',
#                           'GI1': 'wind_direction',
#                           'GI2': 'precipitation',
#                           'GI3': 'Ukjent ABB 1',
#                           'GI4': 'Ukjent ABB 2'}, inplace=True)