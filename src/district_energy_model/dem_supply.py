# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 16:28:04 2024

@author: Somesh
"""

import pandas as pd
import numpy as np
import datetime as dt

from district_energy_model.techs.dem_tech_core import TechCore
from district_energy_model import dem_constants as C

file_path = 'C:/Users/Somesh/OneDrive - Hochschule Luzern/Dokumente/Assessment/Biomasse/50_Code/district_energy_model-dem_somesh/data/biomass_data/'

class Supply(TechCore):
    
    def __init__(
            self,
            com_nr,
            meta_file,
            profiles_file,
            supply_tech_dict,
                 ):
        
        # Paths:
        self.com_nr = com_nr
        self.df_meta = meta_file
        self.profiles_file = profiles_file
        self.supply_tech_dict = supply_tech_dict
    
        # Properties:
        ...
        
        # Carrier types:
        ...
        
        # Hourly values:
        self._s_wet_bm = [] # wet biomass
        self._s_wd = [] # wood
        
        self._s_wet_bm_rem = []
        self._s_wd_rem = []
        
        # self._s_wd_import = []
        
        self._s_hydro = []
        
        # Imports:
        self._m_oil = [0.0]*8760
        self._m_gas = [0.0]*8760        
        self._m_wd = [0.0]*8760
        
        # Annual values:
        self._s_hydroL_yr = ...
        self._s_hydroS_yr = ...
        self._s_hydroP_yr = ...
        
    def update_df_results(self, df):
        
        df['s_wet_bm'] = self.get_s_wet_bm()
        df['s_wd'] = self.get_s_wd()
        df['s_wet_bm_rem'] = self.get_s_wet_bm_rem()
        df['s_wd_rem'] = self.get_s_wd_rem()
        # df['s_wd_import'] = self.get_s_wd_import()
        df['s_hydro'] = self.get_s_hydro()
        df['m_oil'] = self.get_m_oil()
        df['m_gas'] = self.get_m_gas()
        df['m_wd'] = self.get_m_wd()        
        
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
        
        self._s_wet_bm = self._s_wet_bm[:n_hours]
        self._s_wd = self._s_wd[:n_hours]
        
        self._s_wet_bm_rem = self._s_wet_bm_rem[:n_hours]
        self._s_wd_rem = self._s_wd_rem[:n_hours]
        
        # self._s_wd_import = self._s_wd_import[:n_hours]
        
        self._s_hydro = self._s_hydro[:n_hours]
        
        self._m_oil = self._m_oil[:n_hours]
        self._m_gas = self._m_gas[:n_hours]        
        self._m_wd = self._m_wd[:n_hours]
        
    def create_supply_dict_oil(
            self,
            techs_dict,
            # tech_dict,
            color, 
            energy_scaling_factor
            ):
        
        if self.supply_tech_dict['oil_import']:
            cap_max_ = 'inf'
        else:
            cap_max_ = 0.0

        # price_CHFpl=self._oil_price_CHFpl
        # hv_oil_MJpkg=self._hv_oil
        price_CHFpl=self.supply_tech_dict['oil_price_CHFpl']
        hv_oil_MJpkg=self.supply_tech_dict['hv_oil_MJpkg']
        hv_oil_MJpl = hv_oil_MJpkg*C.DENSITY_oil_kgpl # [MJ/l]
        hv_oil_kWhpl = hv_oil_MJpl*C.CONV_MJ_to_kWh
        price_CHFpkWh = price_CHFpl/hv_oil_kWhpl
        
        
        techs_dict['oil_supply'] = {
            'essentials':{
                'name':'Oil Supply',
                'color':color,
                'parent':'supply',
                'carrier':'oil',
                },
            'constraints':{
                # 'resource':'inf',
                'energy_cap_max':cap_max_ / energy_scaling_factor if cap_max_ != 'inf' else 'inf',
                # 'energy_cap_min':'inf', # ensures that supply is always large enough
                'lifetime':1000
                },
            'costs':{
                'monetary':{
                    'om_con':price_CHFpkWh *energy_scaling_factor,
                    'interest_rate':0.0
                    },
                'emissions_co2':{
                    'om_prod': self.supply_tech_dict['co2_content_oil']*energy_scaling_factor   # this is reflected in the emissions of oil_boiler
                    }
                }
            }
        
        return techs_dict
    
    def create_supply_dict_gas(
            self,
            techs_dict,
            color,
            energy_scaling_factor
            ):
        
        if self.supply_tech_dict['gas_import']:
            cap_max_ = 'inf'
        else:
            cap_max_ = 0.0
        
        techs_dict['gas_supply'] = {
            'essentials':{
                'name':'Gas Supply',
                'color':color,
                'parent':'supply',
                'carrier':'gas',
                },
            'constraints':{
                # 'resource':'inf',
                'energy_cap_max':cap_max_ / energy_scaling_factor if cap_max_ != 'inf' else 'inf',
                'lifetime':1000,
                },
            'costs':{
                'monetary':{
                    'om_con':self.supply_tech_dict['gas_price_CHFpkWh']*energy_scaling_factor,
                    'interest_rate':0.0
                    },
                'emissions_co2':{
                    'om_prod': self.supply_tech_dict['co2_content_gas']*energy_scaling_factor  # this is reflected in the emissions of gas_boiler
                    }
                }
            }
        
        return techs_dict

    def create_supply_dict_wet_biomass(self, techs_dict, energy_scaling_factor):
        
        sup_dict = {
            'essentials':{
                'name':'Wet Biomass Supply',
                'color': '#60804C',
                'parent':'supply',
                'carrier':'wet_biomass',
                },
            'constraints':{
                'lifetime': 1000
                },
            'costs':{
                'monetary':{
                    'om_con':0.001*energy_scaling_factor, # WHAT COST SHOULD WE ADD HERE?; currently minimum miniscule cost to favor truly free resources (e.g. PV)
                    'interest_rate':0.0
                    },
                'emissions_co2':{
                    'om_prod': self.supply_tech_dict['co2_content_wet_biomass']*energy_scaling_factor # this is reflected in the emissions of oil_boiler
                    }
                }
            }
        
        techs_dict['wet_biomass_supply'] = sup_dict
        return techs_dict
    
    def create_supply_dict_wood(self, techs_dict, energy_scaling_factor):
        
        price_CHFpkg=self.supply_tech_dict['wood_price_CHFpkg_local']
        hv_wood_MJpkg=self.supply_tech_dict['hv_wood_MJpkg']
        hv_wood_kWhpkg=hv_wood_MJpkg*C.CONV_MJ_to_kWh
        price_CHFpkWh = price_CHFpkg/hv_wood_kWhpkg
        
        sup_dict = {
            'essentials':{
                'name':'Wood Supply',
                'color': '#60804C',
                'parent':'supply',
                'carrier':'wood',
                },
            'constraints':{
                'lifetime': 1000
                },
            'costs':{
                'monetary':{
                    'om_con':price_CHFpkWh*energy_scaling_factor,
                    # 'om_con':0.00001, # add miniscule cost to avoid cycling of TES/BES within same timestep
                    'interest_rate':0.0
                    },
                'emissions_co2':{
                    'om_prod': self.supply_tech_dict['co2_content_local_wood']*energy_scaling_factor    # this is reflected in the emissions of the respective tech
                    }
                }
            }
        techs_dict['wood_supply'] = sup_dict
        return techs_dict
    
    def create_supply_dict_wood_import(self, techs_dict, energy_scaling_factor):
        
        if self.supply_tech_dict['wood_import']:
            cap_max_ = 'inf'
        else:
            cap_max_ = 0.0
        
        price_CHFpkg=self.supply_tech_dict['wood_price_CHFpkg_imported']
        hv_wood_MJpkg=self.supply_tech_dict['hv_wood_MJpkg']
        hv_wood_kWhpkg=hv_wood_MJpkg*C.CONV_MJ_to_kWh
        price_CHFpkWh = price_CHFpkg/hv_wood_kWhpkg
        
        sup_dict = {
            'essentials':{
                'name':'Wood Supply Import',
                'color': '#60804C',
                'parent':'supply',
                'carrier':'wood',
                },
            'constraints':{
                'lifetime': 1000,
                'energy_cap_max':cap_max_ / energy_scaling_factor if cap_max_ != 'inf' else 'inf',
                # 'resource':resource_,
                },
            'costs':{
                'monetary':{
                    'om_con':price_CHFpkWh * energy_scaling_factor,
                    # 'om_con':0.00001, # add miniscule cost to avoid cycling of TES/BES within same timestep
                    'interest_rate':0.0
                    },
                'emissions_co2':{
                    'om_prod': self.supply_tech_dict['co2_content_imported_wood']*energy_scaling_factor # this is reflected in the emissions of the respective tech
                    }
                }
            }
        techs_dict['wood_supply_import'] = sup_dict
        
        return techs_dict
    
    def create_supply_dict_msw( # municipal solid waste
            self,
            techs_dict,
            # tech_dict,
            color,
            energy_scaling_factor
            # resource,
            ):       
        
        # Price conversion from CHF/kg to CHF/kWh:
        hv_msw_MJpkg = self.supply_tech_dict['hv_msw_MJpkg']
        price_CHFpkg = self.supply_tech_dict['msw_price_CHFpkg']
        hv_msw_kWhpkg = hv_msw_MJpkg*C.CONV_MJ_to_kWh
        price_CHFpkWh = price_CHFpkg/hv_msw_kWhpkg
        


        # Compute resource per timestep from annual resource:
        
        resource_kg = self.supply_tech_dict['annual_msw_supply']

        if resource_kg == 'inf':
            resource = 'inf'
        else:
            CONV_MJ_to_kWh = 1000/3600 # Conversion from [MJ] to [kWh]        
            supp_MJ = resource_kg*hv_msw_MJpkg    
            resource = supp_MJ*CONV_MJ_to_kWh

        if resource == 'inf':
            resource_ts = 'inf'
        else:
            resource_ts = resource/8760
        
        techs_dict['msw_supply'] = {
            'essentials':{
                'name':'Municipal Solid Waste Supply',
                'color':color,
                'parent':'supply',
                'carrier':'munic_solid_waste',
                },
            'constraints':{
                'resource':resource_ts / energy_scaling_factor if resource_ts != 'inf' else 'inf', # [kWh] available energy per timestep
                'lifetime':1000
                },
            'costs':{
                'monetary':{
                    'om_con':price_CHFpkWh*energy_scaling_factor,
                    'interest_rate':0.0
                    },
                'emissions_co2':{
                    'om_prod': (
                        self.supply_tech_dict['co2_content_msw']
                        *self.supply_tech_dict['msw_share_fossile']
                        *energy_scaling_factor
                        ) # this is reflected in the emissions of oil_boiler
                    }
                }
            }
        
        return techs_dict
    
    def compute_s_h_wet_biomass(self):
        
        s_wet_bm_yr = self.df_meta.loc[self.df_meta['GGDENR'] == self.com_nr, 's_wet_bm']
        self._s_wet_bm = s_wet_bm_yr.values[0]*self.profiles_file['Wet_Biomass_Profile']
        self._s_wet_bm_rem = self._s_wet_bm
        
        return np.array(self._s_wet_bm)
    
    def compute_s_h_wood(self):
        
        s_wd_bm_yr = self.df_meta.loc[self.df_meta['GGDENR'] == self.com_nr, 's_wd_bm']
        self._s_wd = s_wd_bm_yr.values[0]*self.profiles_file['Woody_Biomass_Profile']
        self._s_wd_rem = self._s_wd
        
        return np.array(self._s_wd)
    
    def compute_s_h_wood_remaining(self, u_wd_wb):
        df = pd.DataFrame({
            's_wd_rem':list(self._s_wd_rem),
            'u_wd_wb':list(u_wd_wb),
            's_wd_imp':[0.0]*len(self._s_wd_rem)
            })
        
        #Update remaining wood potential:
        temp_wd_rem = (df['s_wd_rem'] - df['u_wd_wb']).to_frame('s_wd_rem')
        # print(temp_wd_rem)
        # df_base['s_wd_imp'] = 0
        df.loc[temp_wd_rem['s_wd_rem']<0, 's_wd_imp'] = -temp_wd_rem.loc[temp_wd_rem['s_wd_rem']<0, 's_wd_rem']
        temp_wd_rem.loc[temp_wd_rem['s_wd_rem']<0, 's_wd_rem'] = 0
        df['s_wd_rem'] = temp_wd_rem['s_wd_rem']
        
        
        self._s_wd_rem = np.array(df['s_wd_rem'])
        
        # TEMPORARY:
        # self._s_wd_import = np.array(df['s_wd_imp'])
    
    def compute_s_y_wet_biomass(self):
        return sum(self.compute_s_h_wet_biomass())
    
    def compute_s_y_wood(self):
        return sum(self.compute_s_h_wood())
    
    def __compute_s_hydro_yr(self):
        data = self.df_meta
        arg = data['GGDENR'] == self.com_nr
        
        s_hydroL_y = data.loc[arg, 'LocalHydroPotential_Laufkraftwerk']
        s_hydroS_y = data.loc[arg, 'LocalHydroPotential_Speicherkraftwerk']
        s_hydroP_y = data.loc[arg, 'LocalHydroPotential_Pumpspeicherkraftwerk']
        
        self._s_hydroL_yr = float(s_hydroL_y.iloc[0])
        self._s_hydroS_yr = float(s_hydroS_y.iloc[0])
        self._s_hydroP_yr = float(s_hydroP_y.iloc[0])
        
        # return s_hydroL_y, s_hydroS_y, s_hydroP_y
    
    def compute_s_hydro(self):
        """
        Compute annual and hourly hydro resources.

        Raises
        ------
        ValueError
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        self.__compute_s_hydro_yr()
        
        conds = [
            isinstance(self._s_hydroL_yr, float),
            isinstance(self._s_hydroS_yr, float),
            isinstance(self._s_hydroP_yr, float)
            ]
        
        if any(conds) == False:
            raise ValueError("Annual values must be calculated first!")
        
        s_hydroL_hr = (float(self._s_hydroL_yr) * self.profiles_file['Hydro_Lokal_Laufwasser_Profile']).reset_index(drop = True)
        s_hydroS_hr = (float(self._s_hydroS_yr) * self.profiles_file['Hydro_Lokal_Speicher_Profile']).reset_index(drop = True)
        s_hydroP_hr = (float(self._s_hydroP_yr) * self.profiles_file['Hydro_Lokal_Pumpspeicher_Profile']).reset_index(drop = True)
        
        s_hydro_hr = s_hydroL_hr + s_hydroS_hr + s_hydroP_hr
        
        self._s_hydro = np.array(s_hydro_hr*1e6)
        
        # return s_hydro_hr*1e6
        
    def update_s_wet_bm(self, s_wet_bm_updated):
        if len(s_wet_bm_updated) != len(self._s_wet_bm):
            raise ValueError()        
        self._s_wet_bm = np.array(s_wet_bm_updated)
        
    def update_s_wd(self, s_wd_updated):
        if len(s_wd_updated) != len(self._s_wd):
            raise ValueError()        
        self._s_wd = np.array(s_wd_updated)
        
    def update_s_wet_bm_rem(self, s_wet_bm_rem_updated):
        if len(s_wet_bm_rem_updated) != len(self._s_wet_bm_rem):
            raise ValueError()        
        self._s_wet_bm_rem = np.array(s_wet_bm_rem_updated)
        
    def update_s_wd_rem(self, s_wd_rem_updated):
        if len(s_wd_rem_updated) != len(self._s_wd_rem):
            raise ValueError()        
        self._s_wd_rem = np.array(s_wd_rem_updated)
        
    # def update_s_wd_import(self, s_wd_import_updated):
    #     if len(s_wd_import_updated) != len(self._s_wd_import):
    #         raise ValueError()        
    #     self._s_wd_import = np.array(s_wd_import_updated)
    
    def update_m_oil(self, m_oil_updated):
        if len(m_oil_updated) != len(self._m_oil):
            raise ValueError()        
        self._m_oil = np.array(m_oil_updated)
        
    def update_m_gas(self, m_gas_updated):
        if len(m_gas_updated) != len(self._m_gas):
            raise ValueError()        
        self._m_gas = np.array(m_gas_updated)
        
    def update_m_wd(self, m_wd_updated):
        if len(m_wd_updated) != len(self._m_wd):
            raise ValueError()        
        self._m_wd = np.array(m_wd_updated)
        
    def get_s_wet_bm(self):
        self.len_test(self._s_wet_bm)
        return np.array(self._s_wet_bm)
    
    def get_s_wd(self):
        self.len_test(self._s_wd)
        return np.array(self._s_wd)
    
    def get_s_wet_bm_rem(self):
        self.len_test(self._s_wet_bm_rem)
        return self._s_wet_bm_rem
    
    def get_s_wd_rem(self):
        self.len_test(self._s_wd_rem)
        return self._s_wd_rem

    def get_s_hydro(self):
        self.len_test(self._s_hydro)
        return self._s_hydro
    
    def get_s_hydroL_yr(self):
        self.len_test(self._s_hydroL_yr)
        return self._s_hydroL_yr
    
    def get_s_hydroS_yr(self):
        self.len_test(self._s_hydroS_yr)
        return self._s_hydroS_yr
    
    def get_s_hydroP_yr(self):
        self.len_test(self._s_hydroP_yr)
        return self._s_hydroP_yr
    
    def get_m_oil(self):
        self.len_test(self._m_oil)
        return self._m_oil
    
    def get_m_gas(self):
        self.len_test(self._m_gas)
        return self._m_gas
    
    def get_m_wd(self):
        self.len_test(self._m_wd)
        return self._m_wd


