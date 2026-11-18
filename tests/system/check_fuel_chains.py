"""
Biomass / gas / hydrogen / wood chain: conversion techs and the gas, hydrogen and wood storages.

    python check_fuel_chains.py run <prefix> <workers> [filter]  -> runs all cases (or those containing filter), results in _work/chain/<prefix>_<case>.json
    python check_fuel_chains.py check <prefix>            -> ratios, balances, supply limits, costs

Set DEM_SRC to test another checkout. Each case forces a part of the chain to run: gas techs with gas import off and a
fixed demand share of decentral gas boilers; CHPs with district heating on a fixed share and biomass as only source.
"""
import copy, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, run_env  # noqa: E402
OUT = f'{WORK}/chain'
OPT = {'enabled': True, 'solver_option_Threads': 4}

# short name -> (config key, primary input column, outputs/inputs to report relative to the primary input)
TECHS = {
    'hg': ('hydrothermal_gasification', 'u_wet_bm_hg', ['v_gas_hg']),
    'agu': ('anaerobic_digestion_upgrade', 'u_wet_bm_agu', ['v_gas_agu']),
    'aguh': ('anaerobic_digestion_upgrade_hydrogen', 'u_wet_bm_aguh', ['v_gas_aguh', 'u_hyd_aguh', 'u_e_aguh', 'v_h_aguh']),
    'aguc': ('anaerobic_digestion_chp', 'u_wet_bm_aguc', ['v_e_aguc', 'v_h_aguc']),
    'wgu': ('wood_gasification_upgrade', 'u_wd_wgu', ['v_gas_wgu', 'u_e_wgu', 'v_h_wgu']),
    'wguh': ('wood_gasification_upgrade_hydrogen', 'u_wd_wguh', ['v_gas_wguh', 'u_hyd_wguh', 'u_e_wguh', 'v_h_wguh']),
    'wguc': ('wood_gasification_chp', 'u_wd_wguc', ['v_e_wguc', 'v_h_wguc']),
    'hydp': ('hydrogen_production', 'u_e_hydp', ['v_hyd_hydp']),
}


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def dep(*names, **kw):
    c = {TECHS[n][0] if n in TECHS else n: {'deployment': True} for n in names}
    if any(n in ('aguh', 'wguh') for n in names):
        c['hydrogen_production'] = {'deployment': True}
    return merge(c, kw)


GAS = {'supply': {'gas_import': False}, 'gas_boiler': {'fixed_demand_share': True, 'fixed_demand_share_val': 0.005},
       'district_heating': {'heat_sources': {'biomass': True}}}  # biomass heat needs a sink
GAS_NO_BM_SINK = {'supply': {'gas_import': False}, 'gas_boiler': {'fixed_demand_share': True, 'fixed_demand_share_val': 0.005}}
CHP = {'district_heating': {'demand_share_type': 'fixed', 'demand_share_val': 0.004, 'heat_sources': {'import': False, 'biomass': True}}}
O = lambda **kw: {'optimisation': {**OPT, **kw}}

