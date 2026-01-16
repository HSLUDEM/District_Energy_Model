# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 14:39:11 2024

@author: UeliSchilt
"""

# from pathlib import Path

# # -----------------------------------------------------------------------------
# # recommender tool:
# if True:
#     # path_strt1 = '../..'

#     # ----------------------------------------------------------------------------- 
#     # Determine project root from this file's location, independent of CWD
#     # paths.py is in: <project_root>/src/district_energy_model/paths.py
#     # so project_root = parents[2]
#     PROJECT_ROOT = Path(__file__).resolve().parents[2]
#     path_strt1 = str(PROJECT_ROOT)  # keep as string so the rest of the file still works

# else:
#     path_strt1 = '../../district_energy_model'

#     fetch = '../Sources/Fetch_folder'
#     sources = '../Sources'
#     masters = '../Masters'
#     maps = '../Maps'
#     geojsons = '../GeoJsons'
# # -----------

class DEMPaths:
    
    def __init__(self, root_dir):

        path_strt1 = root_dir
        self.root_dir = root_dir
    
        # simulation_data_dir = '../../data/master_data/simulation_data/'
        self.simulation_data_dir = path_strt1 + '/data/master_data/simulation_data/'
        
        self.master_file = 'df_master_sim.feather'
        self.meta_file = 'meta_file_2.feather'
        
        
        self.profiles_file = 'simulation_profiles_file.feather'
        # -----------------------------------------------------------------------------
        # run_dem.py:
        # -----------
            
        # Directory paths:
        # master_data_dir = '../../data/master_data/'
        # com_data_dir = '../../data/community_data/'
        self.master_data_dir = path_strt1 + '/data/master_data/'
        self.com_data_dir = path_strt1 + '/data/community_data/'
        
        # -----------------------------------------------------------------------------
        # dem.py:
        # -------
        
        # input_files_dir = '../../config/input_files'
        # self.input_files_dir = path_strt1 + '/config/input_files'
        self.input_files_dir = path_strt1 + '/config/config_files'
        
        # Input data directories:
        self.weather_data_dir = path_strt1 + '/data/heat_demand/weather_data/' # location of meteostat files
        self.weather_data_delta_method_dir = path_strt1 + '/data/weather_data/com_files/'
        self.dhw_profile_dir = path_strt1 + '/data/heat_demand/'
        self.pv_data_dir = path_strt1 + '/data/pv_data/pv_input_file/' # location of pv data
        self.energy_mix_CH_dir = path_strt1 + '/data/electricity_mix_national/' # location of energy mix files
        self.electricity_profile_dir = path_strt1 + '/data/electricity_demand/' # location of electr. load profile files
        self.biomass_data_dir = path_strt1 + '/data/biomass_data/'
        self.wind_power_data_dir = path_strt1 + '/data/tech_wind_power/' # location of wind power data (e.g. installed capacities per municipality)
        self.wind_power_profiles_dir = path_strt1 + '/data/tech_wind_power/profiles/' # location of wind power hourly profile files
        self.ev_profiles_dir = path_strt1 + '/data/electricity_demand/ev_profiles/' # location of electric vehicle (ev) charging profiles
        
        # Input data files:
        self.electricity_import_file = 'import_percentage_profile.feather' # csv-file containing timeseries of hourly cross-border electricity import fraction.
        self.electricity_mix_file = 'electricity_mix.feather' # feather-file containing timeseries of hourly electricity mix fractions.
        self.electricity_mix_totals_file = 'CH_production_totals.feather' # csv-file containing timeseries of hourly electricity mix fractions.
        self.strom_profiles_2050_file = 'Strom_Profiles_2050.feather'
        self.electricity_demand_file_household = path_strt1 + '/data/electricity_demand/electricity_demand_household.csv' # csv-file containing a list of all communities and their respective annual electricity demand (kWh).
        self.electricity_demand_file_industry = path_strt1 + '/data/electricity_demand/electricity_demand_industry.csv'
        self.pv_data_meta_file = 'pv_data_meta.csv' # csv file containing meta data about pv profile files
        
        self.pv_roof_dir = path_strt1 + '/data/pv_data/roof_data_per_com'
        self.pv_epps_unassigned_path = path_strt1 + '/data/pv_data/solar_epps_not_assigned_to_roofs_powers.feather'
        
        self.electricity_profile_file = 'load_profiles.csv' # csv-file containing load profile from smart meter data
        self.electricity_profile_industry_file = 'cantonal_industryprofiles.feather' # csv-file containing load profile from smart meter data
        self.wind_power_cap_file = 'p_installed_kW_wind_power.feather' # installed wind power capacity [kW] per municipality
        self.wind_power_national_profile_file = 'v_e_wp_national_installed_kWh.csv' # Hourly profile of national wind power generation [kWh]
        self.dhw_profile_file = 'DHW_Profile.feather'
        self.hydro_profile_file = path_strt1 + '/data/electricity_production_plant/HydroProfiles/Hydro_Profiles.feather'
        self.ev_profile_cp_file = 'profile_CP_y4.feather' # hourly charging load [kW]
        self.ev_profile_fe_file = 'profile_FE_y4.feather' # daily flexible energy [kWh]
        self.ev_profile_pd_file = 'profile_PD_y4.feather' # hourly upper power bound [kW]
        self.ev_profile_pu_file = 'profile_PU_y4.feather' # hourly lower power bound [kW]
        self.ev_munic_name_nr_file = 'ev_munic_name_nr.feather' # municipalities and BFS numnbers for ev data
        
        # Output directory:
        self.output_dir_name = 'dem_output'
