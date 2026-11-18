"""
Tests with time series inputs: waste heat (high and low temperature) and manual heat demand.

    python check_timeseries.py run <prefix> <workers> [filter]  -> runs all cases (or those containing filter), results in _work/ts/<prefix>_<case>.json
    python check_timeseries.py check <prefix>            -> checks every case against the input time series

Set DEM_SRC to test another checkout. The input files (inputs/ts/) have distinct hourly
values, so a time shift or a wrong scaling shows up in the hourly comparison.
"""
import copy, glob, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, run_env, expand  # noqa: E402
D = f'{T}/inputs/ts'
OUT = f'{WORK}/ts'
OPT = {'enabled': True, 'solver_option_Threads': 4}
OPT6 = {**OPT, 'solver_option_FeasibilityTol': 1e-6}
EGIDS = json.load(open(f'{T}/inputs/egids.txt')) if os.path.exists(f'{T}/inputs/egids.txt') else []


def WH(path, **kw):
    return {'waste_heat': {'deployment': True, 'timeseries_file_path': path, **kw},
            'district_heating': {'heat_sources': {'waste_heat': True}}}


def WHLT(path, **kw):
    return {'waste_heat_low_temperature': {'deployment': True, 'timeseries_file_path': path, **kw},
            'heat_pump_cp_lt': {'deployment': True},
            'district_heating': {'heat_sources': {'heat_pump_cp_lt': True}}}


def HDM(path=None, const=None):
    if const is not None:
        return {'heat_demand_manual': {'deployment': True, 'demand_mode': 'const', 'constant_value': const}}
    return {'heat_demand_manual': {'deployment': True, 'demand_mode': 'file', 'timeseries_file_path': path}}


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


TES_SITES = json.loads(expand(open(f'{T}/inputs/tes_sites_cfg.json').read()))
TES_SITES = {k: v for k, v in TES_SITES.items() if k not in ('simulation', 'optimisation', 'waste_heat_low_temperature')}
V, V2, H = f'{D}/wh_var.feather', f'{D}/wh2_var.feather', f'{D}/hdm_var.feather'

