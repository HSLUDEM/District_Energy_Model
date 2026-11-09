# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 16:00:15 2024

@author: UeliSchilt
"""

import os

import numpy as np
import pandas as pd

from district_energy_model import dem_constants as C
from district_energy_model.techs.dem_tech_core import TechCore

class GridSupply(TechCore):
    
    """
    Generation technology: grid supply.
    """
    
    def __init__(self, paths, tech_dict, com_nr=None, simulation_year=None):
        
        """
        Initialise grid supply parameters.
        
        Parameters
        ----------
            
        tech_dict : dict
            Dictionary with technology parameters (subset of scen_techs).
        com_nr : int
            Municipality number; used in tariff_mode 'munic_file'.
        simulation_year : int
            Simulated year; used in tariff_mode 'munic_file'.
    
        Returns
        -------
        n/a
        """
        
        super().__init__(tech_dict)
        
        self.paths = paths
        self._com_nr = com_nr
        self._simulation_year = simulation_year
        
        # Initialize properties:
        self.update_tech_properties(tech_dict)
        self.init_timeseries()
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


        self._interest_rate = tech_dict['interest_rate']

        self._tariff_mode = tech_dict['tariff_mode']
        self._co2_intensity_mode = tech_dict['co2_intensity_mode']

        self._tariff_timeseries_filepath = tech_dict['tariff_timeseries_filepath']
        self._co2_intensity_timeseries_filepath = tech_dict['co2_intensity_timeseries_filepath']

        self._constant_tariff_CHFpkWh = tech_dict['constant_tariff_CHFpkWh']
        self._constant_co2_intensity = tech_dict['constant_co2_intensity']

        # The keys below are missing in older copies of inputs.py:
        self._tariff_munic_filepath = tech_dict.get('tariff_munic_filepath', '')
        self._tariff_year = tech_dict.get('tariff_year', 'auto')
        self._tariff_factor = tech_dict.get('tariff_factor', 1.0)

        if (
                isinstance(self._tariff_factor, bool)
                or not isinstance(self._tariff_factor, (int, float))
                or self._tariff_factor < 0
                ):
            raise ValueError(
                "grid_supply -> tariff_factor must be a number >= 0. "
                f"Selected value: {self._tariff_factor!r}."
                )

        self._capex = 0
        self._capex_one_to_one_replacement = 0
        self._maintenance_cost = 0
        
        self.__tech_dict = tech_dict

        # Scenarios update the properties after the initialisation:
        if hasattr(self, '_tariff_timeseries'):
            self._tariff_timeseries = self._compute_tariff_timeseries(
                len(self._tariff_timeseries)
                )
        
    def _read_tariff_munic_file(self):
        """
        Return the tariff of the municipality [CHF/kWh] from the file with one
        row per municipality (column GGDENR) and one column per year. If
        tariff_year is 'auto', the simulated year is used. If the simulated
        year is not in the file, the last year of the file is used.

        Returns
        -------
        float
            Tariff [CHF/kWh].
        """
        file_path = self._tariff_munic_filepath
        if file_path in ('', None):
            file_path = self.paths.electricity_dir + self.paths.electricity_tariff_file

        if not os.path.isfile(file_path):
            raise FileNotFoundError(
                f"Electricity tariff file not found: {file_path}. Add the file "
                "or set grid_supply -> tariff_mode to 'const' or 'timeseries'."
                )

        df_tariff = pd.read_feather(file_path).set_index('GGDENR')
        years = sorted(int(year) for year in df_tariff.columns)

        if self._com_nr not in df_tariff.index:
            raise ValueError(
                f"Municipality {self._com_nr} is not in the electricity tariff "
                f"file {file_path}."
                )

        if self._tariff_year == 'auto':
            year = self._simulation_year
            if year not in years:
                year = years[-1]
                print(
                    f"\nWARNING: Simulated year {self._simulation_year} is not "
                    f"in the electricity tariff file. The tariff of {year} is "
                    "used. Use grid_supply -> tariff_factor to scale it."
                    )
        elif self._tariff_year in years:
            year = self._tariff_year
        else:
            raise ValueError(
                f"grid_supply -> tariff_year must be 'auto' or a year of the "
                f"tariff file ({years[0]}-{years[-1]}). "
                f"Selected value: {self._tariff_year!r}."
                )

        return float(df_tariff.at[self._com_nr, str(year)])

    def _read_tariff_timeseries_file(self, n_hours):
        """Return the hourly tariff [CHF/kWh] from a feather or npy file."""
        file_path = self._tariff_timeseries_filepath
        if file_path.endswith(".feather"):
            timeseries = pd.read_feather(file_path).to_numpy()[:, 0]
        elif file_path.endswith(".npy"):
            timeseries = np.load(file_path)
        else:
            raise ValueError("Unknown file format for timeseries of electricity prices. Use feather or npy.")

        if len(timeseries) < n_hours:
            raise ValueError(
                f"The electricity tariff timeseries {file_path} has "
                f"{len(timeseries)} values, but {n_hours} are required."
                )

        return timeseries[:n_hours].astype(float)

    def _compute_tariff_timeseries(self, n_hours):
        """
        Compute the hourly tariff [CHF/kWh] according to tariff_mode. The
        tariff_factor is applied in all modes.

        Parameters
        ----------
        n_hours : int
            Number of hours.

        Returns
        -------
        numpy array
            Hourly tariff [CHF/kWh].
        """
        mode = self._tariff_mode

        if mode == 'file':
            print("\nWARNING: grid_supply -> tariff_mode 'file' is deprecated. Use 'timeseries'.")
            mode = 'timeseries'

        if mode == 'const':
            tariff = np.full(n_hours, float(self._constant_tariff_CHFpkWh))
        elif mode == 'munic_file':
            tariff = np.full(n_hours, self._read_tariff_munic_file())
        elif mode == 'timeseries':
            tariff = self._read_tariff_timeseries_file(n_hours)
        else:
            raise ValueError(
                "Unknown mode for timeseries of electricity prices. "
                "Use 'const', 'munic_file' or 'timeseries'."
                )

        return tariff*self._tariff_factor

    def init_timeseries(self):

        #Price

        n_hours = 365*24

        self._tariff_timeseries = self._compute_tariff_timeseries(n_hours)
        self._co2_intensity_timeseries = np.zeros(n_hours)

        #CO2 intensity

        if self._co2_intensity_mode == 'const':
            self._co2_intensity_timeseries = self._co2_intensity_timeseries + self._constant_co2_intensity
        elif self._co2_intensity_mode == 'file':
            if self._co2_intensity_timeseries_filepath.endswith(".feather"):
                self._co2_intensity_timeseries = pd.read_feather(self._co2_intensity_timeseries_filepath).to_numpy()[:n_hours, 0]
            elif self._co2_intensity_timeseries_filepath.endswith(".npy"):
                self._co2_intensity_timeseries = np.load(self._co2_intensity_timeseries_filepath)
            else:
                raise ValueError("Unknown file format for timeseries of electricity co2 intensity. Use feather or npy.")
        else:
            raise ValueError("Unknown mode for timeseries of electricity co2 intensity. Use 'const' or 'file'.")


        
        
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

        self._co2_intensity_timeseries = self._co2_intensity_timeseries[:n_hours]
        self._tariff_timeseries = self._tariff_timeseries[:n_hours]
        
    # def return_balance(self):
        
    #     # returns energy balance
        
    #     return {'input':{},
    #             'output':{'electricity':self.m_grid}
    #             }
    
    def compute_base_grid_import(self):
            # self, m_e
            # ):
        self.len_test(self._m_e)
        
        el_mix_path = self.paths.electricity_dir + self.paths.electricity_mix_file
        el_mix_file = pd.read_feather(el_mix_path)
        
        # el_gen_imp = pd.DataFrame(index = range(8760))
        # el_gen_imp['Hydro'] = el_mix_file.iloc[:, :3].sum(axis = 1)
        # el_gen_imp['Nuclear'] = el_mix_file.iloc[:, 3]
        # el_gen_imp['Wind'] = el_mix_file.iloc[:, 5]
        # el_gen_imp['Biomass'] = el_mix_file.iloc[:, 6]
        # el_gen_imp['Other'] = el_mix_file.iloc[:, 7]
        # el_gen_imp['Import'] = el_mix_file.iloc[:, -1]
        
        # =====================================================================
        el_gen_imp = pd.DataFrame(index=el_mix_file.index)
        
        el_gen_imp['Hydro'] = (
            el_mix_file[
                [
                    'Hydro Pumpspeicher',
                    'Hydro Laufwasser',
                    'Hydro Speicher'
                ]
            ]
            .sum(axis=1)
        )
        
        el_gen_imp['Nuclear'] = el_mix_file['Nuclear']
        el_gen_imp['Wind'] = el_mix_file['Wind']
        el_gen_imp['Biomass'] = el_mix_file['Biomass']
        el_gen_imp['Other'] = el_mix_file['Other']
        el_gen_imp['Import'] = el_mix_file['Import']
        # =====================================================================
        
        
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

    def compute_base_grid_import_without_split(self):
        """
        Set the grid import without splitting it by the national electricity
        mix. Used if national generation is modelled explicitly (national
        generation tech): the import m_e is then the remaining import that is
        not covered by national generation and is accounted as cross-border
        import (m_e_cbimport).
        """
        self.len_test(self._m_e)

        zeros = np.zeros(len(self._m_e))

        self._m_e_ch = zeros.copy()
        self._m_e_ch_hydro = zeros.copy()
        self._m_e_ch_nuclear = zeros.copy()
        self._m_e_ch_wind = zeros.copy()
        self._m_e_ch_biomass = zeros.copy()
        self._m_e_ch_other = zeros.copy()
        self._m_e_cbimport = np.array(self._m_e, dtype=float)

        self.__compute_m_co2()
    
    def __compute_m_co2(self):        
        self._m_co2 = self._m_e*self._co2_intensity_timeseries
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
        self._m_e = np.array(m_e_updated, dtype=float)

        # Set small negative values (numerical inaccuracies of the solver) to 0:
        self._m_e[(self._m_e < 0) & (self._m_e >= C.NEG_ACC)] = 0.0

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
            msg = f"Not all values are >= 0 in m_e (min. value: {self._m_e.min()})."
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
    
    def create_techs_dict(self, 
                          techs_dict, color, 
                          resource_tariff_timeseries,
                          resource_co2_intensity_timeseries,
                          energy_scaling_factor):
            
        techs_dict['grid_supply'] = {
            'essentials':{
                'name':'Grid Supply',
                'color':color,
                'parent':'supply',
                'carrier':'electricity',
                },
            'constraints':{
                'resource':'inf',
                'energy_cap_max':self._kW_max / energy_scaling_factor if self._kW_max != 'inf' else 'inf',
                'lifetime':self._lifetime
                },
            'costs':{
                'monetary':{
                    # 'energy_cap':1000,
                    'om_con': resource_tariff_timeseries, # [CHF/kWh]
                    # 'om_prod':self.scen_techs['grid_supply']['tariff_CHFpkWh'], # [CHF/kWh]
                    'interest_rate':self._interest_rate
                    },
                'emissions_co2':{
                    'om_prod': resource_co2_intensity_timeseries
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

    def set_m_e_ch_nuclear(self, val):
        self._m_e_ch_nuclear = val

    def set_m_e_ch(self, val):
        self._m_e_ch = val

    def get_energy_costs(self):
        return np.sum(np.array(self._m_e)*self._tariff_timeseries)

    def get_tariff_timeseries(self):
        return self._tariff_timeseries
    
    def get_co2_intensity_timeseries(self):
        return self._co2_intensity_timeseries