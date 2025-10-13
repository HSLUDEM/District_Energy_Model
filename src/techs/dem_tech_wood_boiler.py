# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:26:41 2024

@author: UeliSchilt
"""

import pandas as pd
import numpy as np
import dem_constants as C
from techs.dem_tech_core import TechCore

class WoodBoiler(TechCore):
    
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
        self.output_carrier = 'heat'
        
        # Accounting:
        self._u_wd = [] # wood input [kWh]
        self._u_wd_kg = [] # wood input [kg]
        self._v_h = [] # heat output [kWh]
        self._v_co2 = []
        
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
        self._v_h_max = tech_dict['kW_th_max']
        self._hv_wood = tech_dict['hv_wood_MJpkg']
        self._replacement_factor = tech_dict['replacement_factor']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        self._capex = tech_dict['capex']
        self._capex_one_to_one_replacement = tech_dict['capex_one_to_one_replacement']
        self._fixed_demand_share = tech_dict['fixed_demand_share']
        self._fixed_demand_share_val = tech_dict['fixed_demand_share_val']
        self._only_allow_existing = tech_dict['only_allow_existing']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._power_up_for_replacement = 0.0

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_wd_wb'] = self.get_u_wd()
        df['u_wd_wb_kg'] = self.get_u_wd_kg()
        df['v_h_wb'] = self.get_v_h()
        df['v_co2_wb'] = self.get_v_co2()
        
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
        
        # Compute respective wood input:
        self.__compute_u_wd()
        
        self.__compute_v_co2()
        
    def update_v_h(self, v_h_updated):
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
        
        self._v_h = np.array(v_h_updated)
        
        self.__compute_u_wd()
        
        self.__compute_v_co2()
        
    def __compute_u_wd(self):
        """
        Computes the required wood input based on heat output (kWh).
        """
        
        # Conversion from MJ/kg to kJ/kg:
        hv_wood_kJpkg = self._hv_wood*1000
        
        self._u_wd = np.array(self._v_h)/self._eta # [kWh]
        self._u_wd_kg = self._u_wd*3600/hv_wood_kJpkg # [kg]
        
    def __compute_v_co2(self):
        self.len_test(self._v_h)        
        self._v_co2 = self._v_h*self.__tech_dict['co2_intensity']
        
    
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['wood_boiler'] = {
            'essentials':{
                'parent':'conversion',
                'carrier_in':'wood',
                'carrier_out':'heat',
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
                'parent': 'wood_boiler'
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
            name = 'Wood Boiler',
            color = '#8C3B0C',
            capex = 0
            ):
        
        techs_dict['wood_boiler'] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent':'conversion',
                'carrier_in':'wood',
                'carrier_out':'heat',
                },
            'constraints':{
                'energy_eff':self._eta,
                'lifetime':self._lifetime,
                },
            'costs':{
                'monetary':{
                    'om_con':0.0, # costs are reflected in wood_supply
                    'interest_rate':self._interest_rate,
                    'energy_cap': capex
                    },
                'emissions_co2':{
                    'om_prod':self._co2_intensity,
                    }
                }
            }
        
        return techs_dict
    
    def get_replacement_factor(self):
        return self._replacement_factor
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
    
    def get_u_wd(self):
        self.len_test(self._u_wd)
        return self._u_wd
    
    def get_u_wd_kg(self):
        self.len_test(self._u_wd_kg)
        return self._u_wd_kg
    
    def get_v_co2(self):
        self.len_test(self._v_co2)
        return self._v_co2
    
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

    # @staticmethod
    # def get_u_wd(v_h_wb, eta):
    #     """
    #     Computes the required wood input (kWh) based on heat output (kWh).
    #     Function is used to compute base scenario.

    #     Parameters
    #     ----------
    #     v_h_wb : pandas dataseries
    #         Timeseries of heat output from wood boiler.

    #     Returns
    #     -------
    #     u_wd : pandas dataseries
    #         Timeseries of wood input [kWh].

    #     """
    #     u_wd = v_h_wb/eta # [kg]
        
    #     return u_wd
        
    # @staticmethod
    # def convert_price_CHFpkg_to_CHFpkWh(price_CHFpkg, hv_wood_MJpkg):
        
    #     hv_wood_kWhpkg = hv_wood_MJpkg*C.CONV_MJ_to_kWh
        
    #     price_CHFpkWh = price_CHFpkg/hv_wood_kWhpkg
        
    #     return price_CHFpkWh
    
    # @staticmethod
    # def unit_conversion_nparray_kWh_to_kg(nparray_kWh, hv_wood_MJpkg):
    #     """
    #     Return array of values converted from [kWh] to [kg] based on heating
    #     value.

    #     Parameters
    #     ----------
    #     nparray_kWh : numpy array
    #         Timeseries values of wood in units of [kWh].
    #     hv_wood_MJpkg : float
    #         Lower heating value of wood [MJ/kg].

    #     Returns
    #     -------
    #     nparray_kg : numpy array
    #         Timeseries values of wood in units of [kg].
            
    #     """
        
    #     # list to store converted values:
    #     lst_kg = []
        
    #     for val_kWh in nparray_kWh:
    #         val_MJ = val_kWh*C.CONV_kWh_to_MJ
    #         val_kg = val_MJ/hv_wood_MJpkg
    #         lst_kg.append(val_kg)
            
    #     # Convert list back to numpy array:
    #     nparray_kg = np.asarray(lst_kg)
        
    #     return nparray_kg