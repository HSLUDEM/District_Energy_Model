# -*- coding: utf-8 -*-
"""
Created on Mon Aug 21 10:10:10 2023

@author: UeliSchilt
"""

"""
Models for demand profiles.

Implemented:
    - heat
    - electricity
    
To do:
    - E-Mobility --> Daten ETH

"""

import sys
import os
import numpy as np
import pandas as pd
import meteostat
from datetime import datetime

from district_energy_model import dem_constants as C
from district_energy_model import dem_helper

"""----------------------------------------------------------------------------
ELECTRICITY DEMAND:
"""

# def get_d_e_yr(electricity_demand_file,
#                com_name):

#     """Returns the annual electricity demand (d_e_yr) of the selected community.
    
#     Parameters
#     ----------
#     electricity_demand_file : string
#         Path to csv-file containing a list of all communities and their
#         respective annual electricity demand (kWh).
#         Example: 'electricity_demand/d_e_yr.csv'
#     com_name : string
#         Name of community. Example: 'Allschwil'
    
#     Returns
#     -------
#     float
#         annual electricity demand [kWh]
#     """
#     f = electricity_demand_file
#     c = com_name
    
#     # Read csv-file containing annual electricity demand of each community:
#     df_data = pd.read_csv(f,encoding="UTF8")
#     #df_data.to_csv('test_d_e.csv')
    
#     # check if community is contained in the file:            
#     # if df_data['Municipality'].str.contains(c).any(): # This function can't handle string with whitespaces
#     if df_data['Municipality'].apply(lambda x: c in x).any():
#         d_e_yr = df_data.loc[df_data['Municipality']==c,'d_e_yr']
#         d_e_yr = float(d_e_yr)
#     else:
#         sys.exit(f"Error in get_d_e_yr(): {c} is not found in electricity demand file {f}.")
    
#     return d_e_yr

