# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:23:54 2024

Oil boiler central plant. Large oil boiler connected to the district heating
network, mostly to provide peak heat. 

@author: UeliSchilt
"""

import pandas as pd
import numpy as np
import dem_constants as C
from techs.dem_tech_core import TechCore

class ElectricHeaterCP(TechCore):
    
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
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier types:
        self.input_carrier = 'electricity' 
        self.output_carrier = 'heat_ehcp'
        
        # Accounting:
        self._u_e = [] # electric input [kWh]
        self._v_h = [] # heat output [kWh]
        
        #----------------------------------------------------------------------
        # Tests:

        if self._eta > 1:
            printout = ('Error in oil boiler input: '
                        'conversion efficiency (eta) cannot be larger than 1!'
                        )
            raise Exception(printout)
            
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the electric heater technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        # Properties:
        self._eta = tech_dict['eta']
        self._v_h_max = tech_dict['kW_th_max']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._capex = tech_dict['capex']
        self._maintenance_cost = tech_dict['maintenance_cost']
        
        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_e_ehcp'] = self.get_u_e()
        df['v_h_ehcp'] = self.get_v_h()
        
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
        self._v_h = self._v_h[:n_hours]
            
    def update_v_h(self, v_h_updated):
        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
        
        self._v_h = np.array(v_h_updated)
        
        self.__compute_u_e()
                
    def __compute_u_e(self):
        """
        Compute the required electric input (kWh) based on heat output (kWh).
        """                
        self._u_e = np.array(self._v_h)/self._eta # [kWh]
                    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['electric_heater_cp'] = {
            'essentials':{
                'parent':'conversion',
                'carrier_in':'electricity',
                'carrier_out':'heat_ehcp',
                },
            'constraints':{
                'energy_eff':self._eta,
                'lifetime':self._lifetime,
                },
            'costs':{
                'monetary':{
                    'om_con':0.0, # costs are reflected in oil_supply
                    'interest_rate':self._interest_rate,
                    },
                }
            }
        
        return tech_groups_dict
        
    def create_techs_dict(
            self,
            techs_dict,
            header,
            name,
            color,
            ):
        
        capex = self._capex
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': 'electric_heater_cp'
                },
            'constraints':{
                'energy_cap_max': self._v_h_max,
                },
            'costs':{
                'monetary':{
                    'energy_cap': capex,
                    'om_annual': self._maintenance_cost
                    }
                }
            }
        
        return techs_dict
    


    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_e = init_vals.copy()
        self._v_h = init_vals.copy()
    
    def get_v_h(self):
        if len(self._v_h)==0:
            raise ValueError("v_h_ehcp has not yet been computed!")        
        return self._v_h
    
    def get_u_e(self):
        if len(self._u_e)==0:
            raise ValueError("u_oil_ehcp has not yet been computed!")        
        return self._u_e
        
    
    
    
    
    
    
    
    

