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
    
    def __init__(self, 
                 root_dir, 
                 config_dir = '', 
                 output_dir = '',
                 hist_data_year = 2016,
                 current_year = 2026,
                 ):

        h_y = hist_data_year
        c_y = current_year

        path_strt1 = root_dir
        self.root_dir = root_dir
    
        self.simulation_data_dir = path_strt1 + '/data/master_data/'
        
        self.master_file_general = 'master_data_general.feather'
        self.meta_file_general = 'meta_data_general.feather'
        
        self.master_file_year = f"master_data_{h_y}.feather"
        self.meta_file_year = f"meta_data_{h_y}.feather"
        
        self.profiles_file_general = "simulation_profiles_general.feather"
        self.profiles_file_year = f"simulation_profiles_{h_y}.feather"
        
        # -----------------------------------------------------------------------------
        # run_dem.py:
        # -----------        
        self.master_data_dir = path_strt1 + '/data/master_data/'
        self.com_data_dir = path_strt1 + f"/data/community_data/{h_y}_mapped_to_{c_y}/"
        
        # -----------------------------------------------------------------------------
        # dem.py:
        # -------        
        if config_dir == '':
            self.input_files_dir = path_strt1 + '/config/config_files'
        else:
            self.input_files_dir = config_dir
        
        # Input data directories:
        # ----------------------
        self.weather_data_delta_method_dir = path_strt1 + '/data/weather_data/community_files/'
        self.heat_dir = path_strt1 + '/data/heat/'
        self.electricity_dir = path_strt1 + '/data/electricity/'
        self.pv_roof_dir = path_strt1 + '/data/tech_solar_pv/roof_data_per_com'
        self.wind_power_data_dir = path_strt1 + '/data/tech_wind_power/' # location of wind power data (e.g. installed capacities per municipality)
        self.wind_power_profiles_dir = path_strt1 + '/data/tech_wind_power/profiles/' # location of wind power hourly profile files
        self.ev_profiles_dir = path_strt1 + '/data/electricity/ev_profiles/' # location of electric vehicle (ev) charging profiles
        
        # Input data files:
        # ----------------
        self.electricity_mix_file = 'electricity_mix.feather' # timeseries of hourly electricity mix fractions.
        self.pv_alpine_file = path_strt1 + '/data/tech_solar_pv/alpine_pv_profiles.feather'
        self.pv_epps_unassigned_path = path_strt1 + '/data/tech_solar_pv/solar_epps_not_assigned_to_roofs_powers.feather'
        self.wind_power_cap_file = 'p_installed_kW_wind_power.feather' # installed wind power capacity [kW] per municipality
        self.wind_power_national_profile_file = 'v_e_wp_national_installed_kWh.csv' # Hourly profile of national wind power generation [kWh]
        self.dhw_profile_file = 'DHW_Profile.feather'
        self.ev_profile_cp_file = 'profile_CP_y4.feather' # hourly charging load [kW]
        self.ev_profile_fe_file = 'profile_FE_y4.feather' # daily flexible energy [kWh]
        self.ev_profile_pd_file = 'profile_PD_y4.feather' # hourly upper power bound [kW]
        self.ev_profile_pu_file = 'profile_PU_y4.feather' # hourly lower power bound [kW]
        self.ev_munic_name_nr_file = 'ev_munic_name_nr.feather' # municipalities and BFS numnbers for ev data
        
        # Output directory:
        if output_dir == '':
            self.output_dir_name = 'dem_output'
        else:
            self.output_dir_name = output_dir
