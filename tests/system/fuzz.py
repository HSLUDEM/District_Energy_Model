"""
Random combinations of settings.

    python fuzz.py make <n> <seed> <cases.txt>   -> case file for run_cases.py
    python fuzz.py check <prefix>                -> classify _work/results/<prefix>*.json
"""
import glob
import json
import os
import random
import sys

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, MASTER_DATA, run_env  # noqa: E402

MUNIS = [2762, 351, 261, 448, 1367, 6076, 3851, 2549, 371, 5586, 708, 2701]
CENTRAL = ['chp_gt', 'gas_turbine_cp', 'steam_turbine', 'wood_boiler_sg', 'oil_boiler_cp', 'electric_heater_cp',
           'wood_boiler_cp', 'gas_boiler_cp', 'heat_pump_cp_lt', 'deep_geothermal']
BIOMASS = ['hydrothermal_gasification', 'anaerobic_digestion_upgrade', 'anaerobic_digestion_upgrade_hydrogen',
           'anaerobic_digestion_chp', 'wood_gasification_upgrade', 'wood_gasification_upgrade_hydrogen',
           'wood_gasification_chp', 'hydrogen_production']
STORAGE = ['tes', 'tes_decentralised', 'bes', 'gtes', 'ws', 'hes']
DH_SOURCE = {'chp_gt': 'chp_gt', 'steam_turbine': 'steam_turbine', 'oil_boiler_cp': 'oil_boiler_cp',
             'electric_heater_cp': 'electric_heater_cp', 'wood_boiler_cp': 'wood_boiler_cp',
             'gas_boiler_cp': 'gas_boiler_cp', 'heat_pump_cp_lt': 'heat_pump_cp_lt', 'deep_geothermal': 'deep_geothermal'}

# Errors that are intended input validation (not bugs):
EXPECTED = ['Combination of TES and BES scenario not supported', 'thermal_energy_storage_scenario.capacity_kWh',
            'Hydrogen is required', 'could not be computed because scen_techs', 'Fixed demand share values cannot add up',
            'makes the optimisation unbounded', 'No wind power data found']


def rand_cfg(r):
    c = {'simulation': {'number_of_days': r.choice([1, 2, 3, 7, 14]), 'save_results': False,
                        'district_number': r.choice(MUNIS)}}
    if r.random() < 0.12:
        c['meta_data'] = {'custom_district': {'implemented': True, 'EGID_List': '__EGIDS__', 'custom_district_name': 'F'}}
    if r.random() < 0.3:
        c['_launch'] = {'hist_data_year': r.choice([2016, 2018, 2019])}
    sc = {k: r.random() < 0.3 for k in ['demand_side', 'fossil_heater_retrofit', 'pv_integration', 'wind_integration',
                                        'nuclear_phaseout', 'battery_energy_storage', 'thermal_energy_storage']}
    c['scenarios'] = sc
    if sc['thermal_energy_storage']:
        c['tes_decentralised'] = {'deployment': True}
        c['thermal_energy_storage_scenario'] = {'capacity_kWh': r.choice([1e3, 1e5, 1e7]), 'initial_charge': r.choice([0.0, 0.5])}
    if sc['battery_energy_storage']:
        c['battery_energy_storage_scenario'] = {'capacity_kWh': r.choice([1e3, 1e5]), 'initial_charge': r.choice([0.0, 0.5])}
    if sc['fossil_heater_retrofit']:
        c['fossil_heater_retrofit'] = {k: r.choice([0.3, 1.0]) for k in ['oil_boiler_replacement_factor', 'gas_boiler_replacement_factor', 'electric_boiler_replacement_factor']}
    if sc['pv_integration']:
        c['pv_integration'] = {'potential_integration_factor': {'solar_pvrooftop': [r.choice([0.2, 0.9])] * 4}}
    if sc['wind_integration']:
        c['wind_integration'] = {'potential_integration_factor': r.choice([0.2, 0.9])}
    if sc['demand_side']:
        ds = {'simulation_year': {'type': r.choice(['current', 'future']), 'future_year': r.choice([2030, 2040, 2050])},
              'ev_integration': r.random() < 0.7, 'ev_integration_factor': r.choice([30, 100]), 'ev_flexibility': r.random() < 0.5,
              'total_renovation': r.random() < 0.6, 'use_constant_total_renovation_rate': r.random() < 0.5,
              'renovation_scenario': r.choice(['renovation_low', 'renovation_base', 'renovation_high']),
              'heat_generator_renovation': r.random() < 0.6, 'act_on_fossil_heater_retrofit': r.random() < 0.3,
              'dr_flexibility_building_inertia': r.random() < 0.3}
        c['demand_side'] = ds
    c['heat_pump'] = {'cop_mode': r.choice(['location_based', 'location_based', 'constant'])}
    c['oil_boiler'] = {'eta': r.choice([0.75, 0.85])}
    c['solar_pvrooftop'] = {'eta_overall': r.choice([0.15, 0.2185])}
    c['grid_supply'] = {'constant_tariff_CHFpkWh': r.choice([0.2, 0.29, 0.4])}
    if r.random() < 0.15:
        c[r.choice(['oil_boiler', 'gas_boiler', 'electric_heater', 'district_heating'])] = {'deployment': False}
    if r.random() < 0.5:
        o = {'enabled': True, 'solver_option_Threads': 2}
        if r.random() < 0.25:
            o.update(objective_monetary=r.choice([1e-5, 0.5]), objective_co2=1.0)
        if r.random() < 0.05:
            o.update(pareto_monetary_co2=True, N_pareto=3)
            c['simulation']['number_of_days'] = min(c['simulation']['number_of_days'], 2)
        c['optimisation'] = o
        dh = {}
        for t in r.sample(CENTRAL, r.choice([0, 1, 2])):
            c.setdefault(t, {})['deployment'] = True
            if t in DH_SOURCE:
                dh[DH_SOURCE[t]] = True
        if r.random() < 0.3:
            for t in r.sample(BIOMASS, r.choice([1, 2])):
                c[t] = {'deployment': True}
            dh['biomass'] = True
        for t in r.sample(STORAGE, r.choice([0, 1, 2])):
            c.setdefault(t, {})['deployment'] = True
        if r.random() < 0.2:
            c['heat_pump_cp'] = {'instance_1': {'deployment': True, 'cop_mode': r.choice(['constant', 'temperature_based'])}}
            dh['heat_pump_cp'] = True
        if r.random() < 0.15:
            c['wind_power'] = {'kWp_max_systemwide': r.choice([0, 5000])}
        if dh:
            c['district_heating'] = {**c.get('district_heating', {}), 'heat_sources': dh}
        if 'steam_turbine' in c and r.random() < 0.5:
            c['wood_boiler_sg'] = {'deployment': True}
    return c