# name: (config, number_of_days)
CASES = {
    'gas_hg': (merge(dep('hg'), GAS, O()), 7),
    'gas_agu': (merge(dep('agu'), GAS, O()), 7),
    'gas_aguh': (merge(dep('aguh'), GAS, O()), 7),
    'gas_aguh_fluid': (merge(dep('aguh'), {'anaerobic_digestion_upgrade_hydrogen': {'fluid': True}}, GAS, O()), 7),
    'gas_wgu': (merge(dep('wgu'), GAS, O()), 7),
    'gas_wguh': (merge(dep('wguh'), GAS, O()), 7),
    'gas_wgu_eff05': (merge(dep('wgu'), {'wood_gasification_upgrade': {'efficiency': 0.5}}, GAS, O()), 7),
    'gas_all': (merge(dep('hg', 'agu', 'aguh', 'wgu', 'wguh'), GAS, O()), 7),
    'gas_all_365': (merge(dep('hg', 'agu', 'aguh', 'wgu', 'wguh'), GAS, O()), 365),
    'gas_all_scale10': (merge(dep('hg', 'agu', 'aguh', 'wgu', 'wguh'), GAS, O(calliope_energy_scaling_factor=10, solver_option_FeasibilityTol=1e-6)), 7),
    'gas_all_scale01': (merge(dep('hg', 'agu', 'aguh', 'wgu', 'wguh'), GAS, O(calliope_energy_scaling_factor=0.1, solver_option_FeasibilityTol=1e-6)), 7),
    'gas_all_tol6': (merge(dep('hg', 'agu', 'aguh', 'wgu', 'wguh'), GAS, O(solver_option_FeasibilityTol=1e-6)), 7),
    'gas_all_co2': (merge(dep('hg', 'agu', 'aguh', 'wgu', 'wguh'), GAS, O(objective_monetary=1e-5, objective_co2=1)), 7),
    'gas_hg_omcost': (merge(dep('hg'), {'hydrothermal_gasification': {'om_cost': 0.05}}, GAS, O()), 7),
    'gas_hg_cap': (merge(dep('hg'), {'hydrothermal_gasification': {'capacity_kWh': 50}}, GAS, O()), 7),
    'gas_wgu_nowoodimport': (merge(dep('wgu'), {'supply': {'wood_import': False}}, GAS, O()), 7),
    'gas_gtes': (merge(dep('hg', 'gtes'), GAS, O()), 7),
    'gas_import_on': (merge(dep('hg', 'agu', 'aguh', 'wgu', 'wguh'), {'gas_boiler': GAS['gas_boiler']}, O()), 7),
    'gas_bern': (merge(dep('hg', 'agu', 'aguh', 'wgu', 'wguh'), GAS, {'simulation': {'district_number': 351}}, O()), 7),
    'hyd_hes': (merge(dep('aguh', 'hes'), GAS, O()), 7),
    'wood_ws': (merge(dep('wgu', 'ws'), GAS, O()), 7),
    'gas_wgu_no_bm_sink': (merge(dep('wgu'), GAS_NO_BM_SINK, O()), 7),
    'gas_hg_too_much': (merge(dep('hg'), GAS, {'gas_boiler': {'fixed_demand_share_val': 0.1}}, O()), 7),
    'chp_aguc': (merge(dep('aguc'), CHP, O()), 7),
    'chp_wguc': (merge(dep('wguc'), CHP, O()), 7),
    'chp_both': (merge(dep('aguc', 'wguc'), CHP, O()), 7),
    'chp_aguc_noDH': (merge(dep('aguc'), O()), 7),
    'chp_wguc_noDH': (merge(dep('wguc'), O()), 7),
    'chp_aguc_cap': (merge(dep('aguc'), {'anaerobic_digestion_chp': {'capacity_kWh': 50}}, CHP, O()), 7),
    'everything': (merge(dep('hg', 'agu', 'aguh', 'aguc', 'wgu', 'wguh', 'wguc', 'gtes', 'hes', 'ws'), GAS, CHP, O()), 7),
}

RUN1 = r'''
import sys, json, io, contextlib, traceback
import numpy as np
name, cfg, days = sys.argv[1], json.loads(sys.argv[2]), int(sys.argv[3])
cfg.setdefault('simulation', {}).update(number_of_days=days, generate_plots=False, save_results=False)
cfg['simulation'].setdefault('district_number', 2762)
out = {'name': name, 'config': cfg, 'days': days}
try:
    from district_energy_model.model import launch
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        m = launch(root_dir='%s', config_files=False, config_dict=cfg, output_dir='%s/outputs/chain_' + name)
    out['costs'] = json.loads(json.dumps(m.total_cost(), default=str))
    df = m.hourly_results()
    pre = ('u_', 'v_', 'm_', 's_', 'q_', 'l_', 'd_')
    out['hourly'] = {c: [float(x) for x in df[c]] for c in df.columns
                     if c.startswith(pre) and any(k in c for k in ('gas', 'hyd', 'wd', 'bm', 'unmet', 'hydp', 'agu', 'wgu', 'hg'))}
    out['status'] = 'OK'
except BaseException as e:
    out['status'] = 'FAIL'; out['error'] = f'{type(e).__name__}: {e}'[:1500]; out['tb'] = traceback.format_exc()[-3000:]
json.dump(out, open('%s/' + name + '.json', 'w'), default=str)
print(name, out['status'], out.get('error', '')[:200], flush=True)
''' % (ROOT, WORK, OUT)


def run(prefix, workers, flt=''):
    os.makedirs(OUT, exist_ok=True)
    open(f'{OUT}/_run1.py', 'w').write(RUN1)
    env = run_env()
    def one(item):
        n, (c, days) = item
        return subprocess.run([PYTHON, f'{OUT}/_run1.py', f'{prefix}_{n}', json.dumps(c), str(days)],
                              capture_output=True, text=True, env=env).stdout.strip()
    items = sorted(((n, v) for n, v in CASES.items() if flt in n), key=lambda kv: -kv[1][1])
    with ThreadPoolExecutor(workers) as ex:
        for o in ex.map(one, items):
            print(o, flush=True)


def tot(h, prefix, exclude=('_kg',)):
    cols = [c for c in h if c.startswith(prefix) and not any(e in c for e in exclude)]
    return (sum(np.array(h[c]) for c in cols) if cols else 0), cols


