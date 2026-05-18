# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 11:32:14 2026

@author: UeliSchilt
"""
"""
Demand Resonse (DR) Flexibility
"""

"""
TMP Script workflow and methods




    1. Compute aggregated thermal capacity C_cluster
    2. Compute virtual storage size
    3. Compute heat loss rate r based on H-value (C-weighted function?)
    4. Compute annual heat demand (PROFILE AS WELL?)
    5. Compute lower annual heat demand

"""

# import pandas as pd
import numpy as np
import warnings

from district_energy_model import dem_constants as C
from district_energy_model import dem_helper

class BuildingInertiaFlexibility:
    
    def __init__(
            self,
            df_com_yr,
            yearly_heat_demand_col,
            tech_dict,
            ):
        """
        

        Parameters
        ----------
        df_com_yr : dataframe
            dataframe with row-entry per building (annual values).
        delta_T_flex : float
            Accepted deviation from setpoint room-temperature (upwards and
            downwards) [degC]. Example: delta_T_flex = 2.0 degC with setpoint
            at 22.0 degC: The temperature can deviate between 20.0 and 24.0
            degC.
        no_of_clusters : int
            Number of clusters into which buildings are grouped according to
            their thermal characteristics.

        Returns
        -------
        None.

        """        
        
        self.df_com_yr = df_com_yr
        
        
        self.H_header = 'H_W_per_K'
        self.C_header = 'C_MJ_per_K'
        self.yearly_heat_demand_col = yearly_heat_demand_col

        # self._delta_T_flex = delta_T_flex
        # self._no_of_clusters = no_of_clusters
        self._delta_T_flex = tech_dict['dr_flexibility_building_inertia_dT']
        
        if not 0 <= self._delta_T_flex:
            raise ValueError(
                "'dr_flexibility_building_inertia_dT' must be larger"
                " than 0."
                )
        
        self._flex_share = tech_dict['dr_flexibility_building_inertia_share']
        
        if not 0 <= self._flex_share <= 1:
            raise ValueError(
                "'dr_flexibility_building_inertia_share' must be between 0 and 1."
            )
        
        self._heating_systems = tech_dict['dr_flexibility_building_inertia_heating_systems']
        
        # Max. charge rate (mcr) of virtual storage (mcr_vs):
        self._mcr_vs = None
        mcr_vs_hs = (
            tech_dict['dr_flexibility_building_inertia_max_overheating_rate']
            ['max_heating_system_cap']
            )
        mcr_vs_lr = (
            tech_dict['dr_flexibility_building_inertia_max_overheating_rate']
            ['max_virtual_storage_loss_rate']
            )
        if mcr_vs_hs and mcr_vs_lr:
            msg = (
                "Under 'dr_flexibility_building_inertia_max_overheating_rate'"
                " both 'max_heating_system_cap' and"
                " 'max_virtual_storage_loss_rate' are set to True. Only one"
                " can be set to True."
                )
            raise Warning(msg)
        elif mcr_vs_hs:
            self._mcr_vs = 'hs'
        elif mcr_vs_lr:
            self._mcr_vs = 'lr'
        
        # Test if min. one heating system is activated for demand response:
        if not any(self._heating_systems.values()):
            msg = (
                "Demand response flexibility from building inertia is"
                " activated. However, no heating system under"
                " dr_flexibility_building_inertia_heating_systems is set to"
                " True. At least one heating system must be set to True if"
                " flexibility is activated."
                )
            raise ValueError(msg)            
        
        # Only keep the activated flexibility systems (i.e., flexibly controlled technologies)
        # filter True entries and replace value with acronym:
        self.flex_systems = {
            k: dem_helper.get_acronym(k)
            for k, v in self._heating_systems.items()
            if v
        }
        
        # Metrics:
        # =======
        
        # Metrics for whole district:
        self._C_tot_max = None # Max. aggregated thermal capacity (all buidlings) [MJ/K]
        self._C_tot = None # Actual aggregated thermal capacity (selected buildings) [MJ/K]
        self._H_tot = None # Heat loss rate [W/K]
        self._E_vs_tot_max = None # max. virtual storage (vs) capacity (all buildings) [kWh]
        self._E_vs_tot = None # actual total virtual storage (vs) capacity (selected buildings) [kWh]
        self._d_h_yr_tot = None # annual heat demand [kWh]
        self._r_tot = None # Additional heat loss rate [kWh_loss/kWh_stored] per timestep
        self._delta_loss_max_tot = None # [kWh] Max. additional loss from upwards flexibility
        self._delta_loss_tot = None # [kWh] Actual additional loss from upwards flexibility
        self._u_h_vs_max_tot = None # [kWh] charge limit (per timestep)  

        # Lists to store metrics for each flexibility system:
        self._list_C = [] # Aggregated thermal capacity [MJ/K]
        self._list_H = [] # Heat loss rate [W/K]
        self._list_E_vs = [] # virtual storage (vs) capacity [kWh]
        self._list_d_h_yr = [] # annual heat demand [kWh]
        self._list_delta_loss = [] # [kWh] Actual additional loss from upwards flexibility
        self._list_u_h_vs_max = [] # [kWh] charge limit (per timestep)
        
        # Energy flows:
        # ============
        
        # Lists containing values for each flexibility system:
        # (these values can only be determined during optimisation,
        #  when the allocation of heating systems is done.)
        self._list_u_h = [] # [kWh] virtual storage input
        self._list_v_h = [] # [kWh] virtual storage output
        self._list_q_h = [] # [kWh] stored energy
        self._list_l_q_h = [] # storage losses [kWh]
        self._list_dq_h_pos = [] # [kWh] state of storage increases (i.e., positive)
        self._list_dq_h_neg = [] # [kWh] state of storage decreases (i.e., negative)
        self._list_sos = [] # state of storage [-]    
        # self._list_dq_h_pos = [] # [kWh] increase of storage level
        # self._list_dq_h_neg = [] # [kWh] decrease of storage level
        
        self._list_u_h_drain = [] # [kWh] virtual storage input
        self._list_v_h_drain = [] # [kWh] virtual storage output
        self._list_q_h_drain = [] # [kWh] stored energy
        self._list_sos_drain = [] # state of storage [-]    
        
        self._u_h_tot = [] # [kWh] virtual storage input across all flexibility systems
        self._v_h_tot = [] # [kWh] virtual storage output across all flexibility systems
        self._q_h_tot = [] # [kWh] stored energy across all clusters
        self._l_q_h_tot = [] # virtual storage losses [kWh] across all flexibility systems
        self._dq_h_pos_tot = [] # [kWh] total increase of storage level across all virtual storages
        self._dq_h_neg_tot = [] # [kWh] total decrease of storage level across all virtual storages
        self._dq_h_tot = [] # [kWh] total net change of storage level across all virtual storages
        self._sos_tot = [] # state of storage [-] across all clusters
        
        self._u_h_drain_tot = [] # [kWh] virtual storage input across all flexibility systems
        self._v_h_drain_tot = [] # [kWh] virtual storage output across all flexibility systems
        self._q_h_drain_tot = [] # [kWh] stored energy across all clusters
        self._sos_drain_tot = [] # state of storage [-] across all clusters
        
        # Compute metrics for whole district:
        self.compute_flex_metrics()
        
    def update_df_results(self, df):
        
        # Update timeseries for each flexibility system (e.g., heat pumps, district heating, ...):            
        i = 0
        for key, acr in self.flex_systems.items():
            # acr = acronym (e.g., 'hp' for heat pump)
            
            df[f'u_h_vs_{acr}'] = self.get_list_u_h()[i]
            df[f'v_h_vs_{acr}'] = self.get_list_v_h()[i]
            df[f'q_h_vs_{acr}'] = self.get_list_q_h()[i]
            df[f'l_q_h_vs_{acr}'] = self.get_list_l_q_h()[i]
            df[f'dq_h_vs_pos_{acr}'] = self.get_list_dq_h_pos()[i]
            df[f'dq_h_vs_neg_{acr}'] = self.get_list_dq_h_neg()[i]
            df[f'sos_vs_{acr}'] = self.get_list_sos()[i]
            
            df[f'u_h_vs_drain_{acr}'] = self.get_list_u_h_drain()[i]
            df[f'v_h_vs_drain_{acr}'] = self.get_list_v_h_drain()[i]
            df[f'q_h_vs_drain_{acr}'] = self.get_list_q_h_drain()[i]
            df[f'sos_vs_drain_{acr}'] = self.get_list_sos_drain()[i]
            
            i += 1

        # Update aggregated values across flexibility systems:
        df['u_h_vs_tot'] = self.get_u_h_tot()
        df['v_h_vs_tot'] = self.get_v_h_tot()
        df['q_h_vs_tot'] = self.get_q_h_tot()
        df['l_q_h_vs_tot'] = self.get_l_q_h_tot()
        df['dq_h_vs_pos_tot'] = self.get_dq_h_pos_tot()
        df['dq_h_vs_neg_tot'] = self.get_dq_h_neg_tot()
        df['sos_vs_tot'] = self.get_sos_tot()
        
        df['u_h_vs_drain_tot'] = self.get_u_h_drain_tot()
        df['v_h_vs_drain_tot'] = self.get_v_h_drain_tot()
        df['q_h_vs_drain_tot'] = self.get_q_h_drain_tot()
        df['sos_vs_drain_tot'] = self.get_sos_drain_tot()
        

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
        
        # Update timeseries for each flexibility system:
        for i, (key, acr) in enumerate(self.flex_systems.items()):
            # key: full tech name (e.g., 'heat_pump', 'district_heating')
            # acr: acronym (e.g., 'hp', 'dh')       
            self._list_u_h[i] = self._list_u_h[i][:n_hours]
            self._list_v_h[i] = self._list_v_h[i][:n_hours]
            self._list_q_h[i] = self._list_q_h[i][:n_hours]
            self._list_l_q_h[i] = self._list_l_q_h[i][:n_hours]
            self._list_dq_h_pos[i] = self._list_dq_h_pos[i][:n_hours]
            self._list_dq_h_neg[i] = self._list_dq_h_neg[i][:n_hours]
            self._list_sos[i] = self._list_sos[i][:n_hours]

            self._list_u_h_drain[i] = self._list_u_h_drain[i][:n_hours]
            self._list_v_h_drain[i] = self._list_v_h_drain[i][:n_hours]
            self._list_q_h_drain[i] = self._list_q_h_drain[i][:n_hours]
            self._list_l_q_h_drain[i] = self._list_l_q_h_drain[i][:n_hours]
            self._list_sos_drain[i] = self._list_sos_drain[i][:n_hours]

            
        self._u_h_tot = self._u_h_tot[:n_hours]
        self._v_h_tot = self._v_h_tot[:n_hours]
        self._q_h_tot = self._q_h_tot[:n_hours]
        self._l_q_h_tot = self._l_q_h_tot[:n_hours]
        self._dq_h_pos_tot = self._dq_h_pos_tot[:n_hours]
        self._dq_h_neg_tot = self._dq_h_neg_tot[:n_hours]
        self._sos_tot = self._sos_tot[:n_hours]
        
        self._u_h_drain_tot = self._u_h_drain_tot[:n_hours]
        self._v_h_drain_tot = self._v_h_drain_tot[:n_hours]
        self._q_h_drain_tot = self._q_h_drain_tot[:n_hours]
        self._l_q_h_drain_tot = self._l_q_h_drain_tot[:n_hours]
        self._sos_drain_tot = self._sos_drain_tot[:n_hours]
        
    def compute_flex_metrics(self):
        
        # Compute metrics for the whole district, including all buildings:
        self._C_tot_max = self.df_com_yr[self.C_header].sum()
        self._H_tot = self.df_com_yr[self.H_header].sum() # [W/K]
        self._r_tot = self._H_tot / (self._C_tot_max*C.CONV_MJ_to_kWh*1e3) # [kWh_loss/kWh_stored] per timestep
        self._E_vs_tot_max = 2*self._C_tot_max*self._delta_T_flex*C.CONV_MJ_to_kWh # [kWh]; factor 2 because we need upward and downward flexibility
        self._d_h_yr_tot = self.df_com_yr[self.yearly_heat_demand_col].sum()
        self._delta_loss_max_tot = self._r_tot*0.5*self._E_vs_tot_max
        self._u_h_vs_max_tot = self._E_vs_tot_max * self._r_tot
        
        # Compute metrics based on the share of buildings participating in demand response:
        self._C_tot = self._C_tot_max * self._flex_share
        self._E_vs_tot = 2*self._C_tot*self._delta_T_flex*C.CONV_MJ_to_kWh
        self._delta_loss_tot = self._r_tot*0.5*self._E_vs_tot
    
    def __update_metrics_dict(self):
        
        dict_metrics = {
            'C_tot_max_MJ_per_K': self._C_tot_max,
            'C_tot_MJ_per_K': self._C_tot,
            'H_tot_W_per_K': self._H_tot,
            'E_vs_tot_max_kWh': self._E_vs_tot_max,
            'E_vs_tot_kWh': self._E_vs_tot,
            'd_h_yr_tot_kWh': self._d_h_yr_tot,
            'r_tot_kWh_loss_per_kWh_stored': self._r_tot,
            'delta_loss_max_tot_kWh': self._delta_loss_max_tot,
            'u_h_vs_max_tot': self._u_h_vs_max_tot,
            }
        
        dict_metrics['delta_loss_tot_kWh'] = self.get_delta_loss_tot()
        
        for i, (key, acr) in enumerate(self.flex_systems.items()):
            # key: full tech name (e.g., 'heat_pump', 'district_heating')
            # acr: acronym (e.g., 'hp', 'dh') 
            
            E_vs_i = self.get_list_E_vs()[i]
            C_i = E_vs_i / (2*self._delta_T_flex*C.CONV_MJ_to_kWh)
            self._list_C.append(C_i)
            
            dict_metrics[f"E_vs_{acr}_kWh"] = E_vs_i
            dict_metrics[f"C_{acr}_MJ_per_K"] = self._list_C[i]

        return dict_metrics
            
    def create_techs_dict(self, techs_dict, color):
        """
        Create virtual storage tech in Calliope (one per flexibility system).

        Parameters
        ----------
        techs_dict : TYPE
            DESCRIPTION.
        color : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        ic = 0.5 # initial storage charge (50% of total capacity corresponds to neutral demand response state)
        # ic = 0.0

        for i, (key, acr) in enumerate(self.flex_systems.items()):
            # key: full tech name (e.g., 'heat_pump')
            # acr: acronym (e.g., 'hp' for heat pump)
            
            # Create a virtual storage for each connected heating system:
                            
            techs_dict[f'virtual_storage_flex_{acr}'] = {}
                
            techs_dict[f'virtual_storage_flex_{acr}'] = {
                'essentials':{
                    'name':f'Flexibility - Virtual Storage {acr}',
                    'color':color,
                    'parent':'storage',
                    'carrier_in':f'heat_vs_{acr}',
                    'carrier_out':f'heat_vs_{acr}',
                    },
                'constraints':{
                    'storage_initial':ic,
                    'storage_cap_max':self._E_vs_tot,
                    'storage_loss':self._r_tot,
                    'energy_eff': 1.0,
                    'lifetime': 25,
                    },
                'costs':{
                    'monetary':{
                        'om_prod':0.0,
                        'storage_cap':0.0,
                        'interest_rate':0.0,
                        'om_annual':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0
                        }
                    }
                }
            
            # Max. charging rate (mcr) of virtual storage (vs):
            # --> determined in custom constraint virtual_storage_charge_constraint
            # if self.mcr_vs == 'lr': 
            #     # loss rate (lr) is used as limiting value for charging:            
            #     techs_dict[
            #         f'virtual_storage_flex_{acr}'
            #         ][
            #             'constraints'
            #             ]['energy_cap_per_storage_cap_equals'] = self._r_tot
            # elif self.mcr_vs == 'hs':
            #     # Heating system (hs) capacity is limiting value:
            #     pass # This is already provided in the respective tech constraint.
                
            # Conversion from virtual storage to drain (one-way):
            # techs_dict['conv_{acr}_vs'] = {}
            techs_dict[f'conv_{acr}_vs'] = {
                'essentials':{
                    'name':'Conversion: HP to Virtual Storage {acr}',
                    'parent':'conversion',
                    'carrier_in':f'heat_{acr}',
                    'carrier_out':f'heat_vs_{acr}',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # no losses
                    'lifetime':25,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0,
                        'interest_rate':0.0,
                        },
                    } 
                }
            
            # Create virtual storage drain, for when there is no space heating demand:
            # techs_dict[f'virtual_storage_drain_{acr}'] = {}
            techs_dict[f'virtual_storage_drain_{acr}'] = {
                'essentials':{
                    'name':f'Flexibility - Virtual Storage Drain {acr}',
                    'color':color,
                    'parent':'storage',
                    'carrier_in':f'heat_vs_{acr}',
                    'carrier_out':f'heat_vs_{acr}',
                    },
                'constraints':{
                    'storage_initial':0.0,
                    'storage_cap_equals':self._E_vs_tot_max,
                    'storage_loss':0.0, # no losses
                    'energy_cap_per_storage_cap_equals':1.0, # the entire storage can be filled or emptied in one timestep
                    'energy_eff': 1.0,
                    'lifetime': 25,
                    },
                'costs':{
                    'monetary':{
                        'om_prod':0.0,
                        'storage_cap':0.0,
                        'interest_rate':0.0,
                        'om_annual':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0
                        }
                    }
                }
            

        return techs_dict
            
    def __compute_list_l_q_h(self):
        self._list_l_q_h = []
        for i, q_h in enumerate(self._list_q_h):
            l_q_h = np.array(q_h*self._r_tot)
            self._list_l_q_h.append(l_q_h)
        self._l_q_h_tot = np.sum(self._list_l_q_h, axis=0)
        
    def __compute_list_dq_h(self):
        for i, l_q_h in enumerate(self._list_l_q_h):
            dq_h = np.array(
                -l_q_h
                + self.get_list_u_h()[i]
                - self.get_list_v_h()[i]
                )
            dq_h_pos = np.where(dq_h > 0, dq_h, 0)
            dq_h_neg = np.where(dq_h < 0, -dq_h, 0)
            
            self._list_dq_h_pos.append(dq_h_pos)
            self._list_dq_h_neg.append(dq_h_neg)
            
        self._dq_h_pos_tot = np.sum(self._list_dq_h_pos, axis=0)
        self._dq_h_neg_tot = np.sum(self._list_dq_h_neg, axis=0)
        self._dq_h_tot = self._dq_h_pos_tot -  self._dq_h_neg_tot

    def len_test(self,items):
        if len(items)==0:
            raise ValueError()
        
    def num_test(self,var):
        if isinstance(var, (int, float, np.integer))==False:
            raise ValueError()
            
    def positive_test(self, scalar):
        if scalar < 0.0:
            raise ValueError()
            
    def positive_zero_test(self, scalar):
        if scalar <= 0.0:
            raise ValueError()
    
    def update_list_u_h(self, list_u_h_updated):
        self._list_u_h = []
        for u_h in list_u_h_updated:
            self._list_u_h.append(np.array(u_h))
            
        self._u_h_tot = np.sum(self._list_u_h, axis=0)
        
    def update_list_v_h(self, list_v_h_updated):
        self._list_v_h = []
        for v_h in list_v_h_updated:
            self._list_v_h.append(np.array(v_h))
        
        self._v_h_tot = np.sum(self._list_v_h, axis=0)
        
    def update_list_q_h(self, list_q_h_updated):
        self._list_q_h = []
        for q_h in list_q_h_updated:
            self._list_q_h.append(np.array(q_h))
            
        self.__compute_list_l_q_h()        
        self.__compute_list_dq_h()
        
        self._q_h_tot = np.sum(self._list_q_h, axis=0)

    def update_list_sos(self, list_sos_updated):      
        self._list_sos = list_sos_updated    
        
        self._sos_tot = np.sum(self._list_sos, axis=0)
        
    def update_list_u_h_drain(self, list_u_h_drain_updated):
        self._list_u_h_drain = []
        for u_h_drain in list_u_h_drain_updated:
            self._list_u_h_drain.append(np.array(u_h_drain))
            
        self._u_h_drain_tot = np.sum(self._list_u_h_drain, axis=0)
        
    def update_list_v_h_drain(self, list_v_h_drain_updated):
        self._list_v_h_drain = []
        for v_h_drain in list_v_h_drain_updated:
            self._list_v_h_drain.append(np.array(v_h_drain))
        
        self._v_h_drain_tot = np.sum(self._list_v_h_drain, axis=0)
        
    def update_list_q_h_drain(self, list_q_h_drain_updated):
        self._list_q_h_drain = []
        for q_h_drain in list_q_h_drain_updated:
            self._list_q_h_drain.append(np.array(q_h_drain))
        
        self._q_h_drain_tot = np.sum(self._list_q_h_drain, axis=0)

    def update_list_sos_drain(self, list_sos_drain_updated):      
        self._list_sos_drain = list_sos_drain_updated    
        
        self._sos_drain_tot = np.sum(self._list_sos_drain, axis=0)

    def update_list_E_vs(self, list_E_vs_updated):
        self._list_E_vs = list_E_vs_updated
        
        self._E_vs_tot = float(sum(self._list_E_vs))
        
        self._delta_loss_tot = self._r_tot*0.5*self._E_vs_tot
    
    def get_metrics_dict(self):
        return self.__update_metrics_dict()
    
    def get_delta_T_flex(self):
        self.num_test(self._delta_T_flex)
        self.positive_test(self._delta_T_flex)
        return self._delta_T_flex
    
    def get_flex_systems(self):
        return self.flex_systems

    def get_C_tot_max(self):
        self.num_test(self._C_tot_max)
        self.positive_test(self._C_tot_max)
        return self._C_tot_max
    
    def get_H_tot(self):
        self.num_test(self._H_tot)
        self.positive_test(self._H_tot)
        return self._H_tot
    
    def get_E_vs_tot_max(self):
        self.num_test(self._E_vs_tot_max)
        self.positive_test(self._E_vs_tot_max)
        return self._E_vs_tot_max
    
    def get_E_vs_tot(self):
        self.num_test(self._E_vs_tot)
        self.positive_test(self._E_vs_tot)
        return self._E_vs_tot
    
    def get_r_tot(self):
        self.num_test(self._r_tot)
        self.positive_zero_test(self._r_tot)
        return self._r_tot
    
    def get_mcr_vs(self):
        return self._mcr_vs
    
    def get_delta_loss_max_tot(self):
        self.num_test(self._delta_loss_max_tot)
        self.positive_test(self._delta_loss_max_tot)
        return self._delta_loss_max_tot
    
    def get_delta_loss_tot(self):
        self.num_test(self._delta_loss_tot)
        self.positive_test(self._delta_loss_tot)
        return self._delta_loss_tot
    
    def get_list_C(self):
        self.len_test(self._list_C)
        return self._list_C
    
    def get_list_H(self):
        self.len_test(self._list_H)
        return self._list_H
    
    def get_list_E_vs(self):
        self.len_test(self._list_E_vs)
        return self._list_E_vs
    
    def get_list_d_h_yr(self):
        self.len_test(self._list_d_h_yr)
        return self._list_d_h_yr

    def get_list_delta_loss_max(self):
        self.len_test(self._list_delta_loss_max)
        return self._list_delta_loss_max
    
    def get_list_u_h_vs_max(self):
        self.len_test(self._list_u_h_vs_max)
        return self._list_u_h_vs_max

    def get_list_u_h(self):
        self.len_test(self._list_u_h)
        return self._list_u_h
    
    def get_list_v_h(self):
        self.len_test(self._list_v_h)
        return self._list_v_h
    
    def get_list_q_h(self):
        self.len_test(self._list_q_h)
        return self._list_q_h
    
    def get_list_l_q_h(self):
        self.len_test(self._list_l_q_h)
        return self._list_l_q_h
    
    def get_list_dq_h_pos(self):
        self.len_test(self._list_dq_h_pos)
        return self._list_dq_h_pos
    
    def get_list_dq_h_neg(self):
        self.len_test(self._list_dq_h_neg)
        return self._list_dq_h_neg
    
    def get_list_sos(self):
        self.len_test(self._list_sos)
        return self._list_sos
    
    def get_list_u_h_drain(self):
        self.len_test(self._list_u_h_drain)
        return self._list_u_h_drain
    
    def get_list_v_h_drain(self):
        self.len_test(self._list_v_h_drain)
        return self._list_v_h_drain
    
    def get_list_q_h_drain(self):
        self.len_test(self._list_q_h_drain)
        return self._list_q_h_drain
    
    def get_list_sos_drain(self):
        self.len_test(self._list_sos_drain)
        return self._list_sos_drain

    def get_u_h_tot(self):
        self.len_test(self._u_h_tot)
        return self._u_h_tot
    
    def get_v_h_tot(self):
        self.len_test(self._v_h_tot)
        return self._v_h_tot
    
    def get_q_h_tot(self):
        self.len_test(self._q_h_tot)
        return self._q_h_tot
    
    def get_l_q_h_tot(self):
        self.len_test(self._l_q_h_tot)
        return self._l_q_h_tot
    
    def get_dq_h_pos_tot(self):
        self.len_test(self._dq_h_pos_tot)
        return self._dq_h_pos_tot
    
    def get_dq_h_neg_tot(self):
        self.len_test(self._dq_h_neg_tot)
        return self._dq_h_neg_tot
    
    def get_dq_h_tot(self):
        self.len_test(self._dq_h_tot)
        return self._dq_h_tot
    
    def get_sos_tot(self):
        self.len_test(self._sos_tot)
        return self._sos_tot
    
    def get_u_h_drain_tot(self):
        self.len_test(self._u_h_drain_tot)
        return self._u_h_drain_tot
    
    def get_v_h_drain_tot(self):
        self.len_test(self._v_h_drain_tot)
        return self._v_h_drain_tot
    
    def get_q_h_drain_tot(self):
        self.len_test(self._q_h_drain_tot)
        return self._q_h_drain_tot
    
    def get_sos_drain_tot(self):
        self.len_test(self._sos_drain_tot)
        return self._sos_drain_tot













