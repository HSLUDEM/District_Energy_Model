"""
Manual scenarios in simulations: wind_integration, nuclear_phaseout, battery_energy_storage (via PV surplus).

    python check_scenarios.py run <prefix> <workers> [filter]  -> runs all cases, results in _work/scen/<prefix>_<case>.json
    python check_scenarios.py check <prefix>            -> compares each scenario with its base run

Set DEM_SRC to test another checkout.
"""
import copy, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, run_env  # noqa: E402
OUT = f'{WORK}/scen'


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def S(muni, **kw):
    return merge({'simulation': {'district_number': muni}}, kw)


def WIND(f):
    return {'scenarios': {'wind_integration': True}, 'wind_integration': {'potential_integration_factor': f}}


def FUT(y):
    return {'scenarios': {'demand_side': True}, 'demand_side': {'simulation_year': {'type': 'future', 'future_year': y}}}


NUC = {'scenarios': {'nuclear_phaseout': True}}


def BES(cap, ic=0.0):
    return {'scenarios': {'battery_energy_storage': True}, 'battery_energy_storage_scenario': {'capacity_kWh': cap, 'initial_charge': ic}}


PVI = {'scenarios': {'pv_integration': True}, 'pv_integration': {'potential_integration_factor': {'solar_pvrooftop': [0.9] * 4}}}

# name: (config, number_of_days, base case or None)
CASES = {
    'base_2762': (S(2762), 7, None),
    'base_6037': (S(6037), 7, None),
    'base_448': (S(448), 7, None),
    'wind05_2762': (S(2762, **WIND(0.5)), 7, 'base_2762'),
    'wind1_2762': (S(2762, **WIND(1.0)), 7, 'base_2762'),
    'wind05_6037': (S(6037, **WIND(0.5)), 7, 'base_6037'),
    'wind1_448': (S(448, **WIND(1.0)), 7, 'base_448'),
    'wind0_2762': (S(2762, **WIND(0.0)), 7, 'base_2762'),
    'nuc_now': (S(2762, **NUC), 7, 'base_2762'),
    'base_2040': (S(2762, **FUT(2040)), 7, None),
    'nuc_2040': (merge(S(2762, **FUT(2040)), NUC), 7, 'base_2040'),
    'base_2050': (S(2762, **FUT(2050)), 7, None),
    'nuc_2050': (merge(S(2762, **FUT(2050)), NUC), 7, 'base_2050'),
    'base_365': (S(2762), 365, None),
    'bes_365': (S(2762, **BES(1e4)), 365, 'base_365'),
    'bes_365_ic05': (S(2762, **BES(1e4, 0.5)), 365, 'base_365'),
    'bes_365_big': (S(2762, **BES(1e6)), 365, 'base_365'),
    'base_365_pvi': (S(2762, **PVI), 365, None),
    'bes_365_pvi': (merge(S(2762, **PVI), BES(1e5)), 365, 'base_365_pvi'),
}

COLS = ['v_e_wp', 'v_e_wp_cons', 'v_e_wp_exp', 'v_e_wp_pot', 'v_e_wp_pot_remain', 'm_e', 'm_e_ch', 'm_e_cbimport',
        'm_e_ch_nuclear', 'm_e_ch_hydro', 'm_e_ch_wind', 'm_e_ch_biomass', 'm_e_ch_other', 'd_e', 'v_e_pv', 'v_e_pv_cons', 'v_e_pv_exp',
        'u_e_bes', 'v_e_bes', 'q_e_bes', 'sos_bes', 'l_u_e_bes', 'l_v_e_bes', 'l_q_e_bes', 'v_co2_tot', 'm_co2_e']

