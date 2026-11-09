# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 09:00:00 2026

@author: UeliSchilt
"""

"""
National generation: hourly profiles of national generators (e.g. nuclear,
hydro, alpine PV, gas plant) allocated to a municipality in a pre-processing
step (e.g. from the output of a national-scale model such as OREES).

Each generator is an upper bound: in each hour, the municipality can use up to
its allocated share. The part that is not used is reported as curtailment.
National generation cannot be exported, and it is used before cross-border
import, i.e. electricity is only imported from the grid if all national
generation is used (see dem_calliope_cc.py).
"""

import os
import re

import numpy as np
import pandas as pd

from district_energy_model.techs.dem_tech_core import TechCore

# Keys of each generator in scen_techs['national_generation']['generators']:
GENERATOR_KEYS = ('file', 'cost_CHFpkWh', 'co2_intensity', 'local_counterparts')

# Value of cost_CHFpkWh for using the tariff of grid_supply (hourly, incl.
# tariff_factor). This is the default if cost_CHFpkWh is not set:
COST_GRID_TARIFF = 'grid_tariff'

# Local technologies that can be declared as counterparts of a national
# generator (i.e. their generation is part of the national profile).
# 'hydro_power_storage' is the storage and pumped-storage part of hydro_power
# (the run-of-river part remains local); it is checked against the local
# potentials of the municipality (see check_hydro_storage_counterpart):
SUPPORTED_COUNTERPARTS = ('hydro_power', 'hydro_power_storage', 'wind_power', 'solar_pvalpine')

N_HOURS_PROFILE = 8760


def is_deployed(scen_techs):
    """
    Return True if national generation is deployed. Input files without the
    key 'national_generation' (e.g. older copies of inputs.py) are treated as
    not deployed.
    """
    tech_dict = scen_techs.get('national_generation')
    return bool(tech_dict) and bool(tech_dict['deployment'])


def get_local_counterparts(scen_techs):
    """
    Return the local technologies that are replaced by national generators.

    Parameters
    ----------
    scen_techs : dict
        Dictionary containing info about technologies.

    Returns
    -------
    list of str
        Names of local technologies (keys of scen_techs). Empty if national
        generation is not deployed.
    """
    if not is_deployed(scen_techs):
        return []
    counterparts = []
    for gen_dict in scen_techs['national_generation']['generators'].values():
        for tech in gen_dict.get('local_counterparts', []):
            if tech not in counterparts:
                counterparts.append(tech)
    return counterparts


def check_national_generation_config(scen_techs):
    """
    Check the configuration of national generation and its consistency with
    the other technologies and scenarios. Raises a ValueError if:
        - a national generator and its local counterpart are both switched on
          (the same generation would be counted twice),
        - the nuclear phase-out scenario is activated (the phase-out must be
          part of the national profiles).

    Parameters
    ----------
    scen_techs : dict
        Dictionary containing info about technologies.

    Returns
    -------
    None
    """
    if not is_deployed(scen_techs):
        return

    tech_dict = scen_techs['national_generation']
    validate_tech_dict(tech_dict)

    conflicts = []
    for gen_name, gen_dict in tech_dict['generators'].items():
        for tech in gen_dict['local_counterparts']:
            if tech == 'hydro_power_storage':
                continue # requires municipality data; see check_hydro_storage_counterpart
            if scen_techs[tech]['deployment']:
                conflicts.append((gen_name, tech))

    if conflicts:
        lines = [
            f"  - national generator '{gen}' and local technology '{tech}' "
            f"(national_generation -> generators -> {gen} -> local_counterparts "
            f"contains '{tech}', and {tech} -> deployment = True)"
            for gen, tech in conflicts
            ]
        local_techs = sorted(set(tech for _, tech in conflicts))
        raise ValueError(
            "National and local generation of the same type are both switched on:\n"
            + "\n".join(lines) + "\n"
            "The local generation is already part of the national profile and "
            "would be counted twice. Switch one of them off and rerun the model:\n"
            "  - set 'deployment: false' for "
            + ", ".join(f"'{t}'" for t in local_techs) + ", or\n"
            "  - remove the national generator(s) from "
            "national_generation -> generators."
            )

    if scen_techs['scenarios']['nuclear_phaseout']:
        raise ValueError(
            "The scenario 'nuclear_phaseout' cannot be combined with national "
            "generation (national_generation -> deployment = True). The "
            "nuclear phase-out must be included in the national generation "
            "profiles. Set scenarios -> nuclear_phaseout = False and rerun "
            "the model."
            )


def check_hydro_storage_counterpart(scen_techs, df_meta, com_nr, com_name):
    """
    Raise a ValueError if a national generator contains the storage and
    pumped-storage hydro power (local counterpart 'hydro_power_storage') while
    the local hydro power of the municipality also contains storage or
    pumped-storage potential (counted twice). The run-of-river part of
    hydro_power remains local and is not affected.

    Local hydro power is part of the run if hydro_power is deployed, or in a
    simulation run (without optimisation), where the existing generation of
    switched-off techs is kept, unless 'hydro_power' is a local counterpart
    itself (then the local hydro power is removed completely).

    Parameters
    ----------
    scen_techs : dict
        Dictionary containing info about technologies.
    df_meta : pandas dataframe
        Meta data (one row per municipality) incl. the local hydro potentials.
    com_nr : int
        Municipality number.
    com_name : str
        Name of municipality (for the error message).

    Returns
    -------
    None
    """
    if not is_deployed(scen_techs):
        return

    generators = scen_techs['national_generation']['generators']
    gens = [
        g for g, gen_dict in generators.items()
        if 'hydro_power_storage' in gen_dict['local_counterparts']
        ]
    if not gens or 'hydro_power' in get_local_counterparts(scen_techs):
        return

    row = df_meta.loc[df_meta['GGDENR'] == com_nr]
    s_storage = float(row['LocalHydroPotential_Speicherkraftwerk'].iloc[0]) # [GWh/a]
    s_pumped = float(row['LocalHydroPotential_Pumpspeicherkraftwerk'].iloc[0]) # [GWh/a]
    if s_storage + s_pumped <= 0:
        return

    deployed = scen_techs['hydro_power']['deployment']
    optimisation = scen_techs['optimisation']['enabled']
    if not deployed and optimisation:
        return # local hydro power is removed from the optimisation

    if deployed:
        reason = "hydro_power -> deployment = True"
    else:
        reason = (
            "hydro_power -> deployment = False, but in simulation runs "
            "(optimisation -> enabled = False) the existing generation of "
            "switched-off technologies is kept"
            )

    raise ValueError(
        f"National generator(s) {gens} contain the storage and pumped-storage "
        "hydro power (local_counterparts contains 'hydro_power_storage'), but "
        f"the local hydro power of {com_name} also contains storage or "
        f"pumped-storage potential ({s_storage} GWh/a storage, {s_pumped} GWh/a "
        f"pumped storage) and is part of this run ({reason}). This generation "
        "would be counted twice. Resolve it in one of the following ways and "
        "rerun the model:\n"
        "  - use input data in which the local storage and pumped-storage "
        "potentials are 0 (meta data columns "
        "LocalHydroPotential_Speicherkraftwerk and "
        "LocalHydroPotential_Pumpspeicherkraftwerk), as in the OREES data; "
        "the run-of-river potential remains local, or\n"
        "  - set 'deployment: false' for 'hydro_power' and add 'hydro_power' "
        "to local_counterparts (this also removes the local run-of-river "
        "hydro power), or\n"
        "  - remove 'hydro_power_storage' from local_counterparts if the "
        "national profile does not contain the local storage hydro power."
        )


def validate_tech_dict(tech_dict):
    """
    Check the national generation entries in scen_techs. Raises a ValueError
    if an entry is invalid.
    """
    for key in ('export_big_M_kWh', 'import_big_M_kWh'):
        big_M = tech_dict[key]
        if big_M != 'auto' and (
                isinstance(big_M, bool)
                or not isinstance(big_M, (int, float))
                or big_M <= 0
                ):
            raise ValueError(
                f"national_generation -> {key} must be 'auto' or a "
                f"positive number. Selected value: {big_M!r}."
                )

    generators = tech_dict['generators']
    if not isinstance(generators, dict) or len(generators) == 0:
        raise ValueError(
            "national_generation -> generators must contain at least one "
            "generator if national_generation -> deployment = True."
            )

    for gen_name, gen_dict in generators.items():
        context = f"national_generation -> generators -> {gen_name}"

        if not re.fullmatch(r'[a-z][a-z0-9_]*', str(gen_name)):
            raise ValueError(
                f"{context}: invalid generator name. Use lower-case letters, "
                "digits and underscores only, starting with a letter "
                "(e.g. 'alpine_pv')."
                )
        if str(gen_name).startswith(('pot_', 'curt_')) or gen_name in ('pot', 'curt'):
            raise ValueError(
                f"{context}: generator names must not start with 'pot' or "
                "'curt' (reserved for result columns)."
                )
        if not isinstance(gen_dict, dict):
            raise ValueError(f"{context}: must be a dictionary with the keys {list(GENERATOR_KEYS)}.")

        unknown = sorted(set(gen_dict) - set(GENERATOR_KEYS))
        if unknown:
            raise ValueError(
                f"{context}: unknown key(s) {unknown}. "
                f"Allowed keys: {list(GENERATOR_KEYS)}."
                )
        missing = [
            k for k in GENERATOR_KEYS
            if k not in gen_dict and k != 'cost_CHFpkWh'
            ]
        if missing:
            raise ValueError(f"{context}: missing key(s) {missing}.")

        for key in ('cost_CHFpkWh', 'co2_intensity'):
            val = gen_dict.get(key, COST_GRID_TARIFF)
            if key == 'cost_CHFpkWh' and val == COST_GRID_TARIFF:
                continue
            if isinstance(val, bool) or not isinstance(val, (int, float)) or val < 0:
                raise ValueError(
                    f"{context} -> {key} must be a number >= 0"
                    + (f" or '{COST_GRID_TARIFF}'" if key == 'cost_CHFpkWh' else "")
                    + f". Selected value: {val!r}."
                    )

        counterparts = gen_dict['local_counterparts']
        if not isinstance(counterparts, (list, tuple)):
            raise ValueError(
                f"{context} -> local_counterparts must be a list (e.g. "
                "['hydro_power'] or [])."
                )
        unsupported = sorted(set(counterparts) - set(SUPPORTED_COUNTERPARTS))
        if unsupported:
            raise ValueError(
                f"{context} -> local_counterparts: unsupported technologies "
                f"{unsupported}. Supported: {list(SUPPORTED_COUNTERPARTS)}."
                )


def resolve_data_dir(data_dir, root_dir, default_dir):
    """
    Return the directory of the national generation profiles. An empty
    data_dir refers to the default directory, a relative data_dir is relative
    to the root directory.
    """
    if data_dir in ('', None):
        return default_dir
    if os.path.isabs(data_dir):
        return data_dir
    return os.path.join(root_dir, data_dir)


def load_profile(file_path, com_nr, com_percent_2):
    """
    Read the hourly profile of one national generator allocated to the
    selected municipality or custom district.

    Parameters
    ----------
    file_path : str
        Path to profile file (.feather or .csv). Rows: 8760 hours. Columns:
        municipality numbers (BFS numbers). Values: energy [kWh] per hour.
    com_nr : int
        Municipality number.
    com_percent_2 : pandas Series or list
        Custom districts: share of each municipality (index: municipality
        number) that belongs to the district. Empty list otherwise.

    Returns
    -------
    profile : numpy array
        Hourly profile [kWh].
    missing : list
        Municipality numbers without a column in the file (their profile is
        set to 0).
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"National generation profile not found: {file_path}"
            )

    if file_path.endswith('.feather'):
        df = pd.read_feather(file_path)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
        df = df.loc[:, ~df.columns.astype(str).str.startswith('Unnamed')]
    else:
        raise ValueError(
            f"Unknown file format of national generation profile: {file_path}. "
            "Use .feather or .csv."
            )

    df.columns = [str(c) for c in df.columns]

    if len(df) != N_HOURS_PROFILE:
        raise ValueError(
            f"National generation profile {file_path} must have "
            f"{N_HOURS_PROFILE} rows (hours). Number of rows: {len(df)}."
            )

    if len(com_percent_2) != 0:
        shares = {int(nr): float(share) for nr, share in com_percent_2.items()}
    else:
        shares = {int(com_nr): 1.0}

    profile = np.zeros(N_HOURS_PROFILE)
    missing = []
    for nr, share in shares.items():
        if str(nr) in df.columns:
            profile += df[str(nr)].to_numpy(dtype=float)*share
        else:
            missing.append(nr)

    if np.isnan(profile).any():
        raise ValueError(f"National generation profile {file_path} contains NaN values.")
    if (profile < 0).any():
        raise ValueError(f"National generation profile {file_path} contains negative values.")

    return profile, missing


