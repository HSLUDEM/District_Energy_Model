# -*- coding: utf-8 -*-
"""
Created on Thu Apr 09 09:00:58 2026

@author: PascalVecsei
"""

import pandas as pd
import numpy as np
import sys
import os

from district_energy_model.techs.dem_tech_core import TechCore

from district_energy_model import dem_helper

class DeepGeothermal(TechCore):
    
    """
    Supply technology: Deep geothermal.
    This technology produces _heat_ only.
    
    Possible inputs:
    
    """
    
    def __init__(
            self,
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
                
        self.timeseries = ...
        self.update_tech_properties(tech_dict)
                
        # Carrier types:
        self.output_carrier = 'heat_dgt'
        
        # Accounting:
        self._v_h = []
        self._v_co2 = []
        
        # Annual values:
        self._v_h_yr = ...
        self._v_co2_yr = ...
    
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
        # self.v_max = tech_dict['kWp_max']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        self._capex = tech_dict['capex']
        self._maintenance_cost = tech_dict['maintenance_cost']

        # Update input dict:
        self.__tech_dict = tech_dict
        

    def initialise_zero(self, n_days):
        n_hours = n_days*24
        init_vals = np.array([0.0]*n_hours)
        self._v_h = init_vals.copy()
        self._v_co2 = init_vals.copy()

    def update_df_results(self, df):
        
        df['v_h_dgt'] = self.get_v_h()
        df['v_co2_dgt'] = self.get_v_co2()
        
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
        
        self._v_h = self._v_h[:n_hours]
        self._v_co2 = self._v_co2[:n_hours]
    
        
    def __compute_v_co2(self):
        self.len_test(self._v_h)        
        self._v_co2 = self._v_h*self.__tech_dict['co2_intensity']
        
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['deep_geothermal'] = {
            'essentials':{
                'parent':'supply',
                'carrier': 'heat_dgt'
                },
            'constraints':{
                'lifetime': self._lifetime,
                },
            'costs':{
                'monetary':{
                    'interest_rate':self._interest_rate,
                    'om_con':0.0
                    }
                }
            }
        
        return tech_groups_dict
        
    def create_techs_dict(self,
                          techs_dict,
                          header,
                          name, 
                          color, 
                          energy_scaling_factor
                        #   energy_cap,
                          ):
        
        capex = self._capex
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': 'deep_geothermal'
                },
            'constraints':{
                'energy_cap_max': self._capex / energy_scaling_factor if self._capex != 'inf' else 'inf',
                },
            'costs':{
                'monetary':{
                    'energy_cap': capex * energy_scaling_factor,
                    'om_annual': self._maintenance_cost * energy_scaling_factor,
                    },
                'emissions_co2':{
                    'om_prod':self._co2_intensity * energy_scaling_factor, 
                    }
                }
            }    
        
        return techs_dict
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
    
    def get_v_h_resource(self):
        self.len_test(self._v_h_resource)
        return self._v_h_resource 
       
    def get_v_co2(self):
        self.len_test(self._v_co2)
        return self._v_co2
    
    def update_v_h(self, v_h_updated):
        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
        
        self._v_h = np.array(v_h_updated)
        
        self.__compute_v_co2()
