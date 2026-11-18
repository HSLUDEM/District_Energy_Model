"""
TES sites (tes_sites, list_generation_mode 'externally_controlled') with different sizes and parameters.

    python check_tes_sites.py run <prefix> <workers> [filter]  -> runs all cases (or those containing filter), results in _work/tes/<prefix>_<case>.json
    python check_tes_sites.py check <prefix>            -> checks every case against the site definition

Set DEM_SRC to test another checkout. Checks per site and level: size limits and ratios, forced deployment,
exclusion groups, hourly storage balance (losses, efficiency, cyclic), charge rate, stratification order,
simultaneous charging/discharging, reported losses, and the costs (cost module vs. hand calculation vs. objective).
"""
import copy, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, run_env, expand  # noqa: E402
OUT = f'{WORK}/tes'
OPT = {'enabled': True, 'solver_option_Threads': 4}
LEVELS = ['htht', 'htlt', 'ltlt']

BASE = json.loads(expand(open(f'{T}/inputs/tes_sites_cfg.json').read()))
BASE = {k: v for k, v in BASE.items() if k not in ('tes_sites', 'simulation', 'optimisation')}

SITE = {
    'name': 'S1', 'exclusion_group': None, 'force_deployment': True, 'color': [122, 73, 14],
    'type': 'simple_fully_stratified_three_temperature_levels',
    'rel_size_t_levels': {'ltlt': 0.6, 'htlt': 0.2, 'htht': 0.2},
    'capacity_kWh_min': 20000, 'capacity_kWh_max': 60000,
    'capex_base': 600000, 'capex_per_kWh': 2.0, 'maintenance_cost_base': 1000, 'maintenance_cost_per_kWh': 0.05,
    'storage_loss_rate': {'ltlt': 0.001, 'htlt': 0.001, 'htht': 0.002},
    'eta_chg_dchg': {'ltlt': 0.9, 'htlt': 0.9, 'htht': 0.9},
    'lifetime': 30.0, 'interest_rate': 0.025, 'chg_dchg_per_cap_max': 0.1,
    'connected_techs': {'lt': ['heatlt'], 'ht': ['obcp', 'dhimp']},
}


def site(**kw):
    s = copy.deepcopy(SITE)
    for k, v in kw.items():
        s[k] = v
    return s


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def cfg(sites, opt=None, extra=None, tes=None):
    c = merge(BASE, {'tes_sites': {'deployment': True, 'list_generation_mode': 'externally_controlled',
                                   'generation_function_parameters': {'list_of_tes_options': sites}, **(tes or {})},
                     'optimisation': {**OPT, **(opt or {})}}, extra or {})
    return c


FREE = dict(force_deployment=False, capacity_kWh_min=0, capex_base=0, maintenance_cost_base=0)
ALL3 = lambda x: {'ltlt': x, 'htlt': x, 'htht': x}

