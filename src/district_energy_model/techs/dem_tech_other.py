# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 15:17:11 2024

@author: UeliSchilt
"""
import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore

class Other(TechCore):
    
    def __init__(self, tech_dict):
        
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
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier types:
        self.input_carrier_1 = 'electricity'
        self.input_carrier_2 = 'heat'
        self.output_carrier_1 = 'electricity'
        self.output_carrier_2 = 'heat'
        
        # Accounting:
        # self.u_e = []
        # self.u_h = []
        self._v_e = np.array([0]*8760)
        self._v_h = np.array([0]*8760)
        
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the heat pump technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        # super().update_tech_properties(tech_dict)
        
        # Update tech dict:
        self.__tech_dict = tech_dict
        
        # Properties:
        # n/a       
        
        
    def update_df_results(self, df):
        
        # super().update_df_results(df)
        
        # df['u_e_other'] = self.u_e
        # df['u_h_other'] = self.u_h
        df['v_e_other'] = self.get_v_e()
        df['v_h_other'] = self.get_v_h()
        
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
        self._v_h = self._v_h[:n_hours]
    
    def compute_v_h(self, src_h_yr, d_h_profile):

        tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
        tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
        self._v_h = np.array(tmp_df['v_h'])
        
    def update_v_h(self, v_h_updated):
        
        if len(v_h_updated) != len(self._v_e):
            raise ValueError("v_h_updated must have the same length as v_h!")
            
        self._v_h = np.array(v_h_updated)
        
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h