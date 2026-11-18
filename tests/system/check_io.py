"""
Output files and YAML configuration for the cases of the technology tests (pv, cplant, chain, tes, scen).

    python check_io.py run <prefix> <workers> [filter]  -> every case three times, results in _work/io/<prefix>_<case>_<mode>.*
    python check_io.py check <prefix>

Modes:
    A  config_dict, save_results and generate_plots on
    B  the same configuration as one YAML file per top-level key (config_dir), nothing saved
    C  the scen_techs.yaml saved by A, used as technologies.yaml (plus simulation.yaml switching output off)

Checks: A's saved files vs. its in-memory results (hourly_results.csv, annual_results.txt, scen_techs.yaml,
plots written), and A vs. B vs. C (resolved scen_techs, objective / total cost, annual results).
Cases longer than 14 days are shortened to 14 days. Set DEM_SRC to test another checkout.
"""
import copy, glob, json, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import yaml

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, run_env  # noqa: E402
OUT = f'{WORK}/io'


def cases():
    import check_solar, check_central_plants, check_fuel_chains, check_tes_sites, check_scenarios
    out = {}
    for tag, mod in (('pv', check_solar), ('cplant', check_central_plants), ('chain', check_fuel_chains),
                     ('tes', check_tes_sites), ('scen', check_scenarios)):
        for n, v in mod.CASES.items():
            out[f'{tag}_{n}'] = (v[0], min(v[1], 14))
    return out


RUN1 = r'''
import sys, json, io, contextlib, traceback, pickle, os
import numpy as np
name, mode, cfg_arg, days = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
OUT = %r
out = {'name': name, 'mode': mode}
try:
    from district_energy_model.model import launch
    log = io.StringIO()
    odir = f'{OUT}/out_{name}'
    with contextlib.redirect_stdout(log):
        if mode == 'A':
            cfg = json.loads(cfg_arg)
            m = launch(root_dir=%r, config_files=False, config_dict=cfg, output_dir=odir)
        else:
            m = launch(root_dir=%r, config_dir=cfg_arg, output_dir=odir)
    out['results_path'] = str(m.results_path)
    out['scen_techs'] = json.loads(json.dumps(m.scen_techs, default=repr))
    out['annual'] = {k: float(v) for k, v in m.annual_results().items() if isinstance(v, (int, float, np.integer, np.floating))}
    out['costs'] = json.loads(json.dumps(m.total_cost(), default=str))
    m.hourly_results().to_pickle(f'{OUT}/{name}.pkl')
    out['status'] = 'OK'
except BaseException as e:
    out['status'] = 'FAIL'; out['error'] = f'{type(e).__name__}: {e}'[:1500]; out['tb'] = traceback.format_exc()[-3000:]
json.dump(out, open(f'{OUT}/{name}.json', 'w'), default=str)
print(name, out['status'], out.get('error', '')[:200], flush=True)
''' % (OUT, ROOT, ROOT)


def py(name, mode, arg, days):
    env = run_env()
    r = subprocess.run([PYTHON, f'{OUT}/_run1.py', name, mode, arg, str(days)],
                       capture_output=True, text=True, env=env)
    return (r.stdout.strip() or r.stderr.strip()[-300:])


def one(prefix, n, c, days):
    base = f'{prefix}_{n}'
    for mode in 'ABC':
        for p in glob.glob(f'{OUT}/out_{base}_{mode}*'):
            shutil.rmtree(p, ignore_errors=True)
    cfg = copy.deepcopy(c)
    cfg.setdefault('simulation', {}).update(number_of_days=days, generate_plots=True, save_results=True)
    lines = [py(f'{base}_A', 'A', json.dumps(cfg), days)]
    # B: one YAML file per top-level key
    d = f'{OUT}/cfg_{base}_B'
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    cfg_b = copy.deepcopy(cfg)
    cfg_b['simulation'].update(generate_plots=False, save_results=False)
    for k, v in cfg_b.items():
        yaml.safe_dump(v, open(f'{d}/{k}.yaml', 'w'))
    lines.append(py(f'{base}_B', 'B', d, days))
    # C: saved scen_techs.yaml as technologies.yaml
    ra = json.load(open(f'{OUT}/{base}_A.json'))
    saved = f'{ra.get("results_path", "")}/scen_techs.yaml'
    if os.path.exists(saved):
        d = f'{OUT}/cfg_{base}_C'
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        shutil.copy(saved, f'{d}/technologies.yaml')
        yaml.safe_dump({'generate_plots': False, 'save_results': False}, open(f'{d}/simulation.yaml', 'w'))
        lines.append(py(f'{base}_C', 'C', d, days))
    return ' | '.join(lines)


def run(prefix, workers, flt=''):
    os.makedirs(OUT, exist_ok=True)
    open(f'{OUT}/_run1.py', 'w').write(RUN1)
    items = [(n, v) for n, v in cases().items() if flt in n]
    with ThreadPoolExecutor(workers) as ex:
        for o in ex.map(lambda kv: one(prefix, kv[0], *kv[1]), items):
            print(o, flush=True)


def strip_out(st):
    st = copy.deepcopy(st)
    for k in ('generate_plots', 'save_results'):
        st.get('simulation', {}).pop(k, None)
    return st


