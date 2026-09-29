#!/usr/bin/env python3
"""Run a resumable DEM Morris screening study (Python 3.9+).

Place beside run_dem_local.py in <project>/src. Edit SETTINGS below, then run:
    python run_dem_local_sensitivities.py --dry-run
    python run_dem_local_sensitivities.py
    python run_dem_local_sensitivities.py --jobs 8 --solver-threads 16
    python analyse_morris.py            # at any time, also on a partial study

Design: one reference run per municipality plus MORRIS_TRAJECTORIES Morris
trajectories (Morris 1991), each with len(MORRIS_PARAMETERS) + 1 runs. Every
parameter takes MORRIS_LEVELS evenly spaced values between its low and high
bound; the trajectories with the best spread are selected from
MORRIS_CANDIDATES random candidates (Campolongo et al. 2007). The same
trajectories are used for every municipality. MORRIS_SEED makes the design
reproducible, which resuming relies on.

Runs are executed in parallel (PARALLEL_RUNS at once, each in its own process,
each Gurobi solve limited to SOLVER_THREADS_PER_RUN threads). Change --jobs and
--solver-threads on the command line rather than in this file: editing the file
changes the study fingerprint and blocks resuming.

Uses the uploaded DEM Python API, not YAML configuration files. Each run gets a
fresh subprocess, a unique attempt directory, a complete effective input snapshot,
DEM's native outputs, hourly_results.csv.gz, annual_results.json and costs.json.
The parent updates study_results.csv and study_events.jsonl after EVERY attempt.
Failures (including process crashes/timeouts) are recorded and do not stop later
runs. Ctrl+C deliberately stops the study; restarting skips completed runs.

Default: 3 x (1 + 15 x 12) = 543 optimisations; INCLUDE_NO_TES_REFERENCE adds three. This script does
not modify DEM source or the original demand datasets. DEM may itself populate
its ordinary derived-data caches. Do not run two copies in the same STUDY_DIR.
"""
from pathlib import Path

# =========================== EDIT SETTINGS HERE =============================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent              # directory containing data/
DEM_SOURCE_DIR = SCRIPT_DIR                   # contains district_energy_model/
BASE_INPUT_FILE = DEM_SOURCE_DIR / 'district_energy_model/input_files/inputs.py'
STUDY_DIR = PROJECT_ROOT / 'dem_sensitivity_study_2050'
HIST_DATA_YEAR = 2016                         # must match available DEM data
CURRENT_YEAR = 2026                          # municipality mapping year
FUTURE_YEAR = 2050                          # demand-side scenario year
MAX_STUDY_RUNS = 1000                        # enforced before any run starts
NUMBER_OF_DAYS = 365
# Names are resolved against your meta_data_general.feather, avoiding guessed IDs.
# Alternatively supply {"name": "Luzern", "ggdenr": 1061}.
MUNICIPALITIES = [{'name': 'Luzern'}, {'name': 'Breitenbach'}, {'name': 'Suchy'}]

REFERENCE = {
    'electricity_tariff': 0.290,              # CHF/kWh imported electricity
    'electricity_export_tariff': 0.06,      # CHF/kWh feed-in
    'quality_factor_multiplier': 1.0,       # scales all four base quality factors
    'gas_price': 0.13,                      # CHF/kWh fuel
    'oil_price': 1.00,                      # CHF/litre
    'co2_price': 0.0,                       # CHF/kg CO2 (0.1 = 100 CHF/t); CO2 weight in the objective
    'hp_capex_multiplier': 1.0,
    'tes_capex_multiplier': 1.0,
    'pv_capex_multiplier': 1.0,
    'space_heating_multiplier': 1.0,
    'interest_rate': 0.025,                 # applied to every technology
}
# Morris ranges (low, high); values are spaced evenly (linearly) in between.
MORRIS_PARAMETERS = {
    'electricity_tariff': (0.145, 0.580),       # reference -50% / +100%
    'electricity_export_tariff': (0.03, 0.12),  # reference -50% / +100%
    'quality_factor_multiplier': (0.8, 1.2),    # +/-20%
    'gas_price': (0.065, 0.260),                # reference -50% / +100%
    'oil_price': (0.50, 2.00),                  # reference -50% / +100%
    'co2_price': (0.0, 0.2),                    # 0-200 CHF/t CO2
    'hp_capex_multiplier': (0.5, 1.5),          # +/-50%
    'tes_capex_multiplier': (0.5, 1.5),         # +/-50%
    'pv_capex_multiplier': (0.5, 1.5),          # +/-50%
    'space_heating_multiplier': (0.8, 1.2),     # +/-20%
    'interest_rate': (0.01, 0.05),
}
MORRIS_TRAJECTORIES = 15
MORRIS_LEVELS = 4                            # must be even
MORRIS_CANDIDATES = 100                      # random trajectories to select from
MORRIS_SEED = 20260923
# None reads each reference factor from BASE_INPUT_FILE; alternatively enter
# a dictionary with these four keys and your chosen reference values.
QUALITY_FACTOR_BASE_VALUES = None
QUALITY_FACTOR_KEYS = ('quality_factor_ashp_new', 'quality_factor_ashp_old',
                       'quality_factor_gshp_new', 'quality_factor_gshp_old')
