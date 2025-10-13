# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:22:46 2024

@author: UeliSchilt
"""

class HeatExchanger:
    
    def __init__(self, eta):
        
        """
        Initialise technology parameters.
        
        Parameters
        ----------
            
        eta : float
            heat exchanger efficiency [-]
    
        Returns
        -------
        n/a
        """
        
        # Properties:
        self.eta = eta
        
        # Define carrier types:
        self.input_carrier = 'heat'
        self.output_carrier = 'heat'
    
    def heat_transfer(self):
        # UNDER CONSTRUCTION
        pass

    def heat_loss(self):
        # UNDER CONSTRUCTION
        pass