# sirnach_wet.to_frame(sirnach_wet, 'wet_biomass')
# sirnach_wood = get_s_h('wood', 4761, file_path)

# sirnach_wet.to_csv('wet_biomass_' + str(4761) + '.csv')
# sirnach_wood.to_csv('wood_' + str(4761) + '.csv')

    
# path_gw = 'C:/Users/Somesh/OneDrive - Hochschule Luzern/Dokumente/Assessment/Biomasse/50_Code/district_energy_model-dem_somesh/data/biomass_data/green_waste.csv'
# path_w = 'C:/Users/Somesh/OneDrive - Hochschule Luzern/Dokumente/Assessment/Biomasse/50_Code/district_energy_model-dem_somesh/data/biomass_data/wood.csv'
# path_m = 'C:/Users/Somesh/OneDrive - Hochschule Luzern/Dokumente/Assessment/Biomasse/50_Code/district_energy_model-dem_somesh/data/biomass_data/manure.csv'
# path_ss = 'C:/Users/Somesh/OneDrive - Hochschule Luzern/Dokumente/Assessment/Biomasse/50_Code/district_energy_model-dem_somesh/data/biomass_data/sewage_slidge.csv'

# gw = pd.read_csv(path_gw, index_col = 0)
# w = pd.read_csv(path_w, index_col = 0)
# m = pd.read_csv(path_m, index_col = 0)
# ss = pd.read_csv(path_ss, index_col = 0)

