# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 15:05:43 2023

@author: Somesh Vijayananda
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
# import json

from district_energy_model import dem_supply
from district_energy_model import dem_techs
from district_energy_model import dem_energy_balance as dem_eb
from district_energy_model import dem_clustering

class CalliopeOptimiser:
    
    def __init__(self, tech_list, scen_techs, df_scen, com_name, com_file):
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
        self.scen_techs = scen_techs
        self.df_scen = df_scen
        self.com_name = com_name
        self.com_file = com_file
        
        self.tech_list_heat = []
        self.tech_list_central = []

    def run_optimisation(self):
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
        
        import calliope

        print('------------------------------------------------------------')
        print('****OPTIMISATION****')
        ''' -------------------------------------------------------------------
        1. Create timeseries data:
        '''
        # https://calliope.readthedocs.io/en/stable/user/building.html#reading-in-timeseries-from-pandas-dataframes   
        df_demand_heat_temp = -self.df_scen.loc[:, (slice(None), 'd_h_w/o_hp')].droplevel('cluster', axis = 1) # in Calliope all demands must be negative
        df_demand_power = -self.df_scen.loc[:, (0, 'd_e_hh')] # in Calliope all demands must be negative
        
        df_pv_resource_old = self.df_scen.loc[:, (0, 'v_e_pv')]
        df_pv_resource_new = self.df_scen.loc[:, (0, 'v_e_pv_pot_remain')]
        
        df_supply_wet_biomass = self.df_scen.loc[:, (0, 's_wet_bm')]
        df_supply_wood = self.df_scen.loc[:, (0, 's_wd')]
        
        df_wp_resource_annual = self.df_scen.loc[:, (0, 'v_e_wp_pot_annual_kWhpkW')] # [kWh/kW] Generation profile type 'annual' (geared towards all year production)
        df_wp_resource_winter = self.df_scen.loc[:, (0, 'v_e_wp_pot_winter_kWhpkW')] # [kWh/kW] Generatino profile type 'winter' (geared towards winter production)
        
        df_wp_curr_inst = self.df_scen.loc[:, (0, 'v_e_wp')]
        
        df_hydro_resource = self.df_scen.loc[:, (0, 'v_e_hydro')]
        
        # Fraction of installed (inst) and potential (pot) PV (used for
        # handling competing resource between solar PV and solar thermal):
        # self.f_area_installed = self.df_scen['v_e_pv'].sum() / df_pv_resource.sum()
        # self.f_area_potential = 1 - self.f_area_installed
        
        # Create a datetime index (required in Calliope)
        date_index = pd.date_range(
            start='2050-01-01',
            periods=len(df_demand_power),
            freq='H'
            )
        
        df_demand_heat = pd.DataFrame(
            data = df_demand_heat_temp.values,
            index = date_index,
            columns = np.array(range(len(df_demand_heat_temp.columns))).astype(str))
        
        # Set the datetime index to the Series:
        # df_demand_heat.index = date_index
        # df_demand_heat.columns = np.array(range(len(df_demand_heat.columns))).astype(str)
        df_demand_power = pd.Series(df_demand_power.values, index=date_index)
        df_pv_resource_old = pd.Series(df_pv_resource_old.values, index=date_index)
        df_pv_resource_new = pd.Series(df_pv_resource_new.values, index=date_index)

        df_supply_wet_biomass = pd.Series(df_supply_wet_biomass.values, index=date_index)
        df_supply_wood = pd.Series(df_supply_wood.values, index=date_index)
        df_wp_resource_annual = pd.Series(df_wp_resource_annual.values, index=date_index)
        df_wp_resource_winter = pd.Series(df_wp_resource_winter.values, index=date_index)
        df_hydro_resource = pd.Series(df_hydro_resource.values, index=date_index)

        
        # Convert pandas series to dataframe:
        # df_demand_heat = df_demand_heat.to_frame('d_h')
        df_demand_power = df_demand_power.to_frame('d_e_hh')
        df_pv_resource_old = df_pv_resource_old.to_frame('v_e_pv')
        df_pv_resource_new = df_pv_resource_new.to_frame('v_e_pv')

        df_supply_wet_biomass = df_supply_wet_biomass.to_frame('s_wet_bm')
        df_supply_wood = df_supply_wood.to_frame('s_wd')
        df_wp_resource_annual = df_wp_resource_annual.to_frame('v_e_wp')
        df_wp_resource_winter = df_wp_resource_winter.to_frame('v_e_wp')
        df_hydro_resource = df_hydro_resource.to_frame('v_e_hydro')
        
        
        # print(df_solar_th_resource_new.iloc[7:17])
        # print(df_pv_resource_new.iloc[7:17])
        # print()
        # print(df_solar_th_resource_old.iloc[7:17])
        # print(df_pv_resource_old.iloc[7:17])
        # return
        
        # Timeseries data for Calliope model: (Get these from df_scen!!!)
        timeseries_dataframes = {
            'demand_heat':df_demand_heat,
            'demand_power':df_demand_power,
            'pv_resource_old':df_pv_resource_old,
            'pv_resource_new':df_pv_resource_new,
            
            'wet_biomass_resource':df_supply_wet_biomass,
            'wood_resource':df_supply_wood,
            'wp_resource_annual':df_wp_resource_annual,
            'wp_resource_winter':df_wp_resource_winter,
            'hydro_resource':df_hydro_resource
            }

        ''' -------------------------------------------------------------------
        2. Create input dict:
        '''
        input_dict = self.__build_input_dict()
        
        # with open(paths.results_path + '/dict_1.json' , 'w', encoding='utf-8') as f:
        #         json.dump(input_dict, f, ensure_ascii=False, indent=4)
                
        # return 0, 0

        print("\nInput dict generated.\n")
        
        ''' -------------------------------------------------------------------
        3. Generate and run model:
        '''
        
        #----------------------------------------------------------------------
        # Load model:
        print("\nModel loading ...\n")
        
        
        model = calliope.Model(
            input_dict,
            timeseries_dataframes=timeseries_dataframes
            )
        
        print('\nModel running ...\n')
        #----------------------------------------------------------------------
        # Run model:
        calliope.set_log_verbosity('INFO')
        model.run()

        #----------------------------------------------------------------------
        # TEMPORARY: Plot results !!! TEMPORARY !!!
        # model.plot.timeseries()
        
        #----------------------------------------------------------------------
        # Get results:
        opt_results = model.results
        

        # !!! TEMPORARY FOR TESTING:
            
        # for axis in list(opt_results):
        #     if len(opt_results[axis].shape) <= 2:
        #         df = opt_results[axis].to_pandas()
        #         df.to_csv(paths.results_path + '/opt_res/' + axis + '.csv')
        #     elif len(opt_results[axis].shape) == 3:
        #         if opt_results[axis].shape[0] == 2:
        #             df = opt_results[axis][0,:,:].to_pandas()
        #             df.to_csv(paths.results_path + '/opt_res/' + axis + '_emissions_co2.csv')
        #             df = opt_results[axis][1,:,:].to_pandas()
        #             df.to_csv(paths.results_path + '/opt_res/' + axis + 'monetary.csv')
        #         elif opt_results[axis].shape[1] == 2:
        #             df = opt_results[axis][:,0,:].to_pandas()
        #             df.to_csv(paths.results_path + '/opt_res/' + axis + '_emissions_co2.csv')
        #             df = opt_results[axis][:,1,:].to_pandas()
        #             df.to_csv(paths.results_path + '/opt_res/' + axis + 'monetary.csv')
        #         else:
        #             print('Error in saving opt_results')
            
        #     else:
        #         print('Error in saving opt_results')
        # model.to_csv('tmp_results_for_testing/TEST_BALANCE/calliope') # !!! TEMPORARY FOR TESTING
