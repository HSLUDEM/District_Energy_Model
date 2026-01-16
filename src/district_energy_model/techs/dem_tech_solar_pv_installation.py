# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:00:58 2024

@author: pascalvecsei

Class for individual solar PV installation type. 
Each individual installation type or class has two (2) primary properties:
A max-production profile and an occupation.

"""

import pandas as pd
import numpy as np
import sys
import os

from district_energy_model.techs.dem_tech_core import TechCore



# Add modules from parent directory:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
parent_dir_path = os.path.dirname(dname)
sys.path.insert(0, parent_dir_path)

import dem_helper

class SolarPVInstallation(TechCore):

    """
    Supply technology: solar pv installations.
    
    Possible inputs:
    
    """

    def __init__(
        self,
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

        self._share_occupied = share_occupied

        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
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

        n_hours = n_days*24
        
        self._v_e = self._v_e[:n_hours]
        self._v_e_cons = self._v_e_cons[:n_hours]
        self._v_e_exp = self._v_e_exp[:n_hours]
        self._v_e_pot = self._v_e_pot[:n_hours]
        self._v_e_pot_remain = self._v_e_pot_remain[:n_hours]
        self._max_profile = self._max_profile[:n_hours]

    def compute_v_e(self):

        self._v_e = self._max_profile * self._share_occupied
        self._v_e_yr = self._v_e.sum()

    def compute_v_e_pot_base(self):

        self._v_e_pot = self._max_profile
        self._v_e_pot_yr = self._v_e_pot.sum()

    def _compute_v_e_pot_remain(self):

        self._v_e_pot_remain = self._v_e_pot - self._v_e
        self._v_e_pot_remain_yr = self._v_e_pot_remain.sum()

    def update_v_e(self,
                   v_e_updated
                   ):

        if len(v_e_updated) != len(self._v_e):
            raise ValueError("v_e_updated must have the same length as v_e!")

        self._v_e = np.array(v_e_updated)
        self._v_e_yr = self._v_e.sum()
        self._compute_v_e_pot_remain()

    def update_v_e_cons(self, v_e_cons_updated):
        if len(v_e_cons_updated) != len(self._v_e):
            raise ValueError()
        self._v_e_cons = np.array(v_e_cons_updated)
        self._v_e_cons_yr = self._v_e_cons.sum()
    
    def update_v_e_exp(self, v_e_exp_updated):
        if len(v_e_exp_updated) != len(self._v_e):
            raise ValueError()        
        self._v_e_exp = np.array(v_e_exp_updated)
        self._v_e_exp_yr = self._v_e_exp.sum()

        
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
        if self._only_use_installed:
            p_max_unocc = 0
        
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

    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e
    
    def get_v_e_pot(self):
        self.len_test(self._v_e_pot)
        return self._v_e_pot

    def get_v_e_cons(self):
        self.len_test(self._v_e_cons)
        return self._v_e_cons
    
    def get_v_e_exp(self):
        self.len_test(self._v_e_exp)
        return self._v_e_exp

    def get_v_e_pot_remain(self):
        self.len_test(self._v_e_pot_remain)
        return self._v_e_pot_remain
