# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 11:46:14 2023

@author: UeliSchilt
"""

import pandas as pd
# import matplotlib.pylab as plt
import numpy as np
import sys
import os
import math
# import dem_techs
# from meteostat import Point, Hourly, Daily
from datetime import datetime
from district_energy_model import dem_constants as C

# cdir = os.getcwd()
# print(cdir)
# wdir = r'C:\Users\UeliSchilt\OneDrive - Hochschule Luzern\00_GitLab\district_energy_model\src'
# os.chdir(wdir)
# print(os.getcwd())


import yaml
from pathlib import Path

from typing import List, Dict, Any


def update_scen_techs_from_config(scen_techs: Dict[str, Any],
                                  config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a nested scen_techs dict with values from config_dict.

    - Only replaces values where the full key path exists in scen_techs.
    - If a key or downstream key in config_dict does not exist in scen_techs,
      prints a warning.
    - If an upstream key exists, only the specified downstream keys are updated;
      other downstream keys in scen_techs are kept as-is.

    Parameters
    ----------
    scen_techs : dict
        Original nested configuration, modified in-place and also returned.
    config_dict : dict
        Nested configuration with override values.

    Returns
    -------
    dict
        The updated scen_techs (same object, for convenience).
    """

    def _update_recursive(scen_node: Dict[str, Any],
                          cfg_node: Dict[str, Any],
                          path: List[str]) -> None:
        for key, cfg_value in cfg_node.items():
            new_path = path + [str(key)]
            path_str = " -> ".join(new_path)

            if isinstance(cfg_value, dict):
                # Expect a nested dict in scen_node at the same key
                if key not in scen_node:
                    print(f"Warning: key path '{path_str}' from config_dict not found in scen_techs")
                    continue
                if not isinstance(scen_node[key], dict):
                    print(
                        f"Warning: key path '{path_str}' in scen_techs is not a dict; "
                        f"cannot apply nested overrides from config_dict"
                    )
                    continue

                _update_recursive(scen_node[key], cfg_value, new_path)

            else:
                # Leaf value: only update if the key exists in scen_node
                if key not in scen_node:
                    print(f"Warning: key path '{path_str}' from config_dict not found in scen_techs")
                else:
                    scen_node[key] = cfg_value

    _update_recursive(scen_techs, config_dict, [])
    return scen_techs


