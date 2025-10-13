# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:29:27 2024

@author: UeliSchilt
"""
import numpy as np
from techs.dem_tech_core import TechCore

class ThermalEnergyStorage(TechCore):
    
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
        self._input_carrier = 'heat_tes' 
        self._output_carrier = 'heat_tes'
        
        # Accounting:
        self._u_h = [] # heat input [kWh]
        self._v_h = [] # heat output [kWh]
        self._q_h = [] # stored energy [kWh]
        self._l_u_h = [] # charging losses [kWh]
        self._l_v_h = [] # discharging losses [kWh]
        self._l_q_h = [] # storage losses [kWh]
        self._sos = [] # state of charge [-]
        
        
            
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
        self._gamma = tech_dict['tes_gamma']
        self._cap = tech_dict['capacity_kWh']
        self._force_cap_max = tech_dict['force_cap_max']
        self._ic = tech_dict['initial_charge']
        self._optimized_initial_charge = tech_dict['optimized_initial_charge']
        self._chg_dchg_per_cap_max = tech_dict['chg_dchg_per_cap_max']
        self._lifetime = tech_dict['lifetime']
        self._capex = tech_dict['capex']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        self._maintenance_cost = tech_dict['maintenance_cost']
        self._force_asynchronous_prod_con = tech_dict['force_asynchronous_prod_con']

        # self._connection_heat_pump = tech_dict['connections']['heat_pump']
        self._connection_district_heating_network =\
            tech_dict['connections']['district_heating_network']
        self._connection_district_heat_import =\
            tech_dict['connections']['district_heat_import']
        self._connection_chp_gt = tech_dict['connections']['chp_gt']
        self._connection_steam_turbine =\
            tech_dict['connections']['steam_turbine']
        self._connection_waste_to_energy =\
            tech_dict['connections']['waste_to_energy']
        self._connection_heat_pump_cp =\
            tech_dict['connections']['heat_pump_cp']
        self._connection_heat_pump_cp_lt =\
            tech_dict['connections']['heat_pump_cp_lt']
        self._connection_oil_boiler_cp =\
            tech_dict['connections']['oil_boiler_cp']
        self._connection_wood_boiler_cp =\
            tech_dict['connections']['wood_boiler_cp']
        self._connection_gas_boiler_cp =\
            tech_dict['connections']['gas_boiler_cp']
        self._connection_waste_heat =\
            tech_dict['connections']['waste_heat']
        self._connection_biomass =\
            tech_dict['connections']['biomass']

        # Tests:
        if self._ic > 1:
            printout = ('Error in tes input: '
                        'initial_charge cannot be larger than 1!\n'
                        f'Chosen initial_charge: {self.ic}'
                        )
            raise Exception(printout)
        if self._eta_chg_dchg > 1:
            printout = ('Error in tes input: '
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
            printout = ('Error in tes input: '
                        'loss factor (tes_gamma) cannot be larger than 1!'
                        )
            raise Exception(printout)
        
        # Update tech dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):

        df['u_h_tes'] = self.get_u_h() # heat input [kWh]
        df['v_h_tes'] = self.get_v_h() # heat output [kWh]
        df['q_h_tes'] = self.get_q_h() # stored energy [kWh]
        df['l_u_h_tes'] = self.get_l_u_h() # charging losses [kWh]
        df['l_v_h_tes'] = self.get_l_v_h() # discharging losses [kWh]
        df['l_q_h_tes'] = self.get_l_q_h() # storage losses [kWh]
        df['sos_tes'] = self.get_sos() # state of charge [-]
        
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
        
        self._u_h = self._u_h[:n_hours]
        self._v_h = self._v_h[:n_hours]
        self._q_h = self._q_h[:n_hours]
        self._l_u_h = self._l_u_h[:n_hours]
        self._l_v_h = self._l_v_h[:n_hours]
        self._l_q_h = self._l_q_h[:n_hours]
        self._sos = self._sos[:n_hours]
        
    def initialise_zero(self, n_days):
        n_hours = n_days*24
        
        init_vals = np.array([0.0]*n_hours)
        
        self._u_h = init_vals.copy() # heat input [kWh]
        self._v_h = init_vals.copy() # heat output [kWh]
        self._q_h = init_vals.copy() # stored energy [kWh]
        self._l_u_h = init_vals.copy() # charging losses [kWh]
        self._l_v_h = init_vals.copy() # discharging losses [kWh]
        self._l_q_h = init_vals.copy() # storage losses [kWh]
        self._sos = init_vals.copy() # state of charge [-]
        
    def initialise_q_h_0(self):
        self._q_h[0] = self.get_ic()*self.get_cap()
        
    def update_u_h_i(self, i, val):
        self.num_test(val)
        self._u_h[i] = float(val)
        
    def update_v_h_i(self, i, val):
        self.num_test(val)
        self._v_h[i] = float(val)
        
    def update_q_h_i(self, i, val):
        self.num_test(val)
        self._q_h[i] = float(val)
        
    def update_u_h(self, u_h_updated):
        if len(u_h_updated) != len(self._u_h):
            raise ValueError()        
        self._u_h = np.array(u_h_updated)        
        self.__compute_l_u_h()
        
    def update_v_h(self, v_h_updated):
        if len(v_h_updated) != len(self._v_h):
            raise ValueError()        
        self._v_h = np.array(v_h_updated)        
        self.__compute_l_v_h()
        
    def update_q_h(self, q_h_updated):
        if len(q_h_updated) != len(self._q_h):
            raise ValueError()        
        self._q_h = np.array(q_h_updated)        
        self.__compute_l_q_h()

    def update_sos(self, sos_updated):
        if len(sos_updated) != len(self._sos):
            raise ValueError()        
        self._sos = np.array(sos_updated)        

    def update_cap(self, cap_updated):
        self.num_test(cap_updated)
        self._cap = cap_updated      

    def __compute_l_u_h(self):
    # def get_charging_losses(u_h_tes, eta_chg):
        """
        Compute the charging losses for each time step.

        Parameters
        ----------
        u_h_tes : pandas Series
            Timeseries of energy supplied to storage [kWh].
        eta_chg : float
            Charging efficiency [-]. Values between 0 and 1.

        Returns
        -------
        l_u_h_tes : list
            Timeseries of energy lost due to charging [kWh].

        """
        
        l_u_h_tes = self._u_h*(1-self._eta_chg_dchg)
        
        self._l_u_h = np.array(l_u_h_tes)
        
        # l_u_h_tes = l_u_h_tes.tolist()
        
        # return l_u_h_tes
    
    def __compute_l_v_h(self):
    # def get_discharging_losses(v_h_tes, eta_dchg):
        """
        Compute the discharging losses for each time step.

        Parameters
        ----------
        v_h_tes : pandas Series
            Timeseries of energy supplied from storage [kWh].
        eta_chg : float
            Discharging efficiency [-]. Values between 0 and 1.

        Returns
        -------
        l_v_h_tes : list
            Timeseries of energy lost due to discharging [kWh].
        
        """
        
        l_v_h_tes = self._v_h*(1/self._eta_chg_dchg - 1)
        
        self._l_v_h = np.array(l_v_h_tes)
        
        # l_v_h_tes = l_v_h_tes.tolist()
        
        # return l_v_h_tes
    
    def __compute_l_q_h(self):
    # def get_storage_losses(q_h_tes, tes_gamma):
        """
        Compute the storage losses for each time step.

        Parameters
        ----------
        q_h_tes : pandas Series
            Stored heat in thermal energy storage [kWh].
        tes_gamma : float
            Loss rate: fraction of energy lost during one timestep [-]
            (e.g. during 1 hour).

        Returns
        -------
        l_q_h_tes : list
            Timeseries of energy lost during storage [kWh].

        """
        l_q_h_tes = self._q_h*self._gamma
        
        self._l_q_h = np.array(l_q_h_tes)
        
        # l_q_h_tes = l_q_h_tes.tolist()
        
        # return l_q_h_tes
    
    def create_techs_dict(self, techs_dict, color):
            
        techs_dict['tes'] = {}
            
        techs_dict['tes'] = {
            'essentials':{
                'name':'Thermal Energy Storage TES',
                'color':color,
                'parent':'storage',
                'carrier_in':self._input_carrier,
                'carrier_out':self._output_carrier,
                },
            'constraints':{
                'storage_initial':self._ic if not self._optimized_initial_charge else None,
                'storage_cap_max':self._cap,
                'storage_loss':self._gamma,
                'energy_eff': self._eta_chg_dchg,
                'energy_cap_per_storage_cap_max': self._chg_dchg_per_cap_max,
                'lifetime':self._lifetime,
                # 'force_asynchronous_prod_con':True,
                },
            'costs':{
                'monetary':{
                    # 'om_annual':0.0, # !!!TEMPORARY - KOSTEN MÜSSEN DYNAMISCH HINZUGEFÜGT WERDEN!!!
                    'om_prod':0.0000, # [CHF/kWh_dchg] artificial cost per discharged kWh; used to avoid cycling within timestep
                    'storage_cap':self._capex,
                    'om_annual': self._maintenance_cost,
                    'interest_rate':self._interest_rate
                    },
                'emissions_co2':{
                    'om_prod':self._co2_intensity + 0.0000
                    }
                }
            }
        if self._force_asynchronous_prod_con:
            techs_dict['tes']['constraints']['force_asynchronous_prod_con']= True

        tes_techs_label_list = ['tes']
        
        if self._force_cap_max:
            techs_dict['tes']['constraints']['storage_cap_equals'] = self._cap
        
        # # ----------------------------------------
        # # Conversion technologies for connection to decentralised heat pumps:
        
        # if self._connection_heat_pump:
        #     # Conversion from heat pumps to TES (one-way):
        #     techs_dict['conv_hp_tes'] = {
        #         'essentials':{
        #             'name':'Conversion: HP to TES',
        #             'parent':'conversion',
        #             'carrier_in':'heat_hp',
        #             'carrier_out':'heat_tes',
        #             },
        #         'constraints':{
        #             'energy_cap_max':'inf',
        #             'energy_eff':1.0, # Here we could account for transmission losses
        #             'lifetime':self._lifetime,
        #             },
        #         'costs':{
        #             'monetary':{
        #                 'om_con': 0.0, # costs are reflected in supply techs
        #                 'interest_rate':0.0,
        #                 },
        #             'emissions_co2':{
        #                 'om_prod':0.0, # emissions are reflected in supply techs
        #                 }
        #             } 
        #         }
        #     tes_techs_label_list.append('conv_hp_tes') 
            
        #     # From TES to decentralised heat pump hub (one-way; virtual hub):
        #     techs_dict['conv_tes_hp'] = {
        #         'essentials':{
        #             'name':'Conversion: TES to HP',
        #             'parent':'conversion',
        #             'carrier_in':'heat_tes',
        #             'carrier_out':'heat_hp',
        #             },
        #         'constraints':{
        #             'energy_cap_max':'inf',
        #             'energy_eff':1.0, # Here we could account for transmission losses
        #             'lifetime':self._lifetime,
        #             },
        #         'costs':{
        #             'monetary':{
        #                 'om_con': 0.0, # costs are reflected in supply techs
        #                 'interest_rate':0.0,
        #                 },
        #             'emissions_co2':{
        #                 'om_prod':0.0, # emissions are reflected in supply techs
        #                 }
        #             } 
        #         }
        #     tes_techs_label_list.append('conv_tes_hp')
        
        # ----------------------------------------
        # Conversion technologies for connected technologies in district heating network:
            
        # From TES to district heating network (one-way connection):
        if self._connection_district_heating_network:
            techs_dict['conv_tes_dh'] = {
                'essentials':{
                    'name':'Conversion: TES to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_tes',
                    'carrier_out':'heat_dh',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_tes_dh')
            
        # District heat import (dhimp):
        if self._connection_district_heat_import:
            techs_dict['conv_dhimp_tes'] = {
                'essentials':{
                    'name':'Conversion: DHImp to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_dhimp',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_dhimp_tes')
        
        # Combined heat and power gas turbine (chpgt):
        if self._connection_chp_gt:
            techs_dict['conv_chpgt_tes'] = {
                'essentials':{
                    'name':'Conversion: CHPGT to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_chpgt',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_chpgt_tes')
        
        # Steam turbine (st):
        if self._connection_steam_turbine:
            techs_dict['conv_st_tes'] = {
                'essentials':{
                    'name':'Conversion: ST to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_st',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_st_tes')

        # Waste-to-energy (wte):
        if self._connection_waste_to_energy:
            techs_dict['conv_wte_tes'] = {
                'essentials':{
                    'name':'Conversion: WtE to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_wte',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_wte_tes')
        
        # Heat pump central plant (hpcp):
        if self._connection_heat_pump_cp:
            techs_dict['conv_hpcp_tes'] = {
                'essentials':{
                    'name':'Conversion: HPCP to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_hpcp',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_hpcp_tes')

        # Heat pump central plant, from low T heat (hpcplt):
        if self._connection_heat_pump_cp_lt:
            techs_dict['conv_hpcplt_tes'] = {
                'essentials':{
                    'name':'Conversion: HPCPLT to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_hpcplt',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_hpcplt_tes')

        # Oil boiler central plant (obcp):
        if self._connection_oil_boiler_cp:
            techs_dict['conv_obcp_tes'] = {
                'essentials':{
                    'name':'Conversion: OBCP to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_obcp',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_obcp_tes')

        # Oil boiler central plant (obcp):
        if self._connection_biomass:
            techs_dict['conv_biomass_tes'] = {
                'essentials':{
                    'name':'Conversion: Heat_biomass to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_biomass',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_biomass_tes')


        # Wood boiler central plant (wbcp):
        if self._connection_wood_boiler_cp:
            techs_dict['conv_wbcp_tes'] = {
                'essentials':{
                    'name':'Conversion: WBCP to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_wbcp',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_wbcp_tes')

        # Waste heat (wh):
        if self._connection_waste_heat:
            techs_dict['conv_wh_tes'] = {
                'essentials':{
                    'name':'Conversion: WH to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_wh',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_wh_tes')

        # Gas boiler central plant (gbcp):
        if self._connection_gas_boiler_cp:
            techs_dict['conv_gbcp_tes'] = {
                'essentials':{
                    'name':'Conversion: GBCP to TES',
                    'parent':'conversion',
                    'carrier_in':'heat_gbcp',
                    'carrier_out':'heat_tes',
                    },
                'constraints':{
                    'energy_cap_max':'inf',
                    'energy_eff':1.0, # Here we could account for transmission losses
                    'lifetime':self._lifetime,
                    },
                'costs':{
                    'monetary':{
                        'om_con': 0.0, # costs are reflected in supply techs
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':0.0, # emissions are reflected in supply techs
                        }
                    } 
                }
            tes_techs_label_list.append('conv_gbcp_tes')



        return techs_dict, tes_techs_label_list
    
    def get_u_h(self):
        self.len_test(self._u_h)
        return self._u_h
    
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
    
    def get_q_h(self):
        self.len_test(self._q_h)
        return self._q_h
    
    def get_l_u_h(self):
        self.len_test(self._l_u_h)
        return self._l_u_h
    
    def get_l_v_h(self):
        self.len_test(self._l_v_h)
        return self._l_v_h
    
    def get_l_q_h(self):
        self.len_test(self._l_q_h)
        return self._l_q_h
    
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