# =======
        # ==========================================================
        # FOR TESTING ONLY!
        # UN-COMMENT FOR SAVING CALLIOPE FILES:
        # import os
        # folder_path = 'tmp_results_for_testing/' # directory where calliope files folder will be created
        # i = 0
        # while i>=0:
        #     path = f"{folder_path}calliope_files_{i}"
        #     if os.path.isdir(path):
        #         # folder already exists
        #         i += 1
        #         pass
        #     else:
        #         model.to_csv(path)
        #         i=-1
        # ==========================================================

        
        # arr = model.get_formatted_array('carrier_prod')
        
        return opt_results, model
    
    def model_rerun_e_constr(self, model, eps_n):
        
        """
        Implement custom constraints and re-run optimisation model.
        """
        
        # Custom constraints:
        # f = 𝑐_(𝐶𝑂2,𝑒𝑙)∗𝑚_𝐸+𝑐_(𝐶𝑂2,𝑃𝑉)∗𝑣_(𝑒,𝑃𝑉)+𝑐_(𝐶𝑂2,𝑤𝑖𝑛𝑑)∗𝑣_(𝑒,𝑤𝑖𝑛𝑑)+𝑐_(𝐶𝑂2,𝑠𝑜𝑙𝑎𝑟)∗𝑣_(ℎ,𝑠𝑜𝑙𝑎𝑟)+𝑐_(𝐶𝑂2,𝑜𝑏)∗𝑣_(ℎ,𝑜𝑏)+𝑐_(𝐶𝑂2,𝑤𝑏)∗𝑣_(𝑒,𝑤𝑏)+𝑐_(𝐶𝑂2,𝑔𝑏)∗𝑣_(𝑒,𝑔𝑏)+𝑐_(𝐶𝑂2,𝑑ℎ)∗𝑣_(𝑒,𝑑ℎ)
        # f <= epsilon
        
        # Get CO2 intensities [kgCO2/kWh]: # THESE MUST BE EXTRACTED FROM scen_techs
        # c_co2_grid = 0.128
        # c_co2_pv = 0
        # c_co2_wind = 0
        # c_co2_solar = 0.025
        # c_co2_ob = 0.301
        # c_co2_wb = 0.027
        # c_co2_gb = 0.228
        # c_co2_dh = 0.108
        
        c_co2_grid = self.scen_techs['grid_supply']['co2_intensity']
        c_co2_pv = self.scen_techs['solar_pv']['co2_intensity']
        c_co2_wp = self.scen_techs['wind_power']['co2_intensity']
        c_co2_solar = self.scen_techs['solar_thermal']['co2_intensity']
        c_co2_ob = self.scen_techs['oil_boiler']['co2_intensity']
        c_co2_wb = self.scen_techs['wood_boiler']['co2_intensity']
        c_co2_gb = self.scen_techs['gas_boiler']['co2_intensity']
        c_co2_dh = self.scen_techs['district_heating']['co2_intensity']

        # Number of timesteps
        ts_len = 8760 #360 = 15 days !!! THIS INPUT MUST BE TAKEN DYNAMICALLY
                
        constraint_name = 'epsilon_constraint'
        constraint_sets = ['loc_techs_supply_all']
        
        def epsilon_constraint_rule(backend_model, loc_tech):
            
            ts = backend_model.timesteps # retrieve timesteps
            
            print('-----------------------------')
            print('run epsilon_constraint_rule()')
            print('-----------------------------')
        

            sum_kgCO2 = 0    
            
            for i in range(ts_len):
                
                # Get all energy flows:
                m_e = backend_model.carrier_prod['X1::grid_supply::electricity', ts[i+1]]
                v_e_pv = backend_model.carrier_prod['X1::solar_pv::electricity', ts[i+1]]
                v_e_wp = backend_model.carrier_prod['X1::wind_power::electricity', ts[i+1]]
                v_h_solar = backend_model.carrier_prod['X1::solar_thermal::heat', ts[i+1]]
                v_h_ob = backend_model.carrier_prod['X1::oil_boiler::heat', ts[i+1]]
                v_h_wb = backend_model.carrier_prod['X1::wood_boiler::heat', ts[i+1]]
                v_h_gb = backend_model.carrier_prod['X1::gas_boiler::heat', ts[i+1]]
                v_h_dh = backend_model.carrier_prod['X1::district_heating::heat', ts[i+1]]
                
                sum_kgCO2 += (m_e*c_co2_grid
                              + v_e_pv*c_co2_pv
                              + v_e_wp*c_co2_wp
                              + v_h_solar*c_co2_solar
                              + v_h_ob*c_co2_ob
                              + v_h_wb*c_co2_wb
                              + v_h_gb*c_co2_gb
                              + v_h_dh*c_co2_dh
                              )
                
            return sum_kgCO2 <= eps_n
            
        
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            epsilon_constraint_rule
            )
        
        #  - access variables through backend, e.g. backend_model.carrier_prod['X1::grid_supply::electricity']
        # Re-run model to implement custom constraints:
        new_model = model.backend.rerun()
        # see: https://calliope.readthedocs.io/en/stable/user/advanced_constraints.html#user-defined-custom-constraints
        
        opt_results_new = new_model.results
        
        print("\nRe-Run complete.\n")
        
        return opt_results_new, new_model

    def get_optimal_output_df(self,opt_results):
        """
        Write the results of the Calliope optimisation to a dataframe of the same
        format as df_scen.
        
        Parameters
        ----------
        opt_results : xarray
            Results from calliope optimisation.
                
        Returns
        -------
        df_scen_opt : panda dataframe
            Dataframe with resulting hourly values.
        dict_yr_scen_opt : dictionary
            Dictionary with reulting annual values.
        dict_total_costs : dictionary
            Dictionary with resulting total costs split by type (e.g. monetary,
            co2) and energy carrier (e.g. heat, electricity).
            (incl. levelised cost)
            
            
        """
        
        # ---------------------------------------------------------------------
        # Initialise dataframe (hourly values) and dict (annual values):
        
        df_scen_opt = pd.DataFrame()
        dict_yr_scen_opt = {}
        
        
        # ---------------------------------------------------------------------
        # Extract hourly values as numpy arrays:
        
        # !!! CHECK NEGATIVE / POSITIVE !!!
        # !!! HOW IS ADDITIONAL ELECTRICITY DEMAND HANDLED? !!!
        # !!! WHAT IF TECH IS DEACTIVATED?
       
        # =====================================================================
        # SUPERSEDED 28.5.24 (REMOVE IF NEW ROUTINE WORKS)
        # # -------------------
        # # Demand:
        # df_scen_opt['d_e'] = (
        #     -opt_results['carrier_con'].loc['X1::demand_electricity::electricity'].values
        #     -opt_results['carrier_con'].loc['X1::heat_pump::electricity'].values
        #     -opt_results['carrier_con'].loc['X1::electric_heater::electricity'].values
        #     )
        # df_scen_opt['d_e_hh'] = (
        #     -opt_results['carrier_con'].loc['X1::demand_electricity::electricity'].values
        #     )
        # df_scen_opt['d_e_h'] = (
        #     -opt_results['carrier_con'].loc['X1::heat_pump::electricity'].values
        #     -opt_results['carrier_con'].loc['X1::electric_heater::electricity'].values
        #     )
        # df_scen_opt['d_h'] = (
        #     -opt_results['carrier_con'].loc['X1::demand_heat::heat'].values
        #     )
        # =====================================================================
        
        # -------------------
        # Heat pump:
        if self.scen_techs['heat_pump']['deployment'] == True:
            df_scen_opt['v_h_hp'] =(
                opt_results['carrier_prod'].loc['X1::heat_pump_old::heat'].values
                + opt_results['carrier_prod'].loc['New_Techs::heat_pump_new::heat'].values
                )
            df_scen_opt['u_e_hp'] = (
                -opt_results['carrier_con'].loc['X1::heat_pump_old::electricity'].values
                -opt_results['carrier_con'].loc['New_Techs::heat_pump_new::electricity'].values
                )
            df_scen_opt['u_h_hp'] = dem_techs.HeatPump.get_u_h(
                v_h=df_scen_opt['v_h_hp'],
                cop=self.scen_techs['heat_pump']['cop']
                )
        else:
            df_scen_opt['v_h_hp'] = 0
            df_scen_opt['u_e_hp'] = 0
            df_scen_opt['u_h_hp'] = 0
            
        # Heat pump:
        if self.scen_techs['heat_pump']['deployment'] == True:
            df_scen_opt['v_h_hp'] =(
                opt_results['carrier_prod'].loc['X1::heat_pump_old::heat'].values
                + opt_results['carrier_prod'].loc['New_Techs::heat_pump_new::heat'].values
                )
            df_scen_opt['u_e_hp'] = (
                -opt_results['carrier_con'].loc['X1::heat_pump_old::electricity'].values
                -opt_results['carrier_con'].loc['New_Techs::heat_pump_new::electricity'].values
                )
            df_scen_opt['u_h_hp'] = dem_techs.HeatPump.get_u_h(
                v_h=df_scen_opt['v_h_hp'],
                cop=self.scen_techs['heat_pump']['cop']
                )
        else:
            df_scen_opt['v_h_hp'] = 0
            df_scen_opt['u_e_hp'] = 0
            df_scen_opt['u_h_hp'] = 0

        # -------------------
        # Electric heater:
        if self.scen_techs['electric_heater']['deployment'] == True:
            df_scen_opt['v_h_eh'] = opt_results['carrier_prod'].loc['X1::electric_heater_old::heat'].values
            df_scen_opt['u_e_eh'] = -opt_results['carrier_con'].loc['X1::electric_heater_old::electricity'].values
        else:
            df_scen_opt['v_h_eh'] = 0
            df_scen_opt['u_e_eh'] = 0
        
        # -------------------
        # Oil boiler:
        if self.scen_techs['oil_boiler']['deployment'] == True:
            df_scen_opt['u_oil_ob'] = (
                -opt_results['carrier_con'].loc['X1::oil_boiler_old::oil'].values
                -opt_results['carrier_con'].loc['New_Techs::oil_boiler_new::oil'].values
                )
            # df_scen_opt['u_oil_ob'] = dem_techs.OilBoiler.unit_conversion_nparray_kWh_to_kg(
            #     nparray_kWh=tmp_u_oil_ob,
            #     hv_oil_MJpkg=self.scen_techs['oil_boiler']['hv_oil_MJpkg']
            #     )
            df_scen_opt['v_h_ob'] = (
                opt_results['carrier_prod'].loc['X1::oil_boiler_old::heat'].values
                + opt_results['carrier_prod'].loc['New_Techs::oil_boiler_new::heat'].values
                )
        else:
            df_scen_opt['u_oil_ob'] = 0
            df_scen_opt['v_h_ob'] = 0
        
        # -------------------
        # Gas boiler:
        if self.scen_techs['gas_boiler']['deployment'] == True:
            df_scen_opt['u_gas_gb'] = (
                -opt_results['carrier_con'].loc['X1::gas_boiler_old::gas'].values
                -opt_results['carrier_con'].loc['New_Techs::gas_boiler_new::gas'].values
                )
            # df_scen_opt['u_gas_gb'] = dem_techs.GasBoiler.unit_conversion_nparray_kWh_to_kg(
            #     nparray_kWh=tmp_u_gas_gb,
            #     hv_gas_MJpkg=self.scen_techs['gas_boiler']['hv_gas_MJpkg']
            #     )
            df_scen_opt['v_h_gb'] = (
                opt_results['carrier_prod'].loc['X1::gas_boiler_old::heat'].values
                + opt_results['carrier_prod'].loc['New_Techs::gas_boiler_new::heat'].values
                )
        else:
            df_scen_opt['u_gas_gb'] = 0
            df_scen_opt['v_h_gb'] = 0
        
        # -------------------
        # Wood boiler:
        if self.scen_techs['wood_boiler']['deployment'] == True:
            df_scen_opt['u_wd_wb'] = (
                -opt_results['carrier_con'].loc['X1::wood_boiler_old::wood'].values
                -opt_results['carrier_con'].loc['New_Techs::wood_boiler_new::wood'].values
                )
            # df_scen_opt['u_wd_wb'] = 
            
            # dem_techs.WoodBoiler.unit_conversion_nparray_kWh_to_kg(
            #     nparray_kWh=tmp_u_wood_wb,
            #     hv_wood_MJpkg=self.scen_techs['wood_boiler']['hv_wood_MJpkg']
            #     )
            df_scen_opt['v_h_wb'] = (
                opt_results['carrier_prod'].loc['X1::wood_boiler_old::heat'].values
                + opt_results['carrier_prod'].loc['New_Techs::wood_boiler_new::heat'].values
                )
        else:
            df_scen_opt['u_wd_wb'] = 0
            df_scen_opt['v_h_wb'] = 0
        
        
        # -------------------
        # District heating:
        if self.scen_techs['district_heating']['deployment'] == True:
            df_scen_opt['v_h_dh'] = opt_results['carrier_prod'].loc['X1::district_heating::heat'].values
        else:
            df_scen_opt['v_h_dh'] = 0
        
        # -------------------
        # Solar thermal:
        if self.scen_techs['solar_thermal']['deployment'] == True:
            df_scen_opt['v_h_solar'] = (
                opt_results['carrier_prod'].loc['New_Techs::solar_thermal_new::heat'].values
                + opt_results['carrier_prod'].loc['Old_Solar_Thermal::solar_thermal_old::heat'].values
                )
        else:
            df_scen_opt['v_h_solar'] = 0
        
        # -------------------
        # Other (unknown) sources:
        df_scen_opt['v_h_other'] = 0 # !!! CURRENTLY LEAVE AS IS. MUST LATER BE HANDLED DIFFERENTLY !!!
        
        # -------------------
        # Solar PV:
        if self.scen_techs['solar_pv']['deployment'] == True:
            
            df_scen_opt['v_e_pv'] = (
                opt_results['carrier_prod'].loc['New_Techs::solar_pv_new::electricity'].values +
                opt_results['carrier_prod'].loc['Old_Solar_PV::solar_pv_old::electricity'].values
                )
            df_scen_opt['v_e_pv_cons'] = (
                df_scen_opt['v_e_pv']
                -opt_results['carrier_export'].loc['New_Techs::solar_pv_new::electricity'].values
                -opt_results['carrier_export'].loc['Old_Solar_PV::solar_pv_old::electricity'].values
                )
            df_scen_opt['v_e_pv_exp'] = (
                opt_results['carrier_export'].loc['New_Techs::solar_pv_new::electricity'].values + 
                opt_results['carrier_export'].loc['Old_Solar_PV::solar_pv_old::electricity'].values
                )
        else:
            df_scen_opt['v_e_pv'] = 0
            df_scen_opt['v_e_pv_cons'] = 0
            df_scen_opt['v_e_pv_exp'] = 0
        
        # Transfer potential:
        df_scen_opt['v_e_pv_pot'] = self.df_scen['v_e_pv_pot']
        
        # Update remaining potential:
        df_scen_opt['v_e_pv_pot_remain'] = dem_techs.SolarPV.get_v_e_pot_remain(
            v_e_pv=df_scen_opt['v_e_pv'],
            v_e_pv_pot=df_scen_opt['v_e_pv_pot'],
            v_h_solar=df_scen_opt['v_h_solar'],
            eta_pv=self.scen_techs['solar_pv']['eta_overall'],
            eta_thermal=self.scen_techs['solar_thermal']['eta_overall']
            )
        
        # -----------
        # Wind power:
        if self.scen_techs['wind_power']['deployment'] == True:
            # =================================================================
            # SUPERSEDED 29.5.24 b (REMOVE IF NEW ROUTINE IS WORKING)
            # ------------------------------------------------------
            # df_scen_opt['v_e_wp'] = (
            #     opt_results['carrier_prod'].loc['loc_wp_winter::wind_power::electricity'].values
            #     + opt_results['carrier_prod'].loc['loc_wp_annual::wind_power::electricity'].values
            #     )
            
            # df_scen_opt['v_e_wp_exp'] = (
            #     opt_results['carrier_export'].loc['loc_wp_winter::wind_power::electricity'].values
            #     + opt_results['carrier_export'].loc['loc_wp_annual::wind_power::electricity'].values
            #     )
            
            # df_scen_opt['v_e_wp_cons'] = (
            #     df_scen_opt['v_e_wp']
            #     - df_scen_opt['v_e_wp_exp']
            #     )
            # =================================================================
            
            df_scen_opt['v_e_wp'] = (
                opt_results['carrier_prod'].loc['loc_wp_winter::wind_power::wp_electricity'].values
                + opt_results['carrier_prod'].loc['loc_wp_annual::wind_power::wp_electricity'].values
                )
            
            df_scen_opt['v_e_wp_exp'] = (
                opt_results['carrier_export'].loc['loc_wp_winter::wind_power::wp_electricity'].values
                + opt_results['carrier_export'].loc['loc_wp_annual::wind_power::wp_electricity'].values
                )
            
            df_scen_opt['v_e_wp_cons'] = (
                df_scen_opt['v_e_wp']
                - df_scen_opt['v_e_wp_exp']
                )
            
            # =================================================================
            # SUPERSEDED 29.5.24 a (REMOVE IF NEW ROUTINE IS WORKING)
            # ------------------------------------------------------
            # df_scen_opt['v_e_wp'] = opt_results['carrier_prod'].loc['X1::wind_power::electricity'].values
            # df_scen_opt['v_e_wp_cons'] = (
            #     opt_results['carrier_prod'].loc['X1::wind_power::electricity'].values
            #     -opt_results['carrier_export'].loc['X1::wind_power::electricity'].values
            #     )
            # df_scen_opt['v_e_wp_exp'] = opt_results['carrier_export'].loc['X1::wind_power::electricity'].values
            # =================================================================
            
        else:
            df_scen_opt['v_e_wp'] = 0
            df_scen_opt['v_e_wp_cons'] = 0
            df_scen_opt['v_e_wp_exp'] = 0
        
        # Update generation potential based on selected profile type:
        # if opt_results['units'].loc['loc_wp_annual::wind_power_unit'].values == 1:
        #     df_scen_opt['v_e_wp_pot'] = self.df_scen['v_e_wp_pot_annual']
        #     df_scen_opt['v_e_wp_pot_kWhpkW'] =\
        #         self.df_scen['v_e_wp_pot_annual_kWhpkW']
            
        # elif opt_results['units'].loc['loc_wp_winter::wind_power_unit'].values == 1:
        #     df_scen_opt['v_e_wp_pot'] = self.df_scen['v_e_wp_pot_winter']
        #     df_scen_opt['v_e_wp_pot_kWhpkW'] =\
        #         self.df_scen['v_e_wp_pot_winter_kWhpkW']
        # else:
        
        # Total potential remains unchanged:
        df_scen_opt['v_e_wp_pot'] = self.df_scen['v_e_wp_pot']
  
        # Udpate remaining potential:
        df_scen_opt['v_e_wp_pot_remain'] = (df_scen_opt['v_e_wp_pot']
                                            - df_scen_opt['v_e_wp'])
        
        # Transfer 'annual' and 'winter' type potentials:
        df_scen_opt['v_e_wp_pot_annual'] = self.df_scen['v_e_wp_pot_annual']
        df_scen_opt['v_e_wp_pot_annual_kWhpkW'] =\
            self.df_scen['v_e_wp_pot_annual_kWhpkW']
        df_scen_opt['v_e_wp_pot_winter'] = self.df_scen['v_e_wp_pot_winter']
        df_scen_opt['v_e_wp_pot_winter_kWhpkW'] =\
            self.df_scen['v_e_wp_pot_winter_kWhpkW']
            
        #--------
        #Hydrothermal Gasification
        if self.scen_techs['hydrothermal_gasification']['deployment'] == True:
            
            df_scen_opt['u_wet_bm_hg'] = -opt_results['carrier_con'].loc['New_Techs::hydrothermal_gasification::wet_biomass'].values
            df_scen_opt['v_gas_hg'] = opt_results['carrier_prod'].loc['New_Techs::hydrothermal_gasification::gas'].values
        
        else:
            
            df_scen_opt['u_wet_bm_hg'] = 0
            df_scen_opt['v_gas_hg'] = 0
        
        #--------
        #Anaerobic Digesion Upgrade
        if self.scen_techs['anaerobic_digestion_upgrade']['deployment'] == True:
            
            df_scen_opt['u_wet_bm_agu'] = -opt_results['carrier_con'].loc['New_Techs::anaerobic_digestion_upgrade::wet_biomass'].values
            df_scen_opt['v_gas_agu'] = opt_results['carrier_prod'].loc['New_Techs::anaerobic_digestion_upgrade::gas'].values
        
        else:
            
            df_scen_opt['u_wet_bm_agu'] = 0
            df_scen_opt['v_gas_agu'] = 0
            
        #--------
        #Anaerobic Digestion Upgrade Hydrogen
        if self.scen_techs['anaerobic_digestion_upgrade_hydrogen']['deployment'] == True:
            
            df_scen_opt['u_wet_bm_aguh'] = -opt_results['carrier_con'].loc['New_Techs::anaerobic_digestion_upgrade_hydrogen::wet_biomass'].values
            df_scen_opt['u_e_aguh'] = -opt_results['carrier_con'].loc['New_Techs::anaerobic_digestion_upgrade_hydrogen::electricity'].values
            df_scen_opt['u_hyd_aguh'] = -opt_results['carrier_con'].loc['New_Techs::anaerobic_digestion_upgrade_hydrogen::hydrogen'].values
            df_scen_opt['v_gas_aguh'] = opt_results['carrier_prod'].loc['New_Techs::anaerobic_digestion_upgrade_hydrogen::gas'].values
            df_scen_opt['v_h_aguh'] = opt_results['carrier_prod'].loc['New_Techs::anaerobic_digestion_upgrade_hydrogen::heat'].values
            
        else:
            
            df_scen_opt['u_wet_bm_aguh'] = 0
            df_scen_opt['u_e_aguh'] = 0
            df_scen_opt['u_hyd_aguh'] = 0
            df_scen_opt['v_gas_aguh'] = 0
            df_scen_opt['v_h_aguh'] = 0
        
        #--------
        #Anaerobic Digestion CHP
        if self.scen_techs['anaerobic_digestion_chp']['deployment'] == True:
            
            df_scen_opt['u_wet_bm_aguc'] = -opt_results['carrier_con'].loc['New_Techs::anaerobic_digestion_chp::wet_biomass'].values
            df_scen_opt['v_e_aguc'] = opt_results['carrier_prod'].loc['New_Techs::anaerobic_digestion_chp::electricity'].values
            df_scen_opt['v_h_aguc'] = opt_results['carrier_prod'].loc['New_Techs::anaerobic_digestion_chp::heat'].values
            df_scen_opt['v_e_aguc_exp'] = opt_results['carrier_export'].loc['New_Techs::anaerobic_digestion_chp::electricity'].values
            
        else:
            
            df_scen_opt['u_wet_bm_aguc'] = 0
            df_scen_opt['v_e_aguc'] = 0
            df_scen_opt['v_h_aguc'] = 0
            df_scen_opt['v_e_aguc_exp'] = 0
            
        #--------
        #Wood Gasification Upgrade
        if self.scen_techs['wood_gasification_upgrade']['deployment'] == True:
            
            df_scen_opt['u_wd_wgu'] = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_upgrade::wood'].values
            df_scen_opt['u_e_wgu'] = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_upgrade::electricity'].values
            df_scen_opt['v_gas_wgu'] = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_upgrade::gas'].values
            df_scen_opt['v_h_wgu'] = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_upgrade::heat'].values
            
        else:
            
            df_scen_opt['u_wd_wgu'] = 0
            df_scen_opt['u_e_wgu'] = 0
            df_scen_opt['v_gas_wgu'] = 0
            df_scen_opt['v_h_wgu'] = 0
            
        #--------
        #Wood Gasification Upgrade Hydrogen
        if self.scen_techs['wood_gasification_upgrade_hydrogen']['deployment'] == True:
            
            df_scen_opt['u_wd_wguh'] = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_upgrade_hydrogen::wood'].values
            df_scen_opt['u_e_wguh'] = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_upgrade_hydrogen::electricity'].values
            df_scen_opt['u_hyd_wguh'] = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_upgrade_hydrogen::hydrogen'].values
            df_scen_opt['v_gas_wguh'] = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_upgrade_hydrogen::gas'].values
            df_scen_opt['v_h_wguh'] = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_upgrade_hydrogen::heat'].values
            
        else:
            
            df_scen_opt['u_wd_wguh'] = 0
            df_scen_opt['u_e_wguh'] = 0
            df_scen_opt['u_hyd_wguh'] = 0
            df_scen_opt['v_gas_wguh'] = 0
            df_scen_opt['v_h_wguh'] = 0
            
        #--------
        #Wood Gasification CHP
        if self.scen_techs['wood_gasification_chp']['deployment'] == True:
            
            df_scen_opt['u_wd_wguc'] = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_chp::wood'].values
            df_scen_opt['v_e_wguc'] = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_chp::electricity'].values
            df_scen_opt['v_h_wguc'] = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_chp::heat'].values
            df_scen_opt['v_e_wguc_exp'] = opt_results['carrier_export'].loc['New_Techs::wood_gasification_chp::electricity'].values
            
        else:
            
            df_scen_opt['u_wd_wguc'] = 0
            df_scen_opt['v_e_wguc'] = 0
            df_scen_opt['v_h_wguc'] = 0
            df_scen_opt['v_e_wguc_exp'] = 0
            
        #--------
        #Hydrogen Production
        if self.scen_techs['hydrogen_production']['deployment'] == True:
            
            df_scen_opt['u_e_hydp'] = -opt_results['carrier_con'].loc['New_Techs::hydrogen_production::electricity'].values
            df_scen_opt['v_hyd_hydp'] = opt_results['carrier_prod'].loc['New_Techs::hydrogen_production::hydrogen'].values
            
        else:
            
            df_scen_opt['u_e_hydp'] = 0
            df_scen_opt['v_hyd_hydp'] = 0
            
        #------------------
        # Biomass Totals
        df_scen_opt['v_e_bm'] = df_scen_opt['v_e_aguc'] + df_scen_opt['v_e_wguc']
        df_scen_opt['v_e_bm_exp'] = (
            df_scen_opt['v_e_aguc_exp']
            + df_scen_opt['v_e_wguc_exp']
            )
        
        df_scen_opt['v_e_bm_cons'] = (
            df_scen_opt['v_e_bm']
            - df_scen_opt['v_e_bm_exp']
            )
        
        df_scen_opt['v_h_bm'] = (
            df_scen_opt['v_h_aguh']
            + df_scen_opt['v_h_aguc']
            + df_scen_opt['v_h_wgu']
            + df_scen_opt['v_h_wguh']
            + df_scen_opt['v_h_wguc']
            )
        
        df_scen_opt['s_wet_bm'] = self.df_scen['s_wet_bm']
        df_scen_opt['s_wd'] = self.df_scen['s_wd']
        df_scen_opt['s_wet_bm_rem'] = (
            df_scen_opt['s_wet_bm']
            - opt_results['carrier_prod'].loc['Limited_Supplies::wet_biomass_supply::wet_biomass'].values
            )
        df_scen_opt['s_wd_rem'] = (
            df_scen_opt['s_wd']
            - opt_results['carrier_prod'].loc['Limited_Supplies::wood_supply::wood'].values
            )
        
        #------------------
        # Biomass Supply
        df_scen_opt['s_wet_bm'] = opt_results['carrier_prod'].loc['Limited_Supplies::wet_biomass_supply::wet_biomass'].values
        df_scen_opt['s_wd'] = opt_results['carrier_prod'].loc['Limited_Supplies::wood_supply::wood'].values
        
        # ------------------- 
        # Hydro Power (local):
        if self.scen_techs['hydro_power']['deployment'] == True:
            
            df_scen_opt['v_e_hydro'] = (
                opt_results['carrier_prod'].loc['X1::hydro_power::electricity'].values
                )
            df_scen_opt['v_e_hydro_cons'] = (
                df_scen_opt['v_e_hydro']
                -opt_results['carrier_export'].loc['X1::hydro_power::electricity'].values
                )
            df_scen_opt['v_e_hydro_exp'] = (
                opt_results['carrier_export'].loc['X1::hydro_power::electricity'].values
                )
        else:
            df_scen_opt['v_e_hydro'] = 0
            df_scen_opt['v_e_hydro_cons'] = 0
            df_scen_opt['v_e_hydro_exp'] = 0
        
        # Transfer potential:
        df_scen_opt['v_e_hydro_pot'] = self.df_scen['v_e_hydro_pot']
        
        # Update remaining potential:
        df_scen_opt['v_e_hydro_pot_remain'] = dem_techs.HydroPower.get_v_e_pot_remain(
            v_e_hydro=df_scen_opt['v_e_hydro'],
            v_e_hydro_pot=df_scen_opt['v_e_hydro_pot']
            )
        
        # -------------------
        # Demand:
        df_scen_opt['d_e'] = (
            -opt_results['carrier_con'].loc['X1::demand_electricity::electricity'].values
            + df_scen_opt['u_e_hp']
            + df_scen_opt['u_e_eh']
            + df_scen_opt['u_e_aguh']
            + df_scen_opt['u_e_wgu']
            + df_scen_opt['u_e_wguh']
            + df_scen_opt['u_e_hydp']
            # -opt_results['carrier_con'].loc['X1::heat_pump::electricity'].values
            # -opt_results['carrier_con'].loc['X1::electric_heater::electricity'].values
            )
        df_scen_opt['d_e_hh'] = (
            -opt_results['carrier_con'].loc['X1::demand_electricity::electricity'].values
            )
        df_scen_opt['d_e_h'] = (
            df_scen_opt['u_e_hp']
            + df_scen_opt['u_e_eh']
            # -opt_results['carrier_con'].loc['X1::heat_pump::electricity'].values
            # -opt_results['carrier_con'].loc['X1::electric_heater::electricity'].values
            )
        df_scen_opt['d_h'] = (
            -opt_results['carrier_con'].loc['X1::demand_heat::heat'].values
            )
        

        # -------------------
        # Electricity import:
        df_scen_opt['m_e'] =\
            opt_results['carrier_prod'].loc['X1::grid_supply::electricity'].values
            
        # Recalculate electricity mix:
        df_mix_new = dem_techs.GridSupply.update_electricity_mix(
            m_e_new=df_scen_opt['m_e'],
            m_e_old=self.df_scen['m_e'],
            m_e_ch_old=self.df_scen['m_e_ch'],
            m_e_ch_hydro_old=self.df_scen['m_e_ch_hydro'],
            m_e_ch_nuclear_old=self.df_scen['m_e_ch_nuclear'],
            m_e_ch_wind_old=self.df_scen['m_e_ch_wind'],
            m_e_ch_biomass_old=self.df_scen['m_e_ch_biomass'],
            m_e_ch_other_old=self.df_scen['m_e_ch_other']
            )
        
        # Assign recalculated sources:
        df_scen_opt['m_e_cbimport'] = df_mix_new['m_e_cbimport']
        df_scen_opt['m_e_ch'] = df_mix_new['m_e_ch']
        df_scen_opt['m_e_ch_hydro'] = df_mix_new['m_e_ch_hydro']
        df_scen_opt['m_e_ch_nuclear'] = df_mix_new['m_e_ch_nuclear']
        df_scen_opt['m_e_ch_wind'] = df_mix_new['m_e_ch_wind']
        df_scen_opt['m_e_ch_biomass'] = df_mix_new['m_e_ch_biomass']
        df_scen_opt['m_e_ch_other'] = df_mix_new['m_e_ch_other']
        
        # -------------------
        # Thermal energy storage:
        if self.scen_techs['tes']['deployment'] == True:
            df_scen_opt['v_h_tes'] = opt_results['carrier_prod'].loc['X1::tes::heat'].values
            df_scen_opt['u_h_tes'] = -opt_results['carrier_con'].loc['X1::tes::heat'].values
            df_scen_opt['q_h_tes'] = opt_results['storage'].loc['X1::tes'].values
        else:
            df_scen_opt['v_h_tes'] = 0
            df_scen_opt['u_h_tes'] = 0
            df_scen_opt['q_h_tes'] = 0
            
        # -------------------------------------------------------------------------
        # Extract costs:
            
        dict_total_costs = {}
        dict_total_costs['monetary'] = {}
        dict_total_costs['co2'] = {}
        
        tmp_tlc = opt_results['total_levelised_cost'] # array; total levelised costs
        
        dict_total_costs['monetary']['electricity_tlc'] =\
            float(tmp_tlc.loc['electricity'].loc['monetary'].values)
        dict_total_costs['monetary']['heat_tlc'] =\
            float(tmp_tlc.loc['heat'].loc['monetary'].values)
        dict_total_costs['monetary']['total'] =\
            float(opt_results['cost'].loc['monetary'].values.sum())
            
        dict_total_costs['co2']['electricity_tlc'] =\
            float(tmp_tlc.loc['electricity'].loc['emissions_co2'].values)
        dict_total_costs['co2']['heat_tlc'] =\
            float(tmp_tlc.loc['heat'].loc['emissions_co2'].values)
        dict_total_costs['co2']['total'] =\
            float(opt_results['cost'].loc['emissions_co2'].values.sum())
        
        
        return df_scen_opt, dict_total_costs
    
    def __build_input_dict(self):
        
        model_dict = self.__create_model_dict()
        tech_groups_dict = self.__create_tech_groups_dict()
        techs_dict = self.__create_techs_dict()
        loc_dict = self.__create_location_dict()
        links_dict = self.__create_links_dict()
        run_dict = self.__create_run_dict()
        
        # =====================================================================
        # TEMPORARY FOR TESTING: PRINT DICTS TO YAML FILES
        # ---------        
        # import dem_helper
        # dem_helper.save_calliope_dicts_to_yaml(
        #     "tmp_results_for_testing",
        #     model_dict,
        #     tech_groups_dict,
        #     techs_dict,
        #     loc_dict,
        #     links_dict,
        #     run_dict
        #     )       
        # =====================================================================
        
        
        input_dict = {
            'model':model_dict,
            'tech_groups':tech_groups_dict,
            'techs':techs_dict,
            'locations':loc_dict,
            'links':links_dict,
            'run':run_dict,
            }

        return input_dict
        
    def __create_model_dict(self):

        model_dict = {
            'name':self.com_name,
            'calliope_version':'0.6.8', # !!! How to handle the model version dynamically?
            'timeseries_data_path':'timeseries_data',
            # 'subset_time':['2050-02-01', '2050-02-15']
            }        

        return model_dict
    
    def __create_tech_groups_dict(self):
        
        tech_groups_dict = {}
        
        # tech_groups_dict = {
        #     'wind_power':{ # wind power (wp)
        #         'essentials':{
        #             'parent':'supply_plus',
        #             'carrier':'wp_electricity'
        #             }
        #         }
        #     }
        
        # if 'electric_heater' in self.tech_list:
        #     tech_groups_dict = dem_techs.ElectricHeater(
        #         self.scen_techs['electric_heater']['kW_max']
        #         ).create_tech_groups_dict(
        #             tech_groups_dict, 
        #             self.scen_techs['electric_heater'])
                    
        # if 'solar_thermal' in self.tech_list:
        #     tech_groups_dict = dem_techs.SolarThermal.create_tech_groups_dict(
        #         tech_groups_dict, 
        #         self.scen_techs['solar_thermal'])
            
        if 'solar_pv' in self.tech_list:
            tech_groups_dict = dem_techs.SolarPV.create_tech_groups_dict(
                tech_groups_dict, 
                self.scen_techs['solar_pv'])
            
        if 'wind_power' in self.tech_list:
            tech_groups_dict = dem_techs.WindPower.create_tech_groups_dict(
                tech_groups_dict,
                self.scen_techs['wind_power'])
            
        # if 'heat_pump' in self.tech_list:
        #     tech_groups_dict = dem_techs.HeatPump.create_tech_groups_dict(
        #         tech_groups_dict, 
        #         self.scen_techs['heat_pump'])
            
        # if 'oil_boiler' in self.tech_list:
        #     tech_groups_dict = dem_techs.OilBoiler.create_tech_groups_dict(
        #         tech_groups_dict, 
        #         self.scen_techs['oil_boiler'])
            
        # if 'gas_boiler' in self.tech_list:
        #     tech_groups_dict = dem_techs.GasBoiler.create_tech_groups_dict(
        #         tech_groups_dict, 
        #         self.scen_techs['gas_boiler'])
            
        # if 'wood_boiler' in self.tech_list:
        #     tech_groups_dict = dem_techs.WoodBoiler.create_tech_groups_dict(
        #         tech_groups_dict, 
        #         self.scen_techs['wood_boiler'])
            
            
        return tech_groups_dict

    def __create_techs_dict(self):
        # =====================================================================
        # Define colors:
        colors = {
            'demand_electricity':'#072486',
            'demand_heat':'#660507',
            'heat_pump':'#860720',
            'electric_heater':'#F27D52',
            'oil_boiler':'#8E2999',
            'oil_supply':'#8E2999',
            'gas_boiler':'#001A1A',
            'gas_supply':'#001A1A',
            'wood_boiler':'#8C3B0C',
            'wood_supply':'#8C3B0C',
            'district_heating':'#ff99bb',
            'solar_thermal':'#ff99bb', # TBC
            'solar_pv':'#F9D956',
            'hydro_power': '#0000FF',
            'wind_power': '#3333FF',
            'grid_supply':'#C5ABE3',
            'tes':'#EF008C',
            'power_line':'#6783E3',
            'heat_line': '#FF0000',
            'gas_line': '#808080',
            'wood_line': '#6e4500',
            'wet_biomass_line': '#024200'
            }
        
        techs_dict = {}
        
        # =====================================================================
        # Add demands:
        techs_dict['demand_electricity'] = {
            'essentials':{
                'name':'Electrical Demand',
                'color':colors['demand_electricity'],
                'parent':'demand',
                'carrier':'electricity'
                }
            }
        
        techs_dict['demand_heat'] = {
            'essentials':{
                'name':'Heat Demand',
                'color':colors['demand_heat'],
                'parent':'demand',
                'carrier':'consumer_heat'
                }
            }
        
        # =====================================================================
        #Add Supplies:
        
        techs_dict = dem_supply.create_supply_dict_wet_biomass(techs_dict)
        techs_dict = dem_supply.create_supply_dict_wood(techs_dict)
        techs_dict = dem_techs.OilBoiler.create_oil_supply(
            techs_dict, 
            self.scen_techs['oil_boiler'],
            color = colors['oil_supply']
            )
        techs_dict = dem_techs.GasBoiler.create_gas_supply(
            techs_dict, 
            color = colors['gas_supply'], 
            gas_cost = self.scen_techs['gas_boiler']['gas_price_CHFpkWh'])
        
        self.tech_list_central.append('oil_supply')
        self.tech_list_central.append('gas_supply')
        
        # =====================================================================
        # Add user-selected techologies:
        if 'heat_pump' in self.tech_list:
            
            techs_dict = dem_techs.HeatPump.create_techs_dict_clustering(
                techs_dict = techs_dict, 
                tech_dict = self.scen_techs['heat_pump'])
            
            
            self.tech_list_heat.append('heat_pump')
            
        if 'electric_heater' in self.tech_list:
            
            techs_dict = dem_techs.ElectricHeater.create_techs_dict_clustering(
                techs_dict = techs_dict, 
                tech_dict = self.scen_techs['electric_heater']
                )
            
            self.tech_list_heat.append('electric_heater')
            
        if 'oil_boiler' in self.tech_list:
            
            techs_dict = dem_techs.OilBoiler.create_techs_dict_clustering(
                techs_dict = techs_dict, 
                tech_dict = self.scen_techs['oil_boiler']
                )
            
            self.tech_list_heat.append('oil_boiler')
                
        if 'gas_boiler' in self.tech_list:
            
            techs_dict = dem_techs.GasBoiler.create_techs_dict_clustering(
                techs_dict = techs_dict, 
                tech_dict = self.scen_techs['gas_boiler']
                )
            
            self.tech_list_heat.append('gas_boiler')
            
        if 'wood_boiler' in self.tech_list:
            
            techs_dict = dem_techs.WoodBoiler.create_techs_dict_clustering(
                techs_dict = techs_dict, 
                tech_dict = self.scen_techs['wood_boiler']
                )
            
            self.tech_list_heat.append('wood_boiler')
            
        if 'solar_pv' in self.tech_list:
            
            techs_dict = dem_techs.SolarPV.create_techs_dict(techs_dict,
                                  header = 'solar_pv_old',
                                  name = 'Solar PV Old', 
                                  color = colors['solar_pv'], 
                                  resource = 'df=pv_resource_old:v_e_pv',
                                  energy_cap = self.df_scen[(0, 'v_e_pv')].max(),
                                  capex = 0
                                  )
            
            techs_dict = dem_techs.SolarPV.create_techs_dict(techs_dict,
                                  header = 'solar_pv_new',
                                  name = 'Solar PV New',
                                  color = colors['solar_pv'],
                                  resource = 'df=pv_resource_new:v_e_pv',
                                  energy_cap = 'inf',
                                  capex = self.scen_techs['solar_pv']['capex']
                                  )
            
            self.tech_list_central.append('solar_pv_old')
            self.tech_list_central.append('solar_pv_new')
            
        if 'district_heating' in self.tech_list:
            techs_dict = self.__techs_dict_add_district_heating(techs_dict, colors)
            
            self.tech_list_heat.append('district_heating')
            
        if 'wind_power' in self.tech_list:
            
            techs_dict = dem_techs.WindPower.create_techs_dict_unit(
                techs_dict,
                colors['wind_power']
                )
            
            techs_dict = dem_techs.WindPower.create_techs_dict(
                techs_dict = techs_dict,
                header = 'wind_power',
                name = 'Wind Power',
                color = colors['wind_power'],
                # energy_cap = ,
                capex = self.scen_techs['wind_power']['capex_CHFpkWp']
                )
            
            # self.tech_list_central.append('wind_power')
            
        if 'hydro_power' in self.tech_list:
            techs_dict = dem_techs.HydroPower.create_techs_dict(techs_dict,
                                  header = 'hydro_power',
                                  name = 'Hydro Power',
                                  color = colors['hydro_power'],
                                  resource = 'df=hydro_resource:v_e_hydro',
                                  energy_cap = self.df_scen[(0, 'v_e_hydro')].max(),
                                  capex = self.scen_techs['hydro_power']['capex']
                                  )
            
            self.tech_list_central.append('hydro_power')
            
        if 'grid_supply' in self.tech_list:
            techs_dict = self.__techs_dict_add_grid_supply(techs_dict, colors)
            
            self.tech_list_central.append('grid_supply')
            
        if 'tes' in self.tech_list:
            techs_dict = self.__techs_dict_add_tes(techs_dict, colors)
            
            self.tech_list_central.append('tes')
        
        if 'hydrothermal_gasification' in self.tech_list:
            techs_dict = dem_techs.HydrothermalGasification(self.scen_techs['hydrothermal_gasification']).generate_tech_dict(techs_dict)
            
            self.tech_list_central.append('hydrothermal_gasification')
        
        if 'anaerobic_digestion_upgrade' in self.tech_list:
            techs_dict = dem_techs.AnaerobicDigestionUpgrade(self.scen_techs['anaerobic_digestion_upgrade']).generate_tech_dict(techs_dict)
            
            self.tech_list_central.append('anaerobic_digestion_upgrade')
            
        if 'anaerobic_digestion_upgrade_hydrogen' in self.tech_list:
            techs_dict = dem_techs.AnaerobicDigestionUpgradeHydrogen(self.scen_techs['anaerobic_digestion_upgrade_hydrogen']).generate_tech_dict(techs_dict)
            
            self.tech_list_central.append('anaerobic_digestion_upgrade_hydrogen')
            
        if 'anaerobic_digestion_chp' in self.tech_list:
            techs_dict = dem_techs.AnaerobicDigestionCHP(self.scen_techs['anaerobic_digestion_chp']).generate_tech_dict(techs_dict)
            
            self.tech_list_central.append('anaerobic_digestion_chp')
        
        if 'wood_gasification_upgrade' in self.tech_list:
            techs_dict = dem_techs.WoodGasificationUpgrade(self.scen_techs['wood_gasification_upgrade']).generate_tech_dict(techs_dict)
            
            self.tech_list_central.append('wood_gasification_upgrade')
            
        if 'wood_gasification_upgrade_hydrogen' in self.tech_list:
            techs_dict = dem_techs.WoodGasificationUpgradeHydrogen(self.scen_techs['wood_gasification_upgrade_hydrogen']).generate_tech_dict(techs_dict)
            
            self.tech_list_central.append('wood_gasification_upgrade_hydrogen')
            
        if 'wood_gasification_chp' in self.tech_list:
            techs_dict = dem_techs.WoodGasificationCHP(self.scen_techs['wood_gasification_chp']).generate_tech_dict(techs_dict)
            
            self.tech_list_central.append('wood_gasification_chp')
            
        if 'hydrogen_production' in self.tech_list:
            techs_dict = dem_techs.HydrogenProduction(self.scen_techs['hydrogen_production']).generate_tech_dict(techs_dict)
            
            self.tech_list_central.append('hydrogen_production')
            
        # =====================================================================
        # Add Heat-Converters:
        
        techs_dict['heat_converter'] = {
            'essentials':{
                'name':'Heat Conversion Unit',
                'parent':'conversion',
                'carrier_in':'heat',
                'carrier_out':'consumer_heat'
                },
            'constraints':{
                'units_max': 1,
                'units_max_systemwide': self.com_file['cluster_number'].max(),
                'energy_cap_per_unit': 'inf',
                'energy_eff': 1.0,
                'lifetime': 100.0
                },
            'costs':{
                'monetary':{
                    'interest_rate':0.0,
                    'om_con':0.0,
                    'energy_cap':0.0,
                    'purchase':0.0
                    },
                'emissions_co2':{
                    'om_prod':0.0
                    }
                }
            }
        
        # =====================================================================
        # Add connections (i.e. transmission lines):
        techs_dict = self.__techs_dict_add_power_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_heat_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_gas_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_wood_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_oil_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_wet_biomass_line(techs_dict, colors)
            
        return techs_dict
        
    def __create_location_dict(self):
        
        clusters = np.sort(self.df_scen.columns.get_level_values(0).unique())
        
        loc_dict = {}
        
        for cluster in clusters:
            if cluster != 0:
                arg = self.com_file['cluster_number'] == cluster
                
                lat = self.com_file.loc[arg, 'GKODE'].mean()
                lon = self.com_file.loc[arg, 'GKODN'].mean()
                
                cluster_scen = self.df_scen[cluster]
                
                loc_dict['cluster_' + str(cluster)] = {
                    'techs':{
                        'demand_heat':{}
                        },
                    'coordinates':{
                        'lat': lat,
                        'lon': lon
                        }
                    }
                
                loc_dict['cluster_' + str(cluster)]['techs']['demand_heat']['constraints.resource'] =\
                    'df=demand_heat:'+str(cluster)
                
                if cluster_scen['v_h_dh'].sum() > 0:
                    print(cluster)
                    
                    loc_dict['cluster_' + str(cluster) + '_dh'] = {
                        'techs':{},
                        'coordinates':{
                            'lat': lat - 1,
                            'lon': lon
                            }
                        }
                    loc_dict['cluster_' + str(cluster) + '_dh']['techs']['district_heating'] = {
                        
                        }
                    loc_dict['cluster_' + str(cluster) + '_dh']['techs']['district_heating']['constraints.energy_cap_max'] =\
                        cluster_scen['v_h_dh'].max()
                    loc_dict['cluster_' + str(cluster) + '_dh']['techs']['district_heating']['costs'] ={
                        'monetary':{
                            'energy_cap': 0
                            }
                        }
                        
                    loc_dict['cluster_' + str(cluster) + '_dh']['techs']['heat_converter'] = None
                        
                else:
                    
                    loc_dict['cluster_' + str(cluster) + '_old_heating'] = {
                        'techs':{},
                        'coordinates':{
                            'lat': lat + 1,
                            'lon': lon
                            }
                        }
                    heating_techs = [
                        'district_heating',
                        'electric_heater',
                        'oil_boiler',
                        'gas_boiler',
                        'wood_boiler',
                        ]
                    heating_columns = [
                        'v_h_dh',
                        'v_h_eh',
                        'v_h_ob',
                        'v_h_gb',
                        'v_h_wb'
                        ]
                    for heating_tech in zip(heating_techs, heating_columns):
                        if cluster_scen[heating_tech[1]].max() > 0:
                            loc_dict['cluster_' + str(cluster) + '_old_heating']['techs'][heating_tech[0]] = {}
                            loc_dict['cluster_' + str(cluster) + '_old_heating']['techs'][heating_tech[0]]['constraints.energy_cap_max'] =\
                                cluster_scen[heating_tech[1]].max()
                    loc_dict['cluster_' + str(cluster) + '_old_heating']['techs']['heat_converter'] = None
                    
                    loc_dict['cluster_' + str(cluster) + '_dh'] = {
                        'techs':{},
                        'coordinates':{
                            'lat': lat - 1,
                            'lon': lon
                            }
                        }
                    loc_dict['cluster_' + str(cluster) + '_dh']['techs']['district_heating'] = {}
                    loc_dict['cluster_' + str(cluster) + '_dh']['techs']['district_heating']['constraints.energy_cap_max'] =\
                        cluster_scen['d_h'].max()
                    loc_dict['cluster_' + str(cluster) + '_dh']['techs']['heat_converter'] = None
                    
                    loc_dict['cluster_' + str(cluster) + '_heat_pump'] = {
                        'techs':{},
                        'coordinates':{
                            'lat': lat,
                            'lon': lon + 1
                            }
                        }
                    loc_dict['cluster_' + str(cluster) + '_heat_pump']['techs']['heat_pump'] = {}
                    loc_dict['cluster_' + str(cluster) + '_heat_pump']['techs']['heat_converter'] = None
            
            else:
                
                lat = self.com_file.loc[:, 'GKODE'].mean()
                lon = self.com_file.loc[:, 'GKODN'].mean()
                
                loc_dict['central_cluster'] = {
                    'techs':{
                        'demand_electricity':{},
                        'wet_biomass_supply':{},
                        'wood_supply':{}
                        },
                    'available_area': 2,
                    'coordinates':{
                        'lat': lat,
                        'lon': lon
                        }
                    }
                
                loc_dict['central_cluster']['techs']['demand_electricity']['constraints.resource'] =\
                    'df=demand_power:d_e_hh'
                loc_dict['central_cluster']['techs']['wet_biomass_supply']['constraints.resource'] =\
                    'df=wet_biomass_resource:s_wet_bm'
                loc_dict['central_cluster']['techs']['wood_supply']['constraints.resource'] =\
                    'df=wood_resource:s_wd'
                
                for tech in self.tech_list_central:
                    loc_dict['central_cluster']['techs'][tech] = {}
                
                
                loc_dict['central_cluster']['techs']['solar_pv_old']['constraints.resource_area_equals'] =\
                    1
                    
                if 'wind_power' in self.tech_list:
                    
                    # -----------------------------------------------------------------
                    # Location for wind power with profile of type 'winter':
                    # Check which max. cap. value is smaller - (model input vs max resource potential):
                    tmp_cap_max_input = self.scen_techs['wind_power']['kWp_max']
                    tmp_cap_max_resource = (
                        self.df_scen[(0, 'v_e_wp_pot_winter')]/self.df_scen[(0, 'v_e_wp_pot_winter_kWhpkW')]
                        ).mean()
                    cap_max_winter = min(tmp_cap_max_input, tmp_cap_max_resource)
                    
                    # Create dict:
                    loc_dict['loc_wp_winter'] = {
                        'techs':{
                            'wind_power':{}
                            },
                        'coordinates':{}
                        }
                    # Add resource:
                    loc_dict['loc_wp_winter']['techs']['wind_power']['constraints.resource'] =\
                        'df=wp_resource_winter:v_e_wp'
                    # Add max. capacity:
                    loc_dict['loc_wp_winter']['techs']['wind_power']['constraints.energy_cap_max'] =\
                        cap_max_winter
                    # Update coordinates:
                    loc_dict['loc_wp_winter']['coordinates']['lat'] = lat + 2 # !!! Add here actual coordinates
                    loc_dict['loc_wp_winter']['coordinates']['lon'] = lon + 2
                    # Add wind power conversion unit:
                    loc_dict['loc_wp_winter']['techs']['wind_power_unit'] = {}
                    loc_dict['loc_wp_winter']['techs']['wind_power_unit']['constraints.energy_cap_per_unit'] =\
                        cap_max_winter
                    
                    # -----------------------------------------------------------------
                    # Location for wind power with profile of type 'annual':
                    # Check which max. cap. value is smaller - (model input vs max resource potential):
                    tmp_cap_max_input = self.scen_techs['wind_power']['kWp_max']
                    tmp_cap_max_resource = (
                        self.df_scen[(0, 'v_e_wp_pot_annual')]/self.df_scen[(0, 'v_e_wp_pot_annual_kWhpkW')]
                        ).mean()
                    cap_max_annual = min(tmp_cap_max_input, tmp_cap_max_resource)
                    
                    # Create dict:
                    loc_dict['loc_wp_annual'] = {
                        'techs':{
                            'wind_power':{}
                            },
                        'coordinates':{}
                        }
                    # Add resource:
                    loc_dict['loc_wp_annual']['techs']['wind_power']['constraints.resource'] =\
                        'df=wp_resource_annual:v_e_wp'
                    # Add max. capacity:
                    loc_dict['loc_wp_annual']['techs']['wind_power']['constraints.energy_cap_max'] =\
                        cap_max_annual
                    # Update coordinates:
                    loc_dict['loc_wp_annual']['coordinates']['lat'] = lat + 3 # !!! Add here actual coordinates
                    loc_dict['loc_wp_annual']['coordinates']['lon'] = lon + 3
                    # Add wind power conversion unit:
                    loc_dict['loc_wp_annual']['techs']['wind_power_unit'] = {}
                    loc_dict['loc_wp_annual']['techs']['wind_power_unit']['constraints.energy_cap_per_unit'] =\
                        cap_max_annual
        
        return loc_dict
    
    def __create_links_dict(self):
        
        vertices, vertex_lengths = dem_clustering.get_cluster_vertices(self.com_file)
        vertices = vertices + 1
        # print(vertices, vertex_lengths)
        # raise(Exception('TEST'))
        
        # Initialise dict:
        links_dict = {}
        links_dict['central_cluster, loc_wp_winter'] = {
            'techs':{
                'power_line':{
                    'constraints':{
                        'energy_cap_equals':1e12
                        }
                    }
                }
            }
        
        links_dict['central_cluster, loc_wp_annual'] = {
            'techs':{
                'power_line':{
                    'constraints':{
                        'energy_cap_equals':1e12
                        }
                    }
                }
            }
        
        for vertex in vertices:
            dh_1 = self.df_scen[(vertex[0], 'v_h_dh')].sum() > 0
            dh_2 = self.df_scen[(vertex[1], 'v_h_dh')].sum() > 0
            
            if dh_1 & dh_2:
                loc_dh_1 = 'cluster_' + str(vertex[0]) + '_dh'
                loc_dh_2 = 'cluster_' + str(vertex[1]) + '_dh'
                
                links_dict[loc_dh_1 + ',' + loc_dh_2] = {
                    'techs':{
                        'heat_line': None
                        }
                    }
            else:
                loc_dh_1 = 'cluster_' + str(vertex[0]) + '_dh'
                loc_dh_2 = 'cluster_' + str(vertex[1]) + '_dh'
                
                links_dict[loc_dh_1 + ',' + loc_dh_2] = {
                    'techs':{
                        'heat_line':{
                            'costs':{
                                'monetary':{
                                    'purchase_per_distance': 1000
                                    },
                                'emissions_co2':{
                                    'depreciation_rate': 0
                                    }
                                }
                            }
                        }
                    }
        for cluster in np.sort(self.com_file['cluster_number'].unique()):
            dh = self.df_scen[(cluster, 'v_h_dh')].sum() > 0
            
            if not(dh):
            
                links_dict['central_cluster,cluster_' + str(cluster) + '_heat_pump'] = {
                    'techs':{
                        'power_line':{
                            'constraints':{
                                'energy_cap_equals':1e12
                                }
                            }
                        }
                    }
                links_dict['central_cluster,cluster_' + str(cluster) + '_old_heating'] = {
                    'techs':{
                        'gas_line':None,
                        'wood_line':None,
                        'oil_line':None
                        }
                    }
        
        
            
        
        
        return links_dict
    
    def __create_run_dict(self):
        
        run_dict = {
            'mode':'plan',
            'solver':self.scen_techs['optimisation']['solver'],
            'ensure_feasibility':'true',
            'bigM':1000000,
            'objective_options':{
                'cost_class': {
                    'monetary':self.scen_techs['optimisation']['objective_monetary'],
                    'emissions_co2':self.scen_techs['optimisation']['objective_co2']
                    }
                }
            }
        
        return run_dict
        
    # def __techs_dict_add_heat_pump(self, techs_dict, colors):
        
    #     if self.scen_techs['heat_pump']['deployment'] == True:
    #         tmp_cap_max = self.scen_techs['heat_pump']['kW_th_max']
    #     else:
    #         tmp_cap_max = 0
            
    #     techs_dict['heat_pump'] = {
    #         'essentials':{
    #             'name':'Heat Pump',
    #             'color':colors['heat_pump'],
    #             'parent':'conversion_plus',
    #             'carrier_in':'electricity',
    #             'carrier_out':'heat',
    #             'primary_carrier_out':'heat'
    #             },
    #         'constraints':{
    #             'energy_cap_max':tmp_cap_max,
    #             'energy_eff':1,
    #             'carrier_ratios':{'carrier_out':{
    #                 'heat':self.scen_techs['heat_pump']['cop']
    #                                             }
    #                              },
    #             'lifetime':self.scen_techs['heat_pump']['lifetime']
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'om_con':0.0, # this is reflected in the cost of the electricity
    #                 'interest_rate':self.scen_techs['heat_pump']['interest_rate']
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':self.scen_techs['heat_pump']['co2_intensity']
    #                 }
    #             } 
    #         }
        
    #     return techs_dict
        
    # def __techs_dict_add_electric_heater(self, techs_dict, colors):
        
    #     if self.scen_techs['electric_heater']['deployment'] == True:
    #         tmp_cap_max = self.scen_techs['electric_heater']['kW_max']
    #     else:
    #         tmp_cap_max = 0
            
    #     techs_dict['electric_heater'] = {
    #         'essentials':{
    #             'name':'Electric Heater',
    #             'color': colors['electric_heater'],
    #             'parent':'conversion',
    #             'carrier_in':'electricity',
    #             'carrier_out':'heat'
    #                                              },
    #         'constraints':{
    #             'energy_cap_max':tmp_cap_max,
    #             'energy_eff':1,
    #             'lifetime':self.scen_techs['electric_heater']['lifetime']
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'om_con':0.0, # reflected in the cost of electricity
    #                 'interest_rate':self.scen_techs['electric_heater']['interest_rate']
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':self.scen_techs['electric_heater']['co2_intensity']
    #                 }
    #             }
    #         }
        
    #     return techs_dict
        
    # def __techs_dict_add_oil_boiler(self, techs_dict, colors):
        
    #     if self.scen_techs['oil_boiler']['deployment'] == True:
    #         tmp_cap_max = self.scen_techs['oil_boiler']['kW_th_max']
    #     else:
    #         tmp_cap_max = 0
            
    #     # Convert oil price:
    #     p_oil = dem_techs.OilBoiler.convert_price_CHFpl_to_CHFpkWh(
    #         price_CHFpl=self.scen_techs['oil_boiler']['oil_price_CHFpl'],
    #         hv_oil_MJpkg=self.scen_techs['oil_boiler']['hv_oil_MJpkg']
    #         ) # [CHF/kWh]
        
    #     techs_dict['oil_boiler'] = {
    #         'essentials':{
    #             'name':'Oil Boiler',
    #             'color':colors['oil_boiler'],
    #             'parent':'conversion',
    #             'carrier_in':'oil',
    #             'carrier_out':'heat',
    #             },
    #         'constraints':{
    #             'energy_cap_max':tmp_cap_max,
    #             'energy_eff':self.scen_techs['oil_boiler']['eta'],
    #             'lifetime':self.scen_techs['oil_boiler']['lifetime']
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'om_con':0.0, # costs are reflected in oil_supply
    #                 'interest_rate':self.scen_techs['oil_boiler']['interest_rate']
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':self.scen_techs['oil_boiler']['co2_intensity']
    #                 }
    #             }
    #         }
    #     # Generate oil supply:
    #     techs_dict['oil_supply'] = {
    #         'essentials':{
    #             'name':'Oil Supply',
    #             'color':colors['oil_supply'],
    #             'parent':'supply',
    #             'carrier':'oil',
    #             },
    #         'constraints':{
    #             'resource':'inf',
    #             'energy_cap_max':tmp_cap_max, # ensures that supply is always large enough
    #             'lifetime':self.scen_techs['oil_boiler']['lifetime']
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'om_con':p_oil,
    #                 'interest_rate':0.0
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':0.0 # this is reflected in the emissions of oil_boiler
    #                 }
    #             }
    #         }
    #     self.tech_list.append('oil_supply')
        
    #     return techs_dict
        
    # def __techs_dict_add_gas_boiler(self, techs_dict, colors):
        
    #     if self.scen_techs['gas_boiler']['deployment'] == True:
    #         tmp_cap_max = self.scen_techs['gas_boiler']['kW_th_max']
    #     else:
    #         tmp_cap_max = 0
            
    #     techs_dict['gas_boiler'] = {
    #         'essentials':{
    #             'name':'Gas Boiler',
    #             'color':colors['gas_boiler'],
    #             'parent':'conversion',
    #             'carrier_in':'gas',
    #             'carrier_out':'heat',
    #             },
    #         'constraints':{
    #             'energy_cap_max':tmp_cap_max,
    #             'energy_eff':self.scen_techs['gas_boiler']['eta'],
    #             'lifetime':self.scen_techs['gas_boiler']['lifetime']},
    #         'costs':{
    #             'monetary':{
    #                 'om_con':0.0,
    #                 'interest_rate':self.scen_techs['gas_boiler']['interest_rate']
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':self.scen_techs['gas_boiler']['co2_intensity']
    #                 }
    #             }
    #         }
    #     # Generate gas supply:
    #     techs_dict['gas_supply'] = {
    #         'essentials':{
    #             'name':'Gas Supply',
    #             'color':colors['gas_supply'],
    #             'parent':'supply',
    #             'carrier':'gas',
    #             },
    #         'constraints':{
    #             'resource':'inf',
    #             'energy_cap_max':tmp_cap_max, # ensures that supply is always large enough
    #             'lifetime':self.scen_techs['gas_boiler']['lifetime']
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'om_con':self.scen_techs['gas_boiler']['gas_price_CHFpkWh'], # [CHF/kWh]
    #                 'interest_rate':0.0
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':0.0 # this is reflected in the emissions of gas_boiler
    #                 }
    #             }
    #         }
    #     self.tech_list.append('gas_supply')
        
    #     return techs_dict
        
    # def __techs_dict_add_wood_boiler(self, techs_dict, colors):
        
    #     if self.scen_techs['wood_boiler']['deployment'] == True:
    #         tmp_cap_max = self.scen_techs['wood_boiler']['kW_th_max']
    #     else:
    #         tmp_cap_max = 0
            
    #     p_wood = dem_techs.WoodBoiler.convert_price_CHFpkg_to_CHFpkWh(
    #         price_CHFpkg=self.scen_techs['wood_boiler']['wood_price_CHFpkg'],
    #         hv_wood_MJpkg=self.scen_techs['wood_boiler']['hv_wood_MJpkg']
    #         )
        
    #     techs_dict['wood_boiler'] = {
    #         'essentials':{
    #             'name':'Wood Boiler',
    #             'color':colors['wood_boiler'],
    #             'parent':'conversion',
    #             'carrier_in':'wood',
    #             'carrier_out':'heat',
    #             },
    #         'constraints':{
    #             'energy_cap_max':tmp_cap_max,
    #             'energy_eff':self.scen_techs['wood_boiler']['eta'],
    #             'lifetime':self.scen_techs['wood_boiler']['lifetime']},
    #         'costs':{
    #             'monetary':{
    #                 'om_con':0.0, # cost are reflected in wood_supply
    #                 'interest_rate':self.scen_techs['wood_boiler']['interest_rate']
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':self.scen_techs['wood_boiler']['co2_intensity']
    #                 }
    #             }
    #         }
        
    #     return techs_dict
        
    def __techs_dict_add_district_heating(self, techs_dict, colors):
        
        if self.scen_techs['district_heating']['deployment'] == True:
            # !!! To be changed to supply? or conversion_plus?
            tmp_cap_max = self.scen_techs['district_heating']['kW_th_max']
        else:
            tmp_cap_max = 0
            
        techs_dict['district_heating'] = {
            'essentials':{
                'name':'District Heating',
                'color':colors['district_heating'],
                'parent':'conversion',
                'carrier_in': 'dh_heat',
                'carrier_out':'heat',
                },
            'constraints':{
                'energy_eff':1,
                'lifetime':self.scen_techs['district_heating']['lifetime']
                },
            'costs':{
                'monetary':{
                    'om_con':self.scen_techs['district_heating']['tariff_CHFpkWh'],
                    'interest_rate':self.scen_techs['district_heating']['interest_rate']
                    },
                'emissions_co2':{
                    'om_prod':self.scen_techs['district_heating']['co2_intensity']
                    }
                }
            }
        
        return techs_dict
        
    # def __techs_dict_add_solar_thermal(self, techs_dict, colors):
        
    #     if self.scen_techs['solar_thermal']['deployment'] == True:
    #         tmp_cap_max = self.scen_techs['solar_thermal']['kW_th_max']
    #     else:
    #         tmp_cap_max = 0
            
    #     techs_dict['solar_thermal'] = {
    #         'essentials':{
    #             'name':'Solar Thermal',
    #             'color':colors['solar_thermal'],
    #             'parent':'supply_heat_plus',
    #             },
    #         'constraints':{
    #             'resource':'df=solar_th_resource:v_h_solar_th',
    #             'resource_unit': 'energy_per_area', # 'energy',
    #             'parasitic_eff': 1.0, # efficiency is already accounted for in the resource dataseries
    #             'energy_cap_max': tmp_cap_max, # [kWp]
    #             'resource_area_min':0,
    #             'resource_area_max':self.f_area_potential,
    #             'force_resource': False,
    #             'lifetime': self.scen_techs['solar_thermal']['lifetime']
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'interest_rate':self.scen_techs['solar_thermal']['interest_rate'],
    #                 'om_con':0.0
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':self.scen_techs['solar_thermal']['co2_intensity']
    #                 }
    #             }
    #         }
        
    #     return techs_dict
        
    # def __techs_dict_add_solar_pv(self, techs_dict, colors):
        
    #     if self.scen_techs['solar_pv']['deployment'] == True:
    #         tmp_cap_max = self.scen_techs['solar_pv']['kWp_max']
    #     else:
    #         tmp_cap_max = 0
            
    #     techs_dict['solar_pv'] = {
    #         'essentials':{
    #             'name':'Solar PV',
    #             'color':colors['solar_pv'],
    #             'parent':'supply_power_plus'
    #             },
    #         'constraints':{
    #             'export_carrier': 'electricity',
    #             'resource':'df=pv_resource:v_e_pv',
    #             'resource_unit': 'energy_per_area', # 'energy',
    #             'parasitic_eff': 1.0, # efficiency is already accounted for in the resource dataseries
    #             'energy_cap_max': tmp_cap_max, # kWp
    #             'resource_area_min':self.f_area_installed,
    #             'resource_area_max':1,
    #             'force_resource': True,
    #             'lifetime': self.scen_techs['solar_pv']['lifetime']
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'interest_rate':self.scen_techs['solar_pv']['interest_rate'],
    #                 'om_con':0.0,
    #                 'energy_cap':self.scen_techs['wind_power']['capex_CHFpkWp']
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':self.scen_techs['solar_pv']['co2_intensity']
    #                 }
    #             }
    #         }
        
    #     return techs_dict
    
    # def __techs_dict_add_wind_power(self, techs_dict, colors):
        
    #     # =====================================================================
    #     # SUPERSEDED 29.5.24 (REMOVE IF NEW ROUTINE WORKS)
    #     # ------------------------------------------------
    #     # if self.scen_techs['wind_power']['deployment'] == True:
    #     #     # Check which max. cap. value is smaller - (model input vs max resource potential):
    #     #     tmp_cap_max_input = self.scen_techs['wind_power']['kWp_max']
    #     #     tmp_cap_max_resource = (
    #     #         self.df_scen['v_e_wp_pot']/self.df_scen['v_e_wp_pot_kWhpkW']
    #     #         ).mean()
    #     #     tmp_cap_max = min(tmp_cap_max_input, tmp_cap_max_resource)
    #     # 
    #     # else:
    #     #     tmp_cap_max = 0
    #     # =====================================================================
            
    #     # Conversion unit for integer decision (virtual tech):
    #     techs_dict['wind_power_unit'] = {
    #         'essentials':{
    #             'name':'Wind Power Unit',
    #             'color':colors['wind_power'],
    #             'parent':'conversion',
    #             'carrier_in':'wp_electricity',
    #             'carrier_out':'electricity'
    #             },
    #         'constraints':{
    #             'units_max': 1,
    #             'units_max_systemwide': 2,
    #             # 'energy_cap_per_unit': tmp_cap_max, # was added in loc_dict()
    #             'energy_eff': 1.0,
    #             'lifetime': self.scen_techs['wind_power']['lifetime']
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'interest_rate':0.0,
    #                 'om_con':0.0,
    #                 'energy_cap':0.0,
    #                 'purchase':0.0
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':0.0
    #                 }
    #             }
    #         }
        
    #     # Wind power tech:
    #     techs_dict['wind_power'] = {
    #         'essentials':{
    #             'name':'Wind Power',
    #             'color':colors['wind_power'],
    #             'parent':'wind_power'
    #             },
    #         'constraints':{
    #             'export_carrier': 'wp_electricity',
    #             'resource_unit':'energy_per_cap',  # [kWh/kW]
    #             # 'energy_cap_max': tmp_cap_max, # kWp # was added in loc_dict
    #             'force_resource': True,
    #             'lifetime': self.scen_techs['wind_power']['lifetime']
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'interest_rate':self.scen_techs['wind_power']['interest_rate'],
    #                 'om_con':0.0,
    #                 'energy_cap':self.scen_techs['wind_power']['capex_CHFpkWp'],
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':self.scen_techs['wind_power']['co2_intensity']
    #                 }
    #             }
    #         }
        
    #     # =====================================================================
    #     # SUPERSEDED 29.5.24 (REMOVE IF NEW ROUTINE WORKS)
    #     # ------------------------------------------------
    #     # techs_dict['wind_power'] = {
    #     #     'essentials':{
    #     #         'name':'Wind Power',
    #     #         'color':colors['wind_power'],
    #     #         'parent':'supply_power_plus'
    #     #         },
    #     #     'constraints':{
    #     #         'units_max': 1,
    #     #         'units_max_systemwide': 1,
    #     #         'export_carrier': 'electricity',
    #     #         # 'resource':'df=wp_resource:v_e_wp', # this is added at the loc_dict
    #     #         'resource_unit':'energy_per_cap',  # [kWh/kW]
    #     #         # 'energy_cap_per_unit': tmp_cap_max, # !!! TEMPORARY FOR TESTING
    #     #         'energy_cap_max': tmp_cap_max, # kWp
    #     #         'force_resource': True,
    #     #         # 'resource_min_use':1,
    #     #         'lifetime': self.scen_techs['wind_power']['lifetime']
    #     #         },
    #     #     'costs':{
    #     #         'monetary':{
    #     #             'interest_rate':self.scen_techs['wind_power']['interest_rate'],
    #     #             'om_con':0.0,
    #     #             'energy_cap':self.scen_techs['wind_power']['capex_CHFpkWp'],
    #     #             'purchase':0.0
    #     #             },
    #     #         'emissions_co2':{
    #     #             'om_prod':self.scen_techs['wind_power']['co2_intensity']
    #     #             }
    #     #         }
    #     #     }
    #     # =====================================================================
        
    #     return techs_dict
    
    # def __techs_dict_add_wind_power_curr_inst(self, techs_dict, colors):
    #     """
    #     Create separate technology for currently installed wind power.
    #     This generation is forced, but has no capex.
    #     """
        
        
        
    #     ...
        
    def __techs_dict_add_grid_supply(self, techs_dict, colors):
        
        if self.scen_techs['grid_supply']['deployment'] == True:
            tmp_cap_max = self.scen_techs['grid_supply']['kW_max']
        else:
            tmp_cap_max = 0
            
        techs_dict['grid_supply'] = {
            'essentials':{
                'name':'Grid Supply',
                'color':colors['grid_supply'],
                'parent':'supply',
                'carrier':'electricity',
                },
            'constraints':{
                'resource':'inf',
                'energy_cap_max':tmp_cap_max,
                'lifetime':self.scen_techs['grid_supply']['lifetime']
                },
            'costs':{
                'monetary':{
                    'om_con':self.scen_techs['grid_supply']['tariff_CHFpkWh'], # [CHF/kWh]
                    'interest_rate':self.scen_techs['grid_supply']['interest_rate']
                    },
                'emissions_co2':{
                    'om_prod':self.scen_techs['grid_supply']['co2_intensity']
                    }
                }
            }
        
        return techs_dict
    
    def __techs_dict_add_tes(self, techs_dict, colors):
        
        if self.scen_techs['tes']['deployment'] == True:
            tmp_storage_initial = self.scen_techs['tes']['initial_charge_kWh']
            tmp_cap_max = self.scen_techs['tes']['capacity_kWh']
        else:
            tmp_storage_initial = 0
            tmp_cap_max = 0
            
        techs_dict['tes'] = {
            'essentials':{
                'name':'Thermal Energy Storage',
                'color':colors['tes'],
                'parent':'storage',
                'carrier_in':'heat',
                'carrier_out':'heat'
                },
            'constraints':{
                'storage_initial':tmp_storage_initial,
                'storage_cap_max':tmp_cap_max,
                'lifetime':self.scen_techs['tes']['lifetime']
                },
            'costs':{
                'monetary':{
                    'om_annual':0.0, # !!!TEMPORARY - KOSTEN MÜSSEN DYNAMISCH HINZUGEFÜGT WERDEN!!!
                    'interest_rate':self.scen_techs['tes']['interest_rate']
                    },
                'emissions_co2':{
                    'om_prod':self.scen_techs['tes']['co2_intensity']
                    }
                }
            }
        
        return techs_dict
        
    def __techs_dict_add_power_line(self, techs_dict, colors):
        
        # Virtual power line with infinite capacity and no cost attributed.
        techs_dict['power_line'] = {
            'essentials':{
                'name':'Electrical power transmission',
                'color': colors['power_line'],
                'parent':'transmission',
                'carrier':'electricity'
                },
            'constraints':{
                'energy_eff': 1.0,
                'lifetime': 100
                },
            'costs':{
                'monetary':{
                    'interest_rate': 0.0,
                    'energy_cap_per_distance': 0.0
                    },
                'emissions_co2':{
                    'om_prod': 0.0
                    }
                }
            }
        
        return techs_dict
    
    def __techs_dict_add_gas_line(self, techs_dict, colors):
        
        # Virtual power line with infinite capacity and no cost attributed.
        techs_dict['gas_line'] = {
            'essentials':{
                'name':'gas transmission',
                'color': colors['gas_line'],
                'parent':'transmission',
                'carrier':'gas'
                },
            'constraints':{
                'energy_eff': 1.0,
                'lifetime': 100
                },
            'costs':{
                'monetary':{
                    'interest_rate': 0.0,
                    'energy_cap_per_distance': 0.0
                    },
                'emissions_co2':{
                    'om_prod': 0.0
                    }
                }
            }
        
        return techs_dict
    
    def __techs_dict_add_wood_line(self, techs_dict, colors):
        
        # Virtual power line with infinite capacity and no cost attributed.
        techs_dict['wood_line'] = {
            'essentials':{
                'name':'Wood transmission',
                'color': colors['wood_line'],
                'parent':'transmission',
                'carrier':'wood'
                },
            'constraints':{
                'energy_eff': 1.0,
                'lifetime': 100
                },
            'costs':{
                'monetary':{
                    'interest_rate': 0.0,
                    'energy_cap_per_distance': 0.0
                    },
                'emissions_co2':{
                    'om_prod': 0.0
                    }
                }
            }
        
        return techs_dict
    
    def __techs_dict_add_oil_line(self, techs_dict, colors):
        
        # Virtual power line with infinite capacity and no cost attributed.
        techs_dict['oil_line'] = {
            'essentials':{
                'name':'Oil transmission',
                'parent':'transmission',
                'carrier':'oil'
                },
            'constraints':{
                'energy_eff': 1.0,
                'lifetime': 100
                },
            'costs':{
                'monetary':{
                    'interest_rate': 0.0,
                    'energy_cap_per_distance': 0.0
                    },
                'emissions_co2':{
                    'om_prod': 0.0
                    }
                }
            }
        
        return techs_dict
    
    def __techs_dict_add_wet_biomass_line(self, techs_dict, colors):
        
        # Virtual power line with infinite capacity and no cost attributed.
        techs_dict['wet_biomass_line'] = {
            'essentials':{
                'name':'Wet_Biomass transmission',
                'color': colors['wet_biomass_line'],
                'parent':'transmission',
                'carrier':'wet_biomass'
                },
            'constraints':{
                'energy_eff': 1.0,
                'lifetime': 100
                },
            'costs':{
                'monetary':{
                    'interest_rate': 0.0,
                    'energy_cap_per_distance': 0.0
                    },
                'emissions_co2':{
                    'om_prod': 0.0
                    }
                }
            }
        
        return techs_dict
    
    def __techs_dict_add_heat_line(self, techs_dict, colors):
        
        # Virtual power line with infinite capacity and no cost attributed.
        techs_dict['heat_line'] = {
            'essentials':{
                'name':'Heat transmission',
                'color': colors['heat_line'],
                'parent':'transmission',
                'carrier':'heat'
                },
            'constraints':{
                'energy_eff': 1.0,
                'lifetime': 100
                },
            'costs':{
                'monetary':{
                    'interest_rate': 0.0,
                    'energy_cap_per_distance': 0.0
                    },
                'emissions_co2':{
                    'om_prod': 0.0
                    }
                }
            }
        
        return techs_dict