# name: (config, number_of_days)
CASES = {
    # --- waste heat ---
    'wh_opt': (merge(WH(V), {'optimisation': OPT}), 7),
    'wh_opt_free': (merge(WH(V, tariff_CHFpkWh=0.0), {'optimisation': OPT}), 7),
    'wh_opt_dhfixed': (merge(WH(V, tariff_CHFpkWh=0.0), {'district_heating': {'demand_share_type': 'fixed', 'demand_share_val': 0.02}}, {'optimisation': OPT}), 7),
    'wh_opt_co2': (merge(WH(V, co2_intensity=0.05, tariff_CHFpkWh=0.01), {'optimisation': OPT}), 7),
    'wh_list': (merge(WH([V, V2], tariff_CHFpkWh=[0.01, 0.0], capex=[0.0, 0.0], maintenance_cost=[0.0, 0.0], lifetime=[25, 25], co2_intensity=[0.0, 0.02], interest_rate=[0.025, 0.025]), {'optimisation': OPT}), 7),
    'wh_365': (merge(WH(V, tariff_CHFpkWh=0.0), {'optimisation': OPT}), 365),
    'wh_scale10': (merge(WH(V, tariff_CHFpkWh=0.0), {'optimisation': {**OPT6, 'calliope_energy_scaling_factor': 10}}), 7),
    'wh_scale01': (merge(WH(V, tariff_CHFpkWh=0.0), {'optimisation': {**OPT6, 'calliope_energy_scaling_factor': 0.1}}), 7),
    'wh_scale1': (merge(WH(V, tariff_CHFpkWh=0.0), {'optimisation': OPT6}), 7),
    'wh_sim': (WH(V), 7),
    'wh_csv': (merge(WH(f'{D}/wh_var.csv'), {'optimisation': OPT}), 7),
    'wh_nopath': (merge(WH(''), {'optimisation': OPT}), 7),
    'wh_short': (merge(WH(f'{D}/wh_short.feather'), {'optimisation': OPT}), 7),
    'wh_nan': (merge(WH(f'{D}/wh_nan.feather'), {'optimisation': OPT}), 7),
    'wh_neg': (merge(WH(f'{D}/wh_neg.feather'), {'optimisation': OPT}), 7),
    'wh_8784': (merge(WH(f'{D}/wh_8784.feather', tariff_CHFpkWh=0.0), {'optimisation': OPT}), 7),
    'wh_2cols': (merge(WH(f'{D}/wh_2cols.feather'), {'optimisation': OPT}), 7),
    'wh_tes_sites': (merge(WH(V, tariff_CHFpkWh=0.0), TES_SITES, {'optimisation': OPT}), 7),
    'wh_hpcp': (merge(WH(V, tariff_CHFpkWh=0.0), {'heat_pump_cp': {'instance_1': {'deployment': True}}, 'district_heating': {'heat_sources': {'heat_pump_cp': True}}}, {'optimisation': OPT}), 7),
    'wh_bern': (merge(WH(V, tariff_CHFpkWh=0.0), {'simulation': {'district_number': 351}}, {'optimisation': OPT}), 7),
    'wh_pareto': (merge(WH(V, tariff_CHFpkWh=0.0, co2_intensity=0.0), {'optimisation': {**OPT, 'pareto_monetary_co2': True, 'N_pareto': 3}}), 2),
    # --- low temperature waste heat ---
    'whlt_opt': (merge(WHLT(V, tariff_CHFpkWh=0.0), {'optimisation': OPT}), 7),
    'whlt_list': (merge(WHLT([V, V2], tariff_CHFpkWh=[0.0, 0.01], capex=[0.0, 0.0], maintenance_cost=[0.0, 0.0], lifetime=[25, 25], co2_intensity=[0.0, 0.0], interest_rate=[0.025, 0.025]), {'optimisation': OPT}), 7),
    'whlt_scale01': (merge(WHLT(V, tariff_CHFpkWh=0.0), {'optimisation': {**OPT6, 'calliope_energy_scaling_factor': 0.1}}), 7),
    'whlt_scale1': (merge(WHLT(V, tariff_CHFpkWh=0.0), {'optimisation': OPT6}), 7),
    'whlt_tes_sites': (merge(WHLT(V, tariff_CHFpkWh=0.0), TES_SITES, {'optimisation': OPT}), 7),
    'whlt_csv': (merge(WHLT(f'{D}/wh_var.csv'), {'optimisation': OPT}), 7),
    'wh_whlt': (merge(WH(V2, tariff_CHFpkWh=0.0), WHLT(V, tariff_CHFpkWh=0.0), {'optimisation': OPT}), 7),
    # --- manual heat demand ---
    'hdm_opt': (merge(HDM(H), {'optimisation': OPT}), 7),
    'hdm_sim': (HDM(H), 7),
    'hdm_opt_const': (merge(HDM(const=500.0), {'optimisation': OPT}), 7),
    'hdm_sim_const': (HDM(const=500.0), 7),
    'hdm_opt_npy': (merge(HDM(f'{D}/hdm_var.npy'), {'optimisation': OPT}), 7),
    'hdm_opt_short': (merge(HDM(f'{D}/hdm_short.feather'), {'optimisation': OPT}), 7),
    'hdm_opt_nan': (merge(HDM(f'{D}/hdm_nan.feather'), {'optimisation': OPT}), 7),
    'hdm_opt_neg': (merge(HDM(f'{D}/hdm_neg.feather'), {'optimisation': OPT}), 7),
    'hdm_opt_8784': (merge(HDM(f'{D}/hdm_8784.feather'), {'optimisation': OPT}), 7),
    'hdm_365': (merge(HDM(H), {'optimisation': OPT}), 365),
    'hdm_scale10': (merge(HDM(H), {'optimisation': {**OPT6, 'calliope_energy_scaling_factor': 10}}), 7),
    'hdm_scale01': (merge(HDM(H), {'optimisation': {**OPT6, 'calliope_energy_scaling_factor': 0.1}}), 7),
    'hdm_scale1': (merge(HDM(H), {'optimisation': OPT6}), 7),
    'hdm_ds_bi': (merge(HDM(H), {'scenarios': {'demand_side': True}, 'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050}, 'dr_flexibility_building_inertia': True, 'ev_integration': True, 'ev_flexibility': True}}, {'optimisation': OPT}), 7),
    'hdm_sim_scen': (merge(HDM(H), {'scenarios': {'demand_side': True, 'pv_integration': True, 'fossil_heater_retrofit': True}}), 7),
    'hdm_pareto': (merge(HDM(H), {'optimisation': {**OPT, 'pareto_monetary_co2': True, 'N_pareto': 3}}), 2),
    'hdm_tes': (merge(HDM(H), {'tes': {'deployment': True}, 'bes': {'deployment': True}}, {'optimisation': OPT}), 7),
    'hdm_bern': (merge(HDM(H), {'simulation': {'district_number': 351}}, {'optimisation': OPT}), 7),
    'hdm_noheatpump': (merge(HDM(H), {'heat_pump': {'deployment': False}}, {'optimisation': OPT}), 7),
    # --- both ---
    'hdm_wh': (merge(HDM(H), WH(V, tariff_CHFpkWh=0.0), {'optimisation': OPT}), 7),
    'hdm_wh_whlt': (merge(HDM(H), WH(V2, tariff_CHFpkWh=0.0), WHLT(V, tariff_CHFpkWh=0.0), {'optimisation': OPT}), 7),
    'hdm_wh_dhfixed': (merge(HDM(H), WH(V, tariff_CHFpkWh=0.0), {'district_heating': {'demand_share_type': 'fixed', 'demand_share_val': 0.02}}, {'optimisation': OPT}), 7),
    'hdm_wh_ds_cbc': (merge(HDM(H), WH(V, tariff_CHFpkWh=0.0), {'scenarios': {'demand_side': True}}, {'optimisation': {**OPT, 'solver': 'cbc'}}), 2),
}
if EGIDS:
    CASES['wh_custom'] = (merge(WH(V, tariff_CHFpkWh=0.0), {'meta_data': {'custom_district': {'implemented': True, 'EGID_List': EGIDS, 'custom_district_name': 'TS'}}}, {'optimisation': OPT}), 7)
    CASES['hdm_custom'] = (merge(HDM(H), {'meta_data': {'custom_district': {'implemented': True, 'EGID_List': EGIDS, 'custom_district_name': 'TS'}}}, {'optimisation': OPT}), 7)
# Reference runs without the time series technologies:
CASES['ref_opt'] = ({'optimisation': OPT}, 7)
CASES['ref_sim'] = ({}, 7)

RUN1 = r'''
import json, sys, io, contextlib, traceback
import numpy as np
name, cfg, days = sys.argv[1], json.loads(sys.argv[2]), int(sys.argv[3])
cfg.setdefault('simulation', {}).update(number_of_days=days, generate_plots=False, save_results=False)
cfg['simulation'].setdefault('district_number', 2762)
out = {'name': name, 'config': cfg, 'days': days}
COLS = ['v_h_wh', 'v_h_resource_wh', 'v_hlt_whlt', 'v_hlt_resource_whlt', 'd_h_m', 'd_h', 'd_h_unmet', 'd_h_unmet_dhn', 'd_e_unmet',
        'v_h_dh', 'm_h_dh', 'v_h_hpcplt', 'v_co2_wh', 'v_co2_whlt']
try:
    from district_energy_model.model import launch
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        m = launch(root_dir='%s', config_files=False, config_dict=cfg, output_dir='%s/outputs/ts_' + name)
    out['annual'] = {k: float(v) for k, v in m.annual_results().items() if isinstance(v, (int, float, np.integer, np.floating))}
    out['costs'] = json.loads(json.dumps(m.total_cost(), default=str))
    df = m.hourly_results()
    out['hourly'] = {c: [float(x) for x in df[c]] for c in COLS if c in df.columns}
    out['hourly_cols'] = [c for c in df.columns if 'wh' in c or 'whlt' in c or c.startswith('d_h')]
    if getattr(m, 'pareto_results', None):
        out['pareto_n'] = len(m.pareto_results)
    out['warnings'] = [l for l in log.getvalue().splitlines() if 'WARNING' in l.upper() and 'FutureWarning' not in l][:5]
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
        n, (cfg, days) = item
        return subprocess.run([PYTHON, f'{OUT}/_run1.py', f'{prefix}_{n}', json.dumps(cfg), str(days)],
                              capture_output=True, text=True, env=env).stdout.strip()
    # long runs first
    items = sorted(((n, v) for n, v in CASES.items() if flt in n), key=lambda kv: -kv[1][1])
    with ThreadPoolExecutor(workers) as ex:
        for o in ex.map(one, items):
            print(o, flush=True)


def series(path, n):
    import pandas as pd
    if path.endswith('.npy'):
        return np.load(path)[:n]
    return pd.read_feather(path).to_numpy()[:n, 0].astype(float)


def check(prefix):
    R = {n: json.load(open(f)) for n in CASES for f in [f'{OUT}/{prefix}_{n}.json'] if os.path.exists(f)}
    for n, (cfg, days) in CASES.items():
        r = R.get(n)
        if r is None:
            print(f'{n:16s} MISSING'); continue
        if r['status'] != 'OK':
            print(f'{n:16s} FAIL  {r["error"][:180]}'); continue
        nh = days * 24
        h, a, issues, info = r['hourly'], r['annual'], [], []
        c = r['costs']
        km = c.get('Kostenmodul', c)
        # unmet demand
        for k in ['d_h_unmet', 'd_h_unmet_dhn', 'd_e_unmet']:
            if k in h and sum(h[k]) > 1:
                issues.append(f'{k}={sum(h[k]):.0f}')
        # cost module vs objective (monetary objective only)
        o = cfg.get('optimisation', {})
        if 'objective' in c and not o.get('objective_co2') and not o.get('pareto_monetary_co2'):
            mon, obj = km['cost_overview']['monetary']['total'], c['objective']['total']
            if abs(mon - obj) > max(1e-4 * abs(obj), 10):
                issues.append(f'cost module {mon:.0f} != objective {obj:.0f}')
        # waste heat (high and low temperature)
        for key, col, rcol in [('waste_heat', 'v_h_wh', 'v_h_resource_wh'), ('waste_heat_low_temperature', 'v_hlt_whlt', 'v_hlt_resource_whlt')]:
            w = cfg.get(key)
            if not w:
                continue
            paths = w['timeseries_file_path'] if isinstance(w['timeseries_file_path'], list) else [w['timeseries_file_path']]
            try:
                exp = sum(series(p, nh) for p in paths)
            except Exception as e:
                exp = None; info.append(f'{key}: file not readable by test ({type(e).__name__})')
            if col not in h:
                issues.append(f'{col} missing'); continue
            used, res = np.array(h[col]), np.array(h.get(rcol, [np.nan] * nh))
            if exp is not None and len(exp) == nh:
                if not np.allclose(res, exp, rtol=1e-9, atol=1e-6, equal_nan=True):
                    i = int(np.nanargmax(np.abs(res - exp))) if np.isfinite(res - exp).any() else 0
                    issues.append(f'{rcol} != file (h{i}: {res[i]:.1f} vs {exp[i]:.1f}; sums {np.nansum(res):.0f} vs {np.nansum(exp):.0f})')
            if np.any(used > res + 1e-3 + 1e-6 * np.abs(res)):
                i = int(np.argmax(used - res)); issues.append(f'{col} > resource (h{i}: {used[i]:.1f} > {res[i]:.1f})')
            if np.any(~np.isfinite(used)) or np.any(used < -1e-3):
                issues.append(f'{col} nonfinite/negative')
            info.append(f'{col} used {used.sum():.0f} of {np.nansum(res):.0f} kWh')
            # cost and CO2 per kWh used
            tariffs = w.get('tariff_CHFpkWh'); tariffs = tariffs if isinstance(tariffs, list) else [tariffs]
            co2s = w.get('co2_intensity', 0.0); co2s = co2s if isinstance(co2s, list) else [co2s]
            if len(paths) == 1 and tariffs[0] is not None:
                mb = km.get('monetary_breakdown', {}).get(key, {})
                ec = mb.get('energy_costs') if isinstance(mb, dict) else None
                if ec is not None and abs(ec - tariffs[0] * used.sum()) > max(1e-6 * abs(ec), 0.01):
                    issues.append(f'{key} energy_costs {ec:.2f} != tariff*use {tariffs[0]*used.sum():.2f}')
                cc = 'v_co2_wh' if key == 'waste_heat' else 'v_co2_whlt'
                if cc in h and abs(sum(h[cc]) - co2s[0] * used.sum()) > 1e-6 * max(1, used.sum()):
                    issues.append(f'{cc} {sum(h[cc]):.1f} != intensity*use {co2s[0]*used.sum():.1f}')
        # manual heat demand
        hd = cfg.get('heat_demand_manual')
        if hd:
            if hd['demand_mode'] == 'const':
                exp = np.full(nh, hd['constant_value'])
            else:
                try:
                    exp = series(hd['timeseries_file_path'], nh)
                except Exception:
                    exp = None
            if 'd_h_m' not in h:
                issues.append('d_h_m missing')
            elif exp is not None and len(exp) == nh:
                got = np.array(h['d_h_m'])
                if not np.allclose(got, exp, rtol=1e-6, atol=1e-3, equal_nan=True):
                    ratio = np.nansum(got) / np.nansum(exp) if np.nansum(exp) else float('nan')
                    i = int(np.nanargmax(np.abs(got - exp)))
                    issues.append(f'd_h_m != input (h{i}: {got[i]:.1f} vs {exp[i]:.1f}; sum ratio {ratio:.4g})')
                info.append(f'd_h_m {np.nansum(got):.0f} kWh')
        if r.get('warnings'):
            info.append('warnings: ' + ' | '.join(w[:100] for w in r['warnings']))
        print(f'{n:16s} {"ISSUE" if issues else "ok   "} {"; ".join(issues)}  [{"; ".join(info)}]')


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else '')
    else:
        check(sys.argv[2])
