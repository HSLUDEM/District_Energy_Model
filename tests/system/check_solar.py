"""
Solar PV: alpine PV (solar_pvalpine) and rooftop PV (solar_pvrooftop) in optimisations.

    python check_solar.py run <prefix> <workers> [filter]  -> runs all cases (or those containing filter), results in _work/pv/<prefix>_<case>.json
    python check_solar.py check <prefix>            -> potential, kWp_max, consumption/export split, costs

Set DEM_SRC to test another checkout. Davos (3851) has a large alpine PV potential; Allschwil (2762) has none.
"""
import copy, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, run_env  # noqa: E402
OUT = f'{WORK}/pv'
OPT = {'enabled': True, 'solver_option_Threads': 4}
DAVOS, ALLSCHWIL = 3851, 2762


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def C(muni, opt=True, **kw):
    c = {'simulation': {'district_number': muni}}
    if opt:
        c['optimisation'] = dict(OPT)
    return merge(c, kw)


CHEAP_ALP = {'solar_pvalpine': {'base_capex': 100}}
CHEAP_ROOF = {'solar_pvrooftop': {'base_capex': 100}}

# name: (config, number_of_days)
CASES = {
    'alp_default': (C(DAVOS), 7),
    'alp_cheap': (C(DAVOS, **CHEAP_ALP), 7),
    'alp_kwp': (C(DAVOS, solar_pvalpine={'base_capex': 100, 'kWp_max': 1000}), 7),
    'alp_kwp0': (C(DAVOS, solar_pvalpine={'base_capex': 100, 'kWp_max': 0}), 7),
    'alp_only_installed': (C(DAVOS, solar_pvalpine={'base_capex': 100, 'only_use_installed': True}), 7),
    'alp_subsidy': (C(DAVOS, solar_pvalpine={'base_capex': 100, 'export_subsidy': 0.05}), 7),
    'alp_noexport': (C(DAVOS, grid_export={'deployment': False}, **CHEAP_ALP), 7),
    'alp_scale10': (C(DAVOS, optimisation={**OPT, 'calliope_energy_scaling_factor': 10, 'solver_option_FeasibilityTol': 1e-6}, **CHEAP_ALP), 7),
    'alp_scale01': (C(DAVOS, optimisation={**OPT, 'calliope_energy_scaling_factor': 0.1, 'solver_option_FeasibilityTol': 1e-6}, **CHEAP_ALP), 7),
    'alp_tol6': (C(DAVOS, optimisation={**OPT, 'solver_option_FeasibilityTol': 1e-6}, **CHEAP_ALP), 7),
    'alp_365': (C(DAVOS, **CHEAP_ALP), 365),
    'alp_nodata': (C(ALLSCHWIL, **CHEAP_ALP), 7),
    'alp_sim': (C(DAVOS, opt=False, **CHEAP_ALP), 7),
    'alp_off': (C(DAVOS, solar_pvalpine={'deployment': False}), 7),
    'roof_default': (C(ALLSCHWIL), 7),
    'roof_cheap': (C(ALLSCHWIL, **CHEAP_ROOF), 7),
    'roof_kwp': (C(ALLSCHWIL, solar_pvrooftop={'base_capex': 100, 'kWp_max': 100}), 7),
    'roof_kwp0': (C(ALLSCHWIL, solar_pvrooftop={'base_capex': 100, 'kWp_max': 0}), 7),
    'roof_only_installed': (C(ALLSCHWIL, solar_pvrooftop={'base_capex': 100, 'only_use_installed': True}), 7),
    'roof_subsidy': (C(ALLSCHWIL, solar_pvrooftop={'base_capex': 100, 'export_subsidy': 0.05}), 7),
    'roof_eta': (C(ALLSCHWIL, solar_pvrooftop={'base_capex': 100, 'eta_overall': 0.15}), 7),
    'both_davos': (C(DAVOS, **CHEAP_ALP, **CHEAP_ROOF), 7),
    'th_default': (C(ALLSCHWIL), 7),
    'th_cheap': (C(ALLSCHWIL, solarthermal_rooftop={'base_capex': 10}), 7),
    'th_kw': (C(ALLSCHWIL, solarthermal_rooftop={'base_capex': 10, 'kW_th_max': 500}), 7),
    'th_kw0': (C(ALLSCHWIL, solarthermal_rooftop={'base_capex': 10, 'kW_th_max': 0}), 7),
    'th_only_installed': (C(ALLSCHWIL, solarthermal_rooftop={'base_capex': 10, 'only_use_installed': True}), 7),
    'th_eta': (C(ALLSCHWIL, solarthermal_rooftop={'base_capex': 10, 'eta_overall': 0.5}), 7),
    'roof_and_th_cheap': (C(ALLSCHWIL, solar_pvrooftop={'base_capex': 10}, solarthermal_rooftop={'base_capex': 10}), 7),
    'th_scale10': (C(ALLSCHWIL, optimisation={**OPT, 'calliope_energy_scaling_factor': 10, 'solver_option_FeasibilityTol': 1e-6}, solarthermal_rooftop={'base_capex': 10}), 7),
    'th_sim': (C(ALLSCHWIL, opt=False), 7),
    'roof_sim': (C(ALLSCHWIL, opt=False), 7),
    'roof_sim_kwp': (C(ALLSCHWIL, opt=False, solar_pvrooftop={'kWp_max': 100}), 7),
}

