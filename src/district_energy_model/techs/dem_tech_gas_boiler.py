# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:25:10 2024

@author: UeliSchilt
"""

import pandas as pd
import numpy as np

from district_energy_model import dem_constants as C
from district_energy_model.techs.dem_tech_core import TechCore

class GasBoiler(TechCore):
    
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
        self.input_carrier = 'gas' 
        self.output_carrier = 'heat'
        
        # Accounting:
        self._u_gas = [] # gas input [kWh]
        self._u_gas_kg = [] # gas input [kg]
        self._v_h = [] # heat output [kWh]
        
        #----------------------------------------------------------------------
        # Tests:

        if self._eta > 1:
            printout = ('Error in gas boiler input: '
                        'conversion efficiency (eta) cannot be larger than 1!'
                        )
            raise Exception(printout)
            
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the gas boiler technology properties based on a new tech_dict.
        
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
        self._hv_gas = tech_dict['hv_gas_MJpkg']
        self._gas_price_CHFpkWh = tech_dict['gas_price_CHFpkWh']
        self._replacement_factor = tech_dict['replacement_factor']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._capex = tech_dict['capex']
        self._capex_one_to_one_replacement = tech_dict['capex_one_to_one_replacement']
        self._fixed_demand_share = tech_dict['fixed_demand_share']
        self._fixed_demand_share_val = tech_dict['fixed_demand_share_val']
        self._only_allow_existing = tech_dict['only_allow_existing']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._power_up_for_replacement = 0.0

        # Update tech dict:
        self.__tech_dict = tech_dict
    
    def update_df_results(self, df):
        
        df['u_gas_gb'] = self.get_u_gas()
        df['u_gas_gb_kg'] = self.get_u_gas_kg()
        df['v_h_gb'] = self.get_v_h()
        
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
        
        self._u_gas = self._u_gas[:n_hours]
        self._u_gas_kg = self._u_gas_kg[:n_hours]
        self._v_h = self._v_h[:n_hours]
    
    def compute_v_h(self, src_h_yr, d_h_profile):

        tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
        tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
        self._v_h = np.array(tmp_df['v_h'].tolist())
        
        # Compute respective gas input:
        self.__compute_u_gas()
                
    def update_v_h(self, v_h_updated):
        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
        
        self._v_h = np.array(v_h_updated)
        
        self.__compute_u_gas()
         
    def __compute_u_gas(self):
        """
        Computes the required gas input based on heat output (kWh).
        """
        
        # Conversion from MJ/kg to kJ/kg:
        hv_gas_kJpkg = self._hv_gas*1000
                
        self._u_gas = np.array(self._v_h)/self._eta # [kWh]
        self._u_gas_kg = np.array(self._v_h)*3600/(self._eta*hv_gas_kJpkg) # [kg]
                
    # @staticmethod
    # def get_u_gas(hv_gas_MJpkg, v_h_gb):
    #     """
    #     Computes the required gas input based on heat output (kWh).
    #     Function is used to compute base scenario.

    #     Parameters
    #     ----------
    #     hv_gas_MJpkg : float
    #         lower heating value of gas [MJ/kg].
    #     v_h_gb : pandas dataseries
    #         Timeseries of heat output from gas boiler.

    #     Returns
    #     -------
    #     u_gas : pandas dataseries
    #         Timeseries of gas input [kg].
    #     """
        
    #     # Conversion from MJ/kg to kJ/kg:
    #     hv_gas_kJpkg = hv_gas_MJpkg*1000
        
    #     u_gas = v_h_gb*3600/hv_gas_kJpkg # [kg]
        
    #     return u_gas
    
    @staticmethod
    def unit_conversion_nparray_kWh_to_kg(nparray_kWh, hv_gas_MJpkg):
        """
        Return array of values converted from [kWh] to [kg] based on heating
        value.

        Parameters
        ----------
        nparray_kWh : numpy array
            Timeseries values of gas in units of [kWh].
        hv_gas_MJpkg : float
            Lower heating value of gas [MJ/kg].

        Returns
        -------
        nparray_kg : numpy array
            Timeseries values of gas in units of [kg].

        """
        
        # list to store converted values:
        lst_kg = []
        
        for val_kWh in nparray_kWh:
            val_MJ = val_kWh*C.CONV_kWh_to_MJ
            val_kg = val_MJ/hv_gas_MJpkg
            lst_kg.append(val_kg)
            
        # Convert list back to numpy array:
        nparray_kg = np.asarray(lst_kg)
        
        return nparray_kg
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['gas_boiler'] = {
            'essentials':{
                'parent':'conversion',
                'carrier_in':'gas',
                'carrier_out':'heat',
                },
            'constraints':{
                'energy_eff':self._eta,
                'lifetime':self._lifetime,
                },
            'costs':{
                'monetary':{
                    'om_con':0.0, # costs are reflected in gas_supply
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
            energy_cap,
            capex_level = 'full' # 'zero', 'one-to-one-replacement'
            ):
        
        if capex_level=='full':
            capex = self._capex
        elif capex_level=='one-to-one-replacement':
            capex = self._capex_one_to_one_replacement
        elif capex_level=='zero':
            capex = 0
        else:
            raise Exception("Invalid Capex Level. Choose 'full' for new installation capex, "
            "'replacement' for a one-to-one device replacement capex or" \
            " 'zero' for no capex. (Existing and still running devices.) ") 
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': 'gas_boiler'
                },
            'constraints':{
                'energy_cap_max': energy_cap
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
            name = 'Gas Boiler',
            color = '#001A1A',
            capex = 0
            ):
        
        techs_dict['gas_boiler'] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent':'conversion',
                'carrier_in':'gas',
                'carrier_out':'heat',
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
                }
            }
        
        return techs_dict
        
    # def create_gas_supply(
    #         self,
    #         techs_dict,
    #         color,
    #         ):
    #     techs_dict['gas_supply'] = {
    #         'essentials':{
    #             'name':'Gas Supply',
    #             'color':color,
    #             'parent':'supply',
    #             'carrier':'gas',
    #             },
    #         'constraints':{
    #             'resource':'inf',
    #             'lifetime':1000
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'om_con':self._gas_price_CHFpkWh,
    #                 'interest_rate':0.0
    #                 },
    #             }
    #         }
        
    #     return techs_dict
    
    def get_v_h(self):        
        if len(self._v_h)==0:
            raise ValueError("v_h_gb must be computed first!")        
        return self._v_h
    
    def get_u_gas(self):
        if len(self._u_gas)==0:
            raise ValueError()
        return self._u_gas
    
    def get_u_gas_kg(self):
        if len(self._u_gas_kg)==0:
            raise ValueError()
        return self._u_gas_kg
            
    def get_fixed_demand_share(self):
        return self._fixed_demand_share
    
    def get_fixed_demand_share_val(self):
        self.num_test(self._fixed_demand_share_val)
        return self._fixed_demand_share_val
    
    def get_only_allow_existing(self):
        return self._only_allow_existing
  
    def get_power_up_for_replacement(self):
        return self._power_up_for_replacement
    
    def set_power_up_for_replacement(self, value):
        self._power_up_for_replacement = value

    def get_v_h_max(self):
        return self._v_h_max
