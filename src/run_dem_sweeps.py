#!/usr/bin/env python3
"""Run one-at-a-time parameter sweeps with DEM (Python 3.9+).

Reuses run_dem_local_sensitivities.py unchanged: the same municipalities,
reference values (REFERENCE), parameter ranges (MORRIS_PARAMETERS), DEM
settings, worker, parallel execution and saved outputs. Only the design differs:

  1. every parameter swept over its range (SWEEP_POINTS values), others at reference
  2. FINE_PARAMETERS swept with FINE_POINTS values, to locate thresholds
  3. CONDITIONAL_SWEEPS: a parameter swept while a second parameter is held at
     its low and at its high bound (shows whether the effect depends on it)
  4. GRID_2D: a full grid over two parameters

Blocks 2-4 are meant to be filled in after the Morris screening. A study can be
extended: add points or blocks and run again; completed runs are kept and only
new parameter combinations are run. A combination needed by several curves is
run once and shared.

    python run_dem_sweeps.py --dry-run
    python run_dem_sweeps.py --jobs 8 --solver-threads 16
    python analyse_sweeps.py
"""
import argparse
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_dem_local_sensitivities as runner  # noqa: E402

# =========================== EDIT SETTINGS HERE =============================
STUDY_DIR = runner.PROJECT_ROOT / 'dem_sweep_study_2050'
MAX_RUNS_PER_MUNICIPALITY = 200              # includes runs of earlier extensions
SWEEP_POINTS = 7                             # block 1: values per parameter over its range
# Choices below follow the Morris screening (focus: HP, TES and PV capacity).
SWEEP_POINTS_PER_PARAMETER = {'gas_price': 3}   # negligible for all focus outputs
FINE_PARAMETERS = [                          # block 2: most influential, with thresholds
    'electricity_tariff', 'hp_capex_multiplier', 'tes_capex_multiplier',
    'pv_capex_multiplier', 'oil_price', 'co2_price', 'electricity_export_tariff']
FINE_POINTS = 13                             # 13 = the 7-point grid plus the midpoints
CONDITIONAL_SWEEPS = [                       # block 3: pairs with large sigma (interactions)
    ('tes_capex_multiplier', 'electricity_tariff'),
    ('hp_capex_multiplier', 'electricity_tariff'),
    ('electricity_tariff', 'oil_price'),
    ('electricity_tariff', 'co2_price'),
    ('pv_capex_multiplier', 'electricity_export_tariff')]
CONDITIONAL_POINTS = 7
GRID_2D = [('electricity_tariff', 'hp_capex_multiplier')]   # block 4: top pair for HP and TES
GRID_POINTS = 6
# ========================= END EDITABLE SETTINGS =============================

# Short parameter codes keep run folder names (and Windows paths) short.
SHORT_NAMES = {
    'electricity_tariff': 'tariff', 'electricity_export_tariff': 'export',
    'quality_factor_multiplier': 'qf', 'gas_price': 'gas', 'oil_price': 'oil', 'co2_price': 'co2',
    'hp_capex_multiplier': 'hpcapex', 'tes_capex_multiplier': 'tescapex',
    'pv_capex_multiplier': 'pvcapex', 'space_heating_multiplier': 'sh', 'interest_rate': 'interest',
}


def sweep_values(name, points):
    low, high = runner.MORRIS_PARAMETERS[name]
    return [round(low + (high - low) * i / (points - 1), 10) for i in range(points)]


def parameter_key(params):
    return tuple(sorted((k, round(float(v), 10)) for k, v in params.items()))


