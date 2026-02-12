# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 09:23:05 2024

@author: UeliSchilt
"""

import numpy as np
import pandas as pd
import os
import numbers

from district_energy_model.techs.dem_tech_core import TechCore

# How to handle different paths? --> this module is not only called from
# src dir, but also from tests dir


# import dem_helper


class WindPower(TechCore):
    
    """
    Conversion technology: wind power.
    """
    
    # def __init__(self, df_wp_profiles_annual, df_wp_profiles_winter, tech_dict):
    def __init__(
            self,
            wind_power_data_dir,
            wind_power_profiles_dir,
            wind_power_cap_file,
            wind_power_profile_file_annual,
            wind_power_profile_file_winter,
            wind_power_national_profile_file,
            com_name,
            com_percent,
            tech_dict
            ):
        """
        Initialise technology parameters.
        
        Parameters
        ----------
        
        df_wp_profiles_annual : pandas dataframe
            Wind power potential (installed + additional potential) using
            'annual' profile (balanced across the year).
        df_wp_profiles_winter : pandas dataframe
            wind power potential (installed + additional potential) using
            'winter' profile (geared towards winter production).
        tech_dict : dict
            Dictionary with technology parameters (subset of scen_techs).
    
        Returns
        -------
        n/a
        """
        
        super().__init__(tech_dict)
        
        self.tech_dict = tech_dict
        
        # Paths:
        self.wind_power_data_dir = wind_power_data_dir
        self.wind_power_profiles_dir = wind_power_profiles_dir
        self.wind_power_cap_file = wind_power_cap_file
        self.wind_power_profile_file_annual = wind_power_profile_file_annual
        self.wind_power_profile_file_winter = wind_power_profile_file_winter
        self.wind_power_national_profile_file = wind_power_national_profile_file
        
        self.com_name = com_name
        self.com_percent = com_percent
 
        # All properties:
        self.p_max = ...
        self.p_max_annual = ...
        self.p_max_winter = ...
        self.p_e_wp = ... # currently installed capacity
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Preprocess wind resource data:
        self.data_preprocessing(tech_dict)
        
        # Carrier types:
        self.output_carrier = 'electricity'
        
        # Accounting:
        self._v_e = []
        self._v_e_ch = []
        self._v_e_cons = []
        self._v_e_exp = []
        self._v_e_pot = []
        self._v_e_pot_remain = []
        self._v_e_pot_annual = [] # [kWh] Total wind power potential (installed + additional potential) using 'annual' profile (balanced across the year)
        self._v_e_pot_annual_kWhpkW = [] # [kWh/kW]
        self._v_e_pot_winter = [] # [kWh] Total wind power potential (installed + additional potential) using 'winter' profile (geared towards winter production)
        self._v_e_pot_winter_kWhpkW = [] # [kWh/kW]
        
        '''
        - max capacity [GW]
        - v_e_wp
        - specific percentage of potential --> for scenario
        '''
     
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the wind power technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        # Properties:
        self._kWp_max = tech_dict['kWp_max']
        self._kWp_max_systemwide = tech_dict['kWp_max_systemwide']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._capex = tech_dict['capex_CHFpkWp']
        self._installed_allocation = tech_dict['wind_power_installed_allocation']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._export_subsidy = tech_dict['export_subsidy']

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['v_e_wp'] = self.get_v_e()
        df['v_e_wp_ch'] = self.get_v_e_ch()
        df['v_e_wp_cons'] = self.get_v_e_cons()
        df['v_e_wp_exp'] = self.get_v_e_exp()
        df['v_e_wp_pot'] = self.get_v_e_pot()
        df['v_e_wp_pot_remain'] = self.get_v_e_pot_remain()
        df['v_e_wp_pot_annual'] = self.get_v_e_pot_annual()
        df['v_e_wp_pot_annual_kWhpkW'] = self.get_v_e_pot_annual_kWhpkW()
        df['v_e_wp_pot_winter'] = self.get_v_e_pot_winter()
        df['v_e_wp_pot_winter_kWhpkW'] = self.get_v_e_pot_winter_kWhpkW()
        
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
        
        self._v_e = self._v_e[:n_hours]
        self._v_e_ch = self._v_e_ch[:n_hours]
        self._v_e_cons = self._v_e_cons[:n_hours]
        self._v_e_exp = self._v_e_exp[:n_hours]
        self._v_e_pot = self._v_e_pot[:n_hours]
        self._v_e_pot_remain = self._v_e_pot_remain[:n_hours]
        self._v_e_pot_annual = self._v_e_pot_annual[:n_hours]
        self._v_e_pot_annual_kWhpkW = self._v_e_pot_annual_kWhpkW[:n_hours]
        self._v_e_pot_winter = self._v_e_pot_winter[:n_hours]
        self._v_e_pot_winter_kWhpkW = self._v_e_pot_winter_kWhpkW[:n_hours]
    
    def data_preprocessing(self, tech_dict):
        # Preprocess wind power data:
            
        # Installed capacity per munic [kW]:
        wp_path_p = (self.wind_power_data_dir + self.wind_power_cap_file)
        
        # df_p_e_wp = pd.read_csv(wp_path_p)
        df_p_e_wp = pd.read_feather(wp_path_p)
        
        self.p_e_wp = float(
                df_p_e_wp.loc[df_p_e_wp['Municipality']==self.com_name,'p_kW'].iloc[0]
                )
        
        # ---------------------------------------------------------------------
        # TEMPORARY FIX for municipalities where there is currently Wind Power installed, but no potential acc. to Wind-Topo:
        issue_munics = [
            'Goldach',
            'Schmiedrued',
            # 'Martigny',
            'Wyssachen'
            ]
        replacements = {
            'Goldach':'Romanshorn',
            'Schmiedrued':'Rickenbach (LU)',
            'Martigny':'Dorénaz',
            'Wyssachen':'Dürrenroth'
            }
        if self.com_name in issue_munics:
            
            repl_munic = replacements[self.com_name]
            
            # Issue a warning
            import warnings
            warnings.warn(
                "TEMPORARY FIX: The wind potential for "
                f"{self.com_name} is not available. Therefore, the "
                "wind resource files have been modified, using "
                f"the generation profiles of the nearby municipality "
                f"of {repl_munic} instead.", UserWarning
                )
            
            # self.wind_power_profile_file_annual = f"{repl_munic}.csv"
            # self.wind_power_profile_file_winter = f"{repl_munic}_winter.csv"
            self.wind_power_profile_file_annual = f"{repl_munic}.feather"
            self.wind_power_profile_file_winter = f"{repl_munic}_winter.feather"
        # ---------------------------------------------------------------------
        
        # Wind power profiles:
        wp_path_annual = (self.wind_power_profiles_dir
                              + self.wind_power_profile_file_annual)
        wp_path_winter = (self.wind_power_profiles_dir
                              + self.wind_power_profile_file_winter)
        # Hourly profiles:
        # self.df_profiles_annual = self.__csv_to_df_profiles(wp_path_annual)
        # self.df_profiles_winter = self.__csv_to_df_profiles(wp_path_winter)
        
        self.df_profiles_annual = self.__feather_to_df_profiles(wp_path_annual)
        self.df_profiles_winter = self.__feather_to_df_profiles(wp_path_winter)
        
        # ---------------------------------------------------------------------
        # TENORARY FIX (continued)
        if self.com_name in issue_munics:
            for i in range(4):
                self.df_profiles_annual[i][0] = 0.0
            self.df_profiles_annual[4][0] = self.p_e_wp*1000
            for i in range(5):
                self.df_profiles_winter[i][0] = 0.0
        # ---------------------------------------------------------------------
        
        # Get the number of bins in the profiles datasets (i.e. number of columns):
        self.n_bins_annual = self.df_profiles_annual.shape[1]
        self.n_bins_winter = self.df_profiles_winter.shape[1]
        
        if tech_dict['v_e_wp_national_recalc']:
            
            self.recalc_v_e_base_national(
                df_p_e_wp=df_p_e_wp,
                wind_power_profiles_dir=self.wind_power_profiles_dir,
                wind_power_data_dir=self.wind_power_data_dir,
                wind_power_national_profile_file=self.wind_power_national_profile_file
                )
            
    def __feather_to_df_profiles(self, file_path):
        """
        Read wind power data from feather file and convert to dataframe.
        The input file format is the same as for the CSV version:
            - Each column represents a bin for a specific installation capacity
            - Row 0: Percentage values (will be ignored)
            - Row 1: Installation capacity [W] for specific bin
            - Row 2 and following: Capacity factor for each hour [-]
        """
    
        import os
        import pandas as pd
    
        if not os.path.isfile(file_path):
            raise Exception("No wind power data found. Check for file or correct file name.")
    
        # Read feather file (contains same content as CSV)
        df_raw = pd.read_feather(file_path)
    
        # If the file has a single string column (space-delimited), split it into separate columns
        if df_raw.shape[1] == 1:
            df_profiles = df_raw.iloc[:, 0].str.split(" ", expand=True)
            df_profiles = df_profiles.apply(pd.to_numeric, errors="coerce")
        else:
            df_profiles = df_raw.copy()
    
        # Check if there is only one row and it is full of zeroes
        if len(df_profiles) == 1 and (df_profiles.iloc[0] == 0).all():
            additional_rows = pd.DataFrame(0, index=range(8760), columns=df_profiles.columns)
            df_profiles = pd.concat([df_profiles, additional_rows])
            df_profiles.reset_index(inplace=True, drop=True)
    
        # If profile contains leap year (i.e. 8784h), remove last 24h
        if len(df_profiles) == 8785:
            df_profiles = df_profiles.iloc[:-24]
    
        # Replace NaN values with zeroes
        df_profiles.fillna(0, inplace=True)
    
        return df_profiles

    
    # @staticmethod
    def __csv_to_df_profiles(self, file_path):
        """
        Read wind power data from csv and convert to dataframe. The input file
        format is as follows:
            - Each column represents a bin for a specific installation capacity
            - Row 0: Percentage values (will be ignored).
            - Row 1: Installation capacity [W] for specific bin.
            - Row 2 and following: Capacity factor for each hour [-].

        Parameters
        ----------
        file_path : str
            Path to csv file.

        Returns
        -------
        df_profiles : pandas dataframe
            Processed dataframe with wind power profiles data.
            Format:
            - Each column represents a bin for a specific installation capacity
            - Row 0: Installation capacity [W] for specific bin.
            - Row 1 and following: Capacity factor for each hour [-].

        """
        
        file_exist = os.path.isfile(file_path)
        
        if file_exist == False:
            raise Exception("No wind power data found. Check for file or "
                            "correct file name.")
        
        # Read files:
        df_profiles = pd.read_csv(
            file_path,
            skiprows=1,
            delimiter=" ",
            header=None
            )
        
        # Check if there is only one row and it is full of zeroes (i.e. no wind power potential):
        if len(df_profiles) == 1 and (df_profiles.iloc[0] == 0).all():
            # Add 8760 rows of zeroes
            additional_rows = pd.DataFrame(0, index=range(8760), columns=df_profiles.columns)
            df_profiles = pd.concat([df_profiles, additional_rows])
            df_profiles.reset_index(inplace=True, drop=True)
        
        # If profile contains leap year (i.e. 8784h), remove last 24h:
        if len(df_profiles) == 8785:
            df_profiles = df_profiles.iloc[:-24]
        
        # replace 'NaN' values with zeroes:
        df_profiles.fillna(0,inplace=True)
        
        
        return df_profiles
        
        
    
    # NOT USED ANYMORE -- DELETE?    
    # def get_v_e(self, pot_perc, profile='annual'): # IS THIS USED ANYWHERE?
    #     """
    #     Generate hourly wind power profile [kWh] based on selected percentage
    #     of total wind power potential.

    #     Parameters
    #     ----------
    #     pot_perc : float
    #         Selected percentage of wind power potential (e.g. 41.0).
    #     profile : str, optional
    #         Options: 'annual', 'winter'. The default is 'annual'.

    #     Raises
    #     ------
    #     Exception
    #         If profile type is invalid. Must be either 'annual' or 'winter'.

    #     Returns
    #     -------
    #     df_v_e : dataframe column
    #         Hourly profile of wind power (acc. to selected percentage) [kWh].

    #     """
        
    #     # Select which set of profiles to use:
    #     if profile=='annual':
    #         df_profiles = self.df_profiles_annual
    #     elif profile=='winter':
    #         df_profiles = self.df_profiles_winter
    #     else:
    #         raise Exception('Selected profile type invalid. '
    #                         'Choose either \'annual\' or \'winter\' as '
    #                         'profile type.')
        
    #     # Get actual percentages of bins:
    #     cap_perc_bins = self.__get_actual_cap_perc_bins(df_profiles)
        
    #     # Number of profiles:
    #     n = len(cap_perc_bins)
        
    #     # Get the actual capacity based on the selected percentage:
    #     # selected_bin = None
    #     bin_i = None
    #     # Iterate through the list of bin percentages:
    #     for i, bin_perc in enumerate(cap_perc_bins):
    #         # Check if the current bin percentage is larger or equal to the selected fraction:
    #         if bin_perc*100 >= pot_perc:
    #             # selected_bin = bin_perc
    #             bin_i = i
    #             break
            
    #     # Compute the respective capacity [kW]:
    #     p = pot_perc/100.0*df_profiles.iloc[0,n-1]/1000.0
        
    #     # Generate the hourly profile [kWh]:
    #     cap_factors_hourly = df_profiles.iloc[1:,bin_i]
    #     df_v_e = cap_factors_hourly*p       
        
    #     # Reset the index:
    #     df_v_e.reset_index(inplace=True, drop=True)
        
    #     return df_v_e
    
    
    # @staticmethod
    # def get_v_e_from_p(self, profile='total'):
    def compute_v_e(self, profile='total'):
        """
        Generate hourly wind power profile [kWh] based on selected wind power
        capacity p_e_wp.

        Parameters
        ----------
        p_e_wp : float
            Wind power capacity [kW].
        profile : str, optional
            Options: 'annual', 'winter', 'total'. The default is 'total'.

        Raises
        ------
        Exception
            If profile type is invalid. Must be either 'annual', 'winter', or 
            'total'.

        Returns
        -------
        df_v_e : dataframe column
            Hourly profile of wind power (acc. to selected capacity) [kWh].

        """
        
        # ---------------------------------------------------------------------
        # Helper function
        def get_v_e_(arg_p, arg_df_profiles):
        
            # Get capacity of bins:
            cap_bins = self.__get_bin_cap_kW(arg_df_profiles)
            # print(cap_bins)
            # print(arg_p)
            bin_i = None
            # Iterate through the list of bin capacities:
            for i, bin_cap in enumerate(cap_bins):
                # Check if the current bin capacity is larger or equal to the installed capacity p_e_wp:
                if bin_cap >= arg_p:
                    bin_i = i
                    break
            
                
                
                
            # if bin_i == None:
            #     bin_i = 0
            
            # Generate the hourly profile [kWh] using the selected bin:
            # print("==================/////////////////////")
            # print(bin_i)
            # print(arg_df_profiles)
            cap_factors_hourly = arg_df_profiles.iloc[1:,bin_i]
            ret_df_v_e = cap_factors_hourly*arg_p   
        
            # Reset the index:
            ret_df_v_e.reset_index(inplace=True, drop=True)

            return ret_df_v_e
        # ---------------------------------------------------------------------
        
        if len(self.com_percent) == 0:
            
            # Profiles:
            df_profiles_a = self.df_profiles_annual
            df_profiles_w = self.df_profiles_winter 
                
            if profile == 'total':
                # Start by using 'annual' profile. If p_e_wp is larger than the
                # potential capacity in the 'annual' profile, capacity from the
                # 'winter' profile is added.
                
                # Get capacity of 'annual' bins:
                cap_bins_a = self.__get_bin_cap_kW(df_profiles_a)
                
                if self.p_e_wp <= max(cap_bins_a):
                    df_v_e = get_v_e_(self.p_e_wp, df_profiles_a)
                else:
                    p_a = max(cap_bins_a) # [kW] capacity used for annual profile
                    p_w = self.p_e_wp - p_a
                    
                    df_v_e_a = get_v_e_(p_a, df_profiles_a)
                    df_v_e_w = get_v_e_(p_w, df_profiles_w)
                    
                    df_v_e = df_v_e_a + df_v_e_w
            
            elif profile == 'annual':
                df_v_e = get_v_e_(self.p_e_wp, df_profiles_a)
            
            elif profile == 'winter':
                df_v_e = get_v_e_(self.p_e_wp, df_profiles_w)
    
            else:
                raise Exception('Selected profile type invalid. '
                                'Choose either \'annual\', \'winter\', or '
                                '\'total\' as profile type.')
            
            # Allocate installed wind power to either national or local generation:
            if self.__tech_dict['wind_power_installed_allocation'] == 'national':
                df_v_e_ch = df_v_e.copy()
                df_v_e = pd.Series(0, index=df_v_e_ch.index)
                # df_base['v_e_wp_ch'] = df_base['v_e_wp'].copy()
                # df_base['v_e_wp'] = 0
            elif self.__tech_dict['wind_power_installed_allocation'] == 'local':
                df_v_e_ch = df_v_e.copy()
                df_v_e_ch = pd.Series(0, index=df_v_e.index)
                # df_base['v_e_wp_ch'] = 0
            else:
                raise ValueError('Incorrect allocation of installed wind power. '
                                  'Must either be \'national\' or \'local\'.')
                
            self._v_e = np.array(df_v_e)
            self._v_e_ch = np.array(df_v_e_ch)
                        
                
            return df_v_e
        else:
            for i in range(len(self.com_percent)):
                self.com_name = self.com_percent.index[i]
                # self.wind_power_profile_file_annual = f"{self.com_name}.csv" # csv-file containing generation profiles of wind power
                # self.wind_power_profile_file_winter = f"{self.com_name}_winter.csv"
                self.wind_power_profile_file_annual = f"{self.com_name}.feather" # feather-file containing generation profiles of wind power
                self.wind_power_profile_file_winter = f"{self.com_name}_winter.feather"
                self.data_preprocessing(self.tech_dict)
                
                # Profiles:
                df_profiles_a = self.df_profiles_annual
                df_profiles_w = self.df_profiles_winter   
                    
                if profile == 'total':
                    # Start by using 'annual' profile. If p_e_wp is larger than the
                    # potential capacity in the 'annual' profile, capacity from the
                    # 'winter' profile is added.
                    
                    # Get capacity of 'annual' bins:
                    cap_bins_a = self.__get_bin_cap_kW(df_profiles_a)
                    
                    if self.p_e_wp <= max(cap_bins_a):
                        df_v_e = get_v_e_(self.p_e_wp, df_profiles_a)
                    else:
                        p_a = max(cap_bins_a) # [kW] capacity used for annual profile
                        p_w = self.p_e_wp - p_a
                        
                        df_v_e_a = get_v_e_(p_a, df_profiles_a)
                        df_v_e_w = get_v_e_(p_w, df_profiles_w)
                        
                        df_v_e = df_v_e_a + df_v_e_w
                
                elif profile == 'annual':
                    df_v_e = get_v_e_(self.p_e_wp, df_profiles_a)
                
                elif profile == 'winter':
                    df_v_e = get_v_e_(self.p_e_wp, df_profiles_w)
        
                else:
                    raise Exception('Selected profile type invalid. '
                                    'Choose either \'annual\', \'winter\', or '
                                    '\'total\' as profile type.')
                
                # Allocate installed wind power to either national or local generation:
                if self.__tech_dict['wind_power_installed_allocation'] == 'national':
                    df_v_e_ch = df_v_e.copy()
                    df_v_e = pd.Series(0, index=df_v_e_ch.index)
                    # df_base['v_e_wp_ch'] = df_base['v_e_wp'].copy()
                    # df_base['v_e_wp'] = 0
                elif self.__tech_dict['wind_power_installed_allocation'] == 'local':
                    df_v_e_ch = df_v_e.copy()
                    df_v_e_ch = pd.Series(0, index=df_v_e.index)
                    # df_base['v_e_wp_ch'] = 0
                else:
                    raise ValueError('Incorrect allocation of installed wind power. '
                                      'Must either be \'national\' or \'local\'.')
                
                if i == 0:
                    self._v_e = np.array(df_v_e)*self.com_percent.iloc[i]
                    self._v_e_ch = np.array(df_v_e_ch)*self.com_percent.iloc[i]
                    
                    df_profiles_a_tot = df_profiles_a*self.com_percent.iloc[i]
                    df_profiles_w_tot = df_profiles_w*self.com_percent.iloc[i]
                else:
                    self._v_e += np.array(df_v_e)*self.com_percent.iloc[i]
                    self._v_e_ch += np.array(df_v_e_ch)*self.com_percent.iloc[i]
                    
                    df_profiles_a_tot += df_profiles_a*self.com_percent.iloc[i]
                    df_profiles_w_tot += df_profiles_w*self.com_percent.iloc[i]
            
            self.df_profiles_annual = df_profiles_a_tot
            self.df_profiles_winter = df_profiles_w_tot
                        
            return df_v_e
                
    

    # def get_v_e_pot_max_(self, v_e_wp, align_with_installed='False'):
    #     """
    #     Return the hourly profile of the full wind power potential (i.e. 100%)
    #     The profile type is the sum of 'annual' and 'winter'.
        
    #     Parameters
    #     ----------
    #     v_e_wp : dataseries
    #         Dataseries with hourly electricity output (kWh) of installed wind
    #         power. Only used if align_with_installed=True.
    #     align_with_installed_kWh : bool, optional
    #         If set to True, the hourly max. potential (v_e_wp_pot) will be
    #         aligned with the currently installed capactiy. This means that
    #         during hours, where the currently installed yield is higher than
    #         the max. determined potential, the potential will be set to the
    #         installed yield to avoid negative values in v_e_wp_pot_remain.
    #         The default is 'False'.

    #     Returns
    #     -------
    #     df_v_e: dataseries
    #         Hourly wind power profile [kWh]/[kW].
    #     p_max : float
    #         Wind power capacity [kW] that was used to generate hourly profile
    #         (at 100% installation rate).

    #     """
        
    #     df_v_e_annual, p_max_annual = self.__get_v_e_pot_annual()
    #     df_v_e_winter, p_max_winter = self.__get_v_e_pot_winter()
    
    
    # def get_v_e_pot_max(self, v_e_wp, align_with_installed='False'):        
    #     """
    #     Return the hourly profile of the full wind power potential (i.e. 100%)
    #     The profile type (annual vs winter) with the larger total generation
    #     will be chosen.
        
    #     Parameters
    #     ----------
    #     v_e_wp : dataseries
    #         Dataseries with hourly electricity output (kWh) of installed wind
    #         power. Only used if align_with_installed=True.
    #     align_with_installed_kWh : bool, optional
    #         If set to True, the hourly max. potential (v_e_wp_pot) will be
    #         aligned with the currently installed capactiy. This means that
    #         during hours, where the currently installed yield is higher than
    #         the max. determined potential, the potential will be set to the
    #         installed yield to avoid negative values in v_e_wp_pot_remain.
    #         The default is 'False'.

    #     Returns
    #     -------
    #     df_v_e: dataseries
    #         Hourly wind power profile [kWh]/[kW].
    #     p_max : float
    #         Wind power capacity [kW] that was used to generate hourly profile
    #         (at 100% installation rate).

    #     """
        
    #     df_v_e_annual, p_max_annual = self.__get_v_e_pot_annual()
    #     df_v_e_winter, p_max_winter = self.__get_v_e_pot_winter()
        
    #     v_e_yr_annual = df_v_e_annual.sum()
    #     v_e_yr_winter = df_v_e_winter.sum()
        
    #     if v_e_yr_annual >= v_e_yr_winter:
    #         # print("  ------------- wind power: annual profile used.")
    #         df_v_e = df_v_e_annual
    #         p_max = p_max_annual
    #     else:
    #         # print("  ------------- wind power: winter profile used.")
    #         df_v_e = df_v_e_winter
    #         p_max = p_max_winter
            
    #     # Align with currently installed wind power output (if selected):
    #     if align_with_installed:
    #         # Change the values in df_v_e if they are smaller than v_e_wp
    #         df_v_e[df_v_e < v_e_wp] = v_e_wp[df_v_e < v_e_wp]
            
    #     return df_v_e, p_max
    
    
    # def get_v_e_pot(self, v_e_wp, profile, align_with_installed='False'):
    #     """
    #     Return the hourly profile of the full wind power potential (i.e. 100%)
    #     The profile type (annual vs winter) must be selected.
        
    #     Parameters
    #     ----------
    #     v_e_wp : dataseries
    #         Dataseries with hourly electricity output (kWh) of installed wind
    #         power. Only used if align_with_installed=True.
    #     profile : str
    #         Defines the profile type (annual balanced production vs winter
    #         production). Options: 'annual', 'winter', 'total'.
    #     align_with_installed_kWh : bool, optional
    #         If set to True, the hourly max. potential (v_e_wp_pot) will be
    #         aligned with the currently installed capactiy. This means that
    #         during hours, where the currently installed yield is higher than
    #         the max. determined potential, the potential will be set to the
    #         installed yield to avoid negative values in v_e_wp_pot_remain.
    #         The default is 'False'.

    #     Returns
    #     -------
    #     df_v_e: dataseries
    #         Hourly wind power profile [kWh]/[kW].
    #     p_max : float
    #         Wind power capacity [kW] that was used to generate hourly profile
    #         (at 100% installation rate).

    #     """

    #     if profile == 'annual':
    #         df_v_e, p_max = self.__get_v_e_pot_annual()
    #     elif profile == 'winter':
    #         df_v_e, p_max = self.__get_v_e_pot_winter()
    #     elif profile == 'total':
    #         df_v_e_ann, p_max_ann = self.__get_v_e_pot_annual()
    #         df_v_e_win, p_max_win = self.__get_v_e_pot_winter()
    #         df_v_e = df_v_e_ann + df_v_e_win
    #         p_max = p_max_win + p_max_ann
            
    #     # Align with currently installed wind power output (if selected):
    #     if align_with_installed:
    #         # Change the values in df_v_e if they are smaller than v_e_wp
    #         df_v_e[df_v_e < v_e_wp] = v_e_wp[df_v_e < v_e_wp]
            
    #     # Generate power specific potential [kWh/kW]:
    #     df_v_e_kWhpkW = df_v_e/p_max
    #     df_v_e_kWhpkW.fillna(0, inplace=True) # in case p_max = 0
            
    #     return df_v_e, df_v_e_kWhpkW, p_max
    
    # @staticmethod
    def recalc_v_e_base_national(
            self,
            df_p_e_wp,
            wind_power_profiles_dir,
            wind_power_data_dir,
            wind_power_national_profile_file
            ):
        """
        Calculate the hourly wind power generation profile and save to file.
        """
        
        # Get national wind power capacity:
        # p_e_wp_base_national = df_p_e_wp['p_kW'].sum()

        # Remove municipalities where no wind power is installed:
        df_p_e_wp_red = df_p_e_wp[df_p_e_wp['p_kW'] != 0.0].copy()
        
        # Initialise hourly national wind power profile:
        df_v_e_base_national = pd.DataFrame({'v_e_wp': [0.0] * 8760})
        
        # Initialise hourly wind power profile for municipalites:
        df_v_e_base_munic = pd.DataFrame({'v_e_wp': [0.0] * 8760})
        
        # Iterate through municipalities:
        for munic in df_p_e_wp_red['Municipality']:
            
            # Generate profile for municipality:
            p_e_wp_munic = float(
                df_p_e_wp_red.loc[df_p_e_wp_red['Municipality']==munic,'p_kW']
                )
            
            # wind_power_profile_file_annual = f"{munic}.csv" # csv-file containing generation profiles of wind power
            # wind_power_profile_file_winter = f"{munic}_winter.csv" # csv-file containing generation profiles of wind power, with profiles favored for winter-production
            
            wind_power_profile_file_annual = f"{munic}.feather" # feather-file containing generation profiles of wind power
            wind_power_profile_file_winter = f"{munic}_winter.feather" # feather-file containing generation profiles of wind power, with profiles favored for winter-production
            
            # Wind power profiles:
            wp_path_annual = (wind_power_profiles_dir
                              + wind_power_profile_file_annual)
            wp_path_winter = (wind_power_profiles_dir
                              + wind_power_profile_file_winter)
            
            # # =====================================================================
            # # TEMPORARY ROUTINE THAT USES STANDARD FILES WHICH ONLY CONTAIN DUMMY-VALUES IF OTHER FILES ARE NOT FOUND
            # # ---------------------------------------------------------------------
            # file_annual_exist = os.path.isfile(wp_path_annual)
            # file_winter_exist = os.path.isfile(wp_path_winter)

            # if file_annual_exist == False or file_winter_exist == False:
            #     print("\n********************************************************")
            #     print("In recalc_v_e_base_national(...):")
            #     print(f"WARNING: NO WIND POWER DATA FOUND FOR {munic}")
            #     print("\nTEMPORARY FIX: WIND POWER PROFILE FILES DON'T EXIST FOR "
            #           "THIS MUNICIPALITY. FILES WITH LARGE DUMMY-VALUES ARE USED "
            #           "INSTEAD. RESULTS ARE NOT REPRESENTATIVE!")
            #     print("\n********************************************************")
            #     wp_path_annual = (wind_power_profiles_dir
            #                       + '0_PLACEHOLDER_NULL.csv')
            #     wp_path_winter = (wind_power_profiles_dir
            #                       + '0_PLACEHOLDER_NULL_winter.csv')
            # # =====================================================================
            
            # Hourly profiles (capacity factors):
            df_profiles_annual = self.__feather_to_df_profiles(
                wp_path_annual
                )
            df_profiles_winter = self.__feather_to_df_profiles(
                wp_path_winter
                )
            # df_profiles_annual = self.__csv_to_df_profiles(
            #     wp_path_annual
            #     )
            # df_profiles_winter = self.__csv_to_df_profiles(
            #     wp_path_winter
            #     )
                
            df_v_e_base_munic['v_e_wp'] = WindPower(
                df_profiles_annual,
                df_profiles_winter
                ).get_v_e_from_p(
                    p_e_wp=p_e_wp_munic,
                    profile='total'
                    )
            
            # Add profile to national profile:
            df_v_e_base_national['v_e_wp'] += df_v_e_base_munic['v_e_wp']

        del df_v_e_base_munic
        
        # Write profile to csv file:
        path = wind_power_data_dir + wind_power_national_profile_file
        df_v_e_base_national.to_csv(path)
        

    
    # @staticmethod
    # def get_v_e_base_munic(df_meta):
    #     """
    #     Generate hourly wind power profile for municipality as a fraction from
    #     the national profile. Aussumption of wind power consumption on national
    #     level, with allocation to each municipality.
    #     """
    #     ...
        
    # @staticmethod
    # def get_m_e_ch_wp(df_meta):
    #     """
    #     Generate hourly wind power profile for municipality as a national
    #     import (i.e. a fraction from the national profile). Aussumption of wind
    #     power consumption on national level, with allocation to each
    #     municipality.
    #     """
    #     ...
        
        
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['wind_power_parent'] = {
                'essentials':{
                    'parent':'supply_plus',
                    'carrier':'wp_electricity'
                    },
                'constraints':{
                    'export_carrier': 'wp_electricity',
                    'resource_unit':'energy_per_cap',  # [kWh/kW]
                    'force_resource': True,
                    'lifetime': self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'interest_rate':self._interest_rate,
                        'om_con':0.0
                        },
                    }
                }
        
        return tech_groups_dict
    
    
    def create_techs_dict(self,
                          techs_dict,
                          header,
                          name, 
                          color, 
                          # energy_cap,
                          export_cost,
                          capex_0=False,
                          energy_scaling_factor = 1.0
                          ):
        
        if capex_0==False:
            capex = self._capex
        elif capex_0==True:
            capex = 0
        
        techs_dict[header] = {
            'essentials':{
                'name':name,
                'color':color,
                'parent':'wind_power_parent'
                },
            'constraints':{
                # 'energy_cap_max': energy_cap
                },
            'costs':{
                'monetary':{
                    'energy_cap':capex * energy_scaling_factor,
                    'om_annual': self._maintenance_cost * energy_scaling_factor,
                    'export':export_cost-self._export_subsidy * energy_scaling_factor
                    }
                }
            }
        
        return techs_dict
    
    
    def create_techs_dict_unit(
            self,
            techs_dict,
            # header,
            # name, 
            color, 
            energy_scaling_factor
            # resource,
            # energy_cap,
            # energy_cap_max_systemwide,
            # capex
            ):
        
        techs_dict['wind_power_unit'] = {
            'essentials':{
                'name':'Wind Power Unit',
                'color':color,
                'parent':'conversion',
                'carrier_in':'wp_electricity',
                'carrier_out':'electricity'
                },
            'constraints':{
                'units_max': 1,
                'units_max_systemwide': 2,
                'energy_cap_max_systemwide': self._kWp_max_systemwide / energy_scaling_factor if self._kWp_max_systemwide != 'inf' else 'inf',
                # 'energy_cap_per_unit': tmp_cap_max, # was added in loc_dict()
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
                }
            }
        
        return techs_dict
        
        
    # def create_techs_dict(techs_dict,
    #                       header,
    #                       name, 
    #                       color, 
    #                       resource,
    #                       energy_cap,
    #                       capex
    #                       ):
        
    #     techs_dict[header] = {
    #         'essentials':{
    #             'name': name,
    #             'color': color,
    #             'parent': 'solar_pv'
    #             },
    #         'constraints':{
    #             'resource': resource,
    #             'energy_cap_max': energy_cap
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'energy_cap': capex
    #                 }
    #             }
    #         }    
        
    #     return techs_dict
    
    # def get_v_e_pot_tot(self):
    def compute_v_e_pot(self):
        
        self.__compute_v_e_pot_annual()
        self.__compute_v_e_pot_winter()
        
        len1 = len(self._v_e_pot_annual)
        len2 = len(self._v_e_pot_winter)
        
        cond1 = len1==0
        cond2 = len2==0
        
        if any([cond1,cond2]):
            raise ValueError(
                "Wind power potentials must be computed first!"
                f"\n v_e_pot_annual len: {len1}"
                f"\n v_e_pot_winter len: {len2}"
                )
        
        else:
            v_e_pot = (
                self._v_e_pot_annual
                + self._v_e_pot_winter
                )
            
            self.p_max = self.p_max_annual + self.p_max_winter
            
            # Aling with installed:
                
            df_dict = {
                'v_e_pot':v_e_pot,
                'v_e':self._v_e + self._v_e_ch              
                }
            df = pd.DataFrame(df_dict)
            
            df.loc[df['v_e_pot']<df['v_e'], 'v_e_pot'] = df['v_e']
            
            self._v_e_pot = np.array(df['v_e_pot'])
            
            self.__compute_v_e_pot_remain()

    # def get_v_e_pot_annual(self):
    def __compute_v_e_pot_annual(self):
        """
        Return the hourly profile of the full wind power potential (i.e. 100%)
        for the annual profile.

        Returns
        -------
        df_v_e : dataseries
            Hourly wind power profile [kWh]/[kW].

        """
        
        df_profiles = self.df_profiles_annual
                
        # Extract 100% capacity value:
        p_max = self.__get_p_max_kW(df_profiles)
                
        # Extract capacity factors profile for 100% capacity:
        cap_factors_hourly = df_profiles.iloc[1:,-1]
        
        # Reset the index:
        cap_factors_hourly.reset_index(inplace=True, drop=True)

        # Extract power profile:
        df_v_e = cap_factors_hourly*p_max
        # print("__get_v_e_pot_annual()")
        
        # Generate power specific potential [kWh/kW]:
        df_v_e_kWhpkW = df_v_e/p_max
        df_v_e_kWhpkW.fillna(0, inplace=True) # in case p_max = 0
        
        self._v_e_pot_annual = np.array(df_v_e)
        self._v_e_pot_annual_kWhpkW = np.array(df_v_e_kWhpkW)
        self.p_max_annual = p_max

        # return df_v_e, p_max        
        
    # def get_v_e_pot_winter(self):
    def __compute_v_e_pot_winter(self):
        """
        Return the hourly profile of the full wind power potential (i.e. 100%)
        for the winter profile.

        Returns
        -------
        df_v_e : dataseries
            Hourly wind power profile [kWh]/[kW].

        """
        
        df_profiles = self.df_profiles_winter
        
        # Extract 100% capacity value:
        p_max = self.__get_p_max_kW(df_profiles)
        
        # Extract capacity factors profile for 100% capacity:
        cap_factors_hourly = df_profiles.iloc[1:,-1]
        
        # Reset the index:
        cap_factors_hourly.reset_index(inplace=True, drop=True)
        
        # Extract power profile:
        df_v_e = cap_factors_hourly*p_max
        # print("__get_v_e_pot_winter()")
        
        # Generate power specific potential [kWh/kW]:
        df_v_e_kWhpkW = df_v_e/p_max
        df_v_e_kWhpkW.fillna(0, inplace=True) # in case p_max = 0
        
        self._v_e_pot_winter = np.array(df_v_e)
        self._v_e_pot_winter_kWhpkW = np.array(df_v_e_kWhpkW)
        self.p_max_winter = p_max

        # return df_v_e, p_max
            
    # def get_v_e_pot_remain(self):
    def __compute_v_e_pot_remain(self):        
        self._v_e_pot_remain = (self._v_e_pot - self._v_e - self._v_e_ch)
        
    def update_v_e(self, v_e_updated):
        
        if len(v_e_updated) != len(self._v_e):
            raise ValueError("v_e_updated must have the same length as v_e!")
            
        self._v_e = np.array(v_e_updated)
        
        self.__compute_v_e_pot_remain()
        
    def update_v_e_cons(self, v_e_cons_updated):
        if len(v_e_cons_updated) != len(self._v_e):
            raise ValueError()        
        self._v_e_cons = np.array(v_e_cons_updated)
    
    def update_v_e_exp(self, v_e_exp_updated):
        if len(v_e_exp_updated) != len(self._v_e):
            raise ValueError()        
        self._v_e_exp = np.array(v_e_exp_updated)             
    
    def __get_actual_cap_perc_bins(self, df_wp_profiles):
        """
        Compute the actual capacity percentage for each bin of profiles. In the
        files, the bins are labelled 20%, 40%, ... , 100%. However, the actual
        capacity differes slightly.

        Parameters
        ----------
        df_wp_profiles : pandas dataframe
            Dataframe from wind power profiles file. The
            first row contains the capacity of the respective bin.

        Returns
        -------
        cap_perc_bins : list
            List of the actual percentages for the capacity of each bin.
            (e.g. [0.21, 0.42, 0.58, 0.79, 1.00])

        """
        
        # Get the number of bins in the profiles dataset (i.e. number of columns):
        n = df_wp_profiles.shape[1]
        
        # Get the capacity value at 100% (i.e. last column in dataframe):
        p_max = self.__get_p_max_kW(df_wp_profiles)*1000 # [W]
        # p_max = df_wp_profiles.iloc[0, n-1]
        
        # Calculate the percentage for each bin:
        cap_perc_bins = []
        
        # Calculate percentages:
        for i in range(n):
            
            cap_perc_bins.append(df_wp_profiles.iloc[0, i]/p_max)
            
        
        return cap_perc_bins
    
    
    def __get_bin_cap_kW(self, df_wp_profiles):
        
        # Get the number of bins in the profiles dataset (i.e. number of columns):
        n = df_wp_profiles.shape[1]
        
        # List to store the capacity of each bin:
        cap_bins = []
        
        # Fetch capacities:
        for i in range(n):
            
            cap_bins.append(df_wp_profiles.iloc[0, i]/1000) # [kW]
        
        return cap_bins
    
    
    def __get_p_max_kW(self, df_wp_profiles):
        """
        

        Parameters
        ----------
        df_wp_profiles : pandas dataframe
            Dataframe from wind power profiles file. The
            first row contains the capacity of the respective bin.

        Returns
        -------
        p_max : float
            Wind power capacity [kW] at 100% installation rate.

        """
        
        p_max = df_wp_profiles.iloc[0, -1]/1000 # [kW]
        
        return p_max
    
    def compute_cap_max_resource_annual(self):
        numerator = self.get_v_e_pot_annual()
        denominator = self.get_v_e_pot_annual_kWhpkW()
        
        denominator_safe = np.where(denominator == 0, np.nan, denominator)

        cap_max_resource_annual = np.nanmean(numerator/denominator_safe)

        if np.isnan(cap_max_resource_annual):
            cap_max_resource_annual = 0.0

        return cap_max_resource_annual

    def compute_cap_max_resource_winter(self):
        numerator = self.get_v_e_pot_winter()
        denominator = self.get_v_e_pot_winter_kWhpkW()
        
        denominator_safe = np.where(denominator == 0, np.nan, denominator)

        cap_max_resource_winter = np.nanmean(numerator/denominator_safe)
        
        if np.isnan(cap_max_resource_winter):
            cap_max_resource_winter = 0.0

        return cap_max_resource_winter
    
    def get_kWp_max(self):
        self.num_test(self._kWp_max)
        return self._kWp_max
    
    def get_p_e_kW(self):
        self.num_test(self.p_e_wp)
        return self.p_e_wp
    
    def get_installed_allocation(self):
        return self._installed_allocation
    
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e    
    
    def get_v_e_ch(self):
        self.len_test(self._v_e_ch)
        return self._v_e_ch    
    
    def get_v_e_cons(self):
        self.len_test(self._v_e_cons)
        return self._v_e_cons    
    
    def get_v_e_exp(self):
        self.len_test(self._v_e_exp)
        return self._v_e_exp    
    
    def get_v_e_pot(self):
        self.len_test(self._v_e_pot)
        return self._v_e_pot    
    
    def get_v_e_pot_remain(self):
        self.len_test(self._v_e_pot_remain)
        return self._v_e_pot_remain    
    
    def get_v_e_pot_annual(self):
        self.len_test(self._v_e_pot_annual)
        return self._v_e_pot_annual    
    
    def get_v_e_pot_annual_kWhpkW(self):
        self.len_test(self._v_e_pot_annual_kWhpkW)
        return self._v_e_pot_annual_kWhpkW    
    
    def get_v_e_pot_winter(self):
        self.len_test(self._v_e_pot_winter)
        return self._v_e_pot_winter    
    
    def get_v_e_pot_winter_kWhpkW(self):
        self.len_test(self._v_e_pot_winter_kWhpkW)
        return self._v_e_pot_winter_kWhpkW    
            
    