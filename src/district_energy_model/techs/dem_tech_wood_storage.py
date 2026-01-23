#Wood storage

# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 08:49:07 2024

@author: PascalVecsei
"""
import numpy as np
from techs.dem_tech_core import TechCore

class WoodStorage(TechCore):
    
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
        self.input_carrier = 'wood' 
        self.output_carrier = 'wood'
        
        # Accounting:
        self._u_wd = [] # electricity input [wood unit]
        self._v_wd = [] # electricity output [wood unit]
        self._q_wd = [] # stored energy [wood unit]
        self._l_u_wd = [] # charging losses [wood unit]
        self._l_v_wd = [] # discharging losses [wood unit]
        self._l_q_wd = [] # storage losses [wood unit]
        self._sos = [] # state of charge [-]
        
        #----------------------------------------------------------------------
        
            
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
        self._eta_chg_dchg = tech_dict['eta_chg_dchg']
        self._gamma = tech_dict['ws_gamma']
        self._cap = tech_dict['capacity_kWh']
        self._ic = tech_dict['initial_charge']
        self._optimized_initial_charge = tech_dict['optimized_initial_charge']
        self._chg_dchg_per_cap_max = tech_dict['chg_dchg_per_cap_max']
        self._lifetime = tech_dict['lifetime']
        self._capex = tech_dict['capex']
        self._interest_rate = tech_dict['interest_rate']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._force_asynchronous_prod_con = tech_dict['force_asynchronous_prod_con']
        
        
        # Tests:
        if self._ic > 1:
            printout = ('Error in tes input: '
                        'initial_charge cannot be larger than 1!\n'
                        f'Chosen initial_charge: {self._ic}'
                        )
            raise Exception(printout)
        if self._eta_chg_dchg > 1:
            printout = ('Error in wood storage input: '
                        'charging/discharging efficiency (eta_chg_dchg) cannot'
                        ' be larger than 1!'
                        )
            raise Exception(printout)
        if self._eta_chg_dchg <= 0:
            printout = ('Error in wood storage input: '
                        'charging/discharging efficiency (eta_chg_dchg) must'
                        ' be larger than 0!'
                        )
            raise Exception(printout)
        if self._gamma > 1:
            printout = ('Error in wood storage input: '
                        'loss factor (ws_gamma) cannot be larger than 1!'
                        )
            raise Exception(printout)

        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_wd_ws'] = self.get_u_wd() # wood input [wood unit]
        df['v_wd_ws'] = self.get_v_wd() # wood output [wood unit]
        df['q_wd_ws'] = self.get_q_wd() # stored wood [wood unit]
        df['l_u_wd_ws'] = self.get_l_u_wd() # charging losses [wood unit]
        df['l_v_wd_ws'] = self.get_l_v_wd() # discharging losses [wood unit]
        df['l_q_wd_ws'] = self.get_l_q_wd() # storage losses [wood unit]
        df['sos_ws'] = self.get_sos() # state of charge [-]
        
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
        
        self._u_wd = self._u_wd[:n_hours]
        self._v_wd = self._v_wd[:n_hours]
        self._q_wd = self._q_wd[:n_hours]
        self._l_u_wd = self._l_u_wd[:n_hours]
        self._l_v_wd = self._l_v_wd[:n_hours]
        self._l_q_wd = self._l_q_wd[:n_hours]
        self._sos = self._sos[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_wd = init_vals.copy() # electricity input [kWh]
        self._v_wd = init_vals.copy() # electricity output [kWh]
        self._q_wd = init_vals.copy() # stored energy [kWh]
        self._l_u_wd = init_vals.copy() # charging losses [kWh]
        self._l_v_wd = init_vals.copy() # discharging losses [kWh]
        self._l_q_wd = init_vals.copy() # storage losses [kWh]
        self._sos = init_vals.copy() # state of charge [-]
        
    def update_u_wd(self, u_wd_updated):
        if len(u_wd_updated) != len(self._u_wd):
            raise ValueError()        
        self._u_wd = np.array(u_wd_updated)        
        self.__compute_l_u_wd()
        
    def update_v_wd(self, v_wd_updated):
        if len(v_wd_updated) != len(self._v_wd):
            raise ValueError()        
        self._v_wd = np.array(v_wd_updated)        
        self.__compute_l_v_wd()
        
    def update_q_wd(self, q_wd_updated):
        if len(q_wd_updated) != len(self._q_wd):
            raise ValueError()        
        self._q_wd = np.array(q_wd_updated)        
        self.__compute_l_q_wd()

    def update_sos(self, sos_updated):
        if len(sos_updated) != len(self._sos):
            raise ValueError()        
        self._sos = np.array(sos_updated)  
              
    def update_cap(self, cap_updated):
        self.num_test(cap_updated)
        self._cap = cap_updated      

    def __compute_l_u_wd(self):
        """
        Compute the charging losses for each time step.

        Parameters
        ----------

        Returns
        -------

        """
        
        l_u_wd_ws = self._u_wd*(1-self._eta_chg_dchg)
        
        self._l_u_wd = np.array(l_u_wd_ws)
        
    def __compute_l_v_wd(self):
        """
        Compute the discharging losses for each time step.

        Parameters
        ----------
        Returns
        -------
        """
        
        l_v_wd_ws = self._v_wd*(1/self._eta_chg_dchg - 1)
        
        self._l_v_wd = np.array(l_v_wd_ws)
        
    def __compute_l_q_wd(self):
        """
        Compute the storage losses for each time step.

        Parameters
        ----------
        Returns
        -------

        """
        
        l_q_wd_ws = self._q_wd*self._gamma
        
        self._l_q_wd = np.array(l_q_wd_ws)
        
    
    def create_techs_dict(self, techs_dict, color):

        techs_dict['ws'] = {
            'essentials':{
                'name':'Wood Storage',
                'color':color,
                'parent':'storage',
                'carrier_in':'wood',
                'carrier_out':'wood'
                },
            'constraints':{
                'storage_initial':self._ic if not self._optimized_initial_charge else None,
                'storage_cap_max':self._cap,
                'storage_loss':self._gamma,
                'energy_eff':self._eta_chg_dchg,
                'energy_cap_per_storage_cap_max': self._chg_dchg_per_cap_max,
                'lifetime':self._lifetime,
                # 'force_asynchronous_prod_con':True,
                },
            'costs':{
                'monetary':{
                    # 'om_annual':0.0, # !!!TEMPORARY - KOSTEN MÜSSEN DYNAMISCH HINZUGEFÜGT WERDEN!!!
                    'om_prod':0.0000, # # [CHF/kWh_dchg] artificial cost per discharged kWh; used to avoid cycling within timestep
                    'storage_cap':self._capex,
                    'interest_rate':self._interest_rate,
                    'om_annual': self._maintenance_cost
                    },
                }
            }
        if self._force_asynchronous_prod_con:
            techs_dict['ws']['constraints']['force_asynchronous_prod_con']= True

        return techs_dict
    
    def get_u_wd(self):
        self.len_test(self._u_wd)
        return self._u_wd
    
    def get_v_wd(self):
        self.len_test(self._v_wd)
        return self._v_wd
    
    def get_q_wd(self):
        self.len_test(self._q_wd)
        return self._q_wd
    
    def get_l_u_wd(self):
        self.len_test(self._l_u_wd)
        return self._l_u_wd
    
    def get_l_v_wd(self):
        self.len_test(self._l_v_wd)
        return self._l_v_wd
    
    def get_l_q_wd(self):
        self.len_test(self._l_q_wd)
        return self._l_q_wd
    
    def get_sos(self):
        self.len_test(self._sos)
        return self._sos
    
    def get_eta_chg_dchg(self):
        self.num_test(self._eta_chg_dchg)
        return self._eta_chg_dchg
    
    def get_gamma(self):
        self.num_test(self._gamma)
        return self._gamma
        
    def get_cap(self):
        self.num_test(self._cap)
        return self._cap
    
    def get_ic(self):
        self.num_test(self._ic)
        return self._ic
    
    
    def initialise_q_wd_0(self):
        self._q_wd[0] = self.get_ic()*self.get_cap()

    def update_q_wd_i(self, i, val):
        self.num_test(val)
        self._q_wd[i] = float(val)

    def get_chg_dchg_per_cap_max(self):
        self.num_test(self._chg_dchg_per_cap_max)
        return self._chg_dchg_per_cap_max
    
    def update_u_wd_i(self, i, val):
        self.num_test(val)
        self._u_wd[i] = float(val)
        
    def update_v_wd_i(self, i, val):
        self.num_test(val)
        self._v_wd[i] = float(val)
        
    def update_q_wd_i(self, i, val):
        self.num_test(val)
        self._q_wd[i] = float(val)

    def update_l_u_wd_i(self, i, val):
        self.num_test(val)
        self._l_u_wd[i] = float(val)

    def update_l_v_wd_i(self, i, val):
        self.num_test(val)
        self._l_v_wd[i] = float(val)

    def update_l_q_wd_i(self, i, val):
        self.num_test(val)
        self._l_q_wd[i] = float(val)

    def update_sos_i(self, i, val):
        self.num_test(val)
        self._sos[i] = float(val)