#%%


# """----------------------------------------------------------------------------
# FOR TESTING ONLY:
# """

# # if __name__ == "__main__":
    
# import os

# cwdir = os.getcwd()

# print(cwdir)

# # For testing:
# # - Generate results with DEM (without optimisation)
# # - Create input here and run function

# scen_techs_file = 'tmp_input_for_calliope_coupling/scen_techs.txt'
# hourly_results_file = 'tmp_input_for_calliope_coupling/hourly_results.csv'
# #annual_results_file = 'tmp_input_for_calliope_coupling/annual_results.txt'

# com_name = 'Allschwil'

# tech_list = [
#     'heat_pump',              
#     'electric_heater',              
#     'oil_boiler',
#     'gas_boiler',
#     'wood_boiler',
#     'district_heating',
#     'solar_thermal',
#     'solar_pv',
#     'grid_supply',
#     'tes'
#     ]

# import ast

# def scen_techs_txt_to_dict(file_path):
#     result_dict = {}
#     with open(file_path, 'r') as file:
#         for line in file:
#             # Split each line into key and value
#             key, value = line.strip().split(': ', 1)
#             # Use ast.literal_eval to safely evaluate the dictionary string
#             result_dict[key] = ast.literal_eval(value)
#     return result_dict

# # Example usage:
# df_scen_techs = scen_techs_txt_to_dict(scen_techs_file)