def build_cases():
    names = list(runner.MORRIS_PARAMETERS)
    used = (list(SWEEP_POINTS_PER_PARAMETER) + list(FINE_PARAMETERS)
            + [p for pair in CONDITIONAL_SWEEPS for p in pair] + [p for pair in GRID_2D for p in pair])
    unknown = sorted(set(used) - set(names))
    if unknown:
        raise ValueError('Not in MORRIS_PARAMETERS: ' + ', '.join(unknown))
    if any(p == q for p, q in list(CONDITIONAL_SWEEPS) + list(GRID_2D)):
        raise ValueError('Conditional sweeps and grids need two different parameters.')
    counts = [SWEEP_POINTS, FINE_POINTS, CONDITIONAL_POINTS, GRID_POINTS, *SWEEP_POINTS_PER_PARAMETER.values()]
    if any(int(n) < 2 for n in counts):
        raise ValueError('Every sweep needs at least 2 points.')
    def tag(name, value):
        return '%s_%.6g' % (SHORT_NAMES.get(name, name), value)

    cases, seen = [], set()

    def add(name, group, meta, values):
        params = dict(runner.REFERENCE, **values)
        key = parameter_key(params)
        if key not in seen:  # identical combinations are run once
            seen.add(key)
            cases.append({'case': name, 'group': group, 'parameters': params,
                          'no_tes': False, 'sweep': meta})

    add('reference', 'reference', {}, {})
    for p in names:
        for v in sweep_values(p, SWEEP_POINTS_PER_PARAMETER.get(p, SWEEP_POINTS)):
            add('sw_' + tag(p, v), 'sweep', {'parameter': p}, {p: v})
    for p in FINE_PARAMETERS:
        for v in sweep_values(p, FINE_POINTS):
            add('sw_' + tag(p, v), 'fine', {'parameter': p}, {p: v})
    for p, c in CONDITIONAL_SWEEPS:
        for cv in runner.MORRIS_PARAMETERS[c]:
            for v in sweep_values(p, CONDITIONAL_POINTS):
                add('cond_%s__%s' % (tag(p, v), tag(c, cv)), 'conditional',
                    {'parameter': p, 'context': {c: cv}}, {p: v, c: cv})
    for px, py in GRID_2D:
        xs, ys = sweep_values(px, GRID_POINTS), sweep_values(py, GRID_POINTS)
        for vx in xs:
            for vy in ys:
                # Axis values are stored because grid points equal to sweep points are shared.
                add('grid_%s__%s' % (tag(px, vx), tag(py, vy)), 'grid',
                    {'grid': [px, py], 'grid_values': [xs, ys]}, {px: vx, py: vy})
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dry-run', action='store_true', help='List runs; no DEM/data imports or writes.')
    parser.add_argument('--jobs', type=int, default=runner.PARALLEL_RUNS,
                        help='DEM runs executed in parallel (default: PARALLEL_RUNS of the runner).')
    parser.add_argument('--solver-threads', type=int, default=runner.SOLVER_THREADS_PER_RUN,
                        help='Gurobi threads per run (default: available CPUs // jobs).')
    args = parser.parse_args()
    jobs = args.jobs
    if jobs < 1:
        raise ValueError('--jobs must be at least 1.')
    threads = args.solver_threads or max(1, runner.available_cpus() // jobs)
    if threads < 1:
        raise ValueError('--solver-threads must be at least 1.')

    cases = build_cases()
    settings = runner.settings_snapshot()
    plans = []
    for municipality in runner.MUNICIPALITIES:
        slug = ''.join(c if c.isalnum() else '_' for c in municipality['name'])
        for case in cases:
            plans.append(dict(case, municipality=municipality,
                              run_id=slug + '__' + case['case'], settings=settings))
    if len(cases) > MAX_RUNS_PER_MUNICIPALITY:
        raise ValueError('%d runs per municipality; maximum is %d.' % (len(cases), MAX_RUNS_PER_MUNICIPALITY))
    if args.dry_run:
        groups = {}
        for case in cases:
            groups[case['group']] = groups.get(case['group'], 0) + 1
        print('Runs per municipality: %d (%s)' % (len(cases), ', '.join('%s %d' % kv for kv in groups.items())))
        print('Block 1 values per parameter:')
        for p in runner.MORRIS_PARAMETERS:
            values = sweep_values(p, SWEEP_POINTS_PER_PARAMETER.get(p, SWEEP_POINTS))
            print('  %-26s %s  (reference %g)' % (p, ', '.join('%.4g' % v for v in values), runner.REFERENCE[p]))
        for i, p in enumerate(plans, 1):
            print('%03d %s %s' % (i, p['run_id'], p['parameters']))
        print('Total: %d runs (this design). Output: %s' % (len(plans), STUDY_DIR))
        print('Parallel: %d run(s) at once x %d solver thread(s); %d CPUs available.'
              % (jobs, threads, runner.available_cpus()))
        return 0

    if not Path(runner.BASE_INPUT_FILE).is_file():
        raise FileNotFoundError('BASE_INPUT_FILE of the runner does not exist.')
    if not (Path(runner.PROJECT_ROOT) / 'data').is_dir():
        raise FileNotFoundError('PROJECT_ROOT must contain the DEM data/ directory.')
    study = Path(STUDY_DIR).resolve()
    study.mkdir(parents=True, exist_ok=True)
    # The fingerprint covers what determines a run's result (runner code, base
    # inputs, DEM settings) but not the design, so the design can grow.
    runner_path = Path(runner.__file__).resolve()
    fingerprint = hashlib.sha256((runner_path.read_text(encoding='utf-8')
                                  + Path(runner.BASE_INPUT_FILE).read_text(encoding='utf-8')
                                  + json.dumps(settings, sort_keys=True)).encode('utf-8')).hexdigest()
    manifest_path = study / 'study_manifest.json'
    created = runner.now()
    if manifest_path.exists():
        manifest = runner.read_json(manifest_path)
        if manifest['fingerprint'] != fingerprint:
            raise ValueError('Runner script, base inputs or DEM settings changed since this study '
                             'started. Choose a new STUDY_DIR to keep results comparable.')
        created = manifest['created_at']
        known = {run['run_id']: run for run in manifest['runs']}
        existing = {(run['municipality']['name'], parameter_key(run['parameters'])) for run in manifest['runs']}
        for plan in plans:
            if plan['run_id'] in known and parameter_key(known[plan['run_id']]['parameters']) != parameter_key(plan['parameters']):
                raise ValueError('Run %s exists with different parameters.' % plan['run_id'])
        all_plans = manifest['runs'] + [
            plan for plan in plans if plan['run_id'] not in known
            and (plan['municipality']['name'], parameter_key(plan['parameters'])) not in existing]
    else:
        all_plans = plans
    per_municipality = {}
    for plan in all_plans:
        name = plan['municipality']['name']
        per_municipality[name] = per_municipality.get(name, 0) + 1
    if max(per_municipality.values()) > MAX_RUNS_PER_MUNICIPALITY:
        raise ValueError('With earlier runs this study would have %d runs per municipality; maximum is %d.'
                         % (max(per_municipality.values()), MAX_RUNS_PER_MUNICIPALITY))
    runner.atomic_json(manifest_path, {'fingerprint': fingerprint, 'created_at': created,
                                       'updated_at': runner.now(), 'runs': all_plans})
    if not (study / 'runner_snapshot.py').exists():
        (study / 'runner_snapshot.py').write_bytes(runner_path.read_bytes())
        (study / 'base_inputs_snapshot.py').write_bytes(Path(runner.BASE_INPUT_FILE).read_bytes())
    (study / 'sweep_script_snapshot.py').write_bytes(Path(__file__).read_bytes())

    runner.save_summary(study, all_plans)
    queue = []
    for i, spec in enumerate(all_plans, 1):
        run_dir = study / spec['run_id']
        run_dir.mkdir(exist_ok=True)
        status_path = run_dir / 'status.json'
        previous = runner.read_json(status_path) if status_path.exists() else {}
        if runner.RESUME and previous.get('status') in runner.COMPLETE:
            continue
        if runner.RESUME and previous.get('status') == 'failed' and not runner.RETRY_FAILED_RUNS:
            continue
        queue.append((i, spec))
    print('%d of %d runs already completed. Starting %d run(s): up to %d in parallel, '
          '%d solver thread(s) each.' % (len(all_plans) - len(queue), len(all_plans), len(queue), jobs, threads),
          flush=True)
    active = []
    try:
        while queue or active:
            while queue and len(active) < jobs:
                index, spec = queue.pop(0)
                job = runner.new_attempt(study, spec, index, len(all_plans))
                active.append(job)
                try:
                    job['process'], job['log'] = runner.start_attempt(spec, job['attempt'], threads)
                except Exception as error:
                    job['record'].update(status='failed', error_type=type(error).__name__, error=str(error))
                    (job['attempt'] / 'parent_traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
                    active.remove(job)
                    runner.conclude_attempt(study, all_plans, job)
            if active:
                time.sleep(runner.POLL_SECONDS)
            for job in list(active):
                code = job['process'].poll()
                if code is None and time.monotonic() < job['deadline']:
                    continue
                active.remove(job)
                runner.conclude_attempt(study, all_plans, job, code)
    except BaseException as error:
        # Never leave parallel workers running without a parent.
        for job in active:
            if job['process'] is not None:
                runner.stop_process(job['process'])
        for job in list(active):
            runner.conclude_attempt(study, all_plans, job, interrupted=True)
        if isinstance(error, KeyboardInterrupt):
            return 130
        raise
    failures = sum(runner.read_json(study / p['run_id'] / 'status.json')['status'] == 'failed' for p in all_plans)
    print('Study finished. Results: %s\n%d failed run(s); inspect study_events.jsonl and per-attempt logs.'
          % (study / 'study_results.csv', failures))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
