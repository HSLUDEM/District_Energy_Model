# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 14:12:26 2024

@author: UeliSchilt
"""

from district_energy_model.input_files import inputs as inp

oil_density = 0.85  # kg/L
fossil_heating_capacity = 0
eh_heating_capacity = 0
number_of_years = 0

def capex_heat_pump(scen_techs):
    capex = scen_techs['heat_pump']['capex_cost']*(fossil_heating_capacity*inp.fhrp + eh_heating_capacity*inp.ehrp)
    return capex

def opex_heat_pump(scen_techs, df_scen):
    yearly_maintenance = scen_techs['heat_pump']['maintenance_cost']*scen_techs["heat_pump"]['kW_th_max']
    opex = yearly_maintenance*number_of_years + sum(df_scen['u_e_hp']*inp.grid_tariff_CHFpkWh)
    return opex

def capex_electric_heater(scen_techs):
    # No new electric heaters are allowed in switzerland
    return 0

def opex_electric_heater(scen_techs, df_scen):
    yearly_maintenance = scen_techs['electric_heater']['maintenance_cost']*scen_techs["electric_heater"]['kW_th_max']
    opex = yearly_maintenance*number_of_years + sum(df_scen['u_e_eh']*inp.grid_tariff_CHFpkWh)
    return opex

def opex_oil_boiler(scen_techs, df_scen):
    yearly_maintenance = scen_techs['oil_boiler']['maintenance_cost']*scen_techs["oil_boiler"]['kW_th_max']
    opex = yearly_maintenance*number_of_years + sum(df_scen['u_oil_ob_kg']*inp.oil_price/oil_density)
    return opex

def opex_gas_boiler(scen_techs, df_scen):
    yearly_maintenance = scen_techs['gas_boiler']['maintenance_cost']*scen_techs["gas_boiler"]['kW_th_max']
    opex = yearly_maintenance*number_of_years + sum(df_scen['u_oil_gb']*inp.gas_price)
    return opex

def opex_wood_boiler(scen_techs, df_scen):
    yearly_maintenance = scen_techs['wood_boiler']['maintenance_cost']*scen_techs["wood_boiler"]['kW_th_max']
    opex = yearly_maintenance*number_of_years + sum(df_scen['u_wood_wb']*inp.wood_price)
    return opex

def opex_district_heating(scen_techs, df_scen):
    yearly_maintenance = scen_techs['district_heating']['maintenance_cost']*max(df_scen['v_h_dh'])
    opex = yearly_maintenance*number_of_years + sum(df_scen['u_h_dh']*inp.dh_tariff)
    return opex

def opex_solar_thermal(scen_techs, df_scen):
    yearly_maintenance = scen_techs['solar_thermal']['maintenance_cost']*max(df_scen['v_h_st'])
    opex = yearly_maintenance*number_of_years
    return opex

def opex_pv(scen_techs, number_of_years):
    yearly_maintenance = scen_techs['solar_pv']['maintenance_cost']*scen_techs['solar_pv']['kWp_max']
    opex = yearly_maintenance*number_of_years
    return opex

def wind_power(scen_techs, number_of_years):
    yearly_maintenance = scen_techs['wind_power']['maintenance_cost']*scen_techs['wind_power']['kWp_max']
    opex = yearly_maintenance*number_of_years
    return opex

def hydro_power(scen_techs, number_of_years):
    yearly_maintenance = scen_techs['hydro_power']['maintenance_cost']*scen_techs['hydro_power']['kWp_max']
    opex = yearly_maintenance*number_of_years
    return opex

def opex_grid_supply(df_scen):

    return sum(df_scen['u_e_grid']*inp.grid_tariff_CHFpkWh)
    
def opex_tes_centralised():

    return 0

def opex_tes_decentralised(scen_techs):
    yearly_maintenance = scen_techs['tes_decentralised']['maintenance_cost']*scen_techs['tes_decentralised']['capacity_kWh']
    opex = yearly_maintenance*number_of_years
    return opex

def opex_bes(scen_techs):
    yearly_maintenance = scen_techs['bes']['maintenance_cost']*scen_techs['bes']['capacity_kWh']
    opex = yearly_maintenance*number_of_years
    return opex

#def opex_biomass():
#    return 0

def opex_hydrothermal_gasification(scen_techs):
    yearly_maintenance = scen_techs['hydrothermal_gasification']['maintenance_cost']*scen_techs['hydrothermal_gasification']['capacity_kWh']
    opex = yearly_maintenance*number_of_years
    return opex

def opex_anaerobic_digestion_upgrade(scen_techs):
    yearly_maintenance = scen_techs['anaerobic_digestion']['maintenance_cost']*scen_techs['anaerobic_digestion']['capacity_kW']
    opex = yearly_maintenance*number_of_years
    return opex

def opex_anaerobic_digestion_upgrade_hydrogen(scen_techs):
    yearly_maintenance = scen_techs['anaerobic_digestion_hydrogen_upgrade']['maintenance_cost']*scen_techs['anaerobic_digestion_hydrogen_upgrade']['capacity_kWh']
    opex = yearly_maintenance*number_of_years
    return opex

def opex_anaerobic_digestion_chp(scen_techs):
    yearly_maintenance = scen_techs['anaerobic_digestion_chp']['maintenance_cost']*scen_techs['anaerobic_digestion_chp']['capacity_kWh']
    opex = yearly_maintenance*number_of_years
    return opex

def opex_wood_gasification_upgrade(scen_techs):
    yearly_maintenance = scen_techs['wood_gasification_upgrade']['maintenance_cost']*scen_techs['wood_gasification_upgrade']['capacity_kWh']
    opex = yearly_maintenance*number_of_years
    return opex