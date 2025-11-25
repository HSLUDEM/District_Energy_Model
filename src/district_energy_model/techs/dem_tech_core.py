# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 12:50:32 2024

@author: UeliSchilt
"""

"Parent class for tech classes."
import numpy as np

class TechCore:
    
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
    # def initialise_zero(self, variables, n_days):
    #     n_hours = n_days*24
        
    #     for var in variables:
    #         var = np.array([0]*n_hours)
    
    # def initialise_zero(self, variable, n_days):
    #     n_hours = n_days*24
    #     variable = np.array([0]*n_hours)