# print('Read')

# gw = gw*1000/3600
# w = w*1000/3600
# m = m * 1000/3600
# ss = ss*1000/3600

# print('Transform')

# gw.to_csv('green_waste_V2.csv')
# m.to_csv('manure_V2.csv')
# w.to_csv('wood_V2.csv')
# ss.to_csv('sewage_sludge_V2.csv')

# print('Save')




# def get_supply_from_monthly(com_nr, monthly_supply_file):
#     month_range = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
#     supply_time_series = []
    
#     for k, month in enumerate(month_range):
#         time_steps = month * 24
#         data = np.zeros(time_steps)
        
#         arg = np.where(monthly_supply_file['GMDNR'] == com_nr)[0]
#         data[:] = monthly_supply_file.iloc[arg, k + 2]/time_steps
#         # print(len(data))
#         supply_time_series += list(data)
    
#     # supply_time_series = pd.DataFrame(supply_time_series)
#     return supply_time_series


# path = 'C:/Users/Somesh/OneDrive - Hochschule Luzern/Dokumente/Assessment/Biomasse/50_Code/district_energy_model-dem_somesh/data/biomass_data/manure_monthly_data.csv'
# monthly_supply_file = pd.read_csv(path)
# # get_supply_from_monthly(10, monthly_supply_file)

