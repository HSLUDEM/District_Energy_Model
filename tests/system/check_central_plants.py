"""
Central plants connected to district heating: boilers (oil, gas, wood, electric), wood boiler with steam generator,
gas turbine, steam turbine, CHP gas turbine, waste to energy, deep geothermal.

    python check_central_plants.py run <prefix> <workers> [filter]  -> runs all cases (or those containing filter), results in _work/cplant/<prefix>_<case>.json
    python check_central_plants.py check <prefix>            -> ratios, capacity limits, minimum use, steam / heat splits, costs

Set DEM_SRC to test another checkout. Each case forces the plant(s) to run: district heating supplies a fixed share of
the heat demand with the tested plant(s) as only source (import off).
"""
import copy, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, run_env  # noqa: E402
OUT = f'{WORK}/cplant'
OPT = {'enabled': True, 'solver_option_Threads': 4}

DEFAULTS = {
    'oil_boiler_cp': {'eta': 0.85}, 'gas_boiler_cp': {'eta': 0.9}, 'wood_boiler_cp': {'eta': 0.85},
    'electric_heater_cp': {'eta': 0.98}, 'wood_boiler_sg': {'eta': 0.8, 'kW_h_max': 'inf', 'cap_min_use': 0.0},
    'chp_gt': {'eta_el': 0.35, 'htp_ratio': 1.5, 'kW_el_max': 'inf'},
    'gas_turbine_cp': {'eta_el': 0.35, 'htp_ratio': 1.5, 'kW_el_max': 'inf', 'cap_min_use': 0.0},
    'steam_turbine': {'eta_el': 0.35, 'htp_ratio': 1.5, 'kW_el_max': 'inf', 'cap_min_use': 0.0},
    'waste_to_energy': {'eta_el': 0.35, 'htp_ratio': 1.5, 'kW_el_max': 'inf', 'cap_min_use': 0.0},
    'deep_geothermal': {'capex': 25000.0},
}
# key -> (input column, [(output column, expected ratio to the input as function of the parameters)], capacity column, capacity key)
PLANTS = {
    'oil_boiler_cp': ('u_oil_obcp', [('v_h_obcp', lambda p: p['eta'])], 'v_h_obcp', 'kW_th_max'),
    'gas_boiler_cp': ('u_gas_gbcp', [('v_h_gbcp', lambda p: p['eta'])], 'v_h_gbcp', 'kW_th_max'),
    'wood_boiler_cp': ('u_wd_wbcp', [('v_h_wbcp', lambda p: p['eta'])], 'v_h_wbcp', 'kW_th_max'),
    'electric_heater_cp': ('u_e_ehcp', [('v_h_ehcp', lambda p: p['eta'])], 'v_h_ehcp', 'kW_th_max'),
    'wood_boiler_sg': ('u_wd_wbsg', [('v_steam_wbsg', lambda p: p['eta'])], 'v_steam_wbsg', 'kW_h_max'),
    'chp_gt': ('u_gas_chpgt', [('v_e_chpgt', lambda p: p['eta_el']), ('v_h_chpgt', lambda p: p['eta_el'] * p['htp_ratio'])], 'v_e_chpgt', 'kW_el_max'),
    'gas_turbine_cp': ('u_gas_gtcp', [('v_e_gtcp', lambda p: p['eta_el']), ('v_steam_gtcp', lambda p: p['eta_el'] * p['htp_ratio'])], 'v_e_gtcp', 'kW_el_max'),
    'steam_turbine': ('u_steam_st', [('v_e_st', lambda p: p['eta_el']), ('v_h_st', lambda p: p['eta_el'] * p['htp_ratio'])], 'v_e_st', 'kW_el_max'),
    'waste_to_energy': ('u_msw_wte', [('v_e_wte', lambda p: p['eta_el']), ('v_h_wte', lambda p: p['eta_el'] * p['htp_ratio'])], 'v_e_wte', 'kW_el_max'),
    'deep_geothermal': (None, [], 'v_h_dgt', 'kW_th_max'),
}
DH_KEY = {'oil_boiler_cp': 'oil_boiler_cp', 'gas_boiler_cp': 'gas_boiler_cp', 'wood_boiler_cp': 'wood_boiler_cp',
          'electric_heater_cp': 'electric_heater_cp', 'chp_gt': 'chp_gt', 'steam_turbine': 'steam_turbine',
          'waste_to_energy': 'waste_to_energy', 'deep_geothermal': 'deep_geothermal'}


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def force(*techs, share=0.1, **kw):
    """District heating supplies a fixed share with the given plants as only source."""
    c = {t: {'deployment': True} for t in techs}
    srcs = {DH_KEY[t]: True for t in techs if t in DH_KEY}
    c['district_heating'] = {'demand_share_type': 'fixed', 'demand_share_val': share, 'heat_sources': {'import': False, **srcs}}
    if 'waste_to_energy' in techs:
        c['supply'] = {'annual_msw_supply': 1e7}
    return merge(c, kw, {'optimisation': OPT})


