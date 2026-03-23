# -*- coding: utf-8 -*-
"""
Created on Mon May  6 16:16:11 2024

@author: Somesh
"""

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore

class HydrogenProduction(TechCore):
    
    def __init__(self, tech_dict):
        
        """

        Parameters
        ----------
        input_carrier : string, name of input carrier (manure, green_waste, sewage_sludge)
        
        eta : float, value of conversion efficiency, has to be between 0 and 1

        Returns
        -------
        None.

        """
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier types:
        self.input_carrier = 'electricity'
        self.output_carrier = 'hydrogen'
        
        #Accounting:
        self._u_e = [] # manure potential input [kWh]
        self._v_hyd = [] # gas LHV output [kWh]
        
        
        
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        
        #Checks for Errors:
        if tech_dict['efficiency'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")
            
        #Properties:
        self._eta = tech_dict['efficiency']
        self._maintenance_cost = tech_dict['maintenance_cost']

        
        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_e_hydp'] = self.get_u_e()
        df['v_hyd_hydp'] = self.get_v_hyd()
        
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
        self._v_hyd = self._v_hyd[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_e = init_vals.copy()
        self._v_hyd = init_vals.copy()
        
    def compute_u_input_carrier(self):
        """
        Compute the required input [kWh] of the input carrier, given a gas output [kWh].

        Returns
        -------
        None.

        """
        self._u_e = self._v_hyd/self._eta
        
    def __compute_u_e(self):
        """
        Compute the required input [kWh] of the input carrier, given a gas output [kWh].

        Returns
        -------
        None.

        """
        self._u_e = self._v_hyd/self._eta
        
    def compute_o_gas(self):
        """
        Compute the gas output [kWh], given the input [kWh].

        Returns
        -------
        None.

        """
        
        self._v_hyd = self._u_e * self._eta
        
    def update_v_hyd(self, v_hyd_updated):
        if len(v_hyd_updated) != len(self._v_hyd):
            raise ValueError("v_hyd_udpated must have the same length as v_hyd!")            
        self._v_hyd = np.array(v_hyd_updated)
        self.__compute_u_e()
    
    def generate_tech_dict(self, techs_dict, energy_scaling_factor):
        
        hyd_dict = {
            'essentials':{
                'name':'Hydrogen Production',
                'color':self.__tech_dict['color'],
                'parent':'conversion',
                'carrier_in': 'electricity',
                'carrier_out': 'hydrogen',
                },
            'constraints':{
                'energy_cap_max':self.__tech_dict['capacity_kWh']/energy_scaling_factor if self.__tech_dict['capacity_kWh'] != 'inf' else 'inf',
                'energy_eff':self.__tech_dict['efficiency'],
                'lifetime':self.__tech_dict['lifetime']
                },
            'costs':{
                'monetary':{
                    'energy_cap': self.__tech_dict['capital_cost'] * energy_scaling_factor,
                    'om_con':self.__tech_dict['om_cost'] * energy_scaling_factor, # [CHF/kWh]
                    'interest_rate':self.__tech_dict['interest_rate'],
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    },
                }
            }
        
        techs_dict['hydrogen_production'] = hyd_dict
        
        return techs_dict
    
    def get_eta(self):
        self.num_test(self._eta)
        return self._eta
    
    def get_u_e(self):
        self.len_test(self._u_e)
        return self._u_e
    
    def get_v_hyd(self):
        self.len_test(self._v_hyd)
        return self._v_hyd