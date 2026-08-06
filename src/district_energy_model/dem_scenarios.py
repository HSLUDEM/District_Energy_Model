# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 07:19:20 2023

@author: UeliSchilt
"""

"""
Functions to create scenarios for the district energy model.

"""

import numpy as np
import pandas as pd

from district_energy_model import dem_helper
from district_energy_model import dem_energy_balance as dem_eb
from district_energy_model import dem_constants as C

# pd.options.mode.chained_assignment = None

def scenario_heater_electric_to_hp(energy_demand, scen_techs, tech_instances):    
    """
    Function to adjust energy system balance in case of direct electric heater replacement
    by heat pumps.
    
    Requirements:
        - scen_techs['heat_pump']['deployment'] == True
    
    Parameters
    ----------
    Returns
    -------
    n/a
    """
    tech_heat_pump = tech_instances['heat_pump']
    tech_grid_supply = tech_instances['grid_supply']
    tech_electric_heater = tech_instances['electric_heater']

    replacement_factor = scen_techs['fossil_heater_retrofit']['electric_boiler_replacement_factor']

    #--------------------------------------------------------------------------
    # Adjust energy accounting of heating technologies:        
    v_h_eh = tech_electric_heater.get_v_h()
    u_e_eh = tech_electric_heater.get_u_e()

    tmp_v_h_shifted = v_h_eh*replacement_factor # [kWh] heat generation shifted from electric heater to heat pump
    tmp_u_e_shifted = u_e_eh*replacement_factor # [kWh] electricity consumption reduced at electric heater

    # Update electric heater:
    v_h_eh_updated = v_h_eh - tmp_v_h_shifted
    tech_electric_heater.update_v_h(v_h_eh_updated)
    
    # Update heat pump:
    v_h_hp = tech_heat_pump.get_v_h()
    u_e_hp = tech_heat_pump.get_u_e()
    v_h_hp_updated = v_h_hp + tmp_v_h_shifted
    tech_heat_pump.update_v_h(v_h_hp_updated)
    u_e_hp_updated = tech_heat_pump.get_u_e()
    tmp_u_e_additional = u_e_hp_updated - u_e_hp - tmp_u_e_shifted

    #--------------------------------------------------------------------------
    # Update total electricity demand:

    tmp_d_e = energy_demand.get_d_e() + tmp_u_e_additional
    energy_demand.update_d_e(tmp_d_e)
    
    tmp_d_e_h = energy_demand.get_d_e_h() + tmp_u_e_additional
    energy_demand.update_d_e_h(tmp_d_e_h)
    
    #--------------------------------------------------------------------------
    # Update local electricity mix:
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances) #ACHTUNG ACHTUNG ACHTUNG, HIER KÖNNTEN FEHLER SEIN!
    tech_grid_supply.update_m_e(tech_grid_supply.get_m_e()) #ACHTUNG ACHTUNG ACHTUNG, HIER KÖNNTEN FEHLER SEIN
    tech_grid_supply.compute_m_e_cbimport()
    
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply) 
    
    del tmp_v_h_shifted
    del tmp_u_e_additional


def scenario_heater_oil_to_hp(energy_demand, scen_techs, tech_instances):    
    """
    Function to adjust energy system balance in case of oil boiler replacement
    by heat pumps.
    
    Requirements:
        - scen_techs['heat_pump']['deployment'] == True
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    tech_oil_boiler : instance of OilBoiler class.
        Instance of oil boiler
    tech_heat_pump : instance of HeatPump class.
        Instance of heat pump
    tech_solar_pv : instance of SolarPV class
        Instance of solar pv.
    tech_wind_power: instance of WindPower class
        Instance of wind power.
    tech_biomass: instance of Biomass class.
        Instance of biomass.
    tech_grid_supply : instance of GridSupply class
        Instance of grid supply.

    Returns
    -------
    n/a
    """
    tech_heat_pump = tech_instances['heat_pump']
    tech_grid_supply = tech_instances['grid_supply']
    tech_oil_boiler = tech_instances['oil_boiler']

    replacement_factor = scen_techs['fossil_heater_retrofit']['oil_boiler_replacement_factor']

    #--------------------------------------------------------------------------
    # Adjust energy accounting of heating technologies:        
    v_h_ob = tech_oil_boiler.get_v_h()
        
    tmp_v_h_shifted = v_h_ob*replacement_factor # [kWh] heat generation shifted from oil boiler to heat pump
    
    # Update oil boiler:
    v_h_ob_updated = v_h_ob - tmp_v_h_shifted
    tech_oil_boiler.update_v_h(v_h_ob_updated)
    
    # Update heat pump:
    v_h_hp = tech_heat_pump.get_v_h()
    u_e_hp = tech_heat_pump.get_u_e()
    v_h_hp_updated = v_h_hp + tmp_v_h_shifted
    tech_heat_pump.update_v_h(v_h_hp_updated)
    u_e_hp_updated = tech_heat_pump.get_u_e()
    tmp_u_e_additional = u_e_hp_updated - u_e_hp

    #--------------------------------------------------------------------------
    # Update total electricity demand:
    tmp_d_e = energy_demand.get_d_e() + tmp_u_e_additional
    energy_demand.update_d_e(tmp_d_e)
    
    tmp_d_e_h = energy_demand.get_d_e_h() + tmp_u_e_additional
    energy_demand.update_d_e_h(tmp_d_e_h)
    
    #--------------------------------------------------------------------------
    # Update local electricity mix:
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances)
    tech_grid_supply.compute_m_e_cbimport()
    
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply) 
    
    del tmp_v_h_shifted
    del tmp_u_e_additional
    
    
def scenario_heater_gas_to_hp(energy_demand, scen_techs, tech_instances):    
    """
    Function to adjust energy system balance in case of gas boiler replacement
    by heat pumps.
    
    Requirements:
        - scen_techs['heat_pump']['deployment'] == True
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dataframe with resulting hourly values
    tech_gas_boiler : instance of GasBoiler class
        Instance of gas boiler.
    tech_heat_pump : instance of HeatPump class.
        Instance of heat pump.
    tech_solar_pv : instance of SolarPV class
        Instance of solar pv.
    tech_wind_power: instance of WindPower class
        Instance of wind power.
    tech_biomass: instance of Biomass class
        Instance of biomass.
    tech_grid_supply : instance of GridSupply class
        Instance of grid supply.

    Returns
    -------
    n/a
    """
    
    tech_heat_pump = tech_instances['heat_pump']
    tech_grid_supply = tech_instances['grid_supply']
    tech_gas_boiler = tech_instances['gas_boiler']

    replacement_factor = scen_techs['fossil_heater_retrofit']['gas_boiler_replacement_factor']


    #--------------------------------------------------------------------------
    # Adjust energy accounting of heating technologies:        
    v_h_gb = tech_gas_boiler.get_v_h()        
    tmp_v_h_shifted = v_h_gb*replacement_factor # [kWh] heat generation shifted from oil boiler to heat pump
    
    # Update oil boiler:
    v_h_gb_updated = v_h_gb - tmp_v_h_shifted
    tech_gas_boiler.update_v_h(v_h_gb_updated)
    
    # Update heat pump:
    v_h_hp = tech_heat_pump.get_v_h()
    u_e_hp = tech_heat_pump.get_u_e()
    v_h_hp_updated = v_h_hp + tmp_v_h_shifted
    tech_heat_pump.update_v_h(v_h_hp_updated)
    u_e_hp_updated = tech_heat_pump.get_u_e()
    tmp_u_e_additional = u_e_hp_updated - u_e_hp
    
    #--------------------------------------------------------------------------
    # Update total electricity demand:    
    tmp_d_e = energy_demand.get_d_e() + tmp_u_e_additional
    energy_demand.update_d_e(tmp_d_e)
    
    tmp_d_e_h = energy_demand.get_d_e_h() + tmp_u_e_additional
    energy_demand.update_d_e_h(tmp_d_e_h)
    
    #--------------------------------------------------------------------------
    # Update local electricity mix:
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances)
    tech_grid_supply.compute_m_e_cbimport()
    
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply)
    
    del tmp_v_h_shifted
    del tmp_u_e_additional
    
    
def scenario_pv_integration(energy_demand, scen_techs, tech_instances):
    """
    Function to adjust energy system balance in case of solar pv integration.
    A specified share of the additional solar pv potential is integrated.
    
    Requirements:
        - scen_techs['solar_pv']['deployment'] == True
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    tech_solar_pv : instance of SolarPV class
        Instance of solar pv.
    tech_wind_power: instance of WindPower class
        Instance of wind power.
    
    tech_grid_supply : instance of GridSupply class
        Instance of grid supply.

    Returns
    -------
    n/a
    """
    techs_solar_pv_to_integrate = scen_techs["pv_integration"]["pv_techs_to_act_on"]

    tech_grid_supply = tech_instances['grid_supply']

    for key in techs_solar_pv_to_integrate:
        ...
        tech_solar_pv = tech_instances[key]
        pvpifs = scen_techs["pv_integration"]["potential_integration_factor"][key]
        if len(pvpifs) != tech_solar_pv.get_num_installations():
            raise ValueError('pv_integration scenario: number of provided ' \
            'pv integration factors does not agree ' \
            'with number of installations (',len(pvpifs), 
            '!=',tech_solar_pv.get_num_installations(), ') for ' \
            'installation type ', key  )
        
        v_e_pvs = tech_solar_pv.get_v_e_from_installations()
        v_e_pv_pot_remain = tech_solar_pv.get_v_e_pot_remain_from_installations()

        v_e_pv_updated = []

        for i in range(len(pvpifs)):

            v_e_pv_updated.append(v_e_pvs[i] + v_e_pv_pot_remain[i]*pvpifs[i])

        tech_solar_pv.update_v_e(v_e_pv_updated)

    #--------------------------------------------------------------------------
    # Update local electricity mix:
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances)
    
    # Update import:
    tech_grid_supply.update_m_e(tech_grid_supply.get_m_e())
    #--------------------------------------------------------------------------
    # Run test for solar pv:    
    df_column_1 = tech_solar_pv.get_v_e()
    df_column_2 = tech_solar_pv.get_v_e_exp() + tech_solar_pv.get_v_e_cons()
    value_1 = df_column_1.sum()
    value_2 = df_column_2.sum()
    
    dem_eb.energy_balance_test(
        value_1=value_1,
        value_2=value_2,
        description='solar pv balance'
        )
    dem_eb.energy_balance_df_test(
        df_column_1=df_column_1,
        df_column_2=df_column_2,
        description='solar pv balance'
        )    
    dem_helper.positive_values_test(
        df_values=tech_solar_pv.get_v_e_pot_remain(),
        description='remaining solar pv potential'
        )
    
    
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply)    
    
def scenario_wind_integration(energy_demand, scen_techs, tech_instances):    
    """
    Function to adjust energy system balance in case of wind power integration.
    A specified share of the additional wind power potential is integrated.
    
    Requirements:
        - scen_techs['wind_power']['deployment'] == True
        - scen_techs['solar_pv']['deployment'] == True
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    tech_solar_pv : instance of SolarPV class
        Instance of solar pv.
    tech_wind_power: instance of WindPower class
        Instance of wind power.
    tech_grid_supply : instance of GridSupply class
        Instance of grid supply.

    Returns
    -------
    n/a
    """
    
    tech_wind_power = tech_instances['wind_power']
    tech_grid_supply = tech_instances['grid_supply']
    
    #--------------------------------------------------------------------------
    # Adjust energy accounting of technologies:
    wppif = scen_techs["wind_integration"]["potential_integration_factor"]

    v_e_wp = tech_wind_power.get_v_e()
    
    v_e_wp_updated = v_e_wp + tech_wind_power.get_v_e_pot_remain()*wppif
    
    tech_wind_power.update_v_e(v_e_wp_updated)
    
    #--------------------------------------------------------------------------
    # Update local electricity mix:
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances)
    
    # Update import:
    tech_grid_supply.update_m_e(tech_grid_supply.get_m_e())
        
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply)   

def scenario_nuclear_phaseout(
        scen_techs,
        tech_instances,
        df_scen,
        ):
    npp_powers = scen_techs["nuclear_phaseout"]["nuclear_power_plant_powers"]

    planned_shutdown = scen_techs["nuclear_phaseout"]["nuclear_power_plant_shutdown_years"]
    
    if scen_techs['scenarios']['demand_side'] and scen_techs['demand_side']['simulation_year']['type'] == 'future':
        year = scen_techs['demand_side']['simulation_year']['future_year']
    else:
        year = C.CURRENT_YEAR

    tech_grid_supply = tech_instances['grid_supply']

    m_e = tech_grid_supply.get_m_e()
    m_e_cbimport = tech_grid_supply.get_m_e_cbimport()
    m_e_ch = tech_grid_supply.get_m_e_ch()
    m_e_ch_hydro = tech_grid_supply.get_m_e_ch_hydro()
    m_e_ch_nuclear = tech_grid_supply.get_m_e_ch_nuclear()
    m_e_ch_wind = tech_grid_supply.get_m_e_ch_wind()
    m_e_ch_biomass = tech_grid_supply.get_m_e_ch_biomass()
    m_e_ch_other = tech_grid_supply.get_m_e_ch_other()

    power_nuc_tot = np.sum(npp_powers)
    powers_still_available = np.sum([npp_powers[i] 
                                    if year < planned_shutdown[i] 
                                    else 0.0 
                                    for i in range(len(planned_shutdown))])

    nuclear_fraction = powers_still_available / power_nuc_tot

    m_e_ch_nuclear_new = nuclear_fraction * m_e_ch_nuclear

    m_e_ch_new = (m_e_ch_hydro
              + m_e_ch_nuclear_new
              + m_e_ch_wind
              + m_e_ch_biomass
              + m_e_ch_other)

    tech_grid_supply.set_m_e_ch_nuclear(m_e_ch_nuclear_new)

    tech_grid_supply.set_m_e_ch(m_e_ch_new)

    tech_grid_supply.compute_m_e_cbimport()

    __test_import_balance(tech_grid_supply)   



def scenario_battery_energy_storage_via_pv(energy_demand, 
                                           scen_techs, 
                                           tech_instances):
    tech_bes = tech_instances['bes']
    tech_solar_pv = tech_instances['solar_pvrooftop']
    tech_wind_power = tech_instances['wind_power']
    tech_biomass = tech_instances['biomass']
    tech_hydro_power = tech_instances['hydro_power']
    tech_grid_supply = tech_instances['grid_supply']
    
    bes_cap = scen_techs['battery_energy_storage_scenario']['capacity_kWh']
    bes_ic = scen_techs['battery_energy_storage_scenario']['initial_charge'] 

    if tech_bes.get_cap() != 'inf':
        if tech_bes.get_cap() < bes_cap:
            tech_bes.set_cap(bes_cap)



    if bes_cap > 0:
        df = pd.DataFrame()
        len_df = len(tech_bes.get_v_e())
        
        # Add columns to df:
        df['tmp_bes_cap_avl'] = [0.0]*len_df # [kWh] available storage capacity

        tech_bes.update_q_e_i(0, bes_ic*bes_cap)
        df.loc[0, 'tmp_bes_cap_avl'] = bes_cap - tech_bes.get_q_e()[0]   
        
        # Creat lumped variable for renewable energy generation:
        v_e_renewable = (
            tech_solar_pv.get_v_e()
            + tech_wind_power.get_v_e()
            + tech_biomass.get_v_e()
            + tech_hydro_power.get_v_e()
            )
        
        # Creat lumped variable for renewable energy export:
        v_e_exp_renewable = (
            tech_solar_pv.get_v_e_exp()
            + tech_wind_power.get_v_e_exp()
            + tech_biomass.get_v_e_exp()
            + tech_hydro_power.get_v_e_exp()
            )
        for i, hr in enumerate(tech_bes.get_q_e()):
            if i > 0:
                #Apply storage loss
                tech_bes.update_l_q_e_i(i-1, tech_bes.get_q_e()[i-1]*tech_bes.get_gamma() )
                tech_bes.update_q_e_i(i, tech_bes.get_q_e()[i-1] * (1-tech_bes.get_gamma()))
                df.loc[i, 'tmp_bes_cap_avl'] = bes_cap - tech_bes.get_q_e()[i]
            elif i == 0:
                pass

            if v_e_exp_renewable[i] > 0.0: #charge battery

                #determine allowed amount of charged energy
                charging_rate = min([bes_cap*tech_bes.get_chg_dchg_per_cap_max(), 
                                     df.loc[i, 'tmp_bes_cap_avl']/tech_bes.get_eta_chg_dchg(), 
                                     v_e_exp_renewable[i]])
                
                #apply charging
                tech_bes.update_u_e_i(i, charging_rate)
                tech_bes.update_v_e_i(i, 0.0)
                tech_bes.update_q_e_i(i, tech_bes.get_q_e()[i] + charging_rate*tech_bes.get_eta_chg_dchg())
                tech_bes.update_l_u_e_i(i, tech_bes.get_u_e()[i]*(1.0-tech_bes.get_eta_chg_dchg()))
                tech_bes.update_l_v_e_i(i, tech_bes.get_v_e()[i]*((1.0 / tech_bes.get_eta_chg_dchg() )-1.0))
                tech_bes.update_sos_i(i, tech_bes.get_q_e()[i] / bes_cap)

            else: #discharge battery (or leave it at the same charge level)
                
                #determine maximum discharging
                unmet_demand = energy_demand.get_d_e()[i] - v_e_renewable[i]
                max_discharge_rate = bes_cap*tech_bes.get_chg_dchg_per_cap_max()
                stored_energy_bes = tech_bes.get_q_e()[i]*tech_bes.get_eta_chg_dchg()
                discharge_rate = min([unmet_demand, max_discharge_rate, stored_energy_bes])

                #apply discharge
                tech_bes.update_u_e_i(i, 0.0)
                tech_bes.update_v_e_i(i, discharge_rate)
                tech_bes.update_q_e_i(i, tech_bes.get_q_e()[i] - discharge_rate/tech_bes.get_eta_chg_dchg())
                tech_bes.update_l_u_e_i(i, tech_bes.get_u_e()[i]*(1.0-tech_bes.get_eta_chg_dchg()))
                tech_bes.update_l_v_e_i(i, tech_bes.get_v_e()[i]*((1.0 / tech_bes.get_eta_chg_dchg() )-1.0))
                tech_bes.update_sos_i(i, tech_bes.get_q_e()[i] / bes_cap)
                tech_instances['grid_supply'].update_m_e_i(i, tech_instances['grid_supply'].get_m_e()[i] - discharge_rate)
            
    #Adjust import/export balance
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances, with_bes = True)
    tech_grid_supply.update_m_e(tech_grid_supply.get_m_e())
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply) 






def scenario_thermal_energy_storage_via_pv_hp(
        energy_demand, 
        scen_techs, 
        tech_instances
        ):

    """
    Function to adjust energy system balance in case of thermal energy storage
    dispatch. The thermal energy storage unit is charged via heat pump, taking
    electricity from decentralised renewables only (PV, wind, biomass, hydro).
    
    Requirements:
        - scen_techs['tes_decentralised']['deployment'] == True
        - scen_techs['heat_pump']['deployment'] == True
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dictionary with reulting annual values.
    tech_solar_pv : instance of SolarPV class
        Instance of solar pv.
    tech_grid_supply : instance of GridSupply class
        Instance of grid supply.

    Returns
    -------
    n/a
    """
    
    tech_tesdc = tech_instances['tes_decentralised']
    tech_solar_pv = tech_instances['solar_pvrooftop']
    tech_wind_power = tech_instances['wind_power']
    tech_biomass = tech_instances['biomass']
    tech_hydro_power = tech_instances['hydro_power']
    tech_heat_pump = tech_instances['heat_pump']
    tech_grid_supply = tech_instances['grid_supply']
    tech_electric_heater = tech_instances['electric_heater']
    
    tech_heat_pump.calculate_effective_cops()

    tesdc_cap = scen_techs['thermal_energy_storage_scenario']['capacity_kWh']
    tesdc_ic = scen_techs['thermal_energy_storage_scenario']['initial_charge']
    
    dem_helper.check_number(
        value=tesdc_cap, 
        var_name='thermal_energy_storage_scenario.capacity_kWh',
        check_positive=True
        )
    dem_helper.check_number(
        value=tesdc_ic, 
        var_name='thermal_energy_storage_scenario.initial_charge',
        check_positive=True
        )

    if tech_tesdc.get_cap() != 'inf':
        if tech_tesdc.get_cap() < tesdc_cap:
            tech_tesdc.set_cap(tesdc_cap)
    
    if tesdc_cap == 'inf':
        raise ValueError("TES capacity cannot be 'inf' in manual thermal_energy_storage scenario. Change to numeric value.")
    
    if tesdc_cap > 0:
        # Creat temporary df for calculations:
        df = pd.DataFrame()
        
        len_df = len(tech_tesdc.get_v_h())
        
        # Add columns to df:
        df['tmp_tes_cap_avl'] = [0.0]*len_df # [kWh] available storage capacity

        # Initialise storage level and available capacity[kWh]:
        tech_tesdc.update_q_h_i(0, tesdc_ic*tesdc_cap)
        
        df.loc[0, 'tmp_tes_cap_avl'] = tesdc_cap - tech_tesdc.get_q_h()[0]        
        
        # For code optimisation:
        case_A_counter = 0
        case_B_counter = 0
        case_C_counter = 0
        
        # Creat lumped variable for renewable energy generation:
        v_e_renewable = (
            tech_solar_pv.get_v_e()
            + tech_wind_power.get_v_e()
            + tech_biomass.get_v_e()
            + tech_hydro_power.get_v_e()
            )
        
        # Creat lumped variable for renewable energy export:
        v_e_exp_renewable = (
            tech_solar_pv.get_v_e_exp()
            + tech_wind_power.get_v_e_exp()
            + tech_biomass.get_v_e_exp()
            + tech_hydro_power.get_v_e_exp()
            )
        
        # Loop through hourly timesteps to simulate evolution of storage:   
        for i, hr in enumerate(tech_tesdc.get_q_h()):

            # Bring forward TES charging level and available capacity from previous timestep:
            if i > 0:
                tech_tesdc.update_q_h_i(i, tech_tesdc.get_q_h()[i-1])
                df.loc[i, 'tmp_tes_cap_avl'] = tesdc_cap - tech_tesdc.get_q_h()[i]
                
            elif i == 0:
                tech_tesdc.update_q_h_i(i, tesdc_cap*tesdc_ic)
                # values have been initialised
                pass
            # If no renewable electricity is available, check if stored heat can be used for heating (i.e. discharging):
            if v_e_renewable[i] == 0:

                case_A_counter += 1
                # print("Case A")
                
                if tech_tesdc.get_q_h()[i] > 0 and tech_heat_pump.get_v_h()[i] > 0:
                    
                    if tech_tesdc.get_q_h()[i] >= tech_heat_pump.get_v_h()[i]:
                        # hp operation will be replaced completely with TES discharging:
                        
                        # Update tes:
                        tech_tesdc.update_u_h_i(i, 0.0)
                        tech_tesdc.update_v_h_i(i, tech_heat_pump.get_v_h()[i])
                        tech_tesdc.update_q_h_i(
                            i, 
                            tech_tesdc.get_q_h()[i] + tech_tesdc.get_u_h()[i] - tech_tesdc.get_v_h()[i]
                            )
                        
                        # Update PV: no change
                        
                        # Update heat pump:
                        tech_heat_pump.update_v_h_i(i, 0.0) # Heat pump operation replaced by TES discharging
                    
                        # Electricity balances:
                        tmp_u_e_hp_tesdchg =\
                            tech_heat_pump.electricity_input(tech_tesdc.get_v_h()[i],i) # reduced electricity demand due to replacement of heat pump activity
                        
                        # Update electricity demand
                        d_e_i_updated = energy_demand.get_d_e()[i] - tmp_u_e_hp_tesdchg
                        energy_demand.update_d_e_i(i,d_e_i_updated)
                        d_e_h_i_updated = energy_demand.get_d_e_h()[i] - tmp_u_e_hp_tesdchg
                        energy_demand.update_d_e_h_i(i,d_e_h_i_updated)                  
                        
                        # TEMPORARY:
                        if tech_tesdc.get_v_h()[i] < -1e-10:
                            print(f'v_h_tes_i: {tech_tesdc.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_tes_i (3) of {tech_tesdc.get_v_h()[i]}')
                        elif tech_heat_pump.get_v_h()[i] < -1e-10:
                            print(f'v_h_hp_i: {tech_heat_pump.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_hp_i (3) of {tech_heat_pump.get_v_h()[i]}')
                            
                            # TEMPORARY:
                            if tech_tesdc.get_q_h()[i] < -1e-10:
                                raise Exception(f'NEGATIVE q_h_tes_i (3b) of {tech_tesdc.get_q_h()[i]}')
                        
                        del tmp_u_e_hp_tesdchg
                    
                    elif tech_tesdc.get_q_h()[i] > 0 and tech_tesdc.get_q_h()[i] < tech_heat_pump.get_v_h()[i]:
                        # hp operation will partially be replaced with TES discharging:
                        
                        # Update tes:
                        tech_tesdc.update_u_h_i(i, 0.0)
                        tech_tesdc.update_v_h_i(i, tech_tesdc.get_q_h()[i])
                        q_h_tes_new = tech_tesdc.get_q_h()[i] + tech_tesdc.get_u_h()[i] - tech_tesdc.get_v_h()[i]
                        tech_tesdc.update_q_h_i(i, q_h_tes_new)
                        
                        # Update PV: no change
                        
                        # Update heat pump:
                        v_h_hp_new = tech_heat_pump.get_v_h()[i] - tech_tesdc.get_v_h()[i]
                        tech_heat_pump.update_v_h_i(i, v_h_hp_new) # Heat pump operation partially replaced by TES discharging                    
                        
                        # Update electricity import:
                        tmp_u_e_hp_tesdchg =\
                            tech_heat_pump.electricity_input(tech_tesdc.get_v_h()[i],i) # reduced electricity demand
                        # df_scen.loc[i, 'd_e'] = (df_scen.loc[i, 'd_e'] -
                        #                      tmp_u_e_hp_tesdchg) # reducing the overall electricity demand
                        # df_scen.loc[i, 'd_e_h'] = (df_scen.loc[i, 'd_e_h'] -
                        #                        tmp_u_e_hp_tesdchg) # reducing the electrictiy demand for heating
                        d_e_i_updated = energy_demand.get_d_e()[i] - tmp_u_e_hp_tesdchg
                        energy_demand.update_d_e_i(i, d_e_i_updated)
                        d_e_h_i_updated = energy_demand.get_d_e_h()[i] - tmp_u_e_hp_tesdchg
                        energy_demand.update_d_e_h_i(i, d_e_h_i_updated)

                        #TEMPORARY:
                        if tech_tesdc.get_v_h()[i] < -1e-10:
                            print(f'v_h_tes_i: {tech_tesdc.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_tes_i (4) of {tech_tesdc.get_v_h()[i]}')
                        elif tech_heat_pump.get_v_h()[i] < -1e-10:
                            print(f'v_h_hp_i: {tech_heat_pump.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_hp_i (4) of {tech_heat_pump.get_v_h()[i]}')
                            
                        #TEMPORARY:
                        if tech_tesdc.get_q_h()[i] < -1e-10:
                            raise Exception(f'NEGATIVE q_h_tes_i (4b) of {tech_tesdc.get_q_h()[i]}')
                        
                        del tmp_u_e_hp_tesdchg
            
            # If renewable el. is available, but no excess, check if stored heat can be used for heating (i.e. discharging):
            elif v_e_renewable[i] > 0 and v_e_exp_renewable[i] == 0:
                case_B_counter += 1
                # print("Case B")
                
                # Electricity demand not replacable by TES:
                tmp_d_e_non_repl = (
                    energy_demand.get_d_e_baseline()[i]
                    + tech_electric_heater.get_u_e()[i]
                    + energy_demand.get_d_e_ev()[i]
                    )
                
                # Demand replacable by TES (heat and electricity):
                tmp_d_e_repl = tech_heat_pump.get_u_e()[i]
                tmp_d_h_repl = tech_heat_pump.get_v_h()[i]
                
                if tech_tesdc.get_q_h()[i] == 0:
                    pass
                
                elif tmp_d_e_non_repl >= v_e_renewable[i]:
                    # Renewable el. will be used completely for non-replacable e-demand
                    # Replacable e-demand will be served by TES.
                    
                    if tech_tesdc.get_q_h()[i] >= tmp_d_h_repl:
                        # Enough energy stored in the TES to cover all of the
                        # replacable heat demand
                        
                        # Update tes:
                        tech_tesdc.update_u_h_i(i,0.0)
                        tech_tesdc.update_v_h_i(i,tmp_d_h_repl)
                        q_h_tes_i_updated = tech_tesdc.get_q_h()[i] - tmp_d_h_repl
                        tech_tesdc.update_q_h_i(i,q_h_tes_i_updated)
                        
                        # Update PV: no change
                        
                        # Update heat pump:
                        tech_heat_pump.update_v_h_i(i,0.0)
                        
                        # Update electricity demand                       
                        tmp_u_e_hp_tesdchg =\
                            tech_heat_pump.electricity_input(tech_tesdc.get_v_h()[i],i) # reduced electricity demand
                        d_e_i_updated = energy_demand.get_d_e()[i] - tmp_u_e_hp_tesdchg
                        d_e_h_i_updated = energy_demand.get_d_e_h()[i] - tmp_u_e_hp_tesdchg
                        energy_demand.update_d_e_i(i,d_e_i_updated)
                        energy_demand.update_d_e_h_i(i,d_e_h_i_updated)

                        # TEMPORARY:
                        if tech_tesdc.get_v_h()[i] < -1e-10:
                            print(f'v_h_tes_i: {tech_tesdc.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_tes_i (5) of {tech_tesdc.get_v_h()[i]}')
                        elif tech_heat_pump.get_v_h()[i] < -1e-10:
                            print(f'v_h_hp_i: {tech_heat_pump.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_hp_i (5) of {tech_heat_pump.get_v_h()[i]}')
                        
                        # TEMPORARY:
                        if tech_tesdc.get_q_h()[i] < -1e-10:
                            raise Exception(f'NEGATIVE q_h_tes_i (5b) of {tech_tesdc.get_q_h()[i]}')
                        
                        del tmp_u_e_hp_tesdchg
                    
                    elif tech_tesdc.get_q_h()[i] < tmp_d_h_repl:
                        # Not enough energy stored in the TES to cover all of the
                        # replacable heat demand. Only part of the replacable
                        # heat demand can be covered by TES.
                        
                        # TEMPORARY:
                        if tech_tesdc.get_q_h()[i] < -1e-10:
                            raise Exception(f'NEGATIVE q_h_tes_i (6a) of {tech_tesdc.get_q_h()[i]}')
                        
                        # Update tes:
                        tech_tesdc.update_u_h_i(i,0.0)
                        tech_tesdc.update_v_h_i(i,tech_tesdc.get_q_h()[i]) # the TES is emptied
                        tech_tesdc.update_q_h_i(i,0.0)
                        
                        # Update PV: no change
                        
                        # Update heat pump:
                        tmp_u_e_hp_tesdchg =\
                            tech_heat_pump.electricity_input(tech_tesdc.get_v_h()[i],i) # reduced electricity demand
                        v_h_hp_updated = tech_heat_pump.get_v_h()[i] - tech_tesdc.get_v_h()[i]
                        tech_heat_pump.update_v_h_i(i,v_h_hp_updated)                        
                        
                        # Update electricity demand  
                        d_e_i_updated = energy_demand.get_d_e()[i] - tmp_u_e_hp_tesdchg
                        d_e_h_i_updated = energy_demand.get_d_e_h()[i] - tmp_u_e_hp_tesdchg
                        energy_demand.update_d_e_i(i,d_e_i_updated)
                        energy_demand.update_d_e_h_i(i,d_e_h_i_updated)

                        # TEMPORARY:
                        if tech_tesdc.get_v_h()[i] < -1e-10:
                            print(f'v_h_tes_i: {tech_tesdc.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_tes_i (6) of {tech_tesdc.get_v_h()[i]}')
                        elif tech_heat_pump.get_v_h()[i] < -1e-10:
                            print(f'v_h_hp_i: {tech_heat_pump.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_hp_i (6) of {tech_heat_pump.get_v_h()[i]}')
                        
                        del tmp_u_e_hp_tesdchg
                
                elif tmp_d_e_non_repl < v_e_renewable[i]:
                    # part of the replacable electricity demand is already covered by renewable el.
                    
                    # Part of the repl. el. demand that is covered by renewable el.:
                    tmp_v_e_ren_for_hp = v_e_renewable[i] - tmp_d_e_non_repl
                    
                    # Part of the repl. demand that can be covered by TES:
                    tmp_d_e_repl_tes = tmp_d_e_repl - tmp_v_e_ren_for_hp
                    tmp_d_h_repl_tes = tech_heat_pump.heat_output(tmp_d_e_repl_tes,i)
                    
                    if tech_tesdc.get_q_h()[i] >= tmp_d_h_repl_tes:
                        
                        # Update tes:
                        tech_tesdc.update_u_h_i(i,0.0)
                        tech_tesdc.update_v_h_i(i,tmp_d_h_repl_tes)
                        q_h_tes_i_updated = tech_tesdc.get_q_h()[i] - tmp_d_h_repl_tes
                        tech_tesdc.update_q_h_i(i,q_h_tes_i_updated)
                        
                        # Update PV: no change
                        
                        # Update heat pump:
                        v_h_hp_updated = tech_heat_pump.get_v_h()[i] - tech_tesdc.get_v_h()[i]
                        tech_heat_pump.update_v_h_i(i,v_h_hp_updated)
                        
                        # Update electricity demand:
                        d_e_i_updated = energy_demand.get_d_e()[i] - tmp_d_e_repl_tes
                        d_e_h_i_updated = energy_demand.get_d_e_h()[i] - tmp_d_e_repl_tes
                        energy_demand.update_d_e_i(i,d_e_i_updated)
                        energy_demand.update_d_e_h_i(i,d_e_h_i_updated)

                        # TEMPORARY:
                        if tech_tesdc.get_v_h()[i] < -1e-10:
                            print(f'v_h_tes_i (i={i}): {tech_tesdc.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_tes_i (7) of {tech_tesdc.get_v_h()[i]}')
                        elif tech_heat_pump.get_v_h()[i] < -1e-10:
                            print(f'v_h_hp_i (i={i}): {tech_heat_pump.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_hp_i (7) of {tech_heat_pump.get_v_h()[i]}')
                        
                        # TEMPORARY:
                        if tech_tesdc.get_q_h()[i] < -1e-10:
                            print(tech_tesdc.get_v_h()[i])
                            raise Exception(f'NEGATIVE q_h_tes_i (7b) of {tech_tesdc.get_q_h()[i]}')
                        
                    elif tech_tesdc.get_q_h()[i] < tmp_d_h_repl_tes:
                        
                        # Update tes:
                        tech_tesdc.update_u_h_i(i,0.0)
                        tech_tesdc.update_v_h_i(i,tech_tesdc.get_q_h()[i])
                        tech_tesdc.update_q_h_i(i,0.0)
                        
                        # Update PV: no change
                        
                        # Update heat pump:
                        tmp_u_e_hp_tesdchg =\
                            tech_heat_pump.electricity_input(tech_tesdc.get_v_h()[i],i) # reduced electricity demand
                        v_h_hp_updated = tech_heat_pump.get_v_h()[i] - tech_tesdc.get_v_h()[i]
                        tech_heat_pump.update_v_h_i(i,v_h_hp_updated)
                        
                        # Update electricity demand
                        d_e_i_updated = energy_demand.get_d_e()[i] - tmp_u_e_hp_tesdchg
                        d_e_h_i_updated = energy_demand.get_d_e_h()[i] - tmp_u_e_hp_tesdchg
                        energy_demand.update_d_e_i(i,d_e_i_updated)
                        energy_demand.update_d_e_h_i(i,d_e_h_i_updated)

                        # TEMPORARY:
                        if tech_tesdc.get_v_h()[i] < -1e-10:
                            print(f'v_h_tes_i: {tech_tesdc.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_tes_i (8) of {tech_tesdc.get_v_h()[i]}')
                        elif tech_heat_pump.get_v_h()[i] < -1e-10:
                            print(f'v_h_hp_i: {tech_heat_pump.get_v_h()[i]}')
                            raise Exception(f'NEGATIVE v_h_hp_i (8) of {tech_heat_pump.get_v_h()[i]}')
                        
                        # TEMPORARY:
                        if tech_tesdc.get_q_h()[i] < -1e-10:
                            print(tech_tesdc.get_v_h()[i])
                            raise Exception(f'NEGATIVE q_h_tes_i (8b) of {tech_tesdc.get_q_h()[i]}')
                    
                    
                    
                    del tmp_v_e_ren_for_hp
                    del tmp_d_e_repl_tes
                    del tmp_d_h_repl_tes
                                   
                del tmp_d_e_non_repl
                del tmp_d_e_repl
                del tmp_d_h_repl
                
            # check if excess renewable el. is available that can be used to charge TES:
            elif v_e_exp_renewable[i] > 0:
                case_C_counter += 1
                # print("Case C")
                
                # Calculate potential heat generation from excess renewable el.:
                tmp_v_h_hp_ren_exp = tech_heat_pump.heat_output(
                    v_e_exp_renewable[i],i
                    )
            
                if tmp_v_h_hp_ren_exp <= df.loc[i, 'tmp_tes_cap_avl']:
                    # There is enough capacity to absorb all excess pv:
                    
                    # Update TES:
                    tech_tesdc.update_u_h_i(i,tmp_v_h_hp_ren_exp)
                    tech_tesdc.update_v_h_i(i,0.0)
                    q_h_tes_i_updated = tech_tesdc.get_q_h()[i] + tech_tesdc.get_u_h()[i] - tech_tesdc.get_v_h()[i]
                    tech_tesdc.update_q_h_i(i,q_h_tes_i_updated)
                    
                    # Update renewable share for charging:
                    tmp_v_e_ren_tescharging = v_e_exp_renewable[i] # electricity for charging TES via hp
                    
                    # Update heat pump:
                    v_h_hp_updated = tech_heat_pump.get_v_h()[i] + tech_tesdc.get_u_h()[i]
                    tech_heat_pump.update_v_h_i(i,v_h_hp_updated)
                    
                    # Update electricity demand:
                    d_e_i_updated = energy_demand.get_d_e()[i] + tmp_v_e_ren_tescharging
                    d_e_h_i_updated = energy_demand.get_d_e_h()[i] + tmp_v_e_ren_tescharging
                    energy_demand.update_d_e_i(i,d_e_i_updated)
                    energy_demand.update_d_e_h_i(i,d_e_h_i_updated)
                    
                    del tmp_v_e_ren_tescharging

                    # TEMPORARY:
                    if tech_tesdc.get_v_h()[i] < -1e-10:
                        print(f'v_h_tes_i: {tech_tesdc.get_v_h()[i]}')
                        raise Exception(f'NEGATIVE v_h_tes_i (1) of {tech_tesdc.get_v_h()[i]}')
                    elif tech_heat_pump.get_v_h()[i] < -1e-10:
                        print(f'v_h_hp_i: {tech_heat_pump.get_v_h()[i]}')
                        raise Exception(f'NEGATIVE v_h_hp_i (1) of {tech_heat_pump.get_v_h()[i]}')
                        
                    # TEMPORARY:
                    if tech_tesdc.get_q_h()[i] < -1e-10:
                        raise Exception(f'NEGATIVE q_h_tes_i (1b) of {tech_tesdc.get_q_h()[i]}')
                    
                elif tmp_v_h_hp_ren_exp > df.loc[i, 'tmp_tes_cap_avl']:
                    # The TES will be fully charged and excess pv exported:
                     
                    # Update tes:
                    tech_tesdc.update_u_h_i(i,df.loc[i, 'tmp_tes_cap_avl']) # TES is fully charged
                    tech_tesdc.update_v_h_i(i,0.0)
                    q_h_tes_i_updated = tech_tesdc.get_q_h()[i] + tech_tesdc.get_u_h()[i] - tech_tesdc.get_v_h()[i]
                    tech_tesdc.update_q_h_i(i,q_h_tes_i_updated)
                    
                    # Update renewable share for charging:
                    tmp_v_e_ren_tescharging =\
                        tech_heat_pump.electricity_input(tech_tesdc.get_u_h()[i],i)
                    
                    # Update heat pump:
                    v_h_hp_updated = tech_heat_pump.get_v_h()[i] + tech_tesdc.get_u_h()[i]
                    tech_heat_pump.update_v_h_i(i,v_h_hp_updated)
                    
                    # Update electricity demand:
                    d_e_i_updated = energy_demand.get_d_e()[i] + tmp_v_e_ren_tescharging
                    d_e_h_i_updated = energy_demand.get_d_e_h()[i] + tmp_v_e_ren_tescharging
                    energy_demand.update_d_e_i(i,d_e_i_updated)
                    energy_demand.update_d_e_h_i(i,d_e_h_i_updated)
                    
                    del tmp_v_e_ren_tescharging
                    
                    # TEMPORARY:
                    if tech_tesdc.get_v_h()[i] < -1e-10:
                        print(f'v_h_tes_i: {tech_tesdc.get_v_h()[i]}')
                        raise Exception(f'NEGATIVE v_h_tes_i (2) of {tech_tesdc.get_v_h()[i]}')
                    elif tech_heat_pump.get_v_h()[i] < -1e-10:
                        print(f'v_h_hp_i: {tech_heat_pump.get_v_h()[i]}')
                        raise Exception(f'NEGATIVE v_h_hp_i (2) of {tech_heat_pump.get_v_h()[i]}')
                        
                        # TEMPORARY:
                        if tech_tesdc.get_q_h()[i] < -1e-10:
                            raise Exception(f'NEGATIVE q_h_tes_i (2b) of {tech_tesdc.get_q_h()[i]}')
                
                del tmp_v_h_hp_ren_exp
            
            tech_tesdc.update_sos_i(i, tech_tesdc.get_q_h()[i] / tesdc_cap)


            # Loop end
            #------------------------------------------------------------------
            
        del df['tmp_tes_cap_avl']
        
        # print(f'No. of case A occurrences: {case_A_counter}')
        # print(f'No. of case B occurrences: {case_B_counter}')
        # print(f'No. of case C occurrences: {case_C_counter}')
            
    elif tesdc_cap == 0.0:
        print(" TES capacity (tech_tesdc_cap): 0 kWh.")
        pass
    
    #--------------------------------------------------------------------------
    # Update electricity mix:
        
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances, with_bes = ("bes" in tech_instances.keys()))

    # Update import:
    tech_grid_supply.update_m_e(tech_grid_supply.get_m_e())

    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply) 

    
def __test_import_balance(tech_grid_supply):
    
    #--------------------------------------------------------------------------
    # Run tests for import:

    sum_a = dem_helper.get_m_e_ch_sum(tech_grid_supply)

    sum_b = (
        sum(tech_grid_supply.get_m_e_ch())
        + sum(tech_grid_supply.get_m_e_cbimport())
        )

    dem_eb.energy_balance_test(
        sum(tech_grid_supply.get_m_e_ch()),
        sum_a,
        'electricity mix'
        )

    dem_eb.energy_balance_test(sum(tech_grid_supply.get_m_e()),
                                   sum_b,
                                   'electricity import'
                                   )

    dem_eb.energy_balance_df_test(
        tech_grid_supply.get_m_e(),
        tech_grid_supply.get_m_e_ch() + tech_grid_supply.get_m_e_cbimport(),
        'electricity import df'
        )     

    dem_helper.positive_values_test(tech_grid_supply.get_m_e(),
                                    'total import'
                                    )
    dem_helper.positive_values_test(tech_grid_supply.get_m_e_ch(),
                                    'swiss import'
                                    )
    dem_helper.positive_values_test(tech_grid_supply.get_m_e_cbimport(),
                                    'cross-border import'
                                    ) 
    
    
    
    
    