class EnergyDemand:
    
    def __init__(self, paths, com_nr):
        
        self.paths = paths
                
        # Properties:
        self.com_nr = com_nr
        
        # Carrier types:
        ...
        
        # Hourly values:
        self._d_e = []
        self._d_e_ev = []
        
        self._d_e_ev_cp = [] # [kWh] hourly EV charging load (base profile)
        self._d_e_ev_pd = [] # [kWh] hourly EV lower charging bound
        self._d_e_ev_pu = [] # [kWh] hourly EV upper charging bound
        self._d_e_ev_cp_dev = [] # [kWh] Hourly deviation from base profile due to flexibility
        self._d_e_ev_cp_dev_pos = [] # [kWh] Hourly positive deviation from base profile due to flexibility
        self._d_e_ev_cp_dev_neg = [] # [kWh] Hourly negative deviation from base profile due to flexibility
        
        self._d_e_hh = []
        self._d_e_h = []
        self._d_h = [] # [kWh] Total heat demand
        self._d_h_s = [] # [kWh] Heat demand for space heating
        self._d_h_hw = [] # [kWh] Heat demand for hot water
        self._d_e_unmet = []
        self._d_h_unmet = []
        self._d_h_unmet_dhn = [] # [kWh] Unmet heat demand in district heating network
        
        # Daily values:
        self._f_e_ev_pot_dy = [] # [kWh] Daily available flexible energy for EV charging (i.e. flexibility potential)
        self._f_e_ev_dy = [] # [kWh] Daily utilised flexible energy for EV charging
        self._d_e_ev_cp_dy = [] # [kWh] daily EV charging load (base profile)
        
        # Annual values:
        self._d_e_yr = ...
        self._d_e_ev_yr = ...
        self._d_e_hh_yr = ...
        self._d_e_h_yr = ...
        self._d_h_yr = ...
        self._d_h_s_yr = ...
        self._d_h_hw_yr = ...
        
        self._d_e_sfh_yr = ... # formerly: d_e_yr_sfh
        self._d_e_mfh_yr = ... # formerly: d_e_yr_mfh
        self._d_e_ind_yr = ... # formerly: d_e_yr_ind
        self._d_e_ser_yr = ... # formerly: d_e_yr_ser
        
        # Other:
        self._d_h_profile = [] # [-] Hourly normed (normed to 1) heat demand profile
        
    def update_df_results(self, df):
        
        df['d_e'] = self.get_d_e()
        df['d_e_ev'] = self.get_d_e_ev()
        df['d_e_ev_cp'] = self.get_d_e_ev_cp()
        df['d_e_ev_pd'] = self.get_d_e_ev_pd()
        df['d_e_ev_pu'] = self.get_d_e_ev_pu()
        df['d_e_ev_cp_dev'] = self.get_d_e_ev_cp_dev()
        df['d_e_ev_cp_dev_pos'] = self.get_d_e_ev_cp_dev_pos()
        df['d_e_ev_cp_dev_neg'] = self.get_d_e_ev_cp_dev_neg()        
        df['d_e_hh'] = self.get_d_e_hh()
        df['d_e_h'] = self.get_d_e_h()
        df['d_h'] = self.get_d_h()
        df['d_h_s'] = self.get_d_h_s()
        df['d_h_hw'] = self.get_d_h_hw()
        df['d_e_unmet'] = self.get_d_e_unmet()
        df['d_h_unmet'] = self.get_d_h_unmet()
        df['d_h_unmet_dhn'] = self.get_d_h_unmet_dhn()
        
        return df
    
    def reduce_timeframe(self, n_days):
        """
        Reduce the hourly timeseries to the first n days.

        Parameters
        ----------
        n_days : int
            Number of days (starting at the first day of the year).

        Returns
        -------
        None.

        """
        
        n_hours = n_days*24
        
        self._d_e = self._d_e[:n_hours]
        self._d_e_ev = self._d_e_ev[:n_hours]
        self._d_e_ev_cp = self._d_e_ev_cp[:n_hours]
        self._d_e_ev_pd = self._d_e_ev_pd[:n_hours]
        self._d_e_ev_pu = self._d_e_ev_pu[:n_hours]
        self._d_e_ev_cp_dev = self._d_e_ev_cp_dev[:n_hours]
        self._d_e_ev_cp_dev_pos = self._d_e_ev_cp_dev_pos[:n_hours]
        self._d_e_ev_cp_dev_neg = self._d_e_ev_cp_dev_neg[:n_hours]
        self._d_e_hh = self._d_e_hh[:n_hours]
        self._d_e_h = self._d_e_h[:n_hours]
        self._d_h = self._d_h[:n_hours]
        self._d_h_s = self._d_h_s[:n_hours]
        self._d_h_hw = self._d_h_hw[:n_hours]
        self._d_e_unmet = self._d_e_unmet[:n_hours]
        self._d_h_unmet = self._d_h_unmet[:n_hours]
        self._d_h_unmet_dhn = self._d_h_unmet_dhn[:n_hours]
        

    # def get_d_e_hh_yr(
    def compute_d_e_hh_yr(
            self,
            df_meta,
            com_nr):
    
        """Returns the annual electricity demand (d_e_yr) of the selected community.
        
        Parameters
        ----------
        electricity_demand_file : string
            Path to csv-file containing a list of all communities and their
            respective annual electricity demand (kWh).
            Example: 'electricity_demand/d_e_yr.csv'
        com_nr : int
            BFS number of community. Example: 1
        
        Returns
        -------
        float
            annual electricity demand [kWh]
        """
        # f_hh = electricity_demand_file_household
        # f_ind = electricity_demand_file_industry
        c = com_nr
        
        # Read csv-file containing annual electricity demand of each community:
        # df_data_hh = pd.read_csv(f_hh,encoding="UTF8")
        # df_data_ind = pd.read_csv(f_ind,encoding="UTF8")
        #df_data.to_csv('test_d_e.csv')
        
        # check if community is contained in the file:            
        # if df_data['Municipality'].str.contains(c).any(): # This function can't handle string with whitespaces
        if (df_meta['GGDENR'] == c).sum() == 1:
            # d_e_yr = df_meta.loc[df_meta['GGDENR']==c, ]
            d_e_yr_sfh = df_meta.loc[df_meta['GGDENR']==c, 'kWh_household_sfh'].values[0]
            d_e_yr_mfh = df_meta.loc[df_meta['GGDENR']==c, 'kWh_household_mfh'].values[0]
            d_e_yr_ind = df_meta.loc[df_meta['GGDENR']==c, 'Electricity_Industry'].values[0]
            d_e_yr_ser = df_meta.loc[df_meta['GGDENR']==c, 'Electricity_Service'].values[0]
        else:
            sys.exit(f"Error in get_d_e_yr(): {c} is not found in meta file.")
        
        d_e_hh_yr = d_e_yr_sfh + d_e_yr_mfh + d_e_yr_ind + d_e_yr_ser
        
        self._d_e_sfh_yr = d_e_yr_sfh
        self._d_e_mfh_yr = d_e_yr_mfh
        self._d_e_ind_yr = d_e_yr_ind
        self._d_e_ser_yr = d_e_yr_ser
        self._d_e_hh_yr = d_e_hh_yr
        
        return d_e_yr_sfh, d_e_yr_mfh, d_e_yr_ind, d_e_yr_ser
    
    
    # def d_e_hr(d_e_yr,
    #            electricity_profile_dir,
    #            electricity_profile_file
    #            ):
        
    #     """Returns the hourly electricity demand (d_e_hr) of the selected community.
        
    #     Parameters
    #     ----------
    #     d_e_yr : float
    #         Annual electricity demand of selected community [kWh].
    #     electricity_profile_dir : str
    #         Path to directory containing files of electricity load profiles.
    #     electricity_profile_file : str
    #         Name of csv file containing timeseries data of electricity load
    #         profile. (e.g. 'Buildings_A_B_power_load_profile.csv')
        
    #     Returns
    #     -------
    #     list
    #         hourly electricity demand [kWh]
    #     """
    #     file_path = electricity_profile_dir + electricity_profile_file
    #     tmp_df = pd.read_csv(file_path) # [Wh] profile for one building:
    #     tmp_df['P_avg'] = tmp_df['P_avg']/1000 # [kWh] convert unit from Wh to kWh:
    #     tmp_df.reset_index(inplace=True)
    #     tmp_sum = tmp_df['P_avg'].sum()
    #     d_e_hr = d_e_yr/tmp_sum*tmp_df['P_avg']
    #     tmp_df.drop(tmp_df.index, inplace=True) # Delete tmp_df content
        
    #     return d_e_hr
    
    # def get_d_e_hh_hr(
    def compute_d_e_hh_hr(
            self,
            profiles_file,
            com_kt
            ):
        
        """Returns the hourly "household" electricity demand (d_e_hh_hr)
        (excl. elect. demand for heating) of the selected community.
        
        Parameters
        ----------
        d_e_yr_sfh : float
            Annual electricity demand of single family houses of selected community [kWh].
        d_e_yr_mfh : float
            Annual electricity demand of multi family houses of selected community [kWh].
        electricity_profile_dir : str
            Path to directory containing files of electricity load profiles.
        electricity_profile_file : str
            Name of csv file containing timeseries data of electricity load
            profile. (e.g. 'Buildings_A_B_power_load_profile.csv')
        
        Returns
        -------
        list
            hourly electricity demand [kWh]
        """
        self.profiles = profiles_file
        
        # =========================================================================
        # TEMPORARY FIX:
        # Avoid negative values in the demand profile d_e_hh
        # Replace negative values with 0:
        
        # =========================================================================
        
        # Check if annual values have been calculated:
        self.num_test(self._d_e_sfh_yr)
        self.num_test(self._d_e_mfh_yr)
        self.num_test(self._d_e_ind_yr)
        self.num_test(self._d_e_ser_yr)
        
        # cond = (
        #     self._d_e_sfh_yr == 0,
        #     self._d_e_mfh_yr == 0,
        #     self._d_e_ind_yr == 0,
        #     self._d_e_ser_yr == 0,
        #     )
        # # print(self._d_e_sfh_yr)
        # # print(self._d_e_mfh_yr)
        # # print(self._d_e_ind_yr)
        # # print(self._d_e_ser_yr)
        # if any(cond):
        #     raise ValueError("Annual values must be computed first!")
        
        # d_e_hr = (tmp_df['SFH'] * d_e_yr_sfh + 
        #           tmp_df['MFH'] * d_e_yr_mfh +  
        #           temp_df_industry[com_kt] * d_e_yr_ser + 
        #           temp_df_industry[com_kt] * d_e_yr_ind)
        
        d_e_hh_hr = (
            self.profiles['Electricity_Profile_SFH'] * self._d_e_sfh_yr + 
            self.profiles['Electricity_Profile_MFH'] * self._d_e_mfh_yr +
            self.profiles['Electricity_Profile_Industry_' + com_kt] * self._d_e_ser_yr + 
            self.profiles['Electricity_Profile_Industry_' + com_kt] * self._d_e_ind_yr
            )
        
        self._d_e_hh = np.array(d_e_hh_hr)
        
        
        return np.array(d_e_hh_hr)
    
    # def get_d_e_h(self, tech_instances):
    def compute_d_e_h(self, tech_instances):
        """
        Compute the electricity demand for heating (hourly and annual).

        Parameters
        ----------
        tech_instances : dict
            Dictionnary containing technology instances.

        Raises
        ------
        ValueError
            Electricity input to heating techs must be computed before
            computing this electricity demand.

        Returns
        -------
        None.

        """
        
        # -----------------------------------------------
        # Base scenario techs:
        
        # Electricity used for heat pump:
        if 'heat_pump' in tech_instances:
            hp_inst = tech_instances['heat_pump']
            if len(hp_inst.get_u_e()) == 0:
                raise ValueError("u_e_hp must be computed first!")
            else:
                u_e_hp = hp_inst.get_u_e()

        # Electricity used for electric heater:
        if 'electric_heater' in tech_instances:
            eh_inst = tech_instances['electric_heater']
            if len(eh_inst.get_u_e()) == 0:
                raise ValueError("u_e_eh must be computed first!")
            else:
                u_e_eh = eh_inst.get_u_e()
                
        d_e_h = np.array(u_e_hp) + np.array(u_e_eh)
        
        # -----------------------------------------------
        # Additional techs:
                
        if 'heat_pump_cp' in tech_instances:
            hpcp_inst = tech_instances['heat_pump_cp']
            if len(hpcp_inst.get_u_e()) == 0:
                raise ValueError("u_e_hpcp must be computed first!")
            else:
                u_e_hpcp = hpcp_inst.get_u_e()

            d_e_h += np.array(u_e_hpcp)

        if 'heat_pump_cp_lt' in tech_instances:
            hpcplt_inst = tech_instances['heat_pump_cp_lt']
            if len(hpcplt_inst.get_u_e()) == 0:
                raise ValueError("u_e_hpcplt must be computed first!")
            else:
                u_e_hpcplt = hpcplt_inst.get_u_e()

            d_e_h += np.array(u_e_hpcplt)

        d_e_h_yr = sum(d_e_h)
        
        
        self._d_e_h = d_e_h
        self._d_e_h_yr = d_e_h_yr
        
        # print(self._d_e_h)

    # def get_d_e(self):
    def compute_d_e(self):
        """
        Compute total hourly and annual electricity demand
        (household, heating, transport)

        Returns
        -------
        None.

        """
        cond = (len(self._d_e_hh)==0, sum(self._d_e_hh)==0, len(self._d_e_h)==0)
        if any(cond):
            raise ValueError("Household and heating electricity demand must be "
                             "computed first!")
        
        if len(self._d_e_ev) == 0:
            self._d_e = np.array(self._d_e_hh) + np.array(self._d_e_h)
        else:
            self._d_e = (
                np.array(self._d_e_hh)
                + np.array(self._d_e_h) 
                + np.array(self._d_e_ev)
                )

        self._d_e_yr = sum(self._d_e)
        
        # Run test:
        if self._d_e_yr == 0.0:
            raise Exception('Annual electricity demand is zero.')
            
    def compute_d_e_ev(
            self,
            ev_profiles_dir,
            ev_munic_name_nr_file,
            ev_profile_cp_file,
            ev_profile_fe_file,
            ev_profile_pd_file,
            ev_profile_pu_file,            
            ev_integration_factor,
            com_percent,
            optimisation,
            ev_flexibility,
            ):
        
        # Read munic file:
        munic_file_path = ev_profiles_dir + ev_munic_name_nr_file
        df_munic_name_nr = pd.read_feather(munic_file_path)
        
        # print(df_munic_name_nr.head())
        
        cp_file_dir = ev_profiles_dir + ev_profile_cp_file
        pd_file_dir = ev_profiles_dir + ev_profile_pd_file
        pu_file_dir = ev_profiles_dir + ev_profile_pu_file
        fe_file_dir = ev_profiles_dir + ev_profile_fe_file
        
        # df_ev_profile = pd.read_feather(cp_file_dir)
        df_ev_cp_profile = pd.read_feather(cp_file_dir)
        df_ev_pd_profile = pd.read_feather(pd_file_dir)
        df_ev_pu_profile = pd.read_feather(pu_file_dir)
        df_ev_fe_profile = pd.read_feather(fe_file_dir)
        
        ts_len = len(self.get_d_e())
        n_days = int(ts_len/24.0)
        
        if len(com_percent) == 0:
            munic_name = df_munic_name_nr.loc[
                df_munic_name_nr['munic_nr']==self.com_nr,'munic_name'
                ]
            
            munic_name = munic_name.iloc[0]
                
            tmp_d_e_ev_cp = np.array(df_ev_cp_profile[munic_name])
            tmp_d_e_ev_pd = np.array(df_ev_pd_profile[munic_name])
            tmp_d_e_ev_pu = np.array(df_ev_pu_profile[munic_name])
            tmp_f_e_ev_pot_dy = np.array(df_ev_fe_profile[munic_name])
        
        else:
            df_munic_name_nr.sort_values(by='munic_nr')
            munic_names = df_munic_name_nr.loc[
                df_munic_name_nr['munic_nr'].isin(com_percent.index),'munic_name'
                ]
            
            df_ev_cp_profile = df_ev_cp_profile[munic_names]
            df_ev_pd_profile = df_ev_pd_profile[munic_names]
            df_ev_pu_profile = df_ev_pu_profile[munic_names]
            df_ev_fe_profile = df_ev_fe_profile[munic_names]
            
            df_ev_cp_profile.columns = df_munic_name_nr.loc[
                df_munic_name_nr['munic_nr'].isin(com_percent.index),'munic_nr'
                ]
            df_ev_pd_profile.columns = df_munic_name_nr.loc[
                df_munic_name_nr['munic_nr'].isin(com_percent.index),'munic_nr'
                ]
            df_ev_pu_profile.columns = df_munic_name_nr.loc[
                df_munic_name_nr['munic_nr'].isin(com_percent.index),'munic_nr'
                ]
            df_ev_fe_profile.columns = df_munic_name_nr.loc[
                df_munic_name_nr['munic_nr'].isin(com_percent.index),'munic_nr'
                ]
            
            tmp_d_e_ev_cp = np.array(df_ev_cp_profile.mul(com_percent).sum(axis = 1))
            tmp_d_e_ev_pd = np.array(df_ev_pd_profile.mul(com_percent).sum(axis = 1))
            tmp_d_e_ev_pu = np.array(df_ev_pu_profile.mul(com_percent).sum(axis = 1))
            tmp_f_e_ev_pot_dy = np.array(df_ev_fe_profile.mul(com_percent).sum(axis = 1))
            
        tmp_d_e_ev_cp = tmp_d_e_ev_cp[:ts_len]
        tmp_d_e_ev_pd = tmp_d_e_ev_pd[:ts_len]
        tmp_d_e_ev_pu = tmp_d_e_ev_pu[:ts_len]
        tmp_f_e_ev_pot_dy = tmp_f_e_ev_pot_dy[:n_days]
        
        # Set negative values to 0:
        tmp_d_e_ev_cp[tmp_d_e_ev_cp < 0] = 0
        tmp_d_e_ev_pd[tmp_d_e_ev_pd < 0] = 0
        tmp_d_e_ev_pu[tmp_d_e_ev_pu < 0] = 0

        if ev_integration_factor==100:
            pass
        elif not (0 <= ev_integration_factor <= 100):
            msg = "demand_side.ev_integration_factor can not exceed 100% or be negative."
            raise ValueError(msg)
        else:
            tmp_d_e_ev_cp = tmp_d_e_ev_cp*ev_integration_factor/100.0
            tmp_d_e_ev_pd = tmp_d_e_ev_pd*ev_integration_factor/100.0
            tmp_d_e_ev_pu = tmp_d_e_ev_pu*ev_integration_factor/100.0
            tmp_f_e_ev_pot_dy = tmp_f_e_ev_pot_dy*ev_integration_factor/100.0
            
        self.update_d_e_ev_cp(tmp_d_e_ev_cp, n_days)
        self.update_d_e_ev_pd(tmp_d_e_ev_pd)
        self.update_d_e_ev_pu(tmp_d_e_ev_pu)
        self.update_f_e_ev_pot_dy(tmp_f_e_ev_pot_dy)
        
        if ev_flexibility == False or optimisation == False:
            self.update_d_e_ev(tmp_d_e_ev_cp)
            
        elif optimisation==True and ev_flexibility==True:
            self.update_d_e_ev(tmp_d_e_ev_cp)  # This will be adapted in optimisation.
        
        tmp_d_e = self.get_d_e() + self.get_d_e_ev()
        self.update_d_e(tmp_d_e)
        
    # def update(self, var_name, var_data):
    #     # if len(var_data) != len(self.__dict__[var_name]):
    #     #     raise ValueError("d_e_updated must have the same length as " + var_name[1:] + "!")
            
    #     self.__dict__[var_name] = np.array(var_data)
            
    def update_d_e(self, d_e_updated):
        if len(d_e_updated) != len(self._d_e):
            raise ValueError("d_e_updated must have the same length as d_e!")
            
        self._d_e = np.array(d_e_updated)
        
    def update_d_e_i(self, i, val):   
        self.num_test(val)         
        self._d_e[i] = float(val)
        
    def update_d_e_ev(self, d_e_ev_udpated):
        """
        Electric vehicles.

        Parameters
        ----------
        d_e_ev_udpated : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        self._d_e_ev = np.array(d_e_ev_udpated)
        
        self._d_e_ev_cp_dev = self._d_e_ev - self._d_e_ev_cp        
        self._d_e_ev_cp_dev_pos = np.where(
            self._d_e_ev_cp_dev > 0, self._d_e_ev_cp_dev, 0.0
            )
        self._d_e_ev_cp_dev_neg = np.where(
            self._d_e_ev_cp_dev < 0, self._d_e_ev_cp_dev, 0.0
            )
        self._f_e_ev_dy = dem_helper.hourly_array_to_daily(
            self._d_e_ev_cp_dev_pos
            )
        
    def update_d_e_ev_cp(self, d_e_ev_cp_udpated, n_days):       
        self._d_e_ev_cp = np.array(d_e_ev_cp_udpated)
        self._d_e_ev_cp_dy = self.__compute_d_e_ev_cp_dy(
            self._d_e_ev_cp,
            n_days
            )

    def __compute_d_e_ev_cp_dy(self, d_e_ev_cp, n_days):
        """
        Compute daily charging profile from hourly profile.
        """
        
        d_e_ev_cp_dy = np.zeros(n_days)
        
        for day in range(n_days):
            # sum up EV demand for every day:
            hr = 0 # hour of the day
            tmp_sum = 0 # initialise sum across a day
            
            while hr < 24:
                ts = day*24 + hr # absolute timestep
                tmp_sum += d_e_ev_cp[ts]
                hr+=1
                
            d_e_ev_cp_dy[day] = tmp_sum
            
        return d_e_ev_cp_dy
        
    def update_d_e_ev_pd(self, d_e_ev_pd_udpated):
        self._d_e_ev_pd = np.array(d_e_ev_pd_udpated)
        
    def update_d_e_ev_pu(self, d_e_ev_pu_udpated):
        self._d_e_ev_pu = np.array(d_e_ev_pu_udpated)
        
    def update_f_e_ev_pot_dy(self, f_e_ev_pot_dy_udpated):
        self._f_e_ev_pot_dy = np.array(f_e_ev_pot_dy_udpated)
        
    def update_d_e_hh(self, d_e_hh_udpated):
        """
        Electricity for household.

        Parameters
        ----------
        d_e_hh_udpated : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        self._d_e_hh = np.array(d_e_hh_udpated)
        
    def update_d_e_h(self, d_e_h_udpated):
        """
        Electricity for heating.

        Parameters
        ----------
        d_e_h_udpated : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        self._d_e_h = np.array(d_e_h_udpated)
        
    def update_d_e_h_i(self, i, val):
        self.num_test(val)
        self._d_e_h[i] = float(val)
        
    def update_d_h(self, d_h_udpated):
        """
        Heat demand.

        Parameters
        ----------
        d_e_h_udpated : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        self._d_h = np.array(d_h_udpated)

    def update_d_e_unmet(self, d_e_unmet_updated):
        self._d_e_unmet = np.array(d_e_unmet_updated)
        
    def update_d_h_unmet(self, d_h_unmet_updated):
        self._d_h_unmet = np.array(d_h_unmet_updated)
        
    def update_d_h_unmet_dhn(self, d_h_unmet_dhn_updated):
        self._d_h_unmet_dhn = np.array(d_h_unmet_dhn_updated)

    def reset_d_e_unmet(self):
        null_array = np.array([0.0]*len(self._d_e))
        self._d_e_unmet = null_array
        
    def reset_d_h_unmet(self):
        null_array = np.array([0.0]*len(self._d_h))
        self._d_h_unmet = null_array
    
    def reset_d_h_unmet_dhn(self):
        null_array = np.array([0.0]*len(self._d_h))
        self._d_h_unmet_dhn = null_array
        
    # def d_e_hr_split(self, d_e_hr, d_h_e_hr):
        
    #     """
    #     Splits the electricity profile in two parts: direct and heating. Direct part
    #     is used for electric appliances directly (e.g. lighting, ...).
        
    #     Parameters
    #     ----------
    #     d_e_hr : pandas dataseries (e.g. column of a dataframe)
    #         Electricity load profile (total, incl. hp etc...) [kWh].
    #     d_h_e_hr : pandas dataseries (e.g. column of a dataframe)
    #         Electricity load profile for heating (hp, eh, ...) [kWh]. 
    
    #     Returns
    #     -------
    #     list
    #         List with direct electricity load profile [kWh].
    #     """
    #     if len(d_e_hr) == len(d_h_e_hr):
    #         df_d_e_direct_hr = d_e_hr - d_h_e_hr
        
    #     else:
    #         sys.exit("Error in d_e_hr_split(): input arguments must be of same length!")
        
    #     list_d_e_direct_hr = df_d_e_direct_hr.tolist()
        
    #     return list_d_e_direct_hr
    
    
    """----------------------------------------------------------------------------
    HEAT DEMAND:
    """
    
    def meteostat_weather_data(self, lat, lon, alt, tf_start, tf_end):
        
        """
        Accesses hourly meteostat weather data via API and saves it to dataframe.
        Git: https://github.com/meteostat/meteostat-python
        
        Parameters
        ----------
        lat: float
            latitude of location as decimal number (e.g. 47.556)
        lon: float
            longitude of location as decimal number
        tf_start: string
            start of timeframe. Format: '%Y-%m-%d %H:%M' (e.g. 2023-04-26 04:00)
        tf_end: string
            end of timeframe. Format: '%Y-%m-%d %H:%M' (e.g. 2023-07-26 23:00)
            
    
        Returns
        -------
        dataframe
            hourly weatherdata such as temeprature, humidity, ... (see Git link).
        """
        
        # Start date:
        date_obj_s = datetime.strptime(tf_start, '%Y-%m-%d %H:%M')
        year_s = date_obj_s.year
        month_s = date_obj_s.month
        day_s = date_obj_s.day
        hour_s = date_obj_s.hour
        
        # End date:
        date_obj_e = datetime.strptime(tf_end, '%Y-%m-%d %H:%M')
        year_e = date_obj_e.year
        month_e = date_obj_e.month
        day_e = date_obj_e.day
        hour_e = date_obj_e.hour
        
        #start = datetime(2020, 1, 1, 0)
        #end = datetime(2020, 12, 31, 23)
        start = datetime(year_s, month_s, day_s, hour_s)
        end = datetime(year_e, month_e, day_e, hour_e)
        
    
        # Beispiel:
        #lat = 47.03204
        #lon = 9.43204
        #alt = 509
    
        point = meteostat.Point(lat, lon, alt)
    
        #(Dataframe definieren und mit .fetch() Abfrage machen)
        df_ms = meteostat.Hourly(point, start, end)
        df_ms = df_ms.fetch()
        
        return df_ms
        
     
    def weather_data_factory(self,
                             com_name,
                             com_lat,
                             com_lon,
                             com_alt,
                             weather_data_dir,
                             tf_start,
                             tf_end):
        
        """
        Takes meteostat hourly weather data df of several years and creates a df of
        one year with averaged hourly values across several years.
        
        Parameters
        ----------
        com_name : string
            Name of community. Example: 'Allschwil'
        com_lat : float
            Latitude of selected community.
        com_lon : float
            Longitude of selected community.
        com_alt : float
            Altitude of selected community.
        weather_data_dir: string
            Location of meteostat files. Example: './heat_demand/weather_data/'
        tf_start : string
            Start date of measurement data time-series (e.g.'2020-01-01 00:00')
        tf_end:
            End date of measurement data time-series (e.g. '2021-12-21 23:00')
        
        Returns
        -------
        dataframe
            averaged hourly values of weather data
        """
        
        # meteostat file location + name:
        meteostat_file = weather_data_dir + f"meteostat/meteostat_{com_name}.csv"
        # check if file exists:
        file_exist = os.path.isfile(meteostat_file)
        
        if file_exist == True:
            # df_data = pd.read_csv(meteostat_file,
            #                       parse_dates=['time'],
            #                       index_col='time')
            
            # Reading the CSV without parsing dates and setting index initially
            df_data = pd.read_csv(meteostat_file)
            
            # Check if the DataFrame contains data:
            if df_data.shape[0] == 0:
                
                import warnings
    
                # Issue a warning
                warnings.warn(f"The meteostat file for {com_name} does not contain any data! "
                              "A new meteostat file will be generated.", UserWarning)
                
                # raise Warning(f"The meteostat file for {com_name} does not contain any data!")
                # com_alt = com_alt - 100 # reduce altitude to account for meteostat bug
                file_exist = False # reproduce the file
                # raise ValueError(f"The meteostat file for {com_name} does not contain any data!")
                
            else:
                # else:
                #     print("The DataFrame has rows.")
                
                # Manually parse the 'time' column as datetime
                df_data['time'] = pd.to_datetime(df_data['time'])
                
                # Set 'time' column as the index
                df_data.set_index('time', inplace=True)
            
        if file_exist == False:
            # weather data will be retrieved from the meteostat API:
            df_data = self.meteostat_weather_data(
                com_lat,
                com_lon,
                com_alt,
                tf_start,
                tf_end
                )
            
            # Check meteostat data:
            # len_ms = len(df_data)
            # if len_ms < 365:
            if df_data.shape[0] == 0:
                df_data = self.__meteostat_bug_hack(
                    com_name,
                    com_lat,
                    com_lon,
                    com_alt,
                    tf_start,
                    tf_end
                    )
                # raise Exception("Meteostat data incomplete.")
    
            # the data will be saved to a csv file, so that it can be used
            # later, if data for the same location is required (to avoid the
            # number of API calls):
            df_data.to_csv(meteostat_file)
    
    
        # remove 29.02. in leap year:
        df_data = df_data[~((df_data.index.month == 2) & (df_data.index.day == 29))]
           
        # group hourly data and calculate mean for every hour of the year:
        df_grouped = df_data.groupby([df_data.index.month,
                                      df_data.index.day,
                                      df_data.index.hour])
        df_mean = df_grouped.mean()
        
        # create datetime column to be used as index:
        start_date = pd.Timestamp('1900-01-01 00:00') # 1900 is no leap year
        date_range = pd.date_range(start=start_date, periods=8760, freq='H')
        df_mean['datetime'] = date_range
        
        # format the datetime column to "YYYY-MM-DD hh:mm"
        df_mean['datetime'] = df_mean['datetime'].dt.strftime('%Y-%m-%d %H:%M')
        
        # replace index with datetime index:
        df_mean = df_mean.set_index('datetime')
        
        # convert index to DatetimeIndex:
        df_mean.index = pd.to_datetime(df_mean.index)
    
        df_weather = df_mean
    
        return df_weather
    
    def __meteostat_bug_hack(
            self,
            com_name,
            com_lat,
            com_lon,
            com_alt,
            tf_start,
            tf_end
            ):
        
        """
        For some locations, meteostat doesn't produce weather data. If the altitude
        is adjusted, however, it produces data.
        Example: Alto Malcantone
                Coord_lat  Coord_long  altitude_median
          1559  46.042663    8.885755            802.0
        """
        
        import warnings

        # Issue a warning
        warnings.warn(f"The meteostat file for {com_name} does not contain any data! "
                      "com_alt is being adjusted to account for meteostat bug.", UserWarning)
        
        count_max = 100
        counter = 1
        alt_incr = 10
        com_alt_new = com_alt
        
        while counter < count_max:
            
            # Increase:
            com_alt_new = com_alt + counter*alt_incr            
            df_data = self.meteostat_weather_data(
                com_lat,
                com_lon,
                com_alt_new,
                tf_start,
                tf_end
                )
            if df_data.shape[0] > 0:
                print(f"Original altitude: {com_alt}")
                print(f"Adjusted altitude: {com_alt_new}")
                break
            
            # Decrease:
            com_alt_new = com_alt - counter*alt_incr
            if com_alt_new < 0:
                pass
            else:
                df_data = self.meteostat_weather_data(
                    com_lat,
                    com_lon,
                    com_alt_new,
                    tf_start,
                    tf_end
                    )
                if df_data.shape[0] > 0:
                    print(f"Original altitude: {com_alt}")
                    print(f"Adjusted altitude: {com_alt_new}")
                    break

            counter += 1
        
        # Check meteostat data:
        # len_ms = len(df_data)
        # if len_ms < 365:
        if df_data.shape[0] == 0:
            raise Exception("Meteostat data incomplete. "
                            "A new file could not be generated.")
        else:
            return df_data
    
    # def get_d_h_yr(
    def compute_d_h_yr(
            self,
            df_meta
            ):
        
        """Returns the annual heat demand (d_e_yr) of the selected community.
        
        Parameters
        ----------
        df_com_year : pandas dataframe
            Dataframe containing information about the selected community.
            (1 row per building)
        yearly_heat_demand_col : string
            Header of column containing annual heat demand values in df_com_year.
        
        Returns
        -------
        float
            annual heat demand [kWh]
        """
            
        # Annual total heat demand of community:
        d_h_s_yr = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'Total_Heating'].values[0] # [kWh]
        d_h_hw_yr = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'Total_Hot_Water'].values[0] # [kWh]
        d_h_yr = d_h_s_yr + d_h_hw_yr
        
        self._d_h_s_yr = d_h_s_yr
        self._d_h_hw_yr = d_h_hw_yr
        self._d_h_yr = d_h_yr
        
        if self._d_h_yr == 0.0:
            raise Exception('Annual heat demand is zero.')
        
        return d_h_yr, d_h_s_yr, d_h_hw_yr
    
    def add_future_demand_col(
            self,
            com_nrs,
            df_com_yr,
            df_meta,
            year,
            rcp_scenario,
            ts_type,
            yearly_heat_demand_col='heat_energy_demand_estimate_kWh_combined',
            new_header = 'd_h_s_yr_future',
            writeToMeta = True,
            distinguishByConstructionYear = True
            ):
        
        
        
        if len(com_nrs) == 0:
        
            scaling_factor_t12, scaling_factor_t15 =\
                self.__get_d_h_s_scaling_factors(
                    com_nr = self.com_nr,
                    year=year,
                    rcp_scenario=rcp_scenario,
                    ts_type=ts_type,
                    )
                
            # Create additional column for future heat demand:
            df_com_yr[new_header] = df_com_yr[yearly_heat_demand_col].copy()
            
            if distinguishByConstructionYear:
                df_com_yr.loc[df_com_yr['GBAUP'] <= 8015, new_header] =\
                    df_com_yr[yearly_heat_demand_col]*scaling_factor_t15
        
                df_com_yr.loc[df_com_yr['GBAUP'] > 8015, new_header] =\
                    df_com_yr[yearly_heat_demand_col]*scaling_factor_t12
        
                df_com_yr.loc[df_com_yr['GBAUP'].isna(), new_header] =\
                    df_com_yr[yearly_heat_demand_col]*scaling_factor_t15
            else:
                df_com_yr[new_header] =\
                    scaling_factor_t12*df_com_yr[yearly_heat_demand_col]

        else:
            for com_nr in com_nrs:
                
                arg_com = df_com_yr['GGDENR'] == com_nr
                
                scaling_factor_t12, scaling_factor_t15 =\
                    self.__get_d_h_s_scaling_factors(
                        com_nr = com_nr,
                        year=year,
                        rcp_scenario=rcp_scenario,
                        ts_type=ts_type,
                        )
                
                if distinguishByConstructionYear:
                    df_com_yr.loc[(df_com_yr['GBAUP'] <= 8015)&arg_com, new_header] =\
                        df_com_yr[yearly_heat_demand_col]*scaling_factor_t15
            
                    df_com_yr.loc[(df_com_yr['GBAUP'] > 8015)&arg_com, new_header] =\
                        df_com_yr[yearly_heat_demand_col]*scaling_factor_t12
            
                    df_com_yr.loc[(df_com_yr['GBAUP'].isna())&arg_com, new_header] =\
                        df_com_yr[yearly_heat_demand_col]*scaling_factor_t15
                else:
                    df_com_yr.loc[arg_com, new_header] =\
                        df_com_yr[yearly_heat_demand_col]*scaling_factor_t12
                    

        GGDENR = self.com_nr

        if writeToMeta:
            df_meta.loc[df_meta['GGDENR']==GGDENR, 'v_h_eh'] = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_eh', 'd_h_s_yr_future'].sum()
            df_meta.loc[df_meta['GGDENR']==GGDENR, 'v_h_hp'] = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_hp', 'd_h_s_yr_future'].sum()
            df_meta.loc[df_meta['GGDENR']==GGDENR, 'v_h_dh'] = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_dh', 'd_h_s_yr_future'].sum()
            df_meta.loc[df_meta['GGDENR']==GGDENR, 'v_h_gb'] = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_gb', 'd_h_s_yr_future'].sum()
            df_meta.loc[df_meta['GGDENR']==GGDENR, 'v_h_ob'] = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_ob', 'd_h_s_yr_future'].sum()
            df_meta.loc[df_meta['GGDENR']==GGDENR, 'v_h_wb'] = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_wb', 'd_h_s_yr_future'].sum()
            df_meta.loc[df_meta['GGDENR']==GGDENR, 'v_h_solar'] = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_solar', 'd_h_s_yr_future'].sum()
            df_meta.loc[df_meta['GGDENR']==GGDENR, 'v_h_other'] = df_com_yr.loc[df_com_yr['Heating_System'] == 'v_h_other', 'd_h_s_yr_future'].sum()
            df_meta.loc[df_meta['GGDENR']==GGDENR, 'Total_Heating'] = df_com_yr.loc[:, 'd_h_s_yr_future'].sum()
        
            
        return new_header, df_meta
    
    def renovation_adjustments(
                self,
                com_nrs,
                df_com_yr,
                df_meta,
                year,
                total_renovation_activated = True,
                use_constant_total_renovation_rate = False,
                renovation_scenario='renovation_base', # 'renovation_low', 'renovation_high', 'renovation_base'
                constant_total_renovation_rate = 0.01, #float between 0 and 1
                total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios = {
                    'v_h_eh' : 0.0,
                    'v_h_hp' : 0.8, 'v_h_dh' : 0.05, 'v_h_gb' : 0.05, 
                    'v_h_ob' : 0.05, 'v_h_wb' : 0.05, 'v_h_solar' : 0.0, 
                    'v_h_other' : 0.0 }, 
                total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios = {
                    'v_hw_eh' : 0.1,
                    'v_hw_hp' : 0.7, 'v_hw_dh' : 0.05, 'v_hw_gb' : 0.05,
                    'v_hw_ob' : 0.05,'v_hw_wb' : 0.05,'v_hw_solar' : 0.0,
                    'v_hw_other' : 0.0 },
                heat_generator_renovation = True,
                optimisation_enabled = True,
                scen_techs = None,
                data_year = 2023,
                new_header = 'd_h_s_yr_future_renov_adjusted'
                ):


        print("\nAdjustment of demand to renovation, marking of old heat generators as up for renewal")

        df_com_yr['total_renovation_flag'] = False #Likelyhood of a specific building having been totally renovated
        #This can be a float between 0 and 1! 0=False, 1=True
        
        
        #Total renovation of buildings. 
        #This happens according to a rate either given by Streicher's paper or according to a constant rate
        if total_renovation_activated: 

            df_com_yr[new_header] = df_com_yr['d_h_s_yr_future'].copy()

            if use_constant_total_renovation_rate: #If a constant renovation rate is used
                renovation_counting_starting_year = df_com_yr['GBAUJ']+35 #no renovations in first 35 years
                renovation_counting_starting_year.loc[renovation_counting_starting_year < data_year] = data_year#Year when data was gathered
                renovation_counting_starting_year = renovation_counting_starting_year.fillna(data_year) #Fill nans with year when data was gathered
                yeardist = year-renovation_counting_starting_year #distance between simulation year and year when data was gathered
                yeardist = (np.abs(yeardist) + yeardist)/2 #needs to be positive, set all negative values = 0

                accumulated_new_weight = constant_total_renovation_rate*yeardist
                accumulated_new_weight[accumulated_new_weight > 1.0] = 1.0

                # accumulated_new_weight = 1.0-((1-constant_total_renovation_rate)**yeardist) #Probability that renovation has taken place
                df_com_yr[new_header] =\
                    ((1.0-accumulated_new_weight)*df_com_yr['d_h_s_yr_future']
                    +accumulated_new_weight*df_com_yr['d_h_s_yr_renov_future']) #adjust heat consumption
                df_com_yr['total_renovation_flag'] = accumulated_new_weight #float between 0 and 1
                # 'd_h_s_yr_future'

            else: #use Streicher data
                df_com_yr['total_renovation_flag'] = df_com_yr[renovation_scenario] <= year #if renovation year < simulation year--> mark for renovation
                df_com_yr.loc[df_com_yr['total_renovation_flag'], new_header] =\
                    df_com_yr['d_h_s_yr_renov_future'] #adjust heat consumption


            #In case of total renovation, the old heat and dhw generator is thrown out.
            #This dict gives the probabilities what it is replaced with.
            #If optimization is enabled, 100% goes to _other_, and the heat generator is then determiend in the optimization.
            #If optimization is disabled, more modern heat generators are installed.
            reassignment_dict_sh = {'v_h_eh' : 0.0,
                                'v_h_hp' : 0.0, 
                                'v_h_dh' : 0.0, 
                                'v_h_gb' : 0.0,
                                'v_h_ob' : 0.0,
                                'v_h_wb' : 0.0,
                                'v_h_solar' : 0.0,
                                'v_h_other' : 1.0 } if optimisation_enabled else total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios
            reassignment_dict_dhw = {'v_hw_eh' : 0.0,
                                'v_hw_hp' : 0.0, 
                                'v_hw_dh' : 0.0, 
                                'v_hw_gb' : 0.0,
                                'v_hw_ob' : 0.0,
                                'v_hw_wb' : 0.0,
                                'v_hw_solar' : 0.0,
                                'v_hw_other' : 1.0 } if optimisation_enabled else total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios

            GGDENR = self.com_nr


            #replacement of technologies while calculating the total generated heat from different heat sources. 
            # This is also applied to the dhw
            for systemtype in reassignment_dict_sh.keys():        
                df_meta.loc[df_meta['GGDENR']==GGDENR, systemtype] = (
                    df_com_yr.loc[df_com_yr['Heating_System'] == systemtype, new_header]
                                  *(1.0-df_com_yr.loc[df_com_yr['Heating_System'] == systemtype, 'total_renovation_flag'])
                    ).sum() + reassignment_dict_sh[systemtype]*(
                    sum([(df_com_yr.loc[df_com_yr['Heating_System'] == k, new_header]
                          *(df_com_yr.loc[df_com_yr['Heating_System'] == k, 'total_renovation_flag'])
                          ).sum() for k in reassignment_dict_sh.keys()])
                    )
            df_meta.loc[df_meta['GGDENR']==GGDENR, 'Total_Heating'] = df_com_yr.loc[:, new_header].sum()

            for systemtype in reassignment_dict_dhw.keys():        
                df_meta.loc[
                    df_meta['GGDENR']==GGDENR, systemtype
                    ] = (
                        df_com_yr.loc[df_com_yr['Hot_Water_System'] == systemtype, 'dhw_estimation_kWh_combined']
                        *(1.0-df_com_yr.loc[df_com_yr['Hot_Water_System'] == systemtype, 'total_renovation_flag'])
                        ).sum() + reassignment_dict_dhw[systemtype]*(
                    sum(
                        [(df_com_yr.loc[df_com_yr['Hot_Water_System'] == k, 'dhw_estimation_kWh_combined']
                          *(df_com_yr.loc[df_com_yr['Hot_Water_System'] == k, 'total_renovation_flag'])).sum() 
                          for k in reassignment_dict_dhw.keys()]
                        )
                    )



        #Replacement of heat generators after they've reached their end of life
        #For new buildings, they keep their heat generator as long as its lifetime last, and then it is thrown out.
        #For older building, they accumulate a constant probability for heat generator renewal each year, which is 1/lifetime
        #For each year between the simulation year and the data year, they accumulate some probability, e.g. for 2030, 
        # the probability of renewal is (2030 - 2023)/lifetime =~=  0.28
        #For all the renewal probabilities, they are calculated building-wise and the probability of total renovation is deducted.

        if heat_generator_renovation:
            
            df_com_yr['heat_generator_replacement_flag'] = 0.0

            heat_generator_lifetimes = {
                'v_h_eh': scen_techs['electric_heater']['lifetime'],
                'v_h_hp': scen_techs['heat_pump']['lifetime'],
                'v_h_dh': scen_techs['district_heating']['lifetime'],
                'v_h_gb': scen_techs['gas_boiler']['lifetime'],
                'v_h_ob': scen_techs['oil_boiler']['lifetime'],
                'v_h_wb': scen_techs['wood_boiler']['lifetime'],
                'v_h_solar': scen_techs['solarthermal_rooftop']['lifetime'],
                'v_h_other': 1.0,
            }

            build_year_plus_lifetime = df_com_yr['GBAUJ'] + df_com_yr['Heating_System'].map(heat_generator_lifetimes)


            lifetimes = df_com_yr['Heating_System'].map(heat_generator_lifetimes)

            recently_built = (data_year <= build_year_plus_lifetime)

            df_com_yr.loc[recently_built, 'heat_generator_replacement_flag'] = (year > build_year_plus_lifetime).astype(float) - df_com_yr.loc[recently_built, 'total_renovation_flag']

            

            yeardelta = 0.0
            if year-data_year>0:
                yeardelta = year-data_year
            fraction_up_for_renovation = (yeardelta)*1.0/lifetimes
            fraction_up_for_renovation[fraction_up_for_renovation > 1.0] = 1.0
            fraction_up_for_renovation = fraction_up_for_renovation - df_com_yr['total_renovation_flag']
            
            df_com_yr.loc[~recently_built, 'heat_generator_replacement_flag'] = fraction_up_for_renovation

            df_com_yr.loc[df_com_yr['heat_generator_replacement_flag'] < 0.0, 'heat_generator_replacement_flag'] = 0.0
            
            heat_generators_total_power_up_for_renovation = {}
            heat_generators_total_power = {}
            heat_generators_replacement_rates = {}

            for k in heat_generator_lifetimes.keys():
                heat_generators_total_power_up_for_renovation[k] = (
                    (df_com_yr.loc[df_com_yr['Heating_System'] == k, new_header]
                     *(df_com_yr.loc[df_com_yr['Heating_System'] == k, 'heat_generator_replacement_flag'])).sum() 
                     + (df_com_yr.loc[df_com_yr['Hot_Water_System'] == k.replace("_h_", "_hw_"), 'dhw_estimation_kWh_combined']
                        *(df_com_yr.loc[df_com_yr['Hot_Water_System'] == k.replace("_h_", "_hw_"), 'heat_generator_replacement_flag'])).sum())
                heat_generators_total_power[k] = (df_meta.loc[df_meta['GGDENR']==GGDENR, k]
                                                  + df_meta.loc[df_meta['GGDENR']==GGDENR, k.replace("_h_", "_hw_")])
                heat_generators_replacement_rates[k] = (float(heat_generators_total_power_up_for_renovation[k] / heat_generators_total_power[k].iloc[0]) 
                                                        if float(heat_generators_total_power[k].iloc[0])>0 else 0.0)
        
            scen_techs['demand_side']['heat_generator_replacement_rates'] = heat_generators_replacement_rates
            
            return df_meta

        return df_meta


    def __get_d_h_s_scaling_factors(
            self,
            com_nr,
            year,
            rcp_scenario='RCP26',
            ts_type='tas_median'
            ):
        """
        Obtain scaling factor for future space heating demand.
        Based on heating degree days (HDD).

        Parameters
        ----------
        year : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        if year in {2023,2030,2040,2050}:
            pass
        else:
            msg = (
                f"Value for selected year ({year}) is invalid. "
                "Options are 2023, 2030, 2040, or 2050.")
            raise ValueError(msg)
        
        # Scaling factor for future demand:
        hdd_munic_file_current = self.paths.master_data_dir + 'HDD_and_HDH_profiles/HDD_Municipality_2023.feather'
        hdd_munic_file_future = self.paths.master_data_dir + f'HDD_and_HDH_profiles/HDD_Municipality_{str(year)}.feather'
        
        df_hdd_current = pd.read_feather(hdd_munic_file_current)
        df_hdd_future = pd.read_feather(hdd_munic_file_future)
        
        header_current_t12 = "HDD_12_2023"
        header_current_t15 = "HDD_15_2023"
        
        if year==2023:
            header_future_t12 = "HDD_12_2023"
            header_future_t15 = "HDD_15_2023"
        else:        
            header_future_t12 = f"HDD_12_{str(year)}_{rcp_scenario}_{ts_type}"
            header_future_t15 = f"HDD_15_{str(year)}_{rcp_scenario}_{ts_type}"

        hdd_current_t12 = df_hdd_current.loc[df_hdd_current['GGDENR'] == com_nr, header_current_t12].values[0]
        hdd_future_t12 = df_hdd_future.loc[df_hdd_future['GGDENR'] == com_nr, header_future_t12].values[0]

        hdd_current_t15 = df_hdd_current.loc[df_hdd_current['GGDENR'] == com_nr, header_current_t15].values[0]
        hdd_future_t15 = df_hdd_future.loc[df_hdd_future['GGDENR'] == com_nr, header_future_t15].values[0]
        
        scaling_factor_t12 = hdd_future_t12/hdd_current_t12
        scaling_factor_t15 = hdd_future_t15/hdd_current_t15
        
        return scaling_factor_t12, scaling_factor_t15
    
    # def get_d_h_hr(
    def compute_d_h_hr(
            self,
            com_name,
            com_nr_original,
            com_lat,
            com_lon,
            com_alt,
            tf_start,
            tf_end,
            base_year = 2025):
                # d_h_yr,
                # d_hw_yr):
        
        """
        Computes hourly heat demand profile based on annual heat demand using
        heating degree days (hdd) and heating degree hours (hdh).
        
        Parameters
        ----------
        com_name : string
            Name of community. Example: 'Allschwil'
        com_lat : float
            Latitude of selected community.
        com_lon : float
            Longitude of selected community.
        com_alt : float
            Altitude of selected community.
        tf_start : string
            Start date of measurement data time-series (e.g.'2020-01-01 00:00')
        tf_end:
            End date of measurement data time-series (e.g. '2021-12-21 23:00')
        d_h_yr : float
            Annual heating demand [kWh]. 
    
        Returns
        -------
        pandas dataframe
            Dataframe with hourly time-series. Column 'd_h_hr' contains the hourly
            heat demand [kWh].
        """
        
        # Inputs:
        temp_base = 12.0 # Basis Temperatur [°C]
        # hwb =  d_h_yr # Heizwärmebedarf [kWh/y]
        weather_data_dir = self.paths.weather_data_dir
    
        weather_data_dir_delta = self.paths.weather_data_delta_method_dir

        df_hour_all = pd.read_feather(weather_data_dir_delta + str(com_nr_original) + ".feather")

        # Output:
        # Dataframe mit der Kolonne 'd_h_hr' welche die benötigte Energiemenge [kWh] pro Stunde angibt.

        # create weather data:
        # df_weather_data = self.weather_data_factory(
        #     com_name,
        #     com_lat,
        #     com_lon,
        #     com_alt,
        #     weather_data_dir,
        #     tf_start,
        #     tf_end
        #     )
        

        dhw_profile_dir = self.paths.dhw_profile_dir
        dhw_profile_file = self.paths.dhw_profile_file
        
        dhw_profile = pd.read_feather(dhw_profile_dir + dhw_profile_file)
    
        #!!! TBD: how to determine the timeframe of weatherdata? Currently it
        # is hard-coded with tf_start = '2020-01-01 00:00'  and
        # tf_end = '2022-12-31 23:00'
    
        # df_hour = df_weather_data
        
        df_hour = df_hour_all[[base_year]]
        df_hour.index = df_hour.index.map(lambda t: t.replace(year=1900))
        df_hour = df_hour.rename(columns={base_year: "temp"})
        df_hour.index = df_hour.index.set_names("datetime")

        # df_hour["hdd"] = np.nan
        # df_hour["hdh"] = np.nan
        df_hour["hdd"] = pd.Series(False, index=df_hour.index, dtype="boolean")
        df_hour["hdh"] = pd.Series(False, index=df_hour.index, dtype="boolean")
    
        df_hour["tmp_diffT"] = np.nan
        df_hour["d_h_hr"] = np.nan # [kWh] 
    
        df_day = df_hour['temp'].resample("D").mean()
    
        for index_day, tempAverDay in df_day.items() :
            # on days where the avg temperature < base temperature, heat is required:
            if tempAverDay<temp_base :
                df_hour.loc[str(pd.to_datetime(index_day).date()),'hdd'] = True
      
        # determine during which hours of the heating days heat is required:
        df_hour.loc[ (df_hour['hdd']==True) & (df_hour['temp']<temp_base), "hdh"] = True
    
        df_hour.loc[ (df_hour['hdh']==True), 'tmp_diffT'] = df_hour.loc[ (df_hour['hdh']==True),'temp']-temp_base
    
        sum_diffT = df_hour.loc[(df_hour['hdh']==True),'tmp_diffT'].sum()
    
        df_hour.loc[ (df_hour['hdh']==True), 'd_h_hr'] = (self._d_h_s_yr/sum_diffT)*df_hour.loc[(df_hour['hdh']==True),'tmp_diffT']
                
        df_hour.loc[ (df_hour['hdh']!=True), 'd_h_hr'] = 0
    
        df_hour = df_hour.drop(['tmp_diffT'], axis=1)
    
        df_hour.reset_index(inplace=True)
        
        df_hour = df_hour.drop(['datetime'], axis=1)
        
        dhw_hr = (self._d_h_hw_yr * dhw_profile['DHW_Profile']).reset_index(drop = True)
        
        
        d_h_s = df_hour['d_h_hr'].tolist()
        d_h_hw = dhw_hr.tolist()
        
        df_hour['d_h_hr'] += dhw_hr
        
        self._d_h = np.array(df_hour['d_h_hr'])
        self._d_h_s = np.array(d_h_s)
        self._d_h_hw = np.array(d_h_hw)

        # return df_hour['d_h_hr']
        return self._d_h, self._d_h_s, self._d_h_hw
    
    
    def __compute_d_h_profile(self, n_days = 365):
        
        d_h_profile = np.array(self._d_h)/self._d_h_yr
        
        self._d_h_profile = d_h_profile[:(n_days*24)]
        
        return self._d_h_profile
    
    def compute_d_h_hr_mix(self, df_meta, tech_instances, n_days=365):
        
        src_h_elec_direct_yr = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_h_eh'].values[0] + df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_hw_eh'].values[0]
        src_h_hp_yr = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_h_hp'].values[0] + df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_hw_hp'].values[0]
        src_h_distr_yr = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_h_dh'].values[0] + df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_hw_dh'].values[0]
        src_h_gas_yr = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_h_gb'].values[0] + df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_hw_gb'].values[0]
        src_h_oil_yr = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_h_ob'].values[0] + df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_hw_ob'].values[0]
        src_h_wood_yr = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_h_wb'].values[0] + df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_hw_wb'].values[0]
        src_h_solar_yr = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_h_solar'].values[0] + df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_hw_solar'].values[0]
        src_h_other_yr = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_h_other'].values[0] + df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'v_hw_other'].values[0]
        
        heat_labels = ['electric_heater',
                       'heat_pump',
                       'district_heating',
                       'gas_boiler',
                       'oil_boiler',
                       'wood_boiler',
                       'solarthermal_rooftop',
                       'other']
        
        heat_values = [src_h_elec_direct_yr,
                       src_h_hp_yr,
                       src_h_distr_yr,
                       src_h_gas_yr,
                       src_h_oil_yr,
                       src_h_wood_yr,
                       src_h_solar_yr,
                       src_h_other_yr]
                
        self.__compute_d_h_hr_partial(tech_instances, heat_labels, heat_values, n_days)
        
    
    # def d_h_hr_partial(self, df_base, heat_labels, heat_values):
    def __compute_d_h_hr_partial(self, tech_instances, heat_labels, heat_values, n_days):
        
        """
        Computes partial hourly heat demand profile of a specific technology based
        on partial annual heat demand and total annual heat demand. This can be
        used for e.g. computing the hourly heat demand profile for a specific
        technology.
        
        Parameters
        ----------
        df_d_h_hr : pandas dataframe (1 column)
            Hourly heat demand profile [kWh].
        d_h_yr_partial : float
            Partial annual heat demand [kWh].
        d_h_yr : float
            Annual heat demand [kWh].
    
        Returns
        -------
        pandas dataframe
            Dataframe with hourly time-series of partial heat demand.
        """
        
        # d_h_profile = df_base['d_h']/df_base['d_h'].sum()
        self.__compute_d_h_profile(n_days)
        # for heating_type in zip(heat_labels, heat_values):
        #     df_base[heating_type[0]] = heating_type[1]*d_h_profile
        
        for heating_type in zip(heat_labels, heat_values):
            # print(heating_type[0])
            # print(heating_type[1])
            # if heating_type[0] == 'heat_pump':
            #     tech_inst = tech_instances['heat_pump']
            #     tech_inst.compute_cop_timeseries(self._d_h_profile)

            tech_inst = tech_instances[heating_type[0]]

            if heating_type[0] != 'solarthermal_rooftop':
                print(heating_type)
                tech_inst.compute_v_h(heating_type[1], self._d_h_profile)
                tech_inst.reduce_timeframe(n_days)
            else:
                tech_inst.compute_v_h_const_share(heating_type[1], self._d_h_profile)
                tech_inst.reduce_timeframe(n_days)

        
        # return df_base
    
    # def get_base_grid_import(
    #         m_e
    #         ):
    #     el_mix_path = paths.energy_mix_CH_dir + paths.electricity_mix_file
    #     el_mix_file = pd.read_feather(el_mix_path)
        
    #     el_gen_imp = pd.DataFrame(index = range(8760))
    #     el_gen_imp['Hydro'] = el_mix_file.iloc[:, :3].sum(axis = 1)
    #     el_gen_imp['Nuclear'] = el_mix_file.iloc[:, 3]
    #     el_gen_imp['Wind'] = el_mix_file.iloc[:, 5]
    #     el_gen_imp['Biomass'] = el_mix_file.iloc[:, 6]
    #     el_gen_imp['Other'] = el_mix_file.iloc[:, 7]
    #     el_gen_imp['Import'] = el_mix_file.iloc[:, -1]
        
    #     el_gen_imp_percentages = el_gen_imp.div(el_gen_imp.sum(axis = 1), axis = 0)
        
    #     m_e_mix = pd.DataFrame(index = range(8760))
    #     m_e_mix['m_e_ch_hydro'] = m_e * el_gen_imp_percentages['Hydro']
    #     m_e_mix['m_e_ch_nuclear'] = m_e * el_gen_imp_percentages['Nuclear']
    #     m_e_mix['m_e_ch_wind'] = m_e * el_gen_imp_percentages['Wind']
    #     m_e_mix['m_e_ch_biomass'] = m_e * el_gen_imp_percentages['Biomass']
    #     m_e_mix['m_e_ch_other'] = m_e * el_gen_imp_percentages['Other']
    #     m_e_mix['m_e_cbimport'] = m_e * el_gen_imp_percentages['Import']
        
    #     return m_e_mix
    
    def len_test(self,flow):
        if len(flow)==0:
            raise ValueError()
            
    def num_test(self,var):
        # if isinstance(var, float)==False:
        if isinstance(var, (int, float, np.integer))==False:
            raise ValueError()
            
    def get_d_e(self):
        self.len_test(self._d_e)
        return self._d_e
        
    def get_d_e_ev(self):
        self.len_test(self._d_e_ev)
        return self._d_e_ev
    
    def get_d_e_ev_cp(self):
        self.len_test(self._d_e_ev_cp)
        return self._d_e_ev_cp
    
    def get_d_e_ev_cp_dy(self):
        return self._d_e_ev_cp_dy
    
    def get_d_e_ev_pd(self):
        self.len_test(self._d_e_ev_pd)
        return self._d_e_ev_pd
    
    def get_d_e_ev_pu(self):
        self.len_test(self._d_e_ev_pu)
        return self._d_e_ev_pu
    
    def get_d_e_ev_cp_dev(self):
        self.len_test(self._d_e_ev_cp_dev)
        return self._d_e_ev_cp_dev
    
    def get_d_e_ev_cp_dev_pos(self):
        self.len_test(self._d_e_ev_cp_dev_pos)
        return self._d_e_ev_cp_dev_pos
    
    def get_d_e_ev_cp_dev_neg(self):
        self.len_test(self._d_e_ev_cp_dev_neg)
        return self._d_e_ev_cp_dev_neg
    
    def get_f_e_ev_pot_dy(self):
        # self.len_test(self._f_e_ev_pot_dy)
        return self._f_e_ev_pot_dy
    
    def get_f_e_ev_dy(self):
        return self._f_e_ev_dy
    
    def get_d_e_hh(self):
        self.len_test(self._d_e_hh)
        return self._d_e_hh
    
    def get_d_e_h(self):
        self.len_test(self._d_e_h)
        return self._d_e_h
    
    def get_d_h(self):
        self.len_test(self._d_h)
        return self._d_h
    
    def get_d_h_s(self):
        self.len_test(self._d_h_s)
        return self._d_h_s
    
    def get_d_h_hw(self):
        self.len_test(self._d_h_hw)
        return self._d_h_hw

    def get_d_e_yr(self):
        self.num_test(self._d_e_yr)
        return self._d_e_yr
    
    def get_d_e_ev_yr(self):
        self.num_test(self._d_e_ev_yr)
        return self._d_e_ev_yr
    
    def get_d_e_hh_yr(self):
        self.num_test(self._d_e_hh_yr)
        return self._d_e_hh_yr
    
    def get_d_e_h_yr(self):
        self.num_test(self._d_e_h_yr)
        return self._d_e_h_yr
    
    def get_d_h_yr(self):
        self.num_test(self._d_h_yr)
        return self._d_h_yr
    
    def get_d_h_s_yr(self):
        self.num_test(self._d_h_s_yr)
        return self._d_h_s_yr
    
    def get_d_h_hw_yr(self):
        self.num_test(self._d_h_hw_yr)
        return self._d_h_hw_yr
    
    def get_d_e_unmet(self):
        self.len_test(self._d_e_unmet)
        return self._d_e_unmet
    
    def get_d_h_unmet(self):
        self.len_test(self._d_h_unmet)
        return self._d_h_unmet
    
    def get_d_h_unmet_dhn(self):
        self.len_test(self._d_h_unmet_dhn)
        return self._d_h_unmet_dhn