RUN1 = r'''
import sys, json, io, contextlib, traceback
import numpy as np
name, cfg, days = sys.argv[1], json.loads(sys.argv[2]), int(sys.argv[3])
cfg.setdefault('simulation', {}).update(number_of_days=days, generate_plots=False, save_results=False)
out = {'name': name, 'config': cfg, 'days': days}
try:
    from district_energy_model.model import launch
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        m = launch(root_dir='%s', config_files=False, config_dict=cfg, output_dir='%s/outputs/pv_' + name)
    out['costs'] = json.loads(json.dumps(m.total_cost(), default=str))
    df = m.hourly_results()
    out['hourly'] = {c: [float(x) for x in df[c]] for c in df.columns if 'pv' in c or 'solarthermal' in c or c in ('d_e_unmet', 'd_h_unmet', 'f_e', 'm_e', 'd_e')}
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
            print(f'{n:20s} MISSING'); continue
        r = json.load(open(f))
        if r['status'] != 'OK':
            print(f'{n:20s} FAIL  {r["error"][:220]}'); continue
        h, issues, info = {k: np.array(v) for k, v in r['hourly'].items()}, [], []
        shares = {}
        for kind in ['pvalpine', 'pvrooftop', 'solarthermalrooftop']:
            ve = 'v_h' if kind == 'solarthermalrooftop' else 'v_e'
            v, pot = h.get(f'{ve}_{kind}'), h.get(f'{ve}_{kind}_pot')
            if v is None:
                continue
            z = np.zeros_like(v)
            if pot is None:
                info.append(f'{kind}: no potential column'); pot = v
            cons, exp, rem = h.get(f'{ve}_{kind}_cons', v), h.get(f'{ve}_{kind}_exp', z), h.get(f'{ve}_{kind}_pot_remain')
            info.append(f'{kind}: {v.sum():.0f} of pot {pot.sum():.0f} (max {v.max():.1f} kW), exp {exp.sum():.0f}')
            if (v > pot + 1e-3).any():
                issues.append(f'{kind} above potential (max excess {(v - pot).max():.1f})')
            if np.abs(cons + exp - v).max() > 1e-2:
                issues.append(f'{kind}: cons + exp != production')
            if rem is not None and np.abs(pot - v - rem).max() > 1e-2:
                issues.append(f'{kind}: pot - production != pot_remain')
            on = pot > 1e-3 * max(pot.max(), 1e-9)
            if v.sum() > 1 and on.any():
                share = v[on] / pot[on]
                if share.max() - share.min() > 1e-4:
                    info.append(f'{kind} share of potential varies {share.min():.4f}..{share.max():.4f}')
            shares[kind] = v.sum() / pot.sum() if pot.sum() > 0 else 0
            key, kkey = ('solarthermal_rooftop', 'kW_th_max') if kind == 'solarthermalrooftop' else ('solar_' + kind, 'kWp_max')
            kwp = c.get(key, {}).get(kkey, 'inf')
            if kwp != 'inf':
                info.append(f'{kind} kWp_max {kwp}')
                if v.max() > kwp + 1e-3:
                    issues.append(f'{kind}: max production {v.max():.1f} kW > kWp_max {kwp}')
        if 'solarthermalrooftop' in shares and 'pvrooftop' in shares:
            info.append(f'roof use: PV {shares["pvrooftop"]:.3f} + thermal {shares["solarthermalrooftop"]:.3f} of their potentials')
        f_e = h.get('f_e')
        if f_e is not None:
            info.append(f'grid export {f_e.sum():.0f}')
        km = r['costs'].get('Kostenmodul', {})
        if 'objective' in r['costs'] and 'cost_overview' in km:
            mon, obj = km['cost_overview']['monetary']['total'], r['costs']['objective']['total']
            if abs(mon - obj) > max(1e-4 * abs(obj), 10):
                issues.append(f'cost module {mon:.0f} != objective {obj:.0f}')
        for k in ['d_h_unmet', 'd_e_unmet']:
            if k in h and h[k].sum() > 1:
                issues.append(f'{k}={h[k].sum():.0f}')
        print(f'{n:20s} {"ISSUE " + "; ".join(issues) if issues else "ok"}  [{"; ".join(info)}]')


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else '')
    else:
        check(sys.argv[2])
