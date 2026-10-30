# -*- coding: utf-8 -*-
"""
Created on Wed May  1 07:10:51 2024

@author: UeliSchilt
"""

import pandas as pd
# import matplotlib.pylab as plt
import numpy as np
# import sys
# import os
# import math

from district_energy_model import dem_techs
from district_energy_model import dem_helper

# from datetime import datetime

# def get_local_electricity_mix(d_e, v_e_pv, v_e_wp, v_e_bm, v_e_hydro):
def get_local_electricity_mix(energy_demand, tech_instances, with_bes=False,
                              electricity_supply_order=None):
    """Allocate local generation to demand in source-priority order.

    ``electricity_supply_order`` uses technology keys (solar_pvrooftop, solar_pvalpine,
    wind_power, biomass, hydro_power). If omitted, their historical order is retained.
    Absent source objects are skipped, including sources named in an explicit
    order. An explicit order must include every present supported generator
    exactly once; unknown names and duplicates raise ValueError. Deployment
    consistency is checked separately by scenario validation.

    With ``with_bes=True``, battery charging is added to demand and battery
    output is used after all local generators, as before. A BES object must
    then exist. Grid supply is always required, even if there are no sources.

    PV sources are allocated and updated per installation.
    Updates present generators' consumption/export and grid import in place.
    Returns None. Does not decide storage operation or change demand.
    """
    default_order = ('solar_pvrooftop', 'solar_pvalpine', 'wind_power',
                     'biomass', 'hydro_power')
    if electricity_supply_order is None:
        source_order = list(default_order)
    else:
        if (not isinstance(electricity_supply_order, (list, tuple))
                or any(not isinstance(key, str) for key in electricity_supply_order)):
            raise ValueError('electricity_supply_order must be a list or tuple '
                             'of technology names.')
        source_order = list(electricity_supply_order)
        if len(source_order) != len(set(source_order)):
            raise ValueError('electricity_supply_order contains duplicate sources.')
        unknown = sorted(set(source_order) - set(default_order))
        if unknown:
            raise ValueError(f'Unknown electricity supply sources: {unknown}.')
        omitted = sorted(set(default_order).intersection(tech_instances)
                         - set(source_order))
        if omitted:
            raise ValueError('electricity_supply_order omits present sources: '
                             f'{omitted}.')

    source_order = [key for key in source_order if key in tech_instances]
    tech_grid_supply = tech_instances['grid_supply']
    d_e = energy_demand.get_d_e()
    # Allocate PV production per installation, as required by SolarPVType.
    # Expanding each source in-place preserves its configured priority.
    solar_sources = {'solar_pvrooftop', 'solar_pvalpine'}
    dict_v_e = {}
    source_members = {}
    for key in source_order:
        tech = tech_instances[key]
        if key in solar_sources:
            members = []
            for index, generation in enumerate(tech.get_v_e_from_installations()):
                member = f'{key}_{index}'
                members.append(member)
                dict_v_e[member] = pd.Series(generation)
            source_members[key] = members
        else:
            source_members[key] = [key]
            dict_v_e[key] = pd.Series(tech.get_v_e())
    tech_hierarchy = list(dict_v_e)
    series_to_check = [d_e, *dict_v_e.values()]
    if with_bes:
        tech_bes = tech_instances['bes']
        dict_v_e['bes'] = pd.Series(tech_bes.get_v_e())
        u_e_bes = tech_bes.get_u_e()
        tech_hierarchy.append('bes')
        series_to_check.extend([dict_v_e['bes'], u_e_bes])
    dem_helper.check_dataseries_lengths(*series_to_check)
    ds_n = len(d_e)

    # Initialise dicts for self-consumption (con) and export (exp)
    dict_v_e_cons = {}
    dict_v_e_exp = {}
    
    # Initialise the remaining electricity demand
    
    d_e_remain = pd.Series(d_e + u_e_bes) if with_bes else pd.Series(d_e)

    # print(dict_v_e['wp'])
    
    for tech_key in tech_hierarchy:
        # Electricity production timeseries for specific tech:
        tmp_v_e = dict_v_e[tech_key]
        
        # Temporary dataframe for vectorised calculations:
        df_calc = pd.DataFrame({'v_e_cons': [0.0] * ds_n})
        df_calc['v_e_exp'] = [0.0] * ds_n
        df_calc['d_e_remain'] = [0.0] * ds_n
        
        # Calculate difference between production and demand:
        df_calc['dP'] = tmp_v_e - d_e_remain
        
        # Calculate self-consumption:
        df_calc.loc[(df_calc['dP']>=0),'v_e_cons'] = d_e_remain
        df_calc.loc[(df_calc['dP']<0),'v_e_cons'] = tmp_v_e            
            
        # Calculate export:
        df_calc.loc[(df_calc['dP']>=0),'v_e_exp'] = df_calc['dP']
        df_calc.loc[(df_calc['dP']<0),'v_e_exp'] = 0
        
        # Calculate remaining demand:
        df_calc.loc[(df_calc['dP']>=0),'d_e_remain'] = 0
        df_calc.loc[(df_calc['dP']<0),'d_e_remain'] = -df_calc['dP']        
            
        # Pass results to dicts:
        dict_v_e_cons[tech_key] = df_calc['v_e_cons']
        dict_v_e_exp[tech_key] = df_calc['v_e_exp']
        
        # Update remaining demand:
        d_e_remain = df_calc['d_e_remain']
        
        del tmp_v_e
        del df_calc

    # Required import:
    m_e = d_e_remain
    
    #--------------------------------------------------------------------------
    # Update local renewable tech objects:
    
    for tech_key in source_order:
        tech = tech_instances[tech_key]
        members = source_members[tech_key]
        if tech_key in solar_sources:
            tech.update_v_e_cons([dict_v_e_cons[member] for member in members])
            tech.update_v_e_exp([dict_v_e_exp[member] for member in members])
        else:
            tech.update_v_e_cons(dict_v_e_cons[tech_key])
            tech.update_v_e_exp(dict_v_e_exp[tech_key])

    #--------------------------------------------------------------------------
    # Update import:
    tech_grid_supply.add_m_e(np.array(m_e))