INCLUDE_NO_TES_REFERENCE = True
HP_CAPEX_NEW = 3018.0                        # CHF/kW_th
HP_CAPEX_REPLACEMENT = 2422.0                # CHF/kW_th
TES_CAPEX = 64.0                            # CHF/kWh_th, decentralised tank
PV_ROOFTOP_CAPEX = 2079.0                   # CHF/kWp, DEM base_capex
TES_CAPACITY_MAX_KWH = 'inf'                # upper bound, NOT forced capacity
TES_CHARGE_DISCHARGE_EFFICIENCY = 0.95       # per direction
TES_STANDING_LOSS_PER_HOUR = 0.001
TES_POWER_PER_CAPACITY = 0.1                # kW/kWh
FIX_EXISTING_DH_SHARE = True                # derive from municipal heat data
SOLVER_TIME_LIMIT_SECONDS = 36000
RUN_TIMEOUT_SECONDS = 36600                 # whole worker, including saving
MIP_GAP = 1e-4
MAX_UNMET_ENERGY_KWH = 0.1                 # sum of absolute hourly unmet energy
RESUME = True
RETRY_FAILED_RUNS = True
SAVE_CALLIOPE_CSV = True                    # also captures final rerun model
PARALLEL_RUNS = 8                           # DEM runs executed at the same time
SOLVER_THREADS_PER_RUN = None               # None: available CPUs // PARALLEL_RUNS

# Explicit study overrides; everything else is inherited from BASE_INPUT_FILE.
# Only demand_side is activated, with future_year=FUTURE_YEAR.
# Other demand_side values are inherited from BASE_INPUT_FILE, except EV
# flexibility, which is explicitly switched off below. Technology selection and
# existing-asset/replacement assumptions should be reviewed before the full study.
BASE_OVERRIDES = {
    'heat_pump': {'deployment': True, 'fixed_demand_share': False,
                  'only_allow_existing': False},
    'solar_pvrooftop': {'deployment': True, 'only_use_installed': False},
    'tes': {'deployment': False},
    'tes_sites': {'deployment': False},
    'bes': {'deployment': False},
    'solar_pvalpine': {'deployment': False},
    # No new wind: otherwise the optimiser builds turbines purely to export at the
    # feed-in tariff. Requires municipalities without installed wind (checked).
    'wind_power': {'kWp_max': 0.0},
    'demand_side': {'ev_flexibility': False},
    'meta_data': {'custom_district': {'implemented': False}},
}
# ========================= END EDITABLE SETTINGS =============================

import argparse
import contextlib
import copy
import csv
import hashlib
import importlib.util
import json
import math
import os
import random
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone

COMPLETE = {'succeeded', 'completed_unverified'}
POLL_SECONDS = 5
THREAD_ENV_VARS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                   'NUMEXPR_NUM_THREADS')


def now():
    return datetime.now(timezone.utc).isoformat()


def available_cpus():
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        return os.cpu_count() or 1


