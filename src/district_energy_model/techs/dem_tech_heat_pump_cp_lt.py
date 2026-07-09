# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:20:25 2024

@author: UeliSchilt

Technology that uses low temperature heat as an input and converts it into usable heat using a heat pump
"""

import numpy as np
import pandas as pd
import input_files.inputs as inp

from district_energy_model.techs.dem_tech_core import TechCore

class HeatPumpCPLT(TechCore):
    
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
        self._input_carrier_1 = 'electricity'
        self._input_carrier_2 = 'heatlt'
        self._output_carrier = 'heat_hpcplt'
        
        # Accounting:
        self._u_e = [] # heat pump input - electricity
        self._u_hlt = [] # heat pump input - heat from low temperature heat source (e.g. waste heat)
        self._v_h = [] # heat pump output (heat)
        
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
        self._hpcplt_cop = tech_dict['cop'] # Coefficient of performance
        self._v_h_max = tech_dict['kW_th_max'] # Max thermal capacity
        self._force_cap_max = tech_dict['force_cap_max']
        self._cap_min_use = tech_dict['cap_min_use']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._capex = tech_dict['capital_cost']
        self._maintenance_cost = tech_dict['maintenance_cost']
        
        
        
    def update_df_results(self, df):
        
        # super().update_df_results(df)
        
        df['u_e_hpcplt'] = self.get_u_e()
        df['u_hlt_hpcplt'] = self.get_u_hlt()
        df['v_h_hpcplt'] = self.get_v_h()
        
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
        
        self._u_e = self._u_e[:n_hours]
        self._u_hlt = self._u_hlt[:n_hours]
        self._v_h = self._v_h[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_e = init_vals.copy()
        self._u_hlt = init_vals.copy()
        self._v_h = init_vals.copy()
        
    
    # def compute_v_h(self, src_h_yr, d_h_profile):

    #     tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
    #     tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
    #     self._v_h = np.array(tmp_df['v_h'].tolist())
                
    #     # Re-calculate:
    #     self.__compute_u_e()
    #     self.__compute_u_h()

        
    def update_v_h(self, v_h_updated):
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
        
        self._v_h = np.array(v_h_updated)
        
        self.__compute_u_e()
        self.__compute_u_hlt()
        
    
    def get_hpcplt_cop(self):
        self.num_test(self._hpcplt_cop)
        return self._hpcplt_cop
                
    def get_v_h(self):
        if len(self._v_h)==0:
            raise ValueError()
        return self._v_h
    
    def get_u_e(self):
        if len(self._u_e)==0:
            raise ValueError()
        return self._u_e
    
    def get_u_hlt(self):
        if len(self._u_hlt)==0:
            raise ValueError()
        return self._u_hlt
                
    def __compute_u_e(self):
        
        """
        Computes the hourly electricity input (u_e) to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_e = self._v_h/self._hpcplt_cop
   
    def __compute_u_hlt(self):
        
        """
        Computes the hourly heat input (u_hlt) from the environment to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_hlt = self._v_h*(1-1/self._hpcplt_cop)
                        
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['heat_pump_cp_lt'] = {
            'base_tech':'conversion',
            'carrier_in':[self._input_carrier_1, self._input_carrier_2],
            'carrier_out':self._output_carrier,
            'lifetime': self._lifetime,
            'cost_flow_in':{
                'data': 0.0, # this is reflected in the cost of the electricity
                'index':'monetary',
                'dims':'costs',
                },
            'cost_interest_rate':{
                'data':self._interest_rate,
                'index':'monetary',
                'dims':'costs',
                },
            }
        
        return tech_groups_dict
    
    def create_techs_dict(
            self,
            techs_dict,
            header,
            name,
            color,
            energy_scaling_factor
            ):
        
        techs_dict[header] = {
            'name': name,
            'color': color,
            'template': 'heat_pump_cp_lt',
            'flow_cap_max': self._v_h_max / energy_scaling_factor if self._v_h_max != 'inf' else self._v_h_max,
            'flow_out_min_relative': self._cap_min_use,
            'flow_out_eff':self._hpcplt_cop,
            'cost_flow_cap':{
                'data': self._capex * energy_scaling_factor,
                'index':'monetary',
                'dims':'costs',
                },
            'cost_om_annual':{
                'data': self._maintenance_cost * energy_scaling_factor,
                'index':'monetary',
                'dims':'costs',
                },
            }
        
        if self._force_cap_max:
            techs_dict[header]['flow_cap_min'] = self._v_h_max
            techs_dict[header]['flow_cap_max'] = self._v_h_max
        
    
        return techs_dict #, additional_techs_label_list
    

    
        
    
    
    
    
    
    
    
    
    
    
    
    