def update_m_e(m_e_updated, tech_grid_supply):
    """
    Update the import m_e including the splits (e.g. m_e_ch_hydro,
    m_e_ch_nuclear, etc...) based on updated total import values m_e_new.
    
    The following energy flows are updated:
        - m_e_ch
        - m_e_ch_hydro
        - m_e_ch_nuclear
        - m_e_ch_wind
        - m_e_ch_biomass
        - m_e_ch_other
        - m_e_cbimport

    Parameters
    ----------
    m_e_new : dataseries or list
        Updated values of total import.
    df_scen : dataframe
        Dataframe containing hourly timeseries of energy flows [kWh].

    Returns
    -------
    df_scen : dataframe
        Updated dataframe containing hourly timeseries of energy flows [kWh].

    """
    
    df = pd.DataFrame()

    df['m_e'] = m_e_updated
    df['m_e_ch'] = tech_grid_supply.get_m_e_ch()
    df['m_e_ch_hydro'] = tech_grid_supply.get_m_e_ch_hydro()
    df['m_e_ch_nuclear'] = tech_grid_supply.get_m_e_ch_nuclear()
    df['m_e_ch_wind'] = tech_grid_supply.get_m_e_ch_wind()
    df['m_e_ch_biomass'] = tech_grid_supply.get_m_e_ch_biomass()
    df['m_e_ch_other'] = tech_grid_supply.get_m_e_ch_other()
    df['m_e_cbimport'] = tech_grid_supply.get_m_e_cbimport()
    
    # Where m_e = 0, set all imports to 0:
    df.loc[df['m_e'] == 0, 'm_e_ch'] = 0
    df.loc[df['m_e'] == 0, 'm_e_ch_hydro'] = 0
    df.loc[df['m_e'] == 0, 'm_e_ch_nuclear'] = 0
    df.loc[df['m_e'] == 0, 'm_e_ch_wind'] = 0
    df.loc[df['m_e'] == 0, 'm_e_ch_biomass'] = 0
    df.loc[df['m_e'] == 0, 'm_e_ch_other'] = 0
    df.loc[df['m_e'] == 0, 'm_e_cbimport'] = 0
    
    # Update CH-import:
    # Where the ch-import is currently larger than the total import m_e, it is
    # downscaled to m_e (using a ratio) and all the ch-import shares are
    # adapted accordingly.
    df['tmp_m_e_ch_old'] = df['m_e_ch'].copy(deep = True)
    df['tmp_m_e_ratio'] = df['m_e']/df['m_e_ch']
    df.loc[df['m_e']==0,'tmp_m_e_ratio'] = 0
    
    #df_scen['tmp_m_e_ratio'].to_csv('tmp_m_e_ratio.csv')
    
    df.loc[df['tmp_m_e_ratio']<1,'m_e_ch'] = df['m_e_ch']*df['tmp_m_e_ratio']
    df.loc[df['tmp_m_e_ratio']<1,'m_e_ch_hydro'] = df['m_e_ch_hydro']*df['tmp_m_e_ratio']
    df.loc[df['tmp_m_e_ratio']<1,'m_e_ch_nuclear'] = df['m_e_ch_nuclear']*df['tmp_m_e_ratio']
    df.loc[df['tmp_m_e_ratio']<1,'m_e_ch_wind'] = df['m_e_ch_wind']*df['tmp_m_e_ratio']
    df.loc[df['tmp_m_e_ratio']<1,'m_e_ch_biomass'] = df['m_e_ch_biomass']*df['tmp_m_e_ratio']
    df.loc[df['tmp_m_e_ratio']<1,'m_e_ch_other'] = df['m_e_ch_other']*df['tmp_m_e_ratio']
    
    # Update cross-border (cb) import:
    df['m_e_cbimport'] = df['m_e'] - df['m_e_ch']


