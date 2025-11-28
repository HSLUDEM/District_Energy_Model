# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:19:13 2024

@author: UeliSchilt
"""

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore

class SolarThermal(TechCore):
    
    """
    Conversion technology: solar thermal.
    
    """
    
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
        self.output_carrier = 'heat'
        
        # Accounting:
        self._v_h = []
        self._v_co2 = []
        
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the solar thermal technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        # Properties:
        self._v_max = tech_dict['kW_th_max']
        self._eta_overall = tech_dict['eta_overall']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        self._capex = tech_dict['capex']
        self._capex_one_to_one_replacement = tech_dict['capex_one_to_one_replacement']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._power_up_for_replacement = 0.0

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['v_h_solar'] = self.get_v_h()
        df['v_co2_solar'] = self.get_v_co2()
        
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
        
        self._v_h = self._v_h[:n_hours]
        self._v_co2 = self._v_co2[:n_hours]
    
    def compute_v_h(self, src_h_yr, d_h_profile):

        tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
        tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
        self._v_h = np.array(tmp_df['v_h'])
        
        self.__compute_v_co2()
        
    def update_v_h(
            self,
            v_h_updated
            ):
        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
            
        self._v_h = np.array(v_h_updated)
        
        self.__compute_v_co2()
        
    def __compute_v_co2(self):        
        self._v_co2 = self._v_h*self.__tech_dict['co2_intensity']
        
    @staticmethod
    def convert_pv_to_thermal(df_pv_kWh, eta_pv, eta_thermal):
        """
        Return values for solar thermal energy equivalent to pv energy under
        same irradiation and area.

        Parameters
        ----------
        df_pv_kWh : pandas dataseries
            Timeseries of solar pv generation (or potential) [kWh].
        eta_pv : float
            Overall conversion efficiency of solar PV system [-].
        eta_thermal : float
            Overall conversion efficiency of solar thermal system [-].

        Returns
        -------
        df_thermal_kWh : pandas dataseries
            Timeseries of solar thermal generation (or potential) [kWh].

        """
        
        df_thermal_kWh = df_pv_kWh/eta_pv*eta_thermal
        
        return df_thermal_kWh
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['solar_thermal'] = {
            'essentials':{
                'parent':'supply_plus',
                'carrier': 'heat'
                },
            'constraints':{
                'resource_unit': 'energy_per_area', # 'energy',
                'parasitic_eff': 1.0, # efficiency is already accounted for in the resource dataseries
                'force_resource': True,
                'lifetime': self._lifetime,
                },
            'costs':{
                'monetary':{
                    'interest_rate':self._interest_rate,
                    'om_con':0.0
                    },
                'emissions_co2':{
                    'om_prod':self._co2_intensity
                    }
                }
            }
        
        return tech_groups_dict
        
    def create_techs_dict(self,
                          techs_dict,
                          header,
                          name, 
                          color, 
                          resource,
                          energy_cap,
                          capex_0=False,
                          ):
        
        if capex_0==False:
            capex = self._capex
        elif capex_0==True:
            capex = 0
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': 'solar_thermal'
                },
            'constraints':{
                'resource': resource,
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
    
    def get_eta_overall(self):
        self.num_test(self._eta_overall)
        return self._eta_overall
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
        
    def get_v_co2(self):
        self.len_test(self._v_co2)
        return self._v_co2
    
    def get_power_up_for_replacement(self):
        return self._power_up_for_replacement
    
    def set_power_up_for_replacement(self, value):
        self._power_up_for_replacement = value

    