# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:20:25 2024

@author: UeliSchilt
"""

import numpy as np
import pandas as pd
from techs.dem_tech_core import TechCore

# class HeatPump(TechCore):
class HeatPump(TechCore):
    
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
        self._output_carrier = 'heat_hp'
        
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
        self._cop = tech_dict['cop'] # Coefficient of performance
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
    
    def compute_v_h(self, src_h_yr, d_h_profile):

        tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
        tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
        self._v_h = np.array(tmp_df['v_h'].tolist())
        
        # hp_input_kWh = self.__compute_hp_input(src_h_yr, self.cop)
        
        # self.u_e = hp_input_kWh[0]*d_h_profile
        # self.u_h = hp_input_kWh[1]*d_h_profile
        
        # Re-calculate:
        self.__compute_u_e()
        self.__compute_u_h()
        self.__compute_v_co2()

        
    def update_v_h(self, v_h_updated):
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
        
        self._v_h = np.array(v_h_updated)
        
        self.__compute_u_e()
        self.__compute_u_h()
        self.__compute_v_co2()
        
    def update_v_h_i(self, i, val):
        self.num_test(val)
        self._v_h[i] = val
        
        self.__compute_u_e_i(i)
        self.__compute_u_h_i(i)
        self.__compute_v_co2_i(i)
        
    # def update_u_e_i(self, i, val):
    #     self.num_test(val)
    #     self._u_e[i] = val
        
    # def update_u_h_i(self, i, val):
    #     self.num_test(val)
    #     self._u_h[i] = val
    
    def get_cop(self):
        self.num_test(self._cop)
        return self._cop
    
    def get_fixed_demand_share(self):
        return self._fixed_demand_share
    
    def get_fixed_demand_share_val(self):
        self.num_test(self._fixed_demand_share_val)
        return self._fixed_demand_share_val
    
    def get_only_allow_existing(self):
        return self._only_allow_existing
                
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
        
        v_h_i = u_e_i*self._cop
        
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
        
        u_e_i = v_h_i/self._cop
        
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
    
    # def __compute_hp_input(self, arg_v_h_hp, arg_cop):
        
    #             
    #     """
    #     Computes the share of electricity and environmental energy input of the
    #     heat pump based on the thermal output using a fixed cop.
        
    #     Parameters
    #     ----------
    #     arg_v_h_hp : float
    #         Thermal output of heat pump [kWh].
    #     arg_cop : float
    #         Fixed Coefficient Of Performance (COP) [-]. 

    #     Returns
    #     -------
    #     list
    #         a list of length=2 with the input energy.
    #         Item 0: electricity input [kWh]
    #         Item 1: environmental input [kWh]
    #     """
        
    #     '''
    #     TO BE ADDED:
    #         - Temperature dependent COP
    #     '''
        
    #     u_e_hp = arg_v_h_hp/arg_cop # [kWh] electricity input to heat pump
    #     u_env_hp = arg_v_h_hp - u_e_hp # [kWh] environmental input (air, water, ground) to hp
        
    #     return [u_e_hp, u_env_hp]
    
    def __compute_u_e(self):
        
        """
        Computes the hourly electricity input (u_e) to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_e = self._v_h/self._cop
   
    def __compute_u_h(self):
        
        """
        Computes the hourly heat input (u_h) from the environment to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_h = self._v_h*(1-1/self._cop)
        
    def __compute_v_co2(self):
        self._v_co2 = self._v_h*self.__tech_dict['co2_intensity']
        
    def __compute_u_e_i(self,i):
        
        """
        Computes the hourly electricity input (u_e) to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_e[i] = self._v_h[i]/self._cop
   
    def __compute_u_h_i(self,i):
        
        """
        Computes the hourly heat input (u_h) from the environment to the
        heat pump based on the thermal output using a fixed cop.
        """
        
        self._u_h[i] = self._v_h[i]*(1-1/self._cop)
        
    def __compute_v_co2_i(self,i):
        self._v_co2[i] = self._v_h[i]*self.__tech_dict['co2_intensity']
        
    # @staticmethod
    # def get_u_h(v_h, cop):
    #     """
    #     Computes the hourly heat input (u_h) from the environment to the
    #     heat pump based on the thermal output using a fixed cop. Returns the
    #     hourly heat input.

    #     Parameters
    #     ----------
    #     v_h : pandas dataseries
    #         Timeseries of hourly heat output from heat pump.
    #     cop : float
    #         Fixed coefficient of performance (cop) of heat pump.

    #     Returns
    #     -------
    #     u_h : pandas dataseries
    #         Hourly heat input to heat pump.

    #     """
      
    #     u_h = v_h*(1-1/cop)

    #     return u_h
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['heat_pump'] = {
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
                        self._output_carrier:self._cop
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
        
        techs_dict[header] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent': 'heat_pump',
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
        
        additional_techs_label_list = []
        
        if create_tesdc_hp_hub:
            techs_dict['heat_pump_hub'] = {
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
            additional_techs_label_list.append('heat_pump_hub')            
    
        return techs_dict, additional_techs_label_list
    
    def create_techs_dict_clustering(
            self,
            techs_dict,
            # tech_dict,
            name = 'Heat Pump',
            capex = 0,
            color = '#860720'
            ):
        
        techs_dict['heat_pump'] = {
            'essentials':{
                'name': name,
                'color': color,
                'parent':'conversion_plus',
                'carrier_in':'electricity',
                'carrier_out':'heat',
                'primary_carrier_out':'heat'
                },
            'constraints':{
                'energy_eff':1,
                'carrier_ratios':{
                    'carrier_out':{
                        'heat':self._cop,
                        }
                    },
                'lifetime': self._lifetime
                },
            'costs':{
                'monetary':{
                    'om_con': 0.0, # this is reflected in the cost of the electricity
                    'interest_rate':self._interest_rate,
                    'energy_cap': capex + self.get_maintenance_cost()
                    },
                'emissions_co2':{
                    'om_prod':self._co2_intensity,
                    }
                }
            }
    
        return techs_dict
    
    def get_power_up_for_replacement(self):
        return self._power_up_for_replacement
    
    def set_power_up_for_replacement(self, value):
        self._power_up_for_replacement = value

    
    
    
    
    
    
    
    
    
    
    
    
    