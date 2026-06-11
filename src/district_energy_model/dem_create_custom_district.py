# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 16:32:35 2025

@author: Somesh
"""

import pandas as pd
import numpy as np

from district_energy_model import dem_helper

def create_district(paths, scen_techs):
    

    meta_file_general_path = paths.simulation_data_dir + paths.meta_file_general
    df_meta_general = pd.read_feather(meta_file_general_path)
    
    meta_file_year_path = paths.simulation_data_dir + paths.meta_file_year
    df_meta_year = pd.read_feather(meta_file_year_path)
    
    # Merge general with year-specific meta data:
    df_meta = df_meta_general.merge(
        df_meta_year,
        on="GGDENR",
        how="left"
    )

    master_file_general_path = paths.simulation_data_dir + paths.master_file_general
    df_master_general = pd.read_feather(master_file_general_path)
    
    master_file_year_path = paths.simulation_data_dir + paths.master_file_year
    df_master_year = pd.read_feather(master_file_year_path)
    
    # Merge to one master file:
    df_master = df_master_general.merge(
        df_master_year,
        on="EGID",
        how="left"
    )


    EGID_List = scen_techs['meta_data']['custom_district']['EGID_List']
    
    if scen_techs['meta_data']['custom_district']['custom_district_name'] in df_meta['Municipality']:
        arg = df_meta['Municipality'] == scen_techs['meta_data']['custom_district']['custom_district_name']
        arg_master = df_master['EGID'].isin(EGID_List)
        
        com_nr = df_meta.loc[arg, 'GGDENR']
        com_name = df_meta.loc[arg, 'Municipality']
        com_kt = df_meta.loc[arg, 'Canton']
        df_com_yr = df_master.loc[arg_master]
        
        return com_nr, com_nr, com_name, com_kt, df_meta, df_com_yr
    
    else:
        arg_master = df_master['EGID'].isin(EGID_List)
        df_com_yr = df_master.loc[arg_master]
        

        #Add functionality to read in manual district
        #manual district file needs to have the same format as the Master file
        if scen_techs['meta_data']['custom_district']['manual_district']:
            manual_district_df_com_path = scen_techs['meta_data']['custom_district']['manual_district_df_com_path']
            manual_district_df_solar_rooftop_profiles_path = scen_techs['meta_data']['custom_district']['manual_district_df_solar_rooftop_profiles_path']
            manual_district_df_solar_rooftop_building_data_path = scen_techs['meta_data']['custom_district']['manual_district_df_solar_rooftop_building_data_path']
            
            df_com_yr_manual = pd.read_feather(manual_district_df_com_path)

            df_com_yr = (
                pd.concat([df_com_yr, df_com_yr_manual])
                .drop_duplicates(subset="EGID", keep="last")
                .reset_index(drop=True)
            )

        scen_techs['meta_data']['custom_district']['EGID_List'] = list(df_com_yr['EGID'].unique())

        Municipality = scen_techs['meta_data']['custom_district']['custom_district_name']
        
        GGDENR_max = df_meta['GGDENR'].max()
        if GGDENR_max > 10000:
            GGDENR_new = GGDENR_max + 1
        else:
            GGDENR_new = 10001
        
        Canton = df_com_yr.groupby('GDEKT').size().sort_values(ascending = False).index[0]
        
        Coord_lat_median = df_com_yr['Coord_lat'].median()
        Coord_long_median = df_com_yr['Coord_long'].median()
        altitude_median = df_com_yr['altitude'].median()
        
        Filename = None
        
        LocalHydroPotential_Laufkraftwerk = df_com_yr['LocalHydroPotential_Laufkraftwerk'].sum()
        LocalHydroPotential_Speicherkraftwerk = df_com_yr['LocalHydroPotential_Speicherkraftwerk'].sum()
        LocalHydroPotential_Pumpspeicherkraftwerk = df_com_yr['LocalHydroPotential_Pumpspeicherkraftwerk'].sum()
        LocalHydroPotential = LocalHydroPotential_Laufkraftwerk + LocalHydroPotential_Speicherkraftwerk + LocalHydroPotential_Pumpspeicherkraftwerk
        
        v_h_eh = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_eh', 'space_heating_demand_estimation_kWh'].sum()
        v_h_hp = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_hp', 'space_heating_demand_estimation_kWh'].sum()
        v_h_dh = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_dh', 'space_heating_demand_estimation_kWh'].sum()
        v_h_gb = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_gb', 'space_heating_demand_estimation_kWh'].sum()
        v_h_ob = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_ob', 'space_heating_demand_estimation_kWh'].sum()
        v_h_wb = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_wb', 'space_heating_demand_estimation_kWh'].sum()
        v_h_solar = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_solar', 'space_heating_demand_estimation_kWh'].sum()
        v_h_other = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_other', 'space_heating_demand_estimation_kWh'].sum()
        
        space_heating_demand_estimation_kWh = v_h_eh + v_h_hp + v_h_dh + v_h_gb + v_h_ob + v_h_wb + v_h_solar + v_h_other
        
        v_hw_eh = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_eh', 'DHW_demand_estimation_kWh'].sum()
        v_hw_hp = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_hp', 'DHW_demand_estimation_kWh'].sum()
        v_hw_dh = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_dh', 'DHW_demand_estimation_kWh'].sum()
        v_hw_gb = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_gb', 'DHW_demand_estimation_kWh'].sum()
        v_hw_ob = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_ob', 'DHW_demand_estimation_kWh'].sum()
        v_hw_wb = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_wb', 'DHW_demand_estimation_kWh'].sum()
        v_hw_solar = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_solar', 'DHW_demand_estimation_kWh'].sum()
        v_hw_other = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_other', 'DHW_demand_estimation_kWh'].sum()
        
        DHW_demand_estimation_kWh = v_hw_eh + v_hw_hp + v_hw_dh + v_hw_gb + v_hw_ob + v_hw_wb + v_hw_solar + v_hw_other
        
        PV_Pot = df_com_yr['PV_Pot'].sum()
        PV_TotalEnergy = df_com_yr['PV_TotalEnergy'].sum()
        Electricity_demand_household_SFH_kWh = df_com_yr['Electricity_demand_household_SFH_kWh'].sum()
        Electricity_demand_household_MFH_kWh = df_com_yr['Electricity_demand_household_MFH_kWh'].sum()
        s_wd_bm = df_com_yr['s_wd_bm'].sum()
        s_wet_bm = df_com_yr['s_wet_bm'].sum()
        Electricity_demand_industry_kWh = df_com_yr['Electricity_demand_industry_kWh'].sum()
        Electricity_demand_services_kWh = df_com_yr['Electricity_demand_services_kWh'].sum()
        
        # Solar PV data:
        com_nr_majority = df_com_yr.groupby('GGDENR').size().sort_values(ascending = False).index[0]
            
        pv_filename = df_meta.loc[df_meta['GGDENR'] == com_nr_majority, 'PV_Filename'].values[0]
        
        # ================
        # SUPERSEDED:
        # ----------
        # pv_meta_file_path = paths.pv_data_dir + paths.pv_data_meta_file
        # df_pv_meta = pd.read_csv(pv_meta_file_path)
        # tmp_df_pv_meta = df_pv_meta.copy()
        
        # # add column with distances to each pv-simulation location in temp. df
        # tmp_df_pv_meta['dist_km'] = \
        #     tmp_df_pv_meta.apply(lambda row: dem_helper.distance_between_coord(Coord_lat_median, Coord_long_median, row['coord_lat_median'], row['coord_long_median']), axis=1)
        
        # min_dist = tmp_df_pv_meta['dist_km'].min()
        
        # pv_file = tmp_df_pv_meta.loc[tmp_df_pv_meta['dist_km'] == min_dist].index[0]
        # pv_filename = str(pv_file)
        
        # del tmp_df_pv_meta
        # ================
        
        
        
        #Add dh Data
        avg_dist_class_1 = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 1, 'avg_dh_connection_distance'].mean()
        avg_dist_class_2 = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 2, 'avg_dh_connection_distance'].mean()
        avg_dist_class_3 = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 3, 'avg_dh_connection_distance'].mean()
        
        cap_class_1 = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 1, 'space_heating_demand_estimation_kWh'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 1, 'DHW_demand_estimation_kWh'].sum()
        cap_class_2 = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 2, 'space_heating_demand_estimation_kWh'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 2, 'DHW_demand_estimation_kWh'].sum()
        cap_class_3 = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 3, 'space_heating_demand_estimation_kWh'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 3, 'DHW_demand_estimation_kWh'].sum()
            
        cap_class_1_renov = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 1, 'heat_energy_demand_renov_estimate_kWh'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 1, 'DHW_demand_estimation_kWh'].sum()
        cap_class_2_renov = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 2, 'heat_energy_demand_renov_estimate_kWh'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 2, 'DHW_demand_estimation_kWh'].sum()
        cap_class_3_renov = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 3, 'heat_energy_demand_renov_estimate_kWh'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 3, 'DHW_demand_estimation_kWh'].sum()
        
        m_per_kWh_class_1_renov = (df_com_yr['dh_distance_cat'] == 1).sum()*avg_dist_class_1/cap_class_1_renov
        m_per_kWh_class_2_renov = (df_com_yr['dh_distance_cat'] == 2).sum()*avg_dist_class_2/cap_class_2_renov
        m_per_kWh_class_3_renov = (df_com_yr['dh_distance_cat'] == 3).sum()*avg_dist_class_3/cap_class_3_renov
        
        m_per_kWh_class_1 = (df_com_yr['dh_distance_cat'] == 1).sum()*avg_dist_class_1/cap_class_1
        m_per_kWh_class_2 = (df_com_yr['dh_distance_cat'] == 2).sum()*avg_dist_class_2/cap_class_2
        m_per_kWh_class_3 = (df_com_yr['dh_distance_cat'] == 3).sum()*avg_dist_class_3/cap_class_3
        
        new_district = np.array([
            GGDENR_new, Municipality, Canton, 
            Coord_lat_median, Coord_long_median,  
            altitude_median, 
            Filename,
            LocalHydroPotential, 
            LocalHydroPotential_Laufkraftwerk,  
            LocalHydroPotential_Speicherkraftwerk, 
            LocalHydroPotential_Pumpspeicherkraftwerk, 
            v_h_eh, v_h_hp, v_h_dh, v_h_gb, v_h_ob, v_h_wb, v_h_solar, v_h_other, 
            space_heating_demand_estimation_kWh,
            v_hw_eh, v_hw_hp, v_hw_dh, v_hw_gb, v_hw_ob, v_hw_wb, v_hw_solar, v_hw_other, 
            DHW_demand_estimation_kWh, 
            PV_Pot, PV_TotalEnergy, 
            s_wd_bm, s_wet_bm, 
            cap_class_1, cap_class_2, cap_class_3,
            cap_class_1_renov, cap_class_2_renov, cap_class_3_renov,
            avg_dist_class_1, avg_dist_class_2, avg_dist_class_3,
            m_per_kWh_class_1_renov, m_per_kWh_class_2_renov, m_per_kWh_class_3_renov,
            m_per_kWh_class_1, m_per_kWh_class_2, m_per_kWh_class_3,
            Electricity_demand_household_SFH_kWh, Electricity_demand_household_MFH_kWh, 
            Electricity_demand_industry_kWh, Electricity_demand_services_kWh,
            0.0, 0.0
            ])
        
        df_meta.loc[len(df_meta)] = new_district
        
        com_name = df_com_yr.groupby('GGDENAME').size().sort_values(ascending = False).index[0]
        if com_name == r"C'za Cadenazzo/Monteceneri": # Special case
            com_name = "Comunanza Cadenazzo_Monteceneri"
            
        if '/' in com_name:
            com_name = com_name.replace('/', '_')
        
        com_nr_majority = df_com_yr.groupby('GGDENR').size().sort_values(ascending = False).index[0]

        com_percentages = pd.DataFrame(index = range(len(df_com_yr['GGDENAME'].unique())))
        com_percentages['GGDENAME'] = df_com_yr['GGDENAME'].unique()
        
        
        per = df_com_yr.groupby('GGDENAME').size()/df_master.loc[df_master['GGDENAME'].isin(df_com_yr['GGDENAME'].unique())].groupby('GGDENAME').size()
        per_2 = df_com_yr.groupby('GGDENR').size()/df_master.loc[df_master['GGDENR'].isin(df_com_yr['GGDENR'].unique())].groupby('GGDENR').size()
        for i in range(len(per)):
            if per.index[i] == r"C'za Cadenazzo/Monteceneri": # Special case
                arr = np.array(per.index)
                arr[i] = "Comunanza Cadenazzo_Monteceneri"
                per.index = arr
                
            if '/' in per.index[i]:
                arr = np.array(per.index)
                arr[i] = arr[i].replace('/', '_')
                per.index = arr
                
        return GGDENR_new, com_nr_majority, com_name, Canton, df_meta, df_com_yr, per, per_2