# df_scen = pd.read_csv(hourly_results_file)

# optimiser = CalliopeOptimiser(
#     tech_list=tech_list,
#     scen_techs=df_scen_techs,
#     df_scen=df_scen,
#     com_name=com_name
#     )

# opt_results, model = optimiser.run_optimisation()
#     # tech_list=tech_list,
#     # scen_techs=df_scen_techs,
#     # df_scen=df_scen,
#     # com_name=com_name
#     # )
    
# # print(opt_results.info())

# # print(opt_results['loc_techs'])

# # print(opt_results.storage.loc['X1::tes'].sum())
# # print(opt_results.carrier_prod.loc['X1::grid_supply::electricity'].sum())
# # print(float(opt_results['carrier_prod'].loc['X1::grid_supply::electricity'][0]))

# # print(opt_results['carrier_prod'].loc['X1::grid_supply::electricity'])

# # m_e = opt_results['carrier_prod'].loc['X1::grid_supply::electricity'].values

# # print(m_e.sum())
# # print(type(m_e))

# # print(opt_results['energy_cap'].loc['X1::grid_supply'])

# # # print(arr_pv)

# # # print(arr_pv.loc['electricity'])

# # print(opt_results['storage'].loc['X1::tes'].values.sum())

# # df_scen_opt, dict_yr_scen_opt, dict_total_costs = optimiser.get_optimal_output_df(opt_results)

