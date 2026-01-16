# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 12:43:27 2023

@author: UeliSchilt
"""

import pandas as pd
# import os
import sys
import numpy as np
# import matplotlib.pylab as plt
import time
import copy

from district_energy_model import dem_techs
from district_energy_model import dem_demand
from district_energy_model import dem_hp_cop_calculation
from district_energy_model import dem_helper
from district_energy_model import dem_energy_balance as dem_eb
from district_energy_model import dem_output
from district_energy_model import dem_scenarios
from district_energy_model import dem_supply
from district_energy_model import dem_constants as C
from district_energy_model import dem_clustering
from district_energy_model import dem_emissions
from district_energy_model import dem_create_custom_district
from district_energy_model import dem_solar_preprocessing_switzerland

from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
pd.options.mode.chained_assignment = None


# pd.options.mode.chained_assignment = None

class DistrictEnergyModel:
    
    """
    Builds an energy model of a district/community/municipality which can be
    used to emulate different scenarios.
    """
       
    def __init__(self,
                 paths,
                 arg_com_nr,
                 # base_tech_data,
                 scen_techs,
                 toggle_energy_balance_tests = True
                 ):
        
        """
        Loads and prepares the community data for further computations.
        
        Generates base scenario (as-is).
        
        Parameters
        ----------
            
        arg_df_com : pandas dataframe
            Dataframe containing information about the selected community.
            (1 row per building)
        arg_df_meta : pandas dataframe
            Dataframe containing meta information about each community.
            (1 row per community)
        arg_com_name : string
            Name of community/district/municipality
        base_tech_data : dict
            Dictionary contianing metrics about technologies used in base
            scenario (e.g. heat pump COP).

        Returns
        -------
        n/a
        """
    
        
        """--------------------------------------------------------------------
        Prepare input:
        """
        self.paths = paths
        
        # Selected community/ custom scenario:
        self.com_nr = arg_com_nr
        
        # Switch energy balance tests ON/OFF:
        self.toggle_energy_balance_tests = toggle_energy_balance_tests

        # self.com_nr_original = copy.deepcopy(self.com_nr)

        self.com_nr_majority = copy.deepcopy(self.com_nr)

        if scen_techs['meta_data']['custom_district']['implemented'] == True:
            custom_district_name = scen_techs['meta_data']['custom_district']['custom_district_name']
            self.com_nr, self.com_nr_majority, self.com_name_, self.com_kt, self.df_meta, self.df_com_yr, self.com_percent,self.com_percent_2 = dem_create_custom_district.create_district(
                self.paths,
                scen_techs
                )
            print(f"\nCustom district: {custom_district_name} (part of {self.com_name_})")
        
        else:
            self.com_name_, self.com_kt, self.df_meta, self.df_com_yr = dem_helper.get_com_files(
                com_nr = self.com_nr, 
                master_data_dir = paths.simulation_data_dir, 
                com_data_dir = paths.com_data_dir, 
                master_file = paths.master_file, 
                meta_file = paths.meta_file
                )
            self.com_percent = []
            self.com_percent_2 = []
        
            print(f"\n{self.com_name_}")
        
        # Stop execution if munic is on the list to be omitted:
        if self.com_nr in C.munics_omit:
            print("Model aborted.")
            print(f"Munic {self.com_name_} not included in model as it is on the list "
                  "of municipalities to omit (see dem_constants.py).")
            sys.exit()
        
        # Input data directories:
        self.simulation_data_dir = paths.simulation_data_dir
        
        # self.pv_data_dir = paths.pv_data_dir # location of pv data
        # self.energy_mix_CH_dir = paths.energy_mix_CH_dir # location of energy mix files
        # self.electricity_profile_dir = paths.electricity_profile_dir # location of electr. load profile files
        # self.biomass_data_dir = paths.biomass_data_dir
        self.wind_power_data_dir = paths.wind_power_data_dir # location of wind power data (e.g. installed capacities per municipality)
        self.wind_power_profiles_dir = paths.wind_power_profiles_dir  # location of wind power hourly profile files
        self.ev_profiles_dir = paths.ev_profiles_dir # location of electric vehicle (ev) charging profiles
        
        sim_plt = scen_techs['simulation']['generate_plots']
        sim_res = scen_techs['simulation']['save_results']
        if sim_plt or sim_res:
            self.results_path = dem_helper.create_results_directory(
                paths.root_dir,
                paths.output_dir_name
                )
        else:
            self.results_path = 0
            
        # self.results_path = paths.results_path
        # self.results_path = scen_techs['simulation']['results_dir']
        
        # Input data files:
        self.profiles_file = pd.read_feather(self.simulation_data_dir + paths.profiles_file)

            
        # self.electricity_import_file = paths.electricity_import_file # csv-file containing timeseries of hourly cross-border electricity import fraction.
        # self.electricity_mix_file = paths.electricity_mix_file # csv-file containing timeseries of hourly electricity mix fractions.
        # self.electricity_mix_totals_file = paths.electricity_mix_totals_file # csv-file containing timeseries of hourly electricity mix fractions.
        # self.strom_profiles_2050_file = paths.strom_profiles_2050_file # CSV containing hourly production and consumption data
        # self.electricity_demand_file_household = paths.electricity_demand_file_household # csv-file containing a list of all communities and their respective annual electricity demand (kWh).
        # self.electricity_demand_file_industry = paths.electricity_demand_file_industry
        # self.pv_data_meta_file = paths.pv_data_meta_file # csv file containing meta data about pv profile files
        # self.electricity_profile_file = paths.electricity_profile_file # csv-file containing load profile from smart meter data
        # self.electricity_profile_industry_file = paths.electricity_profile_industry_file
        self.wind_power_cap_file = paths.wind_power_cap_file # installed wind power capacity [kW] per municipality
        # self.wind_power_profile_file_annual = f"{self.com_name_}.csv" # csv-file containing generation profiles of wind power
        # self.wind_power_profile_file_winter = f"{self.com_name_}_winter.csv" # csv-file containing generation profiles of wind power, with profiles favored for winter-production
        self.wind_power_profile_file_annual = f"{self.com_name_}.feather" # feather-file containing generation profiles of wind power
        self.wind_power_profile_file_winter = f"{self.com_name_}_winter.feather" # feather-file containing generation profiles of wind power, with profiles favored for winter-production
        self.wind_power_national_profile_file = paths.wind_power_national_profile_file # Hourly profile of national wind power generation [kWh]
        # self.hydro_profile_file = paths.hydro_profile_file
        self.ev_profile_cp_file = paths.ev_profile_cp_file # hourly charging load [kW]
        self.ev_profile_fe_file = paths.ev_profile_fe_file # daily flexible energy [kWh]
        self.ev_profile_pd_file = paths.ev_profile_pd_file # hourly upper power bound [kW]
        self.ev_profile_pu_file = paths.ev_profile_pu_file # hourly lower power bound [kW]
        self.ev_munic_name_nr = paths.ev_munic_name_nr_file # municipalities and BFS numnbers for ev data
        
        # Base technolgies data:
        # self.base_tech_data = base_tech_data
        
        # List to collect input data and write to a file at the end:
        self.list_input_data = []
            # Input data will be added in the form lists of the form:
            # ['parameter', parameter_value, 'description']
       
        #----------------------------------------------------------------------
        # Add data to input-parameter file:
        self.list_input_data.append(
            [
                'com_name',
                self.com_name_,
                'Name of community/district/municipality'
                ]
            )
        
        #----------------------------------------------------------------------
        # Heat demand info:
        self.yearly_heat_demand_col='heat_energy_demand_estimate_kWh_combined' # df column used for annual heat demand
        self.yearly_hot_water_demand_col='dhw_estimation_kWh_combined' # df column used for annual hot_water demand
        
        """--------------------------------------------------------------------
        Read and prepare data:
        """
    
        #----------------------------------------------------------------------
        # Read pv meta file:
        # pv_meta_file_path = self.pv_data_dir + self.pv_data_meta_file
        # self.df_pv_meta = pd.read_csv(pv_meta_file_path)
        
        
        """--------------------------------------------------------------------
        Extract information about community:
        """
        # Latitude, longitude, and altitude of selected community:
        self.com_lat = self.df_meta.loc[
            self.df_meta['GGDENR'] == self.com_nr, 'Coord_lat_median'
            ].item()
        self.com_lon = self.df_meta.loc[
            self.df_meta['GGDENR'] == self.com_nr,'Coord_long_median'
            ].item()
        self.com_alt = self.df_meta.loc[
            self.df_meta['GGDENR'] == self.com_nr, 'altitude_median'
            ].item()
        
        self.list_input_data.append(['com_lat',self.com_lat,'latitude'])
        self.list_input_data.append(['com_lon',self.com_lon,'longitude'])
        self.list_input_data.append(['com_alt',self.com_alt,'altitude'])
        
        """--------------------------------------------------------------------
        Generate base scenario (as-is):
        """
        
        # print('\nGenerating Base Scenario')
        self.df_base, self.dict_yr_base = self.__generate_base_scenario(scen_techs) # results of base scenario
        # print('base clustering')
        # self.df_base_clustering, self.dict_yr_base_clustering = self.__generate_base_clustering_scenario() # self.__df_base = res_base[0]
        
        """--------------------------------------------------------------------
        Binary variables to check model status
        """
        self.scenario_generated = False
        self.pareto_results_generated = False
        self.pareto_results_loaded = False
        
    def __generate_base_scenario(self, scen_techs):
        """
        Generate the base scenario (as-is), which is the basis for other
        scenarios. This method will be run at class intialisation.
        
        Parameters
        ----------
            
        n/a

        Returns
        -------
        df_base : pandas dataframe
            Dataframe with resulting hourly values.
        dict_yr : dictionary
            Dictionary with reulting annual values.
        """
        
        """--------------------------------------------------------------------
        Initialise parameters:
        """
        
        df_base = pd.DataFrame(index = range(8760)) # dataframe for storing hourly results
        df_interim = pd.DataFrame(index = range(8760)) # dataframe for storing interim data
        
        """--------------------------------------------------------------------
        Initialise dict containing demand and tech instances:
        """
        
        self.tech_instances = {}

        """--------------------------------------------------------------------
        Create demand instance:
        """
        
        self.energy_demand = dem_demand.EnergyDemand(paths=self.paths, com_nr=self.com_nr)
        
        """--------------------------------------------------------------------
        Create resource supply instance:
        """
        
        self.supply = dem_supply.Supply(
            com_nr=self.com_nr,
            meta_file=self.df_meta,
            profiles_file=self.profiles_file,
            supply_tech_dict=scen_techs['supply']
            )
        
        
        """--------------------------------------------------------------------
        Heat Demand and Current Consumption:
        """
        
        self.energy_demand.compute_d_h_yr(
            df_meta=self.df_meta
            )

        # Hourly heat demand:
        self.energy_demand.compute_d_h_hr(
            com_name=self.com_name_,
            # com_nr_original=self.com_nr_original,
            com_nr_original=self.com_nr_majority, # changed: 23.12.2025
            com_lat=self.com_lat,
            com_lon=self.com_lon,
            com_alt=self.com_alt,
            tf_start=C.tf_meteostat_start,
            tf_end=C.tf_meteostat_end
            )

        hps_existings_cops, hps_new_cops, hps_one_to_one_replacement_cops, tot_heat_existing, tot_heat_new, tot_heat_one_to_one = dem_hp_cop_calculation.calculateCOPs(
                                                     paths = self.paths,
                                                     df_com_yr=self.df_com_yr, 
                                                     quality_factor_ashp_new = scen_techs['heat_pump']['quality_factor_ashp_new'], 
                                                     quality_factor_ashp_old = scen_techs['heat_pump']['quality_factor_ashp_old'],
                                                     quality_factor_gshp_new = scen_techs['heat_pump']['quality_factor_gshp_new'], 
                                                     quality_factor_gshp_old = scen_techs['heat_pump']['quality_factor_gshp_old'],
                                                     com_nr = self.com_nr_majority,
                                                     dem_demand = self.energy_demand,
                                                     weather_year = C.METEO_YEAR,
                                                     consider_renovation_effects=False,
                                                     total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios =\
                                                        scen_techs['demand_side']['total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios'],
                                                     total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios =\
                                                        scen_techs['demand_side']['total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios'],
                                                     optimisation_enabled = scen_techs['optimisation']['enabled']
                                                     )
        
        hps_existings_cops, hps_new_cops, hps_one_to_one_replacement_cops= dem_techs.HeatPump.select_right_cop_mode(scen_techs, 
                              hps_existings_cops, 
                              hps_new_cops, 
                              hps_one_to_one_replacement_cops)



        """--------------------------------------------------------------------
        Create base tech instances:
        """

        # Create instances:        
        self.tech_heat_pump = dem_techs.HeatPump(scen_techs['heat_pump'])
        self.tech_heat_pump.set_cops_existing(hps_existings_cops)
        self.tech_heat_pump.set_cops_new(hps_new_cops)
        self.tech_heat_pump.set_cops_one_to_one_replacement(hps_one_to_one_replacement_cops)
        self.tech_heat_pump.set_tot_heats_for_cop_calculations(tot_heat_existing, tot_heat_new, tot_heat_one_to_one)
        
        self.tech_instances['heat_pump'] = self.tech_heat_pump

        self.tech_electric_heater = dem_techs.ElectricHeater(scen_techs['electric_heater'])
        self.tech_instances['electric_heater'] = self.tech_electric_heater
        
        self.tech_oil_boiler = dem_techs.OilBoiler(scen_techs['oil_boiler'])
        self.tech_instances['oil_boiler'] = self.tech_oil_boiler
        
        self.tech_gas_boiler = dem_techs.GasBoiler(scen_techs['gas_boiler'])
        self.tech_instances['gas_boiler'] = self.tech_gas_boiler
        
        self.tech_wood_boiler = dem_techs.WoodBoiler(scen_techs['wood_boiler'])
        self.tech_instances['wood_boiler'] = self.tech_wood_boiler
        
        self.tech_district_heating = dem_techs.DistrictHeating(
            scen_techs['district_heating'], 
            self.com_nr, 
            self.df_com_yr, 
            self.df_meta, 
            self.energy_demand
            )
        self.tech_instances['district_heating'] = self.tech_district_heating
        
        # self.tech_solar_thermal = dem_techs.SolarThermal(scen_techs['solar_thermal'])
        # self.tech_instances['solar_thermal'] = self.tech_solar_thermal
        


        # self.tech_solar_pv = dem_techs.SolarPV(
        #     com_nr = self.com_nr,
        #     tech_dict = scen_techs['solar_pv']
        #     )
        # self.tech_instances['solar_pv'] = self.tech_solar_pv
        



        if not scen_techs['meta_data']['custom_district']['implemented']:
            pv_profile_and_capex_factors = (
                dem_solar_preprocessing_switzerland.obtain_com_roof_profile(
                    self.com_nr, 
                    scen_techs['solar_pvrooftop']['eta_overall'],
                    self.paths
                    )
                )
        else:
            com_nrs = list(self.com_percent_2.index)
            pv_profile_and_capex_factors = (
                dem_solar_preprocessing_switzerland.obtain_custom_district_roof_profile(
                    com_nrs,scen_techs['meta_data']['custom_district']['EGID_List'],
                    scen_techs['solar_pvrooftop']['eta_overall'],
                    self.paths
                    )
                )

        solar_pv_rooftop_shares_occupied = [1.0 
                                            if i==0 
                                            else 0.0 
                                            for i in range(
                                                dem_solar_preprocessing_switzerland.NUM_GROUPS
                                                )]

        pv_rooftop_profiles = [pv_profile_and_capex_factors[k][0] for k in range(dem_solar_preprocessing_switzerland.NUM_GROUPS)]
        pv_rooftop_capex_numbers = [pv_profile_and_capex_factors[k][1] for k in range(dem_solar_preprocessing_switzerland.NUM_GROUPS)]

        solarthermal_rooftop_profiles = [scen_techs['solarthermal_rooftop']['eta_overall']* pv_profile_and_capex_factors[k][0]/(scen_techs['solar_pvrooftop']['eta_overall'])
                                          if k>0 else
                                           scen_techs['solarthermal_rooftop']['eta_overall']*pv_profile_and_capex_factors[k][0]/(dem_solar_preprocessing_switzerland.EFFICIENCY_TO_USE)
                                            for k in range(dem_solar_preprocessing_switzerland.NUM_GROUPS)]
        solarthermal_rooftop_share_occupied = [0.0 for i in range(dem_solar_preprocessing_switzerland.NUM_GROUPS)]
        solarthermal_rooftop_capex_numbers = pv_rooftop_capex_numbers

        self.tech_solar_pv_rooftop = dem_techs.SolarPVType(
            "pvrooftop",
            pv_rooftop_profiles,
            pv_rooftop_capex_numbers,
            solar_pv_rooftop_shares_occupied, 
            tech_dict = scen_techs['solar_pvrooftop'])
        self.tech_instances['solar_pvrooftop'] = self.tech_solar_pv_rooftop

        self.tech_solarthermal_rooftop = dem_techs.SolarThermalType(
            "solarthermalrooftop",
            "heat_hp",
            solarthermal_rooftop_profiles,
            solarthermal_rooftop_capex_numbers,
            solarthermal_rooftop_share_occupied, 
            tech_dict = scen_techs['solarthermal_rooftop'])
        self.tech_instances['solarthermal_rooftop'] = self.tech_solarthermal_rooftop
        
        self.tech_solarthermal_rooftop.compute_v_h()
        self.tech_solarthermal_rooftop.compute_v_h_pot_base()
        self.tech_solarthermal_rooftop.compute_v_h_pot_remain()

        self.tech_solarthermal_rooftop.agregate_variables(only_potential = True)


        self.tech_wind_power = dem_techs.WindPower(
            wind_power_data_dir = self.wind_power_data_dir,
            wind_power_profiles_dir = self.wind_power_profiles_dir,
            wind_power_cap_file = self.wind_power_cap_file,
            wind_power_profile_file_annual = self.wind_power_profile_file_annual,
            wind_power_profile_file_winter = self.wind_power_profile_file_winter,
            wind_power_national_profile_file = self.wind_power_national_profile_file,
            com_name = self.com_name_,
            com_percent = self.com_percent,
            tech_dict = scen_techs['wind_power'],
            )
        self.tech_instances['wind_power'] = self.tech_wind_power
        
        # self.tech_biomass = dem_techs.Biomass(scen_techs['biomass'])
        
        self.tech_hydro_power = dem_techs.HydroPower(scen_techs['hydro_power'])
        self.tech_instances['hydro_power'] = self.tech_hydro_power
        
        self.tech_biomass = dem_techs.Biomass(scen_techs['biomass'])
        self.tech_instances['biomass'] = self.tech_biomass
        
        self.tech_grid_supply = dem_techs.GridSupply(
            self.paths,
            scen_techs['grid_supply']
            )
        self.tech_instances['grid_supply'] = self.tech_grid_supply
        
        self.tech_other = dem_techs.Other(0)
        self.tech_instances['other'] = self.tech_other

        
        #----------------------------------------------------------------------
        # Compute primary energy source for heating based on GWR data:
        
        self.energy_demand.compute_d_h_hr_mix(
            df_meta = self.df_meta,
            tech_instances=self.tech_instances
            )
        
        """--------------------------------------------------------------------
        Electricity Demand and Current Consumption Data:
        """
        # Annual electricity demand ("household" (hh) demand, i.e. w/o heating):
        self.energy_demand.compute_d_e_hh_yr(
            self.df_meta,
            self.com_nr
            )
        
        # Hourly electricity demand ("household" (hh) demand, i.e. w/o heating):
        self.energy_demand.compute_d_e_hh_hr(
            profiles_file = self.profiles_file,
            com_kt = self.com_kt
            )
        
        # Electricity demand for heating (hourly and annual):
        self.energy_demand.compute_d_e_h(self.tech_instances)
        
        # Electricity demand for electric vehicles (0 in base scenario):
        tmp_d_e_ev = [0]*8760        
        self.energy_demand.update_d_e_ev_cp(tmp_d_e_ev, 365)
        self.energy_demand.update_d_e_ev_pd(tmp_d_e_ev)
        self.energy_demand.update_d_e_ev_pu(tmp_d_e_ev)
        self.energy_demand.update_d_e_ev(tmp_d_e_ev)
        
        # Total electricity demand (hourly and annual):
        self.energy_demand.compute_d_e()
        
        """--------------------------------------------------------------------
        Reset unmet demand:
        """ 
        self.energy_demand.reset_d_e_unmet()
        self.energy_demand.reset_d_h_unmet()
        self.energy_demand.reset_d_h_unmet_dhn()
            
        """--------------------------------------------------------------------
        Solar PV Potentials and Current Consumption:
        """ 
        # # Compute annual and hourly output of installed PV:
        # self.tech_solar_pv.compute_v_e(
        #     self.df_meta,
        #     self.profiles_file
        #     )
        
        # # Compute total (incl. installed) and remaining rooftop PV potential:
        # self.tech_solar_pv.compute_v_e_pot_base(
        #     self.df_meta
        #     )
        
        self.tech_solar_pv_rooftop.compute_v_e()
        self.tech_solar_pv_rooftop.compute_v_e_pot_base()
        self.tech_solar_pv_rooftop.compute_v_e_pot_remain()
        self.tech_solar_pv_rooftop.agregate_variables(only_potential = True)
        
        """--------------------------------------------------------------------
        Wind Potentials and Current Consumption:
        """
        # Get currently installed wind power:
        self.tech_wind_power.compute_v_e()
            
        # Wind power potential (for profile types 'annual', 'winter', and 'total', and remaining):
        self.tech_wind_power.compute_v_e_pot()

            
        """--------------------------------------------------------------------
        Biomass Potentials and Current Consumption:
        """ 
        # Wet biomass supply:
        self.supply.compute_s_h_wet_biomass()
        
        # Wood supply:
        self.supply.compute_s_h_wood()        
        self.supply.compute_s_h_wood_remaining(self.tech_wood_boiler.get_u_wd())
        
        # Biomass tech (overall):
        tmp_n = len(df_base)
        tmp_null_arr = np.array([0]*tmp_n)
        self.tech_biomass.update_v_e(tmp_null_arr)
        self.tech_biomass.update_v_e_cons(tmp_null_arr)
        self.tech_biomass.update_v_e_exp(tmp_null_arr)
        self.tech_biomass.update_v_h(tmp_null_arr)

        """--------------------------------------------------------------------
        Hydro Potentials and Current Consumption:
        """         
        self.supply.compute_s_hydro()
            
        self.tech_hydro_power.update_v_e_pot(self.supply.get_s_hydro())
        self.tech_hydro_power.update_v_e(self.supply.get_s_hydro())
        
        """--------------------------------------------------------------------
        Electricity mix: self-consumption (cons), export (exp), import (m):
        """
        # dict_v_e_cons, dict_v_e_exp, m_e = dem_eb.get_local_electricity_mix(
        dem_eb.get_local_electricity_mix(
            self.energy_demand,
            self.tech_instances
            )
        
        # Run test for solar PV:     
        # sum_PV = sum(self.tech_solar_pv.get_v_e_cons()) + sum(self.tech_solar_pv.get_v_e_exp())
        sum_PV = sum(self.tech_solar_pv_rooftop.get_v_e_cons()) + sum(self.tech_solar_pv_rooftop.get_v_e_exp())

        dem_eb.energy_balance_test(
            value_1=sum(self.tech_solar_pv_rooftop.get_v_e()),
            value_2=sum_PV,
            description='Solar PV'
            )
        
        """--------------------------------------------------------------------
        Grid Import:
        """
        self.tech_grid_supply.compute_base_grid_import()

        sum_a = dem_helper.get_m_e_ch_sum(self.tech_grid_supply)
        sum_b = (
            sum(self.tech_grid_supply.get_m_e_ch())
            + sum(self.tech_grid_supply.get_m_e_cbimport())
            )        
        dem_eb.energy_balance_test(
            sum(self.tech_grid_supply.get_m_e_ch()), sum_a, 'electricity mix')        
        dem_eb.energy_balance_test(
            sum(self.tech_grid_supply.get_m_e()), sum_b, 'electricity import')


        #----------------------------------------------------------------------
        # Local electricity generation:
        dem_eb.get_local_electricity_mix(self.energy_demand, self.tech_instances)
        
        #----------------------------------------------------------------------
        # Update df_base:        
        dem_helper.update_df_results(
            self.energy_demand,
            self.supply,
            self.tech_instances,
            df_base
            )
        
        
        #----------------------------------------------------------------------
        # Check energy balances:
        if self.toggle_energy_balance_tests:
            dem_eb.electricity_balance_test(
                scen_techs=scen_techs,
                df_scen=df_base,
                optimisation=False,
                diff_accepted = C.DIFF_ACC,
                diff_sum_accepted = C.DIFF_SUM_ACC
                )    
            dem_eb.heat_balance_test(
                df_scen=df_base,
                optimisation=False,
                diff_accepted = C.DIFF_ACC,
                diff_sum_accepted = C.DIFF_SUM_ACC
                )
        
        dict_yr = dem_helper.create_dict_yr(df_base)
        del df_interim
        return df_base, dict_yr
        
    def generate_scenario(self, scen_techs):
        
        """
        Generate scenario based on selected technolgies starting with
        base scenario.
        
        Parameters
        ----------
            
        scen_techs : dictionary
            Dictionary containing info about technologies. 

        Returns
        -------
        df_scen : pandas dataframe
            Dataframe with resulting hourly values.
        dict_yr_scen : dictionary
            Dictionary with reulting annual values.
        dict_total_costs : dictionary
            Dictionary with resulting total costs split by type (e.g. monetary,
            co2) and energy carrier (e.g. heat, electricity).
            (incl. levelised cost)
        """     
        n_days = scen_techs['simulation']['number_of_days']
        ts_num = scen_techs['simulation']['number_of_days']*24 # [h]
        
        dem_helper.reduce_timeframes(
            self.energy_demand,
            self.supply,
            self.tech_instances,
            n_days
            )
        
        # Initialise scenario with base scenario:
        if self.scenario_generated == True:
            df_scen = self.df_scen.iloc[:ts_num].copy()
            dict_yr_scen = self.dict_yr_scen
        else:
            df_scen = self.df_base.iloc[:ts_num].copy()
            dict_yr_scen = self.dict_yr_base
     
        #----------------------------------------------------------------------
        # Update techs from base scenario:     


        for tech_name, tech_instance in list(self.tech_instances.items()): # iterate over a copy()
            if scen_techs[tech_name]['deployment']:
                tech_instance.update_tech_properties(scen_techs[tech_name])
                # print(f"{tech_name} added to scenario.\n")
            # elif tech_name == 'solar_pv' and scen_techs['solar_thermal']['deployment'] == True:
            #     tech_instance.update_tech_properties(scen_techs[tech_name]) # Keep solar PV because information is required for solar thermal
            else:
                del self.tech_instances[tech_name]
                # print(f"{tech_name} was removed from scenario.\n")

        #----------------------------------------------------------------------
        # Add additional techs for new scenario:
        
        # Waste heat flow
        if scen_techs['waste_heat']['deployment']:                
            self.tech_wh = dem_techs.WasteHeat(scen_techs['waste_heat'])
            self.tech_wh.initialise_finite(n_days)
            self.tech_instances['waste_heat'] = self.tech_wh

        # Waste heat (low temperature) flow
        if scen_techs['waste_heat_low_temperature']['deployment']:                
            self.tech_whlt = dem_techs.WasteHeatLowTemperature(scen_techs['waste_heat_low_temperature'])
            self.tech_whlt.initialise_finite(n_days)
            self.tech_instances['waste_heat_low_temperature'] = self.tech_whlt


        # Thermal energy storage
        if scen_techs['tes']['deployment']:                
            self.tech_tes = dem_techs.ThermalEnergyStorage(scen_techs['tes'])
            self.tech_tes.initialise_zero(n_days)
            self.tech_instances['tes'] = self.tech_tes
            
        # Thermal energy storage - decentralised:
        if scen_techs['tes_decentralised']['deployment']:                
            self.tech_tes_decentralised = dem_techs.ThermalEnergyStorageDC(
                scen_techs['tes_decentralised']
                )
            self.tech_tes_decentralised.initialise_zero(n_days)
            self.tech_instances['tes_decentralised'] =\
                self.tech_tes_decentralised

        # Battery energy storage
        if scen_techs['bes']['deployment']:                
            self.tech_bes = dem_techs.BatteryEnergyStorage(scen_techs['bes'])
            self.tech_bes.initialise_zero(n_days)
            self.tech_instances['bes'] = self.tech_bes
        
        # Pile of Berries
        if True:                
            self.tech_pile_of_berries = dem_techs.PileOfBerries(scen_techs['bes'])
            self.tech_pile_of_berries.initialise_zero(n_days)
            self.tech_instances['pile_of_berries'] = self.tech_pile_of_berries

        # Gas tank energy storage
        if scen_techs['gtes']['deployment']:                
            self.tech_gtes = dem_techs.GasTankEnergyStorage(scen_techs['gtes'])
            self.tech_gtes.initialise_zero(n_days)
            self.tech_instances['gtes'] = self.tech_gtes

        # Gas tank energy storage
        if scen_techs['ws']['deployment']:                
            self.tech_ws = dem_techs.WoodStorage(scen_techs['ws'])
            self.tech_ws.initialise_zero(n_days)
            self.tech_instances['ws'] = self.tech_ws

        # Hydrogen energy storage
        if scen_techs['hes']['deployment']:                
            self.tech_hes = dem_techs.HydrogenEnergyStorage(scen_techs['hes'])
            self.tech_hes.initialise_zero(n_days)
            self.tech_instances['hes'] = self.tech_hes

        # Hydrothermal gasification (hg)
        if scen_techs['hydrothermal_gasification']['deployment']:
            self.tech_hydrothermal_gasification =\
                dem_techs.HydrothermalGasification(
                    scen_techs['hydrothermal_gasification']
                    )
            self.tech_hydrothermal_gasification.initialise_zero(n_days)
            self.tech_instances['hydrothermal_gasification'] =\
                self.tech_hydrothermal_gasification
        
        # Anaerobic digestion upgrade (agu):
        if scen_techs['anaerobic_digestion_upgrade']['deployment']:
            self.tech_anaerobic_digestion_upgrade =\
                dem_techs.AnaerobicDigestionUpgrade(
                    scen_techs['anaerobic_digestion_upgrade']
                    )
            self.tech_anaerobic_digestion_upgrade.initialise_zero(n_days)
            self.tech_instances['anaerobic_digestion_upgrade'] =\
                self.tech_anaerobic_digestion_upgrade
        
        # Anaerobic digestion upgrade hydrogen (aguh):
        if scen_techs['anaerobic_digestion_upgrade_hydrogen']['deployment']:
            self.tech_anaerobic_digestion_upgrade_hydrogen =\
                dem_techs.AnaerobicDigestionUpgradeHydrogen(
                    scen_techs['anaerobic_digestion_upgrade_hydrogen']
                    )
            self.tech_anaerobic_digestion_upgrade_hydrogen.initialise_zero(n_days)
            self.tech_instances['anaerobic_digestion_upgrade_hydrogen'] =\
                self.tech_anaerobic_digestion_upgrade_hydrogen
        
        # Anaerobic digestion CHP (aguc):
        if scen_techs['anaerobic_digestion_chp']['deployment']:
            self.tech_anaerobic_digestion_chp =\
                dem_techs.AnaerobicDigestionCHP(
                    scen_techs['anaerobic_digestion_chp']
                    )
            self.tech_anaerobic_digestion_chp.initialise_zero(n_days)
            self.tech_instances['anaerobic_digestion_chp'] =\
                self.tech_anaerobic_digestion_chp
        
        # Wood gasification upgrade (wgu):
        if scen_techs['wood_gasification_upgrade']['deployment'] :
            self.tech_wood_gasification_upgrade =\
                dem_techs.WoodGasificationUpgrade(
                    scen_techs['wood_gasification_upgrade']
                    )
            self.tech_wood_gasification_upgrade.initialise_zero(n_days)
            self.tech_instances['wood_gasification_upgrade'] =\
                self.tech_wood_gasification_upgrade
        
        # Wood gasification upgrade hydrogen (wguh):
        if scen_techs['wood_gasification_upgrade_hydrogen']['deployment']:
            self.tech_wood_gasification_upgrade_hydrogen =\
                dem_techs.WoodGasificationUpgradeHydrogen(
                    scen_techs['wood_gasification_upgrade_hydrogen']
                    )
            self.tech_wood_gasification_upgrade_hydrogen.initialise_zero(n_days)
            self.tech_instances['wood_gasification_upgrade_hydrogen'] =\
                self.tech_wood_gasification_upgrade_hydrogen
        
        # Wood gasification CHP (wguc):
        if scen_techs['wood_gasification_chp']['deployment']:
            self.tech_wood_gasification_chp =\
                dem_techs.WoodGasificationCHP(
                    scen_techs['wood_gasification_chp']
                    )
            self.tech_wood_gasification_chp.initialise_zero(n_days)
            self.tech_instances['wood_gasification_chp'] =\
                self.tech_wood_gasification_chp

        # Hydrogen production (hydp):            
        if scen_techs['hydrogen_production']['deployment']:
            self.tech_hydrogen_production =\
                dem_techs.HydrogenProduction(
                    scen_techs['hydrogen_production']
                    )
            self.tech_hydrogen_production.initialise_zero(n_days)
            self.tech_instances['hydrogen_production'] =\
                self.tech_hydrogen_production

        # Combined Heat and Power Gas Turbine:
        if scen_techs['chp_gt']['deployment']:
            self.tech_chp_gt = dem_techs.CHPGasTurbine(scen_techs['chp_gt'])
            self.tech_chp_gt.initialise_zero(n_days)
            self.tech_instances['chp_gt'] = self.tech_chp_gt
            
        # Gas turbine (central plant):
        if scen_techs['gas_turbine_cp']['deployment']:
            self.tech_gas_turbine_cp =\
                dem_techs.GasTurbineCP(scen_techs['gas_turbine_cp'])
            self.tech_gas_turbine_cp.initialise_zero(n_days)
            self.tech_instances['gas_turbine_cp'] = self.tech_gas_turbine_cp
        
        # Steam turbine:
        if scen_techs['steam_turbine']['deployment']:
            self.tech_steam_turbine =\
                dem_techs.SteamTurbine(scen_techs['steam_turbine'])
            self.tech_steam_turbine.initialise_zero(n_days)
            self.tech_instances['steam_turbine'] = self.tech_steam_turbine
            
        # Wood boiler (central plant):
        if scen_techs['wood_boiler_sg']['deployment']:
            self.tech_wood_boiler_sg =\
                dem_techs.WoodBoilerSG(scen_techs['wood_boiler_sg'])
            self.tech_wood_boiler_sg.initialise_zero(n_days)
            self.tech_instances['wood_boiler_sg'] = self.tech_wood_boiler_sg
            
        # Waste-to-energy plant:
        if scen_techs['waste_to_energy']['deployment']:
            self.tech_waste_to_energy =\
                dem_techs.WasteToEnergy(scen_techs['waste_to_energy'])
            self.tech_waste_to_energy.initialise_zero(n_days)
            self.tech_instances['waste_to_energy'] = self.tech_waste_to_energy
                    
        # Heat pump (central plant):
        if scen_techs['heat_pump_cp']['deployment']:
            self.tech_heat_pump_cp =\
                dem_techs.HeatPumpCP(scen_techs['heat_pump_cp'])
            self.tech_heat_pump_cp.set_temperature_based_cop(dem_hp_cop_calculation.calculateHPCP_COP(
                self.paths,
                self.tech_heat_pump_cp,
                scen_techs['demand_side']['year'] if scen_techs['scenarios']['demand_side'] else C.METEO_YEAR,
                self.com_nr_majority
            ))
            self.tech_heat_pump_cp.compute_cop_timeseries(self.energy_demand._d_h_profile)
            self.tech_heat_pump_cp.initialise_zero(n_days)
            self.tech_instances['heat_pump_cp'] = self.tech_heat_pump_cp

        # Heat pump (central plant, from low temperature heat):
        if scen_techs['heat_pump_cp_lt']['deployment']:
            self.tech_heat_pump_cp_lt =\
                dem_techs.HeatPumpCPLT(scen_techs['heat_pump_cp_lt'])
            self.tech_heat_pump_cp_lt.initialise_zero(n_days)
            self.tech_instances['heat_pump_cp_lt'] = self.tech_heat_pump_cp_lt


        # Oil boiler (central plant):
        if scen_techs['oil_boiler_cp']['deployment']:
            self.tech_oil_boiler_cp =\
                dem_techs.OilBoilerCP(scen_techs['oil_boiler_cp'])
            self.tech_oil_boiler_cp.initialise_zero(n_days)
            self.tech_instances['oil_boiler_cp'] = self.tech_oil_boiler_cp

        # Electric heater (central plant):
        if scen_techs['electric_heater_cp']['deployment']:
            self.tech_electric_heater_cp =\
                dem_techs.ElectricHeaterCP(scen_techs['electric_heater_cp'])
            self.tech_electric_heater_cp.initialise_zero(n_days)
            self.tech_instances['electric_heater_cp'] = self.tech_electric_heater_cp

        # Wood boiler (central plant):
        if scen_techs['wood_boiler_cp']['deployment']:
            self.tech_wood_boiler_cp =\
                dem_techs.WoodBoilerCP(scen_techs['wood_boiler_cp'])
            self.tech_wood_boiler_cp.initialise_zero(n_days)
            self.tech_instances['wood_boiler_cp'] = self.tech_wood_boiler_cp

        # Gas boiler (central plant):
        if scen_techs['gas_boiler_cp']['deployment']:
            self.tech_gas_boiler_cp =\
                dem_techs.GasBoilerCP(scen_techs['gas_boiler_cp'])
            self.tech_gas_boiler_cp.initialise_zero(n_days)
            self.tech_instances['gas_boiler_cp'] = self.tech_gas_boiler_cp


        #----------------------------------------------------------------------
        # Create tech list from tech instances:        
        self.tech_list = list(self.tech_instances.keys())
        
        #----------------------------------------------------------------------
        # Check tech requirements:            
        if ('anaerobic_digestion_upgrade_hydrogen' in self.tech_list)|('wood_gasification_upgrade_hydrogen' in self.tech_list):
            if not('hydrogen_production' in self.tech_list):
                raise(Exception('Hydrogen is required for this tech list!'))        
        
        #----------------------------------------------------------------------
        # Check overall energy balance:        
        if self.toggle_energy_balance_tests:
            dem_eb.electricity_balance_test(
                scen_techs=scen_techs,
                df_scen=df_scen,
                diff_accepted = C.DIFF_ACC,
                diff_sum_accepted = C.DIFF_SUM_ACC
                )
    
            dem_eb.heat_balance_test(
                df_scen=df_scen,
                optimisation=False,
                diff_accepted = C.DIFF_ACC,
                diff_sum_accepted = C.DIFF_SUM_ACC
                )

        #----------------------------------------------------------------------
            
        # !!! Check if there is unmet demand / supply.
        
        # Electricity generation:
            # grid supply
            # solar PV
            # wind power
        
        # Electricity consumption:
            # electricity demand
            # heat pump
            # electric heater
        
        # Heat generation:
            # heat pump
            # electric heater
            # oil boiler
            # gas boiler
            # wood boiler
            # district heating
            # solar thermal
            # tes discharging
            
        # Heat consumption:
            # heat demand
            # tes charging
            
        # """--------------------------------------------------------------------
        # Add EV demand:
        # """
        # !!!UNDER CONSTRUCTION!!!
        # EVENTUALLY PACK EVERYTHING INTO A FUNCTION (E.G. in dem_demand.py)
        
        # How is this additional demand covered in case no scenario is applied?
        #   --> "unmet demand"
        
        # # Add column for EV demand:
        # if scen_techs['demand_side']['ev_integration'] and scen_techs['scenarios']['demand_side']:
            
        #     if dem_helper.check_if_scenario_active(scen_techs): # Only add demand if scenario is activated

        #         # Read munic file:
        #         munic_file_path = self.ev_profiles_dir + self.ev_munic_name_nr
        #         df_munic_name_nr = pd.read_feather(munic_file_path)
                
        #         # print(df_munic_name_nr.head())
                
        #         munic_name = df_munic_name_nr.loc[
        #             df_munic_name_nr['munic_nr']==self.com_nr,'munic_name'
        #             ]
        #         munic_name = munic_name.iloc[0]
                
        #         if scen_techs['demand_side']['ev_profile'] == 'nominal':
        #             cp_file_dir = self.ev_profiles_dir + self.ev_profile_cp_file
        #             df_ev_profile = pd.read_feather(cp_file_dir)                
                    
        #         elif scen_techs['demand_side']['ev_profile'] == 'upper_limit':                
        #             pd_file_dir = self.ev_profiles_dir + self.ev_profile_pd_file
        #             df_ev_profile = pd.read_feather(pd_file_dir)
                    
        #         elif scen_techs['demand_side']['ev_profile'] == 'lower_limit':
        #             pu_file_dir = self.ev_profiles_dir + self.ev_profile_pu_file
        #             df_ev_profile = pd.read_feather(pu_file_dir)
                    
        #         else:
        #             # tmp_val = scen_techs['demand_side']['ev_profile']
        #             err_msg = (
        #                 "Chosen value for "
        #                 "scen_techs['demand_side']['ev_profile'] is invalid! Must "
        #                 "be one of the following: "
        #                 "'nominal', 'upper_limit', 'lower_limit'"
        #                 )
                    
        #             raise ValueError(err_msg)
                
        #         ts_len = len(self.energy_demand.get_d_e())
                    
        #         tmp_d_e_ev = np.array(df_ev_profile[munic_name])
        #         tmp_d_e_ev = tmp_d_e_ev[:ts_len]
        #         df_scen['d_e_ev'] = tmp_d_e_ev
        #         self.energy_demand.update_d_e_ev(tmp_d_e_ev)
                
        #         tmp_d_e = self.energy_demand.get_d_e() + tmp_d_e_ev
        #         df_scen['d_e'] = tmp_d_e
        #         self.energy_demand.update_d_e(tmp_d_e)
                
            
            # df_scen['d_e_unmet'] =         
        
        # ---------------------------------------------------------------------
        # Update df_scen:

        dem_helper.update_df_results(
            self.energy_demand,
            self.supply,
            self.tech_instances,
            df_scen
            )
        
        """--------------------------------------------------------------------
        Apply scenarios:
        """
        if scen_techs['scenarios']['demand_side'] == True:
            # TO DO: WRAP IN SCENARIO FUNCTION
            
            # -----------------------------------------------------------------
            # Recalculate heat demand:
            # ------------------------
            # d_h_prev = self.energy_demand.get_d_h()
            
            if len(self.com_percent) != 0:
                com_nrs = self.df_com_yr['GGDENR'].unique()
            else:
                com_nrs = []

            # Add column to df_com_yr with future heat demand:
            new_col, self.df_meta = self.energy_demand.add_future_demand_col(
                com_nrs = com_nrs,
                df_com_yr=self.df_com_yr,
                df_meta = self.df_meta,
                year=scen_techs['demand_side']['year'],
                rcp_scenario=scen_techs['demand_side']['rcp_scenario'],
                ts_type=scen_techs['demand_side']['ts_type'],
                yearly_heat_demand_col='heat_energy_demand_estimate_kWh_combined',
                new_header = 'd_h_s_yr_future',
                writeToMeta = True,
                distinguishByConstructionYear = True
                )
            
            #Adjust post-total-renovation heat demands to weather of the future
            new_col, self.df_meta = self.energy_demand.add_future_demand_col(
                com_nrs = com_nrs,
                df_com_yr=self.df_com_yr,
                df_meta = self.df_meta,
                year=scen_techs['demand_side']['year'],
                rcp_scenario=scen_techs['demand_side']['rcp_scenario'],
                ts_type=scen_techs['demand_side']['ts_type'],
                yearly_heat_demand_col='heat_energy_demand_renov_estimate_kWh',
                new_header = 'd_h_s_yr_renov_future',
                writeToMeta = False,
                distinguishByConstructionYear = False
                )
            
            post_renovation_sh_heat_demand_name = 'd_h_s_yr_future_renov_adjusted'
            # Do total renovation and heat generator replacement adjustments:
            self.df_meta = self.energy_demand.renovation_adjustments(
                com_nrs = com_nrs,
                df_com_yr=self.df_com_yr,
                df_meta = self.df_meta,
                year=scen_techs['demand_side']['year'],
                total_renovation_activated= scen_techs['demand_side']['total_renovation'],
                use_constant_total_renovation_rate = scen_techs['demand_side']['use_constant_total_renovation_rate'],
                constant_total_renovation_rate = scen_techs['demand_side']['constant_total_renovation_rate'],
                renovation_scenario=scen_techs['demand_side']['renovation_scenario'], # 'renovation_low', 'renovation_high', 'renovation_base' or 'constant_rate',
                total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios =\
                      scen_techs['demand_side']['total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios'],
                total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios =\
                      scen_techs['demand_side']['total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios'],
                heat_generator_renovation = scen_techs['demand_side']['heat_generator_renovation'],
                optimisation_enabled = scen_techs['optimisation']['enabled'],
                scen_techs = scen_techs,
                data_year = C.DATA_YEAR,
                new_header = post_renovation_sh_heat_demand_name
                )



            hps_existings_cops, hps_new_cops, hps_one_to_one_replacement_cops, tot_heat_existing, tot_heat_new, tot_heat_one_to_one = dem_hp_cop_calculation.calculateCOPs(
                                                     paths = self.paths,
                                                     df_com_yr=self.df_com_yr, 
                                                     quality_factor_ashp_new = scen_techs['heat_pump']['quality_factor_ashp_new'], 
                                                     quality_factor_ashp_old = scen_techs['heat_pump']['quality_factor_ashp_old'],
                                                     quality_factor_gshp_new = scen_techs['heat_pump']['quality_factor_gshp_new'], 
                                                     quality_factor_gshp_old = scen_techs['heat_pump']['quality_factor_gshp_old'],
                                                     com_nr = self.com_nr_majority,
                                                     dem_demand = self.energy_demand,
                                                     weather_year = scen_techs['demand_side']['year'],
                                                     consider_renovation_effects=True,
                                                     total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios =\
                                                        scen_techs['demand_side']['total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios'],
                                                     total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios =\
                                                        scen_techs['demand_side']['total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios'],
                                                     optimisation_enabled = scen_techs['optimisation']['enabled'],
                                                     )

            hps_existings_cops, hps_new_cops, hps_one_to_one_replacement_cops= dem_techs.HeatPump.select_right_cop_mode(scen_techs, 
                              hps_existings_cops, 
                              hps_new_cops, 
                              hps_one_to_one_replacement_cops)

            self.tech_heat_pump.set_cops_existing(hps_existings_cops)
            self.tech_heat_pump.set_cops_new(hps_new_cops)
            self.tech_heat_pump.set_cops_one_to_one_replacement(hps_one_to_one_replacement_cops)
            self.tech_heat_pump.set_tot_heats_for_cop_calculations(tot_heat_existing, tot_heat_new, tot_heat_one_to_one)
            # Update district heating price categories to new heat demands after renovations
            if scen_techs['demand_side']['total_renovation']:
                self.tech_district_heating.update_district_heating_categories(
                    self.df_com_yr, self.energy_demand, 
                    post_renovation_sh_heat_demand_name
                    )
            
            # 'd_h_s_yr_future_renov_adjusted'
            
            self.energy_demand.compute_d_h_yr(
                df_meta = self.df_meta
                )

            # Hourly heat demand:
            self.energy_demand.compute_d_h_hr(
                com_name=self.com_name_,
                # com_nr_original=self.com_nr_original,
                com_nr_original=self.com_nr_majority, # changed: 23.12.2025
                com_lat=self.com_lat,
                com_lon=self.com_lon,
                com_alt=self.com_alt,
                tf_start=C.tf_meteostat_start,
                tf_end=C.tf_meteostat_end
                )
            
            # dem_hp_cop_calculation.calculateCOP_no_renov()

            # Allocate heating systems to demand:
            self.energy_demand.compute_d_h_hr_mix(
                df_meta = self.df_meta,
                tech_instances=self.tech_instances,
                n_days=n_days
                )

            self.energy_demand.reduce_timeframe(n_days)


            #Save amount of power generation that needs replacement for each of the existing technologies in tech instance.
            if scen_techs['demand_side']['heat_generator_renovation']:
                
                techstoacton = {'ob': 'oil_boiler', 'gb': 'gas_boiler', 
                                'eh': 'electric_heater', 'hp': 'heat_pump', 
                                'wb': 'wood_boiler', 'dh': 'district_heating', 
                                'solar': 'solarthermal_rooftop'}
                for k in techstoacton.keys():
                    power_up_for_replacement = scen_techs['demand_side']['heat_generator_replacement_rates']['v_h_'+k]*self.tech_instances[techstoacton[k]].get_v_h().max()
                    self.tech_instances[techstoacton[k]].set_power_up_for_replacement(power_up_for_replacement)

            # d_h_new = self.energy_demand.get_d_h()
            # d_h_unmet = d_h_new - d_h_prev
            # self.energy_demand.update_d_h_unmet(d_h_unmet)
            
            # -----------------------------------------------------------------             
            # Recalculate electricity demand:
            # -------------------------------
            # d_e_prev = self.energy_demand.get_d_e()
            # m_e_prev = self.tech_grid_supply.get_m_e()        
            
            if scen_techs['demand_side']['ev_integration']:
                print('\n demand_side')
                self.energy_demand.compute_d_e_ev(
                    ev_profiles_dir=self.ev_profiles_dir,
                    ev_munic_name_nr_file=self.ev_munic_name_nr,
                    ev_profile_cp_file=self.ev_profile_cp_file,
                    ev_profile_fe_file=self.ev_profile_fe_file,
                    ev_profile_pd_file=self.ev_profile_pd_file,
                    ev_profile_pu_file=self.ev_profile_pu_file,                    
                    ev_integration_factor=scen_techs['demand_side']['ev_integration_factor'],
                    com_percent = self.com_percent_2,
                    optimisation = scen_techs['optimisation']['enabled'],
                    ev_flexibility = scen_techs['demand_side']['ev_flexibility'],
                    )
                
            # Electricity demand for heating (hourly and annual):
            self.energy_demand.compute_d_e_h(self.tech_instances)

            # Total electricity demand (hourly and annual):
            self.energy_demand.compute_d_e()

            # d_e_new = self.energy_demand.get_d_e()       
            
            # Update local electricity mix:
            dem_eb.get_local_electricity_mix(self.energy_demand, self.tech_instances)
            
            m_e_updated = self.tech_grid_supply.get_m_e()
            self.tech_grid_supply.update_m_e(m_e_updated)
            
            # m_e_diff = self.tech_grid_supply.compute_m_e_diff(d_e_new, d_e_prev)            
            # m_e_new = m_e_prev + m_e_diff            
            # self.tech_grid_supply.update_m_e(m_e_new)
            
            # Unmet electricity demand:
            # d_e_new = self.energy_demand.get_d_e()
            # d_e_unmet = d_e_new - d_e_prev
            # self.energy_demand.update_d_e_unmet(d_e_unmet)
            
            
            # -----------------------------------------------------------------
            # Update df_scen:
            dem_helper.update_df_results(
                self.energy_demand,
                self.supply,
                self.tech_instances,
                df_scen
                )
            
            #------------------------------------------------------------------
            # Check overall energy balance:            
            if self.toggle_energy_balance_tests:
                dem_eb.electricity_balance_test(
                    scen_techs=scen_techs,
                    df_scen=df_scen,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
                dem_eb.heat_balance_test(
                    df_scen=df_scen,
                    optimisation=False,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )

        #Adjust fossil heater retrofit to renovation rate of heat generators. This is only done if 'demand_side''act_on_fossil_heater_retrofit' is True
        #This is only done if the optimization is not activation. If the optimization is activated, the replacement of heat generators is subject to optimization.
        techstoacton = {'ob': 'oil_boiler', 'gb': 'gas_boiler', 'eh': 'electric_heater'}
        techstoacton_fhrp_keys = {'ob': 'oil_boiler_replacement_factor', 'gb': 'gas_boiler_replacement_factor', 'eh': 'electric_boiler_replacement_factor'}
        if scen_techs['demand_side']['act_on_fossil_heater_retrofit']:
            if scen_techs['scenarios']['fossil_heater_retrofit'] == True:
                if scen_techs['scenarios']['demand_side'] == True:
                    if scen_techs['optimisation']['enabled'] == False:
                        for techkey in techstoacton.keys():
                            tech_inst = self.tech_instances[techstoacton[techkey]]
                            replacement_factor = scen_techs['fossil_heater_retrofit'][techstoacton_fhrp_keys[techkey]]
                            if replacement_factor < scen_techs['demand_side']['heat_generator_replacement_rates']['v_h_'+techkey]:
                                scen_techs['fossil_heater_retrofit'][techstoacton_fhrp_keys[techkey]] = float(scen_techs['demand_side']['heat_generator_replacement_rates']['v_h_'+techkey])
            else:
                if scen_techs['scenarios']['demand_side'] == True:
                    if scen_techs['optimisation']['enabled'] == False:
                        scen_techs['scenarios']['fossil_heater_retrofit'] = True
                        for techkey in techstoacton.keys():
                            tech_inst = self.tech_instances[techstoacton[techkey]]
                            replacement_factor = scen_techs['fossil_heater_retrofit'][techstoacton_fhrp_keys[techkey]]
                            scen_techs['fossil_heater_retrofit'][techstoacton_fhrp_keys[techkey]]=float(scen_techs['demand_side']['heat_generator_replacement_rates']['v_h_'+techkey])

        if scen_techs['scenarios']['fossil_heater_retrofit'] == True:
            print('\n fossil_heater_retrofit')
            # Check if required technologies are deployed:
            required_techs = [
                'oil_boiler',
                'gas_boiler',
                'heat_pump',
                'solar_pvrooftop',
                'wind_power',
                'hydro_power',
                'grid_supply'
                ]
            dem_helper.check_tech_for_scenario(
                techs=required_techs,
                scenario='fossil_heater_retrofit',
                scen_techs=scen_techs
                )
            
            # Reset unmet demands (must be met through scenario):
            # self.energy_demand.reset_d_e_unmet()
            # self.energy_demand.reset_d_h_unmet()

            # Apply scenario:

            dem_scenarios.scenario_heater_electric_to_hp(
                self.energy_demand,
                scen_techs,
                self.tech_instances
                )


            dem_scenarios.scenario_heater_oil_to_hp(
                self.energy_demand,
                scen_techs,
                self.tech_instances
                )
            
            dem_scenarios.scenario_heater_gas_to_hp(
                self.energy_demand,
                scen_techs,
                self.tech_instances
                )
            
            # -----------------------------------------------------------------
            # Update df_scen:
            dem_helper.update_df_results(
                self.energy_demand,
                self.supply,
                self.tech_instances,
                df_scen
                )
            
            #------------------------------------------------------------------
            # Check overall energy balance:            
            if self.toggle_energy_balance_tests:
                dem_eb.electricity_balance_test(
                    scen_techs=scen_techs,
                    df_scen=df_scen,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
                dem_eb.heat_balance_test(
                    df_scen=df_scen,
                    optimisation=False,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
            
        if scen_techs['scenarios']['pv_integration'] == True:
            print('\n pv_integration')
            # Check if required technologies are deployed:
            required_techs = ['solar_pvrooftop', 'wind_power','grid_supply']
            dem_helper.check_tech_for_scenario(
                techs=required_techs,
                scenario='pv_integration',
                scen_techs=scen_techs
                )
            
            # Reset unmet demands (must be met through scenario):
            # self.energy_demand.reset_d_e_unmet()
            # self.energy_demand.reset_d_h_unmet()
            
            # Apply scenario:
            dem_scenarios.scenario_pv_integration(
                self.energy_demand,
                scen_techs,
                self.tech_instances
                )
                # scen_techs=scen_techs,
                # df_scen=df_scen,
                # tech_solar_pv=self.tech_solar_pv,
                # tech_wind_power=self.tech_wind_power,
                # tech_biomass=self.tech_biomass,
                # tech_hydro_power=self.tech_hydro_power,
                # tech_grid_supply=self.tech_grid_supply,
                # )
                
            # -----------------------------------------------------------------
            # Update df_scen:
            dem_helper.update_df_results(
                self.energy_demand,
                self.supply,
                self.tech_instances,
                df_scen
                )
            
            #------------------------------------------------------------------
            # Check overall energy balance:            
            if self.toggle_energy_balance_tests:
                dem_eb.electricity_balance_test(
                    scen_techs=scen_techs,
                    df_scen=df_scen,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
                dem_eb.heat_balance_test(
                    df_scen=df_scen,
                    optimisation=False,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
            
        if scen_techs['scenarios']['wind_integration'] == True:
            print('\n wind_integration')
            # Check if required technologies are deployed:
            required_techs = ['wind_power', 'grid_supply']
            dem_helper.check_tech_for_scenario(
                techs=required_techs,
                scenario='wind_integration',
                scen_techs=scen_techs
                )
            
            # Reset unmet demands (must be met through scenario):
            # self.energy_demand.reset_d_e_unmet()
            # self.energy_demand.reset_d_h_unmet()
            
            # Apply scenario:
            dem_scenarios.scenario_wind_integration(
                self.energy_demand,
                scen_techs,
                self.tech_instances
                )
                # scen_techs=scen_techs,
                # df_scen=df_scen,
                # tech_solar_pv=self.tech_solar_pv,
                # tech_wind_power=self.tech_wind_power,
                # tech_biomass=self.tech_biomass,
                # tech_hydro_power=self.tech_hydro_power,
                # tech_grid_supply=self.tech_grid_supply,
                # )
                
            # -----------------------------------------------------------------
            # Update df_scen:
            dem_helper.update_df_results(
                self.energy_demand,
                self.supply,
                self.tech_instances,
                df_scen
                )
            
            #------------------------------------------------------------------
            # Check overall energy balance:            
            if self.toggle_energy_balance_tests:
                dem_eb.electricity_balance_test(
                    scen_techs=scen_techs,
                    df_scen=df_scen,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
                dem_eb.heat_balance_test(
                    df_scen=df_scen,
                    optimisation=False,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
        if (scen_techs['scenarios']['battery_energy_storage'] == True 
            and scen_techs['scenarios']['thermal_energy_storage'] == True):

            print("Scenarios are called with both the manual TES and BES scenarios activated."
            "This combination is not supported, since it can and does lead to problems"
            "in the energy balance. Please deactivate either the manual TES ('thermal_energy_storage') "
            "or the manual "
            "BES ('battery_energy_storage') scenario ")
            raise NotImplementedError("Combination of TES and BES scenario not supported.")

        if scen_techs['scenarios']['battery_energy_storage'] == True:
            print('\n battery_energy_storage')
            # Check if required technologies are deployed:
            required_techs = [
                'bes',
                'solar_pvrooftop',
                'wind_power',
                'hydro_power',
                'grid_supply',
                ]
            dem_helper.check_tech_for_scenario(
                techs=required_techs,
                scenario='battery_energy_storage',
                scen_techs=scen_techs
                )
            
            # Apply scenario:
            dem_scenarios.scenario_battery_energy_storage_via_pv(
                self.energy_demand,
                scen_techs,
                self.tech_instances
                )
                # scen_techs=scen_techs,
                # df_scen=df_scen,
                # tech_tes=self.tech_tes,
                # tech_solar_pv=self.tech_solar_pv,
                # tech_wind_power=self.tech_wind_power,
                # tech_biomass=self.tech_biomass,
                # tech_hydro_power=self.tech_hydro_power,
                # tech_heat_pump=self.tech_heat_pump,
                # tech_grid_supply=self.tech_grid_supply,
                # tech_electric_heater=self.tech_electric_heater     
                # )
                
            # -----------------------------------------------------------------
            # Update df_scen:
            dem_helper.update_df_results(
                self.energy_demand,
                self.supply,
                self.tech_instances,
                df_scen
                )
            
            print('\nDone')
            
            #------------------------------------------------------------------
            # Check overall energy balance:            
            if self.toggle_energy_balance_tests:
                dem_eb.electricity_balance_test(
                    scen_techs=scen_techs,
                    df_scen=df_scen,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
                dem_eb.heat_balance_test(
                    df_scen=df_scen,
                    optimisation=False,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )





        if scen_techs['scenarios']['thermal_energy_storage'] == True:
            print('\n thermal_energy_storage')
            # Check if required technologies are deployed:
            required_techs = [
                'tes_decentralised',
                'solar_pvrooftop',
                'wind_power',
                'hydro_power',
                'heat_pump',
                'grid_supply',
                'electric_heater'
                ]
            dem_helper.check_tech_for_scenario(
                techs=required_techs,
                scenario='thermal_energy_storage',
                scen_techs=scen_techs
                )
            
            # Reset unmet demands (must be met through scenario):
            # self.energy_demand.reset_d_e_unmet()
            # self.energy_demand.reset_d_h_unmet()
            
            # Apply scenario:
            dem_scenarios.scenario_thermal_energy_storage_via_pv_hp(
                self.energy_demand,
                scen_techs,
                self.tech_instances
                )
                # scen_techs=scen_techs,
                # df_scen=df_scen,
                # tech_tes=self.tech_tes,
                # tech_solar_pv=self.tech_solar_pv,
                # tech_wind_power=self.tech_wind_power,
                # tech_biomass=self.tech_biomass,
                # tech_hydro_power=self.tech_hydro_power,
                # tech_heat_pump=self.tech_heat_pump,
                # tech_grid_supply=self.tech_grid_supply,
                # tech_electric_heater=self.tech_electric_heater     
                # )
                
            # -----------------------------------------------------------------
            # Update df_scen:
            dem_helper.update_df_results(
                self.energy_demand,
                self.supply,
                self.tech_instances,
                df_scen
                )
            
            print('\nDone')
            
            #------------------------------------------------------------------
            # Check overall energy balance:            
            if self.toggle_energy_balance_tests:
                dem_eb.electricity_balance_test(
                    scen_techs=scen_techs,
                    df_scen=df_scen,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
                dem_eb.heat_balance_test(
                    df_scen=df_scen,
                    optimisation=False,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
            
        if scen_techs['scenarios']['nuclear_phaseout'] == True:
            print('\nnuclear_phaseout')
            
            # el_mix_filename_path = (self.energy_mix_CH_dir +
            #                         self.electricity_mix_file
            #                         )
            
            # e_import_filename_path = (self.energy_mix_CH_dir +
            #                           self.electricity_import_file
            #                           )
            
            # Reset unmet demands (must be met through scenario):
            self.energy_demand.reset_d_e_unmet()
            self.energy_demand.reset_d_h_unmet()
            
            dem_scenarios.scenario_nuclear_phaseout(
                scen_techs=scen_techs,
                tech_instances = self.tech_instances,
                df_scen=df_scen,
                # el_mix_filename_path = el_mix_filename_path,
                # e_import_filename_path = e_import_filename_path
            
                # energy_mix_CH_dir=self.energy_mix_CH_dir,
                # strom_profiles_2050_file=self.strom_profiles_2050_file,
                # electricity_mix_file=self.electricity_mix_file,
                # electricity_mix_totals_file=self.electricity_mix_totals_file,
                # electricity_import_file=self.electricity_import_file
                )
            
            # -----------------------------------------------------------------
            # Update df_scen:
            dem_helper.update_df_results(
                self.energy_demand,
                self.supply,
                self.tech_instances,
                df_scen
                )
            
        """--------------------------------------------------------------------
        Apply optimisation:
        """
        if scen_techs['optimisation']['enabled'] == True:
            # print(df_scen.isna().sum().loc[df_scen.isna().sum() != 0])
            # Reset unmet demands (must be met through scenario):
            self.energy_demand.reset_d_e_unmet()
            self.energy_demand.reset_d_h_unmet()
            
            if scen_techs['optimisation']['clustering']:
                
                df_scen_clustering = self.df_base_clustering.loc[:ts_num, (slice(None), slice(None))]
                # print(df_scen_clustering)
                
                from district_energy_model import dem_calliope_clustering
                optimiser = dem_calliope_clustering.CalliopeOptimiser(
                    tech_list=self.tech_list,
                    scen_techs=scen_techs,
                    df_scen=df_scen_clustering,
                    com_name=self.com_name_,
                    com_file=self.df_com_yr
                    )
                opt_results, model = optimiser.run_optimisation()
                return
            
            else:
                from district_energy_model import dem_calliope
                optimiser = dem_calliope.CalliopeOptimiser(
                    tech_list=self.tech_list,
                    tech_instances=self.tech_instances,
                    energy_demand=self.energy_demand,
                    supply=self.supply,
                    com_name=self.com_name_,
                    scen_techs=scen_techs,
                    # opt_metrics=scen_techs['optimisation'],
                    files_path = self.results_path
                    )
                opt_results, model = optimiser.run_optimisation()
                dict_total_costs =\
                    optimiser.get_optimal_output_df(
                    opt_results=opt_results
                    )
                    
                # -------------------------------------------------------------
                # Update df_scen:
                dem_helper.update_df_results(
                    energy_demand=self.energy_demand,
                    supply=self.supply,
                    tech_instances=self.tech_instances,
                    df_results=df_scen
                    )
                    
                if self.toggle_energy_balance_tests:
                    dem_eb.electricity_balance_test(
                        scen_techs=scen_techs,
                        df_scen=df_scen,
                        optimisation=True,
                        diff_accepted = C.DIFF_ACC,
                        diff_sum_accepted = C.DIFF_SUM_ACC
                        )
                    dem_eb.heat_balance_test(
                         df_scen=df_scen,
                         diff_accepted = C.DIFF_ACC,
                         diff_sum_accepted = C.DIFF_SUM_ACC
                         )
                
        else:
            
            # Compute costs in case no optimisation is applied:
            dict_total_costs = {} # !!! a separate module for cost calculations must be implemented
            model = 0

        #----------------------------------------------------------------------
        # Update df_scen:
        dem_helper.update_df_results(
            self.energy_demand,
            self.supply,
            self.tech_instances,
            df_scen
            )
            
        #----------------------------------------------------------------------
        # CO2 emissions:
        # df_scen = dem_emissions.add_emissions_CO2(scen_techs, df_scen)          
                
        #----------------------------------------------------------------------
        # Check for negative values:
        if self.toggle_energy_balance_tests:
            exempted_columns_ = ['d_e_ev_cp_dev', 'd_e_ev_cp_dev_neg']
            dem_helper.positive_values_test_df(
                df_values = df_scen,
                description = 'df_scen',
                error_accepted=C.NEG_ACC,
                exempted_columns=exempted_columns_
                )
        
        #----------------------------------------------------------------------            
        # Change column order of df_scen:
        arg = df_scen.columns.argsort()
        df_scen = df_scen[df_scen.columns[arg]]
        
        dict_yr_scen = dem_helper.create_dict_yr(df_scen)
        
        #----------------------------------------------------------------------        
        self.scen_techs = scen_techs
        self.df_scen = df_scen
        self.dict_yr_scen = dict_yr_scen
        self.dict_total_costs = dict_total_costs
        self.model = model
        self.scenario_generated = True
        
        # print("\nprint in dem.py:")
        # print("\nOil Boiler:")
        # print(df_scen['v_h_ob']/df_scen['d_h']*100)
        # print("")
        # print("\nCHP GT:")
        # print(df_scen['v_h_chp_gt']/df_scen['d_h']*100)
        # print("")
        # print("\nHP:")
        # print(df_scen['v_h_hp']/df_scen['d_h']*100)
        # print("")
        # print("\nDistrict Heating:")
        # print(df_scen['v_h_dh']/df_scen['d_h']*100)
        
    
    def generate_pareto_monetary_co2(self, scen_techs, N_pareto):
        """
        Return the results of multiple optimisations for generating a pareto
        front based on the epsilon-constraint method. Selected weights for
        optimisation objectives are overwritten in this case.
        # A scenario must be computed prior to generating a pareto front
        # (i.e. by running the generate_scenario(...) method).

        Parameters
        ----------
        scen_techs : dictionary
            Dictionary containing info about technologies.
        df_scen : pandas dataframe
            Dataframe with resulting hourly values from previous scenario
            generation.
        N_pareto : int
            Number (N) of points on pareto front. N is used to calculate the
            intervals in the epsilon-constraint method.

        Returns
        -------
        pareto_results : list
            List of optimisation results. Each items in the list is a dict
            containing the results of one optimisation. Data in this
            dict can be accessed via the following keys:'eps_n',
            'dict_yr_scen', 'dict_total_costs', 'scen_techs', 'input_data'.

        """
        
        # Epsilon-Constraint method:
            # a. Run optimisation with monetary_w = 1.0, co2_w = 0.0 => eps_max
            # b. Run optimisation with monetary_w = 0.0, co2_w = 1.0 => eps_min
            # c. Define number of points on pareto front N_pareto (from input)
            # d. Calculate steps: eps_diff = (eps_max - eps_min)/(N_pareto-1)
            # e. Calculate epsilons: eps_n = eps_max - n*eps_diff
            # f. Run single-objective optimisation for each epsilon, with the
            #    constraint total_cost_co2 <= eps_n
        
        # ENERGY-BALANCE TEST AFTER EACH RUN!!!
        
        from district_energy_model import dem_calliope
        
        # =====================================================================
        # DELETE IF NOT USED
        # ------------------
        # # Run scenario without optimisation, to generate input for pareto optimisation:
        # tmp_opt_enabled_orig = scen_techs['optimisation']['enabled'] # save initial setting
        # scen_techs['optimisation']['enabled'] = False # deactivate optimisation to generate scenario
        
        # self.generate_scenario(scen_techs) # generate scenario without optimisation
        # df_scen = self.df_scen
        
        # scen_techs['optimisation']['enabled'] = tmp_opt_enabled_orig # change back to initial setting
        # =====================================================================
        
        # ======================================================================================================
        # Run scenario without optimisation, to generate input for pareto optimisation:
        def reset_optimiser():
            self.scenario_generated = False
            scen_techs['optimisation']['enabled'] = False # deactivate optimisation to generate scenario
            self.__generate_base_scenario(scen_techs)
            self.generate_scenario(scen_techs) # generate scenario without optimisation
            df_scen = self.df_scen            
            
            # Enable optimisation:
            scen_techs['optimisation']['enabled'] = True
            
            # Create optimiser instance:        
            optimiser = dem_calliope.CalliopeOptimiser(
                tech_list=self.tech_list,
                tech_instances=self.tech_instances,
                energy_demand=self.energy_demand,
                supply=self.supply,
                com_name=self.com_name_,
                opt_metrics=scen_techs['optimisation'],
                files_path=self.results_path
                )
            
            return df_scen, optimiser
        
        # Set all objective-weights to 0:
        scen_techs['optimisation']['objective_monetary'] = 0.0
        scen_techs['optimisation']['objective_co2'] = 0.0
        scen_techs['optimisation']['objective_ess'] = 0.0
        scen_techs['optimisation']['tss'] = 0.0
        
        
        df_scen, optimiser = reset_optimiser()
        
        # # Run scenario without optimisation, to generate input for pareto optimisation:
        # scen_techs['optimisation']['enabled'] = False # deactivate optimisation to generate scenario
        # self.generate_scenario(scen_techs) # generate scenario without optimisation
        # df_scen = self.df_scen            
        
        # # Enable optimisation:
        # scen_techs['optimisation']['enabled'] = True      
        
        
        # # ---------------------------------------------------------------------
        # # Create optimiser instance:        
        # optimiser = dem_calliope.CalliopeOptimiser(
        #     tech_list=self.tech_list,
        #     tech_instances=self.tech_instances,
        #     energy_demand=self.energy_demand,
        #     supply=self.supply,
        #     com_name=self.com_name_,
        #     opt_metrics=scen_techs['optimisation'],
        #     files_path=paths.results_path
        #     )

        # ---------------------------------------------------------------------
        # Run optimisation for co2 objective to obtain eps_min:
            
        # Update weights of pareto-objectives:
        scen_techs['optimisation']['objective_monetary'] = 0.00001 ## minimal cost to avoid investment in non-used capacity; CAREFUL: too small values (e.g. 1e-12 yields worse results, most likely due to numerical instability)
        scen_techs['optimisation']['objective_co2'] = 1.0
        
        # Run optimisation:
        opt_results, _ = optimiser.run_optimisation()
        
        dict_total_costs =\
            optimiser.get_optimal_output_df(
            opt_results=opt_results
            )
        
        # Update df_scen and dict_yr_scen:
        dem_helper.update_df_results(
            energy_demand=self.energy_demand,
            supply=self.supply,
            tech_instances=self.tech_instances,
            df_results=df_scen
            )
        dict_yr_scen = dem_helper.create_dict_yr(df_scen)
        
        #--------------------------------------
        # Check overall energy balance:
        
        if self.toggle_energy_balance_tests:
            dem_eb.electricity_balance_test(
                scen_techs=scen_techs,
                df_scen=df_scen,
                optimisation=True,
                diff_accepted = C.DIFF_ACC,
                diff_sum_accepted = C.DIFF_SUM_ACC
                )
            dem_eb.heat_balance_test(
                df_scen=df_scen,
                optimisation=True,
                diff_accepted = C.DIFF_ACC,
                diff_sum_accepted = C.DIFF_SUM_ACC
                )
        
        #--------------------------------------
        
        eps_min = dict_total_costs['co2']['total'] # [kgCO2]
                
        # Save results to dict:
        tmp_results_eps_min = {'eps_n':eps_min} # in this case: eps_n = eps_min
        tmp_results_eps_min['df_scen'] = df_scen
        tmp_results_eps_min['dict_yr_scen'] = dict_yr_scen
        tmp_results_eps_min['dict_total_costs'] = dict_total_costs
        tmp_results_eps_min['scen_techs'] = scen_techs
        tmp_results_eps_min['input_data'] = self.get_input_data()
        
        # ---------------------------------------------------------------------
        # Run optimisation for monetary objective to obtain eps_max:

        
        # Reset model:
        df_scen, optimiser = reset_optimiser()

            
        # Update weights of pareto-objectives:
        scen_techs['optimisation']['objective_monetary'] = 1.0
        scen_techs['optimisation']['objective_co2'] = 0.0
        
        # Run optimisation:
        opt_results, model = optimiser.run_optimisation()
        
        dict_total_costs =\
            optimiser.get_optimal_output_df(
            opt_results=opt_results
            )
            
        # Update df_scen and dict_yr_scen:
        dem_helper.update_df_results(
            energy_demand=self.energy_demand,
            supply=self.supply,
            tech_instances=self.tech_instances,
            df_results=df_scen
            )
        dict_yr_scen = dem_helper.create_dict_yr(df_scen)
        
        #--------------------------------------
        # Check overall energy balance:
        
        if self.toggle_energy_balance_tests:
            dem_eb.electricity_balance_test(
                scen_techs=scen_techs,
                df_scen=df_scen,
                optimisation=True,
                diff_accepted = C.DIFF_ACC,
                diff_sum_accepted = C.DIFF_SUM_ACC
                )
            dem_eb.heat_balance_test(
                df_scen=df_scen,
                optimisation=True,
                diff_accepted = C.DIFF_ACC,
                diff_sum_accepted = C.DIFF_SUM_ACC
                )
        
        #--------------------------------------
        
        eps_max = dict_total_costs['co2']['total'] # [kgCO2]
        # print(f"\n\n EPS MAX: {eps_max} oooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo")
        
        # Save results to dict:
        tmp_results_eps_max = {'eps_n':eps_max} # in this case: eps_n = eps_max
        tmp_results_eps_max['df_scen'] = df_scen
        tmp_results_eps_max['dict_yr_scen'] = dict_yr_scen
        tmp_results_eps_max['dict_total_costs'] = dict_total_costs
        tmp_results_eps_max['scen_techs'] = scen_techs
        tmp_results_eps_max['input_data'] = self.get_input_data()
        
        # pareto_results.append(tmp_dict_results)

        
        # ---------------------------------------------------------------------
        # Compute delta-epsilon:
            
        # eps_N = scen_techs['optimisation']['N_pareto'] # input no longer taken from scen_techs
        eps_N = N_pareto
        eps_pareto_front = eps_max - eps_min
        eps_delta = eps_pareto_front / (eps_N - 1)
        
        # ---------------------------------------------------------------------
        # Initialise list to store results of each optimisation run:
        pareto_results = []
        
        # Safe results of left epsilon-boundary:
        pareto_results.append(tmp_results_eps_min)
        
        # ---------------------------------------------------------------------
        # Run optimisations with epsilon constraints in regular intervals
        # between min and max:
            
        # Run single-objective optimisation with monetary objective
        # (co2 objective is handled via epsilon-constraints):
        scen_techs['optimisation']['objective_monetary'] = 1.0
        scen_techs['optimisation']['objective_co2'] = 0.0

        for i in range(eps_N-2):
            # The first (min) and last (max) value has already been computed.
            # This loop computes the values in between (n=1 to n=N-2).
            
            df_scen, optimiser = reset_optimiser()
        
            n = i + 1
        
            eps_n = eps_min + n*eps_delta
            
            print("\n")
            print("=======================================================")
            print("=======================================================")
            print(f"Compute Pareto point {n+1}/{eps_N}")
            print(f"\nEpsilon: {eps_n}")
            
            # opt_results, _ = optimiser.model_rerun_e_constr(model, eps_n)
            opt_results, _ = optimiser.run_optimisation(
                rerun_eps=True,
                eps_n=eps_n
                )
            
            dict_total_costs =\
                optimiser.get_optimal_output_df(
                opt_results=opt_results
                )
                
            # Update df_scen and dict_yr_scen:
            dem_helper.update_df_results(
                energy_demand=self.energy_demand,
                supply=self.supply,
                tech_instances=self.tech_instances,
                df_results=df_scen
                )
            dict_yr_scen = dem_helper.create_dict_yr(df_scen)
            
            #--------------------------------------
            # Check overall energy balance:
            
            if self.toggle_energy_balance_tests:
                dem_eb.electricity_balance_test(
                    scen_techs=scen_techs,
                    df_scen=df_scen,
                    optimisation=True,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
                dem_eb.heat_balance_test(
                    df_scen=df_scen,
                    optimisation=True,
                    diff_accepted = C.DIFF_ACC,
                    diff_sum_accepted = C.DIFF_SUM_ACC
                    )
            
            #--------------------------------------
            
            # Save results to dict:
            tmp_results_eps_n = {'eps_n':eps_n} # [kgCO2]
            tmp_results_eps_n['df_scen'] = df_scen
            tmp_results_eps_n['dict_yr_scen'] = dict_yr_scen
            tmp_results_eps_n['dict_total_costs'] = dict_total_costs
            tmp_results_eps_n['scen_techs'] = scen_techs
            tmp_results_eps_n['input_data'] = self.get_input_data()
            
            kgCO2_ = dict_total_costs['co2']['total']
            # print(f"\nkgCO2: {kgCO2_}")
            
            pareto_results.append(tmp_results_eps_n)
            
            del tmp_results_eps_n
        
        # Safe results of right epsilon-boundary:
        pareto_results.append(tmp_results_eps_max)
        
        self.pareto_results = pareto_results
        self.pareto_results_generated = True
        self.scenario_generated = False
        self.pareto_results_loaded = False
            
    def load_pareto_monetary_co2(self, filename):
        self.pareto_results = dem_helper.load_from_pickle(
            dir_path=self.results_path,
            filename=filename
            )
        self.pareto_results_loaded = True
        
    def save_results(self):
        
        if self.pareto_results_loaded == True:
            if self.scenario_generated == True:
                dem_output.input_to_file(self.results_path, self.list_input_data)
                dem_output.hourly_results_to_file(self.results_path, self.df_scen)
                dem_output.scen_techs_to_file(self.results_path, self.scen_techs)
                dem_output.annual_results_to_file(self.results_path, self.dict_yr_scen)
                dem_output.total_costs_to_file(self.results_path, self.dict_total_costs)
            else:
                return
        elif self.pareto_results_generated == True:
            # Save results to pickle file:
            dem_helper.save_to_pickle(
                obj=self.pareto_results,
                dir_path=self.results_path,
                filename='pareto_results'
                )
            # Create csv file with pareto metrics:
            dem_output.pareto_metrics_to_csv(
                dir_path=self.results_path,
                pareto_results=self.pareto_results
                )
        elif self.scenario_generated == True:
            dem_output.input_to_file(self.results_path, self.list_input_data)
            dem_output.hourly_results_to_file(self.results_path, self.df_scen)
            dem_output.scen_techs_to_file(self.results_path, self.scen_techs)
            dem_output.annual_results_to_file(self.results_path, self.dict_yr_scen)
            dem_output.total_costs_to_file(self.results_path, self.dict_total_costs)
        else:
            raise(Exception('No Scenario has been generated!'))
            
    def plot(self):
        if self.pareto_results_generated or self.pareto_results_loaded:
            pareto_results=self.pareto_results
            self.dict_yr_scen = 0.0
            self.df_scen = 0.0
        else:
            pareto_results=0
        
        dem_output.plot(
            pareto_results_loaded=self.pareto_results_loaded,
            scenario_generated=self.scenario_generated,
            pareto_results=pareto_results,
            pareto_results_generated=self.pareto_results_generated,
            results_path=self.results_path,
            # dict_yr_scen=0,
            # df_scen=0,
            dict_yr_scen=self.dict_yr_scen,
            df_scen=self.df_scen,                
            )
            
    def run(self,
            scen_techs,
            toggle_load_pareto_results = False, 
            # toggle_create_pareto_monetary_vs_co2 = False, 
            toggle_save_results = False, 
            toggle_plot = False,
            # N_pareto = []
            ):
        
        
        # Record the starting time
        start_time = time.time()
        
        # Get optimisation inputs:
        opt_active = scen_techs['optimisation']['enabled']
        pareto_active = scen_techs['optimisation']['pareto_monetary_co2']
        
        if toggle_load_pareto_results:
            print("\nLoading results from file ...")
            self.load_pareto_monetary_co2(filename='pareto_results')

        # elif toggle_create_pareto_monetary_vs_co2:
        elif opt_active and pareto_active:
            print("\nCreating pareto front: monetary vs. CO2")
            self.generate_pareto_monetary_co2(
                scen_techs=scen_techs,
                N_pareto=scen_techs['optimisation']['N_pareto']
                )

        else:
            print("\nGenerating Scenario")
            self.generate_scenario(scen_techs)
            
        # Record the ending time
        end_time = time.time()
        
        # Calculate the elapsed time
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        print(f'\nModel execution time: {int(minutes)} min {seconds:.1f} s')
            
        """--------------------------------------------------------------------
        Save results to file:
        """
        if toggle_save_results:
            self.save_results()

        """----------------------------------------------------------------------------
        Plot results:
        """
        if toggle_plot:
            print('\nPlotting results ...')
            self.plot()
        
    def get_hourly_results(self):
        if self.generate_scenario == False:
            raise(Exception('No Scenario Results Exist!'))
        else:
            df_scen_d = pd.DataFrame(index = range(365))
            
            for column in self.df_scen.columns:
                # print(column)
                df_scen_d[column] = 0.0
                result_temp = np.zeros(365)
                
                for i in range(24):
                    arg = self.df_scen.index%24 == i
                    result_temp += np.array(self.df_scen.loc[arg, column])
                    
                df_scen_d[column] += result_temp
            
            return df_scen_d
        
    def hourly_results(self):
        return self.df_scen
    
    def annual_results(self):
        return self.dict_yr_scen
    
    def total_cost(self):
        return self.dict_total_costs
        
    def get_plot_infos_RT(self):
        return dem_helper.get_plot_infos_RT()
    
    def get_input_data(self):
        return self.list_input_data
    
        