# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 13:04:38 2024

@author: UeliSchilt
"""
"""
Combined Heat and Power (CHP) from Gas Turbine (GT)
"""
import numpy as np

from district_energy_model.techs.dem_tech_core import TechCore

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
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_gas = init_vals.copy() # [kWh] CHP input - gas
        self._u_gas_kg = init_vals.copy() # [kg] CHP input - gas
        self._v_e = init_vals.copy() # [kWh_el] CHP output - electricity
        self._v_h = init_vals.copy() # [kWh_h] CHP output - heat
        self._v_h_con = init_vals.copy()
        self._v_h_waste = init_vals.copy()
    
    def update_v_e(self, v_e_updated):
        if len(v_e_updated) != len(self._v_e):
            raise ValueError("v_e_updated must have the same length as v_e!")            
        self._v_e = np.array(v_e_updated)
        self.__compute_u_gas()
        # self.__compute_v_h()

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
        
        
    def create_tech_groups_dict(self, tech_groups_dict):
        print("\n Create CHP GT tech group\n")
        tech_groups_dict['chp_gt'] = {
            'base_tech':'conversion',
            'carrier_in':self._input_carrier,
            'carrier_out':[self._output_carrier_1, self._output_carrier_2], # heat via district heating
            'lifetime':self._lifetime,
            'cost_flow_in':{
                'data': 0.0, # costs are reflected in gas supply tech
                'index':'monetary',
                'dims':'costs',
                },
            'cost_interest_rate':{
                'data':self._interest_rate,
                'index':'monetary',
                'dims':'costs',
                },
            }

        return tech_groups_dict
    
    def create_techs_dict(
            self,
            techs_dict,
            header,
            name,
            color,
            energy_scaling_factor,
            # energy_cap=self._kW_el_max,
            # energy_eff,
            # htp_ratio,
            # capex
            ):
        
        techs_dict[header] = {
            'name':name,
            'color':color,
            'template':'chp_gt',
            'flow_cap_max':self._kW_el_max / energy_scaling_factor if self._kW_el_max != 'inf' else 'inf',
            'flow_out_eff':{
                'data':[self._eta_el, self._eta_el * self._htp_ratio],
                'index':[self._output_carrier_1, self._output_carrier_2],
                'dims':'carriers',
                },
            'cost_flow_cap':{
                'data': self._capex * energy_scaling_factor,
                'index':'monetary',
                'dims':'costs',
                },
            'cost_om_annual':{
                'data': self._maintenance_cost * energy_scaling_factor,
                'index':'monetary',
                'dims':'costs',
                },
            }
    
        if self._allow_heat_export:
            techs_dict[header]['carrier_export'] = 'heat_chpgt'
            techs_dict[header]['cost_export'] = {
                'data': -self._heat_export_subsidy * energy_scaling_factor,
                'index':'monetary',
                'dims':'costs',
                }



        if self._force_cap_max:
            flow_cap = self._kW_el_max
            techs_dict[header]['flow_cap_min'] = flow_cap
            techs_dict[header]['flow_cap_max'] = flow_cap
    


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
    #             }
    #         }
        
    #     return techs_dict