def check(prefix):
    for n, (c, days) in CASES.items():
        f = f'{OUT}/{prefix}_{n}.json'
        if not os.path.exists(f):
            print(f'{n:22s} MISSING'); continue
        r = json.load(open(f))
        if r['status'] != 'OK':
            print(f'{n:22s} FAIL  {r["error"][:220]}'); continue
        h, issues, info = {k: np.array(v) for k, v in r['hourly'].items()}, [], []
        # observed ratios per tech (relative to the primary input), and their hourly constancy
        for short, (key, prim, flows) in TECHS.items():
            if key not in c or prim not in h or h[prim].sum() < 1:
                continue
            u = h[prim]; on = u > 1e-3 * u.max()
            rs = []
            for fl in flows:
                if fl not in h:
                    rs.append(f'{fl}:missing'); continue
                ratio = h[fl][on] / u[on]
                rs.append(f'{fl.split("_")[0]}_{fl.split("_")[1]}={h[fl].sum() / u.sum():.4f}')
                if ratio.max() - ratio.min() > 1e-4 * max(1, abs(ratio).max()):
                    issues.append(f'{short}: {fl}/{prim} not constant ({ratio.min():.4f}..{ratio.max():.4f})')
            info.append(f'{short}: in {u.sum():.0f} ' + ' '.join(rs))
            cap = c[key].get('capacity_kWh')
            if isinstance(cap, (int, float)):
                out = h[flows[0]]
                info.append(f'{short} max {flows[0]} {out.max():.1f} (cap {cap}), max input {u.max():.1f}')
                if out.max() > cap * (1 + 1e-6) + 1e-3:
                    issues.append(f'{short}: output {out.max():.1f} > capacity_kWh {cap}')
        # balances
        gp, gpc = tot(h, 'v_gas_'); gc, gcc = tot(h, 'u_gas_'); mg = h.get('m_gas', 0)
        e = np.abs(mg + gp - gc).max() if len(gpc) + len(gcc) else 0
        if e > 1e-2:
            issues.append(f'gas balance off by {e:.2f} kWh/h (m_gas + {gpc} vs {gcc})')
        if not c.get('supply', {}).get('gas_import', True) and np.sum(mg) > 1e-3:
            issues.append(f'gas imported ({np.sum(mg):.0f} kWh) although gas_import is False')
        hp, hpc = tot(h, 'v_hyd_'); hc, hcc = tot(h, 'u_hyd_')
        e = np.abs(hp - hc).max() if len(hpc) + len(hcc) else 0
        if e > 1e-2:
            issues.append(f'hydrogen balance off by {e:.2f} kWh/h ({hpc} vs {hcc})')
        wp = h.get('s_wd', 0) + h.get('m_wd', 0) + h.get('v_wd_ws', 0)
        wc, wcc = tot(h, 'u_wd_')
        e = np.abs(wp - wc).max() if len(wcc) else 0
        if e > 1e-2:
            issues.append(f'wood balance off by {e:.2f} kWh/h (s_wd + m_wd + v_wd_ws vs {wcc})')
        if not c.get('supply', {}).get('wood_import', True) and np.sum(h.get('m_wd', 0)) > 1e-3:
            issues.append(f'wood imported ({np.sum(h["m_wd"]):.0f} kWh) although wood_import is False')
        if 's_wd_pot' in h and (h.get('s_wd', 0) > h['s_wd_pot'] + 1e-2).any():
            issues.append('local wood above its potential')
        bc, bcc = tot(h, 'u_wet_bm_')
        if 's_wet_bm' in h:
            e = np.abs(h['s_wet_bm'] - bc).max() if len(bcc) else 0
            if e > 1e-2:
                issues.append(f'wet biomass balance off by {e:.2f} kWh/h')
            if (h['s_wet_bm'] > h['s_wet_bm_pot'] + 1e-2).any():
                issues.append('wet biomass above its potential')
        if 'v_h_bm' in h:
            parts = [k for k in ('v_h_aguh', 'v_h_aguc', 'v_h_wgu', 'v_h_wguh', 'v_h_wguc') if k in h]
            curt = h.get('v_h_bm_curt', 0)  # curtailed biomass heat (fix/biomass-heat-curtailment)
            e = np.abs(h['v_h_bm'] + curt - sum(h[k] for k in parts)).max() if parts else 0
            if e > 1e-2:
                issues.append(f'v_h_bm (+ v_h_bm_curt) != sum of biomass heat ({e:.2f} kWh/h)')
            if np.sum(curt) > 1:
                info.append(f'curtailed biomass heat {np.sum(curt):.0f}')
        info.append(f'gas: import {np.sum(mg):.0f} prod {np.sum(gp):.0f}; wood local {np.sum(h.get("s_wd", 0)):.0f} import {np.sum(h.get("m_wd", 0)):.0f}')
        # costs
        km, o = r['costs']['Kostenmodul'], c['optimisation']
        if 'objective' in r['costs'] and o.get('objective_monetary', 1) >= 1 and not o.get('objective_co2'):
            mon, obj = km['cost_overview']['monetary']['total'], r['costs']['objective']['total']
            if abs(mon - obj) > max(1e-4 * abs(obj), 10):
                issues.append(f'cost module {mon:.0f} != objective {obj:.0f}')
        for k in ['d_h_unmet', 'd_h_unmet_dhn', 'd_e_unmet']:
            if k in h and h[k].sum() > 1:
                issues.append(f'{k}={h[k].sum():.0f}')
        print(f'{n:22s} {"ISSUE " + "; ".join(issues) if issues else "ok"}  [{"; ".join(info)}]')


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else '')
    else:
        check(sys.argv[2])
