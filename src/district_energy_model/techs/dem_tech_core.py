# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 12:50:32 2024

@author: UeliSchilt
"""

"Parent class for tech classes."
import numpy as np
from abc import ABC, abstractmethod
import warnings

class TechCore(ABC):
    
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
        
        # Initialize properties:
        # self.update_tech_properties(tech_dict)
        
        # Carrier types:
        # --> to be implemented in child classes
        
        # Accounting:
        # --> to be implemented in child classes
        
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
        
        # Update tech dict:
        self.__tech_dict = tech_dict
        
        # Tests:
        # --> To be implemented in child classes
        
        # Properties:
        # --> To be implemented in child classes


    def update_df_results(self, df):
        
        ...
        
        # --> To be implemented in child class
        
        return df
    
    def len_test(self,flow):
        if len(flow)==0:
            raise ValueError()
            
    def num_test(self,var):
        if isinstance(var, (int, float, np.integer))==False:
            raise ValueError()
            
    # def num_test_inf(self, var):
    #     if not (isinstance(var, (int, float, np.integer)) or np.isinf(var)):
    #         raise ValueError("var must be numeric or inf")
    
    def num_test_inf(self, var):
        if isinstance(var, str) and var.lower() in ('inf', '-inf'):
            return  # allow string forms of infinity
        if not (isinstance(var, (int, float, np.integer)) or np.isinf(var)):
            raise ValueError("var must be numeric or inf")

            
    def get_maintenance_cost(self): #per unit kW oder kWh, depending on the technology
        return self._maintenance_cost*sum([(1.0/((1+self._interest_rate)**(i+1))) for i in range(self._lifetime)])
    
    
    def get_energy_costs(self):
        pass
        # --> To be implemented in child class

    def get_energy_revenue(self):
        pass
        # --> To be implemented in child class

    def get_total_capex(self):
        pass
        # --> To be implemented in child class
    
    def get_total_maintenance(self):
        pass
        # --> To be implemented in child class


    # def initialise_zero(self, variables, n_days):
    #     n_hours = n_days*24
        
    #     for var in variables:
    #         var = np.array([0]*n_hours)
    
    # def initialise_zero(self, variable, n_days):
    #     n_hours = n_days*24
    #     variable = np.array([0]*n_hours)

 
    def get_output(self):
        for attr in ['_v_h', '_v_e']:
            if hasattr(self, attr):
                return getattr(self, attr)
        raise AttributeError("No output attribute found (_v_h or _v_e)")
    
    def get_v_max(self):
        for attr in ['v_h_max', 'v_max', 'kw_max', 'kW_el_max']:
            if hasattr(self, attr):
                return getattr(self, attr)
            else: 
                warnings.warn("No max_capacity attribute found returning 'inf'")
                return 'inf'
    
    def get_power_up_for_replacement(self):
        return 0
    
    def get_only_allow_existing(self):
        return False

    def get_existing(self):
        energy_cap_old = self.get_output().max()
        needs_replacement = self.get_power_up_for_replacement()

        energy_cap_zero_capex = energy_cap_old-needs_replacement if energy_cap_old>=needs_replacement else 0.0
        energy_cap_low_capex = needs_replacement if energy_cap_old>=needs_replacement else energy_cap_old
        
        if self.get_only_allow_existing():
            cap_one_to_one_replacement = 0.0
            cap_new = 0.0
        else:
            cap_one_to_one_replacement = energy_cap_low_capex
            if self.get_v_max() == 'inf':
                cap_new = 'inf'
            else:
                cap_new = self.get_v_max() - cap_one_to_one_replacement - energy_cap_zero_capex
        
        if self.get_v_max() != 'inf':
            if cap_new < 0.0:
                cap_one_to_one_replacement += cap_new
                cap_new = 0.0
            if cap_one_to_one_replacement < 0.0:
                energy_cap_zero_capex += cap_one_to_one_replacement
                cap_one_to_one_replacement = 0.0
            if energy_cap_zero_capex <= 0.0:
                energy_cap_zero_capex = 0.0
            
        self.existing = energy_cap_zero_capex
        self.needs_replacement = cap_one_to_one_replacement
        self.cap_new = cap_new

        return energy_cap_zero_capex, cap_one_to_one_replacement, cap_new