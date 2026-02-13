# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:20:25 2024

@author: UeliSchilt
"""

import numpy as np
import pandas as pd
from techs.dem_tech_core import TechCore

class HeatPumpCP(TechCore):
    
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
        self._input_carrier_2 = 'heat_env'
        self._output_carrier = 'heat_hpcp'
        
        # Accounting:
        self._u_e = [] # heat pump input - electricity
        self._u_h = [] # heat pump input - heat from environment
        self._v_h = [] # heat pump output (heat)
        self._v_co2 = []
        
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
        self._hpcp_cop = tech_dict['cop'] # Coefficient of performance
        self._v_h_max = tech_dict['kW_th_max'] # Max thermal capacity
        self._force_cap_max = tech_dict['force_cap_max']
        self._cap_min_use = tech_dict['cap_min_use']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        self._capex = tech_dict['capital_cost']
        self._maintenance_cost = tech_dict['maintenance_cost']
        
        
        
    def update_df_results(self, df):
        
        # super().update_df_results(df)
        
        df['u_e_hpcp'] = self.get_u_e()
        df['u_h_hpcp'] = self.get_u_h()
        df['v_h_hpcp'] = self.get_v_h()
        df['v_co2_hpcp'] = self.get_v_co2()
        
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
        self._u_h = self._u_h[:n_hours]
        self._v_h = self._v_h[:n_hours]
        self._v_co2 = self._v_co2[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_e = init_vals.copy()
        self._u_h = init_vals.copy()
        self._v_h = init_vals.copy()
        self._v_co2 = init_vals.copy()
        
    
    # def compute_v_h(self, src_h_yr, d_h_profile):

    #     tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
    #     tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
    #     self._v_h = np.array(tmp_df['v_h'].tolist())
                
    #     # Re-calculate:
    #     self.__compute_u_e()
    #     self.__compute_u_h()
    #     self.__compute_v_co2()

        
    def update_v_h(self, v_h_updated):
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
        
        self._v_h = np.array(v_h_updated)
        
        self.__compute_u_e()
        self.__compute_u_h()
        self.__compute_v_co2()
        
    # def update_v_h_i(self, i, val):
    #     self.num_test(val)
    #     self._v_h[i] = val
        
    #     self.__compute_u_e_i(i)
    #     self.__compute_u_h_i(i)
    #     self.__compute_v_co2_i(i)
    
    def get_hpcp_cop(self):
        self.num_test(self._hpcp_cop)
        return self._hpcp_cop
                
    def get_v_h(self):
        if len(self._v_h)==0:
            raise ValueError()
        return self._v_h
    
    def get_u_e(self):
        if len(self._u_e)==0:
            raise ValueError()
        return self._u_e
    
    def get_u_h(self):
        if len(self._u_h)==0:
            raise ValueError()
        return self._u_h
    
    def get_v_co2(self):
        if len(self._v_co2)==0:
            raise ValueError()
        return self._v_co2
        
    # def heat_output(self,u_e_i):
        
    #     """
    #     Computes the heat output of one timestep i based on the electricity
    #     input at timestep i.
        
    #     Parameters
    #     ----------
    #     u_e_i : float
    #         Electricity input to heat pump [kWh].

    #     Returns
    #     -------
    #     float
    #         Heat output from heat pump [kWh]
    #     """
        
    #     v_h_i = u_e_i*self._hpcp_cop
        
    #     return v_h_i
    
    # def electricity_input(self,v_h_i):
        
    #     """
    #     Computes the electricity input of one timestep i based on the heat
    #     output at timestep i.
        
    #     Parameters
    #     ----------
    #     v_h_i : float
    #         Heat output from heat pump [kWh].

    #     Returns
    #     -------
    #     float
    #         Electricity input heat pump [kWh]
    #     """
        
    #     u_e_i = v_h_i/self._hpcp_cop
        
    #     return u_e_i
    
    # def electricity_input_df(self,v_h_hpcp):
        
    #     """
    #     Computes the electricity input of based on the heat
    #     output of a timeseries.
        
    #     Parameters
    #     ----------
    #     v_h_hpcp : column of pandas dataframe
    #         Heat output from heat pump [kWh].

    #     Returns
    #     -------
    #     pandas dataframe column
    #         Electricity input heat pump [kWh]
    #     """
        
    #     u_e_hpcp = v_h_hpcp/self._hpcp_cop
        
    #     return u_e_hpcp
    
    def __compute_u_e(self):
        
        """
        Computes the hourly electricity input (u_e) to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_e = self._v_h/self._hpcp_cop
   
    def __compute_u_h(self):
        
        """
        Computes the hourly heat input (u_h) from the environment to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_h = self._v_h*(1-1/self._hpcp_cop)
        
    def __compute_v_co2(self):
        self._v_co2 = self._v_h*self.__tech_dict['co2_intensity']
        
    # def __compute_u_e_i(self,i):
        
    #     """
    #     Computes the hourly electricity input (u_e) to the
    #     heat pump based on the thermal output using a fixed cop.
    #     """
        
    #     self._u_e[i] = self._v_h[i]/self._hpcp_cop
   
    # def __compute_u_h_i(self,i):
        
    #     """
    #     Computes the hourly heat input (u_h) from the environment to the
    #     heat pump based on the thermal output using a fixed cop.
    #     """
        
    #     self._u_h[i] = self._v_h[i]*(1-1/self._hpcp_cop)
        
    # def __compute_v_co2_i(self,i):
    #     self._v_co2[i] = self._v_h[i]*self.__tech_dict['co2_intensity']
        
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['heat_pump_cp'] = {
            'essentials':{
                'parent':'conversion_plus',
                'carrier_in':self._input_carrier_1,
                'carrier_out':self._output_carrier,
                'primary_carrier_out':self._output_carrier,
                },
            'constraints':{
                'energy_eff':1,
                'carrier_ratios':{
                    'carrier_out':{
                        self._output_carrier:self._hpcp_cop
                        }
                    },
                'lifetime': self._lifetime
                },
            'costs':{
                'monetary':{
                    'om_con': 0.0, # this is reflected in the cost of the electricity
                    'interest_rate':self._interest_rate
                    },
                'emissions_co2':{
                    'om_prod':self._co2_intensity
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
            ):
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': 'heat_pump_cp',
                },
            'constraints':{
                'energy_cap_max': self._v_h_max,
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
                = self._v_h_max
        
        # additional_techs_label_list = []
        
        # if create_tes_hpcp_hub:
        #     techs_dict['heat_pump_hub'] = {
        #         'essentials':{
        #             'name':'Heat Pump Hub',
        #             'parent':'conversion',
        #             'carrier_in':'heat_hpcp',
        #             'carrier_out':'heat',
        #             },
        #         'constraints':{
        #             'energy_cap_max':'inf',
        #             'energy_eff':1.0, # Here we could account for transmission losses
        #             'lifetime':self._lifetime,
        #             },
        #         'costs':{
        #             'monetary':{
        #                 'om_con': 0.0, # costs are reflected in supply techs
        #                 'interest_rate':0.0,
        #                 },
        #             'emissions_co2':{
        #                 'om_prod':0.0, # emissions are reflected in supply techs
        #                 }
        #             } 
        #         }
        #     additional_techs_label_list.append('heat_pump_hub')            
    
        return techs_dict #, additional_techs_label_list
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    