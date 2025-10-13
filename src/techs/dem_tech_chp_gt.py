# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 13:04:38 2024

@author: UeliSchilt
"""
"""
Combined Heat and Power (CHP) from Gas Turbine (GT)
"""
import numpy as np
from techs.dem_tech_core import TechCore

class CHPGasTurbine(TechCore):
    
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
        self._input_carrier = 'gas'
        self._output_carrier_1 = 'electricity'
        self._output_carrier_2 = 'heat_chpgt'
        
        # Accounting:
        self._u_gas = [] # [kWh] CHP input - gas
        self._u_gas_kg = [] # [kg] CHP input - gas
        self._v_e = [] # [kWh_el] CHP output - electricity
        self._v_h = [] # [kWh_h] CHP output - heat
        self._v_co2 = [] # [kg] CHP output - CO2 emissions
        
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
        self._deploy_existing = tech_dict['deploy_existing']
        self._eta_el = tech_dict['eta_el']
        self._htp_ratio = tech_dict['htp_ratio']
        self._kW_el_max = tech_dict['kW_el_max'] # [kW_el] Max. electric power output
        self._force_cap_max = tech_dict['force_cap_max']
        self._hv_gas = tech_dict['hv_gas_MJpkg']
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        self._capex = tech_dict['capital_cost']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._allow_heat_export = tech_dict['allow_heat_export']
        self._heat_export_subsidy = tech_dict['heat_export_subsidy']

        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_gas_chpgt'] = self.get_u_gas()
        df['u_gas_chpgt_kg'] = self.get_u_gas_kg()
        df['v_e_chpgt'] = self.get_v_e()
        df['v_h_chpgt'] = self.get_v_h()
        df['v_h_chpgt_waste'] = self.get_v_h_waste()
        df['v_h_chpgt_con'] = self.get_v_h_con()
        df['v_co2_chpgt'] = self.get_v_co2()
        
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
        self._v_h = self._v_h[:n_hours]
        self._v_co2 = self._v_co2[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_gas = init_vals.copy() # [kWh] CHP input - gas
        self._u_gas_kg = init_vals.copy() # [kg] CHP input - gas
        self._v_e = init_vals.copy() # [kWh_el] CHP output - electricity
        self._v_h = init_vals.copy() # [kWh_h] CHP output - heat
        self._v_h_con = init_vals.copy()
        self._v_h_waste = init_vals.copy()
        self._v_co2 = init_vals.copy() # [kg] CHP output - CO2 emissions
    
    def update_v_e(self, v_e_updated):
        if len(v_e_updated) != len(self._v_e):
            raise ValueError("v_e_updated must have the same length as v_e!")            
        self._v_e = np.array(v_e_updated)
        self.__compute_u_gas()
        # self.__compute_v_h()
        self.__compute_v_co2()      

    # def __compute_v_h(self):
    #     self._v_h = self._v_e*self._htp_ratio

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
        print("\n Create CHP GT tech group\n")
        tech_groups_dict['chp_gt'] = {
            'essentials':{
                'parent':'conversion_plus',
                'carrier_in':self._input_carrier,
                'carrier_out':self._output_carrier_1,
                'carrier_out_2':self._output_carrier_2, # VIA DISTRICT HEATING
                'primary_carrier_out':self._output_carrier_1,
                },
            'constraints':{
                'lifetime':self._lifetime,
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
                'parent':'chp_gt',
                },
            'constraints':{
                'energy_cap_max':self._kW_el_max,
                'energy_eff':self._eta_el,
                'carrier_ratios':{
                    'carrier_out_2':{
                        self._output_carrier_2:self._htp_ratio
                        }
                    }
                },
            'costs':{
                'monetary':{
                    'energy_cap': self._capex
                    }
                }
            }
    
        if self._allow_heat_export:
            techs_dict[header]['constraints']['export_carrier'] = 'heat_chpgt'
            techs_dict[header]['costs']['monetary']['export'] = -self._heat_export_subsidy



        if self._force_cap_max:
            techs_dict[header]['constraints']['energy_cap_equals']\
                = self._kW_el_max
    


        return techs_dict
    
    def get_deploy_existing(self):
        return self._deploy_existing
    
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
    
    # NOTE: gas supply is currently implemented in gas boiler class (03.10.2024)
    
    # def create_gas_supply(
    #         techs_dict,
    #         color,
    #         gas_cost
    #         ):
    #     techs_dict['gas_supply_chp_gt'] = {
    #         'essentials':{
    #             'name':'Gas Supply CHP GT',
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
    #                 'om_con':gas_cost,
    #                 'interest_rate':0.0
    #                 },
    #             'emissions_co2':{
    #                 'om_prod':0.0 # this is reflected in the emissions of the CHP gas turbine
    #                 }
    #             }
    #         }
        
    #     return techs_dict