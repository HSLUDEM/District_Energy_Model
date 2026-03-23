# -*- coding: utf-8 -*-
"""
Created on 2025-12-12

@author: pascalvecsei

Class to contain several installation
"""

import pandas as pd
import numpy as np
import sys
import os
import copy



from district_energy_model.techs.dem_tech_core import TechCore

from district_energy_model.techs.dem_tech_solar_pv_installation import SolarPVInstallation

# Add modules from parent directory:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
parent_dir_path = os.path.dirname(dname)
sys.path.insert(0, parent_dir_path)

import dem_helper

from techs.dem_tech_core import TechCore

class SolarPVType(TechCore):
        
    def __init__(
            self,
            techkey,
            profiles,
            capex_scaling,
            shares_occupied,
            tech_dict
            ):
                
        # Initialize properties:

        self._techkey = techkey

        self.update_tech_properties(tech_dict)
        
        self._profiles = profiles
        self._capex_scaling = capex_scaling
        self._shares_occupied = shares_occupied
        self._installations = []

        self.output_carrier = 'electricity'
        
        self._values_of_installations_changed_flag = True

        self.initialize_installation_instances()


        self._v_e = []
        self._v_e_cons = []
        self._v_e_exp = []
        self._v_e_pot = []
        self._v_e_pot_remain = []
        
        # Annual values:
        self._v_e_yr = ...
    
    def initialize_installation_instances(self):

        p_remaining = copy.deepcopy(self._p_max)

        for i in range(len(self._profiles)):

            p_max_profile = self._profiles[i].max() * self._capex_scaling[i]

            if p_remaining != 'inf':
                if p_max_profile < p_remaining:
                    p_max_here = p_max_profile / self._capex_scaling[i]
                    p_remaining -= p_max_profile
                elif p_remaining > 0:
                    p_max_here = p_remaining / self._capex_scaling[i]
                    p_remaining = 0
                elif p_remaining == 0:
                    p_max_here = 0
            else:
                p_max_here = p_max_profile / self._capex_scaling[i]

            tech_dict_instance = copy.deepcopy(self.__tech_dict)

            tech_dict_instance['capex'] = (
                tech_dict_instance['base_capex']
                *self._capex_scaling[i]
                )
            tech_dict_instance['maintenance_cost'] = (
                tech_dict_instance['base_maintenance_cost']
                *self._capex_scaling[i]
                )
            tech_dict_instance['kW_max'] = p_max_here

            del tech_dict_instance["base_capex"]
            del tech_dict_instance["base_maintenance_cost"]
            del tech_dict_instance["kWp_max"]

            self._installations.append(
                SolarPVInstallation(
                    self._profiles[i],
                    self._shares_occupied[i], 
                    tech_dict_instance
                    )
            )


    def update_tech_properties(self, tech_dict):
        
        """
        Updates the solar pv technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        # Properties:
        self._p_max = tech_dict['kWp_max']

        self._eta_overall = tech_dict['eta_overall']

        self._lifetime = tech_dict['lifetime']

        self._interest_rate = tech_dict['interest_rate']

        self._base_capex = tech_dict['base_capex']

        self._only_use_installed = tech_dict['only_use_installed']

        self._base_maintenance_cost = tech_dict['base_maintenance_cost']

        self._export_subsidy = tech_dict['export_subsidy']

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['v_e_'+self._techkey] = self.get_v_e()
        df['v_e_'+self._techkey+'_cons'] = self.get_v_e_cons()
        df['v_e_'+self._techkey+'_exp'] = self.get_v_e_exp()
        df['v_e_'+self._techkey+'_pot'] = self.get_v_e_pot()
        df['v_e_'+self._techkey+'_pot_remain'] = self.get_v_e_pot_remain()
        
        return df
    
    def reduce_timeframe(self, n_days):
       
        n_hours = n_days*24
        
        self._v_e = self._v_e[:n_hours]
        self._v_e_cons = self._v_e_cons[:n_hours]
        self._v_e_exp = self._v_e_exp[:n_hours]
        self._v_e_pot = self._v_e_pot[:n_hours]
        self._v_e_pot_remain = self._v_e_pot_remain[:n_hours]

        for installation in self._installations:
            installation.reduce_timeframe(n_days)
    

    def compute_v_e(self):    

        for installation in self._installations:

            installation.compute_v_e()

        self._values_of_installations_changed_flag = True

    def compute_v_e_pot_base(self):
        
        for installation in self._installations:

            installation.compute_v_e_pot_base()
        
        self._values_of_installations_changed_flag = True
        
    def compute_v_e_pot_remain(
            self
            ):

        for installation in self._installations:

            installation._compute_v_e_pot_remain()

        self._values_of_installations_changed_flag = True

    def agregate_variables(
        self,
        only_potential = False
        ):

        self._v_e = 0.0
        self._v_e_pot = 0.0
        self._v_e_pot_remain = 0.0

        if not only_potential:
            self._v_e_exp = 0.0
            self._v_e_cons = 0.0
        counter = 0
        for installation in self._installations:
            counter += 1
            self._v_e += installation.get_v_e()
            self._v_e_pot += installation.get_v_e_pot()
            self._v_e_pot_remain += installation.get_v_e_pot_remain()
            if not only_potential:
                self._v_e_exp += installation.get_v_e_exp()
                self._v_e_cons += installation.get_v_e_cons()

        self._values_of_installations_changed_flag = False
    def update_v_e(
            self,
            v_e_updated, #Multiprofile!
            ):
        
        for i in range(len(self._installations)):
            self._installations[i].update_v_e(v_e_updated[i])
        
        self._values_of_installations_changed_flag = True

    def update_v_e_cons(self, v_e_cons_updated):

        for i in range(len(self._installations)):
            self._installations[i].update_v_e_cons(v_e_cons_updated[i])

        self._values_of_installations_changed_flag = True
    
    def update_v_e_exp(self, v_e_exp_updated):

        for i in range(len(self._installations)):
            self._installations[i].update_v_e_exp(v_e_exp_updated[i])

        self._values_of_installations_changed_flag = True
                  
    
    def create_tech_groups_dict(self, 
                                tech_groups_dict
                                ):
        
        tech_groups_dict['solar_'+self._techkey] = {
            'essentials':{
                'parent':'supply',
                'carrier': 'electricity'
                },
            'constraints':{
                'export_carrier': 'electricity',
                'resource_unit': 'energy_per_area', # 'energy',
                # 'parasitic_eff': 1.0, # efficiency is already accounted for in the resource dataseries
                'force_resource': True,
                'lifetime': self._lifetime,
                },
            'costs':{
                'monetary':{
                    'interest_rate':self._interest_rate,
                    },
                }
            }
        
        return tech_groups_dict
        
    def create_techs_dict(self,
                          techs_dict,
                          resources,
                          color, 
                          energy_scaling_factor
                          ):
        
        headers = []

        for i in range(len(self._installations)):
            techs_dict, headers = self._installations[i].create_techs_dict(techs_dict = techs_dict,
                                                                           headers = headers,
                                                                            parent = 'solar_'+self._techkey,
                                                                            header = 'solar_'+self._techkey+"_installation_"+str(i),
                                                                            name = 'solar_'+self._techkey+"_installation_"+str(i),
                                                                            color = color,
                                                                            resource = resources[i],
                                                                            energy_scaling_factor = energy_scaling_factor
                                                                                )
                    
        return techs_dict, headers
    

    def check_changed_aggregate(self):
        if self._values_of_installations_changed_flag:
            self.agregate_variables()

    def get_eta_overall(self):
        self.check_changed_aggregate()

        self.num_test(self._eta_overall)
        return self._eta_overall
    
    def get_v_e(self):
        self.check_changed_aggregate()

        self.len_test(self._v_e)
        return self._v_e
    
    def get_v_e_from_installations(self):
        self.check_changed_aggregate()

        v_e_multi = []
        for installation in self._installations:
            v_e_multi.append(installation.get_v_e())
        return v_e_multi
    
    def get_v_e_pot_from_installations(self):
        self.check_changed_aggregate()

        v_e_pot_multi = []
        for installation in self._installations:
            v_e_pot_multi.append(installation.get_v_e_pot())
        return v_e_pot_multi
    
    def get_v_e_pot_remain_from_installations(self):
        self.check_changed_aggregate()

        v_e_pot_remain_multi = []
        for installation in self._installations:
            v_e_pot_remain_multi.append(installation.get_v_e_pot_remain())
        return v_e_pot_remain_multi


    def get_v_e_cons(self):
        self.check_changed_aggregate()

        self.len_test(self._v_e_cons)
        return self._v_e_cons
    
    def get_v_e_exp(self):
        self.check_changed_aggregate()

        self.len_test(self._v_e_exp)
        return self._v_e_exp
    
    def get_v_e_pot(self):
        self.check_changed_aggregate()

        self.len_test(self._v_e_pot)
        return self._v_e_pot
    
    def get_v_e_pot_remain(self):
        self.check_changed_aggregate()

        self.len_test(self._v_e_pot_remain)
        return self._v_e_pot_remain
        
    def get_pot_integration_factor(self):
        self.check_changed_aggregate()

        return self._pot_integration_factor
    
    def get_only_use_installed(self):
        self.check_changed_aggregate()

        return self._only_use_installed
        
    def get_resources(self):
        self.check_changed_aggregate()

        resources = []
        for installation in self._installations:
            resources.append(installation.get_resource())
        return resources
    
    def get_num_installations(self):
        self.check_changed_aggregate()

        return len(self._installations)