# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 17:33:11 2024

@author: UeliSchilt
"""

import pandas as pd

def add_emissions_CO2(scen_techs, df_scen):
    """
    Add columns to df_scen for CO2 emissions [kg] for each technology.

    Parameters
    ----------
    scen_techs : dict
        Inputs dictionary according to inputs.py.
    df_scen : pandas dataframe
        Resulting dataframe with hourly values for inputs and outputs.

    Returns
    -------
    df_scen : pandas dataframe
        Resulting dataframe with hourly values for inputs and outputs, with
        columns for CO2 emissions added [kg].

    """

    # Question: consumed vs produced energy?
    # Currently: produced energy is looked at
    
    # Heat pump:
    df_scen['v_co2_hp'] = df_scen['v_h_hp']*scen_techs['heat_pump']['co2_intensity']

    # Electric heater:
    df_scen['v_co2_eh'] = df_scen['v_h_eh']*scen_techs['electric_heater']['co2_intensity']
    
    # Oil boiler emissions:
    df_scen['v_co2_ob'] = df_scen['v_h_ob']*scen_techs['oil_boiler']['co2_intensity']
        
    # Gas boiler emissions:
    df_scen['v_co2_gb'] = df_scen['v_h_gb']*scen_techs['gas_boiler']['co2_intensity']
        
    # Wood boiler emissions:
    df_scen['v_co2_wb'] = df_scen['v_h_wb']*scen_techs['wood_boiler']['co2_intensity']
        
    # District Heating:
    df_scen['v_co2_dh'] = df_scen['v_h_dh']*scen_techs['district_heating']['co2_intensity']
    
    # Solar Thermal:
    df_scen['v_co2_solar'] = df_scen['v_h_solar']*scen_techs['solar_thermal']['co2_intensity']
    
    # Solar PV (local):
    df_scen['v_co2_pv'] = df_scen['v_e_pv']*scen_techs['solar_pv']['co2_intensity']
    
    # Wind Power (local):
    df_scen['v_co2_wp'] = df_scen['v_e_wp']*scen_techs['wind_power']['co2_intensity']
    
    # Hydro Power (local):
    df_scen['v_co2_hydro'] = df_scen['v_e_hydro']*scen_techs['hydro_power']['co2_intensity']
       
    # Grid Supply:
    df_scen['v_co2_grid'] = df_scen['m_e']*scen_techs['grid_supply']['co2_intensity']
              
    # TES:
    df_scen['v_co2_tes'] = df_scen['v_h_tes']*scen_techs['tes']['co2_intensity']
    
    # BES:
    df_scen['v_co2_bes'] = df_scen['v_e_bes']*scen_techs['bes']['co2_intensity']
    
    # GTES:
    df_scen['v_co2_gtes'] = df_scen['v_gas_gtes']*scen_techs['gtes']['co2_intensity']

    # HES:
    df_scen['v_co2_hes'] = df_scen['v_hyd_hes']*scen_techs['hes']['co2_intensity']

    
    # -------------------------------------------------------------------------
    # BIOMASS // -- UNDER CONSTRUCTION --
    
    # Hydrothermal gasification:
    df_scen['v_co2_hg'] = df_scen['v_gas_hg']*scen_techs['hydrothermal_gasification']['co2_intensity']
    
    # anaerobic_digestion_upgrade:
    df_scen['v_co2_agu'] = df_scen['v_gas_agu']*scen_techs['anaerobic_digestion_upgrade']['co2_intensity']
    
    # anaerobic_digestion_upgrade_hydrogen:
    df_scen['v_co2_aguh'] = df_scen['v_gas_aguh']*scen_techs['anaerobic_digestion_upgrade_hydrogen']['co2_intensity']
    
    # anaerobic_digestion_chp:
    df_scen['v_co2_aguc'] = df_scen['v_e_aguc']*scen_techs['anaerobic_digestion_chp']['co2_intensity']
    
    # wood_gasification_upgrade:
    df_scen['v_co2_wgu'] = df_scen['v_gas_wgu']*scen_techs['wood_gasification_upgrade']['co2_intensity']
    
    # wood_gasification_upgrade_hydrogen:
    df_scen['v_co2_wguh'] = df_scen['v_gas_wguh']*scen_techs['wood_gasification_upgrade_hydrogen']['co2_intensity']
    
    # wood_gasification_chp:
    df_scen['v_co2_wguc'] = df_scen['v_e_wguc']*scen_techs['wood_gasification_chp']['co2_intensity']
    
    # hydrogen_production:
    df_scen['v_co2_hydp'] = df_scen['v_hyd_hydp']*scen_techs['hydrogen_production']['co2_intensity']
    
    # -------------------------------------------------------------------------
    
    
    # chp_gt:
    df_scen['v_co2_chp_gt'] = df_scen['v_e_chp_gt']*scen_techs['chp_gt']['co2_intensity']
    
    return df_scen

def get_tech_emissions_CO2():
    
    ...