class NationalGeneration(TechCore):

    """
    Generation technology: national generators allocated to the municipality.
    """

    def __init__(self, data_dir, com_nr, com_percent_2, tech_dict, grid_supply):

        """
        Initialise national generation and read the hourly profiles.

        Parameters
        ----------
        data_dir : str
            Directory containing one profile file per generator.
        com_nr : int
            Municipality number.
        com_percent_2 : pandas Series or list
            Custom districts: share of each municipality belonging to the
            district. Empty list otherwise.
        tech_dict : dict
            Dictionary with technology parameters (subset of scen_techs).
        grid_supply : GridSupply
            Grid supply technology; provides the tariff for generators with
            the cost 'grid_tariff'.

        Returns
        -------
        n/a
        """

        super().__init__(tech_dict)

        self._grid_supply = grid_supply

        # Initialize properties:
        self.update_tech_properties(tech_dict)

        # Carrier types:
        self.output_carrier = 'electricity'

        # Accounting (one entry per generator):
        self._v_e_pot_gen = {} # [kWh] available (allocated) generation
        self._v_e_gen = {} # [kWh] used generation

        for gen_name in self._generators:
            file_path = os.path.join(data_dir, self.__tech_dict['generators'][gen_name]['file'])
            profile, missing = load_profile(file_path, com_nr, com_percent_2)
            if missing:
                print(f"\nWARNING: National generator '{gen_name}': no column for "
                      f"municipality number(s) {missing} in {file_path}. "
                      "The profile is set to 0 for these municipalities.")
            self._v_e_pot_gen[gen_name] = profile
            self._v_e_gen[gen_name] = np.zeros(len(profile))

    def update_tech_properties(self, tech_dict):

        """
        Updates the national generation properties based on a new tech_dict.

        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        validate_tech_dict(tech_dict)

        generators = list(tech_dict['generators'].keys())
        if hasattr(self, '_generators') and generators != self._generators:
            raise ValueError(
                "The national generators cannot be changed after the model "
                f"has been initialised ({self._generators} -> {generators})."
                )

        self._generators = generators
        self._cost = {
            g: tech_dict['generators'][g].get('cost_CHFpkWh', COST_GRID_TARIFF)
            for g in generators
            } # [CHF/kWh] or COST_GRID_TARIFF
        self._co2_intensity = {g: float(tech_dict['generators'][g]['co2_intensity']) for g in generators} # [kgCO2/kWh]
        self._export_big_M = tech_dict['export_big_M_kWh']
        self._import_big_M = tech_dict['import_big_M_kWh']

        self.__tech_dict = tech_dict

    def update_df_results(self, df):

        for g in self._generators:
            df[f'v_e_nat_{g}'] = self.get_v_e(g)
            df[f'v_e_nat_pot_{g}'] = self.get_v_e_pot(g)
            df[f'v_e_nat_curt_{g}'] = self.get_v_e_pot(g) - self.get_v_e(g)
            df[f'v_co2_nat_{g}'] = self.get_v_e(g)*self._co2_intensity[g]

        df['v_e_nat'] = self.get_v_e_tot()
        df['v_e_nat_pot'] = self.get_v_e_pot_tot()
        df['v_e_nat_curt'] = self.get_v_e_pot_tot() - self.get_v_e_tot()

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

        for g in self._generators:
            self._v_e_pot_gen[g] = self._v_e_pot_gen[g][:n_hours]
            self._v_e_gen[g] = self._v_e_gen[g][:n_hours]

    def dispatch(self, m_e_need):
        """
        Cover the electricity need (i.e. demand not covered by local
        generation) with national generation (simulation, i.e. without
        optimisation). If more national generation is available than needed,
        all generators are reduced by the same fraction of their availability
        (proportional dispatch).

        Parameters
        ----------
        m_e_need : array
            Hourly electricity need [kWh].

        Returns
        -------
        v_e_tot : numpy array
            Hourly national generation used [kWh].

        """
        m_e_need = np.maximum(np.array(m_e_need, dtype=float), 0.0)
        v_e_pot_tot = self.get_v_e_pot_tot()

        if len(m_e_need) != len(v_e_pot_tot):
            raise ValueError(
                "Length of electricity need and national generation profiles "
                f"differ ({len(m_e_need)} != {len(v_e_pot_tot)})."
                )

        # Fraction of the available national generation that is used:
        frac = np.divide(
            m_e_need,
            v_e_pot_tot,
            out=np.zeros(len(m_e_need)),
            where=v_e_pot_tot > 0
            )
        frac = np.minimum(frac, 1.0)

        for g in self._generators:
            self._v_e_gen[g] = self._v_e_pot_gen[g]*frac

        return self.get_v_e_tot()

    def update_v_e(self, dict_v_e):
        """
        Update the used national generation (e.g. after optimisation).

        Parameters
        ----------
        dict_v_e : dict
            Hourly generation [kWh] per generator.
        """
        for g in self._generators:
            v_e = np.array(dict_v_e[g], dtype=float)
            if len(v_e) != len(self._v_e_pot_gen[g]):
                raise ValueError(f"National generator '{g}': length of v_e does not match.")
            self._v_e_gen[g] = v_e

    def create_techs_dict(self,
                          techs_dict,
                          color,
                          energy_scaling_factor
                          ):
        """
        Add one Calliope supply technology per national generator. The
        resource (allocated profile) is an upper bound (no forced
        generation); there is no export carrier.

        Returns
        -------
        techs_dict : dict
        tech_names : list of str
            Names of the Calliope technologies.
        """
        tech_names = []
        for g in self._generators:
            tech_name = f'national_{g}'
            techs_dict[tech_name] = {
                'essentials':{
                    'name':f'National {g}',
                    'color':color,
                    'parent':'supply',
                    'carrier':'electricity',
                    },
                'constraints':{
                    'resource':f'df=national_generation:{g}',
                    'resource_unit':'energy', # [kWh]
                    'force_resource':False,
                    'energy_cap_equals':self._v_e_pot_gen[g].max() / energy_scaling_factor,
                    'lifetime':1, # no capacity costs
                    },
                'costs':{
                    'monetary':{
                        'om_prod':f'df=national_generation_cost:{g}', # [CHF/kWh]
                        'interest_rate':0.0,
                        },
                    'emissions_co2':{
                        'om_prod':self._co2_intensity[g] * energy_scaling_factor, # [kgCO2/kWh]
                        }
                    }
                }
            tech_names.append(tech_name)

        return techs_dict, tech_names

    def get_generators(self):
        return list(self._generators)

    def get_v_e(self, gen_name):
        self.len_test(self._v_e_gen[gen_name])
        return self._v_e_gen[gen_name]

    def get_v_e_pot(self, gen_name):
        self.len_test(self._v_e_pot_gen[gen_name])
        return self._v_e_pot_gen[gen_name]

    def get_v_e_tot(self):
        return sum(self.get_v_e(g) for g in self._generators)

    def get_v_e_pot_tot(self):
        return sum(self.get_v_e_pot(g) for g in self._generators)

    def get_cost_timeseries(self, gen_name):
        """
        Return the hourly cost of a generator [CHF/kWh]: the tariff of
        grid_supply or the value set in cost_CHFpkWh.
        """
        n_hours = len(self._v_e_pot_gen[gen_name])
        if self._cost[gen_name] == COST_GRID_TARIFF:
            return self._grid_supply.get_tariff_timeseries()[:n_hours]
        return np.full(n_hours, float(self._cost[gen_name]))

    def get_co2_intensity(self, gen_name):
        return self._co2_intensity[gen_name]

    def get_export_big_M(self):
        return self._export_big_M
    
    def get_import_big_M(self):
        return self._import_big_M

    def get_energy_costs(self):
        return sum(
            np.sum(self.get_v_e(g)*self.get_cost_timeseries(g))
            for g in self._generators
            )

    def get_co2_emissions(self):
        return sum(
            np.sum(self.get_v_e(g))*self._co2_intensity[g] for g in self._generators
            )