# def update_m_e(m_e_new, df_scen):

#     """
#     Update the import m_e including the splits (e.g. m_e_ch_hydro,
#     m_e_ch_nuclear, etc...) based on updated total import values m_e_new.
    
#     The following energy flows are updated:
#         - m_e_ch
#         - m_e_ch_hydro
#         - m_e_ch_nuclear
#         - m_e_ch_wind
#         - m_e_ch_biomass
#         - m_e_ch_other
#         - m_e_cbimport

#     Parameters
#     ----------
#     m_e_new : dataseries or list
#         Updated values of total import.
#     df_scen : dataframe
#         Dataframe containing hourly timeseries of energy flows [kWh].

#     Returns
#     -------
#     df_scen : dataframe
#         Updated dataframe containing hourly timeseries of energy flows [kWh].

#     """

#     df_scen['m_e'] = m_e_new
    
#     # Where m_e = 0, set all imports to 0:
#     df_scen.loc[df_scen['m_e'] == 0, 'm_e_ch'] = 0
#     df_scen.loc[df_scen['m_e'] == 0, 'm_e_ch_hydro'] = 0
#     df_scen.loc[df_scen['m_e'] == 0, 'm_e_ch_nuclear'] = 0
#     df_scen.loc[df_scen['m_e'] == 0, 'm_e_ch_wind'] = 0
#     df_scen.loc[df_scen['m_e'] == 0, 'm_e_ch_biomass'] = 0
#     df_scen.loc[df_scen['m_e'] == 0, 'm_e_ch_other'] = 0
#     df_scen.loc[df_scen['m_e'] == 0, 'm_e_cbimport'] = 0
    
#     # Update CH-import:
#     # Where the ch-import is currently larger than the total import m_e, it is
#     # downscaled to m_e (using a ratio) and all the ch-import shares are
#     # adapted accordingly.
#     df_scen['tmp_m_e_ch_old'] = df_scen['m_e_ch'].copy(deep = True)
#     df_scen['tmp_m_e_ratio'] = df_scen['m_e']/df_scen['m_e_ch']
#     df_scen.loc[df_scen['m_e']==0,'tmp_m_e_ratio'] = 0
    
#     #df_scen['tmp_m_e_ratio'].to_csv('tmp_m_e_ratio.csv')
    
#     df_scen.loc[df_scen['tmp_m_e_ratio']<1,'m_e_ch'] = df_scen['m_e_ch']*df_scen['tmp_m_e_ratio']
#     df_scen.loc[df_scen['tmp_m_e_ratio']<1,'m_e_ch_hydro'] = df_scen['m_e_ch_hydro']*df_scen['tmp_m_e_ratio']
#     df_scen.loc[df_scen['tmp_m_e_ratio']<1,'m_e_ch_nuclear'] = df_scen['m_e_ch_nuclear']*df_scen['tmp_m_e_ratio']
#     df_scen.loc[df_scen['tmp_m_e_ratio']<1,'m_e_ch_wind'] = df_scen['m_e_ch_wind']*df_scen['tmp_m_e_ratio']
#     df_scen.loc[df_scen['tmp_m_e_ratio']<1,'m_e_ch_biomass'] = df_scen['m_e_ch_biomass']*df_scen['tmp_m_e_ratio']
#     df_scen.loc[df_scen['tmp_m_e_ratio']<1,'m_e_ch_other'] = df_scen['m_e_ch_other']*df_scen['tmp_m_e_ratio']
    
#     # Update cross-border (cb) import:
#     df_scen['m_e_cbimport'] = df_scen['m_e'] - df_scen['m_e_ch']
    
#     del df_scen['tmp_m_e_ch_old']
#     del df_scen['tmp_m_e_ratio']
    
#     return df_scen


def update_dict_yr_scen(df_scen, dict_yr_scen):
    """
    Update annual values based on hourly values of energy flows [kWh].

    Parameters
    ----------
    df_scen : dataframe
        Dataframe containing hourly timeseries of energy flows [kWh].
    dict_yr_scen : dictionnary
        Dictionnary containing annual values of energy flows [kWh], prior
        to update.

    Returns
    -------
    dict_yr_scen : dictionnary
        Dictionnary containing annual values of energy flows [kWh], with
        updated values.

    """
    # Getting the list of headers (i.e. energy flows):
    flows = df_scen.columns.tolist()

    # Write annual sum of each energy flow to dict:
    for flow in flows:
        
        if flow=='q_h_tes':
            # charging leve of TES doesn't require annual value
            pass
        
        else:        
            key = f"{flow}_yr"
            
            dict_yr_scen[key] = df_scen[flow].sum()
    
    return dict_yr_scen