# data = []
# index = []

# for k, nr in enumerate(monthly_supply_file['GMDNR']):
#     if k%100 == 0:
#         print(k)
#     supply = get_supply_from_monthly(nr, monthly_supply_file)
#     data.append(supply)
#     index.append(nr)
    
# data_1 = pd.DataFrame(data = data, index = index)


    

# path = "C:/Users/Somesh/OneDrive - Hochschule Luzern/Dokumente/Assessment/Biomasse/50_Code/district_energy_model-dem_somesh/data/biomass_data/Sustainable_Absolute_2014_per_Month.xlsx"

# biomass_data = pd.read_excel(path)

# wood_data = biomass_data.loc[:, ['GMDNR', 'Total Holz-Primärproduktion pro Jahr [GJ/a]Holz']]

# ss_data = biomass_data.loc[:, ['GMDNR', 'Sewage sludge \nPrimary energy [GJ/a]']]


# data_wood = []
# index_wood = []

# data_ss = []
# index_ss = []

# for k, nr in enumerate(wood_data['GMDNR']):
#     data_wood_nr = np.full(8760, wood_data.iloc[k, 1]/8760)
#     data_wood.append(list(data_wood_nr))
#     index_wood.append(nr)
    
#     data_ss_nr = np.full(8760, ss_data.iloc[k, 1]/8760)
#     data_ss.append(list(data_ss_nr))
#     index_ss.append(nr)