# # print(df_scen_opt.info())

# # --------------------------------
# # Print costs:
# # print(type(float(opt_results['total_levelised_cost'].loc['heat'].loc['monetary'].values)))
# # print(opt_results['total_levelised_cost'].loc['electricity'].loc['monetary'].values)
# # print(opt_results['total_levelised_cost'].loc['heat'].loc['emissions_co2'].values)
# # print(opt_results['total_levelised_cost'].loc['electricity'].loc['emissions_co2'].values)
# # print(opt_results['total_levelised_cost'])
# # print(opt_results['total_levelised_cost'].loc['electricity'])

# # print(opt_results['storage'])

# # TRY THIS:

# # print(opt_results['cost'])
# # print(opt_results['cost'].coords['loc_techs_cost'])
# # print(opt_results['cost'].loc['monetary'].loc['X1::grid_supply'].values.sum())

# # print(opt_results['cost'].loc['monetary'].values.sum())
# # print(opt_results['cost'].loc['emissions_co2'].values.sum())

# # print(opt_results['cost'].loc['monetary'])

# model.plot.timeseries(subset={'costs': ['monetary']})
# # model.plot.timeseries(subset={'costs': ['emissions_co2']})

# #%% Re-run via method:

# eps_n = 500000.0 # 11e6 # [kgCO2] example value

