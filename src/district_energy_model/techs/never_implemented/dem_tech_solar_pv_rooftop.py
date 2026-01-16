# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:00:58 2024

@author: UeliSchilt, pascalvecsei

Class for rooftop solar PV technology
"""

import pandas as pd
import numpy as np
import sys
import os

from techs.dem_tech_solar_pv_base import SolarPVBase

# Add modules from parent directory:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
parent_dir_path = os.path.dirname(dname)
sys.path.insert(0, parent_dir_path)

import dem_helper

class SolarPVRooftop(SolarPVBase):
    
    """
    Conversion technology: solar pv.
    
    Possible inputs:
        - hourly yield (kWh)
        - hourly specific yield (kWh/m2)
        - hourly irradiation (kWh/m2)
        - hourly radiation (kWh)
        - pv surface (m2)
    
    """
    
    def __init__(
            self,
            com_nr,
            tech_dict
            ):
        
        """
        Initialise technology parameters.
        
        Parameters
        ----------
        
        tech_dict : dict
            Dictionary with technology parameters (subset of scen_techs).
    
        Returns
        -------
        n/a
        """
        
        super().__init__(tech_dict)
        
        self.com_nr = com_nr
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # self.com_lat = com_lat
        # self.com_lon = com_lon
        
        # Preprocess pv resource data:
        # self.data_preprocessing()
        
        # Carrier types:
        self.output_carrier = 'electricity'
        
        # Accounting:
        self._v_e = []
        self._v_e_cons = []
        self._v_e_exp = []
        self._v_e_pot = []
        self._v_e_pot_remain = []
        
        # Annual values:
        self._v_e_yr = ...
    
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the solar pv technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        # Properties:
        self.v_max = tech_dict['kWp_max']
        self._eta_overall = tech_dict['eta_overall']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._capex = tech_dict['capex']
        self._only_use_installed = tech_dict['only_use_installed']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._export_subsidy = tech_dict['export_subsidy']

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['v_e_pv'] = self.get_v_e()
        df['v_e_pv_cons'] = self.get_v_e_cons()
        df['v_e_pv_exp'] = self.get_v_e_exp()
        df['v_e_pv_pot'] = self.get_v_e_pot()
        df['v_e_pv_pot_remain'] = self.get_v_e_pot_remain()
        
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
        self._v_e_cons = self._v_e_cons[:n_hours]
        self._v_e_exp = self._v_e_exp[:n_hours]
        self._v_e_pot = self._v_e_pot[:n_hours]
        self._v_e_pot_remain = self._v_e_pot_remain[:n_hours]
    
    def data_preprocessing(self):
        
        #----------------------------------------------------------------------
        # Read pv meta file:
        pv_meta_file_path = self.pv_data_dir + self.pv_data_meta_file
        self.df_pv_meta = pd.read_csv(pv_meta_file_path)
        
        self.pv_data_file = self.__select_pv_file(
            self.df_pv_meta,
            self.com_lat,
            self.com_lon
            )
    
    def __select_pv_file(self, df_pv_meta, com_lat, com_lon):
        
        # !!! This is a temporary model; must be replaced with a better model!
        # For example pv_lib
        
        """Selects the pv input file based on the distance between selected community
        and the location where the pv profile was simulated. The location closest
        to the community is selected.
        
        Parameters
        ----------
        df_pv_meta : pandas dataframe
            dataframe containing meta data about pv profile files
        com_lat : float
            latitude of selected community
        com_lon : float
            longitude of selected community
        
        Returns
        -------
        string
            name of the pv_input_file (e.g. 'Basel_v0_hr.csv')
        """


        # create temporary copy of pv meta df, for evaluation of closest location
        tmp_df_pv_meta = df_pv_meta.copy()
        
        # add column with distances to each pv-simulation location in temp. df
        tmp_df_pv_meta['dist_km'] = \
            tmp_df_pv_meta.apply(lambda row: dem_helper.distance_between_coord(com_lat, com_lon, row['coord_lat_median'], row['coord_long_median']), axis=1)
        
        min_dist = tmp_df_pv_meta['dist_km'].min()
        
        pv_file = tmp_df_pv_meta.loc[tmp_df_pv_meta['dist_km'] == min_dist, 'filename'].item()
        
        del tmp_df_pv_meta
        
        return str(pv_file)
    
    # def get_v_e(self, df_com_yr):
    def compute_v_e(self,
                    df_meta,
                    profiles_file):    
        """
        Compute annual and hourly PV output [kWh].

        Parameters
        ----------
        df_com_yr : dataframe
            Community dataframe with annual valuesö (subset of master file).

        Returns
        -------
        None.

        """
        
        # Annual output of installed PV:
        v_e_pv_yr  = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'TotalEnergy'].values # [kWh]
        pv_filename = 'PV_Profile_' + df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'PV_Filename'].values[0]
        self.pv_profile_hr = profiles_file[pv_filename]
        
        # pv_data_path = self.pv_data_dir + self.pv_data_file
        # pv_profile = pd.read_csv(pv_data_path)
        # self.pv_profile_hr = pv_profile/pv_profile.sum()
        # self.pv_profile_hr = self.pv_profile_hr['v_e_pv'] # Convert to series
        
        # scale profile to annual output:
        v_e_pv = v_e_pv_yr*self.pv_profile_hr
        
        
        self._v_e = np.array(v_e_pv)
        self._v_e_yr = v_e_pv_yr
            
    # def get_v_e_pot_base(self, df_com_yr):
    def compute_v_e_pot_base(self, df_meta):
        
        v_e_pv_pot = df_meta.loc[df_meta['GGDENR'] == self.com_nr, 'PV_Pot'].values*self.pv_profile_hr
        
        v_e_pv_pot_remain = np.array(v_e_pv_pot) - self._v_e
        
        self._v_e_pot = np.array(v_e_pv_pot)
        self._v_e_pot_remain = np.array(v_e_pv_pot_remain)
        
    def __compute_v_e_pot_remain(
            self,
            tech_solar_thermal=0,
            consider_solar_thermal=True
            ): # v_h_solar, eta_thermal): 
    # def get_v_e_pot_remain(v_e_pv, v_e_pv_pot, v_h_solar, eta_pv, eta_thermal):
        """
        Return the remaining potential for solar PV. This potential can also be
        utilised for solar thermal (the two are competing for the same roof
        area). In this case the potential must be converted according to the
        efficiency of the solar thermal system.
        
        The total solar PV potential remains constant, as it includes the
        installed and additional potential.

        Parameters
        ----------
        v_e_pv : pandas dataseries
            Realised (i.e. installed) solar PV potential [kWh].
        v_e_pv_pot : pandas dataseries
            Total solar pv potential (incl. installed) [kWh].
        v_h_solar : pandas dataseries
            Realised (i.e. installed) solar thermal potential [kWh_th].
        eta_pv : float
            Solar PV conversion efficiency. Used to convert between solar pv
            potential and solar thermal potential [-].
        eta_thermal : float
            Solar thermal conversion efficiency. Used to convert between solar
            pv potential and solar thermal potential [-].

        Returns
        -------
        v_e_pv_pot_remain : pandas dataseries
            Remaining solar PV potential after application of a scenario
            or optimistion [kWh].

        """
        
        if consider_solar_thermal:
            
            v_h_solar = tech_solar_thermal.get_v_h()
            eta_thermal = tech_solar_thermal.get_eta_overall()
            eta_pv = self._eta_overall
            
            # Convert realised solar thermal to equivalent pv potential:
            thermal_to_pv_equi = v_h_solar/eta_thermal*eta_pv
        
            v_e_pv_pot_remain = (
                self.get_v_e_pot()
                - self.get_v_e()
                - thermal_to_pv_equi
                )
        
        else:
            v_e_pv_pot_remain = self.get_v_e_pot() - self.get_v_e()
            v_e_pv_pot_remain[np.abs(v_e_pv_pot_remain) < 1e-5] = 0
        
        self._v_e_pot_remain = v_e_pv_pot_remain
        
        return v_e_pv_pot_remain        
                
    def update_v_e(
            self,
            v_e_updated,
            tech_solar_thermal=0,
            consider_solar_thermal=True
            ):
        
        if len(v_e_updated) != len(self._v_e):
            raise ValueError("v_e_updated must have the same length as v_e!")
            
        self._v_e = np.array(v_e_updated)
        
        self.__compute_v_e_pot_remain(
            tech_solar_thermal,
            consider_solar_thermal
            )
        
    def update_v_e_cons(self, v_e_cons_updated):
        if len(v_e_cons_updated) != len(self._v_e):
            raise ValueError()        
        self._v_e_cons = np.array(v_e_cons_updated)
    
    def update_v_e_exp(self, v_e_exp_updated):
        if len(v_e_exp_updated) != len(self._v_e):
            raise ValueError()        
        self._v_e_exp = np.array(v_e_exp_updated)
                  
    
    @staticmethod
    def convert_thermal_to_pv(df_thermal_kWh, eta_pv, eta_thermal):
        # used in dem_energy_balance.py
        """
        Return values for solar pv energy equivalent to solar thermal energy
        under same irradiation and area.

        Parameters
        ----------
        df_thermal_kWh : pandas dataseries
            Timeseries of solar thermal generation (or potential) [kWh].
        eta_pv : float
            Overall conversion efficiency of solar PV system [-].
        eta_thermal : float
            Overall conversion efficiency of solar thermal system [-].

        Returns
        -------
        df_pv_kWh : pandas dataseries
            Timeseries of solar pv generation (or potential) [kWh].

        """
        
        df_pv_kWh = df_thermal_kWh/eta_thermal*eta_pv
        
        return df_pv_kWh
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['solar_pv'] = {
            'essentials':{
                'parent':'supply_plus',
                'carrier': 'electricity'
                },
            'constraints':{
                'export_carrier': 'electricity',
                'resource_unit': 'energy_per_area', # 'energy',
                'parasitic_eff': 1.0, # efficiency is already accounted for in the resource dataseries
                'force_resource': True,
                'lifetime': self._lifetime,
                },
            'costs':{
                'monetary':{
                    'interest_rate':self._interest_rate,
                    'om_con':0.0,
                    },
                }
            }
        
        return tech_groups_dict
        
    def create_techs_dict(self,
                          techs_dict,
                          header,
                          name, 
                          color, 
                          resource,
                          energy_cap,
                          capex_0=False
                          ):
        
        if capex_0==False:
            capex = self._capex
        elif capex_0==True:
            capex = 0
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': 'solar_pv'
                },
            'constraints':{
                'resource': resource,
                'energy_cap_max': energy_cap
                },
            'costs':{
                'monetary':{
                    'energy_cap': capex,
                    'om_annual': self._maintenance_cost,
                    'export': -self._export_subsidy,
                    }
                }
            }    
        
        return techs_dict
    
    def create_techs_dict_clustering(
            techs_dict,
            tech_dict,
            name = 'Solar PV',
            color = '#F9D956',
            capex = 0
            ):
        
        techs_dict['solar_pv'] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent':'supply_plus',
                'carrier': 'electricity'
                },
            'constraints':{
                'export_carrier': 'electricity',
                'resource_unit': 'energy_per_area', # 'energy',
                'parasitic_eff': 1.0, # efficiency is already accounted for in the resource dataseries
                'force_resource': True,
                'lifetime': tech_dict['lifetime']
                },
            'costs':{
                'monetary':{
                    'energy_cap': capex,
                    'interest_rate':tech_dict['interest_rate'],
                    'om_con':0.0
                    },
                }
            }    
        
        return techs_dict
    
    def get_eta_overall(self):
        self.num_test(self._eta_overall)
        return self._eta_overall
    
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e
    
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
        
    def get_pot_integration_factor(self):
        return self._pot_integration_factor
    
    def get_only_use_installed(self):
        return self._only_use_installed
        
        