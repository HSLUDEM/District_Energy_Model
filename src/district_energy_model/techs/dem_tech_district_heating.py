# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:27:46 2024

@author: UeliSchilt
"""
import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore

NUM_DH_CATEGORIES = 3 # includes category "already built", does not include category "too expensive to build"

class DistrictHeating(TechCore):
    
    def __init__(self, tech_dict, com_nr, df_com_yr, df_meta, energy_demand):
    
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
        self.num_dh_categories = NUM_DH_CATEGORIES
        # Carrier types:
        self.output_carrier = 'heat'
        
        # Accounting:
        self._m_h = [] # heat import [kWh]
        self._v_h = [] # heat output [kWh]
        self._v_co2 = []

        self.update_district_heating_categories(df_com_yr, energy_demand, 'heat_energy_demand_estimate_kWh_combined')
        
    def update_district_heating_categories(self, df_com_yr, energy_demand, column_name_for_heat_demand_space_heating): #Update the district heating categories based on closeness data
        
        energy_to_power_conversion_factor = energy_demand.get_d_h().max() / energy_demand.get_d_h_yr()

        dh_already_existing_share_energy = (
            df_com_yr.loc[
                df_com_yr['Heating_System'] == 'v_h_dh', 
                column_name_for_heat_demand_space_heating
                ].sum()
            +df_com_yr.loc[
                df_com_yr['Heating_System'] == 'v_h_dh', 
                'dhw_estimation_kWh_combined'
                ].sum())
        dh_new_categories_energy = [(df_com_yr.loc[(df_com_yr['Heating_System'] != 'v_h_dh') & (df_com_yr['dh_distance_cat'] == i), 
                                                   column_name_for_heat_demand_space_heating].sum()
            +df_com_yr.loc[(df_com_yr['Heating_System'] != 'v_h_dh') & (df_com_yr['dh_distance_cat'] == i), 'dhw_estimation_kWh_combined'].sum())
                                        for i in range(self.num_dh_categories+1)]
        
        dh_already_existing_share_length = df_com_yr.loc[
            df_com_yr['Heating_System'] == 'v_h_dh', 
            'avg_dh_connection_distance'
            ].sum()
        dh_new_categories_length = [
            df_com_yr.loc[
                (df_com_yr['Heating_System'] != 'v_h_dh') 
                & (df_com_yr['dh_distance_cat'] == i), 
                'avg_dh_connection_distance'
                        ].sum()
                        for i in range(self.num_dh_categories+1)]
        
        kW_per_category = ([dh_already_existing_share_energy*energy_to_power_conversion_factor]
                           +[dh_new_categories_energy[i+1]*energy_to_power_conversion_factor 
                             for i in range(self.num_dh_categories)])
        
        if dh_already_existing_share_length > 0:
            length_per_kW_existing = [
                dh_already_existing_share_length/(dh_already_existing_share_energy*energy_to_power_conversion_factor)
                ]
        else:
            length_per_kW_existing = [0.0]
        
        length_per_kW_new = [
            dh_new_categories_length[i+1]/(dh_new_categories_energy[i+1]*energy_to_power_conversion_factor)
            for i in range(self.num_dh_categories)
            ]
        length_per_kW = length_per_kW_existing + length_per_kW_new
        
        # length_per_kW = ([dh_already_existing_share_length/(dh_already_existing_share_energy*energy_to_power_conversion_factor)]
        #                  +[dh_new_categories_length[i+1]/(dh_new_categories_energy[i+1]*energy_to_power_conversion_factor) 
        #                      for i in range(self.num_dh_categories)])

        if self._grid_kW_th_max != 'inf':
            dists_kw_per_category = np.array([0]+[sum(kW_per_category[:i+1]) for i in range(len(kW_per_category))])
            dists_kw_per_category[dists_kw_per_category > self._grid_kW_th_max] = self._grid_kW_th_max
            kW_per_category = dists_kw_per_category[1:]-dists_kw_per_category[:-1]

        self._investment_cost_grid_categories = []
        self._maintenance_cost_grid_categories = []
        self._kW_th_max_grid_categories = []
        
        if self._closeness_based_dh_expansion_cost:
            self.dhn_qty = len(kW_per_category)
            for i in range(self.dhn_qty):
                self._kW_th_max_grid_categories.append(kW_per_category[i])
                self._investment_cost_grid_categories.append(length_per_kW[i]*self._investment_dh_grid_per_m if i>0 else 0)
                self._maintenance_cost_grid_categories.append(length_per_kW[i]*self._maintenance_cost_dh_grid_per_m)
        else:
            self.dhn_qty = 2
            self._investment_cost_grid_categories = [0, self._capex]
            self._maintenance_cost_grid_categories = [self._maintenance_cost, self._maintenance_cost]
            self._kW_th_max_grid_categories = [kW_per_category[0], 
                                               self._grid_kW_th_max-kW_per_category[0] 
                                                    if self._grid_kW_th_max != 'inf' 
                                                    else self._grid_kW_th_max]

        
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the district heating technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        # Properties:
        self._demand_share_type = tech_dict['demand_share_type']
        self._demand_share_val = tech_dict['demand_share_val']
        self._import_kW_th_max = tech_dict['import_kW_th_max']
        self._grid_kW_th_max = tech_dict['grid_kW_th_max']
        self._lifetime = tech_dict['lifetime']
        self._tariff_CHFpkWh = tech_dict['tariff_CHFpkWh']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']

        self._investment_dh_grid_per_m = tech_dict['investment_dh_grid_per_m']
        self._maintenance_cost_dh_grid_per_m = tech_dict['maintenance_cost_dh_grid_per_m']
        self._closeness_based_dh_expansion_cost = tech_dict['closeness_based_dh_expansio_cost']
        self._capex = tech_dict['capex']
        self._maintenance_cost = tech_dict['maintenance_cost']

        self._source_import = tech_dict['heat_sources']['import']
        self._source_chp_gt = tech_dict['heat_sources']['chp_gt']
        self._source_steam_turbine = tech_dict['heat_sources']['steam_turbine']
        self._source_waste_to_energy =\
            tech_dict['heat_sources']['waste_to_energy']
        self._source_heat_pump_cp = tech_dict['heat_sources']['heat_pump_cp']
        self._source_heat_pump_cp_lt = tech_dict['heat_sources']['heat_pump_cp_lt']
        self._source_oil_boiler_cp = tech_dict['heat_sources']['oil_boiler_cp']
        self._source_electric_heater_cp = tech_dict['heat_sources']['electric_heater_cp']

        self._source_wood_boiler_cp = tech_dict['heat_sources']['wood_boiler_cp']
        self._source_gas_boiler_cp = tech_dict['heat_sources']['gas_boiler_cp']
        self._source_waste_heat = tech_dict['heat_sources']['waste_heat']

        self._source_biomass = tech_dict['heat_sources']['biomass']

        self._power_up_for_replacement = 0.0

        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['m_h_dh'] = self.get_m_h()
        df['v_h_dh'] = self.get_v_h()
        df['v_co2_dh'] = self.get_v_co2()
        
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
        
        self._m_h = self._m_h[:n_hours]
        self._v_h = self._v_h[:n_hours]
        self._v_co2 = self._v_co2[:n_hours]
    
    def compute_v_h(self, src_h_yr, d_h_profile):

        tmp_df = pd.DataFrame({'d_h_profile':d_h_profile})        
    
        tmp_df['v_h'] = tmp_df['d_h_profile']*src_h_yr
    
        self._v_h = np.array(tmp_df['v_h'])
        self._m_h = self._v_h.copy()
        
        self.__compute_v_co2()
        
    def update_m_h(self, m_h_updated):
        
        if len(m_h_updated) != len(self._m_h):
            raise ValueError("m_h_updated must have the same length as m_h!")
            
        self._m_h = np.array(m_h_updated)
        
        self.__compute_v_co2()
        
    def update_v_h(self, v_h_updated):
        
        if len(v_h_updated) != len(self._v_h):
            raise ValueError("v_h_updated must have the same length as v_h!")
            
        self._v_h = np.array(v_h_updated)
        
        self.__compute_v_co2()
        
    # def __compute_v_co2_init(self): # base scenario calculation
    #     self.len_test(self._v_h)        
    #     self._v_co2 = self._v_h*self.__tech_dict['co2_intensity']
        
    def __compute_v_co2(self):
        self.len_test(self._m_h)        
        self._v_co2 = self._m_h*self.__tech_dict['co2_intensity']
        
    def create_techs_dict(self, techs_dict, color):

        # techs_dict['district_heating'] = {
        #     'essentials':{
        #         'name':'District Heating',
        #         'color':color,
        #         'parent':'supply',
        #         'carrier':'heat',
        #         },
        #     'constraints':{
        #         'resource':'inf',
        #         'energy_cap_max':self._kW_th_max,
        #         'lifetime':self._lifetime
        #         },
        #     'costs':{
        #         'monetary':{
        #             'om_con':self._tariff_CHFpkWh,
        #             'interest_rate':self._interest_rate,
        #             },
        #         'emissions_co2':{
        #             'om_prod':self._co2_intensity,
        #             }
        #         }
        #     }
        
        # Hub, where all heat sources are fed into the grid:


        # self._investment_cost_grid_categories = [self._capex]
        # self._maintenance_cost_grid_categories = [self._maintenance_cost]
        # self._kW_th_max_grid_categories = [self._grid_kW_th_max]

        for i in range(len(self._investment_cost_grid_categories)):
            techs_dict['district_heating_hub_'+str(i)] = {
                'essentials':{
                    'name': 'District Heating Hub',
                    'parent':'conversion',
                    'carrier_in':'heat_dh',
                    'carrier_out':'heat',
                    },
                'constraints':{
                    'energy_cap_max':self._kW_th_max_grid_categories[i],
                    'energy_eff':1.0, # Here we could account for grid losses
                    'lifetime':self._lifetime,
                    # 'export_carrier': 'heat',
                    },
                'costs':{
                    'monetary':{
                        'om_con':0.0, # costs are reflected in supply techs
                        'interest_rate':self._interest_rate if self._kW_th_max_grid_categories[i]>0 else 0,
                        'energy_cap': self._investment_cost_grid_categories[i] if self._kW_th_max_grid_categories[i]>0 else 0,
                        'om_annual': self._maintenance_cost_grid_categories[i] if self._kW_th_max_grid_categories[i]>0 else 0,
                        # 'export': -1e-5,
                        },
                    } 
                }
        
        dh_techs_label_list = ['district_heating_hub_'+str(i) for i in range(len(self._investment_cost_grid_categories))]
        
        # Heat import from outside the district:
        if self._source_import == False:
            self._import_kW_th_max = 0.0
            
        techs_dict['district_heating_import'] = {
            'essentials':{
                'name':'District Heating Import',
                'color':color,
                'parent':'supply',
                'carrier':'heat_dhimp',
                },
            'constraints':{
                'resource':'inf',
                'energy_cap_max':self._import_kW_th_max,
                'lifetime':self._lifetime
                },
            'costs':{
                'monetary':{
                    'om_con':self._tariff_CHFpkWh,
                    'interest_rate':self._interest_rate,
                    },
                'emissions_co2':{
                    'om_prod':self._co2_intensity,
                    }
                }
            }
        dh_techs_label_list.append('district_heating_import')
            
        
        # ----------------------------------------
        # Conversion technologies for connected technologies:
            
        # District heat import (dhimp):
        # if self._source_import:
        techs_dict['conv_dhimp_dh'] = {
            'essentials':{
                'name':'Conversion: DHImp to DH',
                'parent':'conversion',
                'carrier_in':'heat_dhimp',
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
                } 
            }
        dh_techs_label_list.append('conv_dhimp_dh')
        
        # Combined heat and power gas turbine (chpgt):
        if self._source_chp_gt:
            techs_dict['conv_chpgt_dh'] = {
                'essentials':{
                    'name':'Conversion: CHPGT to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_chpgt',
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
                    } 
                }
            dh_techs_label_list.append('conv_chpgt_dh')
        
        # Steam turbine (st):
        if self._source_steam_turbine:
            techs_dict['conv_st_dh'] = {
                'essentials':{
                    'name':'Conversion: ST to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_st',
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
                    } 
                }
            dh_techs_label_list.append('conv_st_dh')

        # Waste-to-energy (wte):
        if self._source_waste_to_energy:
            techs_dict['conv_wte_dh'] = {
                'essentials':{
                    'name':'Conversion: WtE to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_wte',
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
                    } 
                }
            dh_techs_label_list.append('conv_wte_dh')
        
        # Heat pump central plant (hpcp):
        if self._source_heat_pump_cp:
            techs_dict['conv_hpcp_dh'] = {
                'essentials':{
                    'name':'Conversion: HPCP to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_hpcp',
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
                    } 
                }
            dh_techs_label_list.append('conv_hpcp_dh')

        # Heat pump central plant (from low T heat) (hpcplt):
        if self._source_heat_pump_cp_lt:
            techs_dict['conv_hpcplt_dh'] = {
                'essentials':{
                    'name':'Conversion: HPCPLT to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_hpcplt',
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
                    } 
                }
            dh_techs_label_list.append('conv_hpcplt_dh')

        # Oil boiler central plant (obcp):
        if self._source_oil_boiler_cp:
            techs_dict['conv_obcp_dh'] = {
                'essentials':{
                    'name':'Conversion: OBCP to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_obcp',
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
                    } 
                }
            dh_techs_label_list.append('conv_obcp_dh')

        # Electric heater central plant (ehcp):
        if self._source_electric_heater_cp:
            techs_dict['conv_ehcp_dh'] = {
                'essentials':{
                    'name':'Conversion: EHCP to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_ehcp',
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
                    } 
                }
            dh_techs_label_list.append('conv_ehcp_dh')

        # Wood boiler central plant (wbcp):
        if self._source_wood_boiler_cp:
            techs_dict['conv_wbcp_dh'] = {
                'essentials':{
                    'name':'Conversion: WBCP to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_wbcp',
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
                    } 
                }
            dh_techs_label_list.append('conv_wbcp_dh')

        # Waste heat (wh)
        if self._source_waste_heat:
            techs_dict['conv_wh_dh'] = {
                'essentials':{
                    'name':'Conversion: WH to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_wh',
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
                    } 
                }
            dh_techs_label_list.append('conv_wh_dh')


        # Gas boiler central plant (gbcp):
        if self._source_gas_boiler_cp:
            techs_dict['conv_gbcp_dh'] = {
                'essentials':{
                    'name':'Conversion: GBCP to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_gbcp',
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
                    } 
                }
            dh_techs_label_list.append('conv_gbcp_dh')

        # Biomass technologies (biomass : aguh, ...):
        if self._source_biomass:
            techs_dict['conv_biomass_dh'] = {
                'essentials':{
                    'name':'Conversion: Heat_biomass to DH',
                    'parent':'conversion',
                    'carrier_in':'heat_biomass',
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
                    } 
                }
            dh_techs_label_list.append('conv_biomass_dh')


        return techs_dict, dh_techs_label_list
    
    def get_dhn_qty(self):
        return self.dhn_qty
    
    def get_m_h(self):
        self.len_test(self._m_h)
        return self._m_h
        
    def get_v_h(self):
        self.len_test(self._v_h)
        return self._v_h
    
    def get_v_co2(self):
        self.len_test(self._v_co2)
        return self._v_co2
    
    def get_demand_share_type(self):
        return self._demand_share_type
    
    def get_demand_share_val(self):
        return self._demand_share_val
    
    def get_power_up_for_replacement(self):
        return self._power_up_for_replacement
    
    def set_power_up_for_replacement(self, value):
        self._power_up_for_replacement = value