def energy_balance_test(value_1, value_2, description, diff_accepted = 0.01):
    
    """
    Compares two energy values that should be equal. Raises an exception if the
    difference between the two values is too large.
    
    Parameters
    ----------
    value_1 : float
        Energy value 1 to be compared (kWh).
    value_2 : float
        Energy value 2 to be compared (kWh).
    description : string
        Description of technology / energy type / ... (used for error message).
    diff_accepted : float
        Accepted error due to rounding / decimals / ... (kWh) (e.g. 0.01)

    Returns
    -------
    n/a
    """
            
    diff = abs(value_1 - value_2)
            
    if diff > diff_accepted:
        print(f"Energy balance test for {description} not successful!")
        print(f"Energy value 1 (kWh): {value_1}")
        print(f"Energy value 2 (kWh): {value_2}")
        print(f"Difference (kWh): {diff}")
        raise Exception(f"{description} energy balance is not fulfilled!")
        

def energy_balance_df_test(df_column_1, df_column_2, description, diff_accepted = 0.01):
    
    """
    Compares two dataframe columns containing energy values that should be
    equal. Raises an exception if the difference betweentwo values is too large.
    
    Parameters
    ----------
    df_column_1 : pandas dataframe column
        Dataframe column 1 to be compared (kWh).
    df_column_2 : pandas dataframe column
        Dataframe column 2 to be compared (kWh).
    description : string
        Description of technology / energy type / ... (used for error message).
    diff_accepted : float
        Accepted error due to rounding / decimals / ... (kWh) (e.g. 0.01)

    Returns
    -------
    n/a
    """
            
    df_diff = abs(df_column_1 - df_column_2)
    
    max_diff = df_diff.max()
            
    if max_diff > diff_accepted:
        print(f"Energy balance test for {description} not successful!")
        print(f"Max. difference (kWh): {max_diff}")
        raise Exception(f"{description} energy balance is not fulfilled!")


