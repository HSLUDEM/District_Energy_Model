# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:20:25 2024

@author: UeliSchilt
"""

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_heat_pump_core import HeatPumpCore

# class HeatPump(TechCore):
class HeatPump(HeatPumpCore):
    
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
        # self._cop = tech_dict['cop'] # Coefficient of performance
        self.update_tech_properties(tech_dict)
        
        # Carrier types:
        self._input_carrier = 'electricity'
        self._output_carrier = 'heat_hp'
        
        self._label = 'heat_pump'
        self._hublabel = 'heat_pump_hub'
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
        
        self._v_h_max = tech_dict['kW_th_max'] # Max thermal capacity
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        self._capex = tech_dict['capex']
        self._capex_one_to_one_replacement = tech_dict['capex_one_to_one_replacement']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._fixed_demand_share = tech_dict['fixed_demand_share']
        self._fixed_demand_share_val = tech_dict['fixed_demand_share_val']
        self._only_allow_existing = tech_dict['only_allow_existing']
        self._power_up_for_replacement = 0.0
 
        
        
    def update_df_results(self, df):
        
        # super().update_df_results(df)
        
        df['u_e_hp'] = self.get_u_e()
        df['u_h_hp'] = self.get_u_h()
        df['v_h_hp'] = self.get_v_h()
        df['v_co2_hp'] = self.get_v_co2()
        df['cops_hp_new'] = self.get_cops_new()
        df['cops_hp_existing'] = self.get_cops_existing()
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
        self._cops_new = self._cops_new[:n_hours]
        self._cops_existing = self._cops_existing[:n_hours]
        self._cops_one_to_one_replacement = self._cops_one_to_one_replacement[:n_hours]


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

    def create_techs_dict(
            self,
            techs_dict,
            header,
            name,
            color,
            energy_cap,
            create_tesdc_hp_hub=False,
            capex_level='full', # 'zero', 'one-to-one-replacement'
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
        
        cop_df_label = 'heat_pump_cops_new' if capex_level == 'full' else (
            'heat_pump_cops_existing' if capex_level == 'zero' else
            'heat_pump_cops_one_to_one_replacement'
        )


        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': self._label,
                },
            'constraints':{
                'energy_eff':"df="+cop_df_label+":"+cop_df_label,
                'energy_cap_max': energy_cap
                },
            'costs':{
                'monetary':{
                    'energy_cap': capex,
                    'om_annual': self._maintenance_cost
                    }
                }
            }
        
        additional_techs_label_list = []
        
        if create_tesdc_hp_hub:
            techs_dict[self._hublabel] = {
                'essentials':{
                    'name':'Heat Pump Hub',
                    'parent':'conversion',
                    'carrier_in':self._output_carrier,
                    'carrier_out':'heat',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            additional_techs_label_list.append(self._hublabel)            
    
        return techs_dict, additional_techs_label_list
    
    def set_cops_existing(self, cops_existing):
        self._cops_existing = cops_existing
        self._cops_existing[np.isnan(self._cops_existing)] = 1.0

    def set_cops_new(self, cops_new):
        self._cops_new = cops_new
        self._cops_new[np.isnan(self._cops_new)] = 1.0

    def set_cops_one_to_one_replacement(self, cops_one_to_one_replacement):
        self._cops_one_to_one_replacement = cops_one_to_one_replacement
        self._cops_one_to_one_replacement[np.isnan(self._cops_one_to_one_replacement)] = 1.0
        
    def get_cops_existing(self):
        
        return self._cops_existing
    
    def get_cops_new(self):
        
        return self._cops_new
    
    def get_cops_one_to_one_replacement(self):
        
        return self._cops_one_to_one_replacement

    def getRelativeSharesOfHPCategories(self):

        tot_v_h = np.sum(self._v_h)
        v_h_existing_yr = 0.0
        v_h_one_to_one_yr = 0.0
        v_h_new_yr = 0.0

        if tot_v_h <= self._tot_heat_existing:
            

            v_h_existing_yr = tot_v_h

        elif tot_v_h <= self._tot_heat_existing + self._tot_heat_one_to_one:


            v_h_existing_yr = self._tot_heat_existing
            v_h_one_to_one_yr = tot_v_h - self._tot_heat_existing
            

        else:
            
            v_h_existing_yr = self._tot_heat_existing
            v_h_one_to_one_yr = self._tot_heat_one_to_one
            v_h_new_yr = tot_v_h - self._tot_heat_one_to_one - self._tot_heat_existing

                
        return v_h_existing_yr, v_h_one_to_one_yr, v_h_new_yr, tot_v_h
    
    def calculate_effective_cops(self):
        v_h_existing_yr, v_h_one_to_one_yr, v_h_new_yr, tot_v_h = self.getRelativeSharesOfHPCategories()
        cops_eff_inv = np.zeros(len(self._cops_existing))
        if v_h_existing_yr > 0:
            cops_eff_inv += ((v_h_existing_yr/tot_v_h)/self._cops_existing)
        if v_h_one_to_one_yr > 0:
            cops_eff_inv += ((v_h_one_to_one_yr/tot_v_h)/self._cops_one_to_one_replacement)
        if v_h_new_yr > 0:
            cops_eff_inv += ((v_h_new_yr/tot_v_h)/self._cops_new)

        self._cops_eff = 1.0 / cops_eff_inv


    def _compute_u_e(self):
        
        """
        Computes the hourly electricity input (u_e) to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        v_h_existing_yr, v_h_one_to_one_yr, v_h_new_yr, tot_v_h = self.getRelativeSharesOfHPCategories()
        
        u_e_pre = [np.zeros(np.shape(self._cops_new))]
        if v_h_new_yr > 0:
            u_e_pre.append((v_h_new_yr/tot_v_h)*(self._v_h/self._cops_new))
        if v_h_one_to_one_yr > 0:
            u_e_pre.append((v_h_one_to_one_yr/tot_v_h)*(self._v_h/self._cops_one_to_one_replacement))
        if v_h_existing_yr > 0:
            u_e_pre.append((v_h_existing_yr/tot_v_h)*(self._v_h/self._cops_existing))

        self._u_e = np.sum(u_e_pre, axis = 0)
        
    def _compute_u_h(self):
        
        """
        Computes the hourly heat input (u_h) from the environment to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        v_h_existing_yr, v_h_one_to_one_yr, v_h_new_yr, tot_v_h = self.getRelativeSharesOfHPCategories()

        u_h_pre = [np.zeros(np.shape(self._cops_new))]

        if v_h_new_yr > 0:
            u_h_pre.append((v_h_new_yr/tot_v_h)*self._v_h*(1-1/(self._cops_new)))
        if v_h_existing_yr > 0:
            u_h_pre.append((v_h_existing_yr/tot_v_h)*self._v_h*(1-1/(self._cops_existing)))
        if v_h_one_to_one_yr > 0:
            u_h_pre.append((v_h_one_to_one_yr/tot_v_h)*self._v_h*(1-1/(self._cops_one_to_one_replacement)))

        self._u_h = np.sum(u_h_pre, axis = 0)

        self._u_h[self._u_h < 0] = 0.0

    def set_tot_heats_for_cop_calculations(self, tot_heat_existing, tot_heat_new, tot_heat_one_to_one):
        self._tot_heat_existing = tot_heat_existing
        self._tot_heat_new = tot_heat_new
        self._tot_heat_one_to_one = tot_heat_one_to_one

    def get_tot_heats_for_cop_calculations(self):
        return self._tot_heat_existing, self._tot_heat_new, self._tot_heat_one_to_one
    
    def update_v_h_i(self, i, val):
        self.num_test(val)
        self._v_h[i] = val
        
        self.__compute_u_e_i(i)
        self.__compute_u_h_i(i)
        self.__compute_v_co2_i(i)

    def __compute_u_e_i(self,i):
        
        """
        Computes the hourly electricity input (u_e) to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_e[i] = self._v_h[i]/self._cops_eff[i]
   
    def __compute_u_h_i(self,i):
        
        """
        Computes the hourly heat input (u_h) from the environment to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_h[i] = self._v_h[i]*(1-1/self._cops_eff[i])
        
    def __compute_v_co2_i(self,i):
        self._v_co2[i] = self._v_h[i]*self.__tech_dict['co2_intensity']

    def heat_output(self,u_e_i,i):
        
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
        
        v_h_i = u_e_i*self._cops_eff[i]
        
        return v_h_i

    def electricity_input(self,v_h_i,i):
        
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
        
        u_e_i = v_h_i/self._cops_eff[i]
        
        return u_e_i

    
    
    