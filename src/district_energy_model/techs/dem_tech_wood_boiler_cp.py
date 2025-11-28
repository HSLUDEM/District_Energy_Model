# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:23:54 2024

Wood boiler central plant. Large wood boiler to provide heat
to a district heating network. Unlike WBSG, this tech
does not generate steam.

@author: UeliSchilt
"""

import pandas as pd
import numpy as np

from district_energy_model import dem_constants as C
from district_energy_model.techs.dem_tech_core import TechCore

class WoodBoilerCP(TechCore):
    
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
        self.input_carrier = 'wood' 
        self.output_carrier = 'heat_wbcp'
        
        # Accounting:
        self._u_wd = [] # oil input [kWh]
        self._u_wd_kg = [] # oil input [kg]
        self._v_h = [] # heat output [kWh]
        self._v_co2 = []
        
        #----------------------------------------------------------------------
        # Tests:

        if self._eta > 1:
            printout = ('Error in wood boiler central plant input: '
                        'conversion efficiency (eta) cannot be larger than 1!'
                        )
            raise Exception(printout)
            
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the oil boiler technology properties based on a new tech_dict.
        
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
        self._hv_wood = tech_dict['hv_wood_MJpkg']
        # self._replacement_factor = tech_dict['replacement_factor']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        self._capex = tech_dict['capex']
        self._maintenance_cost = tech_dict['maintenance_cost']
        # self._fixed_demand_share = tech_dict['fixed_demand_share']
        # self._fixed_demand_share_val = tech_dict['fixed_demand_share_val']
        # self._only_allow_existing = tech_dict['only_allow_existing']
        
        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_wd_wbcp'] = self.get_u_wd()
        df['u_wd_wbcp_kg'] = self.get_u_wd_kg()
        df['v_h_wbcp'] = self.get_v_h()
        df['v_co2_wbcp'] = self.get_v_co2()
        
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
        self._v_h = self._v_h[:n_hours]
        self._v_co2 = self._v_co2[:n_hours]
    
    def compute_v_h(self, src_h_yr, d_h_profile):

        tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
        tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
        self._v_h = np.array(tmp_df['v_h'])
        
        # Compute respective oil input:
        self.__compute_u_wd()
        
        # Compute co2:
        self.__compute_v_co2()
        
    def update_v_h(self, v_h_updated):
        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
        
        self._v_h = np.array(v_h_updated)
        
        self.__compute_u_wd()
        
        self.__compute_v_co2()
        
    def __compute_u_wd(self):
        """
        Compute the required oil input (kg) based on heat output (kWh).
        """        
        # Conversion from MJ/kg to kJ/kg:
        hv_wood_kJpkg = self._hv_wood*1000
        
        self._u_wd = np.array(self._v_h)/self._eta # [kWh]
        self._u_wd_kg = self._u_wd*3600/hv_wood_kJpkg # [kg]
        
    def __compute_v_co2(self):        
        self._v_co2 = self._v_h*self.__tech_dict['co2_intensity']
            
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['wood_boiler_cp'] = {
            'essentials':{
                'parent':'conversion',
                'carrier_in':'wood',
                'carrier_out':'heat_wbcp',
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
                'emissions_co2':{
                    'om_prod':self._co2_intensity,
                    }
                }
            }
        
        return tech_groups_dict
        
    def create_techs_dict(
            self,
            techs_dict,
            header,
            name,
            color,
            # energy_cap,
            # capex_0=False,
            ):
        
        capex = self._capex
        # if capex_0==False:
            # capex = self._capex
        # elif capex_0==True:
            # capex = 0
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': 'wood_boiler_cp'
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
    
    def create_techs_dict_clustering(
            self,
            techs_dict,
            # tech_dict,
            name = 'Wood Boiler CP',
            color = '#8E2999',
            capex = 0
            ):
        
        techs_dict['wood_boiler_cp'] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent':'conversion',
                'carrier_in':'wood',
                'carrier_out':'heat_wbcp',
                },
            'constraints':{
                'energy_eff':self._eta,
                'lifetime':self._lifetime,
                },
            'costs':{
                'monetary':{
                    'om_con':0.0, # costs are reflected in oil_supply
                    'interest_rate':self._interest_rate,
                    'energy_cap': capex
                    },
                'emissions_co2':{
                    'om_prod':self._co2_intensity,
                    }
                }
            }
        
        return techs_dict
        


    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_wd = init_vals.copy()
        self._u_wd_kg = init_vals.copy()
        self._v_h = init_vals.copy()
        self._v_co2 = init_vals.copy()
    
    def get_v_h(self):
        if len(self._v_h)==0:
            raise ValueError("v_h_wbcp has not yet been computed!")        
        return self._v_h
    
    def get_u_wd(self):
        if len(self._u_wd)==0:
            raise ValueError("u_wd_wbcp has not yet been computed!")        
        return self._u_wd
    
    def get_u_wd_kg(self):
        if len(self._u_wd_kg)==0:
            raise ValueError("u_wd_wbcp_kg has not yet been computed!")        
        return self._u_wd_kg
    
    def get_v_co2(self):
        if len(self._v_co2)==0:
            raise ValueError("v_co2_wbcp has not yet been computed!")            
        return self._v_co2
    
    # def get_fixed_demand_share(self):
    #     return self._fixed_demand_share
    
    # def get_fixed_demand_share_val(self):
    #     self.num_test(self._fixed_demand_share_val)
    #     return self._fixed_demand_share_val
    
    # def get_only_allow_existing(self):
    #     return self._only_allow_existing
    
    
    
    
    
    
    
    
    
    
    