# data_wood_1 = pd.DataFrame(data = data_wood, index = index_wood)
# data_ss_1 = pd.DataFrame(data = data_ss, index = index_ss)

# arg_green_waste = ['January (monthly repartition following factor of greenwaste inputs in biogas plants)',
# 'February', 'March', 'April', 'May', 'June', 'July', 'August',
# 'September', 'October', 'November', 'December']

# arg_manure = ['January (monthly repartition following yearly pasture time distribution)',
# 'February.1', 'March.1', 'April.1', 'May.1', 'June.1', 'July.1',
# 'August.1', 'September.1', 'October.1', 'November.1', 'December.1']

# green_waste_data = pd.DataFrame(biomass_data['GMDNR'])
# manure_data = pd.DataFrame(biomass_data['GMDNR'])

# for arg in arg_green_waste:
#     print(arg)
#     if 'January' in arg:
#         green_waste_data.insert(len(green_waste_data.columns), 'January', biomass_data[arg])
#     else:
#         green_waste_data.insert(len(green_waste_data.columns), arg, biomass_data[arg])
    
# for arg in arg_manure:
#     print(arg)
#     if 'January' in arg:
#         manure_data.insert(len(manure_data.columns), 'January', biomass_data[arg])
#     else:
#         manure_data.insert(len(manure_data.columns), arg, biomass_data[arg])
        
# green_waste_data.to_csv('manure_monthly_data.csv')
# manure_data.to_csv('green_waste_monthly_data.csv')



