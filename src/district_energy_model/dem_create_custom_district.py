# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 16:32:35 2025

@author: Somesh
"""

import pandas as pd
import numpy as np

from district_energy_model import dem_helper

def create_district(paths, scen_techs):
    
    df_meta = pd.read_feather(paths.simulation_data_dir + paths.meta_file)
    # print(df_meta.columns)
    df_master = pd.read_feather(paths.simulation_data_dir + paths.master_file)
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
        
        v_h_eh = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_eh', 'heat_energy_demand_estimate_kWh_combined'].sum()
        v_h_hp = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_hp', 'heat_energy_demand_estimate_kWh_combined'].sum()
        v_h_dh = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_dh', 'heat_energy_demand_estimate_kWh_combined'].sum()
        v_h_gb = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_gb', 'heat_energy_demand_estimate_kWh_combined'].sum()
        v_h_ob = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_ob', 'heat_energy_demand_estimate_kWh_combined'].sum()
        v_h_wb = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_wb', 'heat_energy_demand_estimate_kWh_combined'].sum()
        v_h_solar = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_solar', 'heat_energy_demand_estimate_kWh_combined'].sum()
        v_h_other = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_other', 'heat_energy_demand_estimate_kWh_combined'].sum()
        
        Total_Heating = v_h_eh + v_h_hp + v_h_dh + v_h_gb + v_h_ob + v_h_wb + v_h_solar + v_h_other
        
        v_hw_eh = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_eh', 'dhw_estimation_kWh_combined'].sum()
        v_hw_hp = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_hp', 'dhw_estimation_kWh_combined'].sum()
        v_hw_dh = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_dh', 'dhw_estimation_kWh_combined'].sum()
        v_hw_gb = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_gb', 'dhw_estimation_kWh_combined'].sum()
        v_hw_ob = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_ob', 'dhw_estimation_kWh_combined'].sum()
        v_hw_wb = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_wb', 'dhw_estimation_kWh_combined'].sum()
        v_hw_solar = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_solar', 'dhw_estimation_kWh_combined'].sum()
        v_hw_other = df_com_yr.loc[df_com_yr['Hot_Water_System'] == 'v_hw_other', 'dhw_estimation_kWh_combined'].sum()
        
        Total_Hot_Water = v_hw_eh + v_hw_hp + v_hw_dh + v_hw_gb + v_hw_ob + v_hw_wb + v_hw_solar + v_hw_other
        
        PV_Pot = df_com_yr['PV_Pot'].sum()
        TotalEnergy = df_com_yr['TotalEnergy'].sum()
        kWh_household_sfh = df_com_yr['kWh_household_sfh'].sum()
        kWh_household_mfh = df_com_yr['kWh_household_mfh'].sum()
        s_wd_bm = df_com_yr['s_wd_bm'].sum()
        s_wet_bm = df_com_yr['s_wet_bm'].sum()
        Electricity_Industry = df_com_yr['Electricity_Industry'].sum()
        Electricity_Service = df_com_yr['Electricity_Service'].sum()
        
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
        
        cap_class_1 = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 1, 'heat_energy_demand_estimate_kWh_combined'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 1, 'dhw_estimation_kWh_combined'].sum()
        cap_class_2 = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 2, 'heat_energy_demand_estimate_kWh_combined'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 2, 'dhw_estimation_kWh_combined'].sum()
        cap_class_3 = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 3, 'heat_energy_demand_estimate_kWh_combined'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 3, 'dhw_estimation_kWh_combined'].sum()
            
        cap_class_1_renov = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 1, 'heat_energy_demand_renov_estimate_kWh'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 1, 'dhw_estimation_kWh_combined'].sum()
        cap_class_2_renov = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 2, 'heat_energy_demand_renov_estimate_kWh'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 2, 'dhw_estimation_kWh_combined'].sum()
        cap_class_3_renov = df_com_yr.loc[df_com_yr['dh_distance_cat'] == 3, 'heat_energy_demand_renov_estimate_kWh'].sum() +\
            df_com_yr.loc[df_com_yr['dh_distance_cat'] == 3, 'dhw_estimation_kWh_combined'].sum()
        
        m_per_kWh_class_1_renov = (df_com_yr['dh_distance_cat'] == 1).sum()*avg_dist_class_1/cap_class_1_renov
        m_per_kWh_class_2_renov = (df_com_yr['dh_distance_cat'] == 2).sum()*avg_dist_class_2/cap_class_2_renov
        m_per_kWh_class_3_renov = (df_com_yr['dh_distance_cat'] == 3).sum()*avg_dist_class_3/cap_class_3_renov
        
        m_per_kWh_class_1 = (df_com_yr['dh_distance_cat'] == 1).sum()*avg_dist_class_1/cap_class_1
        m_per_kWh_class_2 = (df_com_yr['dh_distance_cat'] == 2).sum()*avg_dist_class_2/cap_class_2
        m_per_kWh_class_3 = (df_com_yr['dh_distance_cat'] == 3).sum()*avg_dist_class_3/cap_class_3
        
        new_district = np.array([
            Municipality, GGDENR_new, Canton, 
            Coord_lat_median, Coord_long_median,  altitude_median, 
            Filename,
            LocalHydroPotential, LocalHydroPotential_Laufkraftwerk,  LocalHydroPotential_Speicherkraftwerk, LocalHydroPotential_Pumpspeicherkraftwerk, 
            v_h_eh, v_h_hp, v_h_dh, v_h_gb, v_h_ob, v_h_wb, v_h_solar, v_h_other, Total_Heating,
            v_hw_eh, v_hw_hp, v_hw_dh, v_hw_gb, v_hw_ob, v_hw_wb, v_hw_solar, v_hw_other, Total_Hot_Water, 
            PV_Pot, TotalEnergy, 
            kWh_household_sfh, kWh_household_mfh, 
            Electricity_Industry, Electricity_Service,
            s_wd_bm, s_wet_bm, 
            pv_filename,
            cap_class_1, cap_class_2, cap_class_3,
            cap_class_1_renov, cap_class_2_renov, cap_class_3_renov,
            avg_dist_class_1, avg_dist_class_2, avg_dist_class_3,
            m_per_kWh_class_1_renov, m_per_kWh_class_2_renov, m_per_kWh_class_3_renov,
            m_per_kWh_class_1, m_per_kWh_class_2, m_per_kWh_class_3
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