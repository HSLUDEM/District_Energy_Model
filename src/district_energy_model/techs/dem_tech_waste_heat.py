# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:00:58 2024

@author: UeliSchilt
"""

import pandas as pd
import numpy as np
import sys
import os

from district_energy_model.techs.dem_tech_core import TechCore

# Add modules from parent directory:
# abspath = os.path.abspath(__file__)
# dname = os.path.dirname(abspath)
# parent_dir_path = os.path.dirname(dname)
# sys.path.insert(0, parent_dir_path)

from district_energy_model import dem_helper

class WasteHeat(TechCore):
    
    """
    Conversion technology: Waste heat.
    
    Possible inputs:
    
    """
    
    def __init__(
            self,
            tech_dict
            ):
        
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
                
        self.timeseries = ...
        self.update_tech_properties(tech_dict)
                
        # Carrier types:
        self.output_carrier = 'heat_wh'
        
        # Accounting:
        self._v_h = []
        self._v_h_resource = []
        self._v_co2 = []
        
        # Annual values:
        self._v_h_yr = ...
        self._v_h_resource_yr = ...
        self._v_co2_yr = ...
    
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the waste heat technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        # Properties:
        # self.v_max = tech_dict['kWp_max']

        if isinstance(tech_dict['lifetime'], list):

            self._lifetime = tech_dict['lifetime']
            self._interest_rate = tech_dict['interest_rate']
            self._co2_intensity = tech_dict['co2_intensity']
            self._capex = tech_dict['capex']
            self._maintenance_cost = tech_dict['maintenance_cost']
            self._timeseries_file_path = tech_dict['timeseries_file_path']
            self._tariff_CHFpkWh = tech_dict['tariff_CHFpkWh']
        else:
            self._lifetime = [tech_dict['lifetime']]
            self._interest_rate = [tech_dict['interest_rate']]
            self._co2_intensity = [tech_dict['co2_intensity']]
            self._capex = [tech_dict['capex']]
            self._maintenance_cost = [tech_dict['maintenance_cost']]
            self._timeseries_file_path = [tech_dict['timeseries_file_path']]
            self._tariff_CHFpkWh = [tech_dict['tariff_CHFpkWh']]
        # self._maintenance_cost = tech_dict['maintenance_cost']

        self.number_of_instances = len(self._lifetime)
        # Update input dict:
        self.__tech_dict = tech_dict
        

    def initialise_finite(self, n_days):
        n_hours = n_days*24
        zero_vals = np.zeros(shape = (self.number_of_instances, n_hours))
        timeseries_data = np.zeros(shape = (self.number_of_instances, n_hours))
        self._v_h_resource = zero_vals.copy()
        for i in range(len(self._timeseries_file_path)):
            path = self._timeseries_file_path[i]
            if path.endswith(".feather"):
                timeseries_data[i,:] = pd.read_feather(path).to_numpy()[:n_hours, 0]
            

            self._v_h_resource[i,:] = timeseries_data[i,:].copy()
        self._v_h = zero_vals.copy()
        self._v_co2 = zero_vals.copy()

    def update_df_results(self, df):
        
        df['v_h_wh'] = self.get_v_h() #Total
        df['v_h_resource_wh'] = self.get_v_h_resource().sum(axis=0) #Total
        df['v_co2_wh'] = self.get_v_co2() #Total
        
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

        self._v_h = self._v_h[:, :n_hours]
        self._v_h_resource = self._v_h_resource[:, :n_hours]
        self._v_co2 = self._v_co2[:, :n_hours]
        
        
    def __compute_v_co2(self):
        for i in range(self.number_of_instances):
            self.len_test(self._v_h[i])            
            self._v_co2[i] = self._v_h[i]*self._co2_intensity[i]
    
    # def __compute_import_cost(self):
    #     for i in range(self.number_of_instances):
    #         self.len_test(self._v_h[i])
    #         self._v_mon[i] = self._tariff_CHFpkWh[i] * self._v_h[i]
    
    def create_tech_groups_dict(self, tech_groups_dict):
        
        tech_groups_dict['waste_heat'] = {
            'essentials':{
                'parent':'supply',
                'carrier': 'heat_wh'
                },
            'constraints':{
                },
            'costs':{
                'monetary':{
                    'om_con':0.0
                    }
                }
            }
        
        return tech_groups_dict
        
    def create_techs_dict(self,
                          techs_dict,
                          header,
                          name, 
                          color, 
                          resources,
                          energy_scaling_factor
                        #   energy_cap,
                          ):

        for i in range(self.number_of_instances):
            capex = self._capex[i]
            
            techs_dict[header+"_"+str(i)] = {
                'essentials':{
                    'name': name,
                    'color': color,
                    'parent': 'waste_heat'
                    },
                'constraints':{
                    'lifetime': self._lifetime[i],
                    'resource': resources[i],
                    # 'energy_cap_max': energy_cap
                    },
                'costs':{
                    'monetary':{
                        'interest_rate':self._interest_rate[i],
                        'energy_cap': capex * energy_scaling_factor,
                        'om_annual': self._maintenance_cost[i] * energy_scaling_factor,
                        'om_prod': self._tariff_CHFpkWh[i] * energy_scaling_factor
                        },
                    'emissions_co2':{
                        'om_prod':self._co2_intensity[i] * energy_scaling_factor, 
                        }
                    }
                }    
        
        return techs_dict
    
    def get_v_h(self):
        for i in range(self.number_of_instances):
            self.len_test(self._v_h[i])
        return self._v_h.sum(axis = 0)
    
    def get_v_h_resource(self):
        for i in range(self.number_of_instances):
            self.len_test(self._v_h_resource[i])
        return self._v_h_resource    
    
    def get_v_co2(self):
        for i in range(self.number_of_instances):
            self.len_test(self._v_co2[i])
        return self._v_co2.sum(axis=0)
    
    def update_v_h(self, v_h_updated):
        
        if np.shape(v_h_updated) != np.shape(self._v_h):
            raise ValueError("v_h_updated must have the same shape as v_h!")
        
        self._v_h = np.array(v_h_updated)
        

        self.__compute_v_co2()
        # self.__compute_import_cost()

    def update_v_h_resource(self, v_h_resource_updated):
        
        if np.shape(v_h_resource_updated) != np.shape(self._v_h_resource):
            raise ValueError("v_h_resource_updated must have the same shape as v_h_resource!")
        
        self._v_h_resource = np.array(v_h_resource_updated)
                
    def get_energy_costs(self):
        tot_cost = 0.0
        for i in range(self.number_of_instances):
            tot_cost += self._tariff_CHFpkWh[i]*np.sum(self._v_h[i,:])
        return tot_cost

    def get_total_capex(self):
        new_capex = np.sum([self._capex[i]*(self._v_h[i].max()) for i in range(self.number_of_instances)])
        if new_capex < 0:
            new_capex = 0
        total_capex = new_capex
        return total_capex
    
    def get_total_maintenance(self):
        new_mc = np.sum([self._maintenance_cost[i]*(self._v_h[i].max()) for i in range(self.number_of_instances)])
        if new_mc < 0:
            new_mc = 0
        total_mc = new_mc
        return total_mc

    def get_total_annualized_capex(self):

        tacapex = 0.0

        for i in range(self.number_of_instances):
            af =  1 / self._lifetime[i]
            if self._interest_rate[i] != 0:
                r = self._interest_rate[i]
                t = self._lifetime[i]
                af = (r * (1 + r) ** t) / ((1 + r) ** t - 1)
            tacapex += af * self._capex[i] * (self._v_h[i].max())
            
        return tacapex
            

