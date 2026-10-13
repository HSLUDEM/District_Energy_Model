# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:00:15 2024

@author: PascalVecsei
"""

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore

class GridExport(TechCore):
    
    """
    Export technology: grid Export.
    """
    
    def __init__(self, paths, tech_dict):
        
        """
        Initialise grid supply parameters.
        
        Parameters
        ----------
            
        tech_dict : dict
            Dictionary with technology parameters (subset of scen_techs).
    
        Returns
        -------
        n/a
        """
        
        super().__init__(tech_dict)
        
        self.paths = paths
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        self.init_timeseries()
        # Carrier types:
        self.input_carrier = 'electricity'
        
        # Accounting:
        self._f_e = [] #f for feedin
        self._f_co2 = []
        
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the grid supply technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        self._kW_max = tech_dict['kW_max'] # Max electric capacity
        self._lifetime = tech_dict['lifetime']


        self._interest_rate = tech_dict['interest_rate']

        self._tariff_mode = tech_dict['tariff_mode']
        self._co2_intensity_mode = tech_dict['co2_intensity_mode']

        self._tariff_timeseries_filepath = tech_dict['tariff_timeseries_filepath']
        self._co2_intensity_timeseries_filepath = tech_dict['co2_intensity_timeseries_filepath']

        self._constant_tariff_CHFpkWh = tech_dict['constant_tariff_CHFpkWh']
        self._constant_co2_intensity = tech_dict['constant_co2_intensity']

        self._capex = 0
        self._capex_one_to_one_replacement = 0
        self._maintenance_cost = 0
        
        self.__tech_dict = tech_dict
        
    def init_timeseries(self):

        #Price

        n_hours = 365*24

        self._tariff_timeseries = np.zeros(n_hours)
        self._co2_intensity_timeseries = np.zeros(n_hours)

        if self._tariff_mode == 'const':
            self._tariff_timeseries = self._tariff_timeseries + self._constant_tariff_CHFpkWh
        elif self._tariff_mode == 'file':
            if self._tariff_timeseries_filepath.endswith(".feather"):
                self._tariff_timeseries = pd.read_feather(self._tariff_timeseries_filepath).to_numpy()[:n_hours, 0]
            elif self._tariff_timeseries_filepath.endswith(".npy"):
                self._tariff_timeseries = np.load(self._tariff_timeseries_filepath)
            else:
                raise ValueError("Unknown file format for timeseries of electricity prices. Use feather or npy.")
        else:
            raise ValueError("Unknown mode for timeseries of electricity prices. Use 'const' or 'file'.")

        #CO2 intensity

        if self._co2_intensity_mode == 'const':
            self._co2_intensity_timeseries = self._co2_intensity_timeseries + self._constant_co2_intensity
        elif self._co2_intensity_mode == 'file':
            if self._co2_intensity_timeseries_filepath.endswith(".feather"):
                self._co2_intensity_timeseries = pd.read_feather(self._co2_intensity_timeseries_filepath).to_numpy()[:n_hours, 0]
            elif self._co2_intensity_timeseries_filepath.endswith(".npy"):
                self._co2_intensity_timeseries = np.load(self._co2_intensity_timeseries_filepath)
            else:
                raise ValueError("Unknown file format for timeseries of electricity co2 intensity. Use feather or npy.")
        else:
            raise ValueError("Unknown mode for timeseries of electricity co2 intensity. Use 'const' or 'file'.")

    def initialise_zero(self, n_days):
        n_hours = n_days*24
        zero_vals = np.zeros(n_hours)            

        self._f_e = zero_vals.copy()
        self._f_co2 = zero_vals.copy()

        
        
    def update_df_results(self, df):
        df['f_e'] = self.get_f_e()
        df['f_co2'] = self.get_f_co2()
        
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
        
        self._f_e = self._f_e[:n_hours]
        self._f_co2 = self._f_co2[:n_hours]

        self._co2_intensity_timeseries = self._co2_intensity_timeseries[:n_hours]
        self._tariff_timeseries = self._tariff_timeseries[:n_hours]
            
    def __compute_f_co2(self):        
        self._f_co2 = self._f_e*self._co2_intensity_timeseries
        
    def add_f_e(self, f_e_new):
        self._f_e = np.array(f_e_new)
        
        self.__compute_f_co2()

    def update_f_e(self, f_e_updated):
        self._f_e = np.array(f_e_updated)        
        self.__compute_f_co2()
        
    def create_techs_dict(self, 
                          techs_dict, color, 
                          resource_tariff_timeseries,
                          resource_co2_intensity_timeseries,
                          energy_scaling_factor):
            
        techs_dict['grid_export'] = {
            'essentials':{
                'name':'Grid Export',
                'color':color,
                'parent':'demand',
                'carrier':'electricity',
                },
            'constraints':{
                "resource": 'inf',
                # 'energy_cap_max':self._kW_max / energy_scaling_factor if self._kW_max != 'inf' else 'inf',
                # "export_carrier": "electricity",
                # 'lifetime':self._lifetime
                },
            'costs':{
                'monetary':{
                    "om_con": resource_tariff_timeseries
                    # 'om_con': resource_tariff_timeseries, # [CHF/kWh]
                    },
                'emissions_co2':{
                    # 'om_con': resource_co2_intensity_timeseries
                    "om_con": resource_co2_intensity_timeseries
                    }
                }
            }
        
        return techs_dict
    
    def get_f_e(self):
        self.len_test(self._f_e)
        return self._f_e
        
    def get_f_co2(self):
        self.len_test(self._f_co2)
        return self._f_co2
    
    def update_f_e_i(self, i, val):
        self.num_test(val)
        self._f_e[i] = float(val)

    def get_energy_costs(self):
        return np.sum(np.array(self._f_e)*self._tariff_timeseries)

    def get_tariff_timeseries(self):
        return self._tariff_timeseries
    
    def get_co2_intensity_timeseries(self):
        return self._co2_intensity_timeseries