# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 2025

@author: UeliSchilt
"""
"""
Gas Turbine (GT) Central Plant (CP)

(As opposed to the chp_gt technology, this turbine is meant to model a larger
 power plant supplying a whole district. Outputs are electriciyt and steam,
 meaning it must be coupled with the steam_turbine tech to produce heat.)
"""
import numpy as np
from techs.dem_tech_core import TechCore

class GasTurbineCP(TechCore):
    
    def __init__(self, tech_dict):
        """
        Initialise technology parameters for gas turbine cp (central plant).
        
        Note:
        This gas turbine generates electricity and steam. It must be coupled
        with a steam turbine in order to convert the steam to heat.
        
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
        self.input_carrier = 'gas'
        self.output_carrier_1 = 'electricity'
        self.output_carrier_2 = 'steam'
        
        # Accounting:
        self._u_gas = [] # [kWh] input - gas
        self._u_gas_kg = [] # [kg] input - gas
        self._v_e = [] # [kWh_el] output - electricity
        self._v_steam = [] # [kWh] output - steam
        self._v_steam_con = [] # [kWh] steam consumed
        self._v_steam_surp = [] # [kWh]
        self._v_co2 = [] # [kg] output - emissions
        
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        
        # Properties:
        self._eta_el = tech_dict['eta_el']
        self._htp_ratio = tech_dict['htp_ratio']
        self._kW_el_max = tech_dict['kW_el_max'] # [kW_el] Max. electric power output
        self._force_cap_max = tech_dict['force_cap_max']
        self._cap_min_use = tech_dict['cap_min_use']
        self._hv_gas = tech_dict['hv_gas_MJpkg']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        self._capex = tech_dict['capital_cost']
        self._maintenance_cost = tech_dict['maintenance_cost']

        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_gas_gtcp'] = self.get_u_gas()
        df['u_gas_gtcp_kg'] = self.get_u_gas_kg()
        df['v_e_gtcp'] = self.get_v_e()
        df['v_steam_gtcp'] = self.get_v_steam()
        df['v_steam_gtcp_con'] = self.get_v_steam_con()
        df['v_steam_gtcp_surp'] = self.get_v_steam_surp()
        df['v_co2_gtcp'] = self.get_v_co2()
        
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
        self._v_e = self._v_e[:n_hours]
        self._v_steam = self._v_steam[:n_hours]
        self._v_steam_con = self._v_steam_con[:n_hours]
        self._v_steam_surp = self._v_steam_surp[:n_hours]
        self._v_co2 = self._v_co2[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_gas = init_vals.copy() # [kWh] input - gas
        self._u_gas_kg = init_vals.copy() # [kg] input - gas
        self._v_e = init_vals.copy() # [kWh_el] output - electricity
        self._v_steam = init_vals.copy() # [kWh_th] output - high temperature steam total
        self._v_steam_con = init_vals.copy() # [kWh_th] output - high temperature steam consumed
        self._v_steam_surp = init_vals.copy() # [kWh_th] output - high temperature steam surplus
        self._v_co2 = init_vals.copy() # [kg] CHP output - CO2 emissions
    
    def update_v_e(self, v_e_updated):
        if len(v_e_updated) != len(self._v_e):
            raise ValueError("v_e_updated must have the same length as v_e!")            
        self._v_e = np.array(v_e_updated)
        self.__compute_u_gas()
        # self.__compute_v_steam()
        self.__compute_v_co2()  
        
    def update_v_steam(self, v_steam_updated):
         if len(v_steam_updated) != len(self._v_steam):
             raise ValueError("v_steam_updated must have the same length as v_steam!")            
         self._v_steam = np.array(v_steam_updated)
         
    def update_v_steam_con(self, v_steam_con_updated):
         if len(v_steam_con_updated) != len(self._v_steam_con):
             raise ValueError("v_steam_con_updated must have the same length as v_steam_con!")            
         self._v_steam_con = np.array(v_steam_con_updated)
         
    def update_v_steam_surp(self, v_steam_surp_updated):
         if len(v_steam_surp_updated) != len(self._v_steam_surp):
             raise ValueError("v_steam_surp_updated must have the same length as v_steam_surp!")            
         self._v_steam_surp = np.array(v_steam_surp_updated)
        
    # def __compute_v_steam(self):
    #     self._v_steam = self._v_e*self._htp_ratio
        
    def __compute_u_gas(self):
        """
        Computes the required gas input based on electricity output (kWh).
        """
        
        # Conversion from MJ/kg to kJ/kg:
        hv_gas_kJpkg = self._hv_gas*1000
        
        self._u_gas = np.array(self._v_e)/self._eta_el # [kWh]
        self._u_gas_kg = self._u_gas*3600/hv_gas_kJpkg # [kg]
        
    def __compute_v_co2(self):        
        self._v_co2 = self._v_e*self._co2_intensity
        
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['gas_turbine_cp'] = {
            'essentials':{
                'parent':'conversion_plus',
                'carrier_in':self.input_carrier,
                'carrier_out':self.output_carrier_1,
                'carrier_out_2':self.output_carrier_2,
                'primary_carrier_out':self.output_carrier_1,
                },
            'constraints':{
                'lifetime':self._lifetime,
                'export_carrier': self.output_carrier_2,
                },
            'costs':{
                'monetary':{
                    'om_con': 0.0, # costs are reflected in gas supply tech
                    'interest_rate':self._interest_rate,
                    'om_annual': self._maintenance_cost
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
            # energy_cap=self._kW_el_max,
            # energy_eff,
            # htp_ratio,
            # capex
            ):
        
        techs_dict[header] = {
            'essentials':{
                'name':name,
                'color':color,
                'parent':'gas_turbine_cp',
                },
            'constraints':{
                'energy_cap_max':self._kW_el_max,
                'energy_cap_min_use': self._cap_min_use,
                'energy_eff':self._eta_el,
                'carrier_ratios':{
                    'carrier_out_2':{
                        self.output_carrier_2:self._htp_ratio
                        }
                    }
                },
            'costs':{
                'monetary':{
                    'energy_cap': self._capex
                    }
                }
            }
        
        if self._force_cap_max:
            techs_dict[header]['constraints']['energy_cap_equals']\
                = self._kW_el_max
    
        return techs_dict
    
    def get_eta_el(self):
        self.num_test(self._eta_el)
        return self._eta_el
    
    def get_htp_ratio(self):
        self.num_test(self._htp_ratio)
        return self._htp_ratio
    
    def get_kW_el_max(self):
        self.num_test(self._kW_el_max)
        return self._kW_el_max
    
    def get_u_gas(self):
        self.len_test(self._u_gas)
        return self._u_gas
    
    def get_u_gas_kg(self):
        self.len_test(self._u_gas_kg)
        return self._u_gas_kg
    
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e
    
    def get_v_steam(self):
        self.len_test(self._v_steam)
        return self._v_steam
    
    def get_v_steam_con(self):
        self.len_test(self._v_steam_con)
        return self._v_steam_con
    
    def get_v_steam_surp(self):
        self.len_test(self._v_steam_surp)
        return self._v_steam_surp
    
    def get_v_co2(self):
        self.len_test(self._v_co2)
        return self._v_co2
