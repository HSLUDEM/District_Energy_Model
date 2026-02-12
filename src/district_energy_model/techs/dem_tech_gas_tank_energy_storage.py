#Gas tank energy storage

# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 08:49:07 2024

@author: PascalVecsei
"""
import numpy as np

from district_energy_model.techs.dem_tech_core import TechCore

class GasTankEnergyStorage(TechCore):
    
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
        self.input_carrier = 'gas' 
        self.output_carrier = 'gas'
        
        # Accounting:
        self._u_gas = [] # electricity input [gas unit]
        self._v_gas = [] # electricity output [gas unit]
        self._q_gas = [] # stored energy [gas unit]
        self._l_u_gas = [] # charging losses [gas unit]
        self._l_v_gas = [] # discharging losses [gas unit]
        self._l_q_gas = [] # storage losses [gas unit]
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
        self._gamma = tech_dict['gtes_gamma']
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
            printout = ('Error in gas tank input: '
                        'charging/discharging efficiency (eta_chg_dchg) cannot'
                        ' be larger than 1!'
                        )
            raise Exception(printout)
        if self._eta_chg_dchg <= 0:
            printout = ('Error in gas tank input: '
                        'charging/discharging efficiency (eta_chg_dchg) must'
                        ' be larger than 0!'
                        )
            raise Exception(printout)
        if self._gamma > 1:
            printout = ('Error in gas tank input: '
                        'loss factor (gtes_gamma) cannot be larger than 1!'
                        )
            raise Exception(printout)

        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['u_gas_gtes'] = self.get_u_gas() # gas input [gas unit]
        df['v_gas_gtes'] = self.get_v_gas() # gas output [gas unit]
        df['q_gas_gtes'] = self.get_q_gas() # stored gas [gas unit]
        df['l_u_gas_gtes'] = self.get_l_u_gas() # charging losses [gas unit]
        df['l_v_gas_gtes'] = self.get_l_v_gas() # discharging losses [gas unit]
        df['l_q_gas_gtes'] = self.get_l_q_gas() # storage losses [gas unit]
        df['sos_gtes'] = self.get_sos() # state of charge [-]
        
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
        
        self._u_gas = self._u_gas[:n_hours]
        self._v_gas = self._v_gas[:n_hours]
        self._q_gas = self._q_gas[:n_hours]
        self._l_u_gas = self._l_u_gas[:n_hours]
        self._l_v_gas = self._l_v_gas[:n_hours]
        self._l_q_gas = self._l_q_gas[:n_hours]
        self._sos = self._sos[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_gas = init_vals.copy() # electricity input [kWh]
        self._v_gas = init_vals.copy() # electricity output [kWh]
        self._q_gas = init_vals.copy() # stored energy [kWh]
        self._l_u_gas = init_vals.copy() # charging losses [kWh]
        self._l_v_gas = init_vals.copy() # discharging losses [kWh]
        self._l_q_gas = init_vals.copy() # storage losses [kWh]
        self._sos = init_vals.copy() # state of charge [-]
        
    def update_u_gas(self, u_gas_updated):
        if len(u_gas_updated) != len(self._u_gas):
            raise ValueError()        
        self._u_gas = np.array(u_gas_updated)        
        self.__compute_l_u_gas()
        
    def update_v_gas(self, v_gas_updated):
        if len(v_gas_updated) != len(self._v_gas):
            raise ValueError()        
        self._v_gas = np.array(v_gas_updated)        
        self.__compute_l_v_gas()
        
    def update_q_gas(self, q_gas_updated):
        if len(q_gas_updated) != len(self._q_gas):
            raise ValueError()        
        self._q_gas = np.array(q_gas_updated)        
        self.__compute_l_q_gas()

    def update_sos(self, sos_updated):
        if len(sos_updated) != len(self._sos):
            raise ValueError()        
        self._sos = np.array(sos_updated)  
              
    def update_cap(self, cap_updated):
        self.num_test(cap_updated)
        self._cap = cap_updated      

    def __compute_l_u_gas(self):
        """
        Compute the charging losses for each time step.

        Parameters
        ----------

        Returns
        -------

        """
        
        l_u_gas_gtes = self._u_gas*(1-self._eta_chg_dchg)
        
        self._l_u_gas = np.array(l_u_gas_gtes)
        
    def __compute_l_v_gas(self):
        """
        Compute the discharging losses for each time step.

        Parameters
        ----------
        Returns
        -------
        """
        
        l_v_gas_gtes = self._v_gas*(1/self._eta_chg_dchg - 1)
        
        self._l_v_gas = np.array(l_v_gas_gtes)
        
    def __compute_l_q_gas(self):
    # def get_storage_losses(q_e_gtes, gtes_gamma):    
        """
        Compute the storage losses for each time step.

        Parameters
        ----------
        Returns
        -------

        """
        
        l_q_gas_gtes = self._q_gas*self._gamma
        
        self._l_q_gas = np.array(l_q_gas_gtes)
        
    
    def create_techs_dict(self, techs_dict, color, energy_scaling_factor):

        techs_dict['gtes'] = {
            'essentials':{
                'name':'Gas Tank Energy Storage',
                'color':color,
                'parent':'storage',
                'carrier_in':'gas',
                'carrier_out':'gas'
                },
            'constraints':{
                'storage_initial':self._ic if not self._optimized_initial_charge else None,
                'storage_cap_max':self._cap / energy_scaling_factor if self._cap != 'inf' else 'inf',
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
                    'storage_cap':self._capex * energy_scaling_factor,
                    'interest_rate':self._interest_rate,
                    'om_annual': self._maintenance_cost * energy_scaling_factor
                    },
                }
            }
        if self._force_asynchronous_prod_con:
            techs_dict['gtes']['constraints']['force_asynchronous_prod_con']= True

        return techs_dict
    
    def get_u_gas(self):
        self.len_test(self._u_gas)
        return self._u_gas
    
    def get_v_gas(self):
        self.len_test(self._v_gas)
        return self._v_gas
    
    def get_q_gas(self):
        self.len_test(self._q_gas)
        return self._q_gas
    
    def get_l_u_gas(self):
        self.len_test(self._l_u_gas)
        return self._l_u_gas
    
    def get_l_v_gas(self):
        self.len_test(self._l_v_gas)
        return self._l_v_gas
    
    def get_l_q_gas(self):
        self.len_test(self._l_q_gas)
        return self._l_q_gas
    
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
    
    
    def initialise_q_gas_0(self):
        self._q_gas[0] = self.get_ic()*self.get_cap()

    def update_q_gas_i(self, i, val):
        self.num_test(val)
        self._q_gas[i] = float(val)

    def get_chg_dchg_per_cap_max(self):
        self.num_test(self._chg_dchg_per_cap_max)
        return self._chg_dchg_per_cap_max
    
    def update_u_gas_i(self, i, val):
        self.num_test(val)
        self._u_gas[i] = float(val)
        
    def update_v_gas_i(self, i, val):
        self.num_test(val)
        self._v_gas[i] = float(val)
        
    def update_q_gas_i(self, i, val):
        self.num_test(val)
        self._q_gas[i] = float(val)

    def update_l_u_gas_i(self, i, val):
        self.num_test(val)
        self._l_u_gas[i] = float(val)

    def update_l_v_gas_i(self, i, val):
        self.num_test(val)
        self._l_v_gas[i] = float(val)

    def update_l_q_gas_i(self, i, val):
        self.num_test(val)
        self._l_q_gas[i] = float(val)

    def update_sos_i(self, i, val):
        self.num_test(val)
        self._sos[i] = float(val)