# opt_results_new, new_model = optimiser.model_rerun_e_constr(model, eps_n)

# eps_n_new = float(opt_results_new['cost'].loc['emissions_co2'].values.sum())

# print(f"\neps_n: {eps_n_new}\n")


# new_model.plot.timeseries(subset={'costs': ['monetary']})



# #%% Re-run manually:

# # Retrieve list of sets (i.e model dimensions)
# # print(model.backend.get_all_model_attrs()['Set'])

# # print(model.backend.get_all_model_attrs())

# # for set_i in model.backend.get_all_model_attrs()['Set']:
    
# #     print(set_i)


# # opt_results_new, model_new = optimiser.model_rerun(model)

# """
# Implement custom constraints and re-run optimisation model.
# """

# # eps_n = 965107.7672557358 # 11e6 # [kgCO2] example value
# eps_n = 500000.0 # 11e6 # [kgCO2] example value

# # IMPLEMENT CUSTOM CONSTRAINTS HERE

# # constraint_name = 'pv_limit_constraint'
# constraint_name = 'epsilon_constraint'
# # constraint_sets = ['loc_techs_conversion_plus']
# constraint_sets = ['loc_techs_supply_all']


# # Get CO2 intensities [kgCO2/kWh]:
# c_co2_grid = 0.128
# c_co2_pv = 0
# c_co2_wind = 0
# c_co2_solar = 0.025
# c_co2_ob = 0.301
# c_co2_wb = 0.027
# c_co2_gb = 0.228
# c_co2_dh = 0.108

