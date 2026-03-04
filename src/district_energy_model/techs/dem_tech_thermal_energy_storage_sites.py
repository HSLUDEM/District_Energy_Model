# -*- coding: utf-8 -*-
"""
Created on Jan 16 2026

@author: PascalVecsei
"""
import numpy as np

from district_energy_model.techs.dem_tech_core import TechCore

class ThermalEnergyStorageSites(TechCore):
    
    def __init__(self, tech_dict, tes_sites_list):
        
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

        self._sites_list = tes_sites_list

        self.update_tech_properties(tech_dict)
        
        # Accounting:
        self._u_hhtht = [] # heat input [kWh]
        self._v_hhtht = [] # heat output [kWh]
        self._q_hhtht = [] # stored energy [kWh]
        self._l_u_hhtht = [] # charging losses [kWh]
        self._l_v_hhtht = [] # discharging losses [kWh]
        self._l_q_hhtht = [] # storage losses [kWh]
        
        self._u_hhtlt = [] # heat input [kWh]
        self._v_hhtlt = [] # heat output [kWh]
        self._q_hhtlt = [] # stored energy [kWh]
        self._l_u_hhtlt = [] # charging losses [kWh]
        self._l_v_hhtlt = [] # discharging losses [kWh]
        self._l_q_hhtlt = [] # storage losses [kWh]

        self._u_hltlt = [] # heat input [kWh]
        self._v_hltlt = [] # heat output [kWh]
        self._q_hltlt = [] # stored energy [kWh]
        self._l_u_hltlt = [] # charging losses [kWh]
        self._l_v_hltlt = [] # discharging losses [kWh]
        self._l_q_hltlt = [] # storage losses [kWh]

        self._u_hht_to_hlt = []

        self._soc = [] # state of charge [-]
        self._soc_hhtht = [] # state of charge  [-]
        self._soc_hhtlt = [] # state of charge  [-]
        self._soc_hltlt = [] # state of charge  [-]

        self._cap_htht = []
        self._cap_htlt = []
        self._cap_ltlt = []



            
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

        self._force_asynchronous_prod_con = tech_dict['force_asynchronous_prod_con']

        for site_entry in self._sites_list:
            for k in site_entry['eta_chg_dchg'].keys():
                if site_entry['eta_chg_dchg'][k] > 1:
                    printout = ('Error in tes site ('+site_entry['name']+ ' : '+k+') input: '
                                'charging/discharging efficiency (eta_chg_dchg) cannot'
                                ' be larger than 1!'
                                )
                    raise Exception(printout)
                if site_entry['eta_chg_dchg'][k] < 0:
                    printout = ('Error in tes site ('+site_entry['name']+ ' : '+k+') input: '
                                'charging/discharging efficiency (eta_chg_dchg) must'
                                ' be larger than 0!'
                                )
                    raise Exception(printout)
            for k in site_entry['storage_loss_rate'].keys():
                if site_entry['storage_loss_rate'][k] > 1:
                    printout = ('Error in tes site ('+site_entry['name']+ ' : '+k+') input: '
                                'loss factor (storage_loss_rate) cannot be larger than 1!'
                                )
                    raise Exception(printout)
        
        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):

        for i in range(len(self._sites_list)):

            site_entry = self._sites_list[i]

            df['u_hhtht_tes_site_'+site_entry['name']] = self.get_u_hhtht_site(site_entry_index = i) # heat input [kWh]
            df['v_hhtht_tes_site_'+site_entry['name']] = self.get_v_hhtht_site(site_entry_index = i) # heat output [kWh]
            df['q_hhtht_tes_site_'+site_entry['name']] = self.get_q_hhtht_site(site_entry_index = i) # stored energy [kWh] #av. hot heat
            df['l_u_hhtht_tes_site_'+site_entry['name']] = self.get_l_u_hhtht_site(site_entry_index = i) # charging losses [kWh]
            df['l_v_hhtht_tes_site_'+site_entry['name']] = self.get_l_v_hhtht_site(site_entry_index = i) # discharging losses [kWh]
            df['l_q_hhtht_tes_site_'+site_entry['name']] = self.get_l_q_hhtht_site(site_entry_index = i) # storage losses [kWh]

            df['u_hhtlt_tes_site_'+site_entry['name']] = self.get_u_hhtlt_site(site_entry_index = i) # heat input [kWh]
            df['v_hhtlt_tes_site_'+site_entry['name']] = self.get_v_hhtlt_site(site_entry_index = i) # heat output [kWh]
            df['q_hhtlt_tes_site_'+site_entry['name']] = self.get_q_hhtlt_site(site_entry_index = i) # stored energy [kWh] #available cold heat
            df['l_u_hhtlt_tes_site_'+site_entry['name']] = self.get_l_u_hhtlt_site(site_entry_index = i) # charging losses [kWh]
            df['l_v_hhtlt_tes_site_'+site_entry['name']] = self.get_l_v_hhtlt_site(site_entry_index = i) # discharging losses [kWh]
            df['l_q_hhtlt_tes_site_'+site_entry['name']] = self.get_l_q_hhtlt_site(site_entry_index = i) # storage losses [kWh]

            df['u_hltlt_tes_site_'+site_entry['name']] = self.get_u_hltlt_site(site_entry_index = i) # heat input [kWh]
            df['v_hltlt_tes_site_'+site_entry['name']] = self.get_v_hltlt_site(site_entry_index = i) # heat output [kWh]
            df['q_hltlt_tes_site_'+site_entry['name']] = self.get_q_hltlt_site(site_entry_index = i) # stored energy [kWh] #available cold heat
            df['l_u_hltlt_tes_site_'+site_entry['name']] = self.get_l_u_hltlt_site(site_entry_index = i) # charging losses [kWh]
            df['l_v_hltlt_tes_site_'+site_entry['name']] = self.get_l_v_hltlt_site(site_entry_index = i) # discharging losses [kWh]
            df['l_q_hltlt_tes_site_'+site_entry['name']] = self.get_l_q_hltlt_site(site_entry_index = i) # storage losses [kWh]

            df['u_hht_to_hlt_tes_site_'+site_entry['name']] = self.get_u_hht_to_hlt(site_entry_index = i)

            df['soc_tes_site_'+site_entry['name']] = self.get_soc_site(site_entry_index = i) # state of charge [-] (combined h and hlt)
            df['soc_hhtht_tes_site_'+site_entry['name']] = self.get_soc_hhtht_site(site_entry_index = i) # state of charge [-] 
            df['soc_hhtlt_tes_site_'+site_entry['name']] = self.get_soc_hhtlt_site(site_entry_index = i) # state of charge [-] 
            df['soc_hltlt_tes_site_'+site_entry['name']] = self.get_soc_hltlt_site(site_entry_index = i) # state of charge [-] 

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
        
        self._u_hhtht = self._u_hhtht[:, :n_hours]
        self._v_hhtht = self._v_hhtht[:, :n_hours]
        self._q_hhtht = self._q_hhtht[:, :n_hours]
        self._l_u_hhtht = self._l_u_hhtht[:, :n_hours]
        self._l_v_hhtht = self._l_v_hhtht[:, :n_hours]
        self._l_q_hhtht = self._l_q_hhtht[:, :n_hours]

        self._u_hhtlt = self._u_hhtlt[:, :n_hours]
        self._v_hhtlt = self._v_hhtlt[:, :n_hours]
        self._q_hhtlt = self._q_hhtlt[:, :n_hours]
        self._l_u_hhtlt = self._l_u_hhtlt[:, :n_hours]
        self._l_v_hhtlt = self._l_v_hhtlt[:, :n_hours]
        self._l_q_hhtlt = self._l_q_hhtlt[:, :n_hours]

        self._u_hltlt = self._u_hltlt[:, :n_hours]
        self._v_hltlt = self._v_hltlt[:, :n_hours]
        self._q_hltlt = self._q_hltlt[:, :n_hours]
        self._l_u_hltlt = self._l_u_hltlt[:, :n_hours]
        self._l_v_hltlt = self._l_v_hltlt[:, :n_hours]
        self._l_q_hltlt = self._l_q_hltlt[:, :n_hours]

        self._u_hht_to_hlt = self._u_hltlt[:, :n_hours]

        self._soc = self._soc[:, :n_hours]
        self._soc_hhtht = self._soc_hhtht[:, :n_hours]
        self._soc_hhtlt = self._soc_hhtlt[:, :n_hours]
        self._soc_hhtlt = self._soc_hltlt[:, :n_hours]

    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.zeros(shape = (len(self._sites_list), n_hours))
        
        self._u_hhtht = init_vals.copy() # heat input [kWh]
        self._v_hhtht = init_vals.copy() # heat output [kWh]
        self._q_hhtht = init_vals.copy() # stored energy [kWh]
        self._l_u_hhtht = init_vals.copy() # charging losses [kWh]
        self._l_v_hhtht = init_vals.copy() # discharging losses [kWh]
        self._l_q_hhtht = init_vals.copy() # storage losses [kWh]

        self._u_hhtlt = init_vals.copy() # heat input [kWh]
        self._v_hhtlt = init_vals.copy() # heat output [kWh]
        self._q_hhtlt = init_vals.copy() # stored energy [kWh]
        self._l_u_hhtlt = init_vals.copy() # charging losses [kWh]
        self._l_v_hhtlt = init_vals.copy() # discharging losses [kWh]
        self._l_q_hhtlt = init_vals.copy() # storage losses [kWh]

        self._u_hltlt = init_vals.copy() # heat input [kWh]
        self._v_hltlt = init_vals.copy() # heat output [kWh]
        self._q_hltlt = init_vals.copy() # stored energy [kWh]
        self._l_u_hltlt = init_vals.copy() # charging losses [kWh]
        self._l_v_hltlt = init_vals.copy() # discharging losses [kWh]
        self._l_q_hltlt = init_vals.copy() # storage losses [kWh]

        self._u_hht_to_hlt = init_vals.copy()

        self._soc = init_vals.copy() # state of charge [-]
        self._soc_hhtht = init_vals.copy() # state of charge (lt) [-]
        self._soc_hhtlt = init_vals.copy() # state of charge (ht) [-]
        self._soc_hltlt = init_vals.copy() # state of charge (ht) [-]

        init_vals_cap = np.zeros(shape = (len(self._sites_list),))

        self._cap_htht = init_vals_cap.copy()
        self._cap_htlt = init_vals_cap.copy()
        self._cap_ltlt = init_vals_cap.copy()


    def get_u_hhtht_site(self, site_entry_index):
        self.len_test(self._u_hhtht[site_entry_index])
        return self._u_hhtht[site_entry_index]

    def get_v_hhtht_site(self, site_entry_index):
        self.len_test(self._v_hhtht[site_entry_index])
        return self._v_hhtht[site_entry_index]

    def get_q_hhtht_site(self, site_entry_index):
        self.len_test(self._q_hhtht[site_entry_index])
        return self._q_hhtht[site_entry_index]

    def get_l_u_hhtht_site(self, site_entry_index):
        self.len_test(self._l_u_hhtht[site_entry_index])
        return self._l_u_hhtht[site_entry_index]

    def get_l_v_hhtht_site(self, site_entry_index):
        self.len_test(self._l_v_hhtht[site_entry_index])
        return self._l_v_hhtht[site_entry_index]

    def get_l_q_hhtht_site(self, site_entry_index):
        self.len_test(self._l_q_hhtht[site_entry_index])
        return self._l_q_hhtht[site_entry_index]



    def get_u_hhtlt_site(self, site_entry_index):
        self.len_test(self._u_hhtlt[site_entry_index])
        return self._u_hhtlt[site_entry_index]

    def get_v_hhtlt_site(self, site_entry_index):
        self.len_test(self._v_hhtlt[site_entry_index])
        return self._v_hhtlt[site_entry_index]

    def get_q_hhtlt_site(self, site_entry_index):
        self.len_test(self._q_hhtlt[site_entry_index])
        return self._q_hhtlt[site_entry_index]

    def get_l_u_hhtlt_site(self, site_entry_index):
        self.len_test(self._l_u_hhtlt[site_entry_index])
        return self._l_u_hhtlt[site_entry_index]

    def get_l_v_hhtlt_site(self, site_entry_index):
        self.len_test(self._l_v_hhtlt[site_entry_index])
        return self._l_v_hhtlt[site_entry_index]

    def get_l_q_hhtlt_site(self, site_entry_index):
        self.len_test(self._l_q_hhtlt[site_entry_index])
        return self._l_q_hhtlt[site_entry_index]



    def get_u_hltlt_site(self, site_entry_index):
        self.len_test(self._u_hltlt[site_entry_index])
        return self._u_hltlt[site_entry_index]

    def get_v_hltlt_site(self, site_entry_index):
        self.len_test(self._v_hltlt[site_entry_index])
        return self._v_hltlt[site_entry_index]

    def get_q_hltlt_site(self, site_entry_index):
        self.len_test(self._q_hltlt[site_entry_index])
        return self._q_hltlt[site_entry_index]

    def get_l_u_hltlt_site(self, site_entry_index):
        self.len_test(self._l_u_hltlt[site_entry_index])
        return self._l_u_hltlt[site_entry_index]

    def get_l_v_hltlt_site(self, site_entry_index):
        self.len_test(self._l_v_hltlt[site_entry_index])
        return self._l_v_hltlt[site_entry_index]

    def get_l_q_hltlt_site(self, site_entry_index):
        self.len_test(self._l_q_hltlt[site_entry_index])
        return self._l_q_hltlt[site_entry_index]




    def get_soc_site(self, site_entry_index):
        self.len_test(self._soc[site_entry_index])
        return self._soc[site_entry_index]

    def get_soc_hhtht_site(self, site_entry_index):
        self.len_test(self._soc_hhtht[site_entry_index])
        return self._soc_hhtht[site_entry_index]

    def get_soc_hhtlt_site(self, site_entry_index):
        self.len_test(self._soc_hhtlt[site_entry_index])
        return self._soc_hhtlt[site_entry_index]

    def get_soc_hltlt_site(self, site_entry_index):
        self.len_test(self._soc_hltlt[site_entry_index])
        return self._soc_hltlt[site_entry_index]
    
    def get_u_hht_to_hlt(self, site_entry_index):
        self.len_test(self._u_hht_to_hlt[site_entry_index])
        return self._u_hht_to_hlt[site_entry_index]


    def set_u_h_site_type(self, ext_series, site_entry_index, heat_type):
        if heat_type == 'htht':
            return self.set_u_hhtht_site(ext_series, site_entry_index)
        elif heat_type == 'htlt':
            return self.set_u_hhtlt_site(ext_series, site_entry_index)
        elif heat_type == 'ltlt':
            return self.set_u_hltlt_site(ext_series, site_entry_index)
        else:
            raise ValueError("Inadmissible type "+str(heat_type))

    def set_v_h_site_type(self, ext_series, site_entry_index, heat_type):
        if heat_type == 'htht':
            return self.set_v_hhtht_site(ext_series, site_entry_index)
        elif heat_type == 'htlt':
            return self.set_v_hhtlt_site(ext_series, site_entry_index)
        elif heat_type == 'ltlt':
            return self.set_v_hltlt_site(ext_series, site_entry_index)
        else:
            raise ValueError("Inadmissible type "+str(heat_type))

    def set_q_h_site_type(self, ext_series, site_entry_index, heat_type):
        if heat_type == 'htht':
            return self.set_q_hhtht_site(ext_series, site_entry_index)
        elif heat_type == 'htlt':
            return self.set_q_hhtlt_site(ext_series, site_entry_index)
        elif heat_type == 'ltlt':
            return self.set_q_hltlt_site(ext_series, site_entry_index)
        else:
            raise ValueError("Inadmissible type "+str(heat_type))

    def set_cap_site_type(self, cap_updated, site_entry_index, heat_type):
        if heat_type == 'htht':
            return self.set_cap_htht_site(cap_updated, site_entry_index)
        elif heat_type == 'htlt':
            return self.set_cap_htlt_site(cap_updated, site_entry_index)
        elif heat_type == 'ltlt':
            return self.set_cap_ltlt_site(cap_updated, site_entry_index)
        else:
            raise ValueError("Inadmissible type "+str(heat_type))


    def update_soc_site_type(self, site_entry_index, heat_type):
        if heat_type == 'htht':
            return self.update_soc_htht(site_entry_index)
        elif heat_type == 'htlt':
            return self.update_soc_htlt(site_entry_index)
        elif heat_type == 'ltlt':
            return self.update_soc_ltlt(site_entry_index)
        else:
            raise ValueError("Inadmissible type "+str(heat_type))

    def update_losses_site_type(self, site_entry_index, heat_type):
        if heat_type == 'htht':
            return self.update_losses_htht(site_entry_index)
        elif heat_type == 'htlt':
            return self.update_losses_htlt(site_entry_index)
        elif heat_type == 'ltlt':
            return self.update_losses_ltlt(site_entry_index)
        else:
            raise ValueError("Inadmissible type "+str(heat_type))


    def set_u_hhtht_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._u_hhtht[site_entry_index] = ext_series

    def set_v_hhtht_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._v_hhtht[site_entry_index] = ext_series

    def set_q_hhtht_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._q_hhtht[site_entry_index] = ext_series

    def set_l_u_hhtht_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._l_u_hhtht[site_entry_index] = ext_series

    def set_l_v_hhtht_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._l_v_hhtht[site_entry_index] = ext_series

    def set_l_q_hhtht_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._l_q_hhtht[site_entry_index] = ext_series
    


    def set_u_hhtlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._u_hhtlt[site_entry_index] = ext_series

    def set_v_hhtlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._v_hhtlt[site_entry_index] = ext_series

    def set_q_hhtlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._q_hhtlt[site_entry_index] = ext_series

    def set_l_u_hhtlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._l_u_hhtlt[site_entry_index] = ext_series

    def set_l_v_hhtlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._l_v_hhtlt[site_entry_index] = ext_series

    def set_l_q_hhtlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._l_q_hhtlt[site_entry_index] = ext_series
    


    def set_u_hltlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._u_hltlt[site_entry_index] = ext_series

    def set_v_hltlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._v_hltlt[site_entry_index] = ext_series

    def set_q_hltlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._q_hltlt[site_entry_index] = ext_series

    def set_l_u_hltlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._l_u_hltlt[site_entry_index] = ext_series

    def set_l_v_hltlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._l_v_hltlt[site_entry_index] = ext_series

    def set_l_q_hltlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._l_q_hltlt[site_entry_index] = ext_series


    def set_soc_hhtht_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._soc_hhtht[site_entry_index] = ext_series

    def set_soc_hhtlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._soc_hhtlt[site_entry_index] = ext_series

    def set_soc_hltlt_site(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._soc_hltlt[site_entry_index] = ext_series

    def set_u_hht_to_hlt(self, ext_series, site_entry_index):
        self.len_test(ext_series)
        self._u_hht_to_hlt[site_entry_index] = ext_series

    def update_soc_htht(self, site_entry_index):

        if self._cap_htht[site_entry_index] > 0:
            self._soc_hhtht[site_entry_index] = self._q_hhtht[site_entry_index] / self._cap_htht[site_entry_index]
        else:
            self._soc_hhtht[site_entry_index] = 0.0*self._q_hhtht[site_entry_index]

    def update_soc_htlt(self, site_entry_index):
        if self._cap_htlt[site_entry_index] > 0:
            self._soc_hhtlt[site_entry_index] = self._q_hhtlt[site_entry_index] / self._cap_htlt[site_entry_index]
        else:
            self._soc_hhtlt[site_entry_index] = 0.0*self._q_hhtlt[site_entry_index]

    def update_soc_ltlt(self, site_entry_index):
        if self._cap_ltlt[site_entry_index] > 0:
            self._soc_hltlt[site_entry_index] = self._q_hltlt[site_entry_index] / self._cap_ltlt[site_entry_index]
        else:
            self._soc_hltlt[site_entry_index] = 0.0*self._q_hltlt[site_entry_index]

    def update_losses_htht(self, site_entry_index):
        self._l_q_hhtht[site_entry_index] = self._sites_list[site_entry_index]['storage_loss_rate']['htht'] * self._q_hhtht[site_entry_index]
        self._l_u_hhtht[site_entry_index] = (1.0-self._sites_list[site_entry_index]['eta_chg_dchg']['htht']) * self._u_hhtht[site_entry_index]
        self._l_v_hhtht[site_entry_index] = (1.0/self._sites_list[site_entry_index]['eta_chg_dchg']['htht'] - 1.0) * self._v_hhtht[site_entry_index]

    def update_losses_htlt(self, site_entry_index):
        self._l_q_hhtlt[site_entry_index] = self._sites_list[site_entry_index]['storage_loss_rate']['htht'] * self._q_hhtht[site_entry_index]
        self._l_u_hhtlt[site_entry_index] = (1.0-self._sites_list[site_entry_index]['eta_chg_dchg']['htlt']) * self._u_hhtlt[site_entry_index]
        self._l_v_hhtlt[site_entry_index] = (1.0/self._sites_list[site_entry_index]['eta_chg_dchg']['ltlt'] - 1.0) * self._v_hltlt[site_entry_index]

    def update_losses_ltlt(self, site_entry_index):
        self._l_q_hltlt[site_entry_index] = self._sites_list[site_entry_index]['storage_loss_rate']['htht'] * self._q_hhtht[site_entry_index]
        self._l_u_hltlt[site_entry_index] = (1.0-self._sites_list[site_entry_index]['eta_chg_dchg']['htlt']) * self._u_hhtlt[site_entry_index]
        self._l_v_hltlt[site_entry_index] = (1.0/self._sites_list[site_entry_index]['eta_chg_dchg']['ltlt'] - 1.0) * self._v_hltlt[site_entry_index]

    def set_cap_htht_site(self, cap_updated, site_entry_index):
        self.num_test(cap_updated)
        self._cap_htht[site_entry_index] = cap_updated      

    def set_cap_htlt_site(self, cap_updated, site_entry_index):
        self.num_test(cap_updated)
        self._cap_htlt[site_entry_index] = cap_updated      

    def set_cap_ltlt_site(self, cap_updated, site_entry_index):
        self.num_test(cap_updated)
        self._cap_ltlt[site_entry_index] = cap_updated      

    def get_list_of_sitekeys(self):
        return self._sitekeys

    def get_sites_list(self):
        return self._sites_list

    def get_custom_constraints_required(self):
        flag = False
        for i in range(len(self._sites_list)):
            if self._sites_list[i]['type'] == 'simple_fully_stratified_three_temperature_levels':
                flag = True

        return flag

    def create_techs_dict(self, techs_dict, color, energy_scaling_factor):

        tes_sites_techs_label_list = []

        self._sitekeys = []

        for site_entry in self._sites_list:
            if site_entry['type'] == 'simple_fully_stratified_three_temperature_levels':
                
                sitekeys_per_loc = []
                levels_to_deploy = []

                for k in site_entry['rel_size_t_levels'].keys():
                    if site_entry['rel_size_t_levels'][k] > 0:
                        levels_to_deploy.append(k)

                for level in levels_to_deploy:

                    tes_key = 'tes_site_'+site_entry['name']+'_'+level

                    sitekeys_per_loc.append(tes_key)

                    tes_sites_techs_label_list.append(tes_key)

                    techs_dict[tes_key] = {}

                    techs_dict[tes_key] = {
                        'essentials':{
                            'name':'Thermal Energy Storage TES Site ' + site_entry['name'] + ' ' + level ,
                            'color':color,
                            'parent':'storage',
                            'carrier_in': 'heat_tes_site_'+site_entry['name']+'_'+level,
                            'carrier_out': 'heat_tes_site_'+site_entry['name']+'_'+level,
                            },
                        'constraints':{
                            'storage_initial': None,
                            # 'storage_cap_max': site_entry['capacity_kWh_max']*site_entry['rel_size_t_levels'][level],
                            # 'storage_cap_min': (site_entry['capacity_kWh_min']*site_entry['rel_size_t_levels'][level] 
                            #                     if site_entry['capacity_kWh_min']>0 
                            #                     else None),
                            'storage_loss': site_entry['storage_loss_rate'][level],
                            'energy_eff': site_entry['eta_chg_dchg'][level],
                            'energy_cap_per_storage_cap_max': site_entry['chg_dchg_per_cap_max'],
                            'lifetime': site_entry['lifetime'],
                            },
                        'costs':{
                            'monetary':{
                                'om_prod':0.0000, # [CHF/kWh_dchg] artificial cost per discharged kWh; used to avoid cycling within timestep
                                'storage_cap': site_entry['capex_per_kWh'] * energy_scaling_factor,
                                # 'om_annual': site_entry['maintenance_cost_per_kWh'],
                                'interest_rate': site_entry['interest_rate']
                                },
                            }
                        }
                    
                    if self._force_asynchronous_prod_con:
                        techs_dict[tes_key]['constraints']['force_asynchronous_prod_con'] = True

                # ----------------------------------------
                # Conversion technologies for connected technologies in district heating network:
                    
                # From TES to district heating network (one-way connection):

                connections = []
                if 'htlt' in levels_to_deploy:
                    connections.append({'name': 'Conversion: HEAT_TES_LT to HEAT_LT at '+site_entry['name'],
                                        'techs_dict_symb': 'conv_'+site_entry['name']+'_lt_to_'+'heatlt_htlt',
                                        'heatflow_in': 'heat_tes_site_'+site_entry['name']+'_'+'htlt',
                                        'heatflow_out': 'heatlt'
                                        })
                if 'ltlt' in levels_to_deploy:
                    connections.append({'name': 'Conversion: HEAT_TES_LT to HEAT_LT at '+site_entry['name'],
                                        'techs_dict_symb': 'conv_'+site_entry['name']+'_lt_to_'+'heatlt_ltlt',
                                        'heatflow_in': 'heat_tes_site_'+site_entry['name']+'_'+'ltlt',
                                        'heatflow_out': 'heatlt'
                                        })

                if 'htht' in levels_to_deploy:
                    connections.append({'name': 'Conversion: HEAT_TES_HT to HEAT_DH at '+site_entry['name'],
                                        'techs_dict_symb': 'conv_'+site_entry['name']+'_ht_to_'+'heat_htht',
                                        'heatflow_in': 'heat_tes_site_'+site_entry['name']+'_'+'htht',
                                        'heatflow_out': 'heat_dh'
                                        })
                    
                if 'ltlt' in levels_to_deploy:
                    connections.append({'name': 'Conversion: HEAT_TES_HTHT to HEAT_TES_LTLT at '+site_entry['name'],
                                        'techs_dict_symb': 'conv_'+site_entry['name']+'_htht_to_'+site_entry['name']+'_ltlt',
                                        'heatflow_in': 'heat_tes_site_'+site_entry['name']+'_'+'htht',
                                        'heatflow_out': 'heat_tes_site_'+site_entry['name']+'_'+'ltlt'
                                        })
                    connections.append({'name': 'Conversion: HEAT_TES_HTLT to HEAT_TES_LTLT at '+site_entry['name'],
                                        'techs_dict_symb': 'conv_'+site_entry['name']+'_htlt_to_'+site_entry['name']+'_ltlt',
                                        'heatflow_in': 'heat_tes_site_'+site_entry['name']+'_'+'htlt',
                                        'heatflow_out': 'heat_tes_site_'+site_entry['name']+'_'+'ltlt'
                                        })


                for k in site_entry['connected_techs']:
                    for shortname_of_tech in site_entry['connected_techs'][k]:
                        if k == 'lt':
                            connections.append({'name': 'Conversion: '+'heatlt'+' to '+ 'heat_tes_site_'+site_entry['name']+'_'+'lt'+' at '+site_entry['name'],
                                            'techs_dict_symb': 'conv_'+site_entry['name']+'_'+'heatlt'+'_to_'+('heat_tes_site_'+site_entry['name']+'_'+'ltlt'),
                                            'heatflow_in': 'heatlt',
                                            'heatflow_out': 'heat_tes_site_'+site_entry['name']+'_'+'ltlt',
                                            })
                        elif k== 'ht':
                            for convtype in ['ht', 'lt']:
                                connections.append({'name': 'Conversion: '+ 'heat_'+str(shortname_of_tech)+' to '+ 'heat_tes_site_'+site_entry['name']+'_'+ 'ht'+str(convtype) +' at '+site_entry['name'],
                                                'techs_dict_symb': 'conv_'+site_entry['name']+'_'+ 'heat_'+str(shortname_of_tech) +'_to_'+('heat_tes_site_'+site_entry['name']+'_'+'ht'+str(convtype)),
                                                'heatflow_in': 'heat_'+str(shortname_of_tech),
                                                'heatflow_out': 'heat_tes_site_'+site_entry['name']+'_'+'ht'+str(convtype),
                                                })

                        

                for connection_dict in connections:
                    techs_dict[connection_dict['techs_dict_symb']] = {
                        'essentials':{
                            'name': connection_dict['name'],
                            'parent':'conversion',
                            'carrier_in': connection_dict['heatflow_in'],
                            'carrier_out': connection_dict['heatflow_out'],
                            },
                        'constraints':{
                            'energy_cap_max':'inf',
                            'energy_eff':1.0, # Here we could account for transmission losses
                            'lifetime':site_entry['lifetime'],
                            },
                        'costs':{
                            'monetary':{
                                'om_con': 0.0, # costs are reflected in supply techs
                                'interest_rate':0.0,
                                },
                            } 
                        }
                    

                    tes_sites_techs_label_list.append(connection_dict['techs_dict_symb'])
                
                self._sitekeys.append(sitekeys_per_loc)

        return techs_dict, tes_sites_techs_label_list

    def get_plotting_information(self):
        ...

        res = {}

        for i in range(len(self._sites_list)):
            site_entry = self._sites_list[i]

            site_plotting_information = {}

            site_plotting_information['u'] = []
            site_plotting_information['v'] = []
            site_plotting_information['q'] = []
            site_plotting_information['soc'] = []
            site_plotting_information['l_u'] = []
            site_plotting_information['l_v'] = []
            site_plotting_information['l_q'] = []

            site_plotting_information['u_lt'] = []
            site_plotting_information['v_lt'] = []
            site_plotting_information['q_lt'] = []
            site_plotting_information['soc_lt'] = []
            site_plotting_information['l_u_lt'] = []
            site_plotting_information['l_v_lt'] = []
            site_plotting_information['l_q_lt'] = []


            site_plotting_information['u_hht_to_hlt'] = []

            site_plotting_information['color'] = site_entry['color']

            for k in site_entry['rel_size_t_levels'].keys():
                if site_entry['rel_size_t_levels'][k] > 0:

                    if k == 'htht':
                        site_plotting_information['u'].append('u_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['v'].append('v_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['q'].append('q_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['soc'].append('soc_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['l_u'].append('l_u_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['l_v'].append('l_v_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['l_q'].append('l_q_h'+k+'_tes_site_'+site_entry['name'])

                    
                    if k == 'htlt':
                        site_plotting_information['u'].append('u_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['v_lt'].append('v_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['q_lt'].append('q_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['soc_lt'].append('soc_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['l_u'].append('l_u_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['l_v_lt'].append('l_v_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['l_q_lt'].append('l_q_h'+k+'_tes_site_'+site_entry['name'])
                    if k == 'ltlt':
                        site_plotting_information['u_lt'].append('u_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['v_lt'].append('v_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['q_lt'].append('q_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['soc_lt'].append('soc_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['l_u_lt'].append('l_u_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['l_v_lt'].append('l_v_h'+k+'_tes_site_'+site_entry['name'])
                        site_plotting_information['l_q_lt'].append('l_q_h'+k+'_tes_site_'+site_entry['name'])

            site_plotting_information['u_hht_to_hlt'].append('u_hht_to_hlt_tes_site_'+site_entry['name'])

            res[site_entry['name']] = site_plotting_information
        
        return res











    # def update_u_h(self, u_h_updated):
    #     if len(u_h_updated) != len(self._u_h):
    #         raise ValueError()        
    #     self._u_h = np.array(u_h_updated)        
    #     self.__compute_l_u_h()
        
    # def update_v_h(self, v_h_updated):
    #     if len(v_h_updated) != len(self._v_h):
    #         raise ValueError()        
    #     self._v_h = np.array(v_h_updated)        
    #     self.__compute_l_v_h()
        
    # def update_q_h(self, q_h_updated):
    #     if len(q_h_updated) != len(self._q_h):
    #         raise ValueError()        
    #     self._q_h = np.array(q_h_updated)        
    #     self.__compute_l_q_h()

    # def update_sos(self, sos_updated):
    #     if len(sos_updated) != len(self._sos):
    #         raise ValueError()        
    #     self._sos = np.array(sos_updated)        

    # def update_cap(self, cap_updated):
    #     self.num_test(cap_updated)
    #     self._cap = cap_updated      

    # def __compute_l_u_h(self):
    # # def get_charging_losses(u_h_tes, eta_chg):
    #     """
    #     Compute the charging losses for each time step.

    #     Parameters
    #     ----------
    #     u_h_tes : pandas Series
    #         Timeseries of energy supplied to storage [kWh].
    #     eta_chg : float
    #         Charging efficiency [-]. Values between 0 and 1.

    #     Returns
    #     -------
    #     l_u_h_tes : list
    #         Timeseries of energy lost due to charging [kWh].

    #     """
        
    #     l_u_h_tes = self._u_h*(1-self._eta_chg_dchg)
        
    #     self._l_u_h = np.array(l_u_h_tes)
        
    #     # l_u_h_tes = l_u_h_tes.tolist()
        
    #     # return l_u_h_tes
    
    # def __compute_l_v_h(self):
    # # def get_discharging_losses(v_h_tes, eta_dchg):
    #     """
    #     Compute the discharging losses for each time step.

    #     Parameters
    #     ----------
    #     v_h_tes : pandas Series
    #         Timeseries of energy supplied from storage [kWh].
    #     eta_chg : float
    #         Discharging efficiency [-]. Values between 0 and 1.

    #     Returns
    #     -------
    #     l_v_h_tes : list
    #         Timeseries of energy lost due to discharging [kWh].
        
    #     """
        
    #     l_v_h_tes = self._v_h*(1/self._eta_chg_dchg - 1)
        
    #     self._l_v_h = np.array(l_v_h_tes)
        
    #     # l_v_h_tes = l_v_h_tes.tolist()
        
    #     # return l_v_h_tes
    
    # def __compute_l_q_h(self):
    # # def get_storage_losses(q_h_tes, tes_gamma):
    #     """
    #     Compute the storage losses for each time step.

    #     Parameters
    #     ----------
    #     q_h_tes : pandas Series
    #         Stored heat in thermal energy storage [kWh].
    #     tes_gamma : float
    #         Loss rate: fraction of energy lost during one timestep [-]
    #         (e.g. during 1 hour).

    #     Returns
    #     -------
    #     l_q_h_tes : list
    #         Timeseries of energy lost during storage [kWh].

    #     """
    #     l_q_h_tes = self._q_h*self._gamma
        
    #     self._l_q_h = np.array(l_q_h_tes)
        
    #     # l_q_h_tes = l_q_h_tes.tolist()
        
    #     # return l_q_h_tes
    
    
    # def get_u_h(self):
    #     self.len_test(self._u_h)
    #     return self._u_h
    
    # def get_v_h(self):
    #     self.len_test(self._v_h)
    #     return self._v_h
    
    # def get_q_h(self):
    #     self.len_test(self._q_h)
    #     return self._q_h
    
    # def get_l_u_h(self):
    #     self.len_test(self._l_u_h)
    #     return self._l_u_h
    
    # def get_l_v_h(self):
    #     self.len_test(self._l_v_h)
    #     return self._l_v_h
    
    # def get_l_q_h(self):
    #     self.len_test(self._l_q_h)
    #     return self._l_q_h
    
    # def get_sos(self):
    #     self.len_test(self._sos)
    #     return self._sos
    
    # def get_eta_chg_dchg(self):
    #     self.num_test(self._eta_chg_dchg)
    #     return self._eta_chg_dchg
    
    # def get_gamma(self):
    #     self.num_test(self._gamma)
    #     return self._gamma
        
    # def get_cap(self):
    #     self.num_test(self._cap)
    #     return self._cap
    
    # def get_ic(self):
    #     self.num_test(self._ic)
    #     return self._ic




    # def initialise_q_h_0(self):
    #     self._q_h[0] = self.get_ic()*self.get_cap()
        
    # def update_u_h_i(self, i, val):
    #     self.num_test(val)
    #     self._u_h[i] = float(val)
        
    # def update_v_h_i(self, i, val):
    #     self.num_test(val)
    #     self._v_h[i] = float(val)
        
    # def update_q_h_i(self, i, val):
    #     self.num_test(val)
    #     self._q_h[i] = float(val)