@contextlib.contextmanager
def file_lock(path):
    """Inter-process lock; the OS releases it if the holding process dies."""
    with open(path, 'a+') as handle:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0)
            while True:
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def json_value(value):
    """Convert numpy/pandas scalars and arrays without requiring them in parent."""
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, 'tolist'):
        return json_value(value.tolist())
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def atomic_json(path, data):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf-8') as stream:
        json.dump(json_value(data), stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def strict_update(target, overrides, prefix=''):
    for key, value in overrides.items():
        if key not in target:
            raise KeyError('Unknown DEM input: ' + prefix + key)
        if isinstance(value, dict):
            strict_update(target[key], value, prefix + key + '.')
        else:
            target[key] = copy.deepcopy(value)


def morris_design():
    """Return parameter names and the selected trajectories.

    A trajectory is a list of (levels, changed_parameter) steps; levels are
    integers 0..MORRIS_LEVELS-1 and each step moves one parameter by
    MORRIS_LEVELS/2 levels (delta = p / (2(p-1)) of its range).
    """
    names = list(MORRIS_PARAMETERS)
    k, p = len(names), MORRIS_LEVELS
    if p < 2 or p % 2:
        raise ValueError('MORRIS_LEVELS must be an even number >= 2.')
    if not 1 <= MORRIS_TRAJECTORIES <= MORRIS_CANDIDATES:
        raise ValueError('Need 1 <= MORRIS_TRAJECTORIES <= MORRIS_CANDIDATES.')
    for name, (low, high) in MORRIS_PARAMETERS.items():
        if not 0 <= low < high:
            raise ValueError('Morris range must satisfy 0 <= low < high: ' + name)
    jump = p // 2
    rng = random.Random(MORRIS_SEED)
    candidates = []
    for _ in range(MORRIS_CANDIDATES):
        base = [rng.randrange(p - jump) for _ in range(k)]
        up = [rng.random() < 0.5 for _ in range(k)]
        point = [b if u else b + jump for b, u in zip(base, up)]
        order = list(range(k))
        rng.shuffle(order)
        steps = [(list(point), None)]
        for i in order:
            point[i] += jump if up[i] else -jump
            steps.append((list(point), names[i]))
        candidates.append(steps)
    # Greedy spread selection: start with the most distant pair, then add the
    # candidate with the largest summed distance to those already chosen.
    n = len(candidates)
    dist = [[0.0] * n for _ in range(n)]
    for a in range(n):
        for b in range(a + 1, n):
            dist[a][b] = dist[b][a] = sum(math.dist(x, y) for x, _ in candidates[a]
                                          for y, _ in candidates[b])
    if n == 1:
        chosen = [0]
    else:
        chosen = list(max(((a, b) for a in range(n) for b in range(a + 1, n)),
                          key=lambda pair: dist[pair[0]][pair[1]]))
    while len(chosen) < MORRIS_TRAJECTORIES:
        chosen.append(max((c for c in range(n) if c not in chosen),
                          key=lambda c: sum(dist[c][s] for s in chosen)))
    return names, [candidates[c] for c in chosen[:MORRIS_TRAJECTORIES]]


def build_cases():
    missing = set(MORRIS_PARAMETERS) - set(REFERENCE)
    if missing:
        raise ValueError('Morris parameters missing in REFERENCE: ' + ', '.join(sorted(missing)))
    cases = []

    def add(name, group, values, no_tes=False, morris=None):
        params = dict(REFERENCE, **values)
        if any(not math.isfinite(float(v)) or float(v) < 0 for v in params.values()):
            raise ValueError('Parameter values must be finite and non-negative.')
        case = {'case': name, 'group': group, 'parameters': params, 'no_tes': no_tes}
        if morris is not None:
            case['morris'] = morris
        cases.append(case)

    add('reference', 'reference', {})
    if INCLUDE_NO_TES_REFERENCE:
        add('reference_no_tes', 'no_tes', {}, True)
    names, trajectories = morris_design()
    for t, steps in enumerate(trajectories, 1):
        for s, (levels, changed) in enumerate(steps):
            values = {}
            for name, level in zip(names, levels):
                low, high = MORRIS_PARAMETERS[name]
                values[name] = round(low + (high - low) * level / (MORRIS_LEVELS - 1), 10)
            add('morris_t%02d_s%02d' % (t, s), 'morris', values,
                morris={'trajectory': t, 'step': s, 'changed': changed,
                        'levels': dict(zip(names, levels))})
    return cases


def settings_snapshot():
    return {key: json_value(globals()[key]) for key in (
        'PROJECT_ROOT', 'DEM_SOURCE_DIR', 'BASE_INPUT_FILE', 'HIST_DATA_YEAR',
        'CURRENT_YEAR', 'FUTURE_YEAR', 'QUALITY_FACTOR_BASE_VALUES', 'QUALITY_FACTOR_KEYS', 'NUMBER_OF_DAYS', 'HP_CAPEX_NEW', 'HP_CAPEX_REPLACEMENT',
        'MORRIS_PARAMETERS', 'MORRIS_TRAJECTORIES', 'MORRIS_LEVELS', 'MORRIS_CANDIDATES',
        'MORRIS_SEED', 'PV_ROOFTOP_CAPEX',
        'TES_CAPEX', 'TES_CAPACITY_MAX_KWH',
        'TES_CHARGE_DISCHARGE_EFFICIENCY', 'TES_STANDING_LOSS_PER_HOUR',
        'TES_POWER_PER_CAPACITY', 'FIX_EXISTING_DH_SHARE',
        'SOLVER_TIME_LIMIT_SECONDS', 'RUN_TIMEOUT_SECONDS', 'MIP_GAP',
        'MAX_UNMET_ENERGY_KWH', 'SAVE_CALLIOPE_CSV', 'BASE_OVERRIDES')}


def scale_loaded_demand(loaded, ggdenr, factor):
    """Scale SH before DEM builds profiles, allocations and technology capacities.

    get_com_files returns (name, canton, merged metadata, building dataframe).
    v_h_* metadata are SPACE heating; v_hw_* are DHW and remain unchanged.
    This adapter targets the schema in the uploaded DEM version; fail loudly if
    required columns are missing rather than silently running an unchanged case.
    """
    name, canton, meta, buildings = loaded
    meta, buildings = meta.copy(deep=True), buildings.copy(deep=True)
    sh = 'space_heating_demand_estimation_kWh'
    if sh not in meta or sh not in buildings or 'GGDENR' not in meta:
        raise KeyError('Demand scaling requires DEM space-heating columns.')
    mask = meta['GGDENR'] == ggdenr
    if int(mask.sum()) != 1:
        raise ValueError('Expected exactly one municipality metadata row.')
    before = float(meta.loc[mask, sh].iloc[0])
    # Future demand is a mixture of unrenovated and renovated demand. Scale
    # both endpoints so the perturbation survives the 2050 renovation calculation.
    renovated = 'heat_energy_demand_renov_estimate_kWh'
    if renovated not in buildings:
        raise KeyError('2050 sensitivity requires ' + renovated)
    buildings[sh] = buildings[sh] * factor
    buildings[renovated] = buildings[renovated] * factor
    meta.loc[mask, sh] = meta.loc[mask, sh] * factor
    for suffix in ('eh', 'hp', 'dh', 'gb', 'ob', 'wb', 'solar', 'other'):
        column = 'v_h_' + suffix
        if column not in meta:
            raise KeyError('Missing heat-allocation column: ' + column)
        meta.loc[mask, column] = meta.loc[mask, column] * factor
    audit = {'space_heating_multiplier': factor,
             'renovated_space_heating_scaled': True,
             'space_heating_before_kWh': before,
             'space_heating_after_kWh': float(meta.loc[mask, sh].iloc[0]),
             'dhw_unchanged_kWh': float(meta.loc[mask, 'DHW_demand_estimation_kWh'].iloc[0])}
    return (name, canton, meta, buildings), audit


def execute_dem(spec, attempt):
    """Worker-only imports and changes: no state survives to another run."""
    import pandas as pd
    s, params = spec['settings'], spec['parameters']
    sys.path.insert(0, s['DEM_SOURCE_DIR'])
    os.chdir(s['DEM_SOURCE_DIR'])         # preserve DEM relative input paths
    from district_energy_model import dem, dem_helper, dem_paths, dem_calliope

    module_spec = importlib.util.spec_from_file_location('sensitivity_inputs', s['BASE_INPUT_FILE'])
    inp = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(inp)
    config = copy.deepcopy(inp.scen_techs)
    strict_update(config, s['BASE_OVERRIDES'])
    config['scenarios'] = {key: key == 'demand_side' for key in config['scenarios']}
    strict_update(config, {
        'optimisation': {'enabled': True, 'pareto_monetary_co2': False,
            # objective = cost + co2_price x emissions; DEM reports cost without the CO2 term.
            'objective_monetary': 1.0, 'objective_co2': params['co2_price'],
            'objective_ess': 0.0, 'objective_tss': 0.0,
            'solver_option_TimeLimit': s['SOLVER_TIME_LIMIT_SECONDS'],
            'solver_option_MIPGap': s['MIP_GAP'], 'MIPGap_increase': False,
            'save_calliope_files': s['SAVE_CALLIOPE_CSV']},
        'simulation': {'number_of_days': s['NUMBER_OF_DAYS'],
                       'save_results': True, 'generate_plots': False},
        'demand_side': {'simulation_year': {'type': 'future', 'future_year': s['FUTURE_YEAR']}},
        'heat_pump': {'cop_mode': 'location_based',
            'capex': s['HP_CAPEX_NEW'] * params['hp_capex_multiplier'],
            'capex_one_to_one_replacement': s['HP_CAPEX_REPLACEMENT'] * params['hp_capex_multiplier']},
        'solar_pvrooftop': {'base_capex': s['PV_ROOFTOP_CAPEX'] * params['pv_capex_multiplier']},
        'grid_supply': {'tariff_mode': 'const',
                        'constant_tariff_CHFpkWh': params['electricity_tariff']},
        'grid_export': {'tariff_mode': 'const',
                        'constant_tariff_CHFpkWh': params['electricity_export_tariff']},
        'tes_decentralised': {'deployment': not spec['no_tes'],
            'capex': s['TES_CAPEX'] * params['tes_capex_multiplier'],
            'capacity_kWh': s['TES_CAPACITY_MAX_KWH'],
            'eta_chg_dchg': s['TES_CHARGE_DISCHARGE_EFFICIENCY'],
            'tes_gamma': s['TES_STANDING_LOSS_PER_HOUR'],
            'chg_dchg_per_cap_max': s['TES_POWER_PER_CAPACITY'],
            'optimized_initial_charge': True,
            'connections': {'heat_pump': True, 'solar_thermal': False}},
    })
    # Scale the four factors relative to the base inputs, never cumulatively.
    quality_bases = s['QUALITY_FACTOR_BASE_VALUES']
    if quality_bases is None:
        quality_bases = {key: config['heat_pump'][key] for key in s['QUALITY_FACTOR_KEYS']}
    if set(quality_bases) != set(s['QUALITY_FACTOR_KEYS']):
        raise ValueError('QUALITY_FACTOR_BASE_VALUES must contain exactly the four quality-factor keys.')
    for key, base in quality_bases.items():
        value = float(base) * params['quality_factor_multiplier']
        if not math.isfinite(value) or not 0 < value <= 1:
            raise ValueError('Scaled heat-pump quality factor outside (0,1]: ' + key)
        strict_update(config, {'heat_pump': {key: value}})
    # DEM uses supply prices in the optimisation and technology prices in some
    # accounting paths. Update every occurrence of the matching fuel-price key;
    # the interest rate likewise appears once per technology.
    def set_everywhere(node, name, value):
        for key, item in node.items():
            if isinstance(item, dict):
                set_everywhere(item, name, value)
            elif key == name:
                # Waste-heat parameters may be per-source lists.
                node[key] = [value] * len(item) if isinstance(item, list) else value
    set_everywhere(config, 'gas_price_CHFpkWh', params['gas_price'])
    set_everywhere(config, 'oil_price_CHFpl', params['oil_price'])
    set_everywhere(config, 'interest_rate', params['interest_rate'])
    for fuel_key in ('gas_price_CHFpkWh', 'oil_price_CHFpl'):
        if fuel_key not in config['supply']:
            raise KeyError('Missing optimisation fuel price: supply.' + fuel_key)
    paths = dem_paths.DEMPaths(s['PROJECT_ROOT'], output_dir=str(attempt / 'dem_output'),
                              hist_data_year=s['HIST_DATA_YEAR'], current_year=s['CURRENT_YEAR'])
    municipality = spec['municipality']
    metadata = pd.read_feather(Path(paths.simulation_data_dir) / paths.meta_file_general)
    if municipality.get('ggdenr') is not None:
        selected = metadata.loc[metadata['GGDENR'] == municipality['ggdenr']]
    else:
        selected = metadata.loc[metadata['Municipality'].astype(str).str.casefold()
                                == municipality['name'].casefold()]
    if len(selected) != 1:
        raise ValueError('Municipality must resolve uniquely: %r' % municipality)
    ggdenr = int(selected.iloc[0]['GGDENR'])
    actual_name = str(selected.iloc[0]['Municipality'])
    if actual_name.casefold() != municipality['name'].casefold():
        raise ValueError('Municipality ID/name mismatch: ' + actual_name)
    config['simulation']['district_number'] = ggdenr
    # With kWp_max = 0, DEM moves installed turbines to a zero-capacity wind unit
    # and fails only after the optimisation; stop such runs right away.
    if config['wind_power']['deployment'] and config['wind_power']['kWp_max'] == 0:
        wind = pd.read_feather(Path(paths.wind_power_data_dir) / paths.wind_power_cap_file)
        installed = float(wind.loc[wind['GGDENR'] == ggdenr, 'p_kW'].sum())
        if installed > 0:
            raise ValueError('%s has %.0f kW installed wind; wind_power.kWp_max = 0 (no new wind) '
                             'is only supported without installed turbines.' % (actual_name, installed))
    original_loader = dem_helper.get_com_files
    # get_com_files writes a shared per-municipality CSV cache on first use;
    # serialise it so parallel workers never read a half-written file.
    with file_lock(attempt.parent.parent / 'dem_data_cache.lock'):
        loaded = original_loader(com_nr=ggdenr, master_data_dir=paths.simulation_data_dir,
            com_data_dir=paths.com_data_dir, master_file_general=paths.master_file_general,
            meta_file_general=paths.meta_file_general, master_file_year=paths.master_file_year,
            meta_file_year=paths.meta_file_year)
    loaded, audit = scale_loaded_demand(loaded, ggdenr, params['space_heating_multiplier'])
    audit.update({'GGDENR': ggdenr, 'municipality': actual_name})
    if s['FIX_EXISTING_DH_SHARE']:
        row = loaded[2].loc[loaded[2]['GGDENR'] == ggdenr].iloc[0]
        total = float(row['space_heating_demand_estimation_kWh'] + row['DHW_demand_estimation_kWh'])
        share = float(row['v_h_dh'] + row['v_hw_dh']) / total if total > 0 else 0.0
        if not 0 <= share <= 1:
            raise ValueError('Invalid existing district-heating share.')
        strict_update(config, {'district_heating': {'demand_share_type': 'fixed',
                                                  'demand_share_val': share}})
        audit['fixed_dh_share'] = share
    atomic_json(attempt / 'demand_audit.json', audit)
    atomic_json(attempt / 'effective_inputs.json', config)

    # Only the constructor in this worker sees the altered in-memory datasets.
    def load_copy(*args, **kwargs):
        requested = kwargs.get('com_nr', args[0] if args else None)
        if requested != ggdenr:
            raise ValueError('Unexpected municipality requested by DEM.')
        return loaded[0], loaded[1], loaded[2].copy(deep=True), loaded[3].copy(deep=True)

    dem_helper.get_com_files = load_copy
    captured = {}
    original_optimise = dem_calliope.CalliopeOptimiser.run_optimisation

    def capture_optimisation(optimiser, *args, **kwargs):
        results, model = original_optimise(optimiser, *args, **kwargs)
        # Capture FINAL results, including DEM's custom-constraint rerun. model
        # itself can still refer to the pre-rerun Calliope model in this version.
        captured['attrs'] = dict(results.attrs)
        atomic_json(attempt / 'solver_metadata.json', captured['attrs'])
        for variable in ('energy_cap', 'storage_cap', 'cost', 'unmet_demand'):
            if variable in results:
                results[variable].to_dataframe(name=variable).to_csv(attempt / (variable + '.csv'))
        return results, model

    dem_calliope.CalliopeOptimiser.run_optimisation = capture_optimisation
    # DEM's run dict has no Threads option; without it every parallel Gurobi
    # solve would try to use all cores of the machine.
    original_run_dict = dem_calliope.CalliopeOptimiser._CalliopeOptimiser__create_run_dict

    def run_dict_with_threads(optimiser):
        run_dict = original_run_dict(optimiser)
        if spec.get('solver_threads') and run_dict['solver'] == 'gurobi':
            run_dict['solver_options']['Threads'] = int(spec['solver_threads'])
        return run_dict

    dem_calliope.CalliopeOptimiser._CalliopeOptimiser__create_run_dict = run_dict_with_threads
    try:
        instance = dem.DistrictEnergyModel(paths=paths, arg_com_nr=ggdenr,
            scen_techs=config, hist_data_year=s['HIST_DATA_YEAR'],
            current_year=s['CURRENT_YEAR'], toggle_energy_balance_tests=True)
        instance.run(scen_techs=config, toggle_load_pareto_results=False,
                     toggle_save_results=True, toggle_plot=False)
        # All outputs are persisted BEFORE marking the worker completed.
        # PV energy_cap is in units of the roof-class profile; installed kWp =
        # energy_cap x capex_scaling of that class (as in DEM's cost accounting).
        atomic_json(attempt / 'model_info.json', {
            'pv_rooftop_capex_scaling': instance.tech_solar_pv_rooftop._capex_scaling,
            'calliope_energy_scaling_factor': config['optimisation']['calliope_energy_scaling_factor']})
        annual, costs, hourly = instance.annual_results(), instance.total_cost(), instance.hourly_results()
        atomic_json(attempt / 'annual_results.json', annual)
        atomic_json(attempt / 'costs.json', costs)
        hourly.to_csv(attempt / 'hourly_results.csv.gz', index=True, compression='gzip')
        if len(hourly) != 24 * s['NUMBER_OF_DAYS']:
            raise ValueError('Unexpected number of hourly result rows.')
        unmet_columns = ['d_e_unmet', 'd_h_unmet', 'd_h_unmet_dhn']
        if any(col not in hourly for col in unmet_columns):
            raise ValueError('Missing unmet-demand outputs; cannot validate result.')
        unmet = hourly[unmet_columns].abs().sum().sum()
        if not math.isfinite(float(unmet)) or hourly[unmet_columns].isna().any().any():
            raise ValueError('Non-finite unmet-demand outputs.')
        if float(unmet) > s['MAX_UNMET_ENERGY_KWH']:
            raise ValueError('Unmet demand exceeds threshold: %.6g kWh' % unmet)
        termination = str(captured.get('attrs', {}).get('termination_condition', 'unknown'))
        if termination.lower() not in ('optimal', 'unknown'):
            raise ValueError('Solver termination was %s; outputs retained for review.' % termination)
        return {'status': 'succeeded' if termination.lower() == 'optimal' else 'completed_unverified',
                'GGDENR': ggdenr, 'termination_condition': termination,
                'unmet_energy_kWh': float(unmet), 'dem_results_path': str(instance.results_path),
                'solver_threads': spec.get('solver_threads')}
    finally:
        dem_helper.get_com_files = original_loader
        dem_calliope.CalliopeOptimiser.run_optimisation = original_optimise
        dem_calliope.CalliopeOptimiser._CalliopeOptimiser__create_run_dict = original_run_dict


def worker(spec_path):
    spec = read_json(spec_path)
    attempt = Path(spec_path).parent
    started = time.monotonic()
    record = {'started_at': now()}
    try:
        record.update(execute_dem(spec, attempt))
    except BaseException as error:
        # SystemExit in dependencies must not silently count as success.
        record.update(status='failed', error_type=type(error).__name__, error=str(error))
        (attempt / 'error_traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
        traceback.print_exc()
    record.update(finished_at=now(), duration_seconds=time.monotonic() - started)
    atomic_json(attempt / 'status.json', record)
    return 0 if record['status'] in COMPLETE else 1


def append_event(study, record):
    with (study / 'study_events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(json_value(record), ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def flatten(data, prefix):
    result = {}
    for key, value in data.items():
        label = prefix + str(key)
        if isinstance(value, dict):
            result.update(flatten(value, label + '.'))
        elif isinstance(value, (list, tuple)):
            result[label] = json.dumps(value)
        else:
            result[label] = value
    return result


def save_summary(study, plans):
    rows = []
    for plan in plans:
        run_dir = study / plan['run_id']
        status_path = run_dir / 'status.json'
        record = read_json(status_path) if status_path.exists() else {'status': 'pending'}
        morris = plan.get('morris', {})
        row = {'run_id': plan['run_id'], 'municipality': plan['municipality']['name'],
               'case': plan['case'], 'group': plan['group'],
               'morris_trajectory': morris.get('trajectory'), 'morris_step': morris.get('step'),
               'morris_changed': morris.get('changed'), **plan['parameters'], **record}
        # Failed runs may have partial outputs: preserve them in the attempt
        # folder, but do not mix them with accepted results in the summary.
        if record['status'] in COMPLETE:
            attempt = Path(record['attempt_dir'])
            for filename, prefix in [('annual_results.json', 'annual.'), ('costs.json', 'cost.')]:
                row.update(flatten(read_json(attempt / filename), prefix))
        rows.append(row)
    columns = list(dict.fromkeys(key for row in rows for key in row))
    tmp = study / 'study_results.csv.tmp'
    with tmp.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, study / 'study_results.csv')


def stop_process(process):
    if process.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if process.poll() is None:
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait()


def start_attempt(spec, attempt, threads):
    # solver_threads is stored per attempt, so it does not alter the study fingerprint.
    atomic_json(attempt / 'run_spec.json', dict(spec, solver_threads=threads))
    atomic_json(attempt / 'status.json', {'status': 'running', 'started_at': now()})
    env = dict(os.environ, **{name: str(threads) for name in THREAD_ENV_VARS})
    log = (attempt / 'run.log').open('w', encoding='utf-8')
    try:
        process = subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()),
                                    '--worker', str(attempt / 'run_spec.json')],
            stdout=log, stderr=subprocess.STDOUT, env=env,
            start_new_session=(os.name != 'nt'))
    except BaseException:
        log.close()
        raise
    return process, log


