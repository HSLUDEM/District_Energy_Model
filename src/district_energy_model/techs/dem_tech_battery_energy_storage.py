# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 08:49:07 2024

@author: UeliSchilt
"""
import numpy as np
from techs.dem_tech_core import TechCore

class BatteryEnergyStorage(TechCore):
    
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
        self.input_carrier = 'electricity' 
        self.output_carrier = 'electricity'
        
        # Accounting:
        self._u_e = [] # electricity input [kWh]
        self._v_e = [] # electricity output [kWh]
        self._q_e = [] # stored energy [kWh]
        self._l_u_e = [] # charging losses [kWh]
        self._l_v_e = [] # discharging losses [kWh]
        self._l_q_e = [] # storage losses [kWh]
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
        self._gamma = tech_dict['bes_gamma']
        self._cap = tech_dict['capacity_kWh']
        self._ic = tech_dict['initial_charge']
        self._optimized_initial_charge = tech_dict['optimized_initial_charge']
        self._chg_dchg_per_cap_max = tech_dict['chg_dchg_per_cap_max']
        self._lifetime = tech_dict['lifetime']
        self._capex = tech_dict['capex']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
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
            printout = ('Error in BES input: '
                        'charging/discharging efficiency (eta_chg_dchg) cannot'
                        ' be larger than 1!'
                        )
            raise Exception(printout)
        if self._eta_chg_dchg <= 0:
            printout = ('Error in tes input: '
                        'charging/discharging efficiency (eta_chg_dchg) must'
                        ' be larger than 0!'
                        )
            raise Exception(printout)
        if self._gamma > 1:
            printout = ('Error in BES input: '
                        'loss factor (bes_gamma) cannot be larger than 1!'
                        )
            raise Exception(printout)

        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_e_bes'] = self.get_u_e() # electricity input [kWh]
        df['v_e_bes'] = self.get_v_e() # electricity output [kWh]
        df['q_e_bes'] = self.get_q_e() # stored energy [kWh]
        df['l_u_e_bes'] = self.get_l_u_e() # charging losses [kWh]
        df['l_v_e_bes'] = self.get_l_v_e() # discharging losses [kWh]
        df['l_q_e_bes'] = self.get_l_q_e() # storage losses [kWh]
        df['sos_bes'] = self.get_sos() # state of charge [-]
        
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
        
        self._u_e = self._u_e[:n_hours]
        self._v_e = self._v_e[:n_hours]
        self._q_e = self._q_e[:n_hours]
        self._l_u_e = self._l_u_e[:n_hours]
        self._l_v_e = self._l_v_e[:n_hours]
        self._l_q_e = self._l_q_e[:n_hours]
        self._sos = self._sos[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_e = init_vals.copy() # electricity input [kWh]
        self._v_e = init_vals.copy() # electricity output [kWh]
        self._q_e = init_vals.copy() # stored energy [kWh]
        self._l_u_e = init_vals.copy() # charging losses [kWh]
        self._l_v_e = init_vals.copy() # discharging losses [kWh]
        self._l_q_e = init_vals.copy() # storage losses [kWh]
        self._sos = init_vals.copy() # state of charge [-]
        
    def update_u_e(self, u_e_updated):
        if len(u_e_updated) != len(self._u_e):
            raise ValueError()        
        self._u_e = np.array(u_e_updated)        
        self.__compute_l_u_e()
        
    def update_v_e(self, v_e_updated):
        if len(v_e_updated) != len(self._v_e):
            raise ValueError()        
        self._v_e = np.array(v_e_updated)        
        self.__compute_l_v_e()
        
    def update_q_e(self, q_e_updated):
        if len(q_e_updated) != len(self._q_e):
            raise ValueError()        
        self._q_e = np.array(q_e_updated)        
        self.__compute_l_q_e()

    def update_sos(self, sos_updated):
        if len(sos_updated) != len(self._sos):
            raise ValueError()        
        self._sos = np.array(sos_updated)  
              
    def update_cap(self, cap_updated):
        self.num_test(cap_updated)
        self._cap = cap_updated      

    def __compute_l_u_e(self):
    # def get_charging_losses(u_e_bes, eta_chg):
        """
        Compute the charging losses for each time step.

        Parameters
        ----------
        u_u_bes : pandas Series
            Timeseries of energy supplied to storage [kWh].
        eta_chg : float
            Charging efficiency [-]. Values between 0 and 1.

        Returns
        -------
        l_u_e_bes : pandas Series
            Timeseries of energy lost due to charging [kWh].

        """
        
        l_u_e_bes = self._u_e*(1-self._eta_chg_dchg)
        
        self._l_u_e = np.array(l_u_e_bes)
        
        # return l_u_e_bes
    
    def __compute_l_v_e(self):
    # def get_discharging_losses(v_e_bes, eta_dchg):
        """
        Compute the discharging losses for each time step.

        Parameters
        ----------
        v_e_bes : pandas Series
            Timeseries of energy supplied from storage [kWh].
        eta_chg : float
            Discharging efficiency [-]. Values between 0 and 1.

        Returns
        -------
        l_v_e_bes : pandas Series
            Timeseries of energy lost due to discharging [kWh].
        
        """
        
        l_v_e_bes = self._v_e*(1/self._eta_chg_dchg - 1)
        
        self._l_v_e = np.array(l_v_e_bes)
        
        # return l_v_e_bes
    
    def __compute_l_q_e(self):
    # def get_storage_losses(q_e_bes, bes_gamma):    
        """
        Compute the storage losses for each time step.

        Parameters
        ----------
        q_e_bes : pandas Series
            Stored heat in thermal energy storage [kWh].
        tes_gamma : float
            Loss rate: fraction of energy lost during one timestep [-]
            (e.g. during 1 hour).

        Returns
        -------
        l_q_e_bes : pandas Series
            Timeseries of energy lost during storage [kWh].

        """
        
        l_q_e_bes = self._q_e*self._gamma
        
        self._l_q_e = np.array(l_q_e_bes)
        
        # return l_q_e_bes
    
    def create_techs_dict(self, techs_dict, color):

        techs_dict['bes'] = {
            'essentials':{
                'name':'Battery Energy Storage',
                'color':color,
                'parent':'storage',
                'carrier_in':'electricity',
                'carrier_out':'electricity'
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
                'emissions_co2':{
                    'om_prod':self._co2_intensity + 0.0000
                    }
                }
            }
        if self._force_asynchronous_prod_con:
            techs_dict['bes']['constraints']['force_asynchronous_prod_con']= True


        return techs_dict
    
    def get_u_e(self):
        self.len_test(self._u_e)
        return self._u_e
    
    def get_v_e(self):
        self.len_test(self._v_e)
        return self._v_e
    
    def get_q_e(self):
        self.len_test(self._q_e)
        return self._q_e
    
    def get_l_u_e(self):
        self.len_test(self._l_u_e)
        return self._l_u_e
    
    def get_l_v_e(self):
        self.len_test(self._l_v_e)
        return self._l_v_e
    
    def get_l_q_e(self):
        self.len_test(self._l_q_e)
        return self._l_q_e
    
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
    
    
    def initialise_q_e_0(self):
        self._q_e[0] = self.get_ic()*self.get_cap()

    def update_q_e_i(self, i, val):
        self.num_test(val)
        self._q_e[i] = float(val)

    def get_chg_dchg_per_cap_max(self):
        self.num_test(self._chg_dchg_per_cap_max)
        return self._chg_dchg_per_cap_max
    
    def update_u_e_i(self, i, val):
        self.num_test(val)
        self._u_e[i] = float(val)
        
    def update_v_e_i(self, i, val):
        self.num_test(val)
        self._v_e[i] = float(val)
        
    def update_q_e_i(self, i, val):
        self.num_test(val)
        self._q_e[i] = float(val)

    def update_l_u_e_i(self, i, val):
        self.num_test(val)
        self._l_u_e[i] = float(val)

    def update_l_v_e_i(self, i, val):
        self.num_test(val)
        self._l_v_e[i] = float(val)

    def update_l_q_e_i(self, i, val):
        self.num_test(val)
        self._l_q_e[i] = float(val)

    def update_sos_i(self, i, val):
        self.num_test(val)
        self._sos[i] = float(val)