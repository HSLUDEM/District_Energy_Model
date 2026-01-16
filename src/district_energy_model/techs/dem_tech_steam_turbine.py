# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 2025

@author: UeliSchilt
"""
"""
Steam Turbine (ST)

Takes steam as input and generates electricity and heat (on temperature level
for space heating, i.e. <100degC) as output.
"""
import numpy as np

from district_energy_model.techs.dem_tech_core import TechCore

class SteamTurbine(TechCore):
    
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
        self._input_carrier = 'steam'
        self._output_carrier_1 = 'electricity'
        self._output_carrier_2 = 'heat_st'
        
        # Accounting:
        self._u_steam = [] # [kWh] input - steam
        self._v_e = [] # [kWh_el] output - electricity (total)
        self._v_e_gtcp = [] # [kWh_el] output - electricity stemming from centralised gas turbine (subset of v_e)
        self._v_e_wbsg = [] # [kWh_el] output - electricity stemming from centralised wood boiler (subset of v_e)
        self._v_h = [] # [kWh_th] output - heat (total)
        self._v_h_gtcp = [] # [kWh_th] output - heat stemming from centralised gas turbine (subset of v_h)
        self._v_h_wbsg = [] # [kWh_th] output - heat stemming from centralised wood boiler (subset of v_h)
        
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
        self._lifetime = tech_dict['lifetime']
        self._interest_rate = tech_dict['interest_rate']
        self._capex = tech_dict['capital_cost']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._grid_charges = tech_dict['grid_charges']
        self._allow_heat_export = tech_dict['allow_heat_export']
        self._heat_export_subsidy = tech_dict['heat_export_subsidy']


        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_steam_st'] = self.get_u_steam()
        df['v_e_st'] = self.get_v_e()
        df['v_e_st_gtcp'] = self.get_v_e_gtcp()
        df['v_e_st_wbsg'] = self.get_v_e_wbsg()
        df['v_h_st'] = self.get_v_h()
        df['v_h_st_con'] = self.get_v_h_con()
        df['v_h_st_waste'] = self.get_v_h_waste()

        df['v_h_st_gtcp'] = self.get_v_h_gtcp()
        df['v_h_st_gtcp_con'] = self.get_v_h_gtcp_con()
        df['v_h_st_gtcp_waste'] = self.get_v_h_gtcp_waste()

        df['v_h_st_wbsg'] = self.get_v_h_wbsg()
        df['v_h_st_wbsg_con'] = self.get_v_h_wbsg_con()
        df['v_h_st_wbsg_waste'] = self.get_v_h_wbsg_waste()
        
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
        
        self._u_steam = self._u_steam[:n_hours]
        self._v_e = self._v_e[:n_hours]
        self._v_e_gtcp = self._v_e_gtcp[:n_hours]
        self._v_e_wbsg = self._v_e_wbsg[:n_hours]
        self._v_h = self._v_h[:n_hours]
        self._v_h_con = self._v_h_con[:n_hours]
        self._v_h_waste = self._v_h_waste[:n_hours]

        self._v_h_gtcp = self._v_h_gtcp[:n_hours]
        self._v_h_gtcp_con = self._v_h_gtcp_con[:n_hours]
        self._v_h_gtcp_waste = self._v_h_gtcp_waste[:n_hours]

        self._v_h_wbsg = self._v_h_wbcp[:n_hours]
        self._v_h_wbsg_con = self._v_h_wbsg_con[:n_hours]
        self._v_h_wbsg_waste = self._v_h_wbsg_waste[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_steam = init_vals.copy() # [kWh] input - steam
        self._v_e = init_vals.copy() # [kWh_el] output - electricity
        self._v_e_gtcp = init_vals.copy() # [kWh_el] 
        self._v_e_wbsg = init_vals.copy() # [kWh_el] 
        self._v_h = init_vals.copy() # [kWh_h] output - heat
        self._v_h_con = init_vals.copy() # [kWh_h] output - heat
        self._v_h_waste = init_vals.copy() # [kWh_h] output - heat

        self._v_h_gtcp = init_vals.copy() # [kWh_h] 
        self._v_h_gtcp_con = init_vals.copy() # [kWh_h] 
        self._v_h_gtcp_waste = init_vals.copy() # [kWh_h] 

        self._v_h_wbsg = init_vals.copy() # [kWh_h] 
        self._v_h_wbsg_con = init_vals.copy() # [kWh_h] 
        self._v_h_wbsg_waste = init_vals.copy() # [kWh_h] 

    
    def update_v_e(self, v_e_updated):
        if len(v_e_updated) != len(self._v_e):
            raise ValueError("v_e_updated must have the same length as v_e!")            
        self._v_e = np.array(v_e_updated)
        self.__compute_u_steam()
        # self.__compute_v_h()

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


    def compute_v_e_gtcp(self, tech_gas_turbine_cp):
        v_steam_gtcp_con = tech_gas_turbine_cp.get_v_steam_con()
        self._v_e_gtcp = v_steam_gtcp_con*self._eta_el
        
    def compute_v_e_wbsg(self, tech_wood_boiler_sg):
        v_steam_wbsg = tech_wood_boiler_sg.get_v_steam()
        self._v_e_wbsg = v_steam_wbsg*self._eta_el
        
    def compute_v_h_gtcp(self, tech_gas_turbine_cp):
        v_steam_gtcp_con = tech_gas_turbine_cp.get_v_steam_con()

        self._v_h_gtcp = v_steam_gtcp_con*self._eta_el*self._htp_ratio

        self._v_h_gtcp_con = self._v_h_gtcp * np.nan_to_num(self._v_h_con / self._v_h)
        self._v_h_gtcp_waste = self._v_h_gtcp * np.nan_to_num(self._v_h_waste / self._v_h)

    def compute_v_h_wbsg(self, tech_wood_boiler_sg):
        v_steam_wbsg = tech_wood_boiler_sg.get_v_steam()
        self._v_h_wbsg = v_steam_wbsg*self._eta_el*self._htp_ratio
        
        self._v_h_wbsg_con = self._v_h_wbsg * np.nan_to_num(self._v_h_con / self._v_h)
        self._v_h_wbsg_waste = self._v_h_wbsg * np.nan_to_num(self._v_h_waste / self._v_h)

    # def __compute_v_h(self):
    #     self._v_h = self._v_e*self._htp_ratio
        
    def __compute_u_steam(self):
        """
        Computes the required steam input based on electricity output (kWh).
        """
        self._u_steam = np.array(self._v_e)/self._eta_el # [kWh]
                
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['steam_turbine'] = {
            'essentials':{
                'parent':'conversion_plus',
                'carrier_in':self._input_carrier,
                'carrier_out':self._output_carrier_1,
                'carrier_out_2':self._output_carrier_2,
                'primary_carrier_out':self._output_carrier_1,
                },
            'constraints':{
                'lifetime':self._lifetime,
                # 'export_carrier': self._output_carrier_2,
                },
            'costs':{
                'monetary':{
                    'om_con': 0.0, # costs are reflected in gas supply tech
                    'interest_rate':self._interest_rate,
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
            # energy_cap=self._kW_el_max,
            # energy_eff,
            # htp_ratio,
            # capex
            ):
        
        techs_dict[header] = {
            'essentials':{
                'name':name,
                'color':color,
                'parent':'steam_turbine',
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
                    'om_annual': self._maintenance_cost,
                    'om_prod': self._grid_charges,
                    'interest_rate': self._interest_rate
                    }
                }
            }
        
        if self._allow_heat_export:
            techs_dict[header]['constraints']['export_carrier'] = self._output_carrier_2
            techs_dict[header]['costs']['monetary']['export'] = -self._heat_export_subsidy


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
    
    def get_u_steam(self):
        self.len_test(self._u_steam)
        return self._u_steam
    
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e
    
    def get_v_e_gtcp(self):
        self.len_test(self._v_e_gtcp)
        return self._v_e_gtcp
    
    def get_v_e_wbsg(self):
        self.len_test(self._v_e_wbsg)
        return self._v_e_wbsg
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
    
    def get_v_h_con(self):
        self.len_test(self._v_h_con)
        return self._v_h_con

    def get_v_h_waste(self):
        self.len_test(self._v_h_waste)
        return self._v_h_waste

    def get_v_h_gtcp(self):
        self.len_test(self._v_h_gtcp)
        return self._v_h_gtcp
    
    def get_v_h_gtcp_con(self):
        self.len_test(self._v_h_gtcp_con)
        return self._v_h_gtcp_con

    def get_v_h_gtcp_waste(self):
        self.len_test(self._v_h_gtcp_waste)
        return self._v_h_gtcp_waste

    def get_v_h_wbsg(self):
        self.len_test(self._v_h_wbsg)
        return self._v_h_wbsg

    def get_v_h_wbsg_con(self):
        self.len_test(self._v_h_wbsg_con)
        return self._v_h_wbsg_con

    def get_v_h_wbsg_waste(self):
        self.len_test(self._v_h_wbsg_waste)
        return self._v_h_wbsg_waste
