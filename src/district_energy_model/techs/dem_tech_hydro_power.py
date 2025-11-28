# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 11:20:17 2024

@author: Somesh
"""

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore


class HydroPower(TechCore):
    
    """
    Conversion technology: hydro power.
    """
    
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
        self.output_carrier = 'electricity'
        
        # Accounting:
        self._v_e = []
        self._v_e_cons = []
        self._v_e_exp = []
        self._v_e_pot = []
        self._v_e_pot_remain = []
        self._v_co2 = []
        
        '''
        - max capacity [GW]
        - specific percentage of potential --> for scenario
        '''
    
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the hydro power technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        # Properties:
        self._capex = tech_dict['capex']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._export_subsidy = tech_dict['export_subsidy']

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['v_e_hydro'] = self.get_v_e()
        df['v_e_hydro_cons'] = self.get_v_e_cons()
        df['v_e_hydro_exp'] = self.get_v_e_exp()
        df['v_e_hydro_pot'] = self.get_v_e_pot()
        df['v_e_hydro_pot_remain'] = self.get_v_e_pot_remain()        
        df['v_co2_hydro'] = self.get_v_co2()
        
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
        self._v_e_cons = self._v_e_cons[:n_hours]
        self._v_e_exp = self._v_e_exp[:n_hours]
        self._v_e_pot = self._v_e_pot[:n_hours]
        self._v_e_pot_remain = self._v_e_pot_remain[:n_hours]
        self._v_co2 = self._v_co2[:n_hours]
        
    def create_techs_dict(self,
                          techs_dict,
                          header,
                          name,
                          color,
                          resource,
                          energy_cap,
                          capex_0=False
                          ):
        
        if capex_0==False:
            capex = self._capex
        elif capex_0==True:
            capex = 0
        
        techs_dict[header] = {
            'essentials':{
                'name':name,
                'color':color,
                'parent':'supply',
                'carrier': 'electricity'
                },
            'constraints':{
                'export_carrier': 'electricity',
                'resource': resource,
                'resource_unit':'energy',  # [kWh]
                'energy_cap_max': energy_cap, # kWp # relevant?
                'force_resource': True,
                'lifetime': 100
                },
            'costs':{
                'monetary':{
                    'interest_rate':0.0,
                    'om_con':0.0,
                    'energy_cap':capex,
                    'om_annual': self._maintenance_cost,
                    'export': -self._export_subsidy,
                    },
                'emissions_co2':{
                    'om_prod':0.0
                    }
                }
            }
        return techs_dict
    
    def update_v_e_pot(self, v_e_pot_updated):
        self._v_e_pot = np.array(v_e_pot_updated)
        
        if len(self._v_e)>0:
            self.__compute_v_e_pot_remain()
        else:
            self._v_e_pot_remain = self._v_e_pot
        
    def update_v_e(self, v_e_updated):
        self._v_e = np.array(v_e_updated)
        
        self.__compute_v_e_pot_remain()
        
        self.__compute_v_co2()
        
    def update_v_e_cons(self, v_e_cons_updated):
        if len(v_e_cons_updated) != len(self._v_e):
            raise ValueError()        
        self._v_e_cons = np.array(v_e_cons_updated)
    
    def update_v_e_exp(self, v_e_exp_updated):
        if len(v_e_exp_updated) != len(self._v_e):
            raise ValueError()        
        self._v_e_exp = np.array(v_e_exp_updated)
        
    def __compute_v_e_pot_remain(self):
        if len(self._v_e_pot)==0:
            raise ValueError()
        self._v_e_pot_remain = self._v_e_pot - self._v_e
        
    def __compute_v_co2(self):
        self._v_co2 = self._v_e*self.__tech_dict['co2_intensity']
        
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e
    
    def get_v_e_cons(self):
        self.len_test(self._v_e_cons)
        return self._v_e_cons
    
    def get_v_e_exp(self):
        self.len_test(self._v_e_exp)
        return self._v_e_exp
    
    def get_v_e_pot(self):
        self.len_test(self._v_e_pot)
        return self._v_e_pot
    
    def get_v_e_pot_remain(self):
        self.len_test(self._v_e_pot_remain)
        return self._v_e_pot_remain
    
    def get_v_co2(self):
        self.len_test(self._v_co2)
        return self._v_co2
    
    # @staticmethod
    # def get_v_e_pot_remain(v_e_hydro, v_e_hydro_pot):
    #     """
    #     Return the remaining potential for local hydro power.
        
    #     The total hydro power potential remains constant, as it includes the
    #     installed and additional potential.

    #     Parameters
    #     ----------
    #     v_e_hydro : pandas dataseries
    #         Realised (i.e. installed) hydro power potential [kWh].
    #     v_e_pv_pot : pandas dataseries
    #         Total hydro power potential (incl. installed) [kWh].

    #     Returns
    #     -------
    #     v_e_hydro_pot_remain : pandas dataseries
    #         Remaining hydro power potential after application of a scenario
    #         or optimistion [kWh].

    #     """
        
    #     v_e_hydro_pot_remain = v_e_hydro_pot - v_e_hydro
        
    #     return v_e_hydro_pot_remain