def diff_dicts(a, b, path=''):
    out = []
    for k in sorted(set(a) | set(b), key=str):
        p = f'{path}.{k}' if path else str(k)
        if k not in a or k not in b:
            out.append(f'{p} only in {"B" if k not in a else "A"}')
        elif isinstance(a[k], dict) and isinstance(b[k], dict):
            out += diff_dicts(a[k], b[k], p)
        elif a[k] != b[k] and not (isinstance(a[k], (int, float)) and isinstance(b[k], (int, float)) and abs(a[k] - b[k]) <= 1e-9 * max(1, abs(a[k]))):
            out.append(f'{p}: {a[k]!r} vs {b[k]!r}')
    return out


def total(r):
    c = r.get('costs', {})
    if 'objective' in c:
        return c['objective']['total']
    return c.get('Kostenmodul', {}).get('cost_overview', {}).get('monetary', {}).get('total')


def check(prefix):
    import pandas as pd
    for n in cases():
        base = f'{prefix}_{n}'
        R = {}
        for mode in 'ABC':
            f = f'{OUT}/{base}_{mode}.json'
            if os.path.exists(f):
                R[mode] = json.load(open(f))
        if 'A' not in R:
            print(f'{n:28s} MISSING'); continue
        issues, info = [], []
        st = {m: r['status'] for m, r in R.items()}
        if len(set(st.values())) > 1:
            issues.append('status differs ' + str({m: (r['status'], r.get('error', '')[:120]) for m, r in R.items()}))
        if R['A']['status'] != 'OK':
            # same failure in all modes: report briefly
            print(f'{n:28s} {"ISSUE " + "; ".join(issues) if issues else "fail(all)"}  [{R["A"]["error"][:150]}]'); continue
        a = R['A']
        rp = a['results_path']
        files = os.listdir(rp) if os.path.isdir(rp) else []
        for f in ('hourly_results.csv', 'annual_results.txt', 'scen_techs.yaml', 'input_data.csv', 'total_costs.txt'):
            if f not in files:
                issues.append(f'{f} not saved')
        html = [f for f in files if f.endswith('.html')]
        info.append(f'{len(html)} html')
        if not html:
            issues.append('no plots')
        h = pd.read_pickle(f'{OUT}/{base}_A.pkl')
        if 'hourly_results.csv' in files:
            hc = pd.read_csv(f'{rp}/hourly_results.csv', index_col=0)
            num = h.select_dtypes('number')
            miss = [c for c in num.columns if c not in hc.columns]
            if miss:
                issues.append(f'csv misses {miss[:5]}')
            bad = [c for c in num.columns if c in hc.columns and not np.allclose(num[c].values, hc[c].values, rtol=1e-9, atol=1e-9, equal_nan=True)]
            if bad:
                issues.append(f'csv differs {bad[:5]}')
            if len(hc) != len(h):
                issues.append(f'csv rows {len(hc)} vs {len(h)}')
        if 'annual_results.txt' in files:
            txt = {}
            for line in open(f'{rp}/annual_results.txt'):
                k, _, v = line.partition(': ')
                try:
                    txt[k] = float(v)
                except ValueError:
                    txt[k] = v.strip()
            added = [k for k in a['annual'] if k not in txt]
            if added:
                info.append(f'in memory, not in file: {added}')
            nonnum = [k for k in a['annual'] if k in txt and not isinstance(txt[k], float)]
            if nonnum:
                issues.append(f'annual_results.txt not numeric: {nonnum[:3]} e.g. {txt.get(nonnum[0])!r}')
            bad = [k for k, v in a['annual'].items() if isinstance(txt.get(k), float) and not np.isclose(v, txt[k], rtol=1e-9, atol=1e-9)]
            if bad:
                issues.append(f'annual_results.txt differs {bad[:4]}')
        if 'scen_techs.yaml' in files:
            try:
                yaml.safe_load(open(f'{rp}/scen_techs.yaml'))
            except Exception as e:
                issues.append(f'scen_techs.yaml not loadable: {str(e)[:120]}')
        for mode in 'BC':
            r = R.get(mode)
            if r is None:
                if mode == 'C' and 'scen_techs.yaml' in files:
                    issues.append('C missing')
                continue
            if r['status'] != 'OK':
                continue
            d = diff_dicts(strip_out(a['scen_techs']), strip_out(r['scen_techs']))
            if d:
                issues.append(f'{mode} scen_techs differ: {"; ".join(d[:4])}')
            ta, tb = total(a), total(r)
            if ta is not None and tb is not None and abs(ta - tb) > max(1e-6 * abs(ta), 1e-3):
                issues.append(f'{mode} total {tb:.2f} vs A {ta:.2f}')
            ad = [k for k in a['annual'] if k in r['annual'] and not np.isclose(a['annual'][k], r['annual'][k], rtol=1e-4, atol=1)]
            if ad:
                info.append(f'{mode} annual differs ({len(ad)}: {ad[:3]})')
        print(f'{n:28s} {"ISSUE " + "; ".join(issues) if issues else "ok"}  [{"; ".join(info)}]')


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else '')
    else:
        check(sys.argv[2])
