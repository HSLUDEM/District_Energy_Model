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
    def __init__(self, tech_list, tech_instances, energy_demand, supply, com_name, scen_techs, files_path):
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
        self.com_name = com_name
        self.scen_techs = scen_techs
        self.opt_metrics = scen_techs['optimisation']
        self.files_path = files_path
                
        self.available_area_scaling = 1 # This is NOT a physical area value!!!
        
        self.rerun_eps = False
        self.eps_n = 'inf'
        self.dhn_share_type = False
        self.dhn_share_val = 0.0
        
        self.custom_constraints = False
        
        self.tech_list_new = []
        self.tech_list_old = []
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

        if 'wind_power' in self.tech_list:
            self.tech_wind_power = tech_instances['wind_power']
        
        if 'hydro_power' in self.tech_list:
            self.tech_hydro_power = tech_instances['hydro_power']
            
        if 'biomass' in self.tech_list:
            self.tech_biomass = tech_instances['biomass']
        
        if 'grid_supply' in self.tech_list:
            self.tech_grid_supply = tech_instances['grid_supply']
        
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
        demand_heat = -(self.energy_demand.get_d_h())
        # demand_power = -(self.energy_demand.get_d_e_hh())
        # demand_power = -(
        #     self.energy_demand.get_d_e_hh()
        #     + self.energy_demand.get_d_e_ev()
        #     )
        
        # demand_power = -(
        #     self.energy_demand.get_d_e()
        #     - self.energy_demand.get_d_e_h()
        #     )
        
        demand_power_hh = -(self.energy_demand.get_d_e_hh())
        
        demand_power_ev = -(self.energy_demand.get_d_e_ev())
        demand_power_ev_cp = -(self.energy_demand.get_d_e_ev_cp())
        demand_power_ev_pd = -(self.energy_demand.get_d_e_ev_pd())
        demand_power_ev_pu = -(self.energy_demand.get_d_e_ev_pu())
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
        demand_power_hh = pd.Series(demand_power_hh, index=date_index)
        demand_power_ev = pd.Series(demand_power_ev, index=date_index)
        demand_power_ev_cp = pd.Series(demand_power_ev_cp, index=date_index)
        demand_power_ev_pd = pd.Series(demand_power_ev_pd, index=date_index)
        demand_power_ev_pu = pd.Series(demand_power_ev_pu, index=date_index)
        demand_power_ev_delta = pd.Series(demand_power_ev_delta, index=date_index)

        # pv_resource_old = pd.Series(pv_resource_old, index=date_index)
        # pv_resource_new = pd.Series(pv_resource_new, index=date_index)

        
        
        pv_rooftop_resources = [pd.Series(x, index=date_index) for x in pv_rooftop_resources]
        solarthermal_rooftop_resources = [pd.Series(x, index=date_index) for x in solarthermal_rooftop_resources]

        # solar_th_resource_old = pd.Series(solar_th_resource_old, index=date_index)
        # solar_th_resource_new = pd.Series(solar_th_resource_new, index=date_index)

        supply_wet_biomass = pd.Series(supply_wet_biomass, index=date_index)
        supply_wood = pd.Series(supply_wood, index=date_index)
        wp_resource_annual = pd.Series(wp_resource_annual, index=date_index)
        wp_resource_winter = pd.Series(wp_resource_winter, index=date_index)
        hydro_resource = pd.Series(hydro_resource, index=date_index)
        waste_heat_resource = pd.Series(waste_heat_resource, index=date_index)
        waste_heat_low_temperature_resource = pd.Series(waste_heat_low_temperature_resource, index=date_index)

        heat_pump_cp_cops = pd.Series(heat_pump_cp_cops, index=date_index)

        heat_pump_cops_existing = pd.Series(heat_pump_cops_existing, index=date_index)
        heat_pump_cops_one_to_one_replacement = pd.Series(heat_pump_cops_one_to_one_replacement, index=date_index)
        heat_pump_cops_new = pd.Series(heat_pump_cops_new, index=date_index)

        # Convert pandas series to dataframe:
        df_demand_heat = demand_heat.to_frame('d_h')
        # df_demand_power = demand_power.to_frame('d_e_hh')
        df_demand_power_hh = demand_power_hh.to_frame('d_e_hh')
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

        df_solarthermal_rooftop_resource = pd.concat(solarthermal_rooftop_resources, axis = 1)
        df_solarthermal_rooftop_resource.columns = ['v_h_solarthermalrooftop_'+str(i) for i in range(len(solarthermal_rooftop_resources))]


        # df_solar_th_resource_old = solar_th_resource_old.to_frame('v_h_solar_th')
        # df_solar_th_resource_new = solar_th_resource_new.to_frame('v_h_solar_th')

        df_supply_wet_biomass = supply_wet_biomass.to_frame('s_wet_bm')
        df_supply_wood = supply_wood.to_frame('s_wd')
        df_wp_resource_annual = wp_resource_annual.to_frame('v_e_wp')
        df_wp_resource_winter = wp_resource_winter.to_frame('v_e_wp')
        df_hydro_resource = hydro_resource.to_frame('v_e_hydro')
        df_waste_heat_resource = waste_heat_resource.to_frame('v_h_wh')
        df_waste_heat_low_temperature_resource = waste_heat_low_temperature_resource.to_frame('v_hlt_whlt')

        df_heat_pump_cp_cops = heat_pump_cp_cops.to_frame('cop')

        df_heat_pump_cops_existing = heat_pump_cops_existing.to_frame('heat_pump_cops_existing')
        df_heat_pump_cops_new = heat_pump_cops_new.to_frame('heat_pump_cops_new')
        df_heat_pump_cops_one_to_one_replacement = heat_pump_cops_one_to_one_replacement.to_frame('heat_pump_cops_one_to_one_replacement')

        # print(df_heat_pump_cops_one_to_one_replacement)
        # exit()

        # Timeseries data for Calliope model: (Get these from df_scen!!!)
        timeseries_dataframes = {
            'demand_heat':df_demand_heat,
            # 'demand_power':df_demand_power,
            'demand_power_hh':df_demand_power_hh,
            'demand_power_ev':df_demand_power_ev,
            'demand_power_ev_cp':df_demand_power_ev_cp,
            'demand_power_ev_pd':df_demand_power_ev_pd,
            'demand_power_ev_pu':df_demand_power_ev_pu,
            'demand_power_ev_delta':df_demand_power_ev_delta,            
            # 'pv_resource_old':df_pv_resource_old,
            # 'pv_resource_new':df_pv_resource_new,

            'pvrooftop_resource':df_pv_rooftop_resource,

            'solarthermalrooftop_resource':df_solarthermal_rooftop_resource,

            # 'solar_th_resource_old':df_solar_th_resource_old,
            # 'solar_th_resource_new':df_solar_th_resource_new,            
            'wet_biomass_resource':df_supply_wet_biomass,
            'wood_resource':df_supply_wood,
            'wp_resource_annual':df_wp_resource_annual,
            'wp_resource_winter':df_wp_resource_winter,
            'hydro_resource':df_hydro_resource,
            'waste_heat':df_waste_heat_resource,
            'waste_heat_low_temperature':df_waste_heat_low_temperature_resource,
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
        input_dict = self.__build_input_dict()
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
        model = calliope.Model(
            input_dict,
            timeseries_dataframes=timeseries_dataframes
            )
        
        print('\nModel running ...\n')
    
        #----------------------------------------------------------------------
        # Run model:
        calliope.set_log_verbosity('INFO')

        self.custom_constraint_ev_flexibility = (self.scen_techs['scenarios']['demand_side']
                                        and self.scen_techs['demand_side']['ev_integration']
                                        and self.scen_techs['demand_side']['ev_flexibility'])
        self.custom_constraint_tes_sites = self.tech_tes_sites.get_custom_constraints_required()


        if (
            self.custom_constraint_ev_flexibility or self.custom_constraint_tes_sites
                ):
            self.custom_constraints = True

        if self.custom_constraints:
            model.run(build_only = True)
        else:
            model.run()
        
        
        if self.custom_constraints:
        
            if self.custom_constraint_tes_sites:

                ts_len = len(demand_heat)

                #Custom constraints and costs for TES Sites

                model = dem_calliope_cc.tes_sites_lt_no_conversion_without_charging_constraint(model, ts_len, self.tech_tes_sites.get_sites_list())
                
                model = dem_calliope_cc.tes_sites_size_ratios_constraints(model, ts_len, self.tech_tes_sites.get_sites_list())

                model = dem_calliope_cc.tes_sites_minimum_size_constraints(model, ts_len, self.tech_tes_sites.get_sites_list())

                model = dem_calliope_cc.tes_sites_minimum_size_cost(model, ts_len, self.tech_tes_sites.get_sites_list())
                
                model = dem_calliope_cc.tes_sites_charge_constraints(model, ts_len, self.tech_tes_sites.get_sites_list())

                

                
            if self.custom_constraint_ev_flexibility:
                ts_len = len(demand_heat)
                n_days = int(ts_len/24.0) # assuming hourly timesteps and full days
                
                # Add custom constraints for EV flexibility:

                # print(model.backend)
                # exit()

                model = dem_calliope_cc.ev_flexibility_constraints(
                    model=model,
                    ts_len=ts_len,
                    n_days=n_days,
                    energy_demand=self.energy_demand,
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
        
        # arr = model.get_formatted_array('carrier_prod')
        
        if self.custom_constraints:
            return opt_results, new_model
        else:
            return opt_results, model        

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
        n_hours = len(self.energy_demand.get_d_e())
        null_array = np.array([0.0]*n_hours)
        
        
        # ---------------------------------------------------------------------
        # Extract hourly values as numpy arrays:
        
        # ! CHECK NEGATIVE / POSITIVE !!!
        # ! HOW IS ADDITIONAL ELECTRICITY DEMAND HANDLED? !!!
        # ! WHAT IF TECH IS DEACTIVATED?
        
        # -------------------
        # Heat pump:
        if 'heat_pump' in self.tech_list:                    
            v_h_hp_old = opt_results['carrier_prod'].loc['X1::heat_pump_old::heat_hp'].values
            v_h_hp_one_to_one_replacement = opt_results['carrier_prod'].loc['X1::heat_pump_one_to_one_replacement::heat_hp'].values
            v_h_hp_new = opt_results['carrier_prod'].loc['New_Techs::heat_pump_new::heat_hp'].values
           
            u_e_hp_old = opt_results['carrier_con'].loc['X1::heat_pump_old::electricity'].values
            u_e_hp_one_to_one_replacement = opt_results['carrier_con'].loc['X1::heat_pump_one_to_one_replacement::electricity'].values
            u_e_hp_new = opt_results['carrier_con'].loc['New_Techs::heat_pump_new::electricity'].values

            v_h_hp = v_h_hp_old + v_h_hp_one_to_one_replacement + v_h_hp_new
            u_e_hp = -u_e_hp_old - u_e_hp_one_to_one_replacement - u_e_hp_new
            u_h_hp = v_h_hp - u_e_hp

            # print(opt_results)
            # exit()
            # self.tech_heat_pump.update_v_h(v_h_hp)
            # u_e_hp = self.tech_heat_pump.get_u_e()

            self.tech_heat_pump.update_v_h_u_h_u_e(v_h_hp, u_h_hp, u_e_hp)

        else:            
            u_e_hp = null_array.copy()
            u_h_hp = null_array.copy()
            v_h_hp = null_array.copy()
        

        # -------------------
        # Electric heater:
        if 'electric_heater' in self.tech_list:
            v_h_eh = opt_results['carrier_prod'].loc['X1::electric_heater_old::heat'].values               
            self.tech_electric_heater.update_v_h(v_h_eh)
            u_e_eh = self.tech_electric_heater.get_u_e()
        else:
            u_e_eh = null_array.copy()

        # -------------------
        # Oil boiler:
        if 'oil_boiler' in self.tech_list:
            v_h_ob = (
                opt_results['carrier_prod'].loc['X1::oil_boiler_old::heat'].values
                + opt_results['carrier_prod'].loc['New_Techs::oil_boiler_new::heat'].values
                + opt_results['carrier_prod'].loc['X1::oil_boiler_one_to_one_replacement::heat'].values
                )
            self.tech_oil_boiler.update_v_h(v_h_ob)
        
        # -------------------
        # Gas boiler:
        if 'gas_boiler' in self.tech_list:
            v_h_gb = (
                opt_results['carrier_prod'].loc['X1::gas_boiler_old::heat'].values
                + opt_results['carrier_prod'].loc['New_Techs::gas_boiler_new::heat'].values
                + opt_results['carrier_prod'].loc['X1::gas_boiler_one_to_one_replacement::heat'].values
                )
            self.tech_gas_boiler.update_v_h(v_h_gb)

        # -------------------
        # Wood boiler:
        if 'wood_boiler' in self.tech_list:
            v_h_wb = (
                opt_results['carrier_prod'].loc['X1::wood_boiler_old::heat'].values
                + opt_results['carrier_prod'].loc['New_Techs::wood_boiler_new::heat'].values
                + opt_results['carrier_prod'].loc['X1::wood_boiler_one_to_one_replacement::heat'].values
                )
            self.tech_wood_boiler.update_v_h(v_h_wb)

        # -------------------
        # District heating:
        if 'district_heating' in self.tech_list:
            
            v_h_dh = opt_results['carrier_prod'].loc['X1::district_heating_hub_0::heat'].values
            for i in range(self.tech_district_heating.dhn_qty -1):
                v_h_dh += opt_results['carrier_prod'].loc['X1::district_heating_hub_'+str(i+1)+'::heat'].values
            
            self.tech_district_heating.update_v_h(v_h_dh)

            m_h_dh = opt_results['carrier_prod'].loc['X1::district_heating_import::heat_dhimp'].values
            self.tech_district_heating.update_m_h(m_h_dh)

        # -------------------
        # Solar thermal:
        if 'solar_thermal' in self.tech_list:
            v_h_solar =\
                (
                    opt_results['carrier_prod'].loc['New_Techs::solar_thermal_new::heat'].values
                    + opt_results['carrier_prod'].loc['Old_Solar_Thermal::solar_thermal_old::heat'].values
                    
                    )
            self.tech_solar_thermal.update_v_h(v_h_solar)
                
        # -------------------
        # Other (unknown) sources:
        if 'other' in self.tech_list:
            v_h_other = null_array.copy()
            self.tech_other.update_v_h(v_h_other) # !!! CURRENTLY LEAVE AS IS. MUST LATER BE HANDLED DIFFERENTLY !!!

        # -------------------
        # Solar PV:
        # if 'solar_pv' in self.tech_list:
        #     if self.tech_solar_pv.get_only_use_installed():
        #         v_e_pv =\
        #             opt_results['carrier_prod'].loc['Old_Solar_PV::solar_pv_old::electricity'].values
        #         v_e_pv_cons = (
        #             v_e_pv
        #             -opt_results['carrier_export'].loc['Old_Solar_PV::solar_pv_old::electricity'].values
        #             )
        #         v_e_pv_exp =\
        #             opt_results['carrier_export'].loc['Old_Solar_PV::solar_pv_old::electricity'].values
                
        #     else:
        #         v_e_pv = (
        #             opt_results['carrier_prod'].loc['New_Techs::solar_pv_new::electricity'].values +
        #             opt_results['carrier_prod'].loc['Old_Solar_PV::solar_pv_old::electricity'].values
        #             )
        #         v_e_pv_cons = (
        #             v_e_pv
        #             -opt_results['carrier_export'].loc['New_Techs::solar_pv_new::electricity'].values
        #             -opt_results['carrier_export'].loc['Old_Solar_PV::solar_pv_old::electricity'].values
        #             )
        #         v_e_pv_exp = (
        #             opt_results['carrier_export'].loc['New_Techs::solar_pv_new::electricity'].values + 
        #             opt_results['carrier_export'].loc['Old_Solar_PV::solar_pv_old::electricity'].values
        #             )
        #     if 'solar_thermal' in self.tech_list:
        #         self.tech_solar_pv.update_v_e(
        #                 v_e_updated=v_e_pv,
        #                 tech_solar_thermal=self.tech_solar_thermal,
        #                 consider_solar_thermal=True
        #                 )
        #     else:
        #         self.tech_solar_pv.update_v_e(
        #                 v_e_updated=v_e_pv,
        #                 consider_solar_thermal=False
        #                 )
                
        #     self.tech_solar_pv.update_v_e_cons(v_e_pv_cons)
        #     self.tech_solar_pv.update_v_e_exp(v_e_pv_exp)


        # -------------------
        # Solar PV rooftop:
        if 'solar_pvrooftop' in self.tech_list:

            pvrooftop_cats = self.tech_solar_pvrooftop.get_num_installations()

            if self.tech_solar_pvrooftop.get_only_use_installed():

                v_e_pvrooftop_s = [opt_results['carrier_prod'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity'].values 
                           for i in range(pvrooftop_cats)]

                v_e_pvrooftop_s_cons = [v_e_pvrooftop_s[i] - opt_results['carrier_export'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity'].values 
                           for i in range(pvrooftop_cats)]

                v_e_pvrooftop_s_exp = [opt_results['carrier_export'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity'].values 
                           for i in range(pvrooftop_cats)]
                
            else:

                v_e_pvrooftop_s = [opt_results['carrier_prod'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity'].values 
                           + opt_results['carrier_prod'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_unoccupied'+'::electricity'].values
                           for i in range(pvrooftop_cats)]

                v_e_pvrooftop_s_cons = [v_e_pvrooftop_s[i] - opt_results['carrier_export'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity'].values 
                                - opt_results['carrier_export'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_unoccupied'+'::electricity'].values 
                           for i in range(pvrooftop_cats)]

                v_e_pvrooftop_s_exp = [opt_results['carrier_export'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity'].values 
                               + opt_results['carrier_export'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_unoccupied'+'::electricity'].values
                           for i in range(pvrooftop_cats)]
            
            self.tech_solar_pvrooftop.update_v_e(v_e_pvrooftop_s)
            self.tech_solar_pvrooftop.update_v_e_cons(v_e_pvrooftop_s_cons)
            self.tech_solar_pvrooftop.update_v_e_exp(v_e_pvrooftop_s_exp)

        if 'solarthermal_rooftop' in self.tech_list:

            solarthermal_rooftop_cats = self.tech_solarthermal_rooftop.get_num_installations()

            # if self.tech_solarthermal_rooftop.get_only_use_installed():

                # v_h_solarthermalrooftop_s = [opt_results['carrier_prod'].loc['solarthermal_rooftop_installation_'+str(i)+'::solarthermal_rooftop_installation_'+str(i)+'_occupied'+'::heat_hp'].values 
                #            for i in range(solarthermal_rooftop_cats)]

                # v_h_solarthermalrooftop_s_cons = [v_h_pvrooftop_s[i] - opt_results['carrier_export'].loc['solarthermal_rooftop_installation_'+str(i)+'::solarthermal_rooftop_installation_'+str(i)+'_occupied'+'::heat_hp'].values 
                #            for i in range(solarthermal_rooftop_cats)]

                # v_h_solarthermalrooftop_s_exp = [opt_results['carrier_export'].loc['solarthermal_rooftop_installation_'+str(i)+'::solarthermal_rooftop_installation_'+str(i)+'_occupied'+'::heat_hp'].values 
                #            for i in range(solarthermal_rooftop_cats)]
                
            # else:
            if True:

                # print(opt_results['carrier_prod']['loc_tech_carriers_prod'])
                # print(type(opt_results['carrier_prod']))
                # exit()

                v_h_solarthermalrooftop_s = [opt_results['carrier_prod'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_occupied'+'::heat_hp'].values 
                           + opt_results['carrier_prod'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_unoccupied'+'::heat_hp'].values
                           for i in range(solarthermal_rooftop_cats)]

                v_h_solarthermalrooftop_s_cons = [v_h_solarthermalrooftop_s[i] - opt_results['carrier_export'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_occupied'+'::heat_hp'].values 
                                - opt_results['carrier_export'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_unoccupied'+'::heat_hp'].values 
                           for i in range(solarthermal_rooftop_cats)]

                v_h_solarthermalrooftop_s_exp = [opt_results['carrier_export'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_occupied'+'::heat_hp'].values 
                               + opt_results['carrier_export'].loc['solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_unoccupied'+'::heat_hp'].values
                           for i in range(solarthermal_rooftop_cats)]
            
            self.tech_solarthermal_rooftop.update_v_h(v_h_solarthermalrooftop_s)
            self.tech_solarthermal_rooftop.update_v_h_cons(v_h_solarthermalrooftop_s_cons)
            self.tech_solarthermal_rooftop.update_v_h_exp(v_h_solarthermalrooftop_s_exp)   

        else:
            raise Exception("Not implemented")







        # -----------
        # Wind power:
        if 'wind_power' in self.tech_list:
            v_e_wp = (
                opt_results['carrier_prod'].loc['loc_wp_winter::wind_power_old::wp_electricity'].values
                + opt_results['carrier_prod'].loc['loc_wp_winter::wind_power_new::wp_electricity'].values
                + opt_results['carrier_prod'].loc['loc_wp_annual::wind_power_old::wp_electricity'].values
                + opt_results['carrier_prod'].loc['loc_wp_annual::wind_power_new::wp_electricity'].values
                )
            v_e_wp_exp = (
                opt_results['carrier_export'].loc['loc_wp_winter::wind_power_old::wp_electricity'].values
                + opt_results['carrier_export'].loc['loc_wp_winter::wind_power_new::wp_electricity'].values
                + opt_results['carrier_export'].loc['loc_wp_annual::wind_power_old::wp_electricity'].values
                + opt_results['carrier_export'].loc['loc_wp_annual::wind_power_new::wp_electricity'].values
                )
            v_e_wp_cons = (v_e_wp - v_e_wp_exp)
            self.tech_wind_power.update_v_e(v_e_wp)
            self.tech_wind_power.update_v_e_exp(v_e_wp_exp)
            self.tech_wind_power.update_v_e_cons(v_e_wp_cons)

        #--------
        #Hydrothermal Gasification
        if 'hydrothermal_gasification' in self.tech_list:
            v_gas_hg = opt_results['carrier_prod'].loc['New_Techs::hydrothermal_gasification::gas'].values
            self.tech_hydrothermal_gasification.update_v_gas(v_gas_hg)            
            # u_wet_bm_hg = self.tech_hydrothermal_gasification.get_u_wet_bm()
        
        else:
            v_gas_hg = null_array.copy()
            # u_wet_bm_hg = null_array.copy()
        
        #--------
        #Anaerobic Digesion Upgrade
        if 'anaerobic_digestion_upgrade' in self.tech_list:
            v_gas_agu = opt_results['carrier_prod'].loc['New_Techs::anaerobic_digestion_upgrade::gas'].values
            self.tech_anaerobic_digestion_upgrade.update_v_gas(v_gas_agu)            
            u_wet_bm_agu = self.tech_anaerobic_digestion_upgrade.get_u_wet_bm()
        
        else:
            v_gas_agu = null_array.copy()
            u_wet_bm_agu = null_array.copy()
            
        #--------
        #Anaerobic Digestion Upgrade Hydrogen
        if 'anaerobic_digestion_upgrade_hydrogen' in self.tech_list:
            u_wet_bm_aguh = -opt_results['carrier_con'].loc['New_Techs::anaerobic_digestion_upgrade_hydrogen::wet_biomass'].values
            u_e_aguh = -opt_results['carrier_con'].loc['New_Techs::anaerobic_digestion_upgrade_hydrogen::electricity'].values
            u_hyd_aguh = -opt_results['carrier_con'].loc['New_Techs::anaerobic_digestion_upgrade_hydrogen::hydrogen'].values
            v_gas_aguh = opt_results['carrier_prod'].loc['New_Techs::anaerobic_digestion_upgrade_hydrogen::gas'].values
            v_h_aguh = opt_results['carrier_prod'].loc['New_Techs::anaerobic_digestion_upgrade_hydrogen::heat_biomass'].values
            self.tech_anaerobic_digestion_upgrade_hydrogen.update_u_wet_bm(u_wet_bm_aguh)
            self.tech_anaerobic_digestion_upgrade_hydrogen.update_u_e(u_e_aguh)
            self.tech_anaerobic_digestion_upgrade_hydrogen.update_u_hyd(u_hyd_aguh)
            self.tech_anaerobic_digestion_upgrade_hydrogen.update_v_gas(v_gas_aguh)
            self.tech_anaerobic_digestion_upgrade_hydrogen.update_v_h(v_h_aguh)
            
        else:
            u_wet_bm_aguh = null_array.copy()
            u_e_aguh = null_array.copy()
            u_hyd_aguh = null_array.copy()
            v_gas_aguh = null_array.copy()
            v_h_aguh = null_array.copy()
        
        #--------
        #Anaerobic Digestion CHP
        if 'anaerobic_digestion_chp' in self.tech_list:
            u_wet_bm_aguc = -opt_results['carrier_con'].loc['New_Techs::anaerobic_digestion_chp::wet_biomass'].values
            v_e_aguc = opt_results['carrier_prod'].loc['New_Techs::anaerobic_digestion_chp::electricity'].values
            v_h_aguc = opt_results['carrier_prod'].loc['New_Techs::anaerobic_digestion_chp::heat_biomass'].values
            v_e_aguc_exp = opt_results['carrier_export'].loc['New_Techs::anaerobic_digestion_chp::electricity'].values
            self.tech_anaerobic_digestion_chp.update_u_wet_bm(u_wet_bm_aguc)
            self.tech_anaerobic_digestion_chp.update_v_e(v_e_aguc)
            self.tech_anaerobic_digestion_chp.update_v_h(v_h_aguc)
            self.tech_anaerobic_digestion_chp.update_v_e_exp(v_e_aguc_exp)
            
        else:
            u_wet_bm_aguc = null_array.copy()
            v_e_aguc = null_array.copy()
            v_h_aguc = null_array.copy()
            v_e_aguc_exp = null_array.copy()
            
        #--------
        #Wood Gasification Upgrade
        if 'wood_gasification_upgrade' in self.tech_list:
            u_wd_wgu = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_upgrade::wood'].values
            u_e_wgu = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_upgrade::electricity'].values
            v_gas_wgu = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_upgrade::gas'].values
            v_h_wgu = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_upgrade::heat_biomass'].values
            self.tech_wood_gasification_upgrade.update_u_wd(u_wd_wgu)
            self.tech_wood_gasification_upgrade.update_u_e(u_e_wgu)
            self.tech_wood_gasification_upgrade.update_v_gas(v_gas_wgu)
            self.tech_wood_gasification_upgrade.update_v_h(v_h_wgu)
            
        else:
            u_wd_wgu = null_array.copy()
            u_e_wgu = null_array.copy()
            v_gas_wgu = null_array.copy()
            v_h_wgu = null_array.copy()
            
        #--------
        #Wood Gasification Upgrade Hydrogen
        if 'wood_gasification_upgrade_hydrogen' in self.tech_list:
            u_wd_wguh = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_upgrade_hydrogen::wood'].values
            u_e_wguh = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_upgrade_hydrogen::electricity'].values
            u_hyd_wguh = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_upgrade_hydrogen::hydrogen'].values
            v_gas_wguh = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_upgrade_hydrogen::gas'].values
            v_h_wguh = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_upgrade_hydrogen::heat_biomass'].values
            self.tech_wood_gasification_upgrade_hydrogen.update_u_wd(u_wd_wguh)
            self.tech_wood_gasification_upgrade_hydrogen.update_u_e(u_e_wguh)
            self.tech_wood_gasification_upgrade_hydrogen.update_u_hyd(u_hyd_wguh)
            self.tech_wood_gasification_upgrade_hydrogen.update_v_gas(v_gas_wguh)
            self.tech_wood_gasification_upgrade_hydrogen.update_v_h(v_h_wguh)
            
        else:
            u_wd_wguh = null_array.copy()
            u_e_wguh = null_array.copy()
            u_hyd_wguh = null_array.copy()
            v_gas_wguh = null_array.copy()
            v_h_wguh = null_array.copy()
            
        #--------
        #Wood Gasification CHP
        if 'wood_gasification_chp' in self.tech_list:
            u_wd_wguc = -opt_results['carrier_con'].loc['New_Techs::wood_gasification_chp::wood'].values
            v_e_wguc = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_chp::electricity'].values
            v_h_wguc = opt_results['carrier_prod'].loc['New_Techs::wood_gasification_chp::heat_biomass'].values
            v_e_wguc_exp = opt_results['carrier_export'].loc['New_Techs::wood_gasification_chp::electricity'].values
            self.tech_wood_gasification_chp.update_u_wd(u_wd_wguc)
            self.tech_wood_gasification_chp.update_v_e(v_e_wguc)
            self.tech_wood_gasification_chp.update_v_h(v_h_wguc)
            self.tech_wood_gasification_chp.update_v_e_exp(v_e_wguc_exp)
            
        else:
            u_wd_wguc = null_array.copy()
            v_e_wguc = null_array.copy()
            v_h_wguc = null_array.copy()
            v_e_wguc_exp = null_array.copy()
            
        #--------
        #Hydrogen Production
        if 'hydrogen_production' in self.tech_list:
            v_hyd_hydp = opt_results['carrier_prod'].loc['New_Techs::hydrogen_production::hydrogen'].values
            self.tech_hydrogen_production.update_v_hyd(v_hyd_hydp)
            u_e_hydp = self.tech_hydrogen_production.get_u_e()
        else:
            v_hyd_hydp = null_array.copy()
            u_e_hydp = null_array.copy()
            
        #------------------
        # Biomass Totals
        if 'biomass' in self.tech_list:
            v_e_bm = v_e_aguc + v_e_wguc
            v_e_bm_exp = v_e_aguc_exp + v_e_wguc_exp
            v_e_bm_cons = v_e_bm - v_e_bm_exp
            v_h_bm = v_h_aguh + v_h_aguc + v_h_wgu + v_h_wguh + v_h_wguc
            self.tech_biomass.update_v_e(v_e_bm)
            self.tech_biomass.update_v_e_exp(v_e_bm_exp)
            self.tech_biomass.update_v_e_cons(v_e_bm_cons)
            self.tech_biomass.update_v_h(v_h_bm)

        #------------------
        # Biomass Supply
        s_wet_bm_prev = self.supply.get_s_wet_bm()
        s_wd_prev = self.supply.get_s_wd()

        s_wet_bm_rem = (
            s_wet_bm_prev
            - opt_results['carrier_prod'].loc['Limited_Supplies::wet_biomass_supply::wet_biomass'].values
            )

        s_wd_rem = (
            s_wd_prev
            - opt_results['carrier_prod'].loc['Limited_Supplies::wood_supply::wood'].values
            )

        s_wet_bm = opt_results['carrier_prod'].loc['Limited_Supplies::wet_biomass_supply::wet_biomass'].values
        s_wd = opt_results['carrier_prod'].loc['Limited_Supplies::wood_supply::wood'].values        
        self.supply.update_s_wet_bm(s_wet_bm)
        self.supply.update_s_wd(s_wd)
        self.supply.update_s_wet_bm_rem(s_wet_bm_rem)
        self.supply.update_s_wd_rem(s_wd_rem)
        
        # ------------------- 
        # Hydro Power (local):
        if 'hydro_power' in self.tech_list:
            v_e_hydro = (
                opt_results['carrier_prod'].loc['X1::hydro_power::electricity'].values
                )
            v_e_hydro_cons = (
                v_e_hydro
                -opt_results['carrier_export'].loc['X1::hydro_power::electricity'].values
                )
            v_e_hydro_exp = (
                opt_results['carrier_export'].loc['X1::hydro_power::electricity'].values
                )
            self.tech_hydro_power.update_v_e(v_e_hydro)
            self.tech_hydro_power.update_v_e_cons(v_e_hydro_cons)
            self.tech_hydro_power.update_v_e_exp(v_e_hydro_exp)
            
        # -------------------
        # CHP gas turbine:
        if 'chp_gt' in self.tech_list:
            v_e_chp_gt = opt_results['carrier_prod'].loc['X1::chp_gt_new::electricity'].values
            v_h_chp_gt = opt_results['carrier_prod'].loc['X1::chp_gt_new::heat_chpgt'].values
            v_h_chp_gt_waste = opt_results['carrier_export'].loc['X1::chp_gt_new::heat_chpgt'].values
            v_h_chp_gt_con = v_h_chp_gt - v_h_chp_gt_waste
            
            self.tech_chp_gt.update_v_e(v_e_chp_gt)
            self.tech_chp_gt.update_v_h(v_h_chp_gt)
            self.tech_chp_gt.update_v_h_waste(v_h_chp_gt_waste)
            self.tech_chp_gt.update_v_h_con(v_h_chp_gt_con)

            if self.tech_chp_gt.get_deploy_existing():
                # TO BE IMPLEMENTED
                raise Exception("Existing CHP plants not yet implemented in Calliope get_optimal_output_df()!")
                
        # -------------------
        # Gas turbine (central plant):
        if 'gas_turbine_cp' in self.tech_list:
            v_e_gtcp = opt_results['carrier_prod'].loc['X1::gas_turbine_cp_exist::electricity'].values
            v_steam_gtcp = opt_results['carrier_prod'].loc['X1::gas_turbine_cp_exist::steam'].values
            v_steam_gtcp_surp = opt_results['carrier_export'].loc['X1::gas_turbine_cp_exist::steam'].values
            v_steam_gtcp_con = v_steam_gtcp - v_steam_gtcp_surp
            self.tech_gas_turbine_cp.update_v_e(v_e_gtcp)
            self.tech_gas_turbine_cp.update_v_steam(v_steam_gtcp)
            self.tech_gas_turbine_cp.update_v_steam_surp(v_steam_gtcp_surp)
            self.tech_gas_turbine_cp.update_v_steam_con(v_steam_gtcp_con)
            
        # -------------------
        # Wood boiler (steam generator):
        if 'wood_boiler_sg' in self.tech_list:
            v_steam_wbsg = opt_results['carrier_prod'].loc['X1::wood_boiler_sg_exist::steam'].values
            self.tech_wood_boiler_sg.update_v_steam(v_steam_wbsg)
            
        # -------------------
        # Steam turbine:
        if 'steam_turbine' in self.tech_list:
            v_e_st = opt_results['carrier_prod'].loc['X1::steam_turbine_exist::electricity'].values
            v_h_st = opt_results['carrier_prod'].loc['X1::steam_turbine_exist::heat_st'].values
            v_h_st_waste = opt_results['carrier_export'].loc['X1::steam_turbine_exist::heat_st'].values
            v_h_st_con = v_h_st - v_h_st_waste

            self.tech_steam_turbine.update_v_e(v_e_st)
            self.tech_steam_turbine.update_v_h(v_h_st)
            self.tech_steam_turbine.update_v_h_waste(v_h_st_waste)
            self.tech_steam_turbine.update_v_h_con(v_h_st_con)



            if 'gas_turbine_cp' in self.tech_list:
                self.tech_steam_turbine.compute_v_e_gtcp(self.tech_gas_turbine_cp)
                self.tech_steam_turbine.compute_v_h_gtcp(self.tech_gas_turbine_cp)
            if 'wood_boiler_sg' in self.tech_list:
                self.tech_steam_turbine.compute_v_e_wbsg(self.tech_wood_boiler_sg)
                self.tech_steam_turbine.compute_v_h_wbsg(self.tech_wood_boiler_sg)
            
        # -------------------
        # Waste-to-energy plant:
        if 'waste_to_energy' in self.tech_list:
            v_e_wte = opt_results['carrier_prod'].loc['X1::waste_to_energy_exist::electricity'].values
            v_h_wte = opt_results['carrier_prod'].loc['X1::waste_to_energy_exist::heat_wte'].values
            v_h_wte_waste = opt_results['carrier_export'].loc['X1::waste_to_energy_exist::heat_wte'].values
            v_h_wte_con = v_h_wte - v_h_wte_waste
            
            self.tech_waste_to_energy.update_v_e(v_e_wte)
            self.tech_waste_to_energy.update_v_h(v_h_wte)
            self.tech_waste_to_energy.update_v_h_waste(v_h_wte_waste)
            self.tech_waste_to_energy.update_v_h_con(v_h_wte_con)


        # -------------------
        # Heat pump (central plant):
        if 'heat_pump_cp' in self.tech_list:
            v_h_hpcp = opt_results['carrier_prod'].loc['X1::heat_pump_cp_exist::heat_hpcp'].values
            self.tech_heat_pump_cp.update_v_h(v_h_hpcp)
            u_e_hpcp = self.tech_heat_pump_cp.get_u_e()
        
        else:            
            u_e_hpcp = null_array.copy()

        # -------------------
        # Heat pump (central plant, from low temperature heat):
        if 'heat_pump_cp_lt' in self.tech_list:
            v_h_hpcplt = opt_results['carrier_prod'].loc['X1::heat_pump_cp_lt_exist::heat_hpcplt'].values
            self.tech_heat_pump_cp_lt.update_v_h(v_h_hpcplt)
            u_e_hpcplt = self.tech_heat_pump_cp_lt.get_u_e()

        else:            
            u_e_hpcplt = null_array.copy()

        # -------------------
        # Oil boiler (central plant):
        if 'oil_boiler_cp' in self.tech_list:
            v_h_obcp = opt_results['carrier_prod'].loc['X1::oil_boiler_cp_exist::heat_obcp'].values
            self.tech_oil_boiler_cp.update_v_h(v_h_obcp)
            # u_oil_obcp = self.tech_oil_boiler_cp.get_u_oil()
        
        # else:            
            # u_oil_obcp = null_array.copy()

        # -------------------
        # Electric heater (central plant):
        if 'electric_heater_cp' in self.tech_list:
            v_h_ehcp = opt_results['carrier_prod'].loc['X1::electric_heater_cp_exist::heat_ehcp'].values
            self.tech_electric_heater_cp.update_v_h(v_h_ehcp)
            u_e_ehcp = self.tech_electric_heater_cp.get_u_e()
        else:
            u_e_ehcp = null_array.copy()

        # -------------------
        # Wood boiler (central plant):
        if 'wood_boiler_cp' in self.tech_list:
            v_h_wbcp = opt_results['carrier_prod'].loc['X1::wood_boiler_cp_exist::heat_wbcp'].values
            self.tech_wood_boiler_cp.update_v_h(v_h_wbcp)

        # -------------------
        # Waste_heat
        if 'waste_heat' in self.tech_list:
            # rasa = opt_results['carrier_prod'].loc['X1::waste_heat_exists']
            # print(rasa)
            # exit()

            v_h_wh = opt_results['carrier_prod'].loc['X1::waste_heat_exists::heat_wh'].values
            self.tech_waste_heat.update_v_h(v_h_wh)

        # -------------------
        # Waste_heat_low_temperature
        if 'waste_heat_low_temperature' in self.tech_list:

            v_hlt_whlt = opt_results['carrier_prod'].loc['X1::waste_heat_low_temperature_exists::heatlt'].values
            self.tech_waste_heat_low_temperature.update_v_hlt(v_hlt_whlt)
            
        # -------------------
        # Gas boiler (central plant):
        if 'gas_boiler_cp' in self.tech_list:
            v_h_gbcp = opt_results['carrier_prod'].loc['X1::gas_boiler_cp_exist::heat_gbcp'].values
            self.tech_gas_boiler_cp.update_v_h(v_h_gbcp)

        # -------------------
        # Resources import:
        m_oil = (
            opt_results['carrier_prod'].loc['New_Techs::oil_supply::oil'].values
            + opt_results['carrier_prod'].loc['X1::oil_supply::oil'].values
            )
        m_gas = (
            opt_results['carrier_prod'].loc['New_Techs::gas_supply::gas'].values
            + opt_results['carrier_prod'].loc['X1::gas_supply::gas'].values
            )
        m_wd = (
            opt_results['carrier_prod'].loc['New_Techs::wood_supply_import::wood'].values
            + opt_results['carrier_prod'].loc['X1::wood_supply_import::wood'].values
            )
        self.supply.update_m_oil(m_oil)
        self.supply.update_m_gas(m_gas)
        self.supply.update_m_wd(m_wd)
        

        # -------------------
        # Demand:

        if (
                self.scen_techs['scenarios']['demand_side']
                and self.scen_techs['demand_side']['ev_integration']
                and self.scen_techs['demand_side']['ev_flexibility']
                ):
            
            d_e_ev = (
                -opt_results['carrier_con'].loc['X1::demand_electricity_ev_pd::electricity'].values
                -opt_results['carrier_con'].loc['X1::demand_electricity_ev_delta::electricity'].values
                )
            # tmp_dict = {
            #     'd_e_ev_pd':-opt_results['carrier_con'].loc['X1::demand_electricity_ev_pd::electricity'].values,
            #     'd_e_ev_delta':-opt_results['carrier_con'].loc['X1::demand_electricity_ev_delta::electricity'].values,
            #     'd_e_ev':d_e_ev,
            #     'd_e_ev_cp':self.energy_demand.get_d_e_ev_cp(),
            #     'flexibility_ev':opt_results['carrier_prod'].loc['X1::flexibility_ev::flexible_electricity'].values,
            #     }
            # tmp_df_ev = pd.DataFrame(tmp_dict)
            # tmp_df_ev.to_csv('tmp_results_for_testing/df_d_e_ev.csv')
        else:
            d_e_ev = -opt_results['carrier_con'].loc['X1::demand_electricity_ev::electricity'].values
        
        d_e = (
            -opt_results['carrier_con'].loc['X1::demand_electricity_hh::electricity'].values
            # -opt_results['carrier_con'].loc['X1::demand_electricity_ev::electricity'].values
            + d_e_ev
            + u_e_hp
            + u_e_eh
            + u_e_ehcp
            + u_e_hpcp
            + u_e_hpcplt
            + u_e_aguh
            + u_e_wgu
            + u_e_wguh
            + u_e_hydp
            )         
        d_e_hh = (
            -opt_results['carrier_con'].loc['X1::demand_electricity_hh::electricity'].values
            )        
        d_e_h = u_e_hp + u_e_eh + u_e_hpcp + u_e_hpcplt + u_e_ehcp
        d_h = -opt_results['carrier_con'].loc['X1::demand_heat::heat'].values        
        self.energy_demand.update_d_e(d_e)
        self.energy_demand.update_d_e_hh(d_e_hh)
        self.energy_demand.update_d_e_h(d_e_h)
        self.energy_demand.update_d_e_ev(d_e_ev)
        self.energy_demand.update_d_h(d_h)
        
        # Unmet demand:

        d_e_unmet = (
            opt_results['unmet_demand'].loc['X1::electricity'].values
            + opt_results['unmet_demand'].loc['New_Techs::electricity'].values
            )

        # if 'solar_pv' in self.tech_list:
        #     d_e_unmet = (
        #         opt_results['unmet_demand'].loc['X1::electricity'].values
        #         + opt_results['unmet_demand'].loc['Old_Solar_PV::electricity'].values
        #         + opt_results['unmet_demand'].loc['New_Techs::electricity'].values
        #         )
        # else:
        #     d_e_unmet = (
        #         opt_results['unmet_demand'].loc['X1::electricity'].values
        #         + opt_results['unmet_demand'].loc['New_Techs::electricity'].values
        #         )
            
        d_h_unmet = (
            opt_results['unmet_demand'].loc['X1::heat'].values
            # + opt_results['unmet_demand'].loc['X1::heat_tes'].values
            + opt_results['unmet_demand'].loc['New_Techs::heat'].values
            )
        
        d_h_unmet_dhn = np.array([0.0]*len(d_h_unmet))
        
        if 'district_heating' in self.tech_list:
            d_h_unmet_dhn += (
                opt_results['unmet_demand'].loc['X1::heat_dh'].values
                + opt_results['unmet_demand'].loc['X1::heat_dhimp'].values
                )
        
        if 'steam_turbine' in self.tech_list:
            d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_st'].values
            
        if 'tes' in self.tech_list:
            d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_tes'].values

        if 'tes_sites' in self.tech_list:

            for loc in self.tech_tes_sites.get_list_of_sitekeys():
                for x in loc:
                    if x.endswith("ht"):
                        d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_'+x].values

        if 'waste_to_energy' in self.tech_list:
            d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_wte'].values
            
        if 'heat_pump_cp' in self.tech_list:
            d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_hpcp'].values

        if 'heat_pump_cp_lt' in self.tech_list:
            d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_hpcplt'].values

        if 'oil_boiler_cp' in self.tech_list:
            d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_obcp'].values

        if 'electric_heater_cp' in self.tech_list:
            d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_ehcp'].values

        if 'wood_boiler_cp' in self.tech_list:
            d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_wbcp'].values

        if 'waste_heat' in self.tech_list:
            d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_wh'].values

        if 'gas_boiler_cp' in self.tech_list:
            d_h_unmet_dhn += opt_results['unmet_demand'].loc['X1::heat_gbcp'].values

        self.energy_demand.update_d_e_unmet(d_e_unmet)
        self.energy_demand.update_d_h_unmet(d_h_unmet)
        self.energy_demand.update_d_h_unmet_dhn(d_h_unmet_dhn)

        # -------------------
        # Electricity import:
        if 'grid_supply' in self.tech_list:
            m_e =\
                opt_results['carrier_prod'].loc['X1::grid_supply::electricity'].values
                
            # Recalculate electricity mix:
            self.tech_grid_supply.update_m_e(m_e)
        
        # -------------------
        # Thermal energy storage: # LOSSES TO BE ADDED
        if 'tes' in self.tech_list:
            v_h_tes = opt_results['carrier_prod'].loc['X1::tes::heat_tes'].values
            u_h_tes = -opt_results['carrier_con'].loc['X1::tes::heat_tes'].values
            q_h_tes = opt_results['storage'].loc['X1::tes'].values
            cap_tes = float(opt_results['storage_cap'].loc['X1::tes'].values)

            self.tech_tes.update_v_h(v_h_tes)
            self.tech_tes.update_u_h(u_h_tes)
            self.tech_tes.update_q_h(q_h_tes)
            if cap_tes > 0:
                self.tech_tes.update_sos(q_h_tes / cap_tes)
            else:
                self.tech_tes.update_sos(q_h_tes *0)
            self.tech_tes.update_cap(cap_tes)

# -------------------
        # Thermal energy storage sites: # LOSSES TO BE ADDED
        if 'tes_sites' in self.tech_list:

            list_of_sitekeys = self.tech_tes_sites.get_list_of_sitekeys()
            sites_list = self.tech_tes_sites.get_sites_list()


            for site_indexval in range(len(list_of_sitekeys)):
                sitekeys = list_of_sitekeys[site_indexval]
                for subsite in sitekeys:
                    t = subsite.split("_")[-1]

                    v_h_tessite = opt_results['carrier_prod'].loc['X1::'+subsite+'::heat_'+subsite].values
                    u_h_tessite = -opt_results['carrier_con'].loc['X1::'+subsite+'::heat_'+subsite].values
                    q_h_tessite = opt_results['storage'].loc['X1::'+subsite].values

                    cap_tessite = float(opt_results['storage_cap'].loc['X1::'+subsite].values)

                    

                    self.tech_tes_sites.set_u_h_site_type(u_h_tessite, site_indexval, t)
                    self.tech_tes_sites.set_v_h_site_type(v_h_tessite, site_indexval, t)
                    self.tech_tes_sites.set_q_h_site_type(q_h_tessite, site_indexval, t)

                    self.tech_tes_sites.set_cap_site_type(cap_tessite, site_indexval, t)
                    if subsite[-4:] == 'ltlt':

                        name = sites_list[site_indexval]['name']
                        u_hht_to_hlt = (opt_results['carrier_prod'].loc['X1::conv_'+name+'_htht_to_'+name+'_ltlt::heat_'+subsite]
                         +opt_results['carrier_prod'].loc['X1::conv_'+name+'_htlt_to_'+name+'_ltlt::heat_'+subsite])
                        self.tech_tes_sites.set_u_hht_to_hlt(
                            u_hht_to_hlt+self.tech_tes_sites.get_u_hht_to_hlt(site_indexval)
                            , site_indexval)
                    if subsite[-4:] == 'htlt':
                        name = sites_list[site_indexval]['name']
                        
                        u_hht_to_hlt = opt_results['carrier_prod'].loc['X1::conv_'+name+'_lt_to_'+'heatlt_htlt::heatlt']-v_h_tessite
                        self.tech_tes_sites.set_u_hht_to_hlt(
                            u_hht_to_hlt+self.tech_tes_sites.get_u_hht_to_hlt(site_indexval)
                            , site_indexval)



                    self.tech_tes_sites.update_soc_site_type(site_indexval, t)
                    self.tech_tes_sites.update_losses_site_type(site_indexval, t)


        # -------------------
        # Thermal energy storage - decentralised: # LOSSES TO BE ADDED
        if 'tes_decentralised' in self.tech_list:
            v_h_tesdc = opt_results['carrier_prod'].loc['X1::tes_decentralised::heat_tesdc'].values
            u_h_tesdc = -opt_results['carrier_con'].loc['X1::tes_decentralised::heat_tesdc'].values
            q_h_tesdc = opt_results['storage'].loc['X1::tes_decentralised'].values
            cap_tesdc = float(opt_results['storage_cap'].loc['X1::tes_decentralised'].values)

            self.tech_tes_decentralised.update_v_h(v_h_tesdc)
            self.tech_tes_decentralised.update_u_h(u_h_tesdc)
            self.tech_tes_decentralised.update_q_h(q_h_tesdc)
            if cap_tesdc > 0:
                self.tech_tes_decentralised.update_sos(q_h_tesdc / cap_tesdc)
            else:
                self.tech_tes_decentralised.update_sos(q_h_tesdc * 0)
            self.tech_tes_decentralised.update_cap(cap_tesdc)
        # -------------------
        # Battery energy storage:
        if 'bes' in self.tech_list:
            v_e_bes = opt_results['carrier_prod'].loc['X1::bes::electricity'].values
            u_e_bes = -opt_results['carrier_con'].loc['X1::bes::electricity'].values
            q_e_bes = opt_results['storage'].loc['X1::bes'].values
            cap_bes = float(opt_results['storage_cap'].loc['X1::bes'].values)

            self.tech_bes.update_v_e(v_e_bes)
            self.tech_bes.update_u_e(u_e_bes)
            self.tech_bes.update_q_e(q_e_bes)
            if cap_bes > 0:
                self.tech_bes.update_sos(q_e_bes / cap_bes)
            else:
                self.tech_bes.update_sos(q_e_bes *0)
            self.tech_bes.update_cap(cap_bes)

        # -------------------
        # Gas tank energy storage:
        if 'gtes' in self.tech_list:
            v_gas_gtes = opt_results['carrier_prod'].loc['X1::gtes::gas'].values
            u_gas_gtes = -opt_results['carrier_con'].loc['X1::gtes::gas'].values
            q_gas_gtes = opt_results['storage'].loc['X1::gtes'].values
            cap_gtes = float(opt_results['storage_cap'].loc['X1::gtes'].values)

            self.tech_gtes.update_v_gas(v_gas_gtes)
            self.tech_gtes.update_u_gas(u_gas_gtes)
            self.tech_gtes.update_q_gas(q_gas_gtes)
            if cap_gtes > 0:
                self.tech_gtes.update_sos(q_gas_gtes / cap_gtes)
            else:
                self.tech_gtes.update_sos(q_gas_gtes * 0)
            self.tech_gtes.update_cap(cap_gtes)

        # -------------------
        # Wood storage:
        if 'ws' in self.tech_list:
            v_wd_ws = opt_results['carrier_prod'].loc['X1::ws::wood'].values
            u_wd_ws = -opt_results['carrier_con'].loc['X1::ws::wood'].values
            q_wd_ws = opt_results['storage'].loc['X1::ws'].values
            cap_ws = float(opt_results['storage_cap'].loc['X1::ws'].values)

            self.tech_ws.update_v_wd(v_wd_ws)
            self.tech_ws.update_u_wd(u_wd_ws)
            self.tech_ws.update_q_wd(q_wd_ws)
            if cap_ws > 0:
                self.tech_ws.update_sos(q_wd_ws / cap_ws)
            else:
                self.tech_ws.update_sos(q_wd_ws * 0)
            self.tech_ws.update_cap(cap_ws)


        # -------------------
        # Hydrogen energy storage:
        if 'hes' in self.tech_list:

            # print(opt_results['carrier_prod'])
            # exit()

            v_hyd_hes = opt_results['carrier_prod'].loc['New_Techs::hes::hydrogen'].values
            u_hyd_hes = -opt_results['carrier_con'].loc['New_Techs::hes::hydrogen'].values
            q_hyd_hes = opt_results['storage'].loc['New_Techs::hes'].values
            cap_hes = float(opt_results['storage_cap'].loc['New_Techs::hes'].values)

            self.tech_hes.update_v_hyd(v_hyd_hes)
            self.tech_hes.update_u_hyd(u_hyd_hes)
            self.tech_hes.update_q_hyd(q_hyd_hes)
            if cap_hes > 0:
                self.tech_hes.update_sos(q_hyd_hes / cap_hes)
            else:
                self.tech_hes.update_sos(q_hyd_hes *0)

            self.tech_hes.update_cap(cap_hes)

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
        
        return dict_total_costs
    
    # def __build_input_dict(self, rerun_eps=False, eps_n='inf'):
    def __build_input_dict(self):
        
        model_dict = self.__create_model_dict()
        tech_groups_dict = self.__create_tech_groups_dict()
        techs_dict = self.__create_techs_dict()
        loc_dict = self.__create_location_dict()
        links_dict = self.__create_links_dict()
        run_dict = self.__create_run_dict()
        group_constraints_dict = self.__create_group_constraints_dict()
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
            'group_constraints':group_constraints_dict,#{
            #     'constant_heat_sources':{
            #             'techs':[
            #                 'heat_pump_old',
            #                 'heat_pump_new',
            #                 'electric_heater_old',
            #                 'oil_boiler_old',
            #                 'oil_boiler_new',
            #                 'gas_boiler_old',
            #                 'gas_boiler_new',
            #                 'wood_boiler_old',
            #                 'wood_boiler_new',
            #                 'district_heating',
            #                 ], # ensure techs are spelled correctly!
            #             'locs':['New_Techs', 'X1',],
            #             'demand_share_per_timestep_decision':{
            #                 'heat':None, # if set to 'None', the optimiser chooses a constant value; if a value is given (e.g. 0.2), this value will be used as constant share
            #                 },
            #             },
            # #     'new_oil_boiler_share':{
            # #         'techs':['oil_boiler_new', 'chp_gt_new'], # ensure techs are spelled correctly!
            # #         'locs':['New_Techs', 'X1'],
            # #         'demand_share_per_timestep_decision':{
            # #             'heat':None, # if set to 'None', the optimiser chooses a constant value; if a value is given (e.g. 0.2), this value will be used as constant share
            # #             },
            # #         },
            # #     'old_oil_boiler_share':{
            # #         'techs':['oil_boiler_old'],
            # #         'locs':['New_Techs', 'X1'],
            # #         'demand_share_per_timestep_equals':{
            # #             'heat':0.0,
            # #             },
            # #         },
            # #     'systemwide_co2_cap':{
            # #         'cost_max':{
            # #             'emissions_co2':3.5e6,
            # #             }
            # #         },
            #     }
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
            'waste_heat': '#918686',
            'waste_heat_low_temperature': "#9BBAC9"
            }
        
        techs_dict = {}
        
        # Add demands: # !!! ADD THESE TO DEMAND CLASS?
        techs_dict['demand_electricity_hh'] = {
            'essentials':{
                'name':'Electrical Demand Household',
                'color':colors['demand_electricity'],
                'parent':'demand',
                'carrier':'electricity'
                },
            }
        
        if (
                self.scen_techs['scenarios']['demand_side']
                and self.scen_techs['demand_side']['ev_integration']
                and self.scen_techs['demand_side']['ev_flexibility']
                ):
            
            techs_dict['demand_electricity_ev_pd'] = {
                'essentials':{
                    'name':'Electrical Demand EV - lower bound',
                    'color':colors['demand_electricity'],
                    'parent':'demand',
                    'carrier':'electricity'
                    },
                'constraints':{
                    'force_resource': True,
                    }
                }
            techs_dict['demand_electricity_ev_delta'] = { # Difference between upper and lower bound
                'essentials':{
                    'name':'Electrical Demand EV - delta',
                    'color':colors['demand_electricity'],
                    'parent':'demand',
                    'carrier':'electricity'
                    },
                'constraints':{
                    'force_resource': False,
                    }                
                }
            
            # Virtual variable to quantify flexibility from EV:
            techs_dict['flexibility_ev'] = {
                'essentials':{
                    'name':'EV Flexibility',
                    'color':colors['demand_electricity'],
                    'parent':'supply',
                    'carrier':'flexible_electricity',
                    },
                'constraints':{
                    'force_resource':False,
                    'energy_prod':True,
                    'export_carrier': 'flexible_electricity',
                    },
                'costs':{
                    'monetary':{
                        'om_con':0.0,
                        'interest_rate':0.0
                        },
                    'emissions_co2':{
                        'om_prod':0.0
                        }
                    }
                }
            
        else:
            techs_dict['demand_electricity_ev'] = {
                'essentials':{
                    'name':'Electrical Demand Electric Vehicles',
                    'color':colors['demand_electricity'],
                    'parent':'demand',
                    'carrier':'electricity'
                    },
                'constraints':{
                    'force_resource': True,
                    }
                }
        
        techs_dict['demand_heat'] = {
            'essentials':{
                'name':'Heat Demand',
                'color':colors['demand_heat'],
                'parent':'demand',
                'carrier':'heat'
                }
            }
        
        #Add Supplies:        
        techs_dict = self.supply.create_supply_dict_wet_biomass(techs_dict)
        techs_dict = self.supply.create_supply_dict_wood(techs_dict)
        techs_dict = self.supply.create_supply_dict_oil(
            techs_dict, 
            color = colors['oil_supply']
            )
        techs_dict = self.supply.create_supply_dict_gas(
            techs_dict, 
            color = colors['gas_supply']
            )
        techs_dict = self.supply.create_supply_dict_wood_import(techs_dict)
        
        if 'waste_to_energy' in self.tech_list:
            # resource_msw = self.tech_waste_to_energy.get_annual_msw_supply_kWh()
            techs_dict = self.supply.create_supply_dict_msw(
                techs_dict,
                color=colors['waste_to_energy'],
                # resource=resource_msw
                )
            self.tech_list_old.append('msw_supply')
        
        self.tech_list_old.append('oil_supply')
        self.tech_list_new.append('oil_supply')
        self.tech_list_old.append('gas_supply')
        self.tech_list_new.append('gas_supply')
        self.tech_list_old.append('wood_supply_import')
        self.tech_list_new.append('wood_supply_import')
        
        # Add user-selected techologies:
        if 'heat_pump' in self.tech_list:
            energy_cap_old = self.tech_heat_pump.get_v_h().max()
            needs_replacement = self.tech_heat_pump.get_power_up_for_replacement()

            energy_cap_zero_capex = energy_cap_old-needs_replacement if energy_cap_old>=needs_replacement else 0.0
            energy_cap_low_capex = needs_replacement if energy_cap_old>=needs_replacement else energy_cap_old
            
            if self.tech_heat_pump.get_only_allow_existing():
                cap_one_to_one_replacement = 0.0
                cap_new = 0.0
            else:
                cap_one_to_one_replacement = energy_cap_low_capex
                if self.tech_heat_pump._v_h_max == 'inf':
                    cap_new = 'inf'
                else:
                    cap_new = self.tech_heat_pump._v_h_max - cap_one_to_one_replacement - energy_cap_zero_capex
            
            if self.tech_heat_pump._v_h_max != 'inf':
                if cap_new < 0.0:
                    cap_one_to_one_replacement += cap_new
                    cap_new = 0.0
                if cap_one_to_one_replacement < 0.0:
                    energy_cap_zero_capex += cap_one_to_one_replacement
                    cap_one_to_one_replacement = 0.0
                if energy_cap_zero_capex <= 0.0:
                    energy_cap_zero_capex = 0.0

            techs_dict, additional_techs_label = self.tech_heat_pump.create_techs_dict(
                techs_dict, 
                header = 'heat_pump_old', 
                name = 'Heat Pump Old', 
                color = colors['heat_pump'],
                energy_cap = energy_cap_zero_capex,
                create_tesdc_hp_hub = True,
                capex_level = 'zero')
            

            techs_dict, _ = self.tech_heat_pump.create_techs_dict(
                techs_dict, 
                header = 'heat_pump_one_to_one_replacement', 
                name = 'Heat Pump One-to-One-Replacement', 
                color = colors['heat_pump'],
                energy_cap = cap_one_to_one_replacement,
                capex_level = 'one-to-one-replacement')                
            self.tech_list_old.append('heat_pump_one_to_one_replacement')

            
            techs_dict, _ = self.tech_heat_pump.create_techs_dict(
                techs_dict, 
                header = 'heat_pump_new', 
                name = 'Heat Pump New', 
                color = colors['heat_pump'],
                energy_cap = cap_new,
                )
                        
            self.tech_list_old.append('heat_pump_old')
            self.tech_list_old = self.tech_list_old + additional_techs_label
            self.tech_list_new.append('heat_pump_new')

        if 'electric_heater' in self.tech_list:
            energy_cap_old = self.tech_electric_heater.get_v_h().max()
            needs_replacement = self.tech_electric_heater.get_power_up_for_replacement()

            energy_cap_eh = energy_cap_old-needs_replacement if energy_cap_old > needs_replacement else 0

            techs_dict = self.tech_electric_heater.create_techs_dict(
                    techs_dict, 
                    header = 'electric_heater_old', 
                    name = 'Electric Heater Old', 
                    color = colors['electric_heater'],
                    energy_cap = energy_cap_eh,
                    capex_0 = True)
            
            self.tech_list_old.append('electric_heater_old')
           
        if 'oil_boiler' in self.tech_list:

            energy_cap_old = self.tech_oil_boiler.get_v_h().max()
            needs_replacement = self.tech_oil_boiler.get_power_up_for_replacement()

            energy_cap_zero_capex = energy_cap_old-needs_replacement if energy_cap_old>=needs_replacement else 0.0
            energy_cap_low_capex = needs_replacement if energy_cap_old>=needs_replacement else energy_cap_old

            techs_dict = self.tech_oil_boiler.create_techs_dict(
                techs_dict, 
                header = 'oil_boiler_old', 
                name = 'Oil Boiler Old', 
                color = colors['oil_boiler'],
                energy_cap = energy_cap_zero_capex,
                capex_level = 'zero')
            
            if self.tech_oil_boiler.get_only_allow_existing():
                cap_one_to_one_replacement = 0.0
            else:
                cap_one_to_one_replacement = energy_cap_low_capex

            
            techs_dict = self.tech_oil_boiler.create_techs_dict(
                techs_dict, 
                header = 'oil_boiler_one_to_one_replacement', 
                name = 'Oil Boiler One-to-One-Replacement', 
                color = colors['oil_boiler'],
                energy_cap = cap_one_to_one_replacement,
                capex_level = 'one-to-one-replacement')                
            self.tech_list_old.append('oil_boiler_one_to_one_replacement')


            if self.tech_oil_boiler.get_only_allow_existing():
                cap_new = 0.0
            else:
                cap_new = 'inf'
            
            techs_dict = self.tech_oil_boiler.create_techs_dict(
                techs_dict, 
                header = 'oil_boiler_new', 
                name = 'Oil Boiler New', 
                color = colors['oil_boiler'],
                energy_cap = cap_new,
                capex_level = 'full'
                )
            
            self.tech_list_old.append('oil_boiler_old')
            self.tech_list_new.append('oil_boiler_new')
                 
        if 'gas_boiler' in self.tech_list:
            
            energy_cap_old = self.tech_gas_boiler.get_v_h().max()
            needs_replacement = self.tech_gas_boiler.get_power_up_for_replacement()

            energy_cap_zero_capex = energy_cap_old-needs_replacement if energy_cap_old>=needs_replacement else 0.0
            energy_cap_low_capex = needs_replacement if energy_cap_old>=needs_replacement else energy_cap_old


            techs_dict = self.tech_gas_boiler.create_techs_dict(
                techs_dict, 
                header = 'gas_boiler_old', 
                name = 'Gas Boiler Old', 
                color = colors['gas_boiler'],
                energy_cap = energy_cap_zero_capex,
                capex_level = 'zero')
            
            if self.tech_gas_boiler.get_only_allow_existing():
                cap_one_to_one_replacement = 0.0
            else:
                cap_one_to_one_replacement = energy_cap_low_capex

            techs_dict = self.tech_gas_boiler.create_techs_dict(
                techs_dict, 
                header = 'gas_boiler_one_to_one_replacement', 
                name = 'Gas Boiler One-to-One-Replacement', 
                color = colors['gas_boiler'],
                energy_cap = cap_one_to_one_replacement,
                capex_level = 'one-to-one-replacement')                
            self.tech_list_old.append('gas_boiler_one_to_one_replacement')


            if self.tech_gas_boiler.get_only_allow_existing():
                cap_new = 0.0
            else:
                cap_new = 'inf'
            
            techs_dict = self.tech_gas_boiler.create_techs_dict(
                techs_dict, 
                header = 'gas_boiler_new', 
                name = 'Gas Boiler New', 
                color = colors['gas_boiler'],
                energy_cap = cap_new,
                )
            
            self.tech_list_old.append('gas_boiler_old')
            self.tech_list_new.append('gas_boiler_new')
           
        if 'wood_boiler' in self.tech_list:
            
            energy_cap_old = self.tech_wood_boiler.get_v_h().max()
            needs_replacement = self.tech_wood_boiler.get_power_up_for_replacement()

            energy_cap_zero_capex = energy_cap_old-needs_replacement if energy_cap_old>=needs_replacement else 0.0
            energy_cap_low_capex = needs_replacement if energy_cap_old>=needs_replacement else energy_cap_old


            techs_dict = self.tech_wood_boiler.create_techs_dict(
                techs_dict, 
                header = 'wood_boiler_old', 
                name = 'Wood Boiler Old', 
                color = colors['wood_boiler'],
                energy_cap = energy_cap_zero_capex,
                capex_level = 'zero')

            if self.tech_wood_boiler.get_only_allow_existing():
                cap_one_to_one_replacement = 0.0
            else:
                cap_one_to_one_replacement = energy_cap_low_capex

            techs_dict = self.tech_wood_boiler.create_techs_dict(
                techs_dict, 
                header = 'wood_boiler_one_to_one_replacement', 
                name = 'Wood Boiler One-to-One-Replacement', 
                color = colors['wood_boiler'],
                energy_cap = cap_one_to_one_replacement,
                capex_level = 'one-to-one-replacement')                
            self.tech_list_old.append('wood_boiler_one_to_one_replacement')
    
            if self.tech_wood_boiler.get_only_allow_existing():
                cap_new = 0.0
            else:
                cap_new = 'inf'
            
            techs_dict = self.tech_wood_boiler.create_techs_dict(
                techs_dict, 
                header = 'wood_boiler_new', 
                name = 'Wood Boiler New', 
                color = colors['wood_boiler'],
                energy_cap = cap_new,
                capex_level = 'full'
                )
            
            self.tech_list_old.append('wood_boiler_old')
            self.tech_list_new.append('wood_boiler_new')
             
        if 'district_heating' in self.tech_list:
            techs_dict, dh_techs_label_list =\
                self.tech_district_heating.create_techs_dict(
                    techs_dict,
                    color=colors['district_heating']
                    )
            
            self.tech_list_old = self.tech_list_old + dh_techs_label_list
            
        # if 'solar_thermal' in self.tech_list:            
        #     energy_cap_old = self.tech_solar_thermal.get_v_h().max()
            
        #     techs_dict = self.tech_solar_thermal.create_techs_dict(techs_dict,
        #                           header = 'solar_thermal_old',
        #                           name = 'Solar Thermal Old', 
        #                           color = colors['solar_thermal'], 
        #                           resource = 'df=solar_th_resource_old:v_h_solar_th',
        #                           energy_cap = energy_cap_old,
        #                           capex_0 = True
        #                           )
            
        #     techs_dict = self.tech_solar_thermal.create_techs_dict(techs_dict,
        #                           header = 'solar_thermal_new',
        #                           name = 'Solar Thermal New', 
        #                           color = colors['solar_thermal'], 
        #                           resource = 'df=solar_th_resource_new:v_h_solar_th',
        #                           energy_cap = 'inf',
        #                           )
            
        #     self.tech_list_old.append('solar_thermal_old')
        #     self.tech_list_new.append('solar_thermal_new')
            
        # if 'solar_pv' in self.tech_list:            
        #     energy_cap_old = self.tech_solar_pv.get_v_e().max()
            
        #     techs_dict = self.tech_solar_pv.create_techs_dict(techs_dict,
        #                           header = 'solar_pv_old',
        #                           name = 'Solar PV Old', 
        #                           color = colors['solar_pv'], 
        #                           resource = 'df=pv_resource_old:v_e_pv',
        #                           energy_cap = energy_cap_old,
        #                           capex_0 = True
        #                           )
            
        #     # Force deployment of currently installed systems:
        #     techs_dict['solar_pv_old']['constraints.energy_cap_equals'] =\
        #         energy_cap_old
            
        #     self.tech_list_old.append('solar_pv_old')
            
        #     if self.tech_solar_pv.get_only_use_installed():
        #         pass
        #     else:      
        #         techs_dict = self.tech_solar_pv.create_techs_dict(techs_dict,
        #                               header = 'solar_pv_new',
        #                               name = 'Solar PV New',
        #                               color = colors['solar_pv'],
        #                               resource = 'df=pv_resource_new:v_e_pv',
        #                               energy_cap = 'inf',
        #                               )
                
        #         self.tech_list_new.append('solar_pv_new')

        if 'solar_pvrooftop' in self.tech_list:
            
            print(self.tech_solar_pvrooftop.get_num_installations())

            techs_dict, headers = self.tech_solar_pvrooftop.create_techs_dict(techs_dict,
                                                                              color = colors['solar_pv'],
                                                                              resources = [
                                                                                  'df='+'pvrooftop_resource'+':'+'v_e_pvrooftop_'+str(i) 
                                                                                  for i in range(self.tech_solar_pvrooftop.get_num_installations())]
                                                                              )
            
            self.tech_list_pv.append(headers)

        if 'solarthermal_rooftop' in self.tech_list:
            
            print(self.tech_solarthermal_rooftop.get_num_installations())

            techs_dict, headers = self.tech_solarthermal_rooftop.create_techs_dict(techs_dict,
                                                                              color = colors['solar_thermal'],
                                                                              resources = [
                                                                                  'df='+'solarthermalrooftop_resource'+':'+'v_h_solarthermalrooftop_'+str(i) 
                                                                                  for i in range(self.tech_solarthermal_rooftop.get_num_installations())]
                                                                              )
            
            self.tech_list_solarthermal.append(headers)


        if 'wind_power' in self.tech_list:
            
            techs_dict = self.tech_wind_power.create_techs_dict_unit(
                techs_dict,
                colors['wind_power'],
                )

            techs_dict = self.tech_wind_power.create_techs_dict(
                techs_dict = techs_dict,
                header = 'wind_power_old',
                name = 'Wind Power Old',
                color = colors['wind_power'],
                export_cost=0, # subsidy for feed-in; used to prefer wind over hydro
                capex_0 = True,
                
                )
            
            techs_dict = self.tech_wind_power.create_techs_dict(
                techs_dict = techs_dict,
                header = 'wind_power_new',
                name = 'Wind Power New',
                color = colors['wind_power'],
                export_cost=0.0
                )                

            self.tech_list_old.append('wind_power_old')
            self.tech_list_new.append('wind_power_new')
            
        if 'hydro_power' in self.tech_list:
            energy_cap = self.tech_hydro_power.get_v_e().max()
            
            techs_dict = self.tech_hydro_power.create_techs_dict(
                techs_dict=techs_dict,
                header = 'hydro_power',
                name = 'Hydro Power',
                color = colors['hydro_power'],
                resource = 'df=hydro_resource:v_e_hydro',
                energy_cap = energy_cap,
                capex_0 = True
                )
            
            # Force deployment of currently installed systems:
            techs_dict['hydro_power']['constraints.energy_cap_equals'] =\
                energy_cap
            
            self.tech_list_old.append('hydro_power')
            
        if 'grid_supply' in self.tech_list:
            techs_dict = self.tech_grid_supply.create_techs_dict(
                techs_dict,
                colors['grid_supply']
                )
            
            self.tech_list_old.append('grid_supply')
            
        if 'tes' in self.tech_list:
            techs_dict, tes_techs_label_list = self.tech_tes.create_techs_dict(
                techs_dict,
                colors['tes']
                )
            
            self.tech_list_old = self.tech_list_old + tes_techs_label_list

        if 'tes_sites' in self.tech_list:
            techs_dict, tes_sites_techs_label_list = self.tech_tes_sites.create_techs_dict(
                techs_dict,
                colors['tes']
                )
            
            self.tech_list_old = self.tech_list_old + tes_sites_techs_label_list

        if 'tes_decentralised' in self.tech_list:
            techs_dict, tesdc_techs_label_list = self.tech_tes_decentralised.create_techs_dict(
                techs_dict,
                colors['tes_decentralised']
                )
            
            self.tech_list_old = self.tech_list_old + tesdc_techs_label_list
             
        if 'bes' in self.tech_list:
            techs_dict = self.tech_bes.create_techs_dict(
                techs_dict,
                colors['bes']
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
                colors['gtes']
                )
            self.tech_list_old.append('gtes')

        if 'ws' in self.tech_list:
            techs_dict = self.tech_ws.create_techs_dict(
                techs_dict,
                colors['ws']
                )
            self.tech_list_old.append('ws')


        if 'hes' in self.tech_list:
            techs_dict = self.tech_hes.create_techs_dict(
                techs_dict,
                colors['hes']
                )
            self.tech_list_new.append('hes')

        if 'hydrothermal_gasification' in self.tech_list:
            techs_dict = self.tech_hydrothermal_gasification.generate_tech_dict(techs_dict)
            
            self.tech_list_new.append('hydrothermal_gasification')
        
        if 'anaerobic_digestion_upgrade' in self.tech_list:
            techs_dict = self.tech_anaerobic_digestion_upgrade.generate_tech_dict(techs_dict)
            
            self.tech_list_new.append('anaerobic_digestion_upgrade')
            
        if 'anaerobic_digestion_upgrade_hydrogen' in self.tech_list:
            techs_dict = self.tech_anaerobic_digestion_upgrade_hydrogen.generate_tech_dict(techs_dict)
            
            self.tech_list_new.append('anaerobic_digestion_upgrade_hydrogen')
            
        if 'anaerobic_digestion_chp' in self.tech_list:
            techs_dict = self.tech_anaerobic_digestion_chp.generate_tech_dict(techs_dict)
            
            self.tech_list_new.append('anaerobic_digestion_chp')
        
        if 'wood_gasification_upgrade' in self.tech_list:
            techs_dict = self.tech_wood_gasification_upgrade.generate_tech_dict(techs_dict)
            
            self.tech_list_new.append('wood_gasification_upgrade')
            
        if 'wood_gasification_upgrade_hydrogen' in self.tech_list:
            techs_dict = self.tech_wood_gasification_upgrade_hydrogen.generate_tech_dict(techs_dict)
            
            self.tech_list_new.append('wood_gasification_upgrade_hydrogen')
            
        if 'wood_gasification_chp' in self.tech_list:
            techs_dict = self.tech_wood_gasification_chp.generate_tech_dict(techs_dict)
            
            self.tech_list_new.append('wood_gasification_chp')
            
        if 'hydrogen_production' in self.tech_list:
            techs_dict = self.tech_hydrogen_production.generate_tech_dict(techs_dict)
            
            self.tech_list_new.append('hydrogen_production')
            
        if 'chp_gt' in self.tech_list:            
            techs_dict = self.tech_chp_gt.create_techs_dict(
                techs_dict=techs_dict,
                header='chp_gt_new',
                name='CHP Gas Turbine New',
                color=colors['chp_gt']
                )            
            
            self.tech_list_old.append('chp_gt_new')
            
        if 'gas_turbine_cp' in self.tech_list:
            techs_dict = self.tech_gas_turbine_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='gas_turbine_cp_exist',
                name='Gas Turbine (central plant)',
                color=colors['gas_turbine_cp']
                )
            
            self.tech_list_old.append('gas_turbine_cp_exist')
            
        if 'steam_turbine' in self.tech_list:
            techs_dict = self.tech_steam_turbine.create_techs_dict(
                techs_dict=techs_dict,
                header='steam_turbine_exist',
                name='Steam Turbine',
                color=colors['steam_turbine']
                )
            
            self.tech_list_old.append('steam_turbine_exist')
            
        if 'wood_boiler_sg' in self.tech_list:
            techs_dict = self.tech_wood_boiler_sg.create_techs_dict(
                techs_dict=techs_dict,
                header='wood_boiler_sg_exist',
                name='Wood boiler (steam generator)',
                color=colors['wood_boiler_sg']
                )
            
            self.tech_list_old.append('wood_boiler_sg_exist')
            
        if 'waste_to_energy' in self.tech_list:
            techs_dict = self.tech_waste_to_energy.create_techs_dict(
                techs_dict=techs_dict,
                header='waste_to_energy_exist',
                name='Waste-to-Energy',
                color=colors['waste_to_energy']
                )
            
            self.tech_list_old.append('waste_to_energy_exist')
            
        if 'heat_pump_cp' in self.tech_list:
            techs_dict = self.tech_heat_pump_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='heat_pump_cp_exist',
                name='Heat pump (central plant)',
                color=colors['heat_pump_cp'],
                )
            
            self.tech_list_old.append('heat_pump_cp_exist')

            
        if 'heat_pump_cp_lt' in self.tech_list:
            techs_dict = self.tech_heat_pump_cp_lt.create_techs_dict(
                techs_dict=techs_dict,
                header='heat_pump_cp_lt_exist',
                name='Heat pump (central plant, from low temperature heat)',
                color=colors['heat_pump_cp_lt'],
                )
            
            self.tech_list_old.append('heat_pump_cp_lt_exist')

        if 'oil_boiler_cp' in self.tech_list:
            techs_dict = self.tech_oil_boiler_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='oil_boiler_cp_exist',
                name='Oil boiler (central plant)',
                color=colors['oil_boiler_cp'],
                )
            
            self.tech_list_old.append('oil_boiler_cp_exist')
 
        if 'electric_heater_cp' in self.tech_list:
            techs_dict = self.tech_electric_heater_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='electric_heater_cp_exist',
                name='Electric Heater (central plant)',
                color=colors['electric_heater_cp'],
                )
            
            self.tech_list_old.append('electric_heater_cp_exist')

        if 'wood_boiler_cp' in self.tech_list:
            techs_dict = self.tech_wood_boiler_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='wood_boiler_cp_exist',
                name='Wood boiler (central plant)',
                color=colors['wood_boiler_cp'],
                )
            
            self.tech_list_old.append('wood_boiler_cp_exist')

        if 'waste_heat' in self.tech_list:
            techs_dict = self.tech_waste_heat.create_techs_dict(
                techs_dict=techs_dict,
                header='waste_heat_exists',
                name='Waste heat (source)',
                color=colors['waste_heat'],
                resource="df=waste_heat:v_h_wh"
                )
            
            self.tech_list_old.append('waste_heat_exists')

        if 'waste_heat_low_temperature' in self.tech_list:
            techs_dict = self.tech_waste_heat_low_temperature.create_techs_dict(
                techs_dict=techs_dict,
                header='waste_heat_low_temperature_exists',
                name='Waste heat (source at low temperature)',
                color=colors['waste_heat_low_temperature'],
                resource="df=waste_heat_low_temperature:v_hlt_whlt"
                )
            
            self.tech_list_old.append('waste_heat_low_temperature_exists')

        if 'gas_boiler_cp' in self.tech_list:
            techs_dict = self.tech_gas_boiler_cp.create_techs_dict(
                techs_dict=techs_dict,
                header='gas_boiler_cp_exist',
                name='Gas boiler (central plant)',
                color=colors['gas_boiler_cp'],
                )
            
            self.tech_list_old.append('gas_boiler_cp_exist')

        # Add connections (i.e. transmission lines):
        techs_dict = self.__techs_dict_add_power_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_heat_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_heat_biomass_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_hp_heat_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_gas_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_wood_line(techs_dict, colors)
        techs_dict = self.__techs_dict_add_wet_biomass_line(techs_dict, colors)
   
        return techs_dict
        
    def __create_location_dict(self):
        
        # Techs with separate locations:
        tech_locs = ['wind_power_old', 'wind_power_new']#, 'solar_thermal_old', 'solar_pv_old']
        
        # Dictionary to be populated for main location X1:
        loc_dict = {
            'X1':{
                'techs':{
                    'demand_electricity_hh':{},
                    # 'demand_electricity_ev':{},
                    'demand_heat':{}
                    },
                # 'available_area': 1, # used for "resources competition" between pv and solar thermal; a virtual value of 1 is used.
                'coordinates':{} 
                },
            'New_Techs':{
                'techs':{},
                # 'available_area': self.available_area_scaling, # used for "resources competition" between pv and solar thermal; a virtual value of 1 is used.
                'coordinates':{
                  'lat': 5,
                  'lon': 5
                  }
                },
            'Limited_Supplies':{
                'techs':{
                    'wet_biomass_supply':{},
                    'wood_supply':{}
                    },
                'coordinates':{
                    'lat': 6,
                    'lon':6
                    }
                }
                    }
        
        if (
                self.scen_techs['scenarios']['demand_side']
                and self.scen_techs['demand_side']['ev_integration']
                and self.scen_techs['demand_side']['ev_flexibility']
                ):
            
            loc_dict['X1']['techs']['demand_electricity_ev_pd'] = {}
            loc_dict['X1']['techs']['demand_electricity_ev_delta'] = {}
            loc_dict['X1']['techs']['flexibility_ev'] = {}

        else:
            loc_dict['X1']['techs']['demand_electricity_ev'] = {}
        
        # if 'solar_thermal' in self.tech_list:
        #     loc_dict['Old_Solar_Thermal'] = {
        #         'techs':{},
        #         'available_area': self.available_area_scaling, # used for "resources competition" between pv and solar thermal; a virtual value of 1 is used.
        #         'coordinates':{
        #             'lat': 3,
        #             'lon': 3
        #             }
        #         }
        
        # if 'solar_pv' in self.tech_list:
        #     loc_dict['Old_Solar_PV'] = {
        #         'techs':{},
        #         'available_area': self.available_area_scaling, # used for "resources competition" between pv and solar thermal; a virtual value of 1 is used.
        #         'coordinates':{
        #           'lat': 3,
        #           'lon': 4
        #           }
        #         }
        
        if len(self.tech_list_pv) > 0:
            for i in range(len(self.tech_list_pv)):
                for j in range(len(self.tech_list_pv[i])):
                    loc_dict[self.tech_list_pv[i][j]] = {
                        'techs': {},
                        'available_area': self.available_area_scaling,
                        'coordinates':{
                            'lat': 10+i,
                            'lon': j
                            }
                    }

        # ---------------------------------------------------------------------
        # Populate loc_dict for main location X1:
        for tech in self.tech_list_old:
            if tech in tech_locs:
                # This tech will have a separate location
                pass
            else:
                loc_dict['X1']['techs'][tech] = None
        for tech in self.tech_list_new:
            if tech in tech_locs:
                # This tech will have a separate location
                pass
            else:
                loc_dict['New_Techs']['techs'][tech] = None
        for i in range(len(self.tech_list_pv)):

            techs = self.tech_list_pv[i]

            for j in range(len(techs)):

                tech = techs[j]
                tech_thermal = self.tech_list_solarthermal[i][j]

                print(tech)
                loc_dict[tech]['techs'][tech+"_occupied"] = None
                loc_dict[tech]['techs'][tech+"_unoccupied"] = None

                loc_dict[tech]['techs'][tech_thermal+"_occupied"] = None
                loc_dict[tech]['techs'][tech_thermal+"_unoccupied"] = None



        # Update loc_dict with timeseries
        # loc_dict['X1']['techs']['demand_electricity']['constraints.resource'] =\
        #     'df=demand_power:d_e_hh'
        loc_dict['X1']['techs']['demand_electricity_hh']['constraints.resource'] =\
            'df=demand_power_hh:d_e_hh'
        
        # Electric vehicles:
        if (
                self.scen_techs['scenarios']['demand_side']
                and self.scen_techs['demand_side']['ev_integration']
                and self.scen_techs['demand_side']['ev_flexibility']
                ):
            
            # There is a lower bound (pd) that must be fulfilled and a max. upper bound (pd + delta):
            loc_dict['X1']['techs']['demand_electricity_ev_pd']['constraints.resource'] =\
                'df=demand_power_ev_pd:d_e_ev_pd'
            loc_dict['X1']['techs']['demand_electricity_ev_delta']['constraints.resource'] =\
                'df=demand_power_ev_delta:d_e_ev_delta'
            # Virtual resource to quantify flexibility
            loc_dict['X1']['techs']['flexibility_ev']['constraints.resource'] =\
                'inf'

        else:
            # Fixed charging profile:
            loc_dict['X1']['techs']['demand_electricity_ev']['constraints.resource'] =\
                'df=demand_power_ev:d_e_ev'
                
        loc_dict['X1']['techs']['demand_heat']['constraints.resource'] =\
            'df=demand_heat:d_h'
        loc_dict['Limited_Supplies']['techs']['wet_biomass_supply']['constraints.resource'] =\
            'df=wet_biomass_resource:s_wet_bm'
        loc_dict['Limited_Supplies']['techs']['wood_supply']['constraints.resource'] =\
            'df=wood_resource:s_wd'#
        # Update coordinates:
        loc_dict['X1']['coordinates']['lat'] = 1 
        loc_dict['X1']['coordinates']['lon'] = 1
        
        # ---------------------------------------------------------------------
        # Populate loc_dict for currently existing (i.e. "old") tech locations:
        # if 'solar_thermal_old' in self.tech_list_old:
        #     loc_dict['Old_Solar_Thermal']['techs']['solar_thermal_old'] = None
            
        # if 'solar_pv_old' in self.tech_list_old:
        #     loc_dict['Old_Solar_PV']['techs']['solar_pv_old'] = None        
        
        # ---------------------------------------------------------------------
        # Populate loc_dict for wind power locations:
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
            loc_dict['loc_wp_annual'] = {
                'techs':{
                    'wind_power_old':{},
                    'wind_power_new':{},
                    },
                'coordinates':{}
                }
            # Add resources:
            loc_dict['loc_wp_annual']['techs']['wind_power_old']['constraints.resource'] =\
                'df=wp_resource_annual:v_e_wp'
            loc_dict['loc_wp_annual']['techs']['wind_power_new']['constraints.resource'] =\
                'df=wp_resource_annual:v_e_wp'
            # Add max. capacities:
            # loc_dict['loc_wp_annual']['techs']['wind_power_old']['constraints.energy_cap_max'] =\
            #     cap_max_installed_annual
            loc_dict['loc_wp_annual']['techs']['wind_power_new']['constraints.energy_cap_max'] =\
                cap_max_new_annual
            # Force capacity and resources for currently installed capacities:
            loc_dict['loc_wp_annual']['techs']['wind_power_old']['constraints.force_resource'] =\
                True
            # loc_dict['loc_wp_annual']['techs']['wind_power_old']['constraints.resource_cap_equals'] =\
            #     cap_max_installed_annual
            loc_dict['loc_wp_annual']['techs']['wind_power_old']['constraints.energy_cap_max'] =\
                cap_max_installed_annual
            
            # Update coordinates:
            loc_dict['loc_wp_annual']['coordinates']['lat'] = 3 # ! Add here actual coordinates
            loc_dict['loc_wp_annual']['coordinates']['lon'] = 3
            # Add wind power conversion unit:
            loc_dict['loc_wp_annual']['techs']['wind_power_unit'] = {}
            loc_dict['loc_wp_annual']['techs']['wind_power_unit']['constraints.energy_cap_per_unit'] =\
                cap_max_annual
            
            # -----------------------------------------------------------------
            # Location for wind power with profile of type 'winter':
            
            # Create dict:
            loc_dict['loc_wp_winter'] = {
                'techs':{
                    'wind_power_old':{},
                    'wind_power_new':{}
                    },
                'coordinates':{}
                }
            # Add resources:
            loc_dict['loc_wp_winter']['techs']['wind_power_old']['constraints.resource'] =\
                'df=wp_resource_winter:v_e_wp'
            loc_dict['loc_wp_winter']['techs']['wind_power_new']['constraints.resource'] =\
                'df=wp_resource_winter:v_e_wp'
            # Add max. capacities:
            # loc_dict['loc_wp_winter']['techs']['wind_power_old']['constraints.energy_cap_max'] =\
            #     cap_max_installed_winter
            loc_dict['loc_wp_winter']['techs']['wind_power_new']['constraints.energy_cap_max'] =\
                cap_max_new_winter
            # Force capacity and resources for currently installed capacities:
            loc_dict['loc_wp_winter']['techs']['wind_power_old']['constraints.force_resource'] =\
                True
            # loc_dict['loc_wp_winter']['techs']['wind_power_old']['constraints.resource_cap_equals'] =\
            #     cap_max_installed_winter
            loc_dict['loc_wp_winter']['techs']['wind_power_old']['constraints.energy_cap_max'] =\
                cap_max_installed_winter
            # Update coordinates:
            loc_dict['loc_wp_winter']['coordinates']['lat'] = 2 # ! Add here actual coordinates
            loc_dict['loc_wp_winter']['coordinates']['lon'] = 2
            # Add wind power conversion unit:
            loc_dict['loc_wp_winter']['techs']['wind_power_unit'] = {}
            loc_dict['loc_wp_winter']['techs']['wind_power_unit']['constraints.energy_cap_per_unit'] =\
                cap_max_winter
            
        return loc_dict
    
    def __create_links_dict(self):

        # List of locations to be linked to the main location:
        link_locs = ['New_Techs']
        
        link_locs_power = ['New_Techs']
        
        link_locs_heat = ['New_Techs']

        link_locs_heat_biomass = ['New_Techs']
        
        link_locs_heat_hp = ['New_Techs']
        
        # if 'solar_thermal' in self.tech_list:
        #     link_locs.append('Old_Solar_Thermal')
            
        #     link_locs_heat.append('Old_Solar_Thermal')
        
        # if 'solar_pv' in self.tech_list:
        #     link_locs.append('Old_Solar_PV')
            
        #     link_locs_power.append('Old_Solar_PV')
        
        if 'wind_power' in self.tech_list:
            link_locs.append('loc_wp_winter')
            link_locs.append('loc_wp_annual')
            
            link_locs_power.append('loc_wp_winter')
            link_locs_power.append('loc_wp_annual')
        
        if len(self.tech_list_pv) > 0:
            for i in range(len(self.tech_list_pv)):
                for j in range(len(self.tech_list_pv[i])):
                    link_locs_power.append(self.tech_list_pv[i][j])

        # Initialise dict:
        links_dict = {}
        
        # Add links:
        for loc in link_locs:
            links_dict[f'X1,{loc}'] = {
                'techs':{}
                }
            
        for loc in link_locs_power:
            links_dict[f'X1,{loc}'] = {
                'techs':{}
            }
            links_dict[f'X1,{loc}']['techs']['power_line'] = {
                'constraints':{
                    # 'energy_cap_equals':1e10
                    }
                }
            links_dict[f'X1,{loc}']['techs']['hp_heat_line'] = {
                'constraints':{
                    # 'energy_cap_equals':1e10
                    }
                }

                
            
        for loc in link_locs_heat:
            links_dict[f'X1,{loc}']['techs']['heat_line'] = {
                'constraints':{
                    # 'energy_cap_equals':1e10
                    }
                }
            
        for loc in link_locs_heat_hp:
            links_dict[f'X1,{loc}']['techs']['hp_heat_line'] = {
                'constraints':{
                    # 'energy_cap_equals':1e10
                    }
                }
        
        for loc in link_locs_heat_biomass:
            links_dict[f'X1,{loc}']['techs']['heat_biomass_line'] = {
                'constraints':{
                    # 'energy_cap_equals':1e10
                    }
                }

            
        # links_dict['X1,New_Techs'] = {
        #     'techs':{
        #         'gas_line':{
        #             'constraints':{
        #                 'energy_cap_equals':1e10
        #                 }
        #             }
        #         }
        #     }
        
        links_dict['X1,New_Techs']['techs']['gas_line'] = {
            'constraints':{
                # 'energy_cap_equals':1e10
                }
            }
        
        
        links_dict['X1,Limited_Supplies'] = {
            'techs':{}
            }
        links_dict['New_Techs,Limited_Supplies'] = {
            'techs':{}
            }
        
        links_dict['X1,Limited_Supplies']['techs']['wood_line'] = {
            'constraints':{
                # 'energy_cap_equals':1e10
                }
            }
        
        links_dict['New_Techs,Limited_Supplies']['techs']['wood_line'] = {
            'constraints':{
                # 'energy_cap_equals':1e10
                }
            }
        
        links_dict['New_Techs,Limited_Supplies']['techs']['wet_biomass_line'] = {
            'constraints':{
                # 'energy_cap_equals':1e10
                }
            }
            
        # links_dict['X1,Limited_Supplies'] = {
        #     'techs':{
        #         'wood_line':{
        #             'constraints':{
        #                 'energy_cap_equals':1e10
        #                 }
        #             }
        #         }
        #     }
        
        # links_dict['New_Techs,Limited_Supplies'] = {
        #     'techs':{
        #         'wood_line':{
        #             'constraints':{
        #                 'energy_cap_equals':1e10
        #                 }
        #             }
        #         }
        #     }
        
        # links_dict['New_Techs,Limited_Supplies'] = {
        #     'techs':{
        #         'wet_biomass_line':{
        #             'constraints':{
        #                 'energy_cap_equals':1e10
        #                 }
        #             }
        #         }
        #     }

        return links_dict
    
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
            'mode':'plan',
            'solver':self.opt_metrics['solver'],
            'ensure_feasibility':'true',
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
                'FeasibilityTol':self.opt_metrics['solver_option_FeasibilityTol'],
                'MIPGap':mipgap_,
                
                }
            }
        
        return run_dict
    
    # def __create_group_constraints_dict(self, rerun_eps=False, eps_n='inf'):
    def __create_group_constraints_dict(self):
        
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
        dhn_list= []
        if self.dhn_qty == 0:
            const_techs.append('district_heating_hub')
            dhn_list.append('district_heating_hub')
        elif self.dhn_qty >= 0:
            for i in range(self.dhn_qty):
                const_techs.append(f"district_heating_hub_{i}")
                dhn_list.append(f"district_heating_hub_{i}")
        
        group_constraints_dict = {
            'constant_heat_sources':{
                'techs': const_techs,
                # 'techs':[
                #     # 'heat_pump_old',
                #     # 'heat_pump_new',
                #     'heat_pump_hub',
                #     'electric_heater_old',
                #     'oil_boiler_old',
                #     'oil_boiler_new',
                #     'gas_boiler_old',
                #     'gas_boiler_new',
                #     'wood_boiler_old',
                #     'wood_boiler_new',
                #     'district_heating_hub',
                #     ], # ensure techs are spelled correctly (no error is thrown if tech doesn't exist)!
                'locs':['New_Techs', 'X1',],
                'demand_share_per_timestep_decision':{
                    'heat':None, # if set to 'None', the optimiser chooses a constant value; if a value is given (e.g. 0.2), this value will be used as constant share
                    },
                },
            }
        # self.rerun_eps = True
        # # # self.eps_n = 2091119.65019013
        # self.eps_n = 1707022.26495658
        #429454470
        #448447074

        
        if self.rerun_eps: # set epsilon constraint
            group_constraints_dict['systemwide_co2_cap'] = None
            group_constraints_dict['systemwide_co2_cap'] = {
                    'cost_max':{
                        'emissions_co2':self.eps_n,
                        }
                    }

        # Constraint in regard to what share of the heat demand shall be supplied by district heating:
        if self.dhn_share_type == 'fixed':
            group_constraints_dict['dhn_demand_share'] = None
            group_constraints_dict['dhn_demand_share'] = {
                # 'techs':['district_heating_hub'],
                'techs':dhn_list,
                'locs':['X1'],
                'demand_share_per_timestep_equals':{
                            'heat':self.dhn_share_val,
                            },
                }
        elif self.dhn_share_type == 'min':
            group_constraints_dict['dhn_demand_share'] = None
            group_constraints_dict['dhn_demand_share'] = {
                # 'techs':['district_heating_hub'],
                'techs':dhn_list,
                'locs':['X1'],
                'demand_share_per_timestep_min':{
                            'heat':self.dhn_share_val,
                            },
                }
            
        elif self.dhn_share_type == 'max':
            group_constraints_dict['dhn_demand_share'] = None
            group_constraints_dict['dhn_demand_share'] = {
                # 'techs':['district_heating_hub'],
                'techs':dhn_list,
                'locs':['X1'],
                'demand_share_per_timestep_max':{
                            'heat':self.dhn_share_val,
                            },
                }

        elif self.dhn_share_type == 'free':
            pass
        
        else:
            raise ValueError("district_heating.demand_share_type invalid!")
            
        # Fixed demand shares of decentralised heating techs:
        if self.hp_fixed_demand_share:
            group_constraints_dict['hp_demand_share'] = None
            group_constraints_dict['hp_demand_share'] = {
                'techs':['heat_pump_hub'],
                'locs':['X1'],
                'demand_share_per_timestep_equals':{
                            'heat':self.hp_fixed_demand_share_val ,
                            },
                }
            
        
        if self.eh_fixed_demand_share:
            group_constraints_dict['eh_demand_share'] = None
            group_constraints_dict['eh_demand_share'] = {
                'techs':['electric_heater_old'],
                'locs':['X1'],
                'demand_share_per_timestep_equals':{
                            'heat':self.eh_fixed_demand_share_val ,
                            },
                }
        
        if self.ob_fixed_demand_share:
            group_constraints_dict['ob_demand_share'] = None
            group_constraints_dict['ob_demand_share'] = {
                'techs':['oil_boiler_old', 'oil_boiler_new'],
                'locs':['X1', 'New_Techs'],
                'demand_share_per_timestep_equals':{
                            'heat':self.ob_fixed_demand_share_val ,
                            },
                }
        
        if self.gb_fixed_demand_share:
            group_constraints_dict['gb_demand_share'] = None
            group_constraints_dict['gb_demand_share'] = {
                'techs':['gas_boiler_old', 'gas_boiler_new'],
                'locs':['X1', 'New_Techs'],
                'demand_share_per_timestep_equals':{
                            'heat':self.gb_fixed_demand_share_val ,
                            },
                }
            
        if self.wb_fixed_demand_share:
            group_constraints_dict['wb_demand_share'] = None
            group_constraints_dict['wb_demand_share'] = {
                'techs':['wood_boiler_old', 'wood_boiler_new'],
                'locs':['X1', 'New_Techs'],
                'demand_share_per_timestep_equals':{
                            'heat':self.wb_fixed_demand_share_val ,
                            },
                }
        
            # 'new_oil_boiler_share':{
            #         'techs':['oil_boiler_new', 'chp_gt_new'], # ensure techs are spelled correctly!
            #         'locs':['New_Techs', 'X1'],
            #         'demand_share_per_timestep_decision':{
            #             'heat':None, # if set to 'None', the optimiser chooses a constant value; if a value is given (e.g. 0.2), this value will be used as constant share
            #             },
            #         },
            #     'old_oil_boiler_share':{
            #         'techs':['oil_boiler_old'],
            #         'locs':['New_Techs', 'X1'],
            #         'demand_share_per_timestep_equals':{
            #             'heat':0.0,
            #             },
            # }
        
        return group_constraints_dict
        
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

    def __techs_dict_add_heat_biomass_line(self, techs_dict, colors):
        
        # Virtual power line with infinite capacity and no cost attributed.
        techs_dict['heat_biomass_line'] = {
            'essentials':{
                'name':'Heat_biomass transmission',
                'color': colors['heat_line'],
                'parent':'transmission',
                'carrier':'heat_biomass'
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

    def __techs_dict_add_hp_heat_line(self, techs_dict, colors):
        
        # Virtual heat line with infinite capacity and no cost attributed.
        techs_dict['hp_heat_line'] = {
            'essentials':{
                'name':'Heat transmission for HP heat',
                'color': colors['heat_line'],
                'parent':'transmission',
                'carrier':'heat_hp'
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