# name: (config, number_of_days)
CASES = {
    'forced': (cfg([site()]), 7),
    'forced_minmax': (cfg([site(capacity_kWh_min=30000, capacity_kWh_max=30000)]), 7),
    'forced_tiny': (cfg([site(capacity_kWh_min=10, capacity_kWh_max=50)]), 7),
    'forced_huge': (cfg([site(capacity_kWh_min=5e6, capacity_kWh_max=1e7, capex_base=0, capex_per_kWh=0.01)]), 7),
    'forced_365': (cfg([site(capacity_kWh_min=2e5, capacity_kWh_max=2e6, capex_per_kWh=0.2)]), 365),
    'free_small': (cfg([site(**FREE, capacity_kWh_max=1000, capex_per_kWh=0.01)]), 7),
    'free_large': (cfg([site(**FREE, capacity_kWh_max=1e7, capex_per_kWh=0.01)]), 7),
    'free_expensive': (cfg([site(**FREE, capacity_kWh_max=1e6, capex_per_kWh=500)]), 7),
    'optional_cheap': (cfg([site(force_deployment=False, capex_base=0, maintenance_cost_base=0, capex_per_kWh=0.01)]), 7),
    'optional_costly': (cfg([site(force_deployment=False, capex_base=5e7)]), 7),
    'min0_base': (cfg([site(**{**FREE, 'capex_base': 600000, 'maintenance_cost_base': 1000}, capacity_kWh_max=1e5, capex_per_kWh=0.01)]), 7),
    'rel_ltlt': (cfg([site(rel_size_t_levels={'ltlt': 1.0, 'htlt': 0.0, 'htht': 0.0})]), 7),
    'rel_htht': (cfg([site(rel_size_t_levels={'ltlt': 0.0, 'htlt': 0.0, 'htht': 1.0})]), 7),
    'rel_htlt': (cfg([site(rel_size_t_levels={'ltlt': 0.0, 'htlt': 1.0, 'htht': 0.0})]), 7),
    'rel_ht_pair': (cfg([site(rel_size_t_levels={'ltlt': 0.0, 'htlt': 0.5, 'htht': 0.5})]), 7),
    'rel_lt_pair': (cfg([site(rel_size_t_levels={'ltlt': 0.5, 'htlt': 0.5, 'htht': 0.0})]), 7),
    'rel_no_htlt': (cfg([site(rel_size_t_levels={'ltlt': 0.5, 'htlt': 0.0, 'htht': 0.5})]), 7),
    'rel_no_htlt_free': (cfg([site(**FREE, rel_size_t_levels={'ltlt': 0.7, 'htlt': 0.0, 'htht': 0.3}, capacity_kWh_max=1e6, capex_per_kWh=0.01, chg_dchg_per_cap_max=1.0)]), 7),
    'rel_no_ltlt_free': (cfg([site(**FREE, rel_size_t_levels={'ltlt': 0.0, 'htlt': 0.3, 'htht': 0.7}, capacity_kWh_max=1e6, capex_per_kWh=0.01, chg_dchg_per_cap_max=1.0)]), 7),
    'rel_no_htht_free': (cfg([site(**FREE, rel_size_t_levels={'ltlt': 0.7, 'htlt': 0.3, 'htht': 0.0}, capacity_kWh_max=1e6, capex_per_kWh=0.01, chg_dchg_per_cap_max=1.0)]), 7),
    'rel_sum_1_8':(cfg([site(rel_size_t_levels={'ltlt': 0.6, 'htlt': 0.6, 'htht': 0.6})]), 7),
    'rate_low': (cfg([site(chg_dchg_per_cap_max=0.001)]), 7),
    'rate_high': (cfg([site(chg_dchg_per_cap_max=1.0)]), 7),
    'eta_low': (cfg([site(eta_chg_dchg=ALL3(0.5))]), 7),
    'eta1_loss0': (cfg([site(eta_chg_dchg=ALL3(1.0), storage_loss_rate=ALL3(0.0))]), 7),
    'loss_high': (cfg([site(storage_loss_rate=ALL3(0.05))]), 7),
    'interest0': (cfg([site(interest_rate=0.0)]), 7),
    'async_off': (cfg([site(chg_dchg_per_cap_max=1.0)], tes={'force_asynchronous_prod_con': False}), 7),
    'two_indep': (cfg([site(), site(name='S2', force_deployment=False, capex_base=0, capacity_kWh_min=1000, capacity_kWh_max=5e5, capex_per_kWh=0.05)]), 7),
    'two_excl': (cfg([site(force_deployment=False, exclusion_group='G', capex_base=0, capex_per_kWh=0.01),
                      site(name='S2', force_deployment=False, exclusion_group='G', capex_base=0, capex_per_kWh=0.02, capacity_kWh_min=1000)]), 7),
    # --- several sites ---
    'multi3_levels': (cfg([site(name='A', rel_size_t_levels={'ltlt': 1.0, 'htlt': 0.0, 'htht': 0.0}, capex_base=0),
                           site(name='B', rel_size_t_levels={'ltlt': 0.0, 'htlt': 0.5, 'htht': 0.5}, capex_base=0, capacity_kWh_min=5000),
                           site(name='C', **FREE, capacity_kWh_max=2e5, capex_per_kWh=0.05)]), 7),
    'excl_forced_opt': (cfg([site(name='A', exclusion_group='G'),
                             site(name='B', force_deployment=False, exclusion_group='G', capex_base=0, capex_per_kWh=0.001, capacity_kWh_min=1000, capacity_kWh_max=1e6)]), 7),
    'excl_two_groups': (cfg([site(name='A1', force_deployment=False, exclusion_group='G1', capex_base=0, capex_per_kWh=0.01),
                             site(name='A2', force_deployment=False, exclusion_group='G1', capex_base=0, capex_per_kWh=0.01),
                             site(name='B1', force_deployment=False, exclusion_group='G2', capex_base=0, capex_per_kWh=0.01, rel_size_t_levels={'ltlt': 1.0, 'htlt': 0.0, 'htht': 0.0}),
                             site(name='B2', force_deployment=False, exclusion_group='G2', capex_base=0, capex_per_kWh=0.01, rel_size_t_levels={'ltlt': 0.0, 'htlt': 0.0, 'htht': 1.0})]), 7),
    'multi5_same': (cfg([site(name=f'S{k}', force_deployment=False, capex_base=0, capex_per_kWh=0.05, capacity_kWh_min=1000, capacity_kWh_max=1e5) for k in range(5)]), 7),
    'multi2_365': (cfg([site(name='A', capacity_kWh_min=2e5, capacity_kWh_max=2e6, capex_per_kWh=0.2),
                        site(name='B', capacity_kWh_min=1e5, capacity_kWh_max=1e6, capex_per_kWh=0.3, rel_size_t_levels={'ltlt': 0.5, 'htlt': 0.5, 'htht': 0.0})]), 365),
    'multi2_scale10': (cfg([site(name='A'), site(name='B', **FREE, capacity_kWh_max=1e5, capex_per_kWh=0.05)],
                           opt={'calliope_energy_scaling_factor': 10, 'solver_option_FeasibilityTol': 1e-6}), 7),
    'bad_min_gt_max': (cfg([site(capacity_kWh_min=60000, capacity_kWh_max=20000)]), 7),
    'bad_rel_zero': (cfg([site(rel_size_t_levels={'ltlt': 0.0, 'htlt': 0.0, 'htht': 0.0})]), 7),
    'bad_rel_negative': (cfg([site(**FREE, rel_size_t_levels={'ltlt': 1.2, 'htlt': -0.2, 'htht': 0.0}, capex_per_kWh=0.01)]), 7),
    'dup_names': (cfg([site(), site(force_deployment=False, capex_base=0, capacity_kWh_min=1000, capex_per_kWh=0.05)]), 7),
    'scale10': (cfg([site()], opt={'calliope_energy_scaling_factor': 10, 'solver_option_FeasibilityTol': 1e-6}), 7),
    'scale01': (cfg([site()], opt={'calliope_energy_scaling_factor': 0.1, 'solver_option_FeasibilityTol': 1e-6}), 7),
    'scale1_tol6': (cfg([site()], opt={'solver_option_FeasibilityTol': 1e-6}), 7),
    'co2obj': (cfg([site()], opt={'objective_monetary': 1e-5, 'objective_co2': 1}), 7),
    'bern': (cfg([site(capacity_kWh_min=1e5, capacity_kWh_max=1e6)], extra={'simulation': {'district_number': 351}}), 7),
    'lt_empty': (cfg([site(connected_techs={'lt': [], 'ht': ['obcp', 'dhimp']})]), 7),
    'ht_many': (cfg([site(connected_techs={'lt': ['heatlt'], 'ht': ['obcp', 'hpcplt', 'wh', 'hpcp', 'dhimp', 'ehcp']})]), 7),
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
        m = launch(root_dir='%s', config_files=False, config_dict=cfg, output_dir='%s/outputs/tes_' + name)
    t = m.tech_instances['tes_sites']
    out['caps'] = {lv: [float(x) for x in getattr(t, '_cap_' + lv)] for lv in ['htht', 'htlt', 'ltlt']}
    out['costs'] = json.loads(json.dumps(m.total_cost(), default=str))
    df = m.hourly_results()
    out['hourly'] = {c: [float(x) for x in df[c]] for c in df.columns if 'tes_site' in c or c in ('d_h_unmet', 'd_h_unmet_dhn', 'd_e_unmet')}
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


def af(s):
    r, n = s['interest_rate'], s['lifetime']
    return r * (1 + r)**n / ((1 + r)**n - 1) if r > 0 else 1 / n


def check_site(s, i, r, days, asyn, issues, info):
    nm, h, rel = s['name'], r['hourly'], s['rel_size_t_levels']
    caps = {lv: r['caps'][lv][i] for lv in LEVELS}
    tot = sum(caps.values())
    lv_on = [lv for lv in LEVELS if rel[lv] > 0]
    built = tot > 1e-3
    info.append(f'{nm}: ' + ' '.join(f'{lv}={caps[lv]:.0f}' for lv in lv_on))
    # sizes: one common size X with cap_lv = rel_lv * X, min <= X <= max
    if not lv_on:
        issues.append(f'{nm} has no level with rel_size_t_levels > 0' + (' but is forced' if s['force_deployment'] else '') + ' (accepted silently)')
        return False, 0, 0
    X = caps[lv_on[0]] / rel[lv_on[0]]
    for lv in LEVELS:
        exp = rel[lv] * X
        if abs(caps[lv] - exp) > 1e-4 * max(1, X):
            issues.append(f'{nm} {lv} cap {caps[lv]:.1f} != rel*X {exp:.1f}')
    if X > s['capacity_kWh_max'] * (1 + 1e-6) + 1e-3:
        issues.append(f'{nm} size X={X:.0f} > max {s["capacity_kWh_max"]}')
    if built and s['capacity_kWh_min'] > 0 and X < s['capacity_kWh_min'] * (1 - 1e-6) - 1e-3:
        issues.append(f'{nm} size X={X:.0f} < min {s["capacity_kWh_min"]}')
    if s['force_deployment'] and not built:
        issues.append(f'{nm} forced but not built')
    if abs(sum(rel.values()) - 1) > 1e-9:
        info.append(f'{nm} total cap {tot:.0f} = {sum(rel.values()):.1f} x size')
    # hourly
    q_by = {}
    for lv in lv_on:
        u = np.array(h[f'u_h{lv}_tes_site_{nm}']); v = np.array(h[f'v_h{lv}_tes_site_{nm}'])
        q = np.array(h[f'q_h{lv}_tes_site_{nm}']); q_by[lv] = q
        lu = np.array(h[f'l_u_h{lv}_tes_site_{nm}']); lvv = np.array(h[f'l_v_h{lv}_tes_site_{nm}']); lq = np.array(h[f'l_q_h{lv}_tes_site_{nm}'])
        eta, loss, cap = s['eta_chg_dchg'][lv], s['storage_loss_rate'][lv], caps[lv]
        tol = 1e-3 * max(1, cap) * 1e-2
        qprev = np.roll(q, 1)  # cyclic
        exp = qprev * (1 - loss) + eta * u - v / eta
        err = np.abs(q - exp).max()
        if err > max(1e-2, 1e-5 * cap):
            # non-cyclic start (empty)?
            q0 = np.concatenate([[0], q[:-1]])
            err0 = np.abs(q - (q0 * (1 - loss) + eta * u - v / eta)).max()
            issues.append(f'{nm} {lv} storage balance off by {err:.2f} kWh (empty start: {err0:.2f})')
        if (q > cap * (1 + 1e-6) + 1e-2).any() or (q < -1e-2).any():
            issues.append(f'{nm} {lv} level outside [0, cap]: {q.min():.1f}..{q.max():.1f} cap {cap:.1f}')
        rate = s['chg_dchg_per_cap_max'] * cap
        if u.max() > rate * (1 + 1e-6) + 1e-2 or v.max() > rate * (1 + 1e-6) + 1e-2:
            issues.append(f'{nm} {lv} rate: max u {u.max():.1f} v {v.max():.1f} > {rate:.1f}')
        both = np.minimum(u, v)
        if asyn and both.max() > 1e-2:
            issues.append(f'{nm} {lv} charges and discharges in the same hour ({(both > 1e-2).sum()} h)')
        elif both.sum() > 1:
            info.append(f'{nm} {lv} simultaneous chg/dchg {both.sum():.0f} kWh')
        # reported losses close the balance?
        dq = q - qprev
        rep = u - lu - v - lvv - lq
        e2 = np.abs(dq - rep).max()
        if e2 > max(1e-2, 1e-5 * cap) and np.abs(u).sum() + np.abs(v).sum() > 1:
            info.append(f'{nm} {lv} reported losses do not close the balance (max {e2:.2f} kWh/h)')
        info.append(f'{nm} {lv} in {u.sum():.0f} out {v.sum():.0f}')
    # stratification
    for a, b in [('htht', 'htlt'), ('htht', 'ltlt'), ('htlt', 'ltlt')]:
        if a in q_by and b in q_by:
            d = (q_by[a] / rel[a] - q_by[b] / rel[b]).max()
            if d > 1e-2 + 1e-6 * X:
                issues.append(f'{nm} stratification {a} > {b} by {d:.1f}')
    # expected costs
    fr = days / 365
    base = built and s['capacity_kWh_min'] > 0
    capex = ((s['capex_per_kWh'] * tot + (s['capex_base'] if base else 0)) * af(s)) * fr if built else 0
    opex = (s['maintenance_cost_per_kWh'] * tot + (s['maintenance_cost_base'] if base else 0)) * fr if built else 0
    return built, capex, opex


def check(prefix):
    for n, (c, days) in CASES.items():
        f = f'{OUT}/{prefix}_{n}.json'
        if not os.path.exists(f):
            print(f'{n:15s} MISSING'); continue
        r = json.load(open(f))
        if r['status'] != 'OK':
            print(f'{n:15s} FAIL  {r["error"][:200]}'); continue
        sites = c['tes_sites']['generation_function_parameters']['list_of_tes_options']
        asyn = c['tes_sites'].get('force_asynchronous_prod_con', True)
        issues, info, capex, opex, built = [], [], 0, 0, []
        for i, s in enumerate(sites):
            b, ce, oe = check_site(s, i, r, days, asyn, issues, info)
            built.append(b); capex += ce; opex += oe
        groups = {}
        for s, b in zip(sites, built):
            if s['exclusion_group'] is not None:
                groups[s['exclusion_group']] = groups.get(s['exclusion_group'], 0) + b
        for g, k in groups.items():
            if k > 1:
                issues.append(f'exclusion group {g}: {k} sites built')
        km = r['costs']['Kostenmodul']
        ts = km['monetary_breakdown'].get('tes_sites', {})
        if abs(ts.get('annualized_capex', 0) - capex) > 1e-4 * max(1, capex) + 0.01:
            issues.append(f'cost module capex {ts.get("annualized_capex", 0):.1f} != expected {capex:.1f}')
        if abs(ts.get('opex', 0) - opex) > 1e-4 * max(1, opex) + 0.01:
            issues.append(f'cost module opex {ts.get("opex", 0):.1f} != expected {opex:.1f}')
        o = c['optimisation']
        if 'objective' in r['costs'] and o.get('objective_monetary', 1) and not o.get('objective_co2'):
            mon, obj = km['cost_overview']['monetary']['total'], r['costs']['objective']['total']
            if abs(mon - obj) > max(1e-4 * abs(obj), 10):
                issues.append(f'cost module {mon:.0f} != objective {obj:.0f}')
        for k in ['d_h_unmet', 'd_h_unmet_dhn', 'd_e_unmet']:
            if k in r['hourly'] and sum(r['hourly'][k]) > 1:
                issues.append(f'{k}={sum(r["hourly"][k]):.0f}')
        print(f'{n:15s} {"ISSUE " + "; ".join(issues) if issues else "ok"}  [{"; ".join(info)}]')


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else '')
    else:
        check(sys.argv[2])
