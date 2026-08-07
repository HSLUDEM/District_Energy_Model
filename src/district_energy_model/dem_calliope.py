# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 15:05:43 2023

@author: UeliSchilt
"""

"""
Coupling the DEM with the optimisation framework Calliope.

Reference: https://calliope.readthedocs.io/en/stable/user/introduction.html

"""

"""
CHANGES THAT MUST BE REVERTED EVENTUALLY:
    - In run_optimisation(...), the Calliope model instance was added to the
      return.
    - make this dynamic: subset_time in __create_model_dict(...)

"""


import pandas as pd
import numpy as np

from district_energy_model import dem_calliope_cc

class CalliopeOptimiser:
    
    # def __init__(self, tech_list, tech_instances, energy_demand, supply, com_name, opt_metrics, files_path):
    def __init__(
            self,
            tech_list,
            tech_instances,
            energy_demand,
            supply,
            building_inertia_flex,
            com_name,
            scen_techs,
            files_path
            ):
        """
        Optimisation based on modelling framework Calliope.
    
        Parameters
        ----------
        tech_list : list of strings
            List of deployed technologies.
        scen_techs : dictionary
            Input dictionary to DEM.
        df_scen : dataframe
            Dataframe containing hourly timeseries.
        com_name : string
            Name of community.
    
        Returns
        -------
        opt_results : xarray.core.dataset.Dataset
            Resulting timeseries from optimisation.
    
        """
        
        self.tech_list = tech_list
        self.energy_demand = energy_demand
        self.supply = supply
        self.building_inertia_flex = building_inertia_flex
        self.com_name = com_name
        self.scen_techs = scen_techs
        self.opt_metrics = scen_techs['optimisation']
        self.files_path = files_path
        
        self.energy_scaling_factor = self.scen_techs['optimisation']['calliope_energy_scaling_factor']
        self.available_area_scaling = 1 # This is NOT a physical area value!!!
        
        self.rerun_eps = False
        self.eps_n = 'inf'
        self.dhn_share_type = False
        self.dhn_share_val = 0.0
        
        self.custom_constraints = False
        
        # Flexibility:
        # -----------
        if (
            self.scen_techs['scenarios']['demand_side']
            and self.scen_techs['demand_side']['ev_integration']
            and self.scen_techs['demand_side']['ev_flexibility']
                ):
            self.ev_flex_flag = True
        else:
            self.ev_flex_flag = False            
            
        if (
            self.scen_techs['scenarios']['demand_side']
            and self.scen_techs['demand_side']['dr_flexibility_building_inertia']
                ):
            self.building_inertia_flex_flag = True
        else:
            self.building_inertia_flex_flag = False
        
        # Techs:
        # -----
        self.tech_list_new = []
        self.tech_list_old = []
        self.tech_list_grid_connection = []
        self.tech_list_pv = []
        self.tech_list_solarthermal = [] #Always same length as pv!
        
        # Unpack tech instances:
        if 'heat_pump' in self.tech_list:
            self.tech_heat_pump = tech_instances['heat_pump']
        
        if 'electric_heater' in self.tech_list:
            self.tech_electric_heater = tech_instances['electric_heater']
            
        if 'oil_boiler' in self.tech_list:
            self.tech_oil_boiler = tech_instances['oil_boiler']
        
        if 'gas_boiler' in self.tech_list:
            self.tech_gas_boiler = tech_instances['gas_boiler']
        
        if 'wood_boiler' in self.tech_list:
            self.tech_wood_boiler = tech_instances['wood_boiler']
        
        if 'district_heating' in self.tech_list:
            self.tech_district_heating = tech_instances['district_heating']
            
        if 'solarthermal_rooftop' in self.tech_list:
            self.tech_solarthermal_rooftop = tech_instances['solarthermal_rooftop']

        if 'solar_pvrooftop' in self.tech_list:
            self.tech_solar_pvrooftop = tech_instances['solar_pvrooftop']

        if 'solar_pvalpine' in self.tech_list:
            self.tech_solar_pvalpine = tech_instances['solar_pvalpine']

        if 'wind_power' in self.tech_list:
            self.tech_wind_power = tech_instances['wind_power']
        
        if 'hydro_power' in self.tech_list:
            self.tech_hydro_power = tech_instances['hydro_power']
            
        if 'biomass' in self.tech_list:
            self.tech_biomass = tech_instances['biomass']
        
        if 'grid_supply' in self.tech_list:
            self.tech_grid_supply = tech_instances['grid_supply']

        if 'grid_export' in self.tech_list:
            self.tech_grid_export = tech_instances['grid_export']

        if 'other' in self.tech_list:
            self.tech_other = tech_instances['other']

        if 'tes' in self.tech_list:
            self.tech_tes = tech_instances['tes']

        if 'tes_sites' in self.tech_list:
            self.tech_tes_sites = tech_instances['tes_sites']

        if 'tes_decentralised' in self.tech_list:
            self.tech_tes_decentralised = tech_instances['tes_decentralised']
            
        if 'bes' in self.tech_list:
            self.tech_bes = tech_instances['bes']

        if True:
            self.tech_pile_of_berries = tech_instances['pile_of_berries']

        if 'gtes' in self.tech_list:
            self.tech_gtes = tech_instances['gtes']

        if 'ws' in self.tech_list:
            self.tech_ws = tech_instances['ws']

        if 'hes' in self.tech_list:
            self.tech_hes = tech_instances['hes']

        if 'hydrothermal_gasification' in self.tech_list:
            self.tech_hydrothermal_gasification = tech_instances['hydrothermal_gasification']
    
        if 'anaerobic_digestion_upgrade' in self.tech_list:
            self.tech_anaerobic_digestion_upgrade = tech_instances['anaerobic_digestion_upgrade']
        
        if 'anaerobic_digestion_upgrade_hydrogen' in self.tech_list:
            self.tech_anaerobic_digestion_upgrade_hydrogen = tech_instances['anaerobic_digestion_upgrade_hydrogen']
        
        if 'anaerobic_digestion_chp' in self.tech_list:
            self.tech_anaerobic_digestion_chp = tech_instances['anaerobic_digestion_chp']
        
        if 'wood_gasification_upgrade' in self.tech_list:
            self.tech_wood_gasification_upgrade = tech_instances['wood_gasification_upgrade']
            
        if 'wood_gasification_upgrade_hydrogen' in self.tech_list:
            self.tech_wood_gasification_upgrade_hydrogen = tech_instances['wood_gasification_upgrade_hydrogen']
            
        if 'wood_gasification_chp' in self.tech_list:
            self.tech_wood_gasification_chp = tech_instances['wood_gasification_chp']
            
        if 'hydrogen_production' in self.tech_list:
            self.tech_hydrogen_production = tech_instances['hydrogen_production']

        if 'chp_gt' in self.tech_list:
            self.tech_chp_gt = tech_instances['chp_gt']
            
        if 'gas_turbine_cp' in self.tech_list:
            self.tech_gas_turbine_cp = tech_instances['gas_turbine_cp']
            
        if 'steam_turbine' in self.tech_list:
            self.tech_steam_turbine = tech_instances['steam_turbine']
            
        if 'wood_boiler_sg' in self.tech_list:
            self.tech_wood_boiler_sg = tech_instances['wood_boiler_sg']
        
        if 'waste_to_energy' in self.tech_list:
            self.tech_waste_to_energy = tech_instances['waste_to_energy']
            
        if 'heat_pump_cp' in self.tech_list:
            self.tech_heat_pump_cp = tech_instances['heat_pump_cp']

        if 'heat_pump_cp_lt' in self.tech_list:
            self.tech_heat_pump_cp_lt = tech_instances['heat_pump_cp_lt']

        if 'oil_boiler_cp' in self.tech_list:
            self.tech_oil_boiler_cp = tech_instances['oil_boiler_cp']

        if 'electric_heater_cp' in self.tech_list:
            self.tech_electric_heater_cp = tech_instances['electric_heater_cp']

        if 'wood_boiler_cp' in self.tech_list:
            self.tech_wood_boiler_cp = tech_instances['wood_boiler_cp']

        if 'gas_boiler_cp' in self.tech_list:
            self.tech_gas_boiler_cp = tech_instances['gas_boiler_cp']

        if 'deep_geothermal' in self.tech_list:
            self.tech_deep_geothermal = tech_instances['deep_geothermal']

        if 'heat_demand_manual' in self.tech_list:
            self.tech_heat_demand_manual = tech_instances['heat_demand_manual']

        if 'waste_heat' in self.tech_list:
            self.tech_waste_heat = tech_instances['waste_heat']
        
        if 'waste_heat_low_temperature' in self.tech_list:
            self.tech_waste_heat_low_temperature = tech_instances['waste_heat_low_temperature']



    def run_optimisation(self, rerun_eps=False, eps_n='inf'):
        """
        Generate the input dictionary used to run an optimisation model in
        Calliope. Then generate a Calliope model and run an optimisation.
        
        Steps:
            1. Create timeseries data
            2. Create input dict
            3. Generate and run model
    
        Parameters
        ----------
        n/a
    
        Returns
        -------
        opt_results : xarray.core.dataset.Dataset
            Resulting timeseries from optimisation.
            
        """

        print('------------------------------------------------------------')
        print('****OPTIMISATION****')
        
        import calliope
        
        ''' -------------------------------------------------------------------
        0. Get some parameters:
        '''
        # Update espilon constraint metrics (only used for pareto front):
        self.rerun_eps = rerun_eps
        self.eps_n = eps_n
        
        tmp_tot_share = 0.0
        
        if 'district_heating' in self.tech_list:
            self.dhn_share_type =\
                self.tech_district_heating.get_demand_share_type()
            self.dhn_share_val =\
                self.tech_district_heating.get_demand_share_val()
            self.dhn_qty = self.tech_district_heating.get_dhn_qty()
            if self.dhn_share_type == 'min' or self.dhn_share_type == 'max':
                tmp_tot_share += self.dhn_share_val                
        else:
            self.dhn_share_type = 'free'
            self.dhn_share_val = 0
            self.dhn_qty = 0

        if ('heat_pump' in self.tech_list) and ('heat_pump_coptimeseries' in self.tech_list):
            raise ValueError("Both heat_pump and heat_pump_coptimeseries cannot be active at the same time!")

        if 'heat_pump' in self.tech_list:
            self.hp_fixed_demand_share =\
                self.tech_heat_pump.get_fixed_demand_share()
            self.hp_fixed_demand_share_val =\
                self.tech_heat_pump.get_fixed_demand_share_val()
            if self.hp_fixed_demand_share == True:
                tmp_tot_share += self.hp_fixed_demand_share_val
        else:
            self.hp_fixed_demand_share = False
            self.hp_fixed_demand_share_val = 0

        if 'electric_heater' in self.tech_list:
            self.eh_fixed_demand_share =\
                self.tech_electric_heater.get_fixed_demand_share()
            self.eh_fixed_demand_share_val =\
                self.tech_electric_heater.get_fixed_demand_share_val()
            if self.eh_fixed_demand_share == True:
                tmp_tot_share += self.eh_fixed_demand_share_val
        else:
            self.eh_fixed_demand_share = False
            self.eh_fixed_demand_share_val = 0
            
        if 'oil_boiler' in self.tech_list:
            self.ob_fixed_demand_share =\
                self.tech_oil_boiler.get_fixed_demand_share()
            self.ob_fixed_demand_share_val =\
                self.tech_oil_boiler.get_fixed_demand_share_val()
            if self.ob_fixed_demand_share == True:
                tmp_tot_share += self.ob_fixed_demand_share_val
        else:
            self.ob_fixed_demand_share = False
            self.ob_fixed_demand_share_val = 0
            
        if 'gas_boiler' in self.tech_list:
            self.gb_fixed_demand_share =\
                self.tech_gas_boiler.get_fixed_demand_share()
            self.gb_fixed_demand_share_val =\
                self.tech_gas_boiler.get_fixed_demand_share_val()
            if self.gb_fixed_demand_share == True:
                tmp_tot_share += self.gb_fixed_demand_share_val
        else:
            self.gb_fixed_demand_share = False
            self.gb_fixed_demand_share_val = 0
            
        if 'wood_boiler' in self.tech_list:
            self.wb_fixed_demand_share =\
                self.tech_wood_boiler.get_fixed_demand_share()
            self.wb_fixed_demand_share_val =\
                self.tech_wood_boiler.get_fixed_demand_share_val()
            if self.wb_fixed_demand_share == True:
                tmp_tot_share += self.wb_fixed_demand_share_val
        else:
            self.wb_fixed_demand_share = False
            self.wb_fixed_demand_share_val = 0
            
        # Check that the cummulative shares don't exceed 100%:
        if tmp_tot_share > 1.0:
            raise ValueError("Fixed demand share values cannot add up to more than 100%.")
        
        ''' -------------------------------------------------------------------
        1. Create timeseries data:
        '''
        # https://calliope.readthedocs.io/en/stable/user/building.html#reading-in-timeseries-from-pandas-dataframes
        # demand_heat = -(self.energy_demand.get_d_h())
        # demand_power = -(self.energy_demand.get_d_e_baseline())
        # demand_power = -(
        #     self.energy_demand.get_d_e_baseline()
        #     + self.energy_demand.get_d_e_ev()
        #     )
        
        # flex_label
        if self.building_inertia_flex_flag:
            demand_heat = self.energy_demand.get_d_h_flex_ll()
        else:
            demand_heat = self.energy_demand.get_d_h()
        
        demand_power_baseline = self.energy_demand.get_d_e_baseline()
        
        demand_power_ev = self.energy_demand.get_d_e_ev()
        demand_power_ev_cp = self.energy_demand.get_d_e_ev_cp()
        demand_power_ev_pd = self.energy_demand.get_d_e_ev_pd()
        demand_power_ev_pu = self.energy_demand.get_d_e_ev_pu()
        demand_power_ev_delta = demand_power_ev_pu - demand_power_ev_pd
        
        n_hours = len(self.energy_demand.get_d_e())
        null_array = np.array([0.0]*n_hours)
        
        # if 'solar_pv' in self.tech_list:
        #     pv_resource_old = self.tech_solar_pv.get_v_e()
        #     pv_resource_new = self.tech_solar_pv.get_v_e_pot_remain()
        #     eta_pv=self.tech_solar_pv.get_eta_overall()
        # else:
        #     pv_resource_old = null_array.copy()
        #     pv_resource_new = null_array.copy()
        #     eta_pv = 1

        if 'solar_pvrooftop' in self.tech_list:
            pv_rooftop_resources = [np.array(x) for x in self.tech_solar_pvrooftop.get_resources()]
        else:
            pv_rooftop_resources = [null_array.copy()]

        if 'solarthermal_rooftop' in self.tech_list:
            solarthermal_rooftop_resources = [np.array(x) for x in self.tech_solarthermal_rooftop.get_resources()]
        else:
            solarthermal_rooftop_resources = [null_array.copy()]

        if 'solar_pvalpine' in self.tech_list:
            pv_alpine_resources = [np.array(x)[:n_hours] for x in self.tech_solar_pvalpine.get_resources()]
        else:
            pv_alpine_resources = [null_array.copy()]

        # if 'solar_thermal' in self.tech_list:
        #     solar_th_resource_old = null_array.copy() # TEMPORARY FIX: assumption: currently no solar thermal installed
            
        #     solar_th_resource_new = self.tech_solar_thermal.convert_pv_to_thermal(
        #         # df_pv_kWh=self.tech_solar_pv.get_v_e_pot_remain(),
        #         df_pv_kWh=pv_resource_new,
        #         # eta_pv=self.tech_solar_pv.get_eta_overall(),
        #         eta_pv = eta_pv,
        #         eta_thermal=self.tech_solar_thermal.get_eta_overall()
        #         )
        # else:
        #     solar_th_resource_old = null_array.copy()
        #     solar_th_resource_new = null_array.copy()
        
        # pv_resource_old = pv_resource_old/self.available_area_scaling
        # pv_resource_new = pv_resource_new/self.available_area_scaling

        # solar_th_resource_old = solar_th_resource_old/self.available_area_scaling
        # solar_th_resource_new = solar_th_resource_new/self.available_area_scaling
        

        
        pv_rooftop_resources = [x / self.available_area_scaling for x in pv_rooftop_resources]
        pv_alpine_resources = [x / self.available_area_scaling for x in pv_alpine_resources]

        solarthermal_rooftop_resources = [x / self.available_area_scaling for x in solarthermal_rooftop_resources]
        # ---------------------------------------------------------------------
        # TEMPORARY
        # UN-COMMENT for saving resource to yaml:
        # import yaml
        
        # # Convert to list and save to YAML file
        # with open("tmp_results_for_testing/data.yaml", "w") as file:
        #     yaml.dump({"array": pv_resource_old.tolist()}, file, default_flow_style=False)
        # ---------------------------------------------------------------------

        supply_wet_biomass = self.supply.get_s_wet_bm()
        supply_wood = self.supply.get_s_wd()
                
        if 'wind_power' in self.tech_list:
            wp_resource_annual = self.tech_wind_power.get_v_e_pot_annual_kWhpkW() # [kWh/kW] Generation profile type 'annual' (geared towards all year production)
            wp_resource_winter = self.tech_wind_power.get_v_e_pot_winter_kWhpkW() # [kWh/kW] Generatino profile type 'winter' (geared towards winter production)
        else:            
            wp_resource_annual = null_array.copy()
            wp_resource_winter = null_array.copy()
            
        if 'hydro_power' in self.tech_list:
            hydro_resource = self.tech_hydro_power.get_v_e()
        else:
            hydro_resource = null_array.copy()
        
        if 'waste_heat' in self.tech_list:
            waste_heat_resource = self.tech_waste_heat.get_v_h_resource()
        else:
            waste_heat_resource = null_array.copy()

        if 'heat_demand_manual' in self.tech_list:
            heat_demand_manual_resource = self.tech_heat_demand_manual.get_timeseries()
        else:
            heat_demand_manual_resource = null_array.copy()


        if 'grid_supply' in self.tech_list:
            grid_supply_resource_tariff_timeseries = self.tech_grid_supply.get_tariff_timeseries()
            grid_supply_resource_co2_intensity_timeseries = self.tech_grid_supply.get_co2_intensity_timeseries()
        else:
            grid_supply_resource_tariff_timeseries = null_array.copy()
            grid_supply_resource_co2_intensity_timeseries = null_array.copy()

        if 'grid_export' in self.tech_list:
            grid_export_resource_tariff_timeseries = self.tech_grid_export.get_tariff_timeseries()
            grid_export_resource_co2_intensity_timeseries = self.tech_grid_export.get_co2_intensity_timeseries()
        else:
            grid_export_resource_tariff_timeseries = null_array.copy()
            grid_export_resource_co2_intensity_timeseries = null_array.copy()


        if 'waste_heat_low_temperature' in self.tech_list:
            waste_heat_low_temperature_resource = self.tech_waste_heat_low_temperature.get_v_hlt_resource()
        else:
            waste_heat_low_temperature_resource = null_array.copy()

        if 'heat_pump_cp' in self.tech_list:
            heat_pump_cp_cops = self.tech_heat_pump_cp.get_cop()
        else:
            heat_pump_cp_cops = null_array.copy()

        if 'heat_pump' in self.tech_list:

            heat_pump_cops_existing = self.tech_heat_pump.get_cops_existing()
            heat_pump_cops_new = self.tech_heat_pump.get_cops_new()
            heat_pump_cops_one_to_one_replacement = self.tech_heat_pump.get_cops_one_to_one_replacement()
        else:
            heat_pump_cops_existing = null_array.copy()
            heat_pump_cops_new = null_array.copy()
            heat_pump_cops_one_to_one_replacement = null_array.copy()

        # Create a datetime index (required in Calliope)
        date_index = pd.date_range(
            start='2050-01-01',
            periods=len(demand_heat),
            freq='H'
            )
        # Set the datetime index to the Series:
        demand_heat = pd.Series(demand_heat, index=date_index)
        # demand_power = pd.Series(demand_power, index=date_index)
        demand_power_baseline = pd.Series(demand_power_baseline, index=date_index)
        demand_power_ev = pd.Series(demand_power_ev, index=date_index)
        demand_power_ev_cp = pd.Series(demand_power_ev_cp, index=date_index)
        demand_power_ev_pd = pd.Series(demand_power_ev_pd, index=date_index)
        demand_power_ev_pu = pd.Series(demand_power_ev_pu, index=date_index)
        demand_power_ev_delta = pd.Series(demand_power_ev_delta, index=date_index)

        # pv_resource_old = pd.Series(pv_resource_old, index=date_index)
        # pv_resource_new = pd.Series(pv_resource_new, index=date_index)

        
        
        pv_rooftop_resources = [pd.Series(x, index=date_index) for x in pv_rooftop_resources]
        pv_alpine_resources = [pd.Series(x, index=date_index) for x in pv_alpine_resources]

        solarthermal_rooftop_resources = [pd.Series(x, index=date_index) for x in solarthermal_rooftop_resources]

        # solar_th_resource_old = pd.Series(solar_th_resource_old, index=date_index)
        # solar_th_resource_new = pd.Series(solar_th_resource_new, index=date_index)

        supply_wet_biomass = pd.Series(supply_wet_biomass, index=date_index)
        supply_wood = pd.Series(supply_wood, index=date_index)
        wp_resource_annual = pd.Series(wp_resource_annual, index=date_index)
        wp_resource_winter = pd.Series(wp_resource_winter, index=date_index)
        hydro_resource = pd.Series(hydro_resource, index=date_index)
        heat_demand_manual_resource = pd.Series(heat_demand_manual_resource, index=date_index)
        waste_heat_resource = pd.Series(waste_heat_resource, index=date_index)
        waste_heat_low_temperature_resource = pd.Series(waste_heat_low_temperature_resource, index=date_index)

        grid_supply_resource_tariff_timeseries = pd.Series(grid_supply_resource_tariff_timeseries, index=date_index)
        grid_supply_resource_co2_intensity_timeseries = pd.Series(grid_supply_resource_co2_intensity_timeseries, index=date_index)
        
        grid_export_resource_tariff_timeseries = pd.Series(grid_export_resource_tariff_timeseries, index=date_index)
        grid_export_resource_co2_intensity_timeseries = pd.Series(grid_export_resource_co2_intensity_timeseries, index=date_index)


        heat_pump_cp_cops = pd.Series(heat_pump_cp_cops, index=date_index)

        heat_pump_cops_existing = pd.Series(heat_pump_cops_existing, index=date_index)
        heat_pump_cops_one_to_one_replacement = pd.Series(heat_pump_cops_one_to_one_replacement, index=date_index)
        heat_pump_cops_new = pd.Series(heat_pump_cops_new, index=date_index)

        # Convert pandas series to dataframe:
        df_demand_heat = demand_heat.to_frame('d_h')
        # df_demand_power = demand_power.to_frame('d_e_baseline')
        df_demand_power_baseline = demand_power_baseline.to_frame('d_e_baseline')
        df_demand_power_ev = demand_power_ev.to_frame('d_e_ev')
        df_demand_power_ev_cp = demand_power_ev_cp.to_frame('d_e_ev_cp')
        df_demand_power_ev_pd = demand_power_ev_pd.to_frame('d_e_ev_pd')
        df_demand_power_ev_pu = demand_power_ev_pu.to_frame('d_e_ev_pu')
        df_demand_power_ev_delta = demand_power_ev_delta.to_frame('d_e_ev_delta')

        # df_pv_resource_old = pv_resource_old.to_frame('v_e_pv')
        # df_pv_resource_new = pv_resource_new.to_frame('v_e_pv')

        # df_pv_rooftop_resource = [pv_rooftop_resources[i].to_frame('v_e_pvrooftop_'+str(i)) for i in range(len(pv_rooftop_resources))]
        df_pv_rooftop_resource = pd.concat(pv_rooftop_resources, axis = 1)
        df_pv_rooftop_resource.columns = ['v_e_pvrooftop_'+str(i) for i in range(len(pv_rooftop_resources))]

        df_pv_alpine_resource = pd.concat(pv_alpine_resources, axis = 1)
        df_pv_alpine_resource.columns = ['v_e_pvalpine_'+str(i) for i in range(len(pv_alpine_resources))]

        df_solarthermal_rooftop_resource = pd.concat(solarthermal_rooftop_resources, axis = 1)
        df_solarthermal_rooftop_resource.columns = ['v_h_solarthermalrooftop_'+str(i) for i in range(len(solarthermal_rooftop_resources))]


        # df_solar_th_resource_old = solar_th_resource_old.to_frame('v_h_solar_th')
        # df_solar_th_resource_new = solar_th_resource_new.to_frame('v_h_solar_th')

        df_supply_wet_biomass = supply_wet_biomass.to_frame('s_wet_bm')
        df_supply_wood = supply_wood.to_frame('s_wd')
        df_wp_resource_annual = wp_resource_annual.to_frame('v_e_wp')
        df_wp_resource_winter = wp_resource_winter.to_frame('v_e_wp')
        df_hydro_resource = hydro_resource.to_frame('v_e_hydro')
        df_heat_demand_manual_resource = - heat_demand_manual_resource.to_frame('d_h_m')
        df_waste_heat_resource = waste_heat_resource.to_frame('v_h_wh')
        df_waste_heat_low_temperature_resource = waste_heat_low_temperature_resource.to_frame('v_hlt_whlt')

        df_grid_supply_timeseries = pd.DataFrame({
                                    "tariff_timeseries": grid_supply_resource_tariff_timeseries * self.energy_scaling_factor,
                                    "co2_intensity_timeseries": grid_supply_resource_co2_intensity_timeseries * self.energy_scaling_factor
                                })
        df_grid_export_timeseries = pd.DataFrame({
                                    "tariff_timeseries": - grid_export_resource_tariff_timeseries * self.energy_scaling_factor,
                                    "co2_intensity_timeseries": - grid_export_resource_co2_intensity_timeseries * self.energy_scaling_factor
                                })


        df_heat_pump_cp_cops = heat_pump_cp_cops.to_frame('cop')

        df_heat_pump_cops_existing = heat_pump_cops_existing.to_frame('heat_pump_cops_existing')
        df_heat_pump_cops_new = heat_pump_cops_new.to_frame('heat_pump_cops_new')
        df_heat_pump_cops_one_to_one_replacement = heat_pump_cops_one_to_one_replacement.to_frame('heat_pump_cops_one_to_one_replacement')

        # print(df_heat_pump_cops_one_to_one_replacement)
        # exit()

        # Timeseries data for Calliope model: (Get these from df_scen!!!)
        timeseries_dataframes = {
            'demand_heat': df_demand_heat / self.energy_scaling_factor,
            # 'demand_power':df_demand_power,
            'demand_power_baseline':df_demand_power_baseline / self.energy_scaling_factor,
            'demand_power_ev':df_demand_power_ev / self.energy_scaling_factor,
            'demand_power_ev_cp':df_demand_power_ev_cp / self.energy_scaling_factor,
            'demand_power_ev_pd':df_demand_power_ev_pd / self.energy_scaling_factor,
            'demand_power_ev_pu':df_demand_power_ev_pu / self.energy_scaling_factor,
            'demand_power_ev_delta':df_demand_power_ev_delta / self.energy_scaling_factor,            

            # 'pv_resource_old':df_pv_resource_old,
            # 'pv_resource_new':df_pv_resource_new,

            'pvrooftop_resource': df_pv_rooftop_resource / self.energy_scaling_factor,
            'pvalpine_resource': df_pv_alpine_resource / self.energy_scaling_factor,

            'solarthermalrooftop_resource': df_solarthermal_rooftop_resource / self.energy_scaling_factor,

            # 'solar_th_resource_old':df_solar_th_resource_old,
            # 'solar_th_resource_new':df_solar_th_resource_new,            
            'wet_biomass_resource': df_supply_wet_biomass / self.energy_scaling_factor,
            'wood_resource': df_supply_wood / self.energy_scaling_factor,
            'wp_resource_annual': df_wp_resource_annual, #/ self.energy_scaling_factor,
            'wp_resource_winter': df_wp_resource_winter, #/ self.energy_scaling_factor,
            'hydro_resource': df_hydro_resource / self.energy_scaling_factor,
            'heat_demand_manual': df_heat_demand_manual_resource / self.energy_scaling_factor,
            'waste_heat': df_waste_heat_resource / self.energy_scaling_factor,
            'grid_supply': df_grid_supply_timeseries,
            'grid_export': df_grid_export_timeseries,
            'waste_heat_low_temperature': df_waste_heat_low_temperature_resource / self.energy_scaling_factor,
            'heat_pump_cp': df_heat_pump_cp_cops,
            'heat_pump_cops_existing': df_heat_pump_cops_existing,
            'heat_pump_cops_new': df_heat_pump_cops_new,
            'heat_pump_cops_one_to_one_replacement': df_heat_pump_cops_one_to_one_replacement,

            }
        
        
        # dftpv = timeseries_dataframes['pvrooftop_resource']
        # for key in timeseries_dataframes.keys():
        #     if timeseries_dataframes[key].isna().sum().sum() > 0:
        #         timeseries_dataframes[key] = timeseries_dataframes[key].fillna(0)
        
        ''' -------------------------------------------------------------------
        2. Create input dict:
        '''
        input_dict, math_dict = self.__build_input_dict()
            # rerun_eps=rerun_eps,
            # eps_n=eps_n
            # )

        print("\nInput dict generated.\n")
        
        ''' -------------------------------------------------------------------
        3. Generate and run model:
        '''
        
        #----------------------------------------------------------------------
        # Load model:
        print("\nModel loading ...\n")
        model = calliope.read_dict(
            input_dict,
            data_table_dfs=timeseries_dataframes,
            math_dict=math_dict,
        )
        
        print('\nModel running ...\n')
    
        #----------------------------------------------------------------------
        # Run model:
        calliope.set_log_verbosity('INFO')

        if self.scen_techs['tes_sites']['deployment']:
            self.custom_constraint_tes_sites = self.tech_tes_sites.get_custom_constraints_required()
        else:
            self.custom_constraint_tes_sites = False

        if self.custom_constraint_tes_sites:
            self.custom_constraints = True

        if (self.ev_flex_flag or self.building_inertia_flex_flag):
            self.custom_constraints = True

        if self.custom_constraints:
            model.run(build_only = True)
        else:
            model.run()        
        # self.custom_constraints = False
        if self.custom_constraints:
            
            ts_len = len(demand_heat)
        
            if self.custom_constraint_tes_sites:

                # ts_len = len(demand_heat)

                #Custom constraints and costs for TES Sites

                model = dem_calliope_cc.tes_sites_lt_no_conversion_without_charging_constraint(model, ts_len, self.tech_tes_sites.get_sites_list())
                
                model = dem_calliope_cc.tes_sites_size_ratios_constraints(model, ts_len, self.tech_tes_sites.get_sites_list())

                model = dem_calliope_cc.tes_sites_minimum_size_constraints(model, ts_len, self.tech_tes_sites.get_sites_list(), self.energy_scaling_factor)

                model = dem_calliope_cc.tes_sites_exclusion_constraint(model, ts_len, self.tech_tes_sites.get_sites_list())

                monetary_weight = self.scen_techs['optimisation']['objective_monetary']
                if monetary_weight > 0:
                    model = dem_calliope_cc.tes_sites_minimum_size_cost(model, monetary_weight, ts_len, self.tech_tes_sites.get_sites_list(), self.energy_scaling_factor)
                
                model = dem_calliope_cc.tes_sites_charge_constraints(model, ts_len, self.tech_tes_sites.get_sites_list())

                

                
            if self.ev_flex_flag:
                # ts_len = len(demand_heat)
                n_days = int(ts_len/24.0) # assuming hourly timesteps and full days
                
                # Add custom constraints for EV flexibility:

                # print(model.backend)
                # exit()

                model = dem_calliope_cc.ev_flexibility_constraints(
                    model=model,
                    ts_len=ts_len,
                    n_days=n_days,
                    energy_demand=self.energy_demand,
                    energy_scaling_factor=self.energy_scaling_factor
                    )
            
            # flex_label
            if self.building_inertia_flex_flag:
                pass
                fixed_share_techs = self.__get_constant_heat_source_techs()
                
                model = dem_calliope_cc.building_inertia_flex_constraints(
                    model=model,
                    ts_len=ts_len,
                    energy_demand=self.energy_demand,
                    building_inertia_flex=self.building_inertia_flex,
                    energy_scaling_factor=self.energy_scaling_factor,
                    fixed_share_techs=fixed_share_techs
                    )
 
        
        #----------------------------------------------------------------------
        # Save LP file: (prints file with human-readable mathematical formulation of the model)
        if self.opt_metrics['save_math_model']:
            print("\nPrinting .lp file (math model) ...\n")
            model.to_lp(f'{self.files_path}/mathematical_optimisation_model.lp')

        # ---------------------------------------------------------------------
        # Get results:        
        if self.custom_constraints:
            # Re-run model to implement custom constraints:
            new_model = model.backend.rerun()
            # see: https://calliope.readthedocs.io/en/stable/user/advanced_constraints.html#user-defined-custom-constraints   
            
            opt_results = new_model.results # for custom constraints
        
        else:
            opt_results = model.results

        # ==========================================================
        # FOR TESTING ONLY!
        if self.opt_metrics['save_calliope_files']:
            import os
            print("\nPrinting Calliope files ...\n")
            folder_path = f'{self.files_path}/' # directory where calliope files folder will be created
            i = 0
            while i>=0:
                path = f"{folder_path}calliope_files_{i}"
                if os.path.isdir(path):
                    # folder already exists
                    i += 1
                    pass
                else:
                    if self.custom_constraints:
                        new_model.to_csv(path)
                    else:
                        model.to_csv(path)
                    i=-1
        # ==========================================================
        
        # arr = model.get_formatted_array('flow_out')
        
        if self.custom_constraints:
            return opt_results, new_model
        else:
            return opt_results, model        

    def get_optimal_output_df(self,opt_results):
        from district_energy_model import dem_calliope_output

        return dem_calliope_output.get_optimal_output_df(
            optimiser=self,
            opt_results=opt_results
            )

    # def __build_input_dict(self, rerun_eps=False, eps_n='inf'):
    def __build_input_dict(self):
        
        model_dict = self.__create_model_dict()
        tech_groups_dict = self.__create_tech_groups_dict()
        techs_dict = self.__create_techs_dict()
        nodes_dict = self.__create_nodes_dict()
        data_tables_dict = self.__create_data_tables_dict()
        run_dict = self.__create_run_dict()
        math_dict = self.__create_math_dict()
            # rerun_eps=rerun_eps,
            # eps_n=eps_n
            # )
        
        # =====================================================================
        # TEMPORARY FOR TESTING: PRINT DICTS TO YAML FILES
        # ---------        
        # import dem_helper
        # dem_helper.save_calliope_dicts_to_yaml(
        #     "tmp_results_for_testing",
        #     model_dict,
        #     tech_groups_dict,
        #     techs_dict,
        #     nodes_dict,
        #     run_dict
        #     )       
        # =====================================================================
        
        input_dict = {
            'config':{
                'init':{
                    **model_dict,
                    'mode':run_dict['mode'],
                    },
                'build':{
                    'ensure_feasibility':run_dict['ensure_feasibility'],
                    },
                'solve':{
                    'solver':run_dict['solver'],
                    'solver_options':run_dict['solver_options'],
                    },
                },
            'data_definitions':{
                'bigM':run_dict['bigM'],
                'objective_cost_weights':{
                    'data':list(run_dict['objective_options']['cost_class'].values()),
                    'index':list(run_dict['objective_options']['cost_class'].keys()),
                    'dims':'costs',
                    },
                },
            'templates':tech_groups_dict,
            'techs':techs_dict,
            'nodes':nodes_dict,
            'data_tables':data_tables_dict,
            }
        
        return input_dict, math_dict

    def __create_model_dict(self):

        model_dict = {
            'name':self.com_name,
            'calliope_version':'0.7.0', #'0.6.8', # !!! How to handle the model version dynamically?
            # 'subset_time':['2050-02-01', '2050-02-15']
            }

        return model_dict

    def __create_data_tables_dict(self):

        data_tables_dict = {}

        def add_timeseries_table(
                name,
                data,
                column,
                parameter,
                techs,
                nodes=None,
                costs=None
                ):

            add_dims = {
                'techs':techs,
                'parameters':parameter,
                }

            if nodes is not None:
                add_dims['nodes'] = nodes

            if costs is not None:
                add_dims['costs'] = costs

            data_tables_dict[name] = {
                'data':data,
                'rows':'timesteps',
                'columns':'data_variables',
                'select':{
                    'data_variables':column,
                    },
                'drop':'data_variables',
                'add_dims':add_dims,
                }

        add_timeseries_table(
            'demand_electricity_baseline',
            'demand_power_baseline',
            'd_e_baseline',
            'sink_use_equals',
            'demand_electricity_baseline',
            nodes='X1'
            )
        add_timeseries_table(
            'demand_heat',
            'demand_heat',
            'd_h',
            'sink_use_equals',
            'demand_heat',
            nodes='X1'
            )

        if (
                self.scen_techs['scenarios']['demand_side']
                and self.scen_techs['demand_side']['ev_integration']
                and self.scen_techs['demand_side']['ev_flexibility']
                ):
            add_timeseries_table(
                'demand_electricity_ev_pd',
                'demand_power_ev_pd',
                'd_e_ev_pd',
                'sink_use_equals',
                'demand_electricity_ev_pd',
                nodes='X1'
                )
            add_timeseries_table(
                'demand_electricity_ev_delta',
                'demand_power_ev_delta',
                'd_e_ev_delta',
                'sink_use_max',
                'demand_electricity_ev_delta',
                nodes='X1'
                )
        else:
            add_timeseries_table(
                'demand_electricity_ev',
                'demand_power_ev',
                'd_e_ev',
                'sink_use_equals',
                'demand_electricity_ev',
                nodes='X1'
                )

        add_timeseries_table(
            'wet_biomass_supply_resource',
            'wet_biomass_resource',
            's_wet_bm',
            'source_use_max',
            'wet_biomass_supply',
            nodes='Limited_Supplies'
            )
        add_timeseries_table(
            'wood_supply_resource',
            'wood_resource',
            's_wd',
            'source_use_max',
            'wood_supply',
            nodes='Limited_Supplies'
            )

        if 'solar_pvrooftop' in self.tech_list:
            for i in range(self.tech_solar_pvrooftop.get_num_installations()):
                add_timeseries_table(
                    'solar_pvrooftop_installation_'+str(i),
                    'pvrooftop_resource',
                    'v_e_pvrooftop_'+str(i),
                    'source_use_equals',
                    [
                        'solar_pvrooftop_installation_'+str(i)+'_occupied',
                        'solar_pvrooftop_installation_'+str(i)+'_unoccupied',
                        ]
                    )

        if 'solarthermal_rooftop' in self.tech_list:
            for i in range(self.tech_solarthermal_rooftop.get_num_installations()):
                add_timeseries_table(
                    'solarthermalrooftop_installation_'+str(i),
                    'solarthermalrooftop_resource',
                    'v_h_solarthermalrooftop_'+str(i),
                    'source_use_equals',
                    [
                        'solar_solarthermalrooftop_installation_'+str(i)+'_occupied',
                        'solar_solarthermalrooftop_installation_'+str(i)+'_unoccupied',
                        ]
                    )

        if 'solar_pvalpine' in self.tech_list:
            for i in range(self.tech_solar_pvalpine.get_num_installations()):
                add_timeseries_table(
                    'solar_pvalpine_installation_'+str(i),
                    'pvalpine_resource',
                    'v_e_pvalpine_'+str(i),
                    'source_use_equals',
                    [
                        'solar_pvalpine_installation_'+str(i)+'_occupied',
                        'solar_pvalpine_installation_'+str(i)+'_unoccupied',
                        ]
                    )

        if 'wind_power' in self.tech_list:
            add_timeseries_table(
                'wind_power_annual_old',
                'wp_resource_annual',
                'v_e_wp',
                'source_use_equals',
                'wind_power_old',
                nodes='loc_wp_annual'
                )
            add_timeseries_table(
                'wind_power_annual_new',
                'wp_resource_annual',
                'v_e_wp',
                'source_use_max',
                'wind_power_new',
                nodes='loc_wp_annual'
                )
            add_timeseries_table(
                'wind_power_winter_old',
                'wp_resource_winter',
                'v_e_wp',
                'source_use_equals',
                'wind_power_old',
                nodes='loc_wp_winter'
                )
            add_timeseries_table(
                'wind_power_winter_new',
                'wp_resource_winter',
                'v_e_wp',
                'source_use_max',
                'wind_power_new',
                nodes='loc_wp_winter'
                )

        if 'hydro_power' in self.tech_list:
            add_timeseries_table(
                'hydro_power_resource',
                'hydro_resource',
                'v_e_hydro',
                'source_use_equals',
                'hydro_power'
                )

        if 'grid_supply' in self.tech_list:
            add_timeseries_table(
                'grid_supply_tariff',
                'grid_supply',
                'tariff_timeseries',
                'cost_flow_in',
                'grid_supply',
                costs='monetary'
                )
            add_timeseries_table(
                'grid_supply_co2_intensity',
                'grid_supply',
                'co2_intensity_timeseries',
                'cost_flow_out',
                'grid_supply',
                costs='emissions_co2'
                )

        if 'grid_export' in self.tech_list:
            add_timeseries_table(
                'grid_export_tariff',
                'grid_export',
                'tariff_timeseries',
                'cost_flow_in',
                'grid_export',
                costs='monetary'
                )
            add_timeseries_table(
                'grid_export_co2_intensity',
                'grid_export',
                'co2_intensity_timeseries',
                'cost_flow_in',
                'grid_export',
                costs='emissions_co2'
                )

        if 'heat_pump' in self.tech_list:
            add_timeseries_table(
                'heat_pump_cops_existing',
                'heat_pump_cops_existing',
                'heat_pump_cops_existing',
                'flow_out_eff',
                'heat_pump_old'
                )
            add_timeseries_table(
                'heat_pump_cops_one_to_one_replacement',
                'heat_pump_cops_one_to_one_replacement',
                'heat_pump_cops_one_to_one_replacement',
                'flow_out_eff',
                'heat_pump_one_to_one_replacement'
                )
            add_timeseries_table(
                'heat_pump_cops_new',
                'heat_pump_cops_new',
                'heat_pump_cops_new',
                'flow_out_eff',
                'heat_pump_new'
                )

        if 'heat_pump_cp' in self.tech_list:
            add_timeseries_table(
                'heat_pump_cp_cops',
                'heat_pump_cp',
                'cop',
                'flow_out_eff',
                'heat_pump_cp'
                )

        if 'heat_demand_manual' in self.tech_list:
            add_timeseries_table(
                'heat_demand_manual',
                'heat_demand_manual',
                'd_h_m',
                'sink_use_max',
                'heat_demand_manual_exists',
                nodes='X1'
                )

        if 'waste_heat' in self.tech_list:
            add_timeseries_table(
                'waste_heat',
                'waste_heat',
                'v_h_wh',
                'source_use_max',
                'waste_heat_exists',
                nodes='X1'
                )

        if 'waste_heat_low_temperature' in self.tech_list:
            add_timeseries_table(
                'waste_heat_low_temperature',
                'waste_heat_low_temperature',
                'v_hlt_whlt',
                'source_use_max',
                'waste_heat_low_temperature_exists',
                nodes='X1'
                )

        return data_tables_dict
    
    def __create_tech_groups_dict(self):
        
        tech_groups_dict = {}

        if 'electric_heater' in self.tech_list:
            tech_groups_dict =\
                self.tech_electric_heater.create_tech_groups_dict(
                    tech_groups_dict
                    )
                    
        # if 'solar_thermal' in self.tech_list:
        #     tech_groups_dict = self.tech_solar_thermal.create_tech_groups_dict(
        #         tech_groups_dict
        #         )
            
        if 'solarthermal_rooftop' in self.tech_list:
            tech_groups_dict = self.tech_solarthermal_rooftop.create_tech_groups_dict(
                tech_groups_dict
                )

            
        # if 'solar_pv' in self.tech_list:
        #     tech_groups_dict = self.tech_solar_pv.create_tech_groups_dict(
        #         tech_groups_dict
        #         )
            
        if 'solar_pvrooftop' in self.tech_list:
            tech_groups_dict = self.tech_solar_pvrooftop.create_tech_groups_dict(
                tech_groups_dict
                )

        if 'solar_pvalpine' in self.tech_list:
            tech_groups_dict = self.tech_solar_pvalpine.create_tech_groups_dict(
                tech_groups_dict
                )


        if 'wind_power' in self.tech_list:
            tech_groups_dict = self.tech_wind_power.create_tech_groups_dict(
                tech_groups_dict
                )
            
        if 'heat_pump' in self.tech_list:
            tech_groups_dict = self.tech_heat_pump.create_tech_groups_dict(
                tech_groups_dict
                )
                        
        if 'oil_boiler' in self.tech_list:
            tech_groups_dict = self.tech_oil_boiler.create_tech_groups_dict(
                tech_groups_dict
                )
            
        if 'gas_boiler' in self.tech_list:
            tech_groups_dict = self.tech_gas_boiler.create_tech_groups_dict(
                tech_groups_dict
                )
            
        if 'wood_boiler' in self.tech_list:
            tech_groups_dict = self.tech_wood_boiler.create_tech_groups_dict(
                tech_groups_dict
                )
            
        if 'chp_gt' in self.tech_list:
            tech_groups_dict = self.tech_chp_gt.create_tech_groups_dict(
                tech_groups_dict
                )
            
        if 'gas_turbine_cp' in self.tech_list:
            tech_groups_dict =\
                self.tech_gas_turbine_cp.create_tech_groups_dict(
                    tech_groups_dict
                    )
            
        if 'steam_turbine' in self.tech_list:
            tech_groups_dict = self.tech_steam_turbine.create_tech_groups_dict(
                tech_groups_dict
                )
            
        if 'wood_boiler_sg' in self.tech_list:
            tech_groups_dict =\
                self.tech_wood_boiler_sg.create_tech_groups_dict(
                    tech_groups_dict
                    )
        
        if 'waste_to_energy' in self.tech_list:
            tech_groups_dict =\
                self.tech_waste_to_energy.create_tech_groups_dict(
                    tech_groups_dict
                    )
                
        if 'heat_pump_cp' in self.tech_list:
            tech_groups_dict =\
                self.tech_heat_pump_cp.create_tech_groups_dict(
                    tech_groups_dict
                    )

        if 'heat_pump_cp_lt' in self.tech_list:
            tech_groups_dict =\
                self.tech_heat_pump_cp_lt.create_tech_groups_dict(
                    tech_groups_dict
                    )

        if 'oil_boiler_cp' in self.tech_list:
            tech_groups_dict =\
                self.tech_oil_boiler_cp.create_tech_groups_dict(
                    tech_groups_dict
                    )
            
        if 'electric_heater_cp' in self.tech_list:
            tech_groups_dict =\
                self.tech_electric_heater_cp.create_tech_groups_dict(
                    tech_groups_dict
                    )


        if 'wood_boiler_cp' in self.tech_list:
            tech_groups_dict =\
                self.tech_wood_boiler_cp.create_tech_groups_dict(
                    tech_groups_dict
                    )

        if 'waste_heat' in self.tech_list:
            tech_groups_dict =\
                self.tech_waste_heat.create_tech_groups_dict(
                    tech_groups_dict
                    )
            
        if 'deep_geothermal' in self.tech_list:
            tech_groups_dict =\
                self.tech_deep_geothermal.create_tech_groups_dict(
                    tech_groups_dict
                    )
            
        if 'waste_heat_low_temperature' in self.tech_list:
            tech_groups_dict =\
                self.tech_waste_heat_low_temperature.create_tech_groups_dict(
                    tech_groups_dict
                    )

        if 'gas_boiler_cp' in self.tech_list:
            tech_groups_dict =\
                self.tech_gas_boiler_cp.create_tech_groups_dict(
                    tech_groups_dict
                    )


        return tech_groups_dict

    def __create_techs_dict(self):
        
        # Define colors:
        colors = {
            'demand_electricity':'#072486',
            'demand_heat':'#660507',
            'heat_pump':'#860720',
            'electric_heater':"#F27D52",
            'oil_boiler':'#8E2999',
            'oil_boiler_cp':'#8E2999',
            'electric_heater_cp':'#F27D52',
            'wood_boiler_cp':'#af3420',
            'oil_supply':'#8E2999',
            'gas_boiler':'#001A1A',
            'gas_boiler_cp':'#001A1A',
            'gas_supply':'#001A1A',
            'wood_boiler':'#8C3B0C',
            'wood_supply':'#8C3B0C',
            'district_heating':'#ff99bb',
            'solar_thermal':'#ff99bb', # TBC
            'solar_pv':'#F9D956',
            'hydro_power': '#0000FF',
            'wind_power': '#3333FF',
            'grid_supply':'#C5ABE3',
            'grid_export':"#98EBDD",
            'tes':'#EF008C',
            'tes_sites':'#EF008C',
            'tes_decentralised':'#EF008C',
            'bes': '#229954',
            'gtes': '#000000',
            'ws': "#DFA12E",
            'hes': '#87CEEB',
            'chp_gt':'#16FFCA',
            'gas_turbine_cp':'#FFCC00',
            'steam_turbine':'#FF2300',
            'wood_boiler_sg':'D5C175',
            'waste_to_energy':'#A2D575',
            'heat_pump_cp':'#860720',   
            'heat_pump_cp_lt':"#5E0786",     
            'power_line':'#6783E3',
            'heat_line': '#FF0000',
            'gas_line': '#808080',
            'wood_line': '#6e4500',
            'wet_biomass_line': '#024200',
            'heat_demand_manual': "#B62929",
            'waste_heat': '#918686',
            'waste_heat_low_temperature': "#9BBAC9",
            'deep_geothermal': '#c56019',
	    'flexibility_vs': '#FF0000',
            }
        
        techs_dict = {}
        
        # Add demands: # !!! ADD THESE TO DEMAND CLASS?
        # ===========
        techs_dict['demand_electricity_baseline'] = {
            'name':'Electrical Demand Household',
            'color':colors['demand_electricity'],
            'base_tech':'demand',
            'carrier_in':'electricity',
            }
        
        if (
                self.scen_techs['scenarios']['demand_side']
                and self.scen_techs['demand_side']['ev_integration']
                and self.scen_techs['demand_side']['ev_flexibility']
                ):
            
            techs_dict['demand_electricity_ev_pd'] = {
                'name':'Electrical Demand EV - lower bound',
                'color':colors['demand_electricity'],
                'base_tech':'demand',
                'carrier_in':'electricity',
                }
            techs_dict['demand_electricity_ev_delta'] = { # Difference between upper and lower bound
                'name':'Electrical Demand EV - delta',
                'color':colors['demand_electricity'],
                'base_tech':'demand',
                'carrier_in':'electricity',
                }
            
            # Virtual variable to quantify flexibility from EV:
            techs_dict['flexibility_ev'] = {
                'name':'EV Flexibility',
                'color':colors['demand_electricity'],
                'base_tech':'supply',
                'carrier_out':'flexible_electricity',
                'source_use_max':'inf',
                'cost_flow_in':{
                    'data':0.0,
                    'index':'monetary',
                    'dims':'costs',
                    },
                'cost_interest_rate':{
                    'data':0.0,
                    'index':'monetary',
                    'dims':'costs',
                    },
                'cost_flow_out':{
                    'data':0.0,
                    'index':'emissions_co2',
                    'dims':'costs',
                    },
                }
            
        else:
            techs_dict['demand_electricity_ev'] = {
                'name':'Electrical Demand Electric Vehicles',
                'color':colors['demand_electricity'],
                'base_tech':'demand',
                'carrier_in':'electricity',
                }
        
        techs_dict['demand_heat'] = {
            'name':'Heat Demand',
            'color':colors['demand_heat'],
            'base_tech':'demand',
            'carrier_in':'heat',
            }
        
        # Add Supplies:
	    # ============        
        techs_dict = self.supply.create_supply_dict_wet_biomass(techs_dict, energy_scaling_factor = self.energy_scaling_factor)
        techs_dict = self.supply.create_supply_dict_wood(techs_dict, energy_scaling_factor = self.energy_scaling_factor)
        techs_dict = self.supply.create_supply_dict_oil(
            techs_dict, 
            color = colors['oil_supply'], 
            energy_scaling_factor = self.energy_scaling_factor
            )
        techs_dict = self.supply.create_supply_dict_gas(
            techs_dict, 
            color = colors['gas_supply'],
            energy_scaling_factor = self.energy_scaling_factor
            )
        techs_dict = self.supply.create_supply_dict_wood_import(techs_dict,
                                                                energy_scaling_factor = self.energy_scaling_factor)
        
        if 'waste_to_energy' in self.tech_list:
            # resource_msw = self.tech_waste_to_energy.get_annual_msw_supply_kWh()
            techs_dict = self.supply.create_supply_dict_msw(
                techs_dict,
                color=colors['waste_to_energy'],
                energy_scaling_factor = self.energy_scaling_factor
                # resource=resource_msw
                )
            self.tech_list_old.append('msw_supply')
        
        self.tech_list_old.append('oil_supply')
        self.tech_list_new.append('oil_supply')
        self.tech_list_old.append('gas_supply')
        self.tech_list_new.append('gas_supply')
        self.tech_list_old.append('wood_supply_import')
        self.tech_list_new.append('wood_supply_import')
        
        # Add flexibility from building inertia:
        # =====================================
        # flex_label
        if self.building_inertia_flex_flag:
            techs_dict = self.building_inertia_flex.create_techs_dict(
                techs_dict=techs_dict,
                color=colors['flexibility_vs']
                )
        
        # Add user-selected techologies:
        # =============================
        if 'heat_pump' in self.tech_list:
            energy_cap_zero_capex, cap_one_to_one_replacement, cap_new = self.tech_heat_pump.get_needs_replacement_cap()

            techs_dict, additional_techs_label = self.tech_heat_pump.create_techs_dict(
                techs_dict, 
                header = 'heat_pump_old', 
                name = 'Heat Pump Old', 
                color = colors['heat_pump'],
                energy_cap = energy_cap_zero_capex,
                create_tesdc_hp_hub = True,
                capex_level = 'zero',
                energy_scaling_factor = self.energy_scaling_factor)

            techs_dict, _ = self.tech_heat_pump.create_techs_dict(
                techs_dict, 
                header = 'heat_pump_one_to_one_replacement', 
                name = 'Heat Pump One-to-One-Replacement', 
                color = colors['heat_pump'],
                energy_cap = cap_one_to_one_replacement,
                capex_level = 'one-to-one-replacement',
                energy_scaling_factor = self.energy_scaling_factor)                
            self.tech_list_old.append('heat_pump_one_to_one_replacement')

            
            techs_dict, _ = self.tech_heat_pump.create_techs_dict(
                techs_dict, 
                header = 'heat_pump_new', 
                name = 'Heat Pump New', 
                color = colors['heat_pump'],
                energy_cap = cap_new,
                energy_scaling_factor = self.energy_scaling_factor
                )
                        
            self.tech_list_old.append('heat_pump_old')
            self.tech_list_old = self.tech_list_old + additional_techs_label
            self.tech_list_new.append('heat_pump_new')

        if 'electric_heater' in self.tech_list:
            energy_cap_eh, needs_replacement, _ = self.tech_electric_heater.get_needs_replacement_cap()
        
            techs_dict = self.tech_electric_heater.create_techs_dict(
                    techs_dict, 
                    header = 'electric_heater_old', 
                    name = 'Electric Heater Old', 
                    color = colors['electric_heater'],
                    energy_cap = energy_cap_eh,
                    capex_0 = True,
                    energy_scaling_factor = self.energy_scaling_factor)
            
            self.tech_list_old.append('electric_heater_old')
           
        if 'oil_boiler' in self.tech_list:

            energy_cap_zero_capex, cap_one_to_one_replacement, cap_new = self.tech_oil_boiler.get_needs_replacement_cap()

            techs_dict = self.tech_oil_boiler.create_techs_dict(
                techs_dict, 
                header = 'oil_boiler_old', 
                name = 'Oil Boiler Old', 
                color = colors['oil_boiler'],
                energy_cap = energy_cap_zero_capex,
                capex_level = 'zero',
                energy_scaling_factor = self.energy_scaling_factor)
            
            techs_dict = self.tech_oil_boiler.create_techs_dict(
                techs_dict, 
                header = 'oil_boiler_one_to_one_replacement', 
                name = 'Oil Boiler One-to-One-Replacement', 
                color = colors['oil_boiler'],
                energy_cap = cap_one_to_one_replacement,
                capex_level = 'one-to-one-replacement',
                energy_scaling_factor = self.energy_scaling_factor)                
            self.tech_list_old.append('oil_boiler_one_to_one_replacement')
            
            techs_dict = self.tech_oil_boiler.create_techs_dict(
                techs_dict, 
                header = 'oil_boiler_new', 
                name = 'Oil Boiler New', 
                color = colors['oil_boiler'],
                energy_cap = cap_new,
                capex_level = 'full',
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('oil_boiler_old')
            self.tech_list_new.append('oil_boiler_new')
                 
        if 'gas_boiler' in self.tech_list:

            energy_cap_zero_capex, cap_one_to_one_replacement, cap_new = self.tech_gas_boiler.get_needs_replacement_cap()

            techs_dict = self.tech_gas_boiler.create_techs_dict(
                techs_dict, 
                header = 'gas_boiler_old', 
                name = 'Gas Boiler Old', 
                color = colors['gas_boiler'],
                energy_cap = energy_cap_zero_capex,
                capex_level = 'zero',
                energy_scaling_factor = self.energy_scaling_factor
                )

            techs_dict = self.tech_gas_boiler.create_techs_dict(
                techs_dict, 
                header = 'gas_boiler_one_to_one_replacement', 
                name = 'Gas Boiler One-to-One-Replacement', 
                color = colors['gas_boiler'],
                energy_cap = cap_one_to_one_replacement,
                capex_level = 'one-to-one-replacement',
                energy_scaling_factor = self.energy_scaling_factor
                )                
            self.tech_list_old.append('gas_boiler_one_to_one_replacement')
            
            techs_dict = self.tech_gas_boiler.create_techs_dict(
                techs_dict, 
                header = 'gas_boiler_new', 
                name = 'Gas Boiler New', 
                color = colors['gas_boiler'],
                energy_cap = cap_new,
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('gas_boiler_old')
            self.tech_list_new.append('gas_boiler_new')
           
        if 'wood_boiler' in self.tech_list:
            
            energy_cap_zero_capex, cap_one_to_one_replacement, cap_new = self.tech_wood_boiler.get_needs_replacement_cap()

            techs_dict = self.tech_wood_boiler.create_techs_dict(
                techs_dict, 
                header = 'wood_boiler_old', 
                name = 'Wood Boiler Old', 
                color = colors['wood_boiler'],
                energy_cap = energy_cap_zero_capex,
                capex_level = 'zero',
                energy_scaling_factor = self.energy_scaling_factor
                )

            techs_dict = self.tech_wood_boiler.create_techs_dict(
                techs_dict, 
                header = 'wood_boiler_one_to_one_replacement', 
                name = 'Wood Boiler One-to-One-Replacement', 
                color = colors['wood_boiler'],
                energy_cap = cap_one_to_one_replacement,
                capex_level = 'one-to-one-replacement',
                energy_scaling_factor = self.energy_scaling_factor
                )                
            self.tech_list_old.append('wood_boiler_one_to_one_replacement')
            
            techs_dict = self.tech_wood_boiler.create_techs_dict(
                techs_dict, 
                header = 'wood_boiler_new', 
                name = 'Wood Boiler New', 
                color = colors['wood_boiler'],
                energy_cap = cap_new,
                capex_level = 'full',
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('wood_boiler_old')
            self.tech_list_new.append('wood_boiler_new')
             
        if 'district_heating' in self.tech_list:
            techs_dict, dh_techs_label_list =\
                self.tech_district_heating.create_techs_dict(
                    techs_dict,
                    color=colors['district_heating'],
                    energy_scaling_factor = self.energy_scaling_factor
                    )
            
            self.tech_list_old = self.tech_list_old + dh_techs_label_list
            
        if 'solar_pvrooftop' in self.tech_list:
            
            # print(self.tech_solar_pvrooftop.get_num_installations())

            techs_dict, headers = self.tech_solar_pvrooftop.create_techs_dict(techs_dict,
                                                                              color = colors['solar_pv'],
                                                                              resources = [
                                                                                  None
                                                                                  for i in range(self.tech_solar_pvrooftop.get_num_installations())],
                                                                              energy_scaling_factor = self.energy_scaling_factor
                                                                              )
            
            self.tech_list_pv.append(headers)

        if 'solarthermal_rooftop' in self.tech_list:
            
            # print(self.tech_solarthermal_rooftop.get_num_installations())

            techs_dict, headers = self.tech_solarthermal_rooftop.create_techs_dict(techs_dict, 
                                                                                   color = colors['solar_thermal'],
                                                                                   resources = [
                                                                                    None
                                                                                    for i in range(self.tech_solarthermal_rooftop.get_num_installations())], 
                                                                                  energy_scaling_factor = self.energy_scaling_factor
                                                                              )
            
            self.tech_list_solarthermal.append(headers)
        else:
            self.tech_list_solarthermal.append(None)

        if 'solar_pvalpine' in self.tech_list:
            
            print(self.tech_solar_pvalpine.get_num_installations())

            techs_dict, headers = self.tech_solar_pvalpine.create_techs_dict(techs_dict,
                                                                              color = colors['solar_pv'],
                                                                              resources = [
                                                                                  None
                                                                                  for i in range(self.tech_solar_pvalpine.get_num_installations())],
                                                                              energy_scaling_factor = self.energy_scaling_factor
                                                                              )
            
            self.tech_list_pv.append(headers)
            self.tech_list_solarthermal.append(None)

        if 'wind_power' in self.tech_list:
            
            techs_dict = self.tech_wind_power.create_techs_dict_unit(
                techs_dict,
                colors['wind_power'],
                energy_scaling_factor = self.energy_scaling_factor
                )

            techs_dict = self.tech_wind_power.create_techs_dict(
                techs_dict = techs_dict,
                header = 'wind_power_old',
                name = 'Wind Power Old',
                color = colors['wind_power'],
                export_cost=0, # subsidy for feed-in; used to prefer wind over hydro
                capex_0 = True,
                energy_scaling_factor = self.energy_scaling_factor
                
                )
            
            techs_dict = self.tech_wind_power.create_techs_dict(
                techs_dict = techs_dict,
                header = 'wind_power_new',
                name = 'Wind Power New',
                color = colors['wind_power'],
                export_cost=0.0,
                energy_scaling_factor = self.energy_scaling_factor
                )                

            self.tech_list_old.append('wind_power_old')
            self.tech_list_new.append('wind_power_new')
            
        if 'hydro_power' in self.tech_list:
            energy_cap, _ , _ = self.tech_hydro_power.get_needs_replacement_cap()
            
            techs_dict = self.tech_hydro_power.create_techs_dict(
                techs_dict=techs_dict,
                header = 'hydro_power',
                name = 'Hydro Power',
                color = colors['hydro_power'],
                resource = None,
                energy_cap = energy_cap,
                capex_0 = True,
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            # Force deployment of currently installed systems:
            techs_dict['hydro_power']['flow_cap_equals'] = float(energy_cap)/self.energy_scaling_factor
            
            self.tech_list_old.append('hydro_power')
            
        if 'grid_supply' in self.tech_list:
            techs_dict = self.tech_grid_supply.create_techs_dict(
                techs_dict,
                colors['grid_supply'],
                resource_tariff_timeseries = None,
                resource_co2_intensity_timeseries = None,
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_grid_connection.append('grid_supply')

        if 'grid_export' in self.tech_list:
            techs_dict = self.tech_grid_export.create_techs_dict(
                techs_dict,
                colors['grid_export'],
                resource_tariff_timeseries = None,
                resource_co2_intensity_timeseries = None,
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_grid_connection.append('grid_export')

        if 'tes' in self.tech_list:
            techs_dict, tes_techs_label_list = self.tech_tes.create_techs_dict(
                techs_dict,
                colors['tes'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old = self.tech_list_old + tes_techs_label_list

        if 'tes_sites' in self.tech_list:
            techs_dict, tes_sites_techs_label_list = self.tech_tes_sites.create_techs_dict(
                techs_dict,
                colors['tes'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old = self.tech_list_old + tes_sites_techs_label_list

        if 'tes_decentralised' in self.tech_list:
            techs_dict, tesdc_techs_label_list = self.tech_tes_decentralised.create_techs_dict(
                techs_dict,
                colors['tes_decentralised'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old = self.tech_list_old + tesdc_techs_label_list
             
        if 'bes' in self.tech_list:
            techs_dict = self.tech_bes.create_techs_dict(
                techs_dict,
                colors['bes'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            self.tech_list_old.append('bes')
        
        if 'pile_of_berries' in self.tech_list:
            techs_dict = self.tech_pile_of_berries.create_techs_dict(
                techs_dict
                )
            self.tech_list_old.append('pile_of_berries')

        if 'gtes' in self.tech_list:
            techs_dict = self.tech_gtes.create_techs_dict(
                techs_dict,
                colors['gtes'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            self.tech_list_old.append('gtes')

        if 'ws' in self.tech_list:
            techs_dict = self.tech_ws.create_techs_dict(
                techs_dict,
                colors['ws'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            self.tech_list_old.append('ws')


        if 'hes' in self.tech_list:
            techs_dict = self.tech_hes.create_techs_dict(
                techs_dict,
                colors['hes'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            self.tech_list_new.append('hes')

        if 'hydrothermal_gasification' in self.tech_list:
            techs_dict = self.tech_hydrothermal_gasification.generate_tech_dict(techs_dict, energy_scaling_factor = self.energy_scaling_factor)
            
            self.tech_list_new.append('hydrothermal_gasification')
        
        if 'anaerobic_digestion_upgrade' in self.tech_list:
            techs_dict = self.tech_anaerobic_digestion_upgrade.generate_tech_dict(techs_dict, energy_scaling_factor = self.energy_scaling_factor)
            
            self.tech_list_new.append('anaerobic_digestion_upgrade')
            
        if 'anaerobic_digestion_upgrade_hydrogen' in self.tech_list:
            techs_dict = self.tech_anaerobic_digestion_upgrade_hydrogen.generate_tech_dict(techs_dict, energy_scaling_factor = self.energy_scaling_factor)
            
            self.tech_list_new.append('anaerobic_digestion_upgrade_hydrogen')
            
        if 'anaerobic_digestion_chp' in self.tech_list:
            techs_dict = self.tech_anaerobic_digestion_chp.generate_tech_dict(techs_dict, energy_scaling_factor = self.energy_scaling_factor)
            
            self.tech_list_new.append('anaerobic_digestion_chp')
        
        if 'wood_gasification_upgrade' in self.tech_list:
            techs_dict = self.tech_wood_gasification_upgrade.generate_tech_dict(techs_dict, energy_scaling_factor = self.energy_scaling_factor)
            
            self.tech_list_new.append('wood_gasification_upgrade')
            
        if 'wood_gasification_upgrade_hydrogen' in self.tech_list:
            techs_dict = self.tech_wood_gasification_upgrade_hydrogen.generate_tech_dict(techs_dict, energy_scaling_factor = self.energy_scaling_factor)
            
            self.tech_list_new.append('wood_gasification_upgrade_hydrogen')
            
        if 'wood_gasification_chp' in self.tech_list:
            techs_dict = self.tech_wood_gasification_chp.generate_tech_dict(techs_dict, energy_scaling_factor = self.energy_scaling_factor)
            
            self.tech_list_new.append('wood_gasification_chp')
            
        if 'hydrogen_production' in self.tech_list:
            techs_dict = self.tech_hydrogen_production.generate_tech_dict(techs_dict, energy_scaling_factor = self.energy_scaling_factor)
            
            self.tech_list_new.append('hydrogen_production')
            
        if 'chp_gt' in self.tech_list:            
            techs_dict = self.tech_chp_gt.create_techs_dict(
                techs_dict=techs_dict,
                header='chp_gt_new',
                name='CHP Gas Turbine New',
                color=colors['chp_gt'],
                energy_scaling_factor = self.energy_scaling_factor
                )            
            
            self.tech_list_old.append('chp_gt_new')
            
        if 'gas_turbine_cp' in self.tech_list:
            techs_dict = self.tech_gas_turbine_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='gas_turbine_cp_exist',
                name='Gas Turbine (central plant)',
                color=colors['gas_turbine_cp'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('gas_turbine_cp_exist')
            
        if 'steam_turbine' in self.tech_list:
            techs_dict = self.tech_steam_turbine.create_techs_dict(
                techs_dict=techs_dict,
                header='steam_turbine_exist',
                name='Steam Turbine',
                color=colors['steam_turbine'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('steam_turbine_exist')
            
        if 'wood_boiler_sg' in self.tech_list:
            techs_dict = self.tech_wood_boiler_sg.create_techs_dict(
                techs_dict=techs_dict,
                header='wood_boiler_sg_exist',
                name='Wood boiler (steam generator)',
                color=colors['wood_boiler_sg'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('wood_boiler_sg_exist')
            
        if 'waste_to_energy' in self.tech_list:
            techs_dict = self.tech_waste_to_energy.create_techs_dict(
                techs_dict=techs_dict,
                header='waste_to_energy_exist',
                name='Waste-to-Energy',
                color=colors['waste_to_energy'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('waste_to_energy_exist')
            
        if 'heat_pump_cp' in self.tech_list:
            techs_dict = self.tech_heat_pump_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='heat_pump_cp_exist',
                name='Heat pump (central plant)',
                color=colors['heat_pump_cp'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('heat_pump_cp_exist')

            
        if 'heat_pump_cp_lt' in self.tech_list:
            techs_dict = self.tech_heat_pump_cp_lt.create_techs_dict(
                techs_dict=techs_dict,
                header='heat_pump_cp_lt_exist',
                name='Heat pump (central plant, from low temperature heat)',
                color=colors['heat_pump_cp_lt'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('heat_pump_cp_lt_exist')

        if 'oil_boiler_cp' in self.tech_list:
            techs_dict = self.tech_oil_boiler_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='oil_boiler_cp_exist',
                name='Oil boiler (central plant)',
                color=colors['oil_boiler_cp'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('oil_boiler_cp_exist')
 
        if 'electric_heater_cp' in self.tech_list:
            techs_dict = self.tech_electric_heater_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='electric_heater_cp_exist',
                name='Electric Heater (central plant)',
                color=colors['electric_heater_cp'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('electric_heater_cp_exist')

        if 'wood_boiler_cp' in self.tech_list:
            techs_dict = self.tech_wood_boiler_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='wood_boiler_cp_exist',
                name='Wood boiler (central plant)',
                color=colors['wood_boiler_cp'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('wood_boiler_cp_exist')

        if 'deep_geothermal' in self.tech_list:
            techs_dict = self.tech_deep_geothermal.create_techs_dict(
                techs_dict=techs_dict,
                header='deep_geothermal_exists',
                name='Deep Geothermal',
                color=colors['deep_geothermal'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('deep_geothermal_exists')

        if 'heat_demand_manual' in self.tech_list:
            techs_dict = self.tech_heat_demand_manual.create_techs_dict(
                techs_dict=techs_dict,
                header='heat_demand_manual_exists',
                name='Heat demand manual (sink)',
                color=colors['heat_demand_manual'],
                resource=None,
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('heat_demand_manual_exists')



        if 'waste_heat' in self.tech_list:
            techs_dict = self.tech_waste_heat.create_techs_dict(
                techs_dict=techs_dict,
                header='waste_heat_exists',
                name='Waste heat (source)',
                color=colors['waste_heat'],
                resource=None,
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('waste_heat_exists')

        if 'waste_heat_low_temperature' in self.tech_list:
            techs_dict = self.tech_waste_heat_low_temperature.create_techs_dict(
                techs_dict=techs_dict,
                header='waste_heat_low_temperature_exists',
                name='Waste heat (source at low temperature)',
                color=colors['waste_heat_low_temperature'],
                resource=None,
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('waste_heat_low_temperature_exists')

        if 'gas_boiler_cp' in self.tech_list:
            techs_dict = self.tech_gas_boiler_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='gas_boiler_cp_exist',
                name='Gas boiler (central plant)',
                color=colors['gas_boiler_cp'],
                energy_scaling_factor = self.energy_scaling_factor
                )
            
            self.tech_list_old.append('gas_boiler_cp_exist')

        # Add connections (i.e. transmission lines):
        link_nodes = ['New_Techs']

        if 'wind_power' in self.tech_list:
            link_nodes.append('loc_wp_winter')
            link_nodes.append('loc_wp_annual')

        if len(self.tech_list_pv) > 0:
            for i in range(len(self.tech_list_pv)):
                for j in range(len(self.tech_list_pv[i])):
                    link_nodes.append(self.tech_list_pv[i][j])

        flow_cap_equals = None
        if self.tech_grid_supply._kW_max != 'inf':
            flow_cap_equals = self.tech_grid_supply._kW_max / self.energy_scaling_factor

        techs_dict = self.__techs_dict_add_transmission_link(
            techs_dict,
            colors,
            link_from='X1',
            link_to='Grid_Connection_Node',
            line_type='power_line',
            carrier='electricity',
            name='Electrical power transmission',
            color_key='power_line',
            flow_cap_equals=flow_cap_equals
            )

        for node in link_nodes:
            techs_dict = self.__techs_dict_add_transmission_link(
                techs_dict,
                colors,
                link_from='X1',
                link_to=node,
                line_type='power_line',
                carrier='electricity',
                name='Electrical power transmission',
                color_key='power_line'
                )
            techs_dict = self.__techs_dict_add_transmission_link(
                techs_dict,
                colors,
                link_from='X1',
                link_to=node,
                line_type='hp_heat_line',
                carrier='heat_hp',
                name='Heat transmission for HP heat',
                color_key='heat_line'
                )

        link_specs = [
            {
                'link_from':'X1',
                'link_to':'New_Techs',
                'line_type':'heat_line',
                'carrier':'heat',
                'name':'Heat transmission',
                'color_key':'heat_line',
                },
            {
                'link_from':'X1',
                'link_to':'New_Techs',
                'line_type':'heat_biomass_line',
                'carrier':'heat_biomass',
                'name':'Heat biomass transmission',
                'color_key':'heat_line',
                },
            {
                'link_from':'X1',
                'link_to':'New_Techs',
                'line_type':'gas_line',
                'carrier':'gas',
                'name':'Gas transmission',
                'color_key':'gas_line',
                },
            {
                'link_from':'X1',
                'link_to':'Limited_Supplies',
                'line_type':'wood_line',
                'carrier':'wood',
                'name':'Wood transmission',
                'color_key':'wood_line',
                },
            {
                'link_from':'New_Techs',
                'link_to':'Limited_Supplies',
                'line_type':'wood_line',
                'carrier':'wood',
                'name':'Wood transmission',
                'color_key':'wood_line',
                },
            {
                'link_from':'New_Techs',
                'link_to':'Limited_Supplies',
                'line_type':'wet_biomass_line',
                'carrier':'wet_biomass',
                'name':'Wet biomass transmission',
                'color_key':'wet_biomass_line',
                },
            ]

        for link_spec in link_specs:
            techs_dict = self.__techs_dict_add_transmission_link(
                techs_dict,
                colors,
                **link_spec
                )
   
        return techs_dict
        
    def __create_nodes_dict(self):
        
        # Techs with separate nodes:
        tech_locs = ['wind_power_old', 'wind_power_new']#, 'solar_thermal_old', 'solar_pv_old']
        
        # Dictionary to be populated for main node X1:
        nodes_dict = {
            'X1':{
                'techs':{
                    'demand_electricity_baseline':{},
                    # 'demand_electricity_ev':{},
                    'demand_heat':{}
                    },
                # 'available_area': 1, # used for "resources competition" between pv and solar thermal; a virtual value of 1 is used.
                'latitude':1,
                'longitude':1,
                },
            'Grid_Connection_Node':{
                'techs':{
                    },
                'latitude':0,
                'longitude':0,
                },

            'New_Techs':{
                'techs':{},
                # 'available_area': self.available_area_scaling, # used for "resources competition" between pv and solar thermal; a virtual value of 1 is used.
                'latitude':5,
                'longitude':5,
                },
            'Limited_Supplies':{
                'techs':{
                    'wet_biomass_supply':{},
                    'wood_supply':{}
                    },
                'latitude':6,
                'longitude':6,
                }
                    }
        
        if (
                self.scen_techs['scenarios']['demand_side']
                and self.scen_techs['demand_side']['ev_integration']
                and self.scen_techs['demand_side']['ev_flexibility']
                ):
            
            nodes_dict['X1']['techs']['demand_electricity_ev_pd'] = {}
            nodes_dict['X1']['techs']['demand_electricity_ev_delta'] = {}
            nodes_dict['X1']['techs']['flexibility_ev'] = {}

        else:
            nodes_dict['X1']['techs']['demand_electricity_ev'] = {}
            
        # flex_label
        if self.building_inertia_flex_flag:

            flex_systems = self.building_inertia_flex.get_flex_systems()
            
            for key, acr in flex_systems.items():
                # key: full tech name (e.g., 'heat_pump', 'district_heating')
                # acr: acronym (e.g., 'hp', 'dh')
                nodes_dict['X1']['techs'][f'virtual_storage_flex_{acr}'] = {}
                nodes_dict['X1']['techs'][f'virtual_storage_drain_{acr}'] = {}
                nodes_dict['X1']['techs'][f'conv_{acr}_vs'] = {}
                
        if len(self.tech_list_pv) > 0:
            for i in range(len(self.tech_list_pv)):
                for j in range(len(self.tech_list_pv[i])):
                    nodes_dict[self.tech_list_pv[i][j]] = {
                        'techs': {},
                        'available_area': self.available_area_scaling,
                        'latitude':10+i,
                        'longitude':j,
                    }

        # ---------------------------------------------------------------------
        # Populate nodes_dict for main node X1:
        for tech in self.tech_list_old:
            if tech in tech_locs:
                # This tech will have a separate node
                pass
            else:
                nodes_dict['X1']['techs'][tech] = None
        for tech in self.tech_list_grid_connection:
            if tech in tech_locs:
                # This tech will have a separate node
                pass
            else:
                nodes_dict['Grid_Connection_Node']['techs'][tech] = None

        for tech in self.tech_list_new:
            if tech in tech_locs:
                # This tech will have a separate node
                pass
            else:
                nodes_dict['New_Techs']['techs'][tech] = None

        for i in range(len(self.tech_list_pv)):

            techs = self.tech_list_pv[i]

            for j in range(len(techs)):

                tech = techs[j]

                nodes_dict[tech]['techs'][tech+"_occupied"] = None
                nodes_dict[tech]['techs'][tech+"_unoccupied"] = None

                if self.tech_list_solarthermal[i] != None:
                    tech_thermal = self.tech_list_solarthermal[i][j]
                    nodes_dict[tech]['techs'][tech_thermal+"_occupied"] = None
                    nodes_dict[tech]['techs'][tech_thermal+"_unoccupied"] = None
        
        # ---------------------------------------------------------------------
        # Populate nodes_dict for currently existing (i.e. "old") tech nodes:
        # if 'solar_thermal_old' in self.tech_list_old:
        #     nodes_dict['Old_Solar_Thermal']['techs']['solar_thermal_old'] = None
            
        # if 'solar_pv_old' in self.tech_list_old:
        #     nodes_dict['Old_Solar_PV']['techs']['solar_pv_old'] = None
        
        # ---------------------------------------------------------------------
        # Populate nodes_dict for wind power nodes:
        if 'wind_power' in self.tech_list:
            # Calculate max. capacities:
            tmp_cap_max_input = self.tech_wind_power.get_kWp_max()
            tmp_cap_max_resource_annual =\
                self.tech_wind_power.compute_cap_max_resource_annual()
            tmp_cap_max_resource_winter =\
                self.tech_wind_power.compute_cap_max_resource_winter()
            cap_max_annual = min(tmp_cap_max_input, tmp_cap_max_resource_annual)            
            cap_max_winter = min(tmp_cap_max_input, tmp_cap_max_resource_winter)
            
            # Currently installed capacity
            p_e_wp_kW = self.tech_wind_power.get_p_e_kW()
            
            installed_alloc = self.tech_wind_power.get_installed_allocation()

            if installed_alloc == 'local':
            # The currently installed wind power is considered local:                        
                if p_e_wp_kW <= cap_max_annual:
                    cap_max_installed_annual = p_e_wp_kW
                    cap_max_installed_winter = 0
                    cap_max_new_annual = max(0, cap_max_annual - p_e_wp_kW) # use max() to avoid negative values
                    cap_max_new_winter = cap_max_winter
                elif p_e_wp_kW > cap_max_annual:
                    cap_max_installed_annual = cap_max_annual
                    cap_max_installed_winter = max(0, p_e_wp_kW - cap_max_installed_annual) # use max() to avoid negative values 
                    cap_max_new_annual = 0
                    cap_max_new_winter = max(0, cap_max_winter - cap_max_installed_winter) # use max() to avoid negative values

            elif installed_alloc == 'national':
            # The currently installed wind power is considered national:                
                if p_e_wp_kW <= cap_max_annual:
                    cap_max_installed_annual = 0
                    cap_max_installed_winter = 0
                    cap_max_new_annual = max(0, cap_max_annual - p_e_wp_kW) # use max() to avoid negative values
                    cap_max_new_winter = cap_max_winter
                elif p_e_wp_kW > cap_max_annual:
                    cap_max_installed_annual = 0
                    cap_max_installed_winter = 0
                    cap_max_new_annual = 0
                    cap_max_new_winter = max(0, cap_max_winter - (p_e_wp_kW - cap_max_annual)) # use max() to avoid negative values
            
            # -----------------------------------------------------------------
            # Location for wind power with profile of type 'annual':
            
            # Create dict:
            nodes_dict['loc_wp_annual'] = {
                'techs':{
                    'wind_power_old':{},
                    'wind_power_new':{},
                    },
                'latitude':3,
                'longitude':3,
                }
            # Add max. capacities:
            # nodes_dict['loc_wp_annual']['techs']['wind_power_old']['flow_cap_max'] =\
            #     cap_max_installed_annual
            nodes_dict['loc_wp_annual']['techs']['wind_power_new']['flow_cap_max'] =\
                cap_max_new_annual / self.energy_scaling_factor
            # Force capacity for currently installed capacities:
            # nodes_dict['loc_wp_annual']['techs']['wind_power_old']['source_cap_equals'] =\
            #     cap_max_installed_annual
            nodes_dict['loc_wp_annual']['techs']['wind_power_old']['flow_cap_max'] =\
                cap_max_installed_annual / self.energy_scaling_factor
            # Add wind power conversion unit:
            nodes_dict['loc_wp_annual']['techs']['wind_power_unit'] = {}
            nodes_dict['loc_wp_annual']['techs']['wind_power_unit']['flow_cap_per_unit'] =\
                cap_max_annual / self.energy_scaling_factor
            
            # -----------------------------------------------------------------
            # Location for wind power with profile of type 'winter':
            
            # Create dict:
            nodes_dict['loc_wp_winter'] = {
                'techs':{
                    'wind_power_old':{},
                    'wind_power_new':{}
                    },
                'latitude':2,
                'longitude':2,
                }
            # Add max. capacities:
            # nodes_dict['loc_wp_winter']['techs']['wind_power_old']['flow_cap_max'] =\
            #     cap_max_installed_winter
            nodes_dict['loc_wp_winter']['techs']['wind_power_new']['flow_cap_max'] =\
                cap_max_new_winter / self.energy_scaling_factor
            # Force capacity for currently installed capacities:
            # nodes_dict['loc_wp_winter']['techs']['wind_power_old']['source_cap_equals'] =\
            #     cap_max_installed_winter
            nodes_dict['loc_wp_winter']['techs']['wind_power_old']['flow_cap_max'] =\
                cap_max_installed_winter / self.energy_scaling_factor
            # Add wind power conversion unit:
            nodes_dict['loc_wp_winter']['techs']['wind_power_unit'] = {}
            nodes_dict['loc_wp_winter']['techs']['wind_power_unit']['flow_cap_per_unit'] =\
                cap_max_winter / self.energy_scaling_factor
            
        return nodes_dict
    
    def __create_run_dict(self):
        
        # Adjust MIPGap if Storage techs are selected (to reduce runtime)
        mipgap_ = self.opt_metrics['solver_option_MIPGap']
        
        if self.opt_metrics['MIPGap_increase']:        
            if mipgap_ >= 0.01:
                pass
            elif ('tes' in self.tech_list 
                  or 'bes' in self.tech_list 
                  or 'gtes' in self.tech_list 
                  or 'hes' in self.tech_list 
                  or 'ws' in self.tech_list 
                  or 'tes_sites' in self.tech_list):
                mipgap_ = 0.01 # MIPGap increased to 1% to reduce optimisation runtime
                print("\nSolver MIPGap increased to 1% because of deployment of "
                      "storage technology. Storage technologies contain MIP "
                      "constraints, increasing the runtime of the "
                      "optimisation.\n")
        
        run_dict = {
            'mode':'base',
            'solver':self.opt_metrics['solver'],
            'ensure_feasibility':True,
            # 'cyclic_storage':'true', # If uncommented, 'storage_initial' in bes and tes is not working; cycling constraint is activated by default
            'bigM':self.opt_metrics['bigM_value'],
            'objective_options':{
                'cost_class': {
                    'monetary':self.opt_metrics['objective_monetary'],
                    'emissions_co2':self.opt_metrics['objective_co2']
                    }
                },
            'solver_options':{ # Gurobi options: https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#timelimit
                'NumericFocus':self.opt_metrics['solver_option_NumericFocus'],
                'TimeLimit':self.opt_metrics['solver_option_TimeLimit'],
                'Presolve':self.opt_metrics['solver_option_Presolve'],
                'Aggregate':self.opt_metrics['solver_option_Aggregate'],
                'FeasibilityTol':self.opt_metrics['solver_option_FeasibilityTol'] / self.energy_scaling_factor,
                'MIPGap':mipgap_,
                
                }
            }
        
        return run_dict
    
    def __get_constant_heat_source_techs(self):

        const_techs = [
            'heat_pump_hub',
            'electric_heater_old',
            'oil_boiler_old',
            'oil_boiler_new',
            'oil_boiler_one_to_one_replacement',
            'gas_boiler_old',
            'gas_boiler_new',
            'gas_boiler_one_to_one_replacement',
            'wood_boiler_old',
            'wood_boiler_new',
            'wood_boiler_one_to_one_replacement',
            ] # ensure techs are spelled correctly (no error is thrown if tech doesn't exist)!

        # Create district heating labels:
        if self.dhn_qty == 0:
            const_techs.append('district_heating_hub')
        elif self.dhn_qty >= 0:
            for i in range(self.dhn_qty):
                const_techs.append(f"district_heating_hub_{i}")

        return const_techs

    def __get_district_heating_share_techs(self):

        dhn_list = []
        if self.dhn_qty == 0:
            dhn_list.append('district_heating_hub')
        elif self.dhn_qty >= 0:
            for i in range(self.dhn_qty):
                dhn_list.append(f"district_heating_hub_{i}")

        return dhn_list

    @staticmethod
    def __math_list(items):

        return '['+', '.join(items)+']'

    def __create_math_dict(self):

        math_dict = {
            'variables':{},
            'constraints':{},
            }

        def add_share_constraint(name, techs, nodes, share, operator):

            if len(techs) == 0:
                return

            math_dict['constraints'][name] = {
                'foreach':['timesteps'],
                'equations':[
                    {
                        'expression':(
                            'sum('
                            +'flow_out['
                            +'nodes='+self.__math_list(nodes)+', '
                            +'techs='+self.__math_list(techs)+', '
                            +'carriers=heat'
                            +'], over=[nodes, techs]) '
                            +operator+' '
                            +'sink_use_equals[nodes=X1, techs=demand_heat] * '
                            +str(share)
                            )
                        }
                    ],
                }

        const_techs = self.__get_constant_heat_source_techs()

        math_dict['variables']['constant_heat_source_share'] = {
            'foreach':['techs'],
            'where':'techs='+self.__math_list(const_techs),
            'bounds':{
                'min':0,
                'max':'.inf',
                },
            'default':0,
            }

        math_dict['constraints']['constant_heat_sources'] = {
            'foreach':['techs', 'timesteps'],
            'where':'techs='+self.__math_list(const_techs),
            'equations':[
                {
                    'expression':(
                        'sum('
                        +'flow_out[nodes=[X1, New_Techs], carriers=heat], '
                        +'over=nodes'
                        +') == '
                        +'sink_use_equals[nodes=X1, techs=demand_heat] * '
                        +'constant_heat_source_share'
                        )
                    }
                ],
            }

        # self.rerun_eps = True
        # # # self.eps_n = 2091119.65019013
        # self.eps_n = 1707022.26495658
        # 429454470
        # 448447074
        
        if self.rerun_eps:
            math_dict['constraints']['systemwide_co2_cap'] = {
                'equations':[
                    {
                        'expression':(
                            'sum(cost[costs=emissions_co2], over=[nodes, techs]) <= '
                            +str(self.eps_n)
                            )
                        }
                    ],
                }

        # Constraint in regard to what share of the heat demand shall be supplied by district heating:
        dhn_list = self.__get_district_heating_share_techs()
        if self.dhn_share_type == 'fixed':
            add_share_constraint(
                'dhn_demand_share',
                dhn_list,
                ['X1'],
                self.dhn_share_val,
                '=='
                )
        elif self.dhn_share_type == 'min':
            add_share_constraint(
                'dhn_demand_share',
                dhn_list,
                ['X1'],
                self.dhn_share_val,
                '>='
                )
        elif self.dhn_share_type == 'max':
            add_share_constraint(
                'dhn_demand_share',
                dhn_list,
                ['X1'],
                self.dhn_share_val,
                '<='
                )

        elif self.dhn_share_type == 'free':
            pass
        
        else:
            raise ValueError("district_heating.demand_share_type invalid!")
            
        # Fixed demand shares of decentralised heating techs:
        if self.hp_fixed_demand_share:
            add_share_constraint(
                'hp_demand_share',
                ['heat_pump_hub'],
                ['X1'],
                self.hp_fixed_demand_share_val,
                '=='
                )

        if self.eh_fixed_demand_share:
            add_share_constraint(
                'eh_demand_share',
                ['electric_heater_old'],
                ['X1'],
                self.eh_fixed_demand_share_val,
                '=='
                )

        if self.ob_fixed_demand_share:
            add_share_constraint(
                'ob_demand_share',
                ['oil_boiler_old', 'oil_boiler_new'],
                ['X1', 'New_Techs'],
                self.ob_fixed_demand_share_val,
                '=='
                )

        if self.gb_fixed_demand_share:
            add_share_constraint(
                'gb_demand_share',
                ['gas_boiler_old', 'gas_boiler_new'],
                ['X1', 'New_Techs'],
                self.gb_fixed_demand_share_val,
                '=='
                )

        if self.wb_fixed_demand_share:
            add_share_constraint(
                'wb_demand_share',
                ['wood_boiler_old', 'wood_boiler_new'],
                ['X1', 'New_Techs'],
                self.wb_fixed_demand_share_val,
                '=='
                )

        return math_dict
        
    def __techs_dict_add_transmission_link(
            self,
            techs_dict,
            colors,
            link_from,
            link_to,
            line_type,
            carrier,
            name,
            color_key,
            flow_cap_equals=None
            ):

        header = (
            link_from.lower()
            +'_to_'
            +link_to.lower()
            +'_'
            +line_type
            )

        techs_dict[header] = {
            'name':name,
            'color':colors[color_key],
            'base_tech':'transmission',
            'link_from':link_from,
            'link_to':link_to,
            'carrier_in':carrier,
            'carrier_out':carrier,
            'flow_out_eff':1.0,
            'lifetime':100,
            'cost_interest_rate':{
                'data':0.0,
                'index':'monetary',
                'dims':'costs',
                },
            'cost_flow_cap':{
                'data':0.0,
                'index':'monetary',
                'dims':'costs',
                },
            'cost_flow_out':{
                'data':0.0,
                'index':'emissions_co2',
                'dims':'costs',
                },
            }

        if flow_cap_equals is not None:
            techs_dict[header]['flow_cap_equals'] = flow_cap_equals

        return techs_dict
