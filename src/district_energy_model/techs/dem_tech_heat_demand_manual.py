#Manual technology for timeseries-based heat demand

# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:00:15 2024

@author: PascalVecsei
"""

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore

class HeatDemandManual(TechCore):
    
    """
    Export technology: grid Export.
    """
    
    def __init__(self, tech_dict):
        
        """
        Initialise grid supply parameters.
        
        Parameters
        ----------
            
        tech_dict : dict
            Dictionary with technology parameters (subset of scen_techs).
    
        Returns
        -------
        n/a
        """
        
        super().__init__(tech_dict)
        
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        self.init_timeseries()
        # Carrier types:
        self.input_carrier = 'heat'
        
        # Accounting:
        self._d_h = [] #f for feedin
        
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the grid supply technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """

        self._demand_mode = tech_dict['demand_mode']
        self._timeseries_filepath = tech_dict['timeseries_file_path']

        self._constant_value = tech_dict['constant_value']

        self._capex = 0
        self._capex_one_to_one_replacement = 0
        self._maintenance_cost = 0
        
        self.__tech_dict = tech_dict
        
    def init_timeseries(self):

        #Price

        n_hours = 365*24

        self._timeseries = np.zeros(n_hours)

        if self._demand_mode == 'const':
            self._timeseries = self._timeseries + self._constant_value
        elif self._demand_mode == 'file':
            if self._timeseries_filepath.endswith(".feather"):
                self._timeseries = pd.read_feather(self._timeseries_filepath).to_numpy()[:n_hours, 0]
            elif self._timeseries_filepath.endswith(".npy"):
                self._timeseries = 1e5*np.load(self._timeseries_filepath)
            else:
                raise ValueError("Unknown file format for timeseries for manual heat demand. Use feather or npy.")
        else:
            raise ValueError("Unknown mode for timeseries for manual heat demand. Use 'const' or 'file'.")

    def initialise_zero(self, n_days):
        n_hours = n_days*24
        zero_vals = np.zeros(n_hours)            

        self._d_h = zero_vals.copy()
        self._timeseries = self._timeseries[:n_hours]
        
        
    def update_df_results(self, df):
        df['d_h_m'] = self.get_d_h()
        
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
        
        self._d_h = self.d_h[:n_hours]

        self._timeseries = self._timeseries[:n_hours]
            
        
    def add_d_h(self, d_h_m_new):
        self._d_h = np.array(d_h_m_new)
        
    def update_d_h(self, d_h_updated):
        self._d_h = np.array(d_h_updated)        
        
    def create_techs_dict(self, 
                          techs_dict,
                          header,
                          name,  
                          color, 
                          resource,
                          energy_scaling_factor):
            
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color':color,
                'parent':'demand',
                'carrier': 'heat',
                },
            'constraints':{
                "resource": resource,
                },
            }
        
        return techs_dict
    
    def get_d_h(self):
        self.len_test(self._d_h)
        return self._d_h
    
    def get_timeseries(self):
        return self._timeseries