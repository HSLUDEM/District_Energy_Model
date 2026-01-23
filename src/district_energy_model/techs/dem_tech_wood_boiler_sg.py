# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 2025

@author: UeliSchilt

Wood boiler (WB) for central plant (CP). This tech generates steam (high
temperature) from wood-burning. The tech must be coupled with steam_turbine
to generate electricitsy and heat.
"""

# import sys
# import os

# project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# sys.path.insert(0, project_dir)

# import pandas as pd
import numpy as np

from district_energy_model import dem_constants as C
from district_energy_model.techs.dem_tech_core import TechCore

class WoodBoilerSG(TechCore):
    
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
        self.input_carrier = 'wood' 
        self.output_carrier = 'steam'
        
        # Accounting:
        self._u_wd = [] # wood input [kWh]
        self._u_wd_kg = [] # wood input [kg]
        self._v_steam = [] # steam output [kWh]
        
        #----------------------------------------------------------------------
        # Tests:

        if self._eta > 1:
            printout = ('Error in wood boiler input: '
                        'conversion efficiency (eta) cannot be larger than 1!'
                        )
            raise Exception(printout)     
            
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the wood boiler technology properties based on a new tech_dict.
        
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
        self._v_steam_max = tech_dict['kW_h_max']
        self._force_cap_max = tech_dict['force_cap_max']
        self._wood_input_cap_type = tech_dict['wood_input_cap_type']
        self._wood_input_cap_kg = tech_dict['wood_input_cap_kg']
        self._cap_min_use = tech_dict['cap_min_use']
        self._hv_wood = tech_dict['hv_wood_MJpkg']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._capex = tech_dict['capital_cost']
        self._maintenance_cost = tech_dict['maintenance_cost']

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_wd_wbsg'] = self.get_u_wd()
        df['u_wd_wbsg_kg'] = self.get_u_wd_kg()
        df['v_steam_wbsg'] = self.get_v_steam()
        
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
        
        self._u_wd = self._u_wd[:n_hours]
        self._u_wd_kg = self._u_wd_kg[:n_hours]
        self._v_steam = self._v_steam[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_wd = init_vals.copy()
        self._u_wd_kg = init_vals.copy()
        self._v_steam = init_vals.copy()
    
    # def compute_v_h(self, src_h_yr, d_h_profile):

    #     tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
    #     tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
    #     self._v_h = np.array(tmp_df['v_h'])
        
    #     # Compute respective wood input:
    #     self.__compute_u_wd()
        
        
    def update_v_steam(self, v_steam_updated):
        if len(v_steam_updated) != len(self._v_steam):
            raise ValueError("v_steam_updated must have the same length as v_steam!")
        
        self._v_steam = np.array(v_steam_updated)
        
        self.__compute_u_wd()
                
    def __compute_u_wd(self):
        """
        Computes the required wood input based on heat output (kWh).
        """
        
        # Conversion from MJ/kg to kJ/kg:
        hv_wood_kJpkg = self._hv_wood*1000
        
        self._u_wd = np.array(self._v_steam)/self._eta # [kWh]
        self._u_wd_kg = self._u_wd*3600/hv_wood_kJpkg # [kg]
                
    
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['wood_boiler_sg'] = {
            'essentials':{
                'parent':'conversion',
                'carrier_in':'wood',
                'carrier_out':'steam',
                },
            'constraints':{
                'energy_eff':self._eta,
                'lifetime':self._lifetime,
                },
            'costs':{
                'monetary':{
                    'om_con':0.0, # costs are reflected in wood_supply
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
                
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': 'wood_boiler_sg'
                },
            'constraints':{
                'energy_cap_max': self._v_steam_max,
                'energy_cap_min_use': self._cap_min_use,
                },
            'costs':{
                'monetary':{
                    'energy_cap': self._capex,
                    'om_annual': self._maintenance_cost

                    }
                }
            }
        
        if self._force_cap_max:
            techs_dict[header]['constraints']['energy_cap_equals']\
                = self._v_steam_max
                
        # Input capacity (kg wood):
        if self._wood_input_cap_type == 'free':
            pass
        
        elif self._wood_input_cap_type == 'max':
            resource_cap_kg = self._wood_input_cap_kg
            resource_cap_MJ = resource_cap_kg*self._hv_wood
            resource_cap_kWh = resource_cap_MJ*C.CONV_MJ_to_kWh
            resource_cap_kW = resource_cap_kWh/8760
            output_cap_kW = resource_cap_kW*self._eta
            
            techs_dict[header]['constraints']['energy_cap_max']\
                = output_cap_kW
                
        elif self._wood_input_cap_type == 'fixed':    
            resource_cap_kg = self._wood_input_cap_kg
            resource_cap_MJ = resource_cap_kg*self._hv_wood
            resource_cap_kWh = resource_cap_MJ*C.CONV_MJ_to_kWh
            resource_cap_kW = resource_cap_kWh/8760
            output_cap_kW = resource_cap_kW*self._eta
            
            techs_dict[header]['constraints']['energy_cap_equals']\
                = output_cap_kW
         
        return techs_dict
    
    # def create_techs_dict_clustering(
    #         self,
    #         techs_dict,
    #         # tech_dict,
    #         name = 'Wood Boiler CP',
    #         color = '#8C3B0C',
    #         capex = 0
    #         ):
        
    #     techs_dict['wood_boiler_sg'] = {
    #         'essentials':{
    #             'name': name,
    #             'color': color,
    #             'parent':'conversion',
    #             'carrier_in':'wood',
    #             'carrier_out':'steam',
    #             },
    #         'constraints':{
    #             'energy_eff':self._eta,
    #             'lifetime':self._lifetime,
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'om_con':0.0, # costs are reflected in wood_supply
    #                 'interest_rate':self._interest_rate,
    #                 'energy_cap': capex
    #                 },
    #             }
    #         }
        
    #     return techs_dict
    
    def get_v_steam(self):
        self.len_test(self._v_steam)
        return self._v_steam
    
    def get_u_wd(self):
        self.len_test(self._u_wd)
        return self._u_wd
    
    def get_u_wd_kg(self):
        self.len_test(self._u_wd_kg)
        return self._u_wd_kg
    
