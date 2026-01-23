# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:23:54 2024

Oil boiler central plant. Large oil boiler connected to the district heating
network, mostly to provide peak heat. 

@author: UeliSchilt
"""

import pandas as pd
import numpy as np

from district_energy_model import dem_constants as C
from district_energy_model.techs.dem_tech_core import TechCore

class OilBoilerCP(TechCore):
    
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
        self.input_carrier = 'oil' 
        self.output_carrier = 'heat_obcp'
        
        # Accounting:
        self._u_oil = [] # oil input [kWh]
        self._u_oil_kg = [] # oil input [kg]
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
        self._hv_oil = tech_dict['hv_oil_MJpkg']
        self._oil_price_CHFpl = tech_dict['oil_price_CHFpl']
        # self._replacement_factor = tech_dict['replacement_factor']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._capex = tech_dict['capex']
        self._maintenance_cost = tech_dict['maintenance_cost']
        # self._fixed_demand_share = tech_dict['fixed_demand_share']
        # self._fixed_demand_share_val = tech_dict['fixed_demand_share_val']
        # self._only_allow_existing = tech_dict['only_allow_existing']
        
        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_oil_obcp'] = self.get_u_oil()
        df['u_oil_obcp_kg'] = self.get_u_oil_kg()
        df['v_h_obcp'] = self.get_v_h()
        
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
        
        self._u_oil = self._u_oil[:n_hours]
        self._u_oil_kg = self._u_oil_kg[:n_hours]
        self._v_h = self._v_h[:n_hours]
    
    def compute_v_h(self, src_h_yr, d_h_profile):

        tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
        tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
        self._v_h = np.array(tmp_df['v_h'])
        
        # Compute respective oil input:
        self.__compute_u_oil()
                
    def update_v_h(self, v_h_updated):
        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
        
        self._v_h = np.array(v_h_updated)
        
        self.__compute_u_oil()
                
    def __compute_u_oil(self):
        """
        Compute the required oil input (kg) based on heat output (kWh).
        """        
        # Conversion from MJ/kg to kJ/kg:
        hv_oil_kJpkg = self._hv_oil*1000
        
        self._u_oil = np.array(self._v_h)/self._eta # [kWh]
        self._u_oil_kg = np.array(self._v_h)*3600/(self._eta*hv_oil_kJpkg) # [kg]
                
    # @staticmethod
    # def get_u_oil(hv_oil_MJpkg, v_h_ob):
    #     """
    #     Computes the required oil input (kg) based on heat output (kWh).
    #     Function is used to compute base scenario.

    #     Parameters
    #     ----------
    #     hv_oil_MJpkg : float
    #         lower heating value of oil [MJ/kg].
    #     v_h_ob : pandas dataseries
    #         Timeseries of heat output from oil boiler.

    #     Returns
    #     -------
    #     u_oil : pandas dataseries
    #         Timeseries of oil input [kg].
    #     """
        
    #     # Conversion from MJ/kg to kJ/kg:
    #     hv_oil_kJpkg = hv_oil_MJpkg*1000
        
    #     u_oil = v_h_ob*3600/hv_oil_kJpkg # [kg]
        
    #     return u_oil
        
    @staticmethod
    def convert_price_CHFpl_to_CHFpkWh(price_CHFpl, hv_oil_MJpkg):
        """
        Return the price for purchasing oil in units of CHF/kWh.

        Parameters
        ----------
        price_CHFpl : float
            Purchasing price of oil in units of CHF/l.
        hv_oil_MJpkg : TYPE
            Heating value (lower) of oil [MJ/kg].

        Returns
        -------
        price_CHFpkWh : float
            Purchasing price of oil in units of CHF/kWh.

        """
        
        hv_oil_MJpl = hv_oil_MJpkg*C.DENSITY_oil_kgpl # [MJ/l]
        
        hv_oil_kWhpl = hv_oil_MJpl*C.CONV_MJ_to_kWh
        
        price_CHFpkWh = price_CHFpl/hv_oil_kWhpl
        
        return price_CHFpkWh
    
    @staticmethod
    def unit_conversion_nparray_kWh_to_kg(nparray_kWh, hv_oil_MJpkg):
        """
        Return array of values converted from [kWh] to [kg] based on heating
        value.

        Parameters
        ----------
        nparray_kWh : numpy array
            Timeseries values of oil in units of [kWh].
        hv_oil_MJpkg : float
            Lower heating value of oil [MJ/kg].

        Returns
        -------
        nparray_kg : numpy array
            Timeseries values of oil in units of [kg].
            
        """
        
        # list to store converted values:
        lst_kg = []
        
        for val_kWh in nparray_kWh:
            val_MJ = val_kWh*C.CONV_kWh_to_MJ
            val_kg = val_MJ/hv_oil_MJpkg
            lst_kg.append(val_kg)
            
        # Convert list back to numpy array:
        nparray_kg = np.asarray(lst_kg)
        
        return nparray_kg
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['oil_boiler_cp'] = {
            'essentials':{
                'parent':'conversion',
                'carrier_in':'oil',
                'carrier_out':'heat_obcp',
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
                'parent': 'oil_boiler_cp'
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
            name = 'Oil Boiler CP',
            color = '#8E2999',
            capex = 0
            ):
        
        techs_dict['oil_boiler_cp'] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent':'conversion',
                'carrier_in':'oil',
                'carrier_out':'heat_obcp',
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
        


    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_oil = init_vals.copy()
        self._u_oil_kg = init_vals.copy()
        self._v_h = init_vals.copy()


    # def create_oil_supply(
    #         self,
    #         techs_dict,
    #         # tech_dict,
    #         color
    #         ):

    #     price_CHFpl=self._oil_price_CHFpl
    #     hv_oil_MJpkg=self._hv_oil
    #     hv_oil_MJpl = hv_oil_MJpkg*C.DENSITY_oil_kgpl # [MJ/l]
    #     hv_oil_kWhpl = hv_oil_MJpl*C.CONV_MJ_to_kWh
    #     price_CHFpkWh = price_CHFpl/hv_oil_kWhpl
        
        
    #     techs_dict['oil_supply'] = {
    #         'essentials':{
    #             'name':'Oil Supply',
    #             'color':color,
    #             'parent':'supply',
    #             'carrier':'oil',
    #             },
    #         'constraints':{
    #             'resource':'inf',
    #             'energy_cap_min':'inf', # ensures that supply is always large enough
    #             'lifetime':1000
    #             },
    #         'costs':{
    #             'monetary':{
    #                 'om_con':price_CHFpkWh,
    #                 'interest_rate':0.0
    #                 },
    #             }
    #         }
        
    #     return techs_dict
    
    def get_v_h(self):
        if len(self._v_h)==0:
            raise ValueError("v_h_obcp has not yet been computed!")        
        return self._v_h
    
    def get_u_oil(self):
        if len(self._u_oil)==0:
            raise ValueError("u_oil_obcp has not yet been computed!")        
        return self._u_oil
    
    def get_u_oil_kg(self):
        if len(self._u_oil_kg)==0:
            raise ValueError("u_oil_obcp_kg has not yet been computed!")        
        return self._u_oil_kg
            
    def get_fixed_demand_share(self):
        return self._fixed_demand_share
    
    def get_fixed_demand_share_val(self):
        self.num_test(self._fixed_demand_share_val)
        return self._fixed_demand_share_val
    
    def get_only_allow_existing(self):
        return self._only_allow_existing
    
    
    
    
    
    
    
    
    
    
    