O = lambda **kw: {'optimisation': {**OPT, **kw}}

# name: (config, number_of_days)
CASES = {
    'obcp': (force('oil_boiler_cp'), 7),
    'gbcp': (force('gas_boiler_cp'), 7),
    'wbcp': (force('wood_boiler_cp'), 7),
    'ehcp': (force('electric_heater_cp'), 7),
    'obcp_eta07': (force('oil_boiler_cp', oil_boiler_cp={'deployment': True, 'eta': 0.7}), 7),
    'obcp_cap': (force('oil_boiler_cp', share=0.05, oil_boiler_cp={'deployment': True, 'kW_th_max': 300}, gas_boiler_cp={'deployment': True},
                       district_heating={'heat_sources': {'gas_boiler_cp': True}}), 7),
    'chpgt': (force('chp_gt'), 7),
    'chpgt_noexport': (force('chp_gt', chp_gt={'deployment': True, 'allow_heat_export': False}), 7),
    'chpgt_cap': (force('chp_gt', 'gas_boiler_cp', chp_gt={'deployment': True, 'kW_el_max': 100}), 7),
    'chpgt_forcecap': (force('chp_gt', 'gas_boiler_cp', chp_gt={'deployment': True, 'kW_el_max': 100, 'force_cap_max': True}), 7),
    'chpgt_forcecap_scale10': (merge(force('chp_gt', 'gas_boiler_cp', chp_gt={'deployment': True, 'kW_el_max': 100, 'force_cap_max': True}),
                                     O(calliope_energy_scaling_factor=10, solver_option_FeasibilityTol=1e-6)), 7),
    'chpgt_forcecap_scale01': (merge(force('chp_gt', 'gas_boiler_cp', chp_gt={'deployment': True, 'kW_el_max': 100, 'force_cap_max': True}),
                                     O(calliope_energy_scaling_factor=0.1, solver_option_FeasibilityTol=1e-6)), 7),
    'wbsg_forcecap_inf': (force('wood_boiler_sg', 'steam_turbine', wood_boiler_sg={'deployment': True, 'force_cap_max': True}), 7),
    'chpgt_htp2': (force('chp_gt', chp_gt={'deployment': True, 'htp_ratio': 2.0, 'eta_el': 0.3}), 7),
    'gtcp_st': (force('gas_turbine_cp', 'steam_turbine'), 7),
    'gtcp_st_minuse': (force('gas_turbine_cp', 'steam_turbine', 'gas_boiler_cp', gas_turbine_cp={'deployment': True, 'kW_el_max': 500, 'force_cap_max': True, 'cap_min_use': 0.5}), 7),
    'wbsg_st': (force('wood_boiler_sg', 'steam_turbine'), 7),
    'wbsg_st_free': (force('wood_boiler_sg', 'steam_turbine', wood_boiler_sg={'deployment': True, 'wood_input_cap_type': 'free'}), 7),
    'wbsg_st_max': (force('wood_boiler_sg', 'steam_turbine', 'gas_boiler_cp', wood_boiler_sg={'deployment': True, 'wood_input_cap_type': 'max', 'wood_input_cap_kg': 1e6}), 7),
    'wbsg_st_fixed': (force('wood_boiler_sg', 'steam_turbine', 'gas_boiler_cp', wood_boiler_sg={'deployment': True, 'wood_input_cap_type': 'fixed', 'wood_input_cap_kg': 1e6}), 7),
    'wbsg_st_cap': (force('wood_boiler_sg', 'steam_turbine', 'gas_boiler_cp', wood_boiler_sg={'deployment': True, 'kW_h_max': 500}), 7),
    'st_noexport': (force('wood_boiler_sg', 'steam_turbine', steam_turbine={'deployment': True, 'allow_heat_export': False}), 7),
    'st_minuse': (force('wood_boiler_sg', 'steam_turbine', 'gas_boiler_cp', steam_turbine={'deployment': True, 'kW_el_max': 300, 'force_cap_max': True, 'cap_min_use': 0.8}), 7),
    'gtcp_wbsg_st': (force('gas_turbine_cp', 'wood_boiler_sg', 'steam_turbine'), 7),
    'wte': (force('waste_to_energy'), 7),
    'wte_cap': (force('waste_to_energy', 'gas_boiler_cp', waste_to_energy={'deployment': True, 'kW_el_max': 100}), 7),
    'dgt': (force('deep_geothermal'), 7),
    'dgt_capex_low': (force('deep_geothermal', 'gas_boiler_cp', share=0.5, deep_geothermal={'deployment': True, 'capex': 500.0}), 7),
    'dgt_capex_high': (force('deep_geothermal', 'gas_boiler_cp', share=0.5, deep_geothermal={'deployment': True, 'capex': 50000.0}), 7),
    'dgt_cap': (force('deep_geothermal', 'gas_boiler_cp', share=0.5, deep_geothermal={'deployment': True, 'kW_th_max': 1000}), 7),
    'dgt_zuerich': (force('deep_geothermal', 'gas_boiler_cp', share=0.5, simulation={'district_number': 261}), 7),
    'all_cp': (force('oil_boiler_cp', 'gas_boiler_cp', 'wood_boiler_cp', 'electric_heater_cp', 'chp_gt', 'gas_turbine_cp',
                     'steam_turbine', 'wood_boiler_sg', 'waste_to_energy', 'deep_geothermal', share=0.3), 7),
    'all_cp_365': (force('oil_boiler_cp', 'gas_boiler_cp', 'wood_boiler_cp', 'electric_heater_cp', 'chp_gt', 'gas_turbine_cp',
                         'steam_turbine', 'wood_boiler_sg', 'waste_to_energy', share=0.3), 365),
    'all_cp_scale10': (merge(force('oil_boiler_cp', 'gas_boiler_cp', 'chp_gt', 'gas_turbine_cp', 'steam_turbine', 'wood_boiler_sg', share=0.3),
                             O(calliope_energy_scaling_factor=10, solver_option_FeasibilityTol=1e-6)), 7),
    'all_cp_scale01': (merge(force('oil_boiler_cp', 'gas_boiler_cp', 'chp_gt', 'gas_turbine_cp', 'steam_turbine', 'wood_boiler_sg', share=0.3),
                             O(calliope_energy_scaling_factor=0.1, solver_option_FeasibilityTol=1e-6)), 7),
    'all_cp_co2': (merge(force('oil_boiler_cp', 'gas_boiler_cp', 'wood_boiler_cp', 'electric_heater_cp', 'chp_gt', share=0.3),
                         O(objective_monetary=1e-5, objective_co2=1)), 7),
    'all_cp_bern': (force('oil_boiler_cp', 'gas_boiler_cp', 'chp_gt', 'gas_turbine_cp', 'steam_turbine', 'wood_boiler_sg', share=0.3,
                          simulation={'district_number': 351}), 7),
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
        m = launch(root_dir='%s', config_files=False, config_dict=cfg, output_dir='%s/outputs/cplant_' + name)
    out['costs'] = json.loads(json.dumps(m.total_cost(), default=str))
    df = m.hourly_results()
    pat = ['obcp', 'gbcp', 'wbcp', 'ehcp', 'wbsg', 'chpgt', 'gtcp', '_st', 'wte', 'dgt', 'steam', 'msw', 'unmet', 'v_h_dh', 'm_h_dh']
    out['hourly'] = {c: [float(x) for x in df[c]] for c in df.columns if any(p in c for p in pat)}
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
        n, (c, days) = item
        return subprocess.run([PYTHON, f'{OUT}/_run1.py', f'{prefix}_{n}', json.dumps(c), str(days)],
                              capture_output=True, text=True, env=env).stdout.strip()
    items = sorted(((n, v) for n, v in CASES.items() if flt in n), key=lambda kv: -kv[1][1])
    with ThreadPoolExecutor(workers) as ex:
        for o in ex.map(one, items):
            print(o, flush=True)


def check(prefix):
    for n, (c, days) in CASES.items():
        f = f'{OUT}/{prefix}_{n}.json'
        if not os.path.exists(f):
            print(f'{n:16s} MISSING'); continue
        r = json.load(open(f))
        if r['status'] != 'OK':
            print(f'{n:16s} FAIL  {r["error"][:220]}'); continue
        h, issues, info = {k: np.array(v) for k, v in r['hourly'].items()}, [], []
        z = np.zeros(days * 24)
        for key, (inp, outs, capcol, capkey) in PLANTS.items():
            if key not in c:
                continue
            p = {**DEFAULTS.get(key, {}), **c[key]}
            if inp is not None and inp in h and h[inp].sum() > 1:
                u = h[inp]; on = u > 1e-3 * u.max()
                rs = []
                for col, fn in outs:
                    exp = fn(p)
                    ratio = h[col][on] / u[on]
                    rs.append(f'{col}={h[col].sum() / u.sum():.4f}')
                    if np.abs(ratio - exp).max() > 1e-4:
                        issues.append(f'{key}: {col}/{inp} = {ratio.min():.4f}..{ratio.max():.4f}, expected {exp:.4f}')
                info.append(f'{key}: in {u.sum():.0f} ' + ' '.join(rs))
            elif capcol in h:
                info.append(f'{key}: {capcol} {h[capcol].sum():.0f} (max {h[capcol].max():.1f})')
            cap = p.get(capkey, 'inf')
            if capcol in h and cap != 'inf':
                mx = h[capcol].max()
                info.append(f'{key} max {capcol} {mx:.1f} (cap {cap})')
                if mx > cap * (1 + 1e-6) + 1e-3:
                    issues.append(f'{key}: {capcol} max {mx:.1f} > {capkey} {cap}')
                if p.get('force_cap_max') and p.get('cap_min_use', 0) > 0:
                    low = h[capcol].min()
                    if low < p['cap_min_use'] * cap * (1 - 1e-6) - 1e-3:
                        issues.append(f'{key}: {capcol} min {low:.1f} < cap_min_use x cap {p["cap_min_use"] * cap:.1f}')
            if key == 'wood_boiler_sg' and p.get('wood_input_cap_type', 'free') != 'free':
                kWh = p['wood_input_cap_kg'] * 15.0 / 3.6
                kW = kWh / 8760
                u = h.get('u_wd_wbsg', z)
                info.append(f'wbsg wood max {u.max():.1f} kW (annual cap -> {kW:.1f} kW)')
                if u.max() > kW * (1 + 1e-4) + 1e-3:
                    issues.append(f'wbsg wood input {u.max():.1f} kW > annual cap / 8760 = {kW:.1f} kW')
                if p['wood_input_cap_type'] == 'fixed' and np.abs(u - kW).max() > 1e-2 * kW:
                    info.append(f'wbsg fixed: wood input {u.min():.1f}..{u.max():.1f} kW (cap {kW:.1f})')
        # heat splits and steam balance
        for tot, con, waste in [('v_h_chpgt', 'v_h_chpgt_con', 'v_h_chpgt_waste'), ('v_h_st', 'v_h_st_con', 'v_h_st_waste'),
                                ('v_h_wte', 'v_h_wte_con', 'v_h_wte_waste')]:
            if tot in h and con in h and waste in h:
                e = np.abs(h[tot] - h[con] - h[waste]).max()
                if e > 1e-2:
                    issues.append(f'{tot} != {con} + {waste} ({e:.2f})')
                if h[waste].sum() > 1:
                    info.append(f'{waste} {h[waste].sum():.0f}')
                    key = {'v_h_chpgt': 'chp_gt', 'v_h_st': 'steam_turbine', 'v_h_wte': 'waste_to_energy'}[tot]
                    if key in c and c[key].get('allow_heat_export') is False:
                        issues.append(f'{waste} = {h[waste].sum():.0f} although allow_heat_export is False')
        if 'u_steam_st' in h:
            prod = h.get('v_steam_gtcp', z) + h.get('v_steam_wbsg', z)
            used = h['u_steam_st'] + h.get('v_steam_gtcp_surp', z)
            e = np.abs(prod - used).max()
            if e > 1e-2:
                issues.append(f'steam balance off by {e:.2f} kWh/h')
            if h.get('v_steam_gtcp_surp', z).sum() > 1:
                info.append(f'steam surplus {h["v_steam_gtcp_surp"].sum():.0f}')
        # costs and unmet demand
        km, o = r['costs']['Kostenmodul'], c['optimisation']
        if 'objective' in r['costs'] and o.get('objective_monetary', 1) >= 1 and not o.get('objective_co2'):
            mon, obj = km['cost_overview']['monetary']['total'], r['costs']['objective']['total']
            if abs(mon - obj) > max(1e-4 * abs(obj), 10):
                issues.append(f'cost module {mon:.0f} != objective {obj:.0f}')
        for k in ['d_h_unmet', 'd_h_unmet_dhn', 'd_e_unmet']:
            if k in h and h[k].sum() > 1:
                issues.append(f'{k}={h[k].sum():.0f}')
        if r.get('warnings'):
            info.append('warnings: ' + ' | '.join(w.strip()[:80] for w in r['warnings']))
        print(f'{n:16s} {"ISSUE " + "; ".join(issues) if issues else "ok"}  [{"; ".join(info)}]')


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else '')
    else:
        check(sys.argv[2])
