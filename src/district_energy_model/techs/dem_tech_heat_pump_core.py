# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:20:25 2024

@author: UeliSchilt
"""

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore

class HeatPumpCore(TechCore):
    
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
        self.__tech_dict = tech_dict
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        self.init_cop_properties(tech_dict)

    def init_cop_properties(self, tech_dict):

        self._cop_mode = tech_dict["cop_mode"]
        self._cop_timeseries_file_path = tech_dict["cop_timeseries_file_path"]
        self._cop_constant_value = tech_dict['cop_constant_value']
        if 'spf_to_target' in tech_dict.keys():
            self._spf_to_target = tech_dict['spf_to_target']

    def compute_cop_timeseries(self, d_h_profile):
        n_hours = len(d_h_profile)
        if self._cop_mode == "constant":
            self._cop = np.array([self._cop_constant_value]*n_hours)
        elif self._cop_mode in ["from_file", "from_file_adjusted_to_spf"]:
            df_from_file = pd.read_feather(self._cop_timeseries_file_path)
            self._cop = np.array(df_from_file["cop"])
            if self._cop_mode == "from_file_adjusted_to_spf":
                self._cop = self._adjust_cop_timeseries_to_spf(self._cop, self._spf_to_target, d_h_profile)
        elif self._cop_mode == 'temperature_based':
            self._cop = self._temperature_based_cop
        else:
            raise ValueError("OTHER OPTIONS NOT YET IMPLEMENTED")
        
    def _adjust_cop_timeseries_to_spf(self, cop, spf_to_target, d_h_profile):
        bedarf = d_h_profile / cop
        spf_at_the_moment = d_h_profile.sum() / (bedarf.sum())
        cop_correction_factor = spf_at_the_moment / spf_to_target
        cop = cop / cop_correction_factor
        return cop

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
        self._cop = self._cop[:n_hours]

    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_e = init_vals.copy()
        self._u_h = init_vals.copy()
        self._v_h = init_vals.copy()

    def compute_v_h(self, src_h_yr, d_h_profile):


        tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
        tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
        self._v_h = np.array(tmp_df['v_h'].tolist())
        
        # Re-calculate:
        self._compute_u_e()
        self._compute_u_h()

    def update_v_h_i(self, i, val):
        self.num_test(val)
        self._v_h[i] = val
        
        self.__compute_u_e_i(i)
        self.__compute_u_h_i(i)


    def update_v_h(self, v_h_updated):
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
        
        self._v_h = np.array(v_h_updated)

        self._compute_u_e()
        self._compute_u_h()

    def get_cop(self):
        # self.num_test(self._hpcp_cop)
        return self._cop
                
    def get_v_h(self):
        if len(self._v_h)==0:
            raise ValueError()
        return self._v_h
    
    def get_u_e(self):
        # print(self._u_e)
        if len(self._u_e)==0:
            raise ValueError()
        return self._u_e
    
    def get_u_h(self):
        if len(self._u_h)==0:
            raise ValueError()
        return self._u_h
    
    def _compute_u_e(self):
        
        """
        Computes the hourly electricity input (u_e) to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_e = self._v_h/self._cop
   
    def _compute_u_h(self):
        
        """
        Computes the hourly heat input (u_h) from the environment to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_h = self._v_h*(1-1/self._cop)
        self._u_h[self._u_h < 0] = 0.0
        
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict[self._label] = {
            'essentials':{
                'parent':'conversion',
                'carrier_in':self._input_carrier,
                'carrier_out':self._output_carrier,
                },
            'constraints':{
                'energy_eff':"df="+self._label+":cop",#self._hpcp_cop,
                'lifetime': self._lifetime
                },
            'costs':{
                'monetary':{
                    'om_con': 0.0, # this is reflected in the cost of the electricity
                    'interest_rate':self._interest_rate
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
            energy_scaling_factor
            ):
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': self._label,
                },
            'constraints':{
                'energy_cap_max': self._v_h_max / energy_scaling_factor if self._v_h_max != 'inf' else 'inf',
                'energy_cap_min_use': self._cap_min_use,
                },
            'costs':{
                'monetary':{
                    'energy_cap': self._capex * energy_scaling_factor,
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    }
                }
            }
        
        if self._force_cap_max:
            techs_dict[header]['constraints']['energy_cap_equals']\
                = self._v_h_max / energy_scaling_factor
            
        return techs_dict

    def __compute_u_e_i(self,i):
        
        """
        Computes the hourly electricity input (u_e) to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_e[i] = self._v_h[i]/self._cop[i]
   
    def __compute_u_h_i(self,i):
        
        """
        Computes the hourly heat input (u_h) from the environment to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_h[i] = self._v_h[i]*(1-1/self._cop[i])
        
    def heat_output(self,u_e_i):
        
        """
        Computes the heat output of one timestep i based on the electricity
        input at timestep i.
        
        Parameters
        ----------
        u_e_i : float
            Electricity input to heat pump [kWh].

        Returns
        -------
        float
            Heat output from heat pump [kWh]
        """
        
        v_h_i = u_e_i*self._cop[i]
        
        return v_h_i

    def electricity_input(self,v_h_i):
        
        """
        Computes the electricity input of one timestep i based on the heat
        output at timestep i.
        
        Parameters
        ----------
        v_h_i : float
            Heat output from heat pump [kWh].

        Returns
        -------
        float
            Electricity input heat pump [kWh]
        """
        
        u_e_i = v_h_i/self._cop[i]
        
        return u_e_i

    def electricity_input_df(self,v_h_hp):
        
        """
        Computes the electricity input of based on the heat
        output of a timeseries.
        
        Parameters
        ----------
        v_h_hp : column of pandas dataframe
            Heat output from heat pump [kWh].

        Returns
        -------
        pandas dataframe column
            Electricity input heat pump [kWh]
        """
        
        u_e_hp = v_h_hp/self._cop
        
        return u_e_hp

    def update_v_h_u_h_u_e(self, v_h_hp, u_h_hp, u_e_hp):
        self._v_h = v_h_hp
        self._u_h = u_h_hp
        self._u_e = u_e_hp
    
    
    
    
    
    
    
    
    
    
    