RUN1 = r'''
import sys, json, io, contextlib, traceback
import numpy as np
name, cfg, days = sys.argv[1], json.loads(sys.argv[2]), int(sys.argv[3])
cfg.setdefault('simulation', {}).update(number_of_days=days, generate_plots=False, save_results=False)
out = {'name': name, 'config': cfg, 'days': days}
COLS = %r
try:
    from district_energy_model.model import launch
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        m = launch(root_dir='%s', config_files=False, config_dict=cfg, output_dir='%s/outputs/scen_' + name)
    df = m.hourly_results()
    out['hourly'] = {c: [float(x) for x in df[c]] for c in df.columns if c in COLS or c.startswith('v_e_') and c.endswith(('_exp', '_cons'))}
    a = m.annual_results()
    out['annual'] = {k: float(v) for k, v in a.items() if isinstance(v, (int, float, np.integer, np.floating))}
    out['costs'] = json.loads(json.dumps(m.total_cost(), default=str))
    out['warnings'] = [l for l in log.getvalue().splitlines() if 'WARNING' in l.upper() and 'FutureWarning' not in l][:5]
    out['status'] = 'OK'
except BaseException as e:
    out['status'] = 'FAIL'; out['error'] = f'{type(e).__name__}: {e}'[:1500]; out['tb'] = traceback.format_exc()[-3000:]
json.dump(out, open('%s/' + name + '.json', 'w'), default=str)
print(name, out['status'], out.get('error', '')[:200], flush=True)
''' % (COLS, ROOT, WORK, OUT)


def run(prefix, workers, flt=''):
    os.makedirs(OUT, exist_ok=True)
    open(f'{OUT}/_run1.py', 'w').write(RUN1)
    env = run_env()
    def one(item):
        n, (c, days, _) = item
        return subprocess.run([PYTHON, f'{OUT}/_run1.py', f'{prefix}_{n}', json.dumps(c), str(days)],
                              capture_output=True, text=True, env=env).stdout.strip()
    items = sorted(((n, v) for n, v in CASES.items() if flt in n), key=lambda kv: -kv[1][1])
    with ThreadPoolExecutor(workers) as ex:
        for o in ex.map(one, items):
            print(o, flush=True)


def load(prefix, n):
    f = f'{OUT}/{prefix}_{n}.json'
    return json.load(open(f)) if os.path.exists(f) else None