def update_scen_techs_from_yaml(input_files_dir, scen_techs):
    """
    Update entries in scen_techs based on YAML files in input_files_dir.

    Behaviour:
    1) If a file named 'technologies.yaml' (or .yml) exists, its top-level keys are
       interpreted as technology names (i.e., top keys in scen_techs). For each such
       key, only the listed subkeys are replaced/added in scen_techs[top_key].
    2) Individual files named after a top-level key in scen_techs (e.g., 'simulation.yaml')
       are then applied, again only replacing/adding the listed subkeys in
       scen_techs[top_key]. These per-technology files override values from 'technologies.yaml'.

    Parameters
    ----------
    input_files_dir : str or Path
        Directory containing the YAML files.
    scen_techs : dict
        Dictionary to update in-place.

    Returns
    -------
    scen_techs : dict
        Updated dictionary (same object).
    """

    def deep_merge(dst, src):
        """Recursively merge src into dst."""
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                deep_merge(dst[k], v)
            else:
                dst[k] = v

    input_dir = Path(input_files_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")

    # 1) Apply 'technologies.yaml' (or .yml) first, if present.
    for techs_filename in ("technologies.yaml", "technologies.yml"):
        techs_path = input_dir / techs_filename
        if techs_path.exists():
            with open(techs_path, "r", encoding="utf-8") as f:
                technologies_content = yaml.safe_load(f) or {}
            if not isinstance(technologies_content, dict):
                raise ValueError(
                    f"YAML file {techs_path.name} must contain a dictionary at top level."
                )
            # Each top-level key acts like a per-technology file; merge into scen_techs[top_key].
            for top_key, subcontent in technologies_content.items():
                if not isinstance(subcontent, dict):
                    raise ValueError(
                        f"In {techs_path.name}, top-level key '{top_key}' must map to a dictionary."
                    )
                if top_key not in scen_techs or not isinstance(scen_techs.get(top_key), dict):
                    scen_techs[top_key] = {}
                deep_merge(scen_techs[top_key], subcontent)
            break  # Only one of .yaml/.yml is needed

    # 2) Apply individual per-technology files (override technologies.yaml where overlapping).
    for file in input_dir.glob("*.y*ml"):
        # Skip the technologies file(s) - already handled
        if file.name in ("technologies.yaml", "technologies.yml"):
            continue

        top_key = file.stem
        with open(file, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f) or {}

        if not isinstance(content, dict):
            raise ValueError(f"YAML file {file.name} must contain a dictionary at top level.")

        if top_key not in scen_techs or not isinstance(scen_techs.get(top_key), dict):
            scen_techs[top_key] = {}

        deep_merge(scen_techs[top_key], content)

    return scen_techs


# def update_scen_techs_from_yaml(input_files_dir, scen_techs):
#     """
#     Update entries in scen_techs based on YAML files in input_files_dir.
    
#     Each YAML file must be named after a top-level key in scen_techs
#     (e.g., 'heat_pump.yaml'). If the file exists, only the listed subkeys
#     are replaced or added in scen_techs[top_key].
    
#     Parameters
#     ----------
#     input_files_dir : str or Path
#         Directory containing the YAML files.
#     scen_techs : dict
#         Dictionary to update in-place.
    
#     Returns
#     -------
#     scen_techs : dict
#         Updated dictionary (same object).
#     """

#     def deep_merge(dst, src):
#         """Recursively merge src into dst."""
#         for k, v in src.items():
#             if isinstance(v, dict) and isinstance(dst.get(k), dict):
#                 deep_merge(dst[k], v)
#             else:
#                 dst[k] = v

#     input_dir = Path(input_files_dir)
#     if not input_dir.exists():
#         raise FileNotFoundError(f"Directory not found: {input_dir}")

#     for file in input_dir.glob("*.y*ml"):
#         top_key = file.stem
#         with open(file, "r", encoding="utf-8") as f:
#             content = yaml.safe_load(f) or {}

#         if not isinstance(content, dict):
#             raise ValueError(f"YAML file {file.name} must contain a dictionary at top level.")

#         if top_key not in scen_techs:
#             scen_techs[top_key] = {}

#         deep_merge(scen_techs[top_key], content)

#     return scen_techs


def update_df_results(energy_demand, supply, tech_instances, df_results):
    
    # Setting all values to 0
    df_results.loc[:, :] = 0
    
    # Update demand data:
    df_results = energy_demand.update_df_results(df_results)
    
    # Update supply data:
    df_results = supply.update_df_results(df_results)
    
    # Update tech data:
    for tech_name, tech_instance in tech_instances.items():
        df_results = tech_instance.update_df_results(df_results)
        
    # Compute total CO2 emissions and add column (v_CO2_tot):
    co2_columns = [col for col in df_results.columns if col.startswith('v_co2') or col.startswith('m_co2')]
    df_results['v_co2_tot'] = df_results[co2_columns].sum(axis=1)

        
def reduce_timeframes(energy_demand, supply, tech_instances, n_days):
    
    # Update demand data:
    energy_demand.reduce_timeframe(n_days)
    
    # Update supply data:
    supply.reduce_timeframe(n_days)
    
    # Update tech data:
    for tech_name, tech_instance in tech_instances.items():
         tech_instance.reduce_timeframe(n_days)


# def energy_balance_test(value_1, value_2, description, diff_accepted = 0.01):
    
#     """
#     Compares two energy values that should be equal. Raises an exception if the
#     difference between the two values is too large.
    
#     Parameters
#     ----------
#     value_1 : float
#         Energy value 1 to be compared (kWh).
#     value_2 : float
#         Energy value 2 to be compared (kWh).
#     description : string
#         Description of technology / energy type / ... (used for error message).
#     diff_accepted : float
#         Accepted error due to rounding / decimals / ... (kWh) (e.g. 0.01)

#     Returns
#     -------
#     n/a
#     """
            
#     diff = abs(value_1 - value_2)
            
#     if diff > diff_accepted:
#         print(f"Energy balance test for {description} not successful!")
#         print(f"Energy value 1 (kWh): {value_1}")
#         print(f"Energy value 2 (kWh): {value_2}")
#         print(f"Difference (kWh): {diff}")
#         raise Exception(f"{description} energy balance is not fulfilled!")
        

# def energy_balance_df_test(df_column_1, df_column_2, description, diff_accepted = 0.01):
    
#     """
#     Compares two dataframe columns containing energy values that should be
#     equal. Raises an exception if the difference betweentwo values is too large.
    
#     Parameters
#     ----------
#     df_column_1 : pandas dataframe column
#         Dataframe column 1 to be compared (kWh).
#     df_column_2 : pandas dataframe column
#         Dataframe column 2 to be compared (kWh).
#     description : string
#         Description of technology / energy type / ... (used for error message).
#     diff_accepted : float
#         Accepted error due to rounding / decimals / ... (kWh) (e.g. 0.01)

#     Returns
#     -------
#     n/a
#     """
            
#     df_diff = abs(df_column_1 - df_column_2)
    
#     max_diff = df_diff.max()
            
#     if max_diff > diff_accepted:
#         print(f"Energy balance test for {description} not successful!")
#         print(f"Max. difference (kWh): {max_diff}")
#         raise Exception(f"{description} energy balance is not fulfilled!")


# def electricity_balance_test(scen_techs,
#                              df_scen,
#                              optimisation=False,
#                              diff_accepted = 1e-5,
#                              diff_sum_accepted = 0.01
#                              ):
    
#     """
#     Tests if the overall energy balance for electricity is fullfilled, by
#     comparing generation to consumption.
    
#     Parameters
#     ----------
#     scen_techs : dictionary
#         Dictionary containing info about technologies.
#     df_scen : pandas dataframe
#         Dataframe with resulting hourly values.
#     optimisation : bool
#         Must be set to True if the test is applied after an optimisation. This
#         is due to the calculation of the remaining PV potential, as the solar
#         thermal is also included in the potential in this case (not the case
#         in the base scenario).
#     diff_accepted : float
#         Accepted error due to rounding / decimals / ... for individual values
#         in timeseries (e.g. 0.00001).
#     diff_sum_accepted : float
#         Accepted error due to rounding / decimals / ... for sum of all values
#         in timeseries (e.g. 0.01).

#     Returns
#     -------
#     n/a
#     """
    
#     #--------------------------------------------------------------------------
#     # Check timeseries:
    

    # electricity_consumption = df_scen['d_e'] + df_scen['u_e_wgu']

    
#     electricity_generation = (df_scen['v_e_pv_cons']
#                               + df_scen['m_e']
#                               )
    
#     electricity_demand_split = (df_scen['d_e_h'] # for heating demand
#                                 + df_scen['d_e_hh']  # for household demand
#                                 )
    
#     electricity_for_heating = df_scen['d_e_h']
    
#     electricity_for_heating_split = (df_scen['u_e_hp']
#                                      + df_scen['u_e_eh']
#                                      )
    
#     pv_generation = df_scen['v_e_pv']
    
#     pv_generation_split = (df_scen['v_e_pv_cons']
#                            + df_scen['v_e_pv_exp']
#                            )
    
#     total_import = df_scen['m_e']
    
#     total_import_split = (df_scen['m_e_ch']
#                           + df_scen['m_e_cbimport']
#                           )
    
#     swiss_import = df_scen['m_e_ch']
    
#     swiss_import_split = (df_scen['m_e_ch_hydro']
#                           + df_scen['m_e_ch_nuclear']
#                           + df_scen['m_e_ch_conventional_chp']
#                           + df_scen['m_e_ch_renewable_chp']
#                           + df_scen['m_e_ch_renewable_other']
#                           )
    
#     # Convert solar thermal to equivalent solar pv yield:
#     tmp_pv_equi = dem_techs.SolarPV.convert_thermal_to_pv(
#         df_thermal_kWh=df_scen['v_h_solar'],
#         eta_pv=scen_techs['solar_pv']['eta_overall'],
#         eta_thermal=scen_techs['solar_thermal']['eta_overall']
#         )
    
#     if optimisation:
#         pv_potential_and_installed = (
#             tmp_pv_equi                 # TEMPORARY FIX!!! Wie sollen wir Solarthermie behandeln?                
#             + df_scen['v_e_pv']
#             + df_scen['v_e_pv_pot_add_remain']
#             )
#     else:
#         pv_potential_and_installed = (
#             0# tmp_pv_equi                 # TEMPORARY FIX!!! Wie sollen wir Solarthermie behandeln?                
#             + df_scen['v_e_pv']
#             + df_scen['v_e_pv_pot_add_remain']
#             )
    
#     pv_total_potential = df_scen['v_e_pv_pot_tot'] # installed and additional potential
    
#     # abc = max(tmp_pv_equi)
#     # print(f"tmp_pv_equi max: {abc}")
#     # HIER IST DER FEHLER!!! tmp_pv_equi ist nicht Teil von pv_total_potential

    
#     diff_1 = abs(electricity_consumption - electricity_generation)    
#     max_diff_1 = diff_1.max()
    
#     diff_2 = abs(electricity_consumption - electricity_demand_split)
#     max_diff_2 = diff_2.max()
    
#     diff_3 = abs(electricity_for_heating - electricity_for_heating_split)
#     max_diff_3 = diff_3.max()
    
#     diff_4 = abs(pv_generation - pv_generation_split)
#     max_diff_4 = diff_4.max()
    
#     diff_5 = abs(total_import - total_import_split)
#     max_diff_5 = diff_5.max()
    
#     diff_6 = abs(swiss_import - swiss_import_split)
#     max_diff_6 = diff_6.max()
    
#     diff_7 = abs(pv_potential_and_installed - pv_total_potential)
#     max_diff_7 = diff_7.max()
    
#     if max_diff_1 > diff_accepted:
#         print("Electricity balance (1) is not fulfilled!")
#         print(f"Max. difference (kWh): {max_diff_1}")
#         raise Exception("Electricity balance (timeseries) is not fulfilled!(1)")
        
#     if max_diff_2 > diff_accepted:
#         print("Electricity balance (2) is not fulfilled!")
#         print(f"Max. difference (kWh): {max_diff_2}")
#         raise Exception("Electricity balance (timeseries) is not fulfilled!(2)")
        
#     if max_diff_3 > diff_accepted:
#         print("Electricity balance (3) is not fulfilled!")
#         print(f"Max. difference (kWh): {max_diff_3}")
#         raise Exception("Electricity balance (timeseries) is not fulfilled!(3)")
        
#     if max_diff_4 > diff_accepted:
#         print("Electricity balance (4) is not fulfilled!")
#         print(f"Max. difference (kWh): {max_diff_4}")
#         raise Exception("Electricity balance (timeseries) is not fulfilled!(4)")
        
#     if max_diff_5 > diff_accepted:
#         print("Electricity balance (5) is not fulfilled!")
#         print(f"Max. difference (kWh): {max_diff_5}")
#         raise Exception("Electricity balance (timeseries) is not fulfilled!(5)")
        
#     if max_diff_6 > diff_accepted:
#         print("Electricity balance (6) is not fulfilled!")
#         print(f"Max. difference (kWh): {max_diff_6}")
#         raise Exception("Electricity balance (timeseries) is not fulfilled!(6)")
        
#     if max_diff_7 > diff_accepted:
#         print("Electricity balance (7) is not fulfilled!")
#         print(f"Max. difference (kWh): {max_diff_7}")
#         raise Exception("Electricity balance (timeseries) is not fulfilled!(7)")
    
#     #--------------------------------------------------------------------------
#     # Check sums:
    
#     electricity_consumption_sum = electricity_consumption.sum()
#     electricity_generation_sum = electricity_generation.sum()
#     electricity_demand_split_sum = electricity_demand_split.sum()    
#     electricity_for_heating_sum = electricity_for_heating.sum()    
#     electricity_for_heating_split_sum = electricity_for_heating_split.sum()  
#     pv_generation_sum = pv_generation.sum()
#     pv_generation_split_sum = pv_generation_split.sum()    
#     total_import_sum = total_import.sum()
#     total_import_split_sum = total_import_split.sum()
#     swiss_import_sum = swiss_import.sum()    
#     swiss_import_split_sum = swiss_import_split.sum()
#     pv_potential_and_installed_sum = pv_potential_and_installed.sum()
#     pv_total_potential_sum = pv_total_potential.sum()
    
#     diff_sum_1 = abs(electricity_consumption_sum - electricity_generation_sum)
#     diff_sum_2 = abs(electricity_consumption_sum - electricity_demand_split_sum)
#     diff_sum_3 = abs(electricity_for_heating_sum - electricity_for_heating_split_sum)
#     diff_sum_4 = abs(pv_generation_sum - pv_generation_split_sum)
#     diff_sum_5 = abs(total_import_sum - total_import_split_sum)
#     diff_sum_6 = abs(swiss_import_sum - swiss_import_split_sum)
#     diff_sum_7 = abs(pv_potential_and_installed_sum - pv_total_potential_sum)
    
#     if diff_sum_1 > diff_sum_accepted:
#         print("Electricity balance (1) is not fulfilled!")
#         print(f"Sum difference (kWh): {diff_sum_1}")
#         raise Exception("Electricity balance (sum) is not fulfilled!")
        
#     if diff_sum_2 > diff_sum_accepted:
#         print("Electricity balance (2) is not fulfilled!")
#         print(f"Sum difference (kWh): {diff_sum_2}")
#         raise Exception("Electricity balance (sum) is not fulfilled!")
        
#     if diff_sum_3 > diff_sum_accepted:
#         print("Electricity balance (3) is not fulfilled!")
#         print(f"Sum difference (kWh): {diff_sum_3}")
#         raise Exception("Electricity balance (sum) is not fulfilled!")
        
#     if diff_sum_4 > diff_sum_accepted:
#         print("Electricity balance (4) is not fulfilled!")
#         print(f"Sum difference (kWh): {diff_sum_4}")
#         raise Exception("Electricity balance (sum) is not fulfilled!")
        
#     if diff_sum_5 > diff_sum_accepted:
#         print("Electricity balance (5) is not fulfilled!")
#         print(f"Sum difference (kWh): {diff_sum_5}")
#         raise Exception("Electricity balance (sum) is not fulfilled!")
        
#     if diff_sum_6 > diff_sum_accepted:
#         print("Electricity balance (6) is not fulfilled!")
#         print(f"Sum difference (kWh): {diff_sum_6}")
#         raise Exception("Electricity balance (sum) is not fulfilled!")
        
#     if diff_sum_7 > diff_sum_accepted:
#         print("Electricity balance (7) is not fulfilled!")
#         print(f"Sum difference (kWh): {diff_sum_7}")
#         raise Exception("Electricity balance (sum) is not fulfilled!")
        

# def heat_balance_test(df_scen,
#                       diff_accepted = 1e-5,
#                       diff_sum_accepted = 0.1
#                       ):
    
#     """
#     Tests if the overall energy balance for heat is fullfilled, by comparing
#     generation to consumption.
    
#     Parameters
#     ----------
#     df_scen : pandas dataframe
#         Dataframe with resulting hourly values.
#     diff_accepted : float
#         Accepted error due to rounding / decimals / ... for individual values
#         in timeseries (e.g. 0.00001).
#     diff_sum_accepted : float
#         Accepted error due to rounding / decimals / ... for sum of all values
#         in timeseries (e.g. 0.01).

#     Returns
#     -------
#     n/a
#     """
    
#     heat_consumption = (df_scen['d_h'] +
#                         df_scen['u_h_tes']
#                         )
    
#     heat_generation = (df_scen['v_h_hp'] +
#                        df_scen['v_h_eh'] +
#                        df_scen['v_h_ob'] +
#                        df_scen['v_h_gb'] +
#                        df_scen['v_h_wb'] +
#                        df_scen['v_h_dh'] +
#                        df_scen['v_h_solar'] +
#                        df_scen['v_h_other'] +
#                        df_scen['v_h_tes']
#                        )
    
#     diff = abs(heat_consumption - heat_generation)
    
#     max_diff = diff.max()
    
#     if max_diff > diff_accepted:
#         print("Overall heat balance is not fulfilled!")
#         print(f"Max. difference (kWh): {max_diff}")
#         raise Exception("Heat balance (timeseries) is not fulfilled!")
    
#     heat_consumption_sum = heat_consumption.sum()
    
#     heat_generation_sum = heat_generation.sum()
    
#     diff_sum = abs(heat_consumption_sum - heat_generation_sum)
    
#     if diff_sum > diff_sum_accepted:
#         print("Overall heat balance is not fulfilled!")
#         print(f"Sum difference (kWh): {diff_sum}")
#         raise Exception("Heat balance (sum) is not fulfilled!")



def positive_values_test(df_values, description, error_accepted=-1e-3):
    
    """
    Checks if all values in a dataframe column are positive. Raises an
    exception if one or more values are negative.
    
    Parameters
    ----------
    df_values : pandas dataframe column
        Values to be checked.
    description : string
        Description of technology / energy type / ... (used for error message).
    error_accepted : float
        Accepted error (e.g. a value of -3e-14 counts as 0).

    Returns
    -------
    n/a
    """
            
    negative_check = (df_values < error_accepted).any()
            
    if negative_check == True:
        print(f"Positive value test for {description} not successful!")
        print(f"Min. value: {df_values.min()}")
        raise Exception(f"{description} contains negative values!")
        

# def positive_values_test_df(df_values, description, error_accepted=C.NEG_ACC):
def positive_values_test_df(
        df_values,
        description,
        error_accepted=-0.1,
        exempted_columns=[],
        ):
    
    """
    Checks if all values in a dataframe are positive. Raises an
    exception if one or more values are negative and prints the column headers
    of columns containing negative values.
    
    Parameters
    ----------
    df_values : pandas dataframe (can contain multiple columns)
        Values to be checked.
    description : string
        Description of technology / energy type / ... (used for error message).
    error_accepted : float
        Accepted error (e.g. a value of -3e-14 counts as 0).
    exempted_columns : list of strings
        List containing the column header that are exempted from the test (i.e.
        they can contain negative values.)

    Returns
    -------
    n/a
    """
    
    # Initialize an empty list to store column headers with negative values
    negative_columns = []
    
    # Iterate through each column in the DataFrame
    for column in df_values.columns:
        if column in exempted_columns:
            pass
        
        elif (df_values[column] < error_accepted).any():
        # Check if any value in the column is negative
            negative_columns.append(column)
     
    if len(negative_columns) > 0:
        print(f"Positive value test for {description} not successful!")
        raise Exception(f"{description} contains negative values in the following columns: {negative_columns}")
    

def create_results_directory(arg_path, arg_results_dir_name):
    
    """
    Creates a new directory and returns the path to the directory.
    """
    
    arg_path = arg_path + '\\'
    
    tmp_i = 0
    tmp_results_dir = arg_results_dir_name
    
    while tmp_i < 10000:
        if os.path.isdir(arg_path + tmp_results_dir) == True:
            # directory already exists
            tmp_results_dir = arg_results_dir_name + ' (' +str(tmp_i+1) + ')'
            tmp_i += 1
            
        else:
            os.mkdir(arg_path + tmp_results_dir) # Es wir ein neuer Ordner erzeugt.
            break
        
    return arg_path + tmp_results_dir


def save_values_to_txt(arg_results_dir, arg_filename, arg_dict_data):
    
    """
    Writes values with respective keys to a .txt file and stores it in
    arg_results_dir directory.
    """
    
    #dictionary = dict(zip(arg_keys_list, arg_values_list))
    dictionary = arg_dict_data
    
    file = arg_results_dir + '/' + arg_filename
    
    with open(file, 'w') as f: 
        for key, value in dictionary.items():
            f.write('%s: %s\n' % (key, value))
     

def input_data_to_file(arg_results_dir, arg_filename, arg_input_data_list):
    
    # OBSOLETE (REPLACED BY input_to_file() in dem_helper.py)
    
    """
    Writes inputs values that have been saved in a list to a file as a
    dataframe and stores it in arg_results_dir directory.
    
    Parameters
    ----------
    arg_results_dir: string
        Path to directory where results shall be stored (e.g. 'model/results')
    arg_filename: string
        Name of file name, incl. extension (will be created) (e.g. 'data.txt')
    arg_input_data_list: list
        List containing input data. Each entry of the list is a list of the
        following form: ['parameter', parameter_value, 'description']

    Returns
    -------
    n/a
    """
    
    df = pd.DataFrame(arg_input_data_list, columns=['parameter','value','description'])
    
    if arg_results_dir == '':
        file = arg_filename
    else:
        file = arg_results_dir + '/' + arg_filename
    
    df.to_csv(file)


def compute_hp_input(arg_v_h_hp, arg_cop):

    
    """
    Computes the share of electricity and environmental energy input of the
    heat pump based on the thermal output using a fixed cop.
    
    Parameters
    ----------
    arg_v_h_hp : float
        Thermal output of heat pump [kWh].
    arg_cop : float
        Fixed Coefficient Of Performance (COP) [-]. 

    Returns
    -------
    list
        a list of length=2 with the input energy.
        Item 0: electricity input [kWh]
        Item 1: environmental input [kWh]
    """
    
    '''
    TO BE ADDED:
        - Temperature dependent COP
    '''
    
    u_e_hp = arg_v_h_hp/arg_cop # [kWh] electricity input to heat pump
    u_env_hp = arg_v_h_hp - u_e_hp # [kWh] environmental input (air, water, ground) to hp
    
    return [u_e_hp, u_env_hp]


def d_e_hr_split(arg_d_e_hr, arg_d_h_e_hr):
    
    
    """
    Splits the electricity profile in two parts: direct and heating. Direct part
    is used for electric appliances directly (e.g. lighting, ...).
    
    Parameters
    ----------
    arg_d_e_hr : pandas dataseries (e.g. column of a dataframe)
        Electricity load profile (total, incl. hp etc...) [kWh].
    arg_d_h_e_hr : pandas dataseries (e.g. column of a dataframe)
        Electricity load profile for heating (hp, eh, ...) [kWh]. 

    Returns
    -------
    list
        List with direct electricity load profile [kWh].
    """
    if len(arg_d_e_hr) == len(arg_d_h_e_hr):
        df_d_e_direct_hr = arg_d_e_hr - arg_d_h_e_hr
    
    else:
        sys.exit("Error in d_e_hr_split(): input arguments must be of same length!")
    
    list_d_e_direct_hr = df_d_e_direct_hr.tolist()
    
    return list_d_e_direct_hr


def distance_between_coord(lat1, lon1, lat2, lon2):
    
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)
    
    """
    Calculates the distance between two coordinates in decimal degrees
    using the Haversine formula.
    
    Parameters
    ----------
    lat1: float
        latitude of location 1 as decimal number (e.g. 47.556)
    lon1: float
        longitude of location 1 as decimal number
    lat2: float
        latitude of location 2 as decimal number (e.g. 47.556)
    lon2: float
        longitude of location 2 as decimal number

    Returns
    -------
    float
        distance between to coordinate points [km].
    """
    
    R = 6371  # radius of the earth in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # return distance in km
    dist = R*c
    
    return dist


