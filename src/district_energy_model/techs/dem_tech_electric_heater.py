# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:21:45 2024

@author: UeliSchilt
"""

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore

class ElectricHeater(TechCore):
    
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
        self.input_carrier = 'electricity'
        self.output_carrier = 'heat'
        
        # Accounting:
        self._u_e = [] # electric heater input (electricity)
        self._v_h = [] # electric heater output (heat)
        
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
        self._v_max = tech_dict['kW_max'] # Max electric and thermal capacity
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._capex = tech_dict['capex']
        self._fixed_demand_share = tech_dict['fixed_demand_share']
        self._fixed_demand_share_val = tech_dict['fixed_demand_share_val']
        self._replacement_factor = tech_dict['replacement_factor']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._power_up_for_replacement = 0.0

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_e_eh'] = self.get_u_e()
        df['v_h_eh'] = self.get_v_h()
        
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

    def compute_v_h(self, src_h_yr, d_h_profile):

        tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
        tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
        self._v_h = np.array(tmp_df['v_h'])
        self._u_e = self._v_h # Conversion efficiency = 1.0
        
        
    def update_v_h(
            self,
            v_h_updated
            ):
        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
            
        self._v_h = np.array(v_h_updated)
        self._u_e = self._v_h # Conversion efficiency = 1.0
        
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['electric_heater'] = {
            'essentials':{
                'parent':'conversion',
                'carrier_in':'electricity',
                'carrier_out':'heat'
                },
            'constraints':{
                'energy_eff':1,
                'lifetime':self._lifetime
                },
            'costs':{
                'monetary':{
                    'om_con':0.0, # reflected in the cost of electricity
                    'interest_rate':self._interest_rate,
                    },
                }
            }
        
        return tech_groups_dict
        
    def create_techs_dict(self, 
                          techs_dict,
                          header,
                          name, 
                          color, 
                          energy_cap,
                          capex_0=False,
                          energy_scaling_factor = 1.0
                          ):
        
        if capex_0==False:
            capex = self._capex
        elif capex_0==True:
            capex = 0
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'parent': 'electric_heater',
                'color': color
                },
            'constraints':{
                'energy_cap_max': energy_cap / energy_scaling_factor
                },
            'costs':{
                'monetary':{
                    'energy_cap': capex * energy_scaling_factor,
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    }
                }
            }
        return techs_dict
    
    def create_techs_dict_clustering(
            techs_dict,
            tech_dict,
            name = 'Electric Heater', 
            color = '#F27D52',
            capex = 0
            ):
        
        techs_dict['electric_heater'] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent':'conversion',
                'carrier_in':'electricity',
                'carrier_out':'heat'
                },
            'constraints':{
                'energy_eff':1,
                'lifetime':tech_dict['lifetime']
                },
            'costs':{
                'monetary':{
                    'om_con':0.0, # reflected in the cost of electricity
                    'interest_rate':tech_dict['interest_rate'],
                    'energy_cap': capex
                    },
                }
            }
        return techs_dict
    
    def get_u_e(self):
        self.len_test(self._u_e)
        return self._u_e
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
        
    def get_fixed_demand_share(self):
        return self._fixed_demand_share
    
    def get_fixed_demand_share_val(self):
        self.num_test(self._fixed_demand_share_val)
        return self._fixed_demand_share_val
        
    def get_power_up_for_replacement(self):
        return self._power_up_for_replacement
    
    def set_power_up_for_replacement(self, value):
        self._power_up_for_replacement = value

    
    
    
    
    
    
    
    
        