def check(prefix):
    for n, (c, days, bname) in CASES.items():
        r = load(prefix, n)
        if r is None:
            print(f'{n:14s} MISSING'); continue
        if r['status'] != 'OK':
            print(f'{n:14s} FAIL  {r["error"][:220]}'); continue
        h = {k: np.array(v) for k, v in r['hourly'].items()}
        issues, info = [], []
        # import mix always adds up
        mix = sum(h[k] for k in ['m_e_ch_nuclear', 'm_e_ch_hydro', 'm_e_ch_wind', 'm_e_ch_biomass', 'm_e_ch_other'])
        if np.abs(mix - h['m_e_ch']).max() > 1e-3 or np.abs(h['m_e_ch'] + h['m_e_cbimport'] - h['m_e']).max() > 1e-3:
            issues.append('import mix does not add up')
        b = load(prefix, bname) if bname else None
        if b is not None and b['status'] == 'OK':
            g = {k: np.array(v) for k, v in b['hourly'].items()}
            if 'wind_integration' in c:
                f = c['wind_integration']['potential_integration_factor']
                dv = h['v_e_wp'] - g['v_e_wp']
                exp_dv = f * g['v_e_wp_pot_remain']
                info.append(f'wind +{dv.sum():.0f} (expected {exp_dv.sum():.0f}); import {g["m_e"].sum():.0f} -> {h["m_e"].sum():.0f}; '
                            f'wind exp {g["v_e_wp_exp"].sum():.0f} -> {h["v_e_wp_exp"].sum():.0f}')
                if np.abs(dv - exp_dv).max() > 1e-3:
                    issues.append(f'added wind != factor x remaining potential (max diff {np.abs(dv - exp_dv).max():.2f})')
                # extra wind is used locally (less import) or exported
                d_imp, d_exp = g['m_e'] - h['m_e'], h['v_e_wp_exp'] - g['v_e_wp_exp']
                if np.abs(d_imp + d_exp - dv).max() > 1e-2:
                    issues.append(f'added wind not balanced by import/export (max {np.abs(d_imp + d_exp - dv).max():.2f})')
                if np.abs(h['v_e_wp_pot'] - h['v_e_wp'] - h['v_e_wp_pot_remain']).max() > 1e-2:
                    issues.append(f'wind pot_remain not updated (remain {h["v_e_wp_pot_remain"].sum():.0f}, pot - v_e {(h["v_e_wp_pot"] - h["v_e_wp"]).sum():.0f})')
                if np.abs(h['v_e_wp_cons'] + h['v_e_wp_exp'] - h['v_e_wp']).max() > 1e-2:
                    issues.append('wind cons + exp != v_e_wp')
            if c.get('scenarios', {}).get('nuclear_phaseout'):
                yr = c.get('demand_side', {}).get('simulation_year', {}).get('future_year', 2026)
                pw, sd = [1010, 1233, 365, 365], [2039, 2045, 2033, 2032]
                frac = sum(p for p, y in zip(pw, sd) if yr < y) / sum(pw)
                info.append(f'year {yr}: nuclear {g["m_e_ch_nuclear"].sum():.0f} -> {h["m_e_ch_nuclear"].sum():.0f} (fraction {frac:.3f}); '
                            f'cbimport {g["m_e_cbimport"].sum():.0f} -> {h["m_e_cbimport"].sum():.0f}; CO2 {b["annual"].get("v_co2_tot_yr", 0):.0f} -> {r["annual"].get("v_co2_tot_yr", 0):.0f}')
                if np.abs(h['m_e_ch_nuclear'] - frac * g['m_e_ch_nuclear']).max() > 1e-3:
                    issues.append('nuclear import != fraction x base')
                if np.abs(h['m_e'] - g['m_e']).max() > 1e-3:
                    issues.append('total import changed')
            if 'battery_energy_storage_scenario' in c:
                s = c['battery_energy_storage_scenario']
                cap, ic = s['capacity_kWh'], s['initial_charge']
                u, v, q = h['u_e_bes'], h['v_e_bes'], h['q_e_bes']
                info.append(f'bes in {u.sum():.0f} out {v.sum():.0f} q {q.min():.0f}..{q.max():.0f} (cap {cap:.0f}); import {g["m_e"].sum():.0f} -> {h["m_e"].sum():.0f}; '
                            f'pv exp {g.get("v_e_pvrooftop_exp", 0 * u).sum():.0f} -> {h.get("v_e_pvrooftop_exp", 0 * u).sum():.0f}')
                if q.max() > cap * (1 + 1e-6) + 1e-3 or q.min() < -1e-3:
                    issues.append('battery level outside [0, cap]')
                lu, lv, lq = h['l_u_e_bes'], h['l_v_e_bes'], h['l_q_e_bes']
                qprev = np.concatenate([[ic * cap], q[:-1]])
                lq_prev = np.concatenate([[0.0], lq[:-1]])  # the storage loss of the step i-1 -> i is stored at i-1
                e = np.abs(q - (qprev + u - lu - v - lv - lq_prev)).max()
                if u.min() < -1e-6 or v.min() < -1e-6:
                    issues.append(f'negative battery flows (u min {u.min():.2f}, v min {v.min():.2f})')
                if e > 1e-2:
                    issues.append(f'battery balance with reported losses off by {e:.2f} kWh/h')
                if (np.minimum(u, v) > 1e-3).any():
                    issues.append('battery charges and discharges in the same hour')
                # charging only from PV surplus (base PV export)
                pv_exp = g.get('v_e_pvrooftop_exp', 0 * u)
                if (u > pv_exp + 1e-3).any():
                    issues.append(f'battery charged beyond the PV surplus of the base run ({(u - pv_exp).max():.1f} kWh/h)')
                d_imp = g['m_e'] - h['m_e']
                if np.abs(d_imp - (v - 0)).max() > 1e-2 and np.abs(d_imp.sum() - v.sum()) > 1:
                    info.append(f'import reduction {d_imp.sum():.0f} vs discharge {v.sum():.0f}')
        if r.get('warnings'):
            info.append('warnings: ' + ' | '.join(w.strip()[:100] for w in r['warnings']))
        print(f'{n:14s} {"ISSUE " + "; ".join(issues) if issues else "ok"}  [{"; ".join(info)}]')


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else '')
    else:
        check(sys.argv[2])