def check_tech_for_scenario(techs, scenario, scen_techs):
    """
    Raise a ValueError if a specific technology required for a scenario is not
    deployed.

    Parameters
    ----------
    techs : list of str
        List with names of required technologies as found in scen_techs
        (e.g. ['heat_pump','solar_pv']).
    scenario : str
        Name of scenario as found in scen_techs (e.g. 'pv_integration').
    scen_techs : dictionary
        Dictionary containing info about technologies. Input to
        dem.DistrictEnergyModel.generate_scenario().

    Raises
    ------
    ValueError
        If required technology is not deployed, a ValueError is raised.

    Returns
    -------
    None.

    """
    
    for tech in techs:
    
        if scen_techs[tech]['deployment'] == False:
            
            printout = (
                f"'{scenario}' scenario could not be computed "
                f"because scen_techs['{tech}']['deployment'] = False. "
                "Change to 'True' in order to "
                "compute this scenario.\n"
                )
            
            raise ValueError(printout)


def multi_objective_weights(steps):
    """
    Return weights for two objectives in a multi-objective optimisation, used
    for generating a pareto front. The weights sweep from 1.0 to 0.0 and vice
    versa.

    Parameters
    ----------
    steps : int
        Number of steps to sweep through the weights. The first weight is not
        counted as a step. Example: 2 steps equates to weights [0.0, 0.5, 1.0]

    Returns
    -------
    obj_1_steps : list
        List of weights for objective 1, sweeping from 1.0 to 0.0.
    obj_2_steps : list
        List of weight for objective 2, sweeping from 0.0 to 1.0.

    """
    
    multi_obj_steps = steps
    
    obj_1_steps = []
    obj_2_steps = []

    # Compute number of optimisations runs:

    stepsize = 1.0/multi_obj_steps

    # Initialise objective weights:
    obj_1_weight = 1.0
    obj_2_weight = 0.0

    for i in range(multi_obj_steps + 1):
        
        if i < multi_obj_steps:
            # Update weights:
            obj_1_weight = 1.0 - i*stepsize
            obj_2_weight = 1 - obj_1_weight
        elif i == multi_obj_steps:
            # Assign last step to avoid rounding errors:
            obj_1_weight = 0.0
            obj_2_weight = 1.0
            
        obj_1_weight = round(obj_1_weight, 4)
        obj_2_weight = round(obj_2_weight, 4)
        
        obj_1_steps.append(obj_1_weight)
        obj_2_steps.append(obj_2_weight)
        
    return obj_1_steps, obj_2_steps


