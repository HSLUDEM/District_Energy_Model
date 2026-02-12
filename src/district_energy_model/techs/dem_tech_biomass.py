# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 17:18:29 2024

@author: Somesh
"""

"""

Implementation of the Biomass class

"""

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore


class Biomass(TechCore):
    
    def __init__(self, tech_dict):
        
        """
        Empty class as placeholder.
        """
        super().__init__(tech_dict)
        
        self._v_e = []
        self._v_e_exp = []
        self._v_e_cons = []
        self._v_h = []
        
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
        ...
    
    def update_df_results(self, df):
        
        df['v_e_bm'] = self.get_v_e()
        df['v_e_bm_exp'] = self.get_v_e_exp()
        df['v_e_bm_cons'] = self.get_v_e_cons()
        df['v_h_bm'] = self.get_v_h()
        
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
        
        self._v_e = self._v_e[:n_hours]
        self._v_e_exp = self._v_e_exp[:n_hours]
        self._v_e_cons = self._v_e_cons[:n_hours]
        self._v_h = self._v_h[:n_hours]
        
    def update_v_e(self, v_e_updated):
        self._v_e = np.array(v_e_updated)
        
        # self.__compute_v_e_pot_remain()
                
    def update_v_e_cons(self, v_e_cons_updated):
        if len(v_e_cons_updated) != len(self._v_e):
            raise ValueError()        
        self._v_e_cons = np.array(v_e_cons_updated)
    
    def update_v_e_exp(self, v_e_exp_updated):
        if len(v_e_exp_updated) != len(self._v_e):
            raise ValueError()        
        self._v_e_exp = np.array(v_e_exp_updated)
        
    def update_v_h(self, v_h_updated):
        self._v_h = np.array(v_h_updated)
        
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e
    
    def get_v_e_cons(self):
        self.len_test(self._v_e_cons)
        return self._v_e_cons
    
    def get_v_e_exp(self):
        self.len_test(self._v_e_exp)
        return self._v_e_exp
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
    
    # def _______():
    #     ...
        
    # def get_u_wet_bm(self):
    #     self.len_test(self._u_wet_bm)
    #     return self._u_wet_bm
    
    # def get_u_hyd(self):
    #     self.len_test(self._u_hyd)
    #     return self._u_hyd
    
    # def get_u_e(self):
    #     self.len_test(self._u_e)
    #     return self._u_e
    
    # def get_u_wd(self):
    #     self.len_test(self._u_wd)
    #     return self._u_wd
    
    # def get_v_e(self):
    #     self.len_test(self._v_e)
    #     return self._v_e
    
    # def get_v_e_cons(self):
    #     self.len_test(self._v_e_cons)
    #     return self._v_e_cons
    
    # def get_v_e_exp(self):
    #     self.len_test(self._v_e_exp)
    #     return self._v_e_exp
    
    # def get_v_h(self):
    #     self.len_test(self._v_h)
    #     return self._v_h
    
    # def get_v_gas(self):
    #     self.len_test(self._v_gas)
    #     return self._v_gas
    
class HydrothermalGasification(TechCore): # hg
    
    def __init__(self, tech_dict):
        
        """

        Parameters
        ----------
        input_carrier : string, name of input carrier (manure, green_waste, sewage_sludge)
        
        eta : float, value of conversion efficiency, has to be between 0 and 1

        Returns
        -------
        None.

        """
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier types:
        self.input_carrier = 'wet_biomass'
        self.output_carrier = 'gas'
        
        #Accounting:
        # self.u_input_carrier = [] # manure potential input [kWh] # IS THIS USED???
        self._u_wet_bm = []
        self._v_gas = [] # gas LHV output [kWh]
        
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
        
        #Checks for Errors:
        if tech_dict['efficiency'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")
            
        #Properties:
        self._eta = tech_dict['efficiency']
        self._maintenance_cost = tech_dict['maintenance_cost']

        # Update input dict:
        self.__tech_dict = tech_dict 
        
    def update_df_results(self, df):
        
        df['u_wet_bm_hg'] = self._u_wet_bm
        df['v_gas_hg'] = self._v_gas
        
        return df
    
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_wet_bm = init_vals.copy()
        self._v_gas = init_vals.copy()
        
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
        
        self._v_gas = self._v_gas[:n_hours]
        self._u_wet_bm = self._u_wet_bm[:n_hours]
        # self._v_h = self._v_h[:n_hours]

    # def compute_u_input_carrier(self):
    #     """
    #     Compute the required input [kWh] of the input carrier, given a gas output [kWh].

    #     Returns
    #     -------
    #     None.

    #     """
    #     self.u_input_carrier = self._v_gas/self._eta
        
    # def compute_v_gas(self):
    #     """
    #     Compute the gas output [kWh], given the input [kWh].

    #     Returns
    #     -------
    #     None.

    #     """
        
    #     self._v_gas = self.u_input_carrier * self._eta
        
    def update_v_gas(self, v_gas_updated):
        
        if len(v_gas_updated) != len(self._v_gas):
            raise ValueError("v_gas_updated must have the same length as v_gas!")
            
        self._v_gas = np.array(v_gas_updated)
        
        self.__compute_u_wet_bm()
        
    def __compute_u_wet_bm(self):
        self._u_wet_bm = self._v_gas/self._eta        
    
    def generate_tech_dict(self, techs_dict, energy_scaling_factor):
        
        hg_dict = {
            'essentials':{
                'name':'Hydrothermal Gasification',
                'color':self.__tech_dict['color'],
                'parent':'conversion',
                'carrier_in': 'wet_biomass',
                'carrier_out': 'gas',
                },
            'constraints':{
                'energy_cap_max':self.__tech_dict['capacity_kWh'] / energy_scaling_factor if self.__tech_dict['capacity_kWh'] != 'inf' else 'inf',
                'energy_eff':self.__tech_dict['efficiency'],
                'lifetime':self.__tech_dict['lifetime']
                },
            'costs':{
                'monetary':{
                    'energy_cap': self.__tech_dict['capital_cost'] * energy_scaling_factor,
                    'om_con':self.__tech_dict['om_cost'] * energy_scaling_factor, # [CHF/kWh]
                    'interest_rate':self.__tech_dict['interest_rate'],
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    },
                }
            }
        
        techs_dict['hydrothermal_gasification'] = hg_dict
        
        return techs_dict

    def get_u_wet_bm(self):
        self.len_test(self._u_wet_bm)
        return self._u_wet_bm
    
    def get_v_gas(self):
        self.len_test(self._v_gas)
        return self._v_gas        
        
