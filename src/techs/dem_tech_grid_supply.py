# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:00:15 2024

@author: UeliSchilt
"""

import numpy as np
import pandas as pd
import paths

from techs.dem_tech_core import TechCore

class GridSupply(TechCore):
    
    """
    Generation technology: grid supply.
    """
    
    def __init__(self, tech_dict):
        
        """
        Initialise grid supply parameters.
        
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
        self.output_carrier = 'electricity'
        
        # Accounting:
        self._m_e = []
        self._m_e_cbimport = []
        self._m_e_ch = []
        self._m_e_ch_hydro = []
        self._m_e_ch_nuclear = []
        self._m_e_ch_wind = []
        self._m_e_ch_biomass = []
        self._m_e_ch_other = []
        self._m_co2 = []
        
    def update_tech_properties(self, tech_dict):
        
        """
        Updates the grid supply technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        self._kW_max = tech_dict['kW_max'] # Max electric capacity
        self._lifetime = tech_dict['lifetime']
        self._tariff_CHFpkWh = tech_dict['tariff_CHFpkWh']
        self._interest_rate = tech_dict['interest_rate']
        self._co2_intensity = tech_dict['co2_intensity']
        
        # Update input dict:
        self.__tech_dict = tech_dict
        
    def update_df_results(self, df):
        
        df['m_e'] = self.get_m_e()
        df['m_e_cbimport'] = self.get_m_e_cbimport()
        df['m_e_ch'] = self.get_m_e_ch()
        df['m_e_ch_hydro'] = self.get_m_e_ch_hydro()
        df['m_e_ch_nuclear'] = self.get_m_e_ch_nuclear()
        df['m_e_ch_wind'] = self.get_m_e_ch_wind()
        df['m_e_ch_biomass'] = self.get_m_e_ch_biomass()
        df['m_e_ch_other'] = self.get_m_e_ch_other()
        df['m_co2'] = self.get_m_co2()
        
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
        
        self._m_e = self._m_e[:n_hours]
        self._m_e_cbimport = self._m_e_cbimport[:n_hours]
        self._m_e_ch = self._m_e_ch[:n_hours]
        self._m_e_ch_hydro = self._m_e_ch_hydro[:n_hours]
        self._m_e_ch_nuclear = self._m_e_ch_nuclear[:n_hours]
        self._m_e_ch_wind = self._m_e_ch_wind[:n_hours]
        self._m_e_ch_biomass = self._m_e_ch_biomass[:n_hours]
        self._m_e_ch_other = self._m_e_ch_other[:n_hours]
        self._m_co2 = self._m_co2[:n_hours]
        
    # def return_balance(self):
        
    #     # returns energy balance
        
    #     return {'input':{},
    #             'output':{'electricity':self.m_grid}
    #             }
    
    def compute_base_grid_import(self):
            # self, m_e
            # ):
        self.len_test(self._m_e)
        
        el_mix_path = paths.energy_mix_CH_dir + paths.electricity_mix_file
        el_mix_file = pd.read_feather(el_mix_path)
        
        el_gen_imp = pd.DataFrame(index = range(8760))
        el_gen_imp['Hydro'] = el_mix_file.iloc[:, :3].sum(axis = 1)
        el_gen_imp['Nuclear'] = el_mix_file.iloc[:, 3]
        el_gen_imp['Wind'] = el_mix_file.iloc[:, 5]
        el_gen_imp['Biomass'] = el_mix_file.iloc[:, 6]
        el_gen_imp['Other'] = el_mix_file.iloc[:, 7]
        el_gen_imp['Import'] = el_mix_file.iloc[:, -1]
        
        
        el_gen_imp_percentages = el_gen_imp.div(el_gen_imp.sum(axis = 1), axis = 0)
        
        m_e_mix = pd.DataFrame(index = range(8760))
        m_e_mix['m_e_ch_hydro'] = self._m_e * el_gen_imp_percentages['Hydro']
        m_e_mix['m_e_ch_nuclear'] = self._m_e * el_gen_imp_percentages['Nuclear']
        m_e_mix['m_e_ch_wind'] = self._m_e * el_gen_imp_percentages['Wind']
        m_e_mix['m_e_ch_biomass'] = self._m_e * el_gen_imp_percentages['Biomass']
        m_e_mix['m_e_ch_other'] = self._m_e * el_gen_imp_percentages['Other']
        m_e_mix['m_e_cbimport'] = self._m_e * el_gen_imp_percentages['Import']
        
        
        self._m_e_ch_hydro = np.array(m_e_mix['m_e_ch_hydro'])
        self._m_e_ch_nuclear = np.array(m_e_mix['m_e_ch_nuclear'])
        self._m_e_ch_wind = np.array(m_e_mix['m_e_ch_wind'])
        self._m_e_ch_biomass = np.array(m_e_mix['m_e_ch_biomass'])
        self._m_e_ch_other = np.array(m_e_mix['m_e_ch_other'])
        self._m_e_cbimport = np.array(m_e_mix['m_e_cbimport'])
        
        self._m_e_ch = self._m_e - self._m_e_cbimport
        
        self.__compute_m_co2()
        
        # return m_e_mix
    
    def __compute_m_co2(self):        
        self._m_co2 = self._m_e*self.__tech_dict['co2_intensity']
        # !!! THIS MUST BE SPLIT UP (cbimport vs national production)
        
    def compute_m_e_cbimport(self):
        self._m_e_cbimport = self._m_e - self._m_e_ch
        
    def add_m_e(self, m_e_new):
        self._m_e = np.array(m_e_new)
        
        self.__compute_m_co2()
        
    # def compute_m_e_diff(self, d_e_new, d_e_prev):
        
    #     df = pd.DataFrame()
        
    #     df['d_e_new'] = d_e_new
    #     df['d_e_prev'] = d_e_prev
    #     df['d_e_diff'] = df['d_e_new'] - df['d_e_prev']
    #     df['m_e_prev'] = self._m_e
    #     df['m_e_diff'] = 0
        
    #     df.loc[df['d_e_diff'] >= 0, 'm_e_diff'] = df['d_e_diff']
    #     df.loc[(df['d_e_diff'] < 0) & (df['d_e_diff'].abs() < df['m_e_prev']), 'm_e_diff'] = df['d_e_diff']
    #     df.loc[(df['d_e_diff'] < 0) & (df['d_e_diff'].abs() >= df['m_e_prev']), 'm_e_diff'] = -df['m_e_prev']
            
    #     return np.array(df['m_e_diff'])

    
    def update_m_e(self, m_e_updated):
        self._m_e = np.array(m_e_updated)
        
        df = pd.DataFrame()

        df['m_e'] = self._m_e
        df['m_e_ch'] = self._m_e_ch
        df['m_e_ch_hydro'] = self._m_e_ch_hydro
        df['m_e_ch_nuclear'] = self._m_e_ch_nuclear
        df['m_e_ch_wind'] = self._m_e_ch_wind
        df['m_e_ch_biomass'] = self._m_e_ch_biomass
        df['m_e_ch_other'] = self._m_e_ch_other
        df['m_e_cbimport'] = self._m_e_cbimport
        
        # Where m_e = 0, set all imports to 0:
        df.loc[df['m_e'] == 0, 'm_e_ch'] = 0
        df.loc[df['m_e'] == 0, 'm_e_ch_hydro'] = 0
        df.loc[df['m_e'] == 0, 'm_e_ch_nuclear'] = 0
        df.loc[df['m_e'] == 0, 'm_e_ch_wind'] = 0
        df.loc[df['m_e'] == 0, 'm_e_ch_biomass'] = 0
        df.loc[df['m_e'] == 0, 'm_e_ch_other'] = 0
        df.loc[df['m_e'] == 0, 'm_e_cbimport'] = 0
        
        # Update CH-import:
        # Where the ch-import is currently larger than the total import m_e, it is
        # downscaled to m_e (using a ratio) and all the ch-import shares are
        # adapted accordingly.
        df['tmp_m_e_ch_old'] = df['m_e_ch'].copy(deep = True)
        df['tmp_m_e_ratio'] = df['m_e']/df['m_e_ch']
        df.loc[df['m_e']==0,'tmp_m_e_ratio'] = 0
        
        #df_scen['tmp_m_e_ratio'].to_csv('tmp_m_e_ratio.csv')
        
        df.loc[df['tmp_m_e_ratio']<1,'m_e_ch'] = df['m_e_ch']*df['tmp_m_e_ratio']
        df.loc[df['tmp_m_e_ratio']<1,'m_e_ch_hydro'] = df['m_e_ch_hydro']*df['tmp_m_e_ratio']
        df.loc[df['tmp_m_e_ratio']<1,'m_e_ch_nuclear'] = df['m_e_ch_nuclear']*df['tmp_m_e_ratio']
        df.loc[df['tmp_m_e_ratio']<1,'m_e_ch_wind'] = df['m_e_ch_wind']*df['tmp_m_e_ratio']
        df.loc[df['tmp_m_e_ratio']<1,'m_e_ch_biomass'] = df['m_e_ch_biomass']*df['tmp_m_e_ratio']
        df.loc[df['tmp_m_e_ratio']<1,'m_e_ch_other'] = df['m_e_ch_other']*df['tmp_m_e_ratio']
        
        self._m_e_ch = np.array(df['m_e_ch'])
        self._m_e_ch_hydro = np.array(df['m_e_ch_hydro'])
        self._m_e_ch_nuclear = np.array(df['m_e_ch_nuclear'])
        self._m_e_ch_wind = np.array(df['m_e_ch_wind'])
        self._m_e_ch_biomass = np.array(df['m_e_ch_biomass'])
        self._m_e_ch_other = np.array(df['m_e_ch_other'])
        self._m_e_cbimport = np.array(df['m_e_cbimport'])
        
        # Test if all import values are >= 0:
        if np.all(self._m_e >= 0):
            pass
        else:
            msg = "Not all values are >= 0 in m_e."
            raise ValueError(msg)
        
        # Update cross-border (cb) import:
        self.compute_m_e_cbimport()
        # df['m_e_cbimport'] = df['m_e'] - df['m_e_ch']
        
        self.__compute_m_co2()
        
        del df
    
    # def update_m_e_cb_import(self, m_e_cb_import_updated):
    #     self._m_e_cb_import = np.array(m_e_cb_import_updated)        
    
    # def update_electricity_mix( # USED IN CALLIOPE
    #         m_e_new,
    #         m_e_old,
    #         m_e_ch_old,
    #         m_e_ch_hydro_old,
    #         m_e_ch_nuclear_old,
    #         m_e_ch_wind_old,
    #         m_e_ch_biomass_old,
    #         m_e_ch_other_old
    #         ):
    #     """
    #     Return updated electricity mix for imported electricity if the total
    #     import has been recalculated (e.g. after optimisation).

    #     Parameters
    #     ----------
    #     m_e_new : pandas dataseries
    #         Recalculated (i.e. new) total import.
    #     m_e_old : pandas dataseries
    #         Previous (i.e. old) total import.
    #     m_e_ch_old : pandas dataseries
    #         Previous national import.
    #     m_e_ch_hydro_old : pandas dataseries
    #         Previous national import supplied by hydro power.
    #     m_e_ch_nuclear_old : pandas dataseries
    #         Previous national import supplied by nuclear power.
    #     m_e_ch_wind : pandas dataseries
    #         Previous national import supplied by wind power.
    #     m_e_ch_biomass : pandas dataseries
    #         Previous national import supplied by biomass.
    #     m_e_ch_other : pandas dataseries
    #         Previous national import supplied by other plants.

    #     Returns
    #     -------
    #     df_mix_new : pandas dataframe
    #         Dataframe containing the recalculated electricity supply mix.
    #         Columns are named according to sources, e.g. 'm_e_cbimport',
    #         'm_e_ch', 'm_e_ch_hydro', etc...

    #     """
        
    #     # ---------------------------------------------------------------------
    #     # Create dataframe with previous (i.e. old) electricity mix. Later, the
    #     # updated electricity mix can be added.
            
    #     dict_mix = {
    #         'm_e_old':m_e_old,
    #         'm_e_ch_old':m_e_ch_old,
    #         'm_e_ch_hydro_old':m_e_ch_hydro_old,
    #         'm_e_ch_nuclear_old':m_e_ch_nuclear_old,
    #         'm_e_ch_wind_old':m_e_ch_wind_old,
    #         'm_e_ch_biomass_old':m_e_ch_biomass_old,
    #         'm_e_ch_other_old':m_e_ch_other_old,
    #         'm_e_new':m_e_new
    #         }
        
    #     df_mix = pd.DataFrame(dict_mix)

        
    #     # ---------------------------------------------------------------------
    #     # Update mix:
            
    #     # Case 1: m_e_new >= m_e_ch_old:
    #     df_mix.loc[df_mix['m_e_new'] >= df_mix['m_e_ch_old'], 'm_e_ch_new'] = df_mix['m_e_ch_old']
    #     df_mix.loc[df_mix['m_e_new'] >= df_mix['m_e_ch_old'], 'm_e_ch_hydro_new'] = df_mix['m_e_ch_hydro_old']
    #     df_mix.loc[df_mix['m_e_new'] >= df_mix['m_e_ch_old'], 'm_e_ch_nuclear_new'] = df_mix['m_e_ch_nuclear_old']
    #     df_mix.loc[df_mix['m_e_new'] >= df_mix['m_e_ch_old'], 'm_e_ch_wind_new'] = df_mix['m_e_ch_wind_old']
    #     df_mix.loc[df_mix['m_e_new'] >= df_mix['m_e_ch_old'], 'm_e_ch_biomass_new'] = df_mix['m_e_ch_biomass_old']
    #     df_mix.loc[df_mix['m_e_new'] >= df_mix['m_e_ch_old'], 'm_e_ch_other_new'] = df_mix['m_e_ch_other_old']
    #     df_mix.loc[df_mix['m_e_new'] >= df_mix['m_e_ch_old'], 'm_e_cbimport_new'] = (df_mix['m_e_new'] - df_mix['m_e_ch_old'])

    #     # Case 2: m_e_new < m_e_ch_old:
    #     df_mix.loc[df_mix['m_e_new'] < df_mix['m_e_ch_old'], 'm_e_ch_new'] = df_mix['m_e_new']
    #     # df_mix['m_e_ch_new'] = df_mix['m_e_new'] HERE IS THE MISTAKE!!!
        
    #     df_scaling = df_mix['m_e_ch_new']/df_mix['m_e_ch_old'] # scaling factor
        
    #     df_mix.loc[df_mix['m_e_new'] < df_mix['m_e_ch_old'], 'm_e_ch_hydro_new'] = df_mix['m_e_ch_hydro_old']*df_scaling
    #     df_mix.loc[df_mix['m_e_new'] < df_mix['m_e_ch_old'], 'm_e_ch_nuclear_new'] = df_mix['m_e_ch_nuclear_old']*df_scaling
    #     df_mix.loc[df_mix['m_e_new'] < df_mix['m_e_ch_old'], 'm_e_ch_wind_new'] = df_mix['m_e_ch_wind_old']*df_scaling
    #     df_mix.loc[df_mix['m_e_new'] < df_mix['m_e_ch_old'], 'm_e_ch_biomass_new'] = df_mix['m_e_ch_biomass_old']*df_scaling
    #     df_mix.loc[df_mix['m_e_new'] < df_mix['m_e_ch_old'], 'm_e_ch_other_new'] = df_mix['m_e_ch_other_old']*df_scaling
    #     df_mix.loc[df_mix['m_e_new'] < df_mix['m_e_ch_old'], 'm_e_cbimport_new'] = 0
        
 
    #     # check if the dataframe contains any NaNs:
    #     if df_mix.isnull().values.any():
    #         raise ValueError('There are NaN values in the dataframe.')
  
    #     # ---------------------------------------------------------------------
    #     # Write to dict:
            
    #     dict_mix_new = {
    #         'm_e_cbimport':df_mix['m_e_cbimport_new'],
    #         'm_e_ch':df_mix['m_e_ch_new'],
    #         'm_e_ch_hydro':df_mix['m_e_ch_hydro_new'],
    #         'm_e_ch_nuclear':df_mix['m_e_ch_nuclear_new'],
    #         'm_e_ch_wind':df_mix['m_e_ch_wind_new'],
    #         'm_e_ch_biomass':df_mix['m_e_ch_biomass_new'],
    #         'm_e_ch_other':df_mix['m_e_ch_other_new']
    #         }
        
    #     df_mix_new = pd.DataFrame(dict_mix_new)
        
    #     return df_mix_new
    
    def create_techs_dict(self, techs_dict, color):
            
        techs_dict['grid_supply'] = {
            'essentials':{
                'name':'Grid Supply',
                'color':color,
                'parent':'supply',
                'carrier':'electricity',
                },
            'constraints':{
                'resource':'inf',
                'energy_cap_max':self._kW_max,
                'lifetime':self._lifetime
                },
            'costs':{
                'monetary':{
                    # 'energy_cap':1000,
                    'om_con':self._tariff_CHFpkWh, # [CHF/kWh]
                    # 'om_prod':self.scen_techs['grid_supply']['tariff_CHFpkWh'], # [CHF/kWh]
                    'interest_rate':self._interest_rate
                    },
                'emissions_co2':{
                    'om_prod':self._co2_intensity
                    }
                }
            }
        
        return techs_dict
    
    def get_m_e(self):
        self.len_test(self._m_e)
        return self._m_e
    
    def get_m_e_cbimport(self):
        self.len_test(self._m_e_cbimport)
        return self._m_e_cbimport
    
    def get_m_e_ch(self):
        self.len_test(self._m_e_ch)
        return self._m_e_ch
    
    def get_m_e_ch_hydro(self):
        self.len_test(self._m_e_ch_hydro)
        return self._m_e_ch_hydro
    
    def get_m_e_ch_nuclear(self):
        self.len_test(self._m_e_ch_nuclear)
        return self._m_e_ch_nuclear
    
    def get_m_e_ch_wind(self):
        self.len_test(self._m_e_ch_wind)
        return self._m_e_ch_wind
    
    def get_m_e_ch_biomass(self):
        self.len_test(self._m_e_ch_biomass)
        return self._m_e_ch_biomass
    
    def get_m_e_ch_other(self):
        self.len_test(self._m_e_ch_other)
        return self._m_e_ch_other
    
    def get_m_co2(self):
        self.len_test(self._m_co2)
        return self._m_co2
    
    def update_m_e_i(self, i, val):
        self.num_test(val)
        self._m_e[i] = float(val)
