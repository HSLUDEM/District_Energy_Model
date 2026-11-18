"""
Grid supply / grid export with tariff and CO2 intensity time series (tariff_mode / co2_intensity_mode 'file').

    python check_grid_tariffs.py <prefix> [workers]   -> runs all cases, results in _work/gt/<prefix>_<case>.json, then checks them

Set DEM_SRC to test another checkout. Checks: the cost module's grid costs and emissions equal the
hourly flows times the input series, and (optimisation) the cost module equals the objective.
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, run_env  # noqa: E402
D = f'{T}/inputs/gt'
OUT = f'{WORK}/gt'
OPT = {'enabled': True, 'solver_option_Threads': 4}


def GS(ext, tariff=True, co2=True):
    d = {}
    if tariff:
        d.update(tariff_mode='file', tariff_timeseries_filepath=f'{D}/tariff.{ext}')
    if co2:
        d.update(co2_intensity_mode='file', co2_intensity_timeseries_filepath=f'{D}/co2.{ext}')
    return {'grid_supply': d}


def GE(ext):
    return {'grid_export': {'tariff_mode': 'file', 'tariff_timeseries_filepath': f'{D}/exp.{ext}',
                            'co2_intensity_mode': 'file', 'co2_intensity_timeseries_filepath': f'{D}/co2.{ext}'}}


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


CASES = {
    'sim_feather': (GS('feather'), 7),
    'sim_npy': (GS('npy'), 7),
    'sim_export': (merge(GS('feather'), GE('feather')), 7),
    'opt_feather': (merge(GS('feather'), {'optimisation': OPT}), 7),
    'opt_npy': (merge(GS('npy'), {'optimisation': OPT}), 7),
    'opt_export': (merge(GS('feather'), GE('npy'), {'optimisation': OPT}), 7),
    'opt_scale10': (merge(GS('feather'), {'optimisation': {**OPT, 'solver_option_FeasibilityTol': 1e-6, 'calliope_energy_scaling_factor': 10}}), 7),
    'opt_co2obj': (merge(GS('feather'), {'optimisation': {**OPT, 'objective_co2': True}}), 7),
    'opt_365': (merge(GS('npy'), {'optimisation': OPT}), 365),
    'opt_bern': (merge(GS('feather'), GE('feather'), {'simulation': {'district_number': 351}}, {'optimisation': OPT}), 7),
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
        m = launch(root_dir='%s', config_files=False, config_dict=cfg, output_dir='%s/outputs/gt_' + name)
    out['costs'] = json.loads(json.dumps(m.total_cost(), default=str))
    df = m.hourly_results()
    out['hourly'] = {c: [float(x) for x in df[c]] for c in ['m_e', 'm_e_cbimport', 'f_e', 'd_e_unmet'] if c in df.columns}
    out['status'] = 'OK'
except BaseException as e:
    out['status'] = 'FAIL'; out['error'] = f'{type(e).__name__}: {e}'[:1500]; out['tb'] = traceback.format_exc()[-3000:]
json.dump(out, open('%s/' + name + '.json', 'w'), default=str)
print(name, out['status'], out.get('error', '')[:200], flush=True)
''' % (ROOT, WORK, OUT)


def run(prefix, workers):
    os.makedirs(OUT, exist_ok=True)
    open(f'{OUT}/_run1.py', 'w').write(RUN1)
    env = run_env()
    def one(item):
        n, (cfg, days) = item
        return subprocess.run([PYTHON, f'{OUT}/_run1.py', f'{prefix}_{n}', json.dumps(cfg), str(days)],
                              capture_output=True, text=True, env=env).stdout.strip()
    with ThreadPoolExecutor(workers) as ex:
        for o in ex.map(one, sorted(CASES.items(), key=lambda kv: -kv[1][1])):
            print(o, flush=True)


def find(d, key):
    """First value for key anywhere in a nested dict."""
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for v in d.values():
            r = find(v, key)
            if r is not None:
                return r
    return None


def check(prefix):
    for n, (cfg, days) in CASES.items():
        r = json.load(open(f'{OUT}/{prefix}_{n}.json'))
        if r['status'] != 'OK':
            print(f'{n:12s} FAIL  {r["error"][:200]}'); continue
        nh, h, c, issues = days * 24, r['hourly'], r['costs'], []
        tar = np.load(f'{D}/tariff.npy')[:nh]
        co2 = np.load(f'{D}/co2.npy')[:nh]
        m_e = np.array(h['m_e'])
        gs = find(c, 'grid_supply')
        exp_cost = float(np.sum(m_e * tar))
        got = gs.get('energy_costs') if isinstance(gs, dict) else None
        if got is None or abs(got - exp_cost) > 1e-6 * max(1, abs(exp_cost)):
            issues.append(f'grid_supply energy cost {got} != m_e*tariff {exp_cost:.2f}')
        em = find(c, 'emissions_grid')
        if em is None or abs(em - float(np.sum(m_e * co2))) > 1e-6 * max(1, em or 1):
            issues.append(f'emissions_grid {em} != m_e*co2 {np.sum(m_e * co2):.2f}')
        if 'grid_export' in cfg:
            ex = np.load(f'{D}/exp.npy')[:nh]
            f_e = np.array(h['f_e'])
            ge = find(c, 'grid_export')
            got = ge.get('energy_costs') if isinstance(ge, dict) else None
            if got is None or abs(got + float(np.sum(f_e * ex))) > 1e-6 * max(1, np.sum(f_e * ex)):
                issues.append(f'grid_export energy cost {got} != -f_e*tariff {-np.sum(f_e * ex):.2f}')
        if 'objective' in c and not cfg['optimisation'].get('objective_co2'):
            mon, obj = find(c, 'monetary')['total'], c['objective']['total']
            if abs(mon - obj) > max(1e-4 * abs(obj), 10):
                issues.append(f'cost module {mon:.0f} != objective {obj:.0f}')
        # day/night split of grid import (tariff is high 8-20 h)
        day = (np.arange(nh) % 24 >= 8) & (np.arange(nh) % 24 < 20)
        info = f'import day {m_e[day].sum():.0f} night {m_e[~day].sum():.0f} kWh'
        print(f'{n:12s} {"ISSUE " + "; ".join(issues) if issues else "ok"}  [{info}]')


if __name__ == '__main__':
    run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8)
    check(sys.argv[1])