class AnaerobicDigestionUpgrade(TechCore): # agu
    
    def __init__(self, tech_dict):
        """

        Parameters
        ----------
        input_carrier : string, name of input carrier (manure, green_waste, sewage_sludge)
        
        eta : float, value of conversion efficiency, has to be between 0 and 1

        Returns
        -------
        None.

        """
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier Types:
        self.input_carrier = 'wet_biomass'
        self.output_carrier = "gas"
        
        #Accounting:
        # self.u_input_carrier = []
        self._u_wet_bm = []
        self._v_gas = []
        
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
        
        #Checks for Errors:
        if tech_dict['efficiency'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")

        #Properties:
        self._eta = tech_dict['efficiency']
        self._maintenance_cost = tech_dict['maintenance_cost']

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_wet_bm_agu'] = self._u_wet_bm
        df['v_gas_agu'] = self._v_gas
        
        return df
    
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_wet_bm = init_vals.copy()
        self._v_gas = init_vals.copy()
        
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
        
        self._v_gas = self._v_gas[:n_hours]
        self._u_wet_bm = self._u_wet_bm[:n_hours]
        # self._v_h = self._v_h[:n_hours]


    # def compute_u_input_carrier(self):
    #     """
    #     Compute the required input [kWh] of the input carrier, given a gas output [kWh].

    #     Returns
    #     -------
    #     None.

    #     """
        
    #     self.u_input_carrier = self._v_gas/self._eta
    
    # def compute_v_gas(self):
    #     """
    #     Compute the gas output [kWh], given the input [kWh].

    #     Returns
    #     -------
    #     None.

    #     """
        
    #     self._v_gas = self.u_input_carrier * self._eta
    
    def update_v_gas(self, v_gas_updated):
        
        if len(v_gas_updated) != len(self._v_gas):
            raise ValueError("v_gas_updated must have the same length as v_gas!")
            
        self._v_gas = np.array(v_gas_updated)
        
        self.__compute_u_wet_bm()
        
    def __compute_u_wet_bm(self):
        self._u_wet_bm = self._v_gas/self._eta 
        
    def generate_tech_dict(self, techs_dict, energy_scaling_factor):
        
        adu_dict = {
            'essentials':{
                'name': 'Anaerobic Digestion Upgrade',
                'color':self.__tech_dict['color'],
                'parent':'conversion',
                'carrier_in': 'wet_biomass',
                'carrier_out': 'gas',
                },
            'constraints':{
                'energy_cap_max':self.__tech_dict['capacity_kWh'] / energy_scaling_factor if self.__tech_dict['capacity_kWh'] != 'inf' else 'inf',
                'energy_eff':self.__tech_dict['efficiency'],
                'lifetime':self.__tech_dict['lifetime']
                },
            'costs':{
                'monetary':{
                    'energy_cap': self.__tech_dict['capital_cost'] * energy_scaling_factor,
                    'om_con':self.__tech_dict['om_cost'] * energy_scaling_factor, # [CHF/kWh]
                    'interest_rate':self.__tech_dict['interest_rate'],
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    },
                }
            }
        
        techs_dict['anaerobic_digestion_upgrade'] = adu_dict
        
        return techs_dict
    
    def get_u_wet_bm(self):
        self.len_test(self._u_wet_bm)
        return self._u_wet_bm
    
    def get_v_gas(self):
        self.len_test(self._v_gas)
        return self._v_gas
         
        
class AnaerobicDigestionUpgradeHydrogen(): # aguh
    
    def __init__(self, tech_dict):
        """
        

        Parameters
        ----------
        input_carrier : input_carrier : string, name of input carrier (manure, green_waste, sewage_sludge)
        
        fluid : bool, indicator for the upgrade process
        
        eta_1 : float, value of conversion efficiency of the input carrier, has to be between 0 and 1
        
        eta_2 : float, value of conversion efficiency of the input hydrogen, has to be between 0 and 1
        
        methane_percentage : float, amount of methane in the ouput biogas of the conversion from input carrier

        Returns
        -------
        None.

        """

        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier Types:
        self.input_carrier_1 = 'wet_biomass'
        self.input_carrier_2 = "hydrogen"
        self.input_carrier_3 = "electricity"
        self.output_carrier_1 = "gas"
        self.output_carrier_2 = "heat_biomass"
        
        #Accounting:
        # self.u_input_carrier = []
        self._u_wet_bm = []
        self._u_hyd = []
        self._u_e = []
        self._v_h = []
        self._v_gas = []
        
        self.__tech_dict = tech_dict
        
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
        
        #Check Input Variables:
        if tech_dict['efficiency_primary'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency_primary'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")
            
        if tech_dict['efficiency_secondary'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency_secondary'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")
            
            
        self._eta_1 = tech_dict['efficiency_primary']
        self._methane_percentage = tech_dict['methane_percentage']
        self._maintenance_cost = tech_dict['maintenance_cost']

        if tech_dict['fluid']:
            self.__eta_e = 0.0205
            self.__eta_h = 0.087
        else:
            self.__eta_e = 0.0135
            self.__eta_h = 0.079
        
        #Assign Properties:
        self._eta = self._eta_1 + self._eta_1*(1 - self._methane_percentage)/self._methane_percentage
        self._eta_hyd = tech_dict['efficiency_secondary']
        
        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_wet_bm_aguh'] = self._u_wet_bm
        df['u_hyd_aguh'] = self._u_hyd
        df['u_e_aguh'] = self._u_e
        df['v_h_aguh'] = self._v_h
        df['v_gas_aguh'] = self._v_gas
        
        return df
    
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_wet_bm = init_vals.copy()
        self._u_hyd = init_vals.copy()
        self._u_e = init_vals.copy()
        self._v_h = init_vals.copy()
        self._v_gas = init_vals.copy()
        
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
        
        self._v_gas = self._v_gas[:n_hours]
        self._u_hyd = self._u_hyd[:n_hours]
        self._u_e = self._u_e[:n_hours]
        self._v_h = self._v_h[:n_hours]
        self._u_wet_bm = self._u_wet_bm[:n_hours]

        # self._v_h = self._v_h[:n_hours]

    def update_u_wet_bm(self, u_wet_bm_updated):        
        if len(u_wet_bm_updated) != len(self._u_wet_bm):
            raise ValueError("u_wet_bm_updated must have the same length as u_wet_bm!")            
        self._u_wet_bm = np.array(u_wet_bm_updated)
    
    def update_u_hyd(self, u_hyd_updated):        
        if len(u_hyd_updated) != len(self._u_hyd):
            raise ValueError("u_hyd_updated must have the same length as u_hyd!")            
        self._u_hyd = np.array(u_hyd_updated)
        
    def update_u_e(self, u_e_updated):        
        if len(u_e_updated) != len(self._u_e):
            raise ValueError("u_e_updated must have the same length as u_e!")            
        self._u_e = np.array(u_e_updated)
        
    def update_v_h(self, v_h_updated):        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")            
        self._v_h = np.array(v_h_updated)
        
    def update_v_gas(self, v_gas_updated):        
        if len(v_gas_updated) != len(self._v_gas):
            raise ValueError("v_gas_updated must have the same length as v_gas!")            
        self._v_gas = np.array(v_gas_updated)

    def compute_u_input_carrier(self):
        
        self._u_wet_bm = self._v_gas/self._eta
        self._u_hyd = self._v_gas*(1 - self._methane_percentage)/self._eta_hyd
        self._u_e = self._v_gas*(1 - self._methane_percentage)*self.__eta_e
        self._v_h = self._v_gas*(1 - self._methane_percentage)*self.__eta_h
    
    # def compute_v_gas(self):
        
    #     self._v_gas = self.u_input_carrier * self._eta
    #     self._u_hyd = self._v_gas*(1 - self._methane_percentage)/self._eta_hyd
    #     self._u_e = self._v_gas*(1 - self._methane_percentage)*self.__eta_e
    #     self._v_h = self._v_gas*(1 - self._methane_percentage)*self.__eta_h
        
    def generate_tech_dict(self, techs_dict, energy_scaling_factor):

        tech_dict = {
            'essentials':{
                'name':'Anaerobic Digestion Upgrade Hydrogen',
                'color':self.__tech_dict['color'],
                'parent':'conversion_plus',
                'carrier_in':'wet_biomass',
                'carrier_in_2': 'electricity',
                'carrier_in_3': 'hydrogen',
                'carrier_out':'gas',
                'carrier_out_2': 'heat_biomass',
                'primary_carrier_in': 'wet_biomass',
                'primary_carrier_out':'gas'
                },
            'constraints':{
                'energy_cap_max':self.__tech_dict['capacity_kWh'] / energy_scaling_factor if self.__tech_dict['capacity_kWh'] != 'inf' else 'inf',
                'energy_eff': self.__tech_dict['efficiency_primary'],
                'carrier_ratios':{
                    'carrier_in_2':{
                        'electricity': self._eta*(1 - self._methane_percentage)*self.__eta_e
                        },
                    'carrier_in_3':{
                        'hydrogen': self._eta*(1 - self._methane_percentage)/self._eta_hyd
                        },
                    'carrier_out_2':{
                        'heat_biomass': (1 - self._methane_percentage)*self.__eta_h
                        }
                    },
                'lifetime':self.__tech_dict['lifetime']
                },
            'costs':{
                'monetary':{
                    'energy_cap': self.__tech_dict['capital_cost'] * energy_scaling_factor,
                    'om_con':0.0, # this is reflected in the cost of the electricity
                    'interest_rate':self.__tech_dict['interest_rate'],
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    },
                } 
            }
        
        techs_dict['anaerobic_digestion_upgrade_hydrogen'] = tech_dict
        return techs_dict
    
    def get_u_wet_bm(self):
        self.len_test(self._u_wet_bm)
        return self._u_wet_bm
    
    def get_u_hyd(self):
        self.len_test(self._u_hyd)
        return self._u_hyd
    
    def get_u_e(self):
        self.len_test(self._u_e)
        return self._u_e
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
    
    def get_v_gas(self):
        self.len_test(self._v_gas)
        return self._v_gas
        
        
class AnaerobicDigestionCHP(TechCore): # aguc
    
    #TODO: REDO MECHANISM
    
    def __init__(self, tech_dict):
        """

        Parameters
        ----------
        input_carrier : TYPE
            DESCRIPTION.
        eta_e : float, value of conversion efficiency of the input carrier to electricity, has to be between 0 and 1
        
        eta_h : float, value of conversion efficiency of the input carrier to heat, has to be between 0 and 1

        Returns
        -------
        None.

        """

        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        #Carrier Types:
        self.input_carrier = 'wet_biomass'
        self.output_carrier_1 = "heat_biomass"
        self.output_carrier_2 = "electricity"
        
        #Accounting:
        # self.u_input_carrier = []
        self._u_wet_bm = []
        self._v_h = []
        self._v_e = []
        self._v_e_exp = []
        
        self.__tech_dict = tech_dict
        
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
        
        if tech_dict['efficiency_electricity'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency_electricity'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")
            
        if tech_dict['efficiency_heat'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency_heat'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")
        
        #Properties:
        self._eta_e = tech_dict['efficiency_electricity']
        self._eta_h = tech_dict['efficiency_heat']
        self._maintenance_cost = tech_dict['maintenance_cost']

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_wet_bm_aguc'] = self._u_wet_bm
        df['v_h_aguc'] = self._v_h
        df['v_e_aguc'] = self._v_e
        df['v_e_aguc_exp'] = self._v_e_exp
        
        return df
    
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_wet_bm = init_vals.copy()
        self._v_h = init_vals.copy()
        self._v_e = init_vals.copy()
        self._v_e_exp = init_vals.copy()
        
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
        
        self._v_gas = self._v_gas[:n_hours]
        self._v_e = self._v_e[:n_hours]
        self._v_h = self._v_h[:n_hours]
        self._u_wet_bm = self._u_wet_bm[:n_hours]

        # self._v_h = self._v_h[:n_hours]



    def compute_u_input_carrier_from_v_e(self):
        """
        Given a electricity output [kWh], computes the required wood input [kWh] and the heat output [kWh]

        Returns
        -------
        None.

        """
        
        self.u_input_carrier = self._v_e/self._eta_e
        self._v_h = self.u_input_carrier*self._eta_h
    
    def compute_u_input_carrier_from_v_h(self):
        """
        Given a heat output [kWh], computes the required wood input [kWh] and the electricity output [kWh]

        Returns
        -------
        None.

        """
        
        self.u_input_carrier = self._v_h/self._eta_h
        self._v_e = self.u_input_carrier*self._eta_e
    
    def compute_v_e__v_h(self):
        """
        Given a wood input [kWh], computes the electricity output [kWh] and the heat output [kWh]

        Returns
        -------
        None.

        """
        
        self._v_e = self.u_input_carrier*self._eta_e
        self._v_h = self.u_input_carrier*self._eta_h
        
    def update_u_wet_bm(self, u_wet_bm_updated):        
        if len(u_wet_bm_updated) != len(self._u_wet_bm):
            raise ValueError("u_wet_bm_updated must have the same length as u_wet_bm!")            
        self._u_wet_bm = np.array(u_wet_bm_updated)
        
    def update_v_h(self, v_h_updated):        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")            
        self._v_h = np.array(v_h_updated)
        
    def update_v_e(self, v_e_updated):        
        if len(v_e_updated) != len(self._v_e):
            raise ValueError("v_e_updated must have the same length as v_e!")            
        self._v_e = np.array(v_e_updated)
        
    def update_v_e_exp(self, v_e_exp_updated):        
        if len(v_e_exp_updated) != len(self._v_e_exp):
            raise ValueError("v_e_exp_updated must have the same length as v_e_exp!")            
        self._v_e_exp = np.array(v_e_exp_updated)
        
    def generate_tech_dict(self, techs_dict, energy_scaling_factor):
        
        tech_dict = {
            'essentials':{
                'name':'Anaerobic Digestion CHP',
                'color':self.__tech_dict['color'],
                'parent':'conversion_plus',
                'carrier_in':'wet_biomass',
                'carrier_out':'electricity',
                'carrier_out_2': 'heat_biomass',
                'primary_carrier_out':'electricity'
                },
            'constraints':{
                'export_carrier': 'electricity',
                'energy_cap_max':self.__tech_dict['capacity_kWh'] / energy_scaling_factor if self.__tech_dict['capacity_kWh'] != 'inf' else 'inf',
                'energy_eff': self.__tech_dict['efficiency_electricity'],
                'carrier_ratios':{
                    'carrier_out_2':{
                        'heat_biomass': self.__tech_dict['efficiency_heat']/self.__tech_dict['efficiency_electricity']
                        }
                    },
                'lifetime':self.__tech_dict['lifetime']
                },
            'costs':{
                'monetary':{
                    'energy_cap': self.__tech_dict['capital_cost'] * energy_scaling_factor,
                    'om_con':0.0, # this is reflected in the cost of the electricity
                    'interest_rate':self.__tech_dict['interest_rate'],
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    },
                } 
            }
        
        techs_dict['anaerobic_digestion_chp'] = tech_dict
        return techs_dict
    
    def get_u_wet_bm(self):
        self.len_test(self._u_wet_bm)
        return self._u_wet_bm
    
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e
    
    def get_v_e_exp(self):
        self.len_test(self._v_e_exp)
        return self._v_e_exp
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h    
        
class WoodGasificationUpgrade(TechCore): # wgu
    
    def __init__(self, tech_dict):
        """

        Parameters
        ----------
        eta : float, value of conversion efficiency, has to be between 0 and 1
            
        fluid : bool, indicator for the upgrade process

        Returns
        -------
        None.

        """

        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier Types:
        self.input_carrier_1 = "wood"
        self.input_carrier_2 = "electricity"
        self.output_carrier_1 = "gas"
        self.output_carrier_2 = "heat_biomass"
        
        #Accounting:
        # self.u_w = []
        self._u_wd = []
        self._u_e = []
        self._v_h = []
        self._v_gas = []
        
        self.__tech_dict = tech_dict
        
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
        
        #Check Input Variables:
        if tech_dict['efficiency'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")
        
        #Assign Technology Efficiancies:
        self.__eta_e = 0.1
        self.__eta_h = 0.09
            
        self._eta = tech_dict['efficiency']
        self._maintenance_cost = tech_dict['maintenance_cost']

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_wd_wgu'] = self._u_wd
        df['u_e_wgu'] = self._u_e
        df['v_h_wgu'] = self._v_h
        df['v_gas_wgu'] = self._v_gas
        
        return df
    
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_wd = init_vals.copy()
        self._u_e = init_vals.copy()
        self._v_h = init_vals.copy()
        self._v_gas = init_vals.copy()
        
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
        
        self._v_gas = self._v_gas[:n_hours]
        self._u_e = self._u_e[:n_hours]
        self._v_h = self._v_h[:n_hours]
        self._u_wd = self._u_wd[:n_hours]

        # self._v_h = self._v_h[:n_hours]



    def compute_u_w(self):
        """
        Given a gas output [kWh], calculates the required wood input [kWh],
        the required electricity input [kWh] and the heat output [kWh].

        Returns
        -------
        None.

        """
        
        self.u_w = self._v_gas/self._eta
        self._u_e = self._v_gas*self.__eta_e
        self._v_h = self._v_gas*self.__eta_h
    
    
    def compute_v_gas(self):
        """
        Given a wood input [kWh], calculates the required electricity input [kWh],
        the gas output [kWh] and the heat output [kWh].

        Returns
        -------
        None.

        """
        
        self._v_h = self._u_wd*self._eta
        self._u_e = self._v_gas*self.__eta_e
        self._v_h = self._v_gas*self.__eta_h
        
    def update_u_wd(self, u_wd_updated):        
        if len(u_wd_updated) != len(self._u_wd):
            raise ValueError("u_wd_updated must have the same length as u_wd!")            
        self._u_wd = np.array(u_wd_updated)
        
    def update_u_e(self, u_e_updated):        
        if len(u_e_updated) != len(self._u_e):
            raise ValueError("u_e_updated must have the same length as u_e!")            
        self._u_e = np.array(u_e_updated)
        
    def update_v_h(self, v_h_updated):        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")            
        self._v_h = np.array(v_h_updated)
        
    def update_v_gas(self, v_gas_updated):        
        if len(v_gas_updated) != len(self._v_gas):
            raise ValueError("v_gas_updated must have the same length as v_gas!")            
        self._v_gas = np.array(v_gas_updated)
    
    def generate_tech_dict(self, techs_dict, energy_scaling_factor):
        
        
        tech_dict = {
            'essentials':{
                'name':'Wood Gasification Upgrade',
                'color':self.__tech_dict['color'],
                'parent':'conversion_plus',
                'carrier_in':'wood',
                'carrier_in_2': 'electricity',
                'carrier_out': 'gas',
                'carrier_out_2': 'heat_biomass',
                'primary_carrier_in': 'wood',
                'primary_carrier_out':'gas'
                },
            'constraints':{
                'energy_cap_max':self.__tech_dict['capacity_kWh'] / energy_scaling_factor if self.__tech_dict['capacity_kWh'] != 'inf' else 'inf',
                'energy_eff': self.__tech_dict['efficiency'],
                'carrier_ratios':{
                    'carrier_in_2':{
                        'electricity': 0.0625
                        },
                    'carrier_out_2':{
                        'heat_biomass': 0.09/0.625
                        }
                    },
                'lifetime':self.__tech_dict['lifetime']
                },
            'costs':{
                'monetary':{
                    'energy_cap': self.__tech_dict['capital_cost'] * energy_scaling_factor,
                    'om_con':0.0, # this is reflected in the cost of the electricity
                    'interest_rate':self.__tech_dict['interest_rate'],
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    },
                } 
            }
        
        techs_dict['wood_gasification_upgrade'] = tech_dict
        return techs_dict

    def get_u_e(self):
        self.len_test(self._u_e)
        return self._u_e
    
    def get_u_wd(self):
        self.len_test(self._u_wd)
        return self._u_wd
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
    
    def get_v_gas(self):
        self.len_test(self._v_gas)
        return self._v_gas
            

class WoodGasificationUpgradeHydrogen(TechCore): # wguh
    
    def __init__(self, tech_dict):
        """

        Parameters
        ----------
        eta : float, value of conversion efficiency, has to be between 0 and 1
            
        fluid : bool, indicator for the upgrade process

        Returns
        -------
        None.

        """
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier Types:
        self.input_carrier_1 = "wood"
        self.input_carrier_2 = "hydrogen"
        self.input_carrier_3 = "electricity"
        self.output_carrier_1 = "gas"
        self.output_carrier_2 = "heat_biomass"
        
        #Accounting:
        # self.u_w = []
        self._u_wd = []
        self._u_hyd = []
        self._u_e = []
        self._v_h = []
        self._v_gas = []
        
        self.__tech_dict = tech_dict
        
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
        
        #Check Input Variables:
        if tech_dict['efficiency_primary'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency_primary'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")
        
        #Assign Technology Efficiancies:
        self.__eta_e = 0.1
        self.__eta_h = 0.126
        
        self._eta = tech_dict['efficiency_primary']
        self._eta_hyd = tech_dict['efficiency_secondary'] #TODO: Find actuall efficiency
        self._maintenance_cost = tech_dict['maintenance_cost']

        self._methane_percentage = tech_dict['methane_percentage']
        
        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_wd_wguh'] = self._u_wd
        df['u_hyd_wguh'] = self._u_hyd
        df['u_e_wguh'] = self._u_e
        df['v_h_wguh'] = self._v_h
        df['v_gas_wguh'] = self._v_gas
        
        return df
    
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_wd = init_vals.copy()
        self._u_hyd = init_vals.copy()
        self._u_e = init_vals.copy()
        self._v_h = init_vals.copy()
        self._v_gas = init_vals.copy()

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
        
        self._v_gas = self._v_gas[:n_hours]
        self._u_e = self._u_e[:n_hours]
        self._v_h = self._v_h[:n_hours]
        self._u_wd = self._u_wd[:n_hours]
        self._u_hyd = self._u_hyd[:n_hours]

        # self._v_h = self._v_h[:n_hours]



    def compute_u_w(self):
        """
        Given a gas output [kWh], calculates the required wood input [kWh],
        the required electricity input [kWh], the required hydrogen input [kWh] and the heat output [kWh].

        Returns
        -------
        None.

        """
        
        self.u_w = self._v_gas/self._eta
        self._u_hyd = self._v_gas/self._eta_hyd
        self._u_e = self._v_gas/self.__eta_e
        self._v_h = self._v_gas*self.__eta_h
    
    
    def compute_v_gas(self):
        """
        Given a wood input [kWh], calculates the required electricity input [kWh], 
        the required hydrogen input [kWh], the gas output [kWh] and the heat output [kWh].

        Returns
        -------
        None.

        """
        
        self._v_gas = self.u_w*self._eta
        self._u_hyd = self._v_gas/self._eta_hyd
        self._u_e = self._v_gas*self.__eta_e
        self._v_h = self._v_gas*self.__eta_h
        
    def update_u_wd(self, u_wd_updated):        
        if len(u_wd_updated) != len(self._u_wd):
            raise ValueError("u_wd_updated must have the same length as u_wd!")            
        self._u_wd = np.array(u_wd_updated)
    
    def update_u_hyd(self, u_hyd_updated):        
        if len(u_hyd_updated) != len(self._u_hyd):
            raise ValueError("u_hyd_updated must have the same length as u_hyd!")            
        self._u_hyd = np.array(u_hyd_updated)
        
    def update_u_e(self, u_e_updated):        
        if len(u_e_updated) != len(self._u_e):
            raise ValueError("u_e_updated must have the same length as u_e!")            
        self._u_e = np.array(u_e_updated)
        
    def update_v_h(self, v_h_updated):        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")            
        self._v_h = np.array(v_h_updated)
        
    def update_v_gas(self, v_gas_updated):        
        if len(v_gas_updated) != len(self._v_gas):
            raise ValueError("v_gas_updated must have the same length as v_gas!")            
        self._v_gas = np.array(v_gas_updated)
        
    def generate_tech_dict(self, techs_dict, energy_scaling_factor):
        
        tech_dict = {
            'essentials':{
                'name':'Wood Gasification Upgrade Hydrogen',
                'color':self.__tech_dict['color'],
                'parent':'conversion_plus',
                'carrier_in':'wood',
                'carrier_in_2': 'electricity',
                'carrier_in_3': 'hydrogen',
                'carrier_out':'gas',
                'carrier_out_2': 'heat_biomass',
                'primary_carrier_in': 'wood',
                'primary_carrier_out':'gas'
                },
            'constraints':{
                'energy_cap_max':self.__tech_dict['capacity_kWh'] / energy_scaling_factor if self.__tech_dict['capacity_kWh'] != 'inf' else 'inf',
                'energy_eff': self.__tech_dict['efficiency_primary'],
                'carrier_ratios':{
                    'carrier_in_2':{
                        'electricity': self._eta*(1 - self._methane_percentage)*self.__eta_e
                        },
                    'carrier_in_3':{
                        'hydrogen': self._eta*(1 - self._methane_percentage)/self._eta_hyd
                        },
                    'carrier_out_2':{
                        'heat_biomass': (1 - self._methane_percentage)*self.__eta_h
                        }
                    },
                'lifetime':self.__tech_dict['lifetime']
                },
            'costs':{
                'monetary':{
                    'energy_cap': self.__tech_dict['capital_cost'] * energy_scaling_factor,
                    'om_con':0.0, # this is reflected in the cost of the electricity
                    'interest_rate':self.__tech_dict['interest_rate'],
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    },
                } 
            }
        
        techs_dict['wood_gasification_upgrade_hydrogen'] = tech_dict
        return techs_dict

    def get_u_hyd(self):
        self.len_test(self._u_hyd)
        return self._u_hyd
    
    def get_u_e(self):
        self.len_test(self._u_e)
        return self._u_e
    
    def get_u_wd(self):
        self.len_test(self._u_wd)
        return self._u_wd

    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
    
    def get_v_gas(self):
        self.len_test(self._v_gas)
        return self._v_gas
            
            
class WoodGasificationCHP(TechCore): # wguc
    
    def __init__(self, tech_dict):
        """

        Parameters
        ----------
        eta_e : float, electric efficiency of technology
        
        eta_h : float, heat efficiency of technology
        
        Returns
        -------
        None.

        """
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        
        # Carrier Types:
        self.input_carrier = "wood"
        self.output_carrier_1 = "electricity"
        self.output_carrier_2 = "heat_biomass"
        
        #Accounting:
        # self.u_w = []
        self._u_wd = []
        self._v_e = []
        self._v_h = []
        self._v_e_exp = []
        
        self.__tech_dict = tech_dict
        
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
        
        #Check Input Variables:
        if tech_dict['efficiency_electricity'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency_electricity'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")
        if tech_dict['efficiency_heat'] > 1:
            raise Exception("This technology cannot have an efficiency above 1.")
        if tech_dict['efficiency_heat'] < 0:
            raise Exception("This technology cannot have an efficiency below 0.")
        
        #Assign Technology Efficiancies:
        self._eta_e = tech_dict['efficiency_electricity']
        self._eta_h = tech_dict['efficiency_heat']
        self._maintenance_cost = tech_dict['maintenance_cost']

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_wd_wguc'] = self._u_wd
        df['v_e_wguc'] = self._v_e
        df['v_h_wguc'] = self._v_h
        df['v_e_wguc_exp'] = self._v_e_exp
        
        return df
    
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_wd = init_vals.copy()
        self._v_e = init_vals.copy()
        self._v_h = init_vals.copy()
        self._v_e_exp = init_vals.copy()
        
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
        
        self._v_e = self._v_e[:n_hours]
        self._v_h = self._v_h[:n_hours]
        self._u_wd = self._u_wd[:n_hours]
        self._v_e_exp = self._v_e_exp[:n_hours]

        # self._v_h = self._v_h[:n_hours]



    def compute_u_w_from_v_e(self):
        """
        Given a electricity output [kWh], computes the required wood input [kWh] and the heat output [kWh]

        Returns
        -------
        None.

        """
        
        self.u_w = self._v_e/self._eta_e
        self._v_h = self.u_w*self._eta_h
    
    def compute_u_w_from_v_h(self):
        """
        Given a heat output [kWh], computes the required wood input [kWh] and the electricity output [kWh]

        Returns
        -------
        None.

        """
        
        self.u_w = self._v_h/self._eta_h
        self._v_e = self.u_w*self._eta_e
    
    def compute_v_e__v_h(self):
        """
        Given a wood input [kWh], computes the electricity output [kWh] and the heat output [kWh]

        Returns
        -------
        None.

        """
        
        self._v_e = self.u_w*self._eta_e
        self._v_h = self.u_w*self._eta_h
        
    def update_u_wd(self, u_wd_updated):        
        if len(u_wd_updated) != len(self._u_wd):
            raise ValueError("u_wd_updated must have the same length as u_wd!")            
        self._u_wd = np.array(u_wd_updated)
        
    def update_v_e(self, v_e_updated):        
        if len(v_e_updated) != len(self._v_e):
            raise ValueError("v_e_updated must have the same length as v_e!")            
        self._v_e = np.array(v_e_updated)
        
    def update_v_h(self, v_h_updated):        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")            
        self._v_h = np.array(v_h_updated)
        
    def update_v_e_exp(self, v_e_exp_updated):        
        if len(v_e_exp_updated) != len(self._v_e_exp):
            raise ValueError("v_e_exp_updated must have the same length as v_e_exp!")            
        self._v_e_exp = np.array(v_e_exp_updated)
        
    def generate_tech_dict(self, techs_dict, energy_scaling_factor):
        
        tech_dict = {
            'essentials':{
                'name':'Hydrothermal Gasification CHP',
                'color':self.__tech_dict['color'],
                'parent':'conversion_plus',
                'carrier_in': 'wood',
                'carrier_out': 'electricity',
                'carrier_out_2': 'heat_biomass',
                'primary_carrier_out':'electricity'
                },
            'constraints':{
                'export_carrier': 'electricity',
                'energy_cap_max':self.__tech_dict['capacity_kWh'] / energy_scaling_factor if self.__tech_dict['capacity_kWh'] != 'inf' else 'inf',
                'energy_eff': self.__tech_dict['efficiency_electricity'],
                'carrier_ratios':{
                    'carrier_out_2':{
                        'heat_biomass': self.__tech_dict['efficiency_heat']/self.__tech_dict['efficiency_electricity']
                        }
                    },
                'lifetime':self.__tech_dict['lifetime']
                },
            'costs':{
                'monetary':{
                    'energy_cap': self.__tech_dict['capital_cost'] * energy_scaling_factor,
                    'om_con':0.0, # this is reflected in the cost of the electricity
                    'interest_rate':self.__tech_dict['interest_rate'],
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    },
                } 
            }
        
        techs_dict['wood_gasification_chp'] = tech_dict
        return techs_dict

    def get_u_wd(self):
        self.len_test(self._u_wd)
        return self._u_wd
    
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e

    def get_v_e_exp(self):
        self.len_test(self._v_e_exp)
        return self._v_e_exp
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h

        
            


