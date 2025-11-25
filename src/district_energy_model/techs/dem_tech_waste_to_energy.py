# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 2025

@author: UeliSchilt
"""
"""
Waste-to-energy plant (WtE).
"""
import numpy as np
from techs.dem_tech_core import TechCore

class WasteToEnergy(TechCore):
    
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
        self._input_carrier = 'munic_solid_waste' # municipal solid waste (msw)
        self._output_carrier_1 = 'electricity'
        self._output_carrier_2 = 'heat_wte'
        
        # Accounting:
        self._u_msw = [] # [kWh] input - municipal solid waste (msw)
        self._u_msw_kg = [] # [kg] input - municipal solid waste (msw)
        self._v_e = [] # [kWh_el] output - electricity
        self._v_h = [] # [kWh_th] output - heat
        self._v_h_con = [] # [kWh_th] consumed heat
        self._v_h_waste = [] # [kWh_th] waste heat
        self._v_co2 = [] # [kg] output - CO2 emissions
        
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
        self._force_cap_max = tech_dict['force_cap_max']
        self._cap_min_use = tech_dict['cap_min_use']
        self._annual_msw_supply_kg = tech_dict['annual_msw_supply']
        self._kW_el_max = tech_dict['kW_el_max'] # [kW_el] Max. electric power output
        self._hv_msw = tech_dict['hv_msw_MJpkg']
        self._price_msw = tech_dict['msw_price_CHFpkg']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        self._capex = tech_dict['capital_cost']
        self._maintenance_cost = tech_dict['maintenance_cost']
        
        # Computed properties:
        self.__compute_annual_msw_supply_kWh()
        
        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_msw_wte'] = self.get_u_msw()
        df['u_msw_wte_kg'] = self.get_u_msw_kg()
        df['v_e_wte'] = self.get_v_e()
        df['v_h_wte'] = self.get_v_h()
        df['v_h_wte_con'] = self.get_v_h_con()
        df['v_h_wte_waste'] = self.get_v_h_waste()
        df['v_co2_wte'] = self.get_v_co2()
        
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
        
        self._u_msw = self._u_msw[:n_hours]
        self._u_msw_kg = self._u_msw_kg[:n_hours]
        self._v_e = self._v_e[:n_hours]
        self._v_h = self._v_h[:n_hours]
        self._v_h_con = self._v_h_con[:n_hours]
        self._v_h_waste = self._v_h_waste[:n_hours]
        self._v_co2 = self._v_co2[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_msw = init_vals.copy() # [kWh] input - municipal solid waste (msw)
        self._u_msw_kg = init_vals.copy() # [kg] input - municipal solid waste (msw)
        self._v_e = init_vals.copy() # [kWh_el] output - electricity
        self._v_h = init_vals.copy() # [kWh_h] output - heat
        self._v_h_con = init_vals.copy()
        self._v_h_waste = init_vals.copy()
        
        
        self._v_co2 = init_vals.copy() # [kg] output - CO2 emissions
    
    def update_v_e(self, v_e_updated):
        if len(v_e_updated) != len(self._v_e):
            raise ValueError("v_e_updated must have the same length as v_e!")            
        self._v_e = np.array(v_e_updated)
        self.__compute_u_msw()
        # self.__compute_v_h()
        self.__compute_v_co2()      
        
    def update_v_h(self, v_h_updated):
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")            
        self._v_h = np.array(v_h_updated)
        
    def update_v_h_con(self, v_h_con_updated):
        if len(v_h_con_updated) != len(self._v_h_con):
            raise ValueError("v_h_con_updated must have the same length as v_h_con!")            
        self._v_h_con = np.array(v_h_con_updated)
        
    def update_v_h_waste(self, v_h_waste_updated):
        if len(v_h_waste_updated) != len(self._v_h_waste):
            raise ValueError("v_h_waste_updated must have the same length as v_h_waste!")            
        self._v_h_waste = np.array(v_h_waste_updated)
    
    # def __compute_v_h(self):
    #     self._v_h = self._v_e*self._htp_ratio
        
    def __compute_u_msw(self):
        """
        Computes the required waste input based on electricity output (kWh).
        """
        
        # Conversion from MJ/kg to kJ/kg:
        hv_msw_kJpkg = self._hv_msw*1000
        
        self._u_msw = np.array(self._v_e)/self._eta_el # [kWh]
        self._u_msw_kg = self._u_msw*3600/hv_msw_kJpkg # [kg]
        
    def __compute_v_co2(self):        
        self._v_co2 = self._v_e*self._co2_intensity
        
    def __compute_annual_msw_supply_kWh(self):
        if self._annual_msw_supply_kg == 'inf':
            self._annual_msw_supply_kWh = 'inf'
        else:
            CONV_MJ_to_kWh = 1000/3600 # Conversion from [MJ] to [kWh]        
            supp_MJ = self._annual_msw_supply_kg*self._hv_msw    
            self._annual_msw_supply_kWh = supp_MJ*CONV_MJ_to_kWh
        
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['waste_to_energy'] = {
            'essentials':{
                'parent':'conversion_plus',
                'carrier_in':self._input_carrier,
                'carrier_out':self._output_carrier_1,
                'carrier_out_2':self._output_carrier_2,
                'primary_carrier_out':self._output_carrier_1,
                },
            'constraints':{
                'lifetime':self._lifetime,
                'export_carrier': self._output_carrier_2,
                },
            'costs':{
                'monetary':{
                    'om_con': 0.0, # cost/revenue is reflected in MSW supply
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
            # energy_cap=self._kW_el_max,
            # energy_eff,
            # htp_ratio,
            # capex
            ):
        
        techs_dict[header] = {
            'essentials':{
                'name':name,
                'color':color,
                'parent':'waste_to_energy',
                },
            'constraints':{
                'energy_cap_max':self._kW_el_max,
                'energy_cap_min_use': self._cap_min_use,
                'energy_eff':self._eta_el,
                'carrier_ratios':{
                    'carrier_out_2':{
                        self._output_carrier_2:self._htp_ratio
                        }
                    }
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
                = self._kW_el_max
    
        return techs_dict
    
    def get_eta_el(self):
        self.num_test(self._eta_el)
        return self._eta_el
    
    def get_htp_ratio(self):
        self.num_test(self._htp_ratio)
        return self._htp_ratio
    
    def get_annual_msw_supply_kg(self):
        return self._annual_msw_supply_kg
    
    def get_annual_msw_supply_kWh(self):
        if self._annual_msw_supply_kWh == None:
            raise ValueError("annual_msw_supply_kWh not defined.")
        else:
            return self._annual_msw_supply_kWh
    
    def get_kW_el_max(self):
        self.num_test(self._kW_el_max)
        return self._kW_el_max
    
    def get_u_msw(self):
        self.len_test(self._u_msw)
        return self._u_msw
    
    def get_u_msw_kg(self):
        self.len_test(self._u_msw_kg)
        return self._u_msw_kg
    
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
    
    def get_v_h_con(self):
        self.len_test(self._v_h_con)
        return self._v_h_con
    
    def get_v_h_waste(self):
        self.len_test(self._v_h_waste)
        return self._v_h_waste
    
    def get_v_co2(self):
        self.len_test(self._v_co2)
        return self._v_co2
    