# # Number of timesteps
# ts_len = 360 #360 = 15 days


# # def pv_limit_constraint_rule(backend_model, loc_tech):
# def epsilon_constraint_rule(backend_model, loc_tech):
    
#     ts = backend_model.timesteps # retrieve timesteps
    
#     print('------------------------------------------------------------------')
#     print(backend_model.timesteps)
#     print('------------------------------------------------------------------')

#     # pv_sum = 0
#     sum_kgCO2 = 0    
    
#     # print(type(backend_model.carrier_prod['X1::solar_pv::electricity', ts[1]]))
    
#     for i in range(ts_len):
        
#         # Get all energy flows:
#         m_e = backend_model.carrier_prod['X1::grid_supply::electricity', ts[i+1]]
#         v_e_pv = backend_model.carrier_prod['X1::solar_pv::electricity', ts[i+1]]
#         v_e_wind = 0
#         v_h_solar = backend_model.carrier_prod['X1::solar_thermal::heat', ts[i+1]]
#         v_h_ob = backend_model.carrier_prod['X1::oil_boiler::heat', ts[i+1]]
#         v_h_wb = backend_model.carrier_prod['X1::wood_boiler::heat', ts[i+1]]
#         v_h_gb = backend_model.carrier_prod['X1::gas_boiler::heat', ts[i+1]]
#         v_h_dh = backend_model.carrier_prod['X1::district_heating::heat', ts[i+1]]
        
