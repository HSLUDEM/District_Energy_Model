# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 14:39:11 2024

@author: UeliSchilt
"""

# -----------------------------------------------------------------------------
# recommender tool:
if True:
    path_strt1 = '..'
else:
    path_strt1 = '../../district_energy_model'

    fetch = '../Sources/Fetch_folder'
    sources = '../Sources'
    masters = '../Masters'
    maps = '../Maps'
    geojsons = '../GeoJsons'
# -----------

simulation_data_dir = '../data/master_data/simulation_data/'

master_file = 'df_master_sim.feather'
# meta_file = 'df_meta_2.feather'
meta_file = 'meta_file_2.feather'


profiles_file = 'simulation_profiles_file.feather'
# -----------------------------------------------------------------------------
# run_dem.py:
# -----------
    
# Directory paths:
# master_data_dir = 'C:/Users/Somesh/OneDrive - Hochschule Luzern/Dokumente/Assessment/Biomasse/50_Code/district_energy_model/data/master_data/'
# master_data_dir = 'C:/Users/UeliSchilt/Hochschule Luzern/CC TES - 1122442_EDGE/Modelling/Masters/'
master_data_dir = '../data/master_data/'
com_data_dir = '../data/community_data/'

# results_path = 'C:/Users/UeliSchilt/Hochschule Luzern/CC TES - EDGE/Modelling/Results/District_Energy_Model/Multi_obj_opt/Allschwil/v20240312_with_tes_5_weights'
results_path = 'tmp_results_for_testing'
# results_path = 'tmp_results_for_testing/TEST_BALANCE/ISSUE_20240408_electricity_balance'
# results_path = 'C:/Users/UeliSchilt/Hochschule Luzern/CC TES - EDGE/Modelling/Results/District_Energy_Model/Multi_obj_opt/Sirnach'
# results_path = 'C:/Users/UeliSchilt/Hochschule Luzern/CC TES - EDGE/Modelling/Results/District_Energy_Model/Multi_obj_opt/0_tmp_new_results'

# Filenames:
# master_file = 'Schweiz.csv'
# master_file = '/simulation_data/df_master_sim.feather'
# meta_file = 'meta.csv' # 'meta_0623.csv'
# meta_file = '/simulation_data/meta_file_2.feather'

# -----------------------------------------------------------------------------
# dem.py:
# -------

# Input data directories:
weather_data_dir = path_strt1 + '/data/heat_demand/weather_data/' # location of meteostat files

weather_data_delta_method_dir = path_strt1 + '/data/weather_data/com_files/'

dhw_profile_dir = path_strt1 + '/data/heat_demand/'
pv_data_dir = path_strt1 + '/data/pv_data/pv_input_file/' # location of pv data
energy_mix_CH_dir = path_strt1 + '/data/electricity_mix_national/' # location of energy mix files
electricity_profile_dir = path_strt1 + '/data/electricity_demand/' # location of electr. load profile files
biomass_data_dir = path_strt1 + '/data/biomass_data/'
wind_power_data_dir = path_strt1 + '/data/tech_wind_power/' # location of wind power data (e.g. installed capacities per municipality)
wind_power_profiles_dir = path_strt1 + '/data/tech_wind_power/profiles/' # location of wind power hourly profile files
# electr_prod_plant_dir = path_strt1 + '/data/electricity_production_plant/'
ev_profiles_dir = path_strt1 + '/data/electricity_demand/ev_profiles/' # location of electric vehicle (ev) charging profiles

# Input data files:
electricity_import_file = 'import_percentage_profile.feather' # csv-file containing timeseries of hourly cross-border electricity import fraction.
electricity_mix_file = 'electricity_mix.feather' # feather-file containing timeseries of hourly electricity mix fractions.
electricity_mix_totals_file = 'CH_production_totals.feather' # csv-file containing timeseries of hourly electricity mix fractions.
strom_profiles_2050_file = 'Strom_Profiles_2050.feather'
electricity_demand_file_household = path_strt1 + '/data/electricity_demand/electricity_demand_household.csv' # csv-file containing a list of all communities and their respective annual electricity demand (kWh).
electricity_demand_file_industry = path_strt1 + '/data/electricity_demand/electricity_demand_industry.csv'
pv_data_meta_file = 'pv_data_meta.csv' # csv file containing meta data about pv profile files
electricity_profile_file = 'load_profiles.csv' # csv-file containing load profile from smart meter data
electricity_profile_industry_file = 'cantonal_industryprofiles.feather' # csv-file containing load profile from smart meter data
# electricity_profile_file = 'Buildings_A_B_power_load_profile.csv' # csv-file containing load profile from smart meter data
# electr_prod_plant_file = 'ElectricityProductionPlant.csv' # electricity production plants in Switzerland (from UVEK)
# wind_power_cap_file = 'p_installed_kW_wind_power.csv' # installed wind power capacity [kW] per municipality
wind_power_cap_file = 'p_installed_kW_wind_power.feather' # installed wind power capacity [kW] per municipality
wind_power_national_profile_file = 'v_e_wp_national_installed_kWh.csv' # Hourly profile of national wind power generation [kWh]
dhw_profile_file = 'DHW_Profile.feather'
hydro_profile_file = path_strt1 + '/data/electricity_production_plant/HydroProfiles/Hydro_Profiles.feather'
# electr_prod_plant_file = 'ElectricityProductionPlant_wind.csv' # electricity production plants in Switzerland (from UVEK); TMP: only for wind, with correct munic names
ev_profile_cp_file = 'profile_CP_y4.feather' # hourly charging load [kW]
ev_profile_fe_file = 'profile_FE_y4.feather' # daily flexible energy [kWh]
ev_profile_pd_file = 'profile_PD_y4.feather' # hourly upper power bound [kW]
ev_profile_pu_file = 'profile_PU_y4.feather' # hourly lower power bound [kW]
ev_munic_name_nr_file = 'ev_munic_name_nr.feather' # municipalities and BFS numnbers for ev data


# Other files:
# municipality_names_file = r'C:\Users\UeliSchilt\Hochschule Luzern\CC TES - EDGE\Resources\municipality_names.xlsx'

