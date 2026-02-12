# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:00:58 2024

@author: UeliSchilt
"""

import pandas as pd
import numpy as np
import sys
import os

from district_energy_model.techs.dem_tech_core import TechCore

# Add modules from parent directory:
# abspath = os.path.abspath(__file__)
# dname = os.path.dirname(abspath)
# parent_dir_path = os.path.dirname(dname)
# sys.path.insert(0, parent_dir_path)

from district_energy_model import dem_helper

class WasteHeat(TechCore):
    
    """
    Conversion technology: Waste heat.
    
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
        self.output_carrier = 'heat_wh'
        
        # Accounting:
        self._v_h = []
        self._v_h_resource = []
        self._v_co2 = []
        
        # Annual values:
        self._v_h_yr = ...
        self._v_h_resource_yr = ...
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
        self._timeseries_file_path = tech_dict['timeseries_file_path']
        self._tariff_CHFpkWh = tech_dict['tariff_CHFpkWh']
        # self._maintenance_cost = tech_dict['maintenance_cost']

        # Update input dict:
        self.__tech_dict = tech_dict
        

    def initialise_finite(self, n_days):
        n_hours = n_days*24
        zero_vals = np.zeros(n_hours)
        timeseries_data = np.zeros(n_hours)
        if self._timeseries_file_path.endswith(".feather"):
            timeseries_data = pd.read_feather(self._timeseries_file_path).to_numpy()[:n_hours, 0]
            

        self._v_h = zero_vals.copy()
        self._v_co2 = zero_vals.copy()
        self._v_h_resource = timeseries_data.copy()

    def update_df_results(self, df):
        
        df['v_h_wh'] = self.get_v_h()
        df['v_h_resource_wh'] = self.get_v_h_resource()
        df['v_co2_wh'] = self.get_v_co2()
        
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
        self._v_h_resource = self._v_h_resource[:n_hours]
        self._v_co2 = self._v_co2[:n_hours]
    
        
    def __compute_v_co2(self):
        self.len_test(self._v_h)        
        self._v_co2 = self._v_h*self.__tech_dict['co2_intensity']
    
    def __compute_import_cost(self):
        self.len_test(self._v_h)
        self._v_mon = self._tariff_CHFpkWh * self._v_co2
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['waste_heat'] = {
            'essentials':{
                'parent':'supply',
                'carrier': 'heat_wh'
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
                          resource,
                          energy_scaling_factor
                        #   energy_cap,
                          ):
        
        capex = self._capex
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': 'waste_heat'
                },
            'constraints':{
                'resource': resource,
                # 'energy_cap_max': energy_cap
                },
            'costs':{
                'monetary':{
                    'energy_cap': capex * energy_scaling_factor,
                    'om_annual': self._maintenance_cost * energy_scaling_factor,
                    'om_prod': self._tariff_CHFpkWh * energy_scaling_factor
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
        self.__compute_import_cost()

    def update_v_h_resource(self, v_h_resource_updated):
        
        if len(v_h_resource_updated) != len(self._v_h_resource):
            raise ValueError("v_h_resource_updated must have the same length as v_h_resource!")
        
        self._v_h_resource = np.array(v_h_resource_updated)
                