def make(n, seed, out):
    import pandas as pd
    m = pd.read_feather(MASTER_DATA, columns=['EGID', 'GGDENR'])
    r = random.Random(seed)
    with open(out, 'w') as f:
        for i in range(n):
            c = rand_cfg(r)
            if 'meta_data' in c:
                a, b = r.sample([2762, 2765, 2701, 351, 448, 434], 2)
                eg = [int(e) for e in m.loc[m.GGDENR == a, 'EGID'].sample(300, random_state=i)] + \
                     [int(e) for e in m.loc[m.GGDENR == b, 'EGID'].sample(300, random_state=i)]
                c['meta_data']['custom_district']['EGID_List'] = eg
            f.write(f"fz{seed}_{i:03d}\t{json.dumps(c)}\t\n")


def check(prefix):
    import math
    stats = {'OK': 0, 'expected error': 0, 'UNEXPECTED ERROR': 0, 'OK but suspicious': 0}
    for f in sorted(glob.glob(f'{WORK}/results/{prefix}*.json')):
        d = json.load(open(f))
        if d['status'] != 'OK':
            err = d.get('error', '')
            if any(e in err for e in EXPECTED):
                stats['expected error'] += 1
            else:
                stats['UNEXPECTED ERROR'] += 1
                print('UNEXPECTED', d['name'], err[:200])
            continue
        issues = []
        ch = d.get('checks', {})
        if ch.get('nonfinite_cols') or ch.get('negative_cols'):
            issues.append(f"nonfinite={ch.get('nonfinite_cols')} negative={ch.get('negative_cols')}")
        a = d.get('annual', {})
        if a.get('d_h_unmet_yr', 0) > 1 or a.get('d_e_unmet_yr', 0) > 1:
            issues.append(f"unmet h={a.get('d_h_unmet_yr', 0):.0f} e={a.get('d_e_unmet_yr', 0):.0f}")
        c = d.get('costs') or {}
        k = c['Kostenmodul']['cost_overview'] if 'Kostenmodul' in c else c
        mon = (k.get('monetary') or {}).get('total') if isinstance(k, dict) else None
        if mon is not None and isinstance(mon, float) and math.isnan(mon):
            issues.append('NaN cost')
        o = d['config'].get('optimisation', {})
        if 'objective' in c and o.get('objective_co2', 0) == 0 and not o.get('pareto_monetary_co2'):
            obj = c['objective']['total']
            if abs(mon - obj) > max(0.01 * abs(obj), 100):
                issues.append(f'cost module {mon:.0f} != objective {obj:.0f}')
        if a and 'co2' in (k or {}) and abs(a.get('v_co2_tot_yr', 0) - k['co2']) > 1e-6 * max(1, abs(k['co2'])):
            issues.append(f"v_co2_tot {a.get('v_co2_tot_yr', 0):.0f} != {k['co2']:.0f}")
        if issues:
            stats['OK but suspicious'] += 1
            print('SUSPICIOUS', d['name'], '; '.join(issues)[:300])
        else:
            stats['OK'] += 1
    print(stats)


if __name__ == '__main__':
    if sys.argv[1] == 'make':
        make(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    else:
        check(sys.argv[2])