def finish_attempt(attempt, code):
    record = read_json(attempt / 'status.json')
    if code != 0 or record.get('status') not in COMPLETE:
        if record.get('status') != 'failed':
            record.update(status='failed', error_type='WorkerExit',
                          error='Worker exited without completing; see run.log.')
    record['returncode'] = code
    return record


def new_attempt(study, spec, index, total):
    run_dir = study / spec['run_id']
    number = 1
    while (run_dir / ('attempt_%03d' % number)).exists():
        number += 1
    attempt = run_dir / ('attempt_%03d' % number)
    attempt.mkdir()
    record = {'status': 'running', 'started_at': now(), 'attempt_dir': str(attempt)}
    atomic_json(run_dir / 'status.json', record)
    append_event(study, dict(record, run_id=spec['run_id']))
    print('[%d/%d] RUN %s -> %s' % (index, total, spec['run_id'], attempt), flush=True)
    return {'index': index, 'spec': spec, 'attempt': attempt, 'record': record,
            'process': None, 'log': None,
            'deadline': time.monotonic() + spec['settings']['RUN_TIMEOUT_SECONDS']}


def conclude_attempt(study, plans, job, code=None, interrupted=False):
    """Record the outcome of one attempt. code=None with a live process means timeout."""
    record, attempt, process = job['record'], job['attempt'], job['process']
    try:
        if interrupted:
            if process is not None:
                stop_process(process)
            record.update(status='interrupted', error='Stopped by user; safe to resume.')
        elif process is not None and code is None:
            stop_process(process)
            record.update(status='failed', error_type='TimeoutExpired',
                          error='Whole-run timeout exceeded; worker terminated.')
        elif process is not None:
            record.update(finish_attempt(attempt, code))
    except Exception as error:
        record.update(status='failed', error_type=type(error).__name__, error=str(error))
        (attempt / 'parent_traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        if job['log'] is not None:
            job['log'].close()
    record['finished_at'] = now()
    run_id = job['spec']['run_id']
    atomic_json(attempt / 'status.json', record)
    atomic_json(study / run_id / 'status.json', record)
    append_event(study, dict(record, run_id=run_id))
    save_summary(study, plans)
    print('[%d/%d] %s %s%s' % (job['index'], len(plans), record['status'].upper(), run_id,
                               ': ' + record['error'] if 'error' in record else ''), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='List runs; no DEM/data imports or writes.')
    parser.add_argument('--jobs', type=int, default=PARALLEL_RUNS,
                        help='DEM runs executed in parallel (default: PARALLEL_RUNS).')
    parser.add_argument('--solver-threads', type=int, default=SOLVER_THREADS_PER_RUN,
                        help='Gurobi threads per run (default: available CPUs // jobs).')
    parser.add_argument('--worker', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker)
    jobs = args.jobs
    if jobs < 1:
        raise ValueError('--jobs must be at least 1.')
    threads = args.solver_threads or max(1, available_cpus() // jobs)
    if threads < 1:
        raise ValueError('--solver-threads must be at least 1.')
    cases = build_cases()
    settings = settings_snapshot()
    plans = []
    for municipality in MUNICIPALITIES:
        slug = ''.join(c if c.isalnum() else '_' for c in municipality['name'])
        for case in cases:
            plans.append(dict(case, municipality=municipality,
                              run_id=slug + '__' + case['case'], settings=settings))
    if not plans or len({p['run_id'] for p in plans}) != len(plans):
        raise ValueError('Empty study or duplicate run IDs; check municipality names.')
    if len(plans) > MAX_STUDY_RUNS or len(plans) > 1000:
        raise ValueError('Study has %d runs; maximum is %d. Reduce municipalities or trajectories.'
                         % (len(plans), min(MAX_STUDY_RUNS, 1000)))
    if args.dry_run:
        print('Morris design: %d trajectories x %d runs, %d levels per parameter:'
              % (MORRIS_TRAJECTORIES, len(MORRIS_PARAMETERS) + 1, MORRIS_LEVELS))
        for name, (low, high) in MORRIS_PARAMETERS.items():
            levels = [low + (high - low) * i / (MORRIS_LEVELS - 1) for i in range(MORRIS_LEVELS)]
            print('  %-26s %s  (reference %g)' % (name, ', '.join('%.4g' % v for v in levels),
                                                  REFERENCE[name]))
        for i, p in enumerate(plans, 1):
            print('%03d %s %s' % (i, p['run_id'], p['parameters']))
        print('Total: %d runs. Output: %s' % (len(plans), STUDY_DIR))
        print('Parallel: %d run(s) at once x %d solver thread(s); %d CPUs available.'
              % (jobs, threads, available_cpus()))
        return 0
    if not Path(BASE_INPUT_FILE).is_file():
        raise FileNotFoundError('Set BASE_INPUT_FILE and DEM_SOURCE_DIR at the top of this script.')
    if not (Path(PROJECT_ROOT) / 'data').is_dir():
        raise FileNotFoundError('PROJECT_ROOT must contain the DEM data/ directory.')
    if RUN_TIMEOUT_SECONDS <= 0 or not 0 < NUMBER_OF_DAYS <= 365:
        raise ValueError('Invalid timeout or number_of_days.')
    study = Path(STUDY_DIR).resolve()
    study.mkdir(parents=True, exist_ok=True)
    # Prevent accidentally resuming results with different code or study inputs.
    fingerprint = hashlib.sha256((json.dumps(plans, sort_keys=True) +
        Path(__file__).read_text(encoding='utf-8') +
        Path(BASE_INPUT_FILE).read_text(encoding='utf-8')).encode('utf-8')).hexdigest()
    manifest = study / 'study_manifest.json'
    if manifest.exists():
        if read_json(manifest)['fingerprint'] != fingerprint:
            raise ValueError('Study settings/script/inputs changed. Choose a new STUDY_DIR to preserve prior results.')
    else:
        atomic_json(manifest, {'fingerprint': fingerprint, 'created_at': now(), 'runs': plans})
        (study / 'base_inputs_snapshot.py').write_bytes(Path(BASE_INPUT_FILE).read_bytes())
        (study / 'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    save_summary(study, plans)
    queue = []
    for i, spec in enumerate(plans, 1):
        run_dir = study / spec['run_id']
        run_dir.mkdir(exist_ok=True)
        status_path = run_dir / 'status.json'
        previous = read_json(status_path) if status_path.exists() else {}
        if RESUME and previous.get('status') in COMPLETE:
            print('[%d/%d] SKIP %s (already completed)' % (i, len(plans), spec['run_id']), flush=True)
            continue
        if RESUME and previous.get('status') == 'failed' and not RETRY_FAILED_RUNS:
            continue
        queue.append((i, spec))
    print('Starting %d run(s): up to %d in parallel, %d solver thread(s) each, %d CPUs available.'
          % (len(queue), jobs, threads, available_cpus()), flush=True)
    active = []
    try:
        while queue or active:
            while queue and len(active) < jobs:
                index, spec = queue.pop(0)
                job = new_attempt(study, spec, index, len(plans))
                active.append(job)
                try:
                    job['process'], job['log'] = start_attempt(spec, job['attempt'], threads)
                except Exception as error:
                    job['record'].update(status='failed', error_type=type(error).__name__, error=str(error))
                    (job['attempt'] / 'parent_traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
                    active.remove(job)
                    conclude_attempt(study, plans, job)
            if active:
                time.sleep(POLL_SECONDS)
            for job in list(active):
                code = job['process'].poll()
                if code is None and time.monotonic() < job['deadline']:
                    continue
                active.remove(job)
                conclude_attempt(study, plans, job, code)
    except BaseException as error:
        # Never leave parallel workers running without a parent: stop them all
        # first, then record them as interrupted (safe to resume).
        for job in active:
            if job['process'] is not None:
                stop_process(job['process'])
        for job in list(active):
            conclude_attempt(study, plans, job, interrupted=True)
        if isinstance(error, KeyboardInterrupt):
            return 130
        raise
    print('Study finished. Results: %s' % (study / 'study_results.csv'))
    failures = sum(read_json(study / p['run_id'] / 'status.json')['status'] == 'failed' for p in plans)
    print('%d failed run(s); inspect study_events.jsonl and per-attempt logs.' % failures)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
