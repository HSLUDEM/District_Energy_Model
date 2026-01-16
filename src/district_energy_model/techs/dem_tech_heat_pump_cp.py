# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:20:25 2024

@author: UeliSchilt
"""

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore
from district_energy_model.techs.dem_tech_heat_pump_core import HeatPumpCore

# class HeatPump(TechCore):
class HeatPumpCP(HeatPumpCore):
    
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
        # super().__init__(tech_dict)
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier types:
        self._input_carrier = 'electricity'
        self._output_carrier = 'heat_hpcp'
        
        self._label = 'heat_pump_cp'

        # Accounting:
        self._u_e = [] # heat pump input - electricity
        self._u_h = [] # heat pump input - heat from environment
        self._v_h = [] # heat pump output (heat)
        # self._cop = []

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
        # self._cop = tech_dict['cop'] # Coefficient of performance
        self._v_h_max = tech_dict['kW_th_max'] # Max thermal capacity
        self._force_cap_max = tech_dict['force_cap_max']
        self._cap_min_use = tech_dict['cap_min_use']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._capex = tech_dict['capital_cost']
        self._maintenance_cost = tech_dict['maintenance_cost']

        self.init_cop_properties(tech_dict)

    def init_cop_properties(self, tech_dict):

        self._cop_mode = tech_dict["cop_mode"]
        self._cop_timeseries_file_path = tech_dict["cop_timeseries_file_path"]
        self._cop_constant_value = tech_dict['cop_constant_value']
        self._spf_to_target = tech_dict['spf_to_target']

        self._cop_source_temperature = tech_dict["cop_source_temperature"]
        self._cop_source_constant_temperature_value = tech_dict["cop_source_constant_temperature_value"]
        self._cop_hot_temperature = tech_dict["cop_hot_temperature"]
        self._cop_hot_temperature_constant_temperature_value = tech_dict["cop_hot_temperature_constant_temperature_value"]
        self._quality_factor = tech_dict["quality_factor"]



    def update_df_results(self, df):
        
        # super().update_df_results(df)
        
        df['u_e_hpcp'] = self.get_u_e()
        df['u_h_hpcp'] = self.get_u_h()
        df['v_h_hpcp'] = self.get_v_h()
        df['cop_hpcp'] = self.get_cop()

        return df
    

    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_e = init_vals.copy()
        self._u_h = init_vals.copy()
        self._v_h = init_vals.copy()
        self._cop = self._cop[:n_hours]
        self._temperature_based_cop = init_vals.copy()

    # def compute_v_h(self, src_h_yr, d_h_profile):

    #     tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
    #     tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
    #     self._v_h = np.array(tmp_df['v_h'].tolist())
                
    #     # Re-calculate:
    #     self.__compute_u_e()
    #     self.__compute_u_h()

        
        
    # def update_v_h_i(self, i, val):
    #     self.num_test(val)
    #     self._v_h[i] = val
        
    #     self.__compute_u_e_i(i)
    #     self.__compute_u_h_i(i)
    
    def set_temperature_based_cop(self, coplist):
        self._temperature_based_cop = coplist
    def get_temperature_based_cop(self):
        return self._temperature_based_cop
        
        
    
    
    
    
    
    
    
    
    