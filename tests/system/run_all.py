"""
Run the system checks of DEM and print a summary.

    python tests/system/run_all.py                    # matrix + all subsystem suites, 8 workers
    python tests/system/run_all.py -w 16 -p mybranch  # more workers, own result prefix
    python tests/system/run_all.py --only ts,pv       # selected suites
    python tests/system/run_all.py --check-only       # re-check existing results

Suites: matrix (cases/matrix.txt, generic checks), ts, gt, tes, chain, cplant, pv, scen
(subsystem checks against inputs and invariants). 'io' (every subsystem case three times,
output files and YAML round trip) is slow and only runs with --only io.

Output lines: 'ok' / 'ISSUE ...' / 'FAIL ...' (model raised) / 'MISSING'. Some cases are
meant to fail with a validation error; see the case definitions. Results go to _work/
(DEM_CHECK_WORK). Set DEM_SRC to test another checkout, DEM_TEST_ROOT for the data folder.
"""
import argparse
import contextlib
import importlib
import inspect
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _common import PYTHON, run_env  # noqa: E402

SUITES = {'ts': 'check_timeseries', 'gt': 'check_grid_tariffs', 'tes': 'check_tes_sites',
          'chain': 'check_fuel_chains', 'cplant': 'check_central_plants', 'pv': 'check_solar',
          'scen': 'check_scenarios', 'io': 'check_io'}
DEFAULT = ['matrix', 'ts', 'gt', 'tes', 'chain', 'cplant', 'pv', 'scen']


def tally(text):
    words = [l.split()[1] if len(l.split()) > 1 else '' for l in text.splitlines()]
    out = {k: sum(w.startswith(k) for w in words) for k in ('ok', 'ISSUE', 'FAIL', 'MISSING')}
    return out


def run_matrix(prefix, workers, check_only):
    if not check_only:
        subprocess.run([PYTHON, f'{HERE}/run_cases.py', f'{HERE}/cases/matrix.txt', str(workers), f'{prefix}_m_'],
                       env=run_env(), stdout=subprocess.DEVNULL)
    import fuzz
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fuzz.check(f'{prefix}_m_')
    return buf.getvalue()


def run_suite(key, prefix, workers, check_only):
    mod = importlib.import_module(SUITES[key])
    if not check_only:
        with contextlib.redirect_stdout(io.StringIO()):
            if 'flt' in inspect.signature(mod.run).parameters:
                mod.run(prefix, workers, '')
            else:
                mod.run(prefix, workers)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            mod.check(prefix)
        except FileNotFoundError as e:
            print(f'- MISSING {e}')
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-w', '--workers', type=int, default=8)
    ap.add_argument('-p', '--prefix', default='run')
    ap.add_argument('--only', help='comma-separated suites: matrix,' + ','.join(SUITES))
    ap.add_argument('--check-only', action='store_true', help='do not run DEM, only check existing results')
    a = ap.parse_args()
    suites = a.only.split(',') if a.only else DEFAULT
    summary = {}
    for s in suites:
        print(f'===== {s}', flush=True)
        text = run_matrix(a.prefix, a.workers, a.check_only) if s == 'matrix' else run_suite(s, a.prefix, a.workers, a.check_only)
        print(text, flush=True)
        summary[s] = text.strip().splitlines()[-1] if s == 'matrix' else tally(text)
    print('===== summary')
    for s, t in summary.items():
        print(f'{s:8s} {t}')


if __name__ == '__main__':
    main()