#         sum_kgCO2 += (m_e*c_co2_grid
#                       + v_e_pv*c_co2_pv
#                       + v_e_wind*c_co2_wind
#                       + v_h_solar*c_co2_solar
#                       + v_h_ob*c_co2_ob
#                       + v_h_wb*c_co2_wb
#                       + v_h_gb*c_co2_gb
#                       + v_h_dh*c_co2_dh
#                       )
        
#         # pv_sum += backend_model.carrier_prod['X1::solar_pv::electricity', ts[i+1]]
    
#     # return pv_sum <= 1000000
#     return sum_kgCO2 <= eps_n

#     # return backend_model.carrier_prod['X1::solar_pv::electricity', ts[1]] == 0

#     # print("TEST -----------------------------------")
    
#     # return backend_model.energy_cap['X1::heat_pump'] == 0.0
    

# model.backend.add_constraint(
#     constraint_name,
#     constraint_sets,
#     epsilon_constraint_rule
#     )

# #  - access variables through backend, e.g. backend_model.carrier_prod['X1::grid_supply::electricity']
# # Re-run model to implement custom constraints:
# new_model = model.backend.rerun()

# opt_results_ = new_model.results

# eps_n_new = float(opt_results_['cost'].loc['emissions_co2'].values.sum())

# print(f"\neps_n: {eps_n_new}\n")


# new_model.plot.timeseries(subset={'costs': ['monetary']})

# '''
# Ideas for epsilon-constraint:
    
    
# Possible sets:
    
    

    
# '''

