def electricity_balance_test(scen_techs,
                             df_scen,
                             optimisation=False,
                             diff_accepted = 1e-5,
                             diff_sum_accepted = 0.01
                             ):
    
    """
    Tests if the overall energy balance for electricity is fullfilled, by
    comparing generation to consumption.
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    optimisation : bool
        Must be set to True if the test is applied after an optimisation. This
        is due to the calculation of the remaining PV potential, as the solar
        thermal is also included in the potential in this case (not the case
        in the base scenario).
    diff_accepted : float
        Accepted error due to rounding / decimals / ... for individual values
        in timeseries (e.g. 0.00001).
    diff_sum_accepted : float
        Accepted error due to rounding / decimals / ... for sum of all values
        in timeseries (e.g. 0.01).

    Returns
    -------
    n/a
    """
    
    #--------------------------------------------------------------------------
    # Check timeseries:

    df_scen = dem_helper.add_missing_keys(df_scen)
        
    electricity_consumption = df_scen['d_e'] + df_scen['u_e_bes'] + df_scen['f_e']
    
    electricity_generation = (
                                # df_scen['v_e_pv_cons']
                                df_scen['v_e_pvrooftop_cons']
                              + df_scen['v_e_pvalpine_cons']
                              + df_scen['v_e_wp_cons']
                              + df_scen['v_e_bm_cons']
                              + df_scen['v_e_hydro_cons']
                              + df_scen['v_e_chpgt']
                              + df_scen['v_e_gtcp']
                              + df_scen['v_e_st']
                              + df_scen['v_e_wte']
                              + df_scen['v_e_bes']
                              + df_scen['m_e']
                              + df_scen['d_e_unmet']
                              )
    
    electricity_demand_split = (df_scen['d_e_h'] # heating demand
                                + df_scen['d_e_baseline']  # baseline demand
                                + df_scen['d_e_ev'] # EV demand
                                + df_scen['u_e_aguh']
                                + df_scen['u_e_wgu'] 
                                + df_scen['u_e_wguh']# TEMPORARY!!!
                                + df_scen['u_e_hydp']
                                + df_scen['u_e_bes']
                                + df_scen['f_e']
                                )
    
    electricity_baseline_demand = df_scen['d_e_baseline']
    
    electricity_baseline_demand_split = (
        df_scen['d_e_res']
        + df_scen['d_e_ind']
        + df_scen['d_e_ser']
        + df_scen['d_e_pump']
        + df_scen['d_e_loss']
        )
    
    electricity_for_heating = df_scen['d_e_h']
    
    electricity_for_heating_split = (df_scen['u_e_hp']
                                     + df_scen['u_e_eh']
                                     + df_scen['u_e_hpcp']
                                     + df_scen['u_e_hpcplt']
                                     + df_scen['u_e_ehcp']
                                     )
    # Tank resistance charging is a heating load independent of building EH.
    electricity_for_heating_split += df_scen.get('u_e_tesdc_direct', 0.0)
    
    pv_generation = df_scen['v_e_pvrooftop']
    
    # pv_generation_split = (df_scen['v_e_pv_cons']
    #                        + df_scen['v_e_pv_exp']
    #                        )

    pv_generation_split = (
        df_scen['v_e_pvrooftop_cons']
        + df_scen['v_e_pvrooftop_exp']
            )
    
    total_import = df_scen['m_e']
    
    total_import_split = (df_scen['m_e_ch']
                          + df_scen['m_e_cbimport']
                          )
    
    swiss_import = df_scen['m_e_ch']
    
    swiss_import_split = (df_scen['m_e_ch_hydro']
                          + df_scen['m_e_ch_nuclear']
                          + df_scen['m_e_ch_wind']
                          + df_scen['m_e_ch_biomass']
                          + df_scen['m_e_ch_other']
                          )
    
    # Convert solar thermal to equivalent solar pv yield:
    
    # tmp_pv_equi = dem_techs.SolarPV.convert_thermal_to_pv(
    #     df_thermal_kWh=df_scen['v_h_solar'],
    #     eta_pv=scen_techs['solar_pv']['eta_overall'],
    #     eta_thermal=scen_techs['solar_thermal']['eta_overall']
    #     )
    
    # pv_potential_split = (
    #     tmp_pv_equi                 # TEMPORARY FIX!!! Wie sollen wir Solarthermie behandeln?                
    #     + df_scen['v_e_pv']
    #     + df_scen['v_e_pv_pot_remain']
    #     )
    
    pv_potential_split = (
        df_scen['v_e_pvrooftop']
        + df_scen['v_e_pvrooftop_pot_remain']
        )
        
    pv_potential = df_scen['v_e_pvrooftop_pot'] # installed and additional potential
    
    wp_generation = df_scen['v_e_wp']
    
    wp_generation_split = df_scen['v_e_wp_cons'] + df_scen['v_e_wp_exp']
    
    wp_potential = df_scen['v_e_wp_pot']
    
    wp_potential_split = (
        df_scen['v_e_wp']
        + df_scen['v_e_wp_ch']
        + df_scen['v_e_wp_pot_remain']
        )
    
    # Storage losses are only checked as a sum:
    bes_losses_sum = (
        df_scen['l_u_e_bes']
        + df_scen['l_v_e_bes']
        + df_scen['l_q_e_bes']
        ).sum()

    bes_input_sum = df_scen['u_e_bes'].sum() 
    
    bes_output_sum = df_scen['v_e_bes'].sum()
    
    bes_sos_diff = (df_scen['q_e_bes'].iloc[-1]
                    -df_scen['l_q_e_bes'].iloc[-1] 
                    - df_scen['q_e_bes'].iloc[0] 
                    - df_scen['v_e_bes'].iloc[0]/scen_techs['bes']['eta_chg_dchg']
                    + df_scen['u_e_bes'].iloc[0]*scen_techs['bes']['eta_chg_dchg']) # state-of-charge (sos) difference
    
    # ------------------------------------------------------------------------
    dict_diff_max = {}

    dict_diff_max[1] = abs(electricity_consumption - electricity_generation).max()
    # max_diff_1 = diff_1.max()
    
    dict_diff_max[2] = abs(
        electricity_consumption - electricity_demand_split
        ).max()
    # max_diff_2 = diff_2.max()
    
    dict_diff_max[3] = abs(
        electricity_for_heating - electricity_for_heating_split
        ).max()
    # max_diff_3 = diff_3.max()

    dict_diff_max[4] = abs(pv_generation - pv_generation_split).max()
    # max_diff_4 = diff_4.max()
    
    dict_diff_max[5] = abs(total_import - total_import_split).max()
    # max_diff_5 = diff_5.max()
    
    dict_diff_max[6] = abs(swiss_import - swiss_import_split).max()
    # max_diff_6 = diff_6.max()
    
    dict_diff_max[7] = abs(pv_potential_split - pv_potential).max()
    # max_diff_7 = diff_7.max()
    
    dict_diff_max[8] = abs(wp_generation - wp_generation_split).max()
    # max_diff_8 = diff_8.max()
    
    dict_diff_max[9] = abs(wp_potential - wp_potential_split).max()
    # max_diff_9 = diff_9.max()
        
    # diff_10: Battery Energy Storage(BES) losses are only checked as sums
    
    dict_diff_max[11] = abs(
        electricity_baseline_demand - electricity_baseline_demand_split
        ).max()
    # max_diff_11 = diff_11.max()
    
    for nr, diff_max in dict_diff_max.items():
        if diff_max > diff_accepted:
            # print(f"Electricity balance ({nr}) is not fulfilled!")
            # print(f"Max. difference (kWh): {diff_max}")
            raise Exception(
                f"Electricity balance ({nr}) is not fulfilled!"
                f"\nMax. difference (kWh): {diff_max}"
                f"\nElectricity balance (timeseries) is not fulfilled!({nr})"
                "\nThis error can potentially be avoided by increasing "
                "bigM_value in optimisation.yaml. "
                "\nIf no solution can be found, please report the error here: "
                r"https://dem-documentation.readthedocs.io/en/latest/contact.html"
                )
    
    #--------------------------------------------------------------------------
    # Check sums:
    dict_diff_sum = {}

    electricity_consumption_sum = electricity_consumption.sum()
    electricity_generation_sum = electricity_generation.sum()
    electricity_demand_split_sum = electricity_demand_split.sum()
    electricity_baseline_demand_split_sum =\
        electricity_baseline_demand_split.sum()
    electricity_baseline_demand_sum = electricity_baseline_demand.sum()    
    electricity_for_heating_sum = electricity_for_heating.sum()    
    electricity_for_heating_split_sum = electricity_for_heating_split.sum()  
    pv_generation_sum = pv_generation.sum()
    pv_generation_split_sum = pv_generation_split.sum()    
    total_import_sum = total_import.sum()
    total_import_split_sum = total_import_split.sum()
    swiss_import_sum = swiss_import.sum()    
    swiss_import_split_sum = swiss_import_split.sum()
    pv_potential_split_sum = pv_potential_split.sum()
    pv_potential_sum = pv_potential.sum()
    wp_generation_sum = wp_generation.sum()
    wp_generation_split_sum = wp_generation_split.sum()
    wp_potential_sum = wp_potential.sum()
    wp_potential_split_sum = wp_potential_split.sum()
    
    dict_diff_sum[1] =\
        abs(electricity_consumption_sum - electricity_generation_sum)
    dict_diff_sum[2] =\
        abs(electricity_consumption_sum - electricity_demand_split_sum)
    dict_diff_sum[3] =\
        abs(electricity_for_heating_sum - electricity_for_heating_split_sum)
    dict_diff_sum[4] = abs(pv_generation_sum - pv_generation_split_sum)
    dict_diff_sum[5] = abs(total_import_sum - total_import_split_sum)
    dict_diff_sum[6] = abs(swiss_import_sum - swiss_import_split_sum)
    dict_diff_sum[7] = abs(pv_potential_split_sum - pv_potential_sum)
    dict_diff_sum[8] = abs(wp_generation_sum - wp_generation_split_sum)
    dict_diff_sum[9] = abs(wp_potential_sum - wp_potential_split_sum)
    # diff_sum_10 = abs(bes_input_sum - bes_output_sum - bes_losses_sum - bes_sos_diff)
    dict_diff_sum[10] = abs(
        bes_input_sum - bes_output_sum - bes_losses_sum - bes_sos_diff
        ) # assuming cycling constraint
    dict_diff_sum[11] = abs(
        electricity_baseline_demand_sum - electricity_baseline_demand_split_sum
        )
    
    for nr, diff_sum in dict_diff_sum.items():
        if diff_sum > diff_sum_accepted:
            print(f"Electricity balance ({nr}) is not fulfilled!")
            print(f"Sum difference (kWh): {diff_sum}")
            raise Exception(f"Electricity balance (sum) is not fulfilled! ({nr})")