def save_to_pickle(obj, dir_path, filename):
    """
    Save an object to a pickle file.

    Parameters
    ----------
    obj : var
        Python object to be saved to pickle file.
    dir_path : str
        Path to directory where the file shall be saved (e.g 'data/results').
    filename : str
        Name of pickle file, without extension (e.g. 'my_data').

    Returns
    -------
    None.

    """
    
    import pickle
    
    filepath = f"{dir_path}/{filename}.pkl"

    with open(filepath, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
def load_from_pickle(dir_path, filename):
    """
    Return object that is loaded form a pickle file.

    Parameters
    ----------
    dir_path : str
        Path to directory where pickle file is stored (e.g 'data/results').
    filename : str
        Name of pickle file, without extension (e.g. 'my_data').

    Returns
    -------
    obj : var
        Python object to be read from pickle file.

    """
    
    import pickle
    
    filepath = f"{dir_path}/{filename}.pkl"
    
    with open(filepath, 'rb') as handle:
        obj = pickle.load(handle)
        
    return obj


def days_between_dates(start_date, end_date):
    """
    Calculate the number of days between two dates (inclusive).

    Parameters
    ----------
    start_date : str
        The start date in the format 'YYYY-MM-DD'.
    end_date : str
        The end date in the format 'YYYY-MM-DD'.

    Returns
    -------
    int
        The number of days between the start and end dates, inclusive.

    """

    # Convert the date strings to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate the difference between the dates
    delta = end_date - start_date
    
    # Return the number of days (including both start and end dates)
    return delta.days + 1


def number_of_timesteps(start_date, end_date, ts_resolution=60):
    """
    Calculate the number of timesteps in a given simulation timeframe.

    Parameters
    ----------
    start_date : str
        The start date in the format 'YYYY-MM-DD'.
    end_date : str
        The end date in the format 'YYYY-MM-DD'.
    ts_resolution : int
        Timestemp resolution (i.e. length of one timestep) in minutes.

    Returns
    -------
    no_ts : int
        Number of timesteps in given timeframe (rounded to int).

    """
    
    # Calculate number of days in given timeframe (incl. first and last day):
    days = days_between_dates(start_date, end_date)
    
    # Calculate no of timesteps per hour:
    num_ts_hours = 60.0 / ts_resolution
    
    # Number of timesteps in given timeframe:
    num_ts = int(days*24*num_ts_hours)
    
    return num_ts


def electricity_production_plant_data(epp_file_path, plant_type):
    """
    Write data of electricity production plants for specific plant type
    (e.g. wind power, solar pv, ...) to a pandas dataframe.
    Data is taken from BFE database on electricity production plants
    (Elektrizitätsproduktionsanlagen).
    
    To be implemented:
        Municipality name is adjusted according to names found in metafile.
    

    Parameters
    ----------
    file_path : str
        Path to ElectricityProductionPlant.csv file, which is obtained from
        BFE database.
    plant_type : str
        Type of electricity production plant (e.g. wind power).

    Raises
    ------
    Exception
        If the chose electricity production plant is invalid. This means either
        it doesn't exist or hasn't been implemented in the method yet.

    Returns
    -------
    df_epp : pandas dataframe
        Dataset reduced for chosen plant type.

    """
    
    # Select plant type:
    if plant_type == 'wind_power':
        maincat = 'maincat_2'
        subcat = 'subcat_3'
    else:
        raise Exception("plant_type invalid.")
    
    # ADD OTHERS HERE WHERE REQUIRED
        
    # Read file:
    df_epp_all = pd.read_csv(epp_file_path)
    
    # Filter for specified plant type:
    cat_filter = (
        df_epp_all['MainCategory'] == maincat)\
        & (df_epp_all['SubCategory'] == subcat
              )
    df_epp = df_epp_all[cat_filter]
    
    
    # df_epp = df_epp_all
    
    return df_epp


def epp_installed_cap_by_munic(df_epp, df_meta, plant_type, file_dir='', to_csv=True):
    
    '''
    Generate csv file with installed capacity of electricity production plant
    aggregated by municipalities.
    
    
    - Sum per municipality
    - Keep:
        - Municipality
        - Canton
        - TotalPower
    '''
    
    # Initialize new dataframe to store installed capacity for each munic:
    df_epp_all_munics = df_meta['Municipality'].copy()
    
    # Reduce existing epp dataframe to only keep relevant columns:
    # df_reduced = df_epp[['Municipality', 'Canton', 'TotalPower']]
    df_reduced = df_epp[['Municipality', 'TotalPower']]
    
    # Aggregate by municipality:
    # df_epp_munic = df_reduced.groupby(['Municipality', 'Canton']).sum()
    df_epp_munic = df_reduced.groupby(['Municipality']).sum()
    df_epp_munic.reset_index(inplace=True)
    
    # Merge dataframes on 'Municipality' column
    df_epp_inst = pd.merge(df_epp_all_munics, df_epp_munic, on='Municipality', how='left')
    
    # Fill missing values with 0
    df_epp_inst['p_kW'] = df_epp_inst['TotalPower'].fillna(0)
    
    # Drop 'TotalPower' column
    df_epp_inst.drop('TotalPower', axis=1, inplace=True)
    
    
    if to_csv:
        csv_file = file_dir + f'p_installed_kW_{plant_type}.csv'
        df_epp_inst.to_csv(csv_file)
    
    return df_epp_inst


def munic_name(names, names_file_path):
    """
    ___ !!! UNDER CONSTRUCTION !!! ___

    Take a list of municipality names and return the correct name as per
    metafile.

    Parameters
    ----------
    names : list or dataframe
        List of municipality names to be checked.
    names_file_path : str
        Path to excel file with list of invalid names and corresponding
        names acc. to metafile.

    Returns
    -------
    df_names_correct : pandas dataframe
        Dataframe with the following columns:
            - 'invalid_name': names from input list 'names'
            - 'metafile_names': corresponding names acc. metafile

    """
    
    df_names_correct = ...
    
    return df_names_correct

def check_dataseries_lengths(*dataseries):
    lengths = [len(ds) for ds in dataseries]
    # for l in lengths:
    #     print(l)
    if len(set(lengths)) != 1:
        raise ValueError("All dataseries must have the same length")


def save_calliope_dicts_to_yaml(
        dir_path,
        model_dict,
        tech_groups_dict,
        techs_dict,
        loc_dict,
        links_dict,
        run_dict
        ):
    
    import yaml
    import os
    
    def save_dict_to_yaml(data, file_path):
        """Save a dictionary to a YAML file."""
        with open(file_path, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)
    
    def save_dicts_to_yaml(
            dir_path,
            model_dict,
            tech_groups_dict,
            techs_dict,
            loc_dict,
            links_dict,
            run_dict
            ):
        """Convert and save dicts to YAML files in the specified directory."""
        # Create the directory if it doesn't exist
        os.makedirs(dir_path, exist_ok=True)
    
        # Define the dictionary names and corresponding filenames
        dicts = {
            'model': model_dict,
            'tech_groups': tech_groups_dict,
            'techs': techs_dict,
            'locations': loc_dict,
            'links': links_dict,
            'run': run_dict
        }
    
        # Save each dictionary as a YAML file
        for name, data in dicts.items():
            file_path = os.path.join(dir_path, f"{name}.yaml")
            save_dict_to_yaml(data, file_path)
    
    save_dicts_to_yaml(
        dir_path,
        model_dict,
        tech_groups_dict,
        techs_dict,
        loc_dict,
        links_dict,
        run_dict
        )
    
def get_com_files(com_nr,
                 master_data_dir,
                 com_data_dir,
                 master_file, 
                 meta_file):
    
    meta_file_path = master_data_dir + meta_file
    df_meta = pd.read_feather(meta_file_path)
    
    com_name = df_meta.loc[df_meta['GGDENR']==com_nr,'Municipality'].iloc[0]
    com_kt = df_meta.loc[df_meta['GGDENR']==com_nr,'Canton'].iloc[0]
    
    com_yr_file_name = df_meta.loc[df_meta['Municipality'] == com_name, 'Filename'].item() + '.csv'
    com_yr_file_path = com_data_dir + com_yr_file_name 
    file_exist = os.path.isfile(com_yr_file_path)
    
    if file_exist == False:
        # read master file and create new csv file with community data:
        master_file_path = master_data_dir + master_file
        df_master_yr = pd.read_feather(master_file_path)
        com_mask = df_master_yr['GGDENR'] == com_nr    
        df_com_yr = df_master_yr[com_mask]
        df_com_yr.to_csv(com_yr_file_path)
    elif file_exist == True:
        # read community file:
        df_com_yr = pd.read_csv(com_yr_file_path)
    else:
        raise(Exception("Community file not found?"))
        
    # print("==================////////////////////////////////////////////////")
    # print(com_name)
    
    # com_name for wind_power File:
    # com_name_wp = com_name
        
    # Change com_name containing forward slash (e.g. Biel/Bienne --> Biel_Bienne)
    if com_name == r"C'za Cadenazzo/Monteceneri": # Special case
        com_name = "Comunanza Cadenazzo_Monteceneri"
        
    if '/' in com_name:
        com_name = com_name.replace('/', '_')
        
    # # Change com_name in df_meta:
    df_meta.loc[df_meta['GGDENR']==com_nr, 'Municipality'] = com_name
        
    # print("==================////////////////////////////////////////////////")
    # print(com_name)
        
    return com_name, com_kt, df_meta, df_com_yr

def create_dict_yr(df_base):
    columns = df_base.columns
    dict_yr = {}
    
    for column in columns:
        dict_yr[column + '_yr'] = df_base[column].sum()
        
    return dict_yr


def update_electricity_mix_file(
        df_change,
        outfile_dir,
        strom_profiles_2050_file,
        electricity_mix_totals_file
        ):
    
    file = pd.read_feather(outfile_dir + strom_profiles_2050_file).reset_index(drop = True)
    
    cons = file.iloc[:, -1]
    
    totals = pd.read_feather(outfile_dir + electricity_mix_totals_file)
    
    columns = df_change.columns
    if columns.isin(totals.columns).sum() != len(columns):
        raise(Exception('There columns are not valid!'))
    else:
        for col in columns:
            totals[col] = df_change[col]
            
    shares = totals.div(totals.sum(axis = 1), axis = 0)
    
    
    import_file = pd.DataFrame(index = range(8760))
    import_file['percent'] = 1 - totals.sum(axis = 1)/cons
    import_file.loc[import_file['percent'] < 0, 'percent'] = 0
    
    totals.columns = totals.columns.astype(str)
    shares.columns = shares.columns.astype(str)
    import_file.columns = import_file.columns.astype(str)
    
    # print(shares)
    
    totals_filename = 'CH_production_totals.feather'
    shares_filename = 'CH_production_shares.feather'
    import_filename = 'import_percentage_profile.feather'
    
    totals.to_feather(outfile_dir + totals_filename)
    shares.to_feather(outfile_dir + shares_filename)
    import_file.to_feather(outfile_dir + import_filename)
    
    

def create_electricity_mix_file(
        outfile_dir,
        strom_profiles_2050_file
        ):

    file = pd.read_feather(outfile_dir + strom_profiles_2050_file).reset_index(drop = True)

    shares = pd.DataFrame(index = range(8760))
    totals = pd.DataFrame(index = range(8760))

    production_sum = file.iloc[:, [0, 1, 2, 3, 5, 6, 7]].sum(axis = 1)
    consumption_sum = file.iloc[:, 12]

    shares['hydro_share'] = file.iloc[:, :3].sum(axis = 1)/production_sum
    shares['nuclear_share'] = file.iloc[:, 3]/production_sum
    shares['wind_share'] = file.iloc[:, 5]/production_sum
    shares['biomass_share'] = file.iloc[:, 6]/production_sum
    shares['other_share'] = file.iloc[:, 7]/production_sum
    
    totals['hydro_share'] = file.iloc[:, :3].sum(axis = 1)
    totals['nuclear_share'] = file.iloc[:, 3]
    totals['wind_share'] = file.iloc[:, 5]
    totals['biomass_share'] = file.iloc[:, 6]
    totals['other_share'] = file.iloc[:, 7]
    
    import_file = pd.DataFrame(index = range(8760))
    import_file['percent'] = 1 - production_sum/consumption_sum
    import_file.loc[import_file['percent'] < 0] = 0
    
    totals.columns = totals.columns.astype(str)
    shares.columns = shares.columns.astype(str)
    import_file.columns = import_file.columns.astype(str)
    
    totals_filename = 'CH_production_totals.feather'
    shares_filename = 'CH_production_shares.feather'
    import_filename = 'import_percentage_profile.feather'
    
    totals.to_feather(outfile_dir + totals_filename)
    shares.to_feather(outfile_dir + shares_filename)
    import_file.to_feather(outfile_dir + import_filename)
    
def get_m_e_ch_sum(tech_grid_supply):
    
    sum_a = (
        sum(tech_grid_supply.get_m_e_ch_hydro())
        + sum(tech_grid_supply.get_m_e_ch_nuclear())
        + sum(tech_grid_supply.get_m_e_ch_wind())
        + sum(tech_grid_supply.get_m_e_ch_biomass())
        + sum(tech_grid_supply.get_m_e_ch_other())
        )
    
    # sum_a = df_scen['m_e_ch_hydro'].sum() +\
    #         df_scen['m_e_ch_nuclear'].sum() +\
    #         df_scen['m_e_ch_wind'].sum() +\
    #         df_scen['m_e_ch_biomass'].sum() +\
    #         df_scen['m_e_ch_other'].sum()
            
    return sum_a

def generate_e_mix(df_scen, el_mix_filename_path):
    
    df_interim = pd.DataFrame(index = range(8760))
    
    tmp_df = pd.read_feather(el_mix_filename_path)
    df_interim['Hydro_share'] = tmp_df['hydro_share']
    df_interim['Nuclear_share'] = tmp_df['nuclear_share']
    df_interim['Wind_share'] = tmp_df['wind_share']
    df_interim['Biomass_share'] = tmp_df['biomass_share']
    df_interim['Other_share'] = tmp_df['other_share']
    # print(df_interim.sum(axis = 1).sum())
    del tmp_df
      
    # Generate hourly profiles:
    df_scen['m_e_ch_hydro'] = df_interim['Hydro_share']*df_scen['m_e_ch']
    df_scen['m_e_ch_nuclear'] = df_interim['Nuclear_share']*df_scen['m_e_ch']
    df_scen['m_e_ch_wind'] = df_interim['Wind_share']*df_scen['m_e_ch']
    df_scen['m_e_ch_biomass'] = df_interim['Biomass_share']*df_scen['m_e_ch']
    df_scen['m_e_ch_other'] = df_interim['Other_share']*df_scen['m_e_ch']
    
    return df_scen

# def check_if_scenario_active(scen_techs):
#     """
#     Returns True if at least on of the scenario is activated.

#     Parameters
#     ----------
#     scen_techs : dictionary
#         Dictionary containing info about technologies. Input to
#         dem.DistrictEnergyModel.generate_scenario().

#     Returns
#     -------
#     check : bool
#         Returns True if at least one of the scenarios is activated.

#     """
    
#     list_scens = []
    
#     list_scens.append(scen_techs['optimisation']['enabled'])
    
#     for val in scen_techs['scenarios'].values():
#         list_scens.append(val)
    
#     check = any(list_scens)
    
#     # print(check)
    
#     return check

def get_plot_infos_RT():
    opac = 1.0
    opac_red_factor = 0.5 # reduced opacity 
    
    col_pv = f'rgba(238,238,0,{opac})' # 'yellow2'
    col_pv_exp = f'rgba(238,238,0,{opac*opac_red_factor})' # 'yellow2'
    col_wp =  f'rgba(51,51,255,{opac})'
    col_wp_exp =  f'rgba(51,51,255,{opac*opac_red_factor})'
    col_bm = f'rgba(0,112,0,{opac})'
    col_bm_exp = f'rgba(0,112,0,{opac*opac_red_factor})'
    col_hydro = f'rgba(0,0,255,{opac})'
    col_hydro_exp = f'rgba(0,0,255,{opac*opac_red_factor})'
    col_chp_gt = f'rgba(22,255,202,{opac})'

    # col_local_import = f'rgba(30,144,255,{opac})' # 'dodgerblue1'

    col_cross_border_import = f'rgba(119,136,153,{opac})' # 'lightslategray'
    col_CH_hydro = f'rgba(0,178,238,{opac})' # 'deepskyblue2'
    col_CH_nuclear = f'rgba(205,133,0,{opac})' # 'orange3'
    col_CH_wind =  f'rgba(140,20,252,{opac*opac_red_factor})'
    col_CH_biomass = f'rgba(50,205,50,{opac})' # 'limegreen'
    col_CH_other = f'rgba(162,205,90,{opac})' # 'darkolivegreen3'

    col_heat_pump = f'rgba(134, 7, 32,{opac})' # '#860720'
    col_tes_chg = f'rgba(239, 0, 140,{opac*opac_red_factor})' # '#EF008C'
    col_tes_dchg = f'rgba(239, 0, 140,{opac})' # '#EF008C'
    col_bes_chg = f'rgba(34, 153, 84,{opac*opac_red_factor})' # '#EF008C'
    col_bes_dchg = f'rgba(34, 153, 84,{opac})' # '#EF008C'
    col_gtes_chg = f'rgba(0, 0, 0,{opac*opac_red_factor})' # '#EF008C'
    col_gtes_dchg = f'rgba(0, 0, 0,{opac})' # '#EF008C'
    col_ws_chg = f'rgba(0, 0, 0,{opac*opac_red_factor})' # '#EF008C'
    col_ws_dchg = f'rgba(0, 0, 0,{opac})' # '#EF008C'

    col_hes_chg = f'rgba(135, 206, 235,{opac*opac_red_factor})' # '#EF008C'
    col_hes_dchg = f'rgba(135, 206, 235,{opac})' # '#EF008C'

    col_electric_heater = f'rgba(102,205,170,{opac})' # aquamarine3
    col_oil_boiler = f'rgba(255,64,64,{opac})' # brown1
    col_gas_boiler = f'rgba(255,97,3,{opac})' # cadmiumorange
    col_wood_boiler = f'rgba(205,133,0,{opac})' # 'orange3'
    col_district_heating = f'rgba(0,178,238,{opac})' # 'deepskyblue2'
    col_solar_thermal = f'rgba(238,238,0,{opac})' # 'yellow2'
    col_other =  f'rgba(119,136,153,{opac})' # 'lightslategray'
    
    col_wet_bm = f'rgba(139,69,19,{opac})'
    col_wet_bm_exp = f'rgba(139,69,19,{opac*opac_red_factor})'
    
    plot_dict = {
        'Electricity Profile Daily':{
            'column_headers':[
                'v_e_pv_cons',
                'v_e_pv_exp',
                'v_e_wp_cons',
                'v_e_wp_exp',
                'v_e_hydro_cons',
                'v_e_hydro_exp',
                'm_e_ch_hydro',
                'v_e_bm_cons',
                'v_e_bm_exp',
                'v_e_chp_gt',
                'm_e_ch_nuclear',
                'm_e_ch_wind',
                'm_e_ch_biomass',
                'm_e_ch_other',
                'm_e_cbimport',
                'v_e_bes',
                'u_e_bes'
                ],
            'column_labels':[
                'Solar',
                'Solar Einspeisung',
                'Wind',
                'Wind Einspeisung',
                'Wasser (lokal)',
                'Wasser Einspeisung',
                'Wasser',
                'Biomasse (lokal)',
                'Biomasse Einspeisung',
                'Gaskombikraftwerk',
                'Nuklear',
                'Wind',
                'Biomasse',
                'Andere Erneuerbare',
                'Ausland Import',
                'Batteriespeicher Entladen',
                'Battersiespeicher Laden'
                ],
            'colors':[
                col_pv,
                col_pv_exp,
                col_wp,
                col_wp_exp,
                col_hydro,
                col_hydro_exp,
                col_CH_hydro,
                col_bm,
                col_bm_exp,
                col_chp_gt,
                col_CH_nuclear,
                col_CH_wind,
                col_CH_biomass,
                col_CH_other,
                col_cross_border_import,
                col_bes_dchg,
                col_bes_chg
                ]
            },
        'Electricity Profile Weekly':{
            'column_headers':[
                'v_e_pv_cons',
                'v_e_pv_exp',
                'v_e_wp_cons',
                'v_e_wp_exp',
                'v_e_hydro_cons',
                'v_e_hydro_exp',
                'm_e_ch_hydro',
                'v_e_bm_cons',
                'v_e_bm_exp',
                'v_e_chp_gt',
                'm_e_ch_nuclear',
                'm_e_ch_wind',
                'm_e_ch_biomass',
                'm_e_ch_other',
                'm_e_cbimport',
                'v_e_bes',
                'u_e_bes'
                ],
            'column_labels':[
                'Solar',
                'Solar Einspeisung',
                'Wind',
                'Wind Einspeisung',
                'Wasser (lokal)',
                'Wasser Einspeisung',
                'Wasser',
                'Biomasse (lokal)',
                'Biomasse Einspeisung',
                'Gaskombikraftwerk',
                'Nuklear',
                'Wind',
                'Biomasse',
                'Andere Erneuerbare',
                'Ausland Import',
                'Batteriespeicher Entladen',
                'Battersiespeicher Laden'
                ],
            'colors':[
                col_pv,
                col_pv_exp,
                col_wp,
                col_wp_exp,
                col_hydro,
                col_hydro_exp,
                col_CH_hydro,
                col_bm,
                col_bm_exp,
                col_chp_gt,
                col_CH_nuclear,
                col_CH_wind,
                col_CH_biomass,
                col_CH_other,
                col_cross_border_import,
                col_bes_dchg,
                col_bes_chg
                ]
            },
        'Electricity Total Consumption':{
            'column_headers':[
                'v_e_pv_cons',
                'v_e_wp_cons',
                'v_e_hydro_cons',
                'm_e_ch_hydro',
                'v_e_bm_cons',
                'v_e_chp_gt',
                'm_e_ch_nuclear',
                'm_e_ch_wind',
                'm_e_ch_biomass',
                'm_e_ch_other',
                'm_e_cbimport'
                ],
            'column_labels':[
                'Solar',
                'Wind',
                'Wasser (lokal)',
                'Wasser',
                'Biomasse (lokal)',
                'Gaskombikraftwerk (lokal)',
                'Nuklear',
                'Wind',
                'Biomasse',
                'Andere Erneuerbare',
                'Ausland Import'
                ],
            'colors':[
                col_pv,
                col_wp,
                col_hydro,
                col_CH_hydro,
                col_bm,
                col_chp_gt,
                col_CH_nuclear,
                col_CH_wind,
                col_CH_biomass,
                col_CH_other,
                col_cross_border_import,       
                ]
            },
        'Electricity Total Production':{
            'column_headers':[
                'v_e_pv',
                'v_e_wp',
                'v_e_hydro',
                'v_e_bm',
                'v_e_chp_gt',
                ],
            'column_labels':[
                'PV Produktion',
                'Wind Produktion',
                'Lokal Wasser Produktion',
                'Biomasse Produktion',
                'Gaskombikraftwerk Produktion',
                ],
            'colors':[
                col_pv,
                col_wp,
                col_hydro,
                col_bm,
                col_chp_gt,
                ]
            },
        'Heat Profile Daily':{
            'column_headers':[
                'v_h_hp',
                'v_h_eh',
                'v_h_ob',
                'v_h_gb',
                'v_h_wb',
                'v_h_dh',
                'v_h_solar',
                'v_h_chp_gt',
                'v_h_other',
                'v_h_bm',
                'v_h_tes',
                'u_h_tes'
                ],
            'column_labels':[
                'Wärmepumpe',
                'Elektrische Heizung',
                'Ölheizung',
                'Gasheizung',
                'Holzofen',
                'Fernwärme',
                'Solarthermie',
                'Gaskombikraftwerk',
                'Andere',
                'Biomasse',
                'TES Entladen',
                'TES Laden'
                ],
            'colors':[
                col_heat_pump,
                col_electric_heater,
                col_oil_boiler,
                col_gas_boiler,
                col_wood_boiler,
                col_district_heating,
                col_solar_thermal,
                col_chp_gt,
                col_other,
                col_bm,
                col_tes_dchg,
                col_tes_chg
                ]
            },
        'Heat Profile Weekly':{
            'column_headers':[
                'v_h_hp',
                'v_h_eh',
                'v_h_ob',
                'v_h_gb',
                'v_h_wb',
                'v_h_dh',
                'v_h_solar',
                'v_h_chp_gt',
                'v_h_other',
                'v_h_bm',
                'v_h_tes',
                'u_h_tes'
                ],
            'column_labels':[
                'Wärmepumpe',
                'Elektrische Heizung',
                'Ölheizung',
                'Gasheizung',
                'Holzofen',
                'Fernwärme',
                'Solarthermie',
                'Gaskombikraftwerk',
                'Andere',
                'Biomasse',
                'TES Entladen',
                'TES Laden'
                ],
            'colors':[
                col_heat_pump,
                col_electric_heater,
                col_oil_boiler,
                col_gas_boiler,
                col_wood_boiler,
                col_district_heating,
                col_solar_thermal,
                col_chp_gt,
                col_other,
                col_bm,
                col_tes_dchg,
                col_tes_chg
                ]
            },
        'Heat Generation Total':{
            'column_headers':[
                'v_h_hp',
                'v_h_eh',
                'v_h_ob',
                'v_h_gb',
                'v_h_wb',
                'v_h_dh',
                'v_h_solar',
                'v_h_chp_gt',
                'v_h_other',
                'v_h_bm',
                'v_h_tes',
                'u_h_tes'
                ],
            'column_labels':[
                'Wärmepumpe',
                'Elektrische Heizung',
                'Ölheizung',
                'Gasheizung',
                'Holzofen',
                'Fernwärme',
                'Solarthermie',
                'Gaskombikraftwerk',
                'Andere',
                'Biomasse',
                'TES Entladen',
                'TES Laden'
                ],
            'colors':[
                col_heat_pump,
                col_electric_heater,
                col_oil_boiler,
                col_gas_boiler,
                col_wood_boiler,
                col_district_heating,
                col_solar_thermal,
                col_chp_gt,
                col_other,
                col_bm,
                col_tes_dchg,
                col_tes_chg
                ]
            },
        'PV Potential Total':{
            # 'column_headers':[
            #     'v_e_pv',
            #     'v_e_pv_pot',
            #     'v_e_pv_pot_fas'
            #     ],
            'column_headers':[
                'PV Consumed',
                'PV Dach Potenzial',
                'PV Fassade Potenzial'
                ],
            'colors':[
                col_bm,
                col_pv,
                col_pv
                ]
            },
        'Biomass Potential Total':{
            # 'column_headers':[
            #     's_wd',
            #     's_wd_rem',
            #     's_wet_bm',
            #     's_wet_bm_rem'
            #     ],
            'column_headers':[
                'Holz Potenzial',
                'Holz Übrig',
                'Nasse Biomasse Potenzial',
                'Nasse Biomasse Übrig',
                ],
            'colors':[
                col_wet_bm,
                col_wet_bm_exp,
                col_bm,
                col_bm_exp
                ]
            },
        'Wind Potential Total':{
            # 'column_headers':[
            #     'v_e_wp',
            #     'v_e_wp_pot'
            #     ],
            'column_headers':[
                'Wind Gebrauch',
                'Wind Potenzial'
                ],
            'colors':[
                col_wp,
                col_wp_exp
                ]
            }
        }
    return plot_dict

def hourly_array_to_daily(hourly_array):
    """
    Sum up hourly values to daily values in an numpy array.
    """
    x = hourly_array
    if x.size % 24 != 0:
        raise ValueError("Array length must be a multiple of 24.")
    daily_array = x.reshape(-1, 24).sum(axis=1)
    
    return np.array(daily_array)

    
#%% FOR TESTING ONLY







