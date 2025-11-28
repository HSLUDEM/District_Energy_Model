# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 08:49:07 2024

@author: UeliSchilt
"""
import numpy as np

from district_energy_model.techs.dem_tech_core import TechCore

class PileOfBerries(TechCore):
    
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
        self.input_carrier = 'berryjam' 
        self.output_carrier = 'berryjam'
        
        # Accounting:
        self._u_jam = [] # electricity input [kWh]
        self._v_jam = [] # electricity output [kWh]
        self._q_jam = [] # stored energy [kWh]
        self._l_u_jam = [] # charging losses [kWh]
        self._l_v_jam = [] # discharging losses [kWh]
        self._l_q_jam = [] # storage losses [kWh]
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
        self._eta_chg_dchg = 0.99
        self._gamma = 0.99
        self._cap = 10.0
        self._ic = 1.0
        self._optimized_initial_charge = False
        self._chg_dchg_per_cap_max = 0.2
        self._lifetime = 20.0
        self._capex = 1.0
        self._interest_rate = 0.2
        self._co2_intensity = 0.2
        self._maintenance_cost = 0.00
        self._force_asynchronous_prod_con = False
        
        
        
        # Tests:
        if self._ic > 1:
            printout = ('Error in tes input: '
                        'initial_charge cannot be larger than 1!\n'
                        f'Chosen initial_charge: {self._ic}'
                        )
            raise Exception(printout)
        if self._eta_chg_dchg > 1:
            printout = ('Error in POB input: '
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
            printout = ('Error in POB input: '
                        'loss factor (pob_gamma) cannot be larger than 1!'
                        )
            raise Exception(printout)

        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_jam_pob'] = self.get_u_jam() # electricity input [kWh]
        df['v_jam_pob'] = self.get_v_jam() # electricity output [kWh]
        df['q_jam_pob'] = self.get_q_jam() # stored energy [kWh]
        df['l_u_jam_pob'] = self.get_l_u_jam() # charging losses [kWh]
        df['l_v_jam_pob'] = self.get_l_v_jam() # discharging losses [kWh]
        df['l_q_jam_pob'] = self.get_l_q_jam() # storage losses [kWh]
        df['sos_pob'] = self.get_sos() # state of charge [-]
        
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
        
        self._u_jam = self._u_jam[:n_hours]
        self._v_jam = self._v_jam[:n_hours]
        self._q_jam = self._q_jam[:n_hours]
        self._l_u_jam = self._l_u_jam[:n_hours]
        self._l_v_jam = self._l_v_jam[:n_hours]
        self._l_q_jam = self._l_q_jam[:n_hours]
        self._sos = self._sos[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_jam = init_vals.copy() # electricity input [kWh]
        self._v_jam = init_vals.copy() # electricity output [kWh]
        self._q_jam = init_vals.copy() # stored energy [kWh]
        self._l_u_jam = init_vals.copy() # charging losses [kWh]
        self._l_v_jam = init_vals.copy() # discharging losses [kWh]
        self._l_q_jam = init_vals.copy() # discharging losses [kWh]
        self.jam = init_vals.copy() # storage losses [kWh]
        self._sos = init_vals.copy() # state of charge [-]
        
    def update_u_jam(self, u_jam_updated):
        if len(u_jam_updated) != len(self._u_jam):
            raise ValueError()        
        self._u_jam = np.array(u_jam_updated)        
        self.__compute_l_u_jam()
        
    def update_v_jam(self, v_jam_updated):
        if len(v_jam_updated) != len(self._v_jam):
            raise ValueError()        
        self._v_jam = np.array(v_jam_updated)        
        self.__compute_l_v_jam()
        
    def update_q_jam(self, q_jam_updated):
        if len(q_jam_updated) != len(self._q_jam):
            raise ValueError()        
        self._q_jam = np.array(q_jam_updated)        
        self.__compute_l_q_jam()

    def update_sos(self, sos_updated):
        if len(sos_updated) != len(self._sos):
            raise ValueError()        
        self._sos = np.array(sos_updated)  
              
    def update_cap(self, cap_updated):
        self.num_test(cap_updated)
        self._cap = cap_updated      

    def __compute_l_u_jam(self):
        l_u_jam_pob = self._u_jam*(1-self._eta_chg_dchg)
        
        self._l_u_jam = np.array(l_u_jam_pob)
        
    
    def __compute_l_v_jam(self):
        
        l_v_jam_pob = self._v_jam*(1/self._eta_chg_dchg - 1)
        
        self._l_v_jam = np.array(l_v_jam_pob)
        
    
    def __compute_l_q_jam(self):
        
        
        l_q_jam_pob = self._q_jam*self._gamma
        
        self._l_q_jam = np.array(l_q_jam_pob)
        
    
    def create_techs_dict(self, techs_dict):

        techs_dict['pile_of_berries'] = {
            'essentials':{
                'name':'Pile Of Berries',
                'parent':'storage',
                'carrier_in':'berryjam',
                'carrier_out':'berryjam'
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
            techs_dict['pile_of_berries']['constraints']['force_asynchronous_prod_con']= True


        return techs_dict
    
    def get_u_jam(self):
        self.len_test(self._u_jam)
        return self._u_jam
    
    def get_v_jam(self):
        self.len_test(self._v_jam)
        return self._v_jam
    
    def get_q_jam(self):
        self.len_test(self._q_jam)
        return self._q_jam
    
    def get_l_u_jam(self):
        self.len_test(self._l_u_jam)
        return self._l_u_jam
    
    def get_l_v_jam(self):
        self.len_test(self._l_v_jam)
        return self._l_v_jam
    
    def get_l_q_jam(self):
        self.len_test(self._l_q_jam)
        return self._l_q_jam
    
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
    
    
    # def initialise_q_e_0(self):
    #     self._q_e[0] = self.get_ic()*self.get_cap()

    # def update_q_e_i(self, i, val):
    #     self.num_test(val)
    #     self._q_e[i] = float(val)

    # def get_chg_dchg_per_cap_max(self):
    #     self.num_test(self._chg_dchg_per_cap_max)
    #     return self._chg_dchg_per_cap_max
    
    # def update_u_e_i(self, i, val):
    #     self.num_test(val)
    #     self._u_e[i] = float(val)
        
    # def update_v_e_i(self, i, val):
    #     self.num_test(val)
    #     self._v_e[i] = float(val)
        
    # def update_q_e_i(self, i, val):
    #     self.num_test(val)
    #     self._q_e[i] = float(val)

    # def update_l_u_e_i(self, i, val):
    #     self.num_test(val)
    #     self._l_u_e[i] = float(val)

    # def update_l_v_e_i(self, i, val):
    #     self.num_test(val)
    #     self._l_v_e[i] = float(val)

    # def update_l_q_e_i(self, i, val):
    #     self.num_test(val)
    #     self._l_q_e[i] = float(val)

    # def update_sos_i(self, i, val):
    #     self.num_test(val)
    #     self._sos[i] = float(val)