def heat_balance_test(scen_techs,
                      df_scen,
                      optimisation=False,
                      diff_accepted = 1e-5,
                      diff_sum_accepted = 0.1,
                      tes_sites_plotting_inf = {}
                      ):
    
    """
    Tests if the overall energy balance for heat is fullfilled, by comparing
    generation to consumption.
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    diff_accepted : float
        Accepted error due to rounding / decimals / ... for individual values
        in timeseries (e.g. 0.00001).
    diff_sum_accepted : float
        Accepted error due to rounding / decimals / ... for sum of all values
        in timeseries (e.g. 0.01).

    Returns
    -------
    n/a
    """

    # Fill dataframe with 0s if columns are missing:

    df_scen = dem_helper.add_missing_keys(df_scen, tes_sites_plotting_inf)
    
    # flex_label
    if (
        scen_techs['optimisation']['enabled']
        and scen_techs['scenarios']['demand_side']
        and scen_techs['demand_side']['dr_flexibility_building_inertia']
        ):
        heat_demand = df_scen['d_h_flex_ll']
    else:
        heat_demand = df_scen['d_h']
    
    heat_consumption = (heat_demand # df_scen['d_h']
                        + df_scen['u_h_tesdc']
                        + df_scen['v_h_solarthermalrooftop_exp']
                        + df_scen['d_h_m']
                        + df_scen['u_h_vs_hp'] # Virtual storage for flexiblity modelling
                        # + df_scen['u_h_vs_dh'] # Virtual storage for flexiblity modelling # INCLUDED IN DISTRICT HEATING
                        # + df_scen['u_h_tes'] # INCLUDED IN DISTRICT HEATING
                        )
    
    heat_generation = (df_scen['v_h_hp']
                       + df_scen['v_h_eh']
                       + df_scen['v_h_ob']
                       + df_scen['v_h_gb']
                       + df_scen['v_h_wb']
                       + df_scen['v_h_dh']
                       + df_scen['v_h_solarthermalrooftop']
                       + df_scen['v_h_other']
                       + df_scen['v_h_tesdc']
                       + df_scen['v_h_vs_hp'] # Virtual storage for flexiblity modelling
                       # + df_scen['v_h_vs_dh'] # Virtual storage for flexiblity modelling # INCLUDED IN DISTRICT HEATING
                       # + df_scen['v_h_tes'] # INCLUDED IN DISTRICT HEATING
                       # + df_scen['v_h_bm'] # INCLUDED IN DISTRICT HEATING
                       # + df_scen['v_h_chpgt'] # INCLUDED IN DISTRICT HEATING
                       # + df_scen['v_h_st'] # INCLUDED IN DISTRICT HEATING
                       # + df_scen['v_h_wte'] # INCLUDED IN DISTRICT HEATING
                       # + df_scen['v_h_hpcp'] # INCLUDED IN DISTRICT HEATING
                       + df_scen['d_h_unmet']
                       )
    # Direct electricity becomes heat at the TES inlet at unity efficiency.
    # Count this conversion once against total TES heat input; HP charging
    # heat is already contained in v_h_hp and must not be added again.
    heat_generation += df_scen.get('u_h_tesdc_direct', 0.0)
    
    # ------------------------------------------------
    # TES for district heating:
    
    # Storage losses are only checked as a sum:
    tes_losses_sum = (
        df_scen['l_u_h_tes']
        + df_scen['l_v_h_tes']
        + df_scen['l_q_h_tes']
        ).sum()
    for k in tes_sites_plotting_inf:
        for k2 in tes_sites_plotting_inf[k]:
            if k2 != 'color':
                if k2.startswith('l_') and '_lt' not in k2:
                    for x in tes_sites_plotting_inf[k][k2]:
                        tes_losses_sum += df_scen[x].sum()

    
    tes_input_sum = df_scen['u_h_tes'].sum()
    
    tes_output_sum = df_scen['v_h_tes'].sum()

    for k in tes_sites_plotting_inf:
        for k2 in tes_sites_plotting_inf[k]:
            if k2 != 'color':
                if k2.startswith('u') and '_lt' not in k2:
                    for x in tes_sites_plotting_inf[k][k2]:
                        tes_input_sum += df_scen[x].sum()
                if k2.startswith('v') and '_lt' not in k2:
                    for x in tes_sites_plotting_inf[k][k2]:
                        tes_output_sum += df_scen[x].sum()



    tes_sos_diff = df_scen['q_h_tes'].iloc[-1] - df_scen['q_h_tes'].iloc[0] # state-of-charge (sos) difference
    
    # ------------------------------------------------
    # TES for decentralised techs:
    
    # Storage losses are only checked as a sum:
    tesdc_losses_sum = (
        df_scen['l_u_h_tesdc']
        + df_scen['l_v_h_tesdc']
        + df_scen['l_q_h_tesdc']
        ).sum()
    
    tesdc_input_sum = df_scen['u_h_tesdc'].sum()
    
    tesdc_output_sum = df_scen['v_h_tesdc'].sum()
    
    tesdc_sos_diff = df_scen['q_h_tesdc'].iloc[-1] - df_scen['q_h_tesdc'].iloc[0] # state-of-charge (sos) difference
    
    # ------------------------------------------------
    # District heating:
    district_heat = df_scen['v_h_dh']
    
    district_heat_techs = (
        + df_scen['v_h_chpgt_con']
        + df_scen['m_h_dh']
        + df_scen['v_h_st_con']
        + df_scen['v_h_wte_con']
        + df_scen['v_h_hpcp']
        + df_scen['v_h_hpcplt']
        + df_scen['v_h_obcp']
        + df_scen['v_h_ehcp']
        + df_scen['v_h_wbcp']
        + df_scen['v_h_wh']
        + df_scen['v_h_dgt']
        + df_scen['v_h_gbcp']
        + df_scen['v_h_bm']
        + df_scen['v_h_tes']
        - df_scen['u_h_tes']
        + df_scen['v_h_vs_dh']
        - df_scen['u_h_vs_dh']
        + df_scen['d_h_unmet_dhn']
        )

    for k in tes_sites_plotting_inf:
        for k2 in tes_sites_plotting_inf[k]:
            if k2 != 'color':
                if k2.startswith('u') and '_lt' not in k2:
                    
                    for x in tes_sites_plotting_inf[k][k2]:
                        district_heat_techs -= df_scen[x]
                if k2.startswith('v') and '_lt' not in k2:
                    
                    for x in tes_sites_plotting_inf[k][k2]:
                        district_heat_techs += df_scen[x]


    # ------------------------------------------------
    # Virtual storage for demand response flexibility from building inertia:
    if 'q_h_vs_tot' in df_scen.columns:
        
        # Storage losses are only checked as a sum:
        vs_losses_sum = ( # virtual storage has no charging/discharging losses
            + df_scen['l_q_h_vs_tot']
            ).sum()
        
        vs_input_sum = df_scen['u_h_vs_tot'].sum()
        
        vs_output_sum = df_scen['v_h_vs_tot'].sum()

    # -------------------------------------------------------------------------
    # Check timeseries
    
    diff_1 = abs(heat_consumption - heat_generation)
    
    max_diff_1 = diff_1.max()
    
    if max_diff_1 > diff_accepted:
        print("Overall heat balance (1) is not fulfilled!")
        print(f"Max. difference (kWh): {max_diff_1}")
        raise Exception("Heat balance (timeseries) is not fulfilled! (1)")
        
    diff_4 = abs(district_heat - district_heat_techs)
    
    max_diff_4 = diff_4.max()
    
    if max_diff_4 > diff_accepted:
        print("Overall heat balance (4) is not fulfilled!")
        print(f"Max. difference (kWh): {max_diff_4}")
        raise Exception("Heat balance (timeseries) is not fulfilled! (4)")
        
        
    # -------------------------------------------------------------------------
    # Check sums:
    
    heat_consumption_sum = heat_consumption.sum()
    
    heat_generation_sum = heat_generation.sum()
    
    district_heat_sum = district_heat.sum()
    
    district_heat_techs_sum = district_heat_techs.sum()
    
    diff_sum_1 = abs(heat_consumption_sum - heat_generation_sum)
    
    # diff_sum_2 = abs(tes_input_sum - tes_output_sum - tes_losses_sum - tes_sos_diff)
    diff_sum_2 = abs(tes_input_sum - tes_output_sum - tes_losses_sum) # assuming cycling constraint
    
    diff_sum_3 = abs(tesdc_input_sum - tesdc_output_sum - tesdc_losses_sum) # assuming cycling constraint
    
    diff_sum_4 = abs(district_heat_sum - district_heat_techs_sum)
    
    if 'q_h_vs_tot' in df_scen.columns:
        diff_sum_5 = abs(vs_input_sum - vs_output_sum - vs_losses_sum) # assuming cycling constraint
    
    if diff_sum_1 > diff_sum_accepted:
        print("Overall heat balance (1) is not fulfilled!")
        print(f"Sum difference (kWh): {diff_sum_1}")
        raise Exception("Heat balance (sum) is not fulfilled! (1)")
    
    if optimisation:
        
        if diff_sum_2 > diff_sum_accepted:
            print("Heat balance (2) is not fulfilled!")
            print(f"Sum difference (kWh): {diff_sum_2}")
            raise Exception("Heat balance (sum) is not fulfilled! (2)")
            
        if diff_sum_3 > diff_sum_accepted:
            print("Heat balance (3) is not fulfilled!")
            print(f"Sum difference (kWh): {diff_sum_3}")
            raise Exception("Heat balance (sum) is not fulfilled! (3)")
            
    if diff_sum_4 > diff_sum_accepted:
        print("Overall heat balance (4) is not fulfilled!")
        print(f"Sum difference (kWh): {diff_sum_4}")
        raise Exception("Heat balance (sum) is not fulfilled! (4)")
        
    if 'q_h_vs_tot' in df_scen.columns:
        if diff_sum_5 > diff_sum_accepted*100: # larger tolerance for virtual storage
            print("Overall heat balance (5) is not fulfilled!")
            print(f"Sum difference (kWh): {diff_sum_5}")
            raise Exception("Heat balance (sum) is not fulfilled! (5)")
        

          
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
