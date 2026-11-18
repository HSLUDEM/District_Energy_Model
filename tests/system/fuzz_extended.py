"""
Random combinations, extended: adds settings fuzz.py does not vary (energy scaling,
building-inertia and EV flexibility in optimisations, TES sites, waste heat with a
timeseries, central heat pump instances, grid limits, only_allow_existing, solver tolerance).

    python fuzz_extended.py make <n> <seed> <cases.txt>
    python fuzz.py check <prefix>      (same classification as fuzz.py)
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fuzz  # noqa: E402
from _common import INPUTS as I, MASTER_DATA, expand  # noqa: E402


def rand_cfg(r):
    c = fuzz.rand_cfg(r)
    o = c.get('optimisation')
    if not o:
        return c
    o['solver_option_FeasibilityTol'] = r.choice([1e-6, 1e-6, 1e-4])
    if r.random() < 0.4:
        o['calliope_energy_scaling_factor'] = r.choice([0.01, 0.1, 10.0, 1000.0])
    if r.random() < 0.3:
        ds = c.setdefault('demand_side', {})
        c['scenarios']['demand_side'] = True
        ds.setdefault('simulation_year', {'type': r.choice(['current', 'future']), 'future_year': r.choice([2030, 2050])})
        ds['dr_flexibility_building_inertia'] = True
        ds['ev_integration'] = r.random() < 0.6
        ds['ev_flexibility'] = ds['ev_integration'] and r.random() < 0.6
        if r.random() < 0.5:
            dh = c.setdefault('district_heating', {})
            dh['demand_share_type'] = 'min'; dh['demand_share_val'] = 0.1
    if r.random() < 0.15:
        ts = json.loads(expand(open(f'{I}/tes_sites_cfg.json').read()))
        ts.pop('simulation', None); ts.pop('optimisation', None)
        for k, v in ts.items():
            c[k] = {**c.get(k, {}), **v} if isinstance(v, dict) else v
        c['district_heating']['heat_sources'] = {**c.get('district_heating', {}).get('heat_sources', {}), 'oil_boiler_cp': True, 'heat_pump_cp_lt': True}
    if r.random() < 0.2:
        c['waste_heat'] = {'deployment': True, 'timeseries_file_path': f'{I}/wh.feather', 'tariff_CHFpkWh': r.choice([0.0, 0.02])}
        c.setdefault('district_heating', {}).setdefault('heat_sources', {})['waste_heat'] = True
    if r.random() < 0.15:
        c['heat_pump_cp'] = {'deployment': True, 'cop_mode': ['temperature_based', 'constant']}  # two instances
        c.setdefault('district_heating', {}).setdefault('heat_sources', {})['heat_pump_cp'] = True
    if r.random() < 0.15:
        c.setdefault('grid_supply', {})['kW_max'] = r.choice([5000, 20000])
    if r.random() < 0.1:
        c.setdefault('grid_export', {})['kW_max'] = r.choice([0, 1000])
    if r.random() < 0.15:
        c.setdefault(r.choice(['heat_pump', 'oil_boiler', 'gas_boiler']), {})['only_allow_existing'] = True
    if r.random() < 0.1:
        o['MIPGap_increase'] = True
    return c


def make(n, seed, out):
    import pandas as pd
    m = pd.read_feather(MASTER_DATA, columns=['EGID', 'GGDENR'])
    r = random.Random(1000 + seed)
    with open(out, 'w') as f:
        for i in range(n):
            c = rand_cfg(r)
            if 'meta_data' in c:
                a, b = r.sample([2762, 2765, 2701, 351, 448, 434], 2)
                eg = [int(e) for e in m.loc[m.GGDENR == a, 'EGID'].sample(300, random_state=i)] + \
                     [int(e) for e in m.loc[m.GGDENR == b, 'EGID'].sample(300, random_state=i)]
                c['meta_data']['custom_district']['EGID_List'] = eg
            f.write(f"fy{seed}_{i:03d}\t{json.dumps(c)}\t\n")


if __name__ == '__main__':
    make(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
