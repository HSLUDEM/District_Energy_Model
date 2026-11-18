"""
Does each numeric input parameter have any effect?

    python param_effect.py make <cases.txt>   -> case file (run with: python param_effect.py run <cases.txt> <workers>)
    python param_effect.py check              -> list parameters whose change leaves every result unchanged

Every numeric leaf of scen_techs is changed (x1.5; x0.8 for values in (0, 1]; 0 -> 0.1) in two contexts:
SIMB (base simulation), SIM (simulation with all manual scenarios) and OPT (optimisation with the parameter's
technology deployed and, if applicable, connected to district heating).
Results compared: all annual results, the full cost module output and hourly column sums.
"""
import copy, glob, json, numbers, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, MASTER_DATA, run_env  # noqa: E402
OUT = f'{WORK}/param_effect'
DAYS = 3
SIM = {'scenarios': {'demand_side': True, 'fossil_heater_retrofit': True, 'pv_integration': True, 'wind_integration': True,
                     'nuclear_phaseout': True, 'thermal_energy_storage': True},
       'tes_decentralised': {'deployment': True},
       'thermal_energy_storage_scenario': {'capacity_kWh': 1e5, 'initial_charge': 0.5},
       'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050}, 'ev_integration': True}}
DH_SRC = ['chp_gt', 'steam_turbine', 'waste_to_energy', 'heat_pump_cp_lt', 'oil_boiler_cp', 'electric_heater_cp',
          'wood_boiler_cp', 'gas_boiler_cp', 'deep_geothermal', 'waste_heat']
BIOMASS = ['hydrothermal_gasification', 'anaerobic_digestion_upgrade', 'anaerobic_digestion_upgrade_hydrogen',
           'anaerobic_digestion_chp', 'wood_gasification_upgrade', 'wood_gasification_upgrade_hydrogen',
           'wood_gasification_chp', 'hydrogen_production']


def opt_ctx(sec, defaults):
    c = {'optimisation': {'enabled': True, 'solver_option_Threads': 2}}
    d = defaults.get(sec)
    if isinstance(d, dict) and d.get('deployment') is False:
        c[sec] = {'deployment': True}
    # Force the technology to run where possible: district heating supplies a fixed
    # share with the technology as only source; decentral heaters a fixed share.
    dh_fixed = {'demand_share_type': 'fixed', 'demand_share_val': 0.3}
    if sec in DH_SRC:
        c['district_heating'] = {**dh_fixed, 'heat_sources': {'import': False, sec: True}}
    if sec == 'district_heating':
        c['district_heating'] = dict(dh_fixed)
    if sec in ['oil_boiler', 'gas_boiler', 'wood_boiler', 'electric_heater', 'heat_pump']:
        c[sec] = {'fixed_demand_share': True, 'fixed_demand_share_val': 0.2}
    if sec in BIOMASS:
        c['district_heating'] = {'heat_sources': {'biomass': True}}
        if 'hydrogen' in sec and sec != 'hydrogen_production':
            c['hydrogen_production'] = {'deployment': True}
            c['hes'] = {'deployment': True}
    if sec == 'steam_turbine':
        c['wood_boiler_sg'] = {'deployment': True}
    if sec == 'wood_boiler_sg':
        c['steam_turbine'] = {'deployment': True}
        c['district_heating'] = {'heat_sources': {'steam_turbine': True}}
    if sec == 'tes_decentralised':
        c['scenarios'] = {'thermal_energy_storage': False}
    return c


def leaves(d, p=()):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from leaves(v, p + (k,))
        elif isinstance(v, numbers.Number) and not isinstance(v, bool):
            yield p + (k,), v


def setp(c, path, v):
    for k in path[:-1]:
        c = c.setdefault(k, {})
    c[path[-1]] = v


def merge(a, b):
    out = copy.deepcopy(a)
    for k, v in b.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


SKIP = {('simulation', 'number_of_days'), ('simulation', 'district_number'), ('optimisation', 'solver_option_Threads'),
        ('optimisation', 'solver_option_TimeLimit')}


def make(fn):
    from district_energy_model.input_files.inputs import scen_techs as D
    cases, bases = [], {}
    for path, v in leaves(D):
        if path in SKIP or path[0] == 'meta_data' or path[1:2] == ('fixed_demand_share_val',):
            continue
        nv = v * 1.5 if v != 0 else 0.1
        if 0 < v <= 1:
            nv = v * 0.8
        if isinstance(v, int) and v != 0:
            nv = int(round(v * 1.5)) if abs(v) > 1 else v + 1
        for ctx_name, ctx in (('SIMB', {}), ('SIM', SIM), ('OPT', opt_ctx(path[0], D))):
            key = ctx_name + ':' + json.dumps(ctx, sort_keys=True)
            if key not in bases:
                bases[key] = f'base{len(bases):03d}_{ctx_name}'
                cases.append((bases[key], ctx))
            c = copy.deepcopy(ctx)
            setp(c, path, nv)
            cases.append((f"p_{ctx_name}_{'.'.join(path)}", merge(ctx, c), bases[key]))
    with open(fn, 'w') as f:
        for c in cases:
            f.write('\t'.join([c[0], json.dumps(c[1])] + ([c[2]] if len(c) > 2 else [])) + '\n')
    print(len(cases), 'cases', len(bases), 'bases')


RUN1 = r'''
import json, sys, io, contextlib, traceback
import numpy as np
name, cfg = sys.argv[1], json.loads(sys.argv[2])
cfg.setdefault('simulation', {}).update(number_of_days=%d, generate_plots=False, save_results=False)
out = {'name': name, 'config': cfg}
try:
    from district_energy_model.model import launch
    with contextlib.redirect_stdout(io.StringIO()):
        m = launch(root_dir='%s', config_files=False, config_dict=cfg, output_dir='%s/outputs/pe_' + name)
    out['annual'] = {k: float(v) for k, v in m.annual_results().items() if isinstance(v, (int, float, np.integer, np.floating))}
    out['costs'] = json.loads(json.dumps(m.total_cost(), default=str))
    df = m.hourly_results().select_dtypes('number')
    out['hourly_sums'] = {c: float(df[c].sum()) for c in df.columns}
    out['status'] = 'OK'
except BaseException as e:
    out['status'] = 'FAIL'; out['error'] = f'{type(e).__name__}: {e}'[:1500]; out['tb'] = traceback.format_exc()[-3000:]
json.dump(out, open('%s/' + name + '.json', 'w'), default=str)
print(name, out['status'], out.get('error', '')[:200], flush=True)
''' % (DAYS, ROOT, WORK, OUT)


def run(fn, workers):
    os.makedirs(OUT, exist_ok=True)
    open(f'{OUT}/_run1.py', 'w').write(RUN1)
    cases = [l.rstrip('\n').split('\t') for l in open(fn) if l.strip()]
    env = run_env()
    def one(c):
        return subprocess.run([PYTHON, f'{OUT}/_run1.py', c[0], c[1]],
                              capture_output=True, text=True, env=env).stdout.strip()
    with ThreadPoolExecutor(workers) as ex:
        for o in ex.map(one, cases):
            print(o, flush=True)


def flat(d, p=''):
    if isinstance(d, dict):
        for k, v in d.items():
            yield from flat(v, f'{p}.{k}' if p else str(k))
    elif isinstance(d, (int, float)) and not isinstance(d, bool):
        yield p, float(d)


def check(fn):
    cases = [l.rstrip('\n').split('\t') for l in open(fn) if l.strip()]
    res = {}
    for c in cases:
        f = f'{OUT}/{c[0]}.json'
        res[c[0]] = json.load(open(f)) if os.path.exists(f) else {'status': 'MISSING'}
    noeffect = {}
    for c in cases:
        if len(c) < 3:
            continue
        r, b = res[c[0]], res[c[2]]
        _, ctx, par = c[0].split('_', 2)
        if r['status'] != 'OK' or b['status'] != 'OK':
            print('FAIL', c[0], r.get('error', '')[:150], '| base', b['status'])
            continue
        fr, fb = dict(flat({k: r[k] for k in ('annual', 'costs', 'hourly_sums')})), dict(flat({k: b[k] for k in ('annual', 'costs', 'hourly_sums')}))
        diff = [k for k in set(fr) | set(fb) if abs(fr.get(k, 0) - fb.get(k, 0)) > 1e-9 * max(1, abs(fb.get(k, 0)))]
        noeffect.setdefault(par, {})[ctx] = len(diff)
    print('\nParameters without any effect (SIM / OPT number of changed outputs):')
    for p, d in sorted(noeffect.items()):
        if all(v == 0 for v in d.values()):
            print(' ', p, d)


if __name__ == '__main__':
    {'make': lambda: make(sys.argv[2]), 'run': lambda: run(sys.argv[2], int(sys.argv[3])),
     'check': lambda: check(sys.argv[2])}[sys.argv[1]]()
