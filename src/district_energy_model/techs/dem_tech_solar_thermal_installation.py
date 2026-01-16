# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:00:58 2024

@author: pascalvecsei

Class for individual solar Thermal installation type. 
Each individual installation type or class has two (2) primary properties:
A max-production profile and an occupation.

The classes for solar thermal and solar PV installations are not coupled directly. They may use the same area, but in manual scenarios, they do not compete.



"""

import pandas as pd
import numpy as np
import sys
import os

from techs.dem_tech_core import TechCore

# Add modules from parent directory:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
parent_dir_path = os.path.dirname(dname)
sys.path.insert(0, parent_dir_path)

import dem_helper

class SolarThermalInstallation(TechCore):

    """
    Supply technology: solar thermal installations.
    
    Possible inputs:
    
    """

    def __init__(
        self,
        output_carrier,
        profile,
        share_occupied,
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

        ...

        #Meta_Data:

        self._max_profile = profile
        self._max_profile_yr_tot = profile.sum()


        self._share_occupied = share_occupied

        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier types:
        self.output_carrier = output_carrier
        
        # Accounting:
        self._v_h = []
        self._v_h_cons = []
        self._v_h_exp = []
        self._v_h_pot = []
        self._v_h_pot_remain = []
        
        # Annual values:
        self._v_h_yr = ...

        self.power_up_for_replacement = 0

    def update_tech_properties(self, tech_dict):

        """        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        # Properties:

        self._v_max = tech_dict['kW_max']
                        
        self._lifetime = tech_dict['lifetime']
        
        self._interest_rate = tech_dict['interest_rate']
        
        self._capex = tech_dict['capex'] #base_capex in Fr./kWp installed power (not be confused with the real peak power)
        
        # self._only_use_installed = tech_dict['only_use_installed']
        
        self._maintenance_cost = tech_dict['maintenance_cost']

        self._export_subsidy = tech_dict['export_subsidy']

        self._only_use_installed = tech_dict['only_use_installed']

        # Update input dict:
        self.__tech_dict = tech_dict

    def set_power_up_for_replacement(self, power_up_for_replacement):
        self.power_up_for_replacement = power_up_for_replacement

    def update_df_results(self, df):
        
        df['v_h_solar'] = self.get_v_h()
        df['v_h_solar_cons'] = self.get_v_h_cons()
        df['v_h_solar_exp'] = self.get_v_h_exp()
        df['v_h_solar_pot'] = self.get_v_h_pot()
        df['v_h_solar_pot_remain'] = self.get_v_h_pot_remain()
        
        return df

    def reduce_timeframe(self, n_days):

        n_hours = n_days*24
        
        self._v_h = self._v_h[:n_hours]
        self._v_h_cons = self._v_h_cons[:n_hours]
        self._v_h_exp = self._v_h_exp[:n_hours]
        self._v_h_pot = self._v_h_pot[:n_hours]
        self._v_h_pot_remain = self._v_h_pot_remain[:n_hours]
        self._max_profile = self._max_profile[:n_hours]

    def set_v_h(self, v_h_updated):

        self._v_h = v_h_updated
    
        self._compute_v_h_pot_remain()


    def compute_v_h(self):

        self._v_h = self._max_profile * self._share_occupied
        self._v_h_yr = self._v_h.sum()

    def compute_v_h_const_share(self, src_h_yr, d_h_profile):

        # print("comparison", src_h_yr, ' / ', self._max_profile_yr_tot)

        self._share_occupied = src_h_yr / self._max_profile_yr_tot

        tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
        tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
        self._v_h = np.array(tmp_df['v_h'])
        self._v_h_cons = np.array(tmp_df['v_h'])
        self._v_h_exp = 0*np.array(tmp_df['v_h'])


    def compute_v_h_pot_base(self):

        self._v_h_pot = self._max_profile
        self._v_h_pot_yr = self._v_h_pot.sum()

    def _compute_v_h_pot_remain(self):

        self._v_h_pot_remain = self._v_h_pot - self._v_h
        self._v_h_pot_remain_yr = self._v_h_pot_remain.sum()

    def update_v_h(self,
                   v_h_updated
                   ):

        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")

        self._v_h = np.array(v_h_updated)
        self._v_h_yr = self._v_h.sum()
        self._compute_v_h_pot_remain()

    def update_v_h_cons(self, v_h_cons_updated):
        if len(v_h_cons_updated) != len(self._v_h):
            raise ValueError()
        self._v_h_cons = np.array(v_h_cons_updated)
        self._v_h_cons_yr = self._v_h_cons.sum()
    
    def update_v_h_exp(self, v_h_exp_updated):
        if len(v_h_exp_updated) != len(self._v_h):
            raise ValueError()        
        self._v_h_exp = np.array(v_h_exp_updated)
        self._v_h_exp_yr = self._v_h_exp.sum()

        
    def create_techs_dict(self,
                          techs_dict,
                          headers, 
                          parent,
                          header,
                          name, 
                          color, 
                          resource,
                          ):
        
        self._share_occupied

        p_max_occ = self._max_profile.max() * self._share_occupied
        p_max_unocc = self._max_profile.max() * np.round((1.0 - self._share_occupied),5)

        # print("VALUES = ", p_max_occ, p_max_unocc, self._share_occupied, self._max_profile.max())


        if p_max_unocc <0:
            p_max_unocc = 0
        if self._only_use_installed:
            p_max_unocc = 0
        
        # print("VALUES = ", p_max_occ, p_max_unocc)

        techs_dict[header+"_occupied"] = {
            'essentials':{
                'name': name+"_occupied",
                'color': color,
                'parent': parent
                },
            'constraints':{
                'resource': resource,
                'energy_cap_max': p_max_occ
                },
            'costs':{
                'monetary':{
                    'energy_cap': 0,
                    'om_annual': self._maintenance_cost,
                    'export': -self._export_subsidy,
                    }
                }
            }    
        
        # headers.append(header+"_occupied")

        techs_dict[header+"_unoccupied"] = {
            'essentials':{
                'name': name+"_unoccupied",
                'color': color,
                'parent': parent
                },
            'constraints':{
                'resource': resource,
                'energy_cap_max': p_max_unocc
                },
            'costs':{
                'monetary':{
                    'energy_cap': self._capex,
                    'om_annual': self._maintenance_cost,
                    'export': -self._export_subsidy,
                    }
                }
            }    

        # headers.append(header+"_unoccupied")
        headers.append(header)

        return techs_dict, headers

    def get_resource(self):
        return self._max_profile

    def get_v_h(self):

        print(len(self._v_h))

        self.len_test(self._v_h)
        return self._v_h
    
    def get_v_h_pot(self):
        self.len_test(self._v_h_pot)
        return self._v_h_pot

    def get_v_h_cons(self):
        self.len_test(self._v_h_cons)
        return self._v_h_cons
    
    def get_v_h_exp(self):
        self.len_test(self._v_h_exp)
        return self._v_h_exp

    def get_v_h_pot_remain(self):
        self.len_test(self._v_h_pot_remain)
        return self._v_h_pot_remain
