# -*- coding: utf-8 -*-
"""
Created on Thu Oct  1 2026

@author: UeliSchilt
"""

"""
For running DEM locally for multiple municipalities in parallel, using the
source code.

Difference to run_dem_local_multiple.py:
    - Several municipalities are simulated at the same time, each in a
      separate process. The solver (Gurobi) uses THREADS_PER_TASK threads per
      municipality.
    - The municipalities (BFS numbers) are read from a .yaml file.
    - The script can be restarted: municipalities with existing results are
      skipped, all others (missing, failed, interrupted) are run.

The model input is not read from the config .yaml files (config/config_files),
but defined in this script (CONFIG_DICT: only the input deviating from the
default values in district_energy_model/input_files/inputs.py).

Output in <ROOT_DIR>/<RESULTS_DIR_NAME>:
    dem_output_BFS_<nr>/        Results of each municipality. A municipality
                                is completed when the file 'run_completed.json'
                                exists in its folder. Folders without this
                                file stem from interrupted runs; they are
                                deleted and rerun. To rerun a completed
                                municipality, delete its folder.
    logs/BFS_<nr>.log           Console output of each run (incl. solver).
    annual_results_summary.csv  Annual results of all completed municipalities.
    failed_municipalities.csv   Municipalities without results due to an error
                                (see log file). They are rerun on restart.
    runtime_summary.txt         Average runtime per municipality and total
                                runtime (wall-clock time of all sessions, i.e.
                                incl. restarts).
    run_settings.json           Settings used for the results in this folder
                                and list of sessions. If results exist, the
                                script stops when CONFIG_DICT has changed, so
                                that results of different settings are not
                                mixed.

Usage (from the 'src' directory; on a remote Linux machine preferably within
tmux/screen or with nohup, so that the run continues after logging out):
    python run_dem_local_parallel.py
Ctrl+C stops all running municipalities; restart the script to continue.
"""

import copy
import datetime
import json
import os
import pickle
import shutil
import signal
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path

import pandas as pd
import psutil
import yaml

# =============================================================================
# USER INPUT
# =============================================================================

# Number of municipalities simulated in parallel:
N_PARALLEL_RUNS = 16 #16

# Number of solver threads per municipality (Gurobi parameter 'Threads').
# N_PARALLEL_RUNS * THREADS_PER_TASK should not exceed the number of CPU cores.
THREADS_PER_TASK = 8

# .yaml file with the municipalities (BFS numbers) to be simulated, e.g.:
#     district_number: [2762, 351, 1061]
# (relative paths are relative to the directory of this script)
BFS_LIST_FILE = '../config/district_numbers_parallel.yaml'

# Root directory (containing the 'data' folder) and name of the results
# directory created therein (relative paths are relative to this script):
ROOT_DIR = '..'
RESULTS_DIR_NAME = 'results_parallel_runs'

# Input deviating from the default input (input_files/inputs.py). The config
# .yaml files are not used. 'district_number' and 'solver_option_Threads' are
# set by this script.
CONFIG_DICT = {
    'simulation':{
        'number_of_days':365,# 365,
        'generate_plots':False,
        'save_results':True,
        },
    'optimisation':{
        'enabled':True,
        },
    }

# =============================================================================

SCRIPT_PATH = Path(__file__).resolve()
WORKER_FLAG = '--worker' # command line flag: run script as worker process for one municipality

COMPLETED_FILE = 'run_completed.json' # written to output folder as last step of a successful run
SUMMARY_FILE = 'annual_results_summary.csv'
FAILED_FILE = 'failed_municipalities.csv'
RUNTIME_FILE = 'runtime_summary.txt'
SETTINGS_FILE = 'run_settings.json'
LOG_DIR_NAME = 'logs'

LAUNCH_INTERVAL = 0.0 # [s] min. time between two process starts (spreads the loading of large input files)
POLL_INTERVAL = 0.1 # [s] interval for checking whether processes have finished
RUNTIME_UPDATE_INTERVAL = 60 # [s] interval for updating the runtime information

SUMMARY_COLUMNS = ['GGDENR', 'munic_name', 'runtime_min', 'finished'] # followed by annual results
FAILED_COLUMNS = ['GGDENR', 'munic_name', 'error_type', 'error_message', 'exit_code', 'runtime_min', 'finished', 'log_file']
FAILED_TYPES_FROM_LIST = ('Omitted', 'UnknownBFS') # re-evaluated from the BFS list in every session


def output_dir_path(results_dir, bfs):
    return results_dir / f"dem_output_BFS_{bfs}"

def log_file_path(results_dir, bfs):
    return results_dir / LOG_DIR_NAME / f"BFS_{bfs}.log"

def error_file_path(results_dir, bfs):
    return results_dir / LOG_DIR_NAME / f"BFS_{bfs}_error.json"

def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def write_json(path, data):
    """Write data to a .json file via a temporary file (i.e. never incomplete)."""
    tmp_path = path.with_name(path.name + '.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False, default=repr)
    os.replace(tmp_path, path)

def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def to_json_value(value):
    """Convert a value (e.g. numpy number) to a type that can be saved in a .json file."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


# =============================================================================
# Worker process: runs one municipality
# =============================================================================

def run_worker():
    """
    Run the model for one municipality. Called by main() in a separate
    process; the arguments are passed via stdin (see start_worker()).

    Returns
    -------
    int
        Exit code of the process (0: success).
    """
    args = pickle.load(sys.stdin.buffer)
    bfs = args['bfs']
    results_dir = Path(args['results_dir'])
    output_dir = output_dir_path(results_dir, bfs)
    error_file = error_file_path(results_dir, bfs)
    started = now()
    t_start = time.time()

    print("==============================================================")
    print(f"DEM parallel run: BFS {bfs} {args['munic_name']}")
    print(f"Started: {started} | Host: {socket.gethostname()} | PID: {os.getpid()}"
          f" | Solver threads: {args['config_dict']['optimisation']['solver_option_Threads']}")
    print("==============================================================")

    try:
        error_file.unlink(missing_ok=True)

        if (output_dir / COMPLETED_FILE).is_file():
            print("Results already exist. Nothing to do.")
            return 0

        if output_dir.exists():
            # Folder without COMPLETED_FILE: incomplete results of an interrupted run
            print(f"Removing incomplete results of an earlier run: {output_dir}")
            shutil.rmtree(output_dir)

        from district_energy_model.model import launch

        model = launch(
            root_dir=args['root_dir'],
            config_files=False,
            config_dict=args['config_dict'],
            output_dir=str(output_dir),
            )

        if model.results_path != 0 and Path(model.results_path) != output_dir:
            raise RuntimeError(f"Results saved to {model.results_path} instead of {output_dir}.")
        output_dir.mkdir(exist_ok=True) # if neither results nor plots are saved

        try:
            annual_results = model.annual_results()
        except AttributeError: # e.g. pareto front
            annual_results = {}
        if not isinstance(annual_results, dict):
            annual_results = {}

        # Mark run as completed (must be the last step):
        write_json(
            output_dir / COMPLETED_FILE,
            {
                'GGDENR':bfs,
                'munic_name':model.com_name_,
                'started':started,
                'finished':now(),
                'runtime_min':round((time.time() - t_start)/60, 2),
                'annual_results':{str(k):to_json_value(v) for k, v in annual_results.items()},
                }
            )

    except Exception as e:
        traceback.print_exc()
        write_json(error_file, {'error_type':type(e).__name__, 'error_message':str(e)})
        try:
            output_dir.rmdir() # only removed if empty (partial results are kept for debugging)
        except OSError:
            pass
        print(f"\nBFS {bfs}: FAILED after {(time.time() - t_start)/60:.1f} min")
        return 1

    print(f"\nBFS {bfs}: completed in {(time.time() - t_start)/60:.1f} min")
    return 0


# =============================================================================
# Main process: distributes the municipalities to worker processes
# =============================================================================

def read_bfs_list(file_path):
    """Read the BFS numbers from a .yaml file (key 'district_number')."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = yaml.safe_load(f)

    if isinstance(content, dict):
        if 'district_number' not in content:
            raise KeyError(f"{file_path}: key 'district_number' not found.")
        content = content['district_number']

    if not isinstance(content, list):
        content = [content]

    bfs_list = []
    for value in content:
        if isinstance(value, bool) or not str(value).strip().isdigit():
            raise ValueError(f"{file_path}: invalid BFS number '{value}'.")
        bfs = int(value)
        if bfs in bfs_list:
            print(f"Note: BFS number {bfs} is listed more than once in {file_path.name}.")
        else:
            bfs_list.append(bfs)

    return bfs_list

def check_config_dict(config, defaults, key_path=''):
    """
    Raise an error if CONFIG_DICT contains keys that do not exist in the
    default input (launch() would only print a warning and ignore them).
    """
    for key, value in config.items():
        path_str = f"{key_path}['{key}']"
        if key not in defaults:
            raise KeyError(f"CONFIG_DICT{path_str}: unknown key. Allowed keys: {sorted(defaults)}")
        if isinstance(value, dict):
            if not isinstance(defaults[key], dict):
                raise TypeError(f"CONFIG_DICT{path_str}: must not be a dict.")
            check_config_dict(value, defaults[key], path_str)

def check_and_save_settings(results_dir, root_dir, bfs_list_file, results_exist):
    """
    Save the settings to SETTINGS_FILE. Stop if the results directory
    contains results computed with a different CONFIG_DICT.

    Returns
    -------
    dict
        Settings, incl. the list of earlier sessions (key 'sessions').
    """
    settings_file = results_dir / SETTINGS_FILE
    config_str = json.dumps(CONFIG_DICT, sort_keys=True, default=repr)
    sessions = []

    if settings_file.is_file():
        previous = read_json(settings_file)
        if results_exist and json.dumps(previous.get('config_dict'), sort_keys=True) != config_str:
            raise RuntimeError(
                f"CONFIG_DICT differs from the settings of the existing results in "
                f"{results_dir} (see {SETTINGS_FILE}). To continue with these "
                f"results, restore the previous CONFIG_DICT. To start with the new "
                f"settings, change RESULTS_DIR_NAME (or rename the existing results "
                f"directory)."
                )
        sessions = previous.get('sessions', [])
        for session in sessions:
            if session.get('status') == 'running': # session ended without final update (e.g. process killed)
                session['status'] = 'aborted'

    settings = {
        'config_dict':json.loads(config_str),
        'n_parallel_runs':N_PARALLEL_RUNS,
        'threads_per_task':THREADS_PER_TASK,
        'root_dir':str(root_dir),
        'bfs_list_file':str(bfs_list_file),
        'host':socket.gethostname(),
        'sessions':sessions,
        }
    write_json(settings_file, settings)
    return settings

def load_munic_names(root_dir):
    """Return {BFS number: municipality name} from the municipality meta data."""
    from district_energy_model import dem_paths
    paths = dem_paths.DEMPaths(str(root_dir))
    df_meta = pd.read_feather(paths.simulation_data_dir + paths.meta_file_general)
    return dict(zip(df_meta['GGDENR'].astype(int), df_meta['Municipality']))

def summary_row(info):
    """Return a row of the summary file from the content of COMPLETED_FILE."""
    row = {
        'GGDENR':int(info['GGDENR']),
        'munic_name':info['munic_name'],
        'runtime_min':info['runtime_min'],
        'finished':info['finished'],
        }
    row.update(info['annual_results'])
    return row

def failed_row(bfs, munic_name, error_type, error_message, exit_code='', runtime_min='', log_file=''):
    return {
        'GGDENR':bfs,
        'munic_name':munic_name,
        'error_type':error_type,
        'error_message':error_message,
        'exit_code':exit_code,
        'runtime_min':runtime_min,
        'finished':now(),
        'log_file':log_file,
        }

def load_completed(results_dir):
    """Return {BFS number: summary row} of all completed municipalities in results_dir."""
    completed = {}
    for completed_file in results_dir.glob(f"dem_output_BFS_*/{COMPLETED_FILE}"):
        try:
            row = summary_row(read_json(completed_file))
            completed[row['GGDENR']] = row
        except (OSError, ValueError, KeyError) as e:
            print(f"WARNING: Could not read {completed_file} ({e}).")
    return completed

def load_failed(results_dir, completed):
    """Return {BFS number: row} of municipalities that failed in earlier sessions and still have no results."""
    failed_file = results_dir / FAILED_FILE
    if not failed_file.is_file():
        return {}
    try:
        df_failed = pd.read_csv(failed_file, dtype=str, keep_default_na=False, encoding='utf-8-sig')
    except (OSError, ValueError) as e:
        print(f"WARNING: Could not read {failed_file} ({e}).")
        return {}

    failed = {}
    for row in df_failed.to_dict('records'):
        bfs = int(row['GGDENR'])
        if bfs not in completed and row.get('error_type') not in FAILED_TYPES_FROM_LIST:
            failed[bfs] = row
    return failed

def write_csv(df, path):
    """Write a .csv file via a temporary file. Failure (e.g. file open in Excel) only prints a warning."""
    tmp_path = path.with_name(path.name + '.tmp')
    try:
        df.to_csv(tmp_path, index=False, encoding='utf-8-sig')
        os.replace(tmp_path, path)
    except OSError as e:
        print(f"WARNING: Could not write {path.name} ({e}). Is the file open in another "
              f"program? It is written again with the next update.")

def write_summary(results_dir, completed):
    rows = [completed[bfs] for bfs in sorted(completed)]
    df_summary = pd.DataFrame(rows) if rows else pd.DataFrame(columns=SUMMARY_COLUMNS)
    write_csv(df_summary, results_dir / SUMMARY_FILE)

def write_failed(results_dir, failed):
    rows = [failed[bfs] for bfs in sorted(failed)]
    write_csv(pd.DataFrame(rows, columns=FAILED_COLUMNS), results_dir / FAILED_FILE)

def runtime_stats(completed, sessions):
    """
    Returns
    -------
    tuple
        Number of completed municipalities, average runtime per municipality
        [min], and total runtime of all sessions [min] (None if not available).
    """
    runtimes = [row['runtime_min'] for row in completed.values()]
    average_min = sum(runtimes)/len(runtimes) if runtimes else None
    total_min = sum(session['duration_min'] for session in sessions) if sessions else None
    return len(runtimes), average_min, total_min

def write_runtime_summary(results_dir, completed, sessions):
    """Write the average runtime per municipality and the total runtime to RUNTIME_FILE."""
    n_completed, average_min, total_min = runtime_stats(completed, sessions)

    lines = [
        f"DEM parallel run: runtime summary ({now()})",
        "==============================================================",
        f"Completed municipalities:          {n_completed}",
        ]
    if average_min is not None:
        lines.append(f"Average runtime per municipality:  {average_min:.2f} min")
    if total_min is not None:
        lines.append(f"Total runtime:                     {total_min:.2f} min ({total_min/60:.2f} h)")
    if average_min is not None and total_min is not None:
        lines.append(f"Total runtime / completed munics:  {total_min/n_completed:.2f} min")
    lines += [
        "--------------------------------------------------------------",
        "Average runtime per municipality: mean runtime of one municipality",
        f"  (runs in parallel; see runtime_min in {SUMMARY_FILE}).",
        "Total runtime: wall-clock time of all sessions (incl. restarts).",
        "==============================================================",
        "Sessions:",
        f"{'#':>3}  {'started':<19}  {'duration [min]':>14}  {'completed':>9}  {'failed':>6}"
        f"  {'runs x threads':>14}  status",
        ]
    for i, session in enumerate(sessions, start=1):
        runs_threads = f"{session['n_parallel_runs']} x {session['threads_per_task']}"
        lines.append(
            f"{i:>3}  {session['started']:<19}  {session['duration_min']:>14.2f}  "
            f"{session['completed']:>9}  {session['failed']:>6}  {runs_threads:>14}  {session['status']}"
            )

    path = results_dir / RUNTIME_FILE
    tmp_path = path.with_name(path.name + '.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    os.replace(tmp_path, path)

def write_runtime_files(results_dir, settings, completed):
    """Save the sessions (SETTINGS_FILE) and write RUNTIME_FILE. Failure only prints a warning."""
    try:
        write_json(results_dir / SETTINGS_FILE, settings)
        write_runtime_summary(results_dir, completed, settings['sessions'])
    except OSError as e:
        print(f"WARNING: Could not write runtime information ({e}).")

def worker_args(bfs, munic_name, root_dir, results_dir):
    """Return the arguments passed to the worker process of a municipality."""
    config_dict = copy.deepcopy(CONFIG_DICT)
    config_dict.setdefault('simulation', {})['district_number'] = bfs
    config_dict.setdefault('optimisation', {})['solver_option_Threads'] = THREADS_PER_TASK
    return {
        'bfs':bfs,
        'munic_name':munic_name,
        'root_dir':str(root_dir),
        'results_dir':str(results_dir),
        'config_dict':config_dict,
        }

def start_worker(args, results_dir, env):
    """Start the worker process for one municipality. Its output is written to the log file."""
    with open(log_file_path(results_dir, args['bfs']), 'wb') as log_file:
        process = subprocess.Popen(
            [sys.executable, '-u', str(SCRIPT_PATH), WORKER_FLAG],
            stdin=subprocess.PIPE,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=str(SCRIPT_PATH.parent),
            env=env,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), # Windows: no console windows
            )
    try:
        process.stdin.write(pickle.dumps(args))
        process.stdin.close()
    except OSError: # worker ended prematurely; reported via its exit code
        pass
    return process

def kill_process_tree(process):
    """Kill a worker process incl. its child processes (e.g. the solver)."""
    try:
        parent = psutil.Process(process.pid)
        processes = parent.children(recursive=True) + [parent]
    except psutil.NoSuchProcess:
        return
    for p in processes:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass
    psutil.wait_procs(processes, timeout=10)

def describe_exit_code(exit_code):
    if exit_code < 0: # Linux: process terminated by a signal
        try:
            signal_name = signal.Signals(-exit_code).name
        except ValueError:
            signal_name = f"signal {-exit_code}"
        message = f"Process terminated by {signal_name}"
        if signal_name == 'SIGKILL':
            message += " (e.g. by the operating system due to insufficient memory)"
        return message
    if exit_code > 255: # Windows: e.g. 0xC0000005 (access violation)
        return f"Process ended with exit code {exit_code} (0x{exit_code:X})"
    return f"Process ended with exit code {exit_code}"

def evaluate_run(results_dir, bfs, exit_code):
    """
    Returns
    -------
    tuple
        (summary row, None) of a completed run, or
        (None, (error type, error message)) of a failed run.
    """
    completed_file = output_dir_path(results_dir, bfs) / COMPLETED_FILE
    if exit_code == 0 and completed_file.is_file():
        try:
            return summary_row(read_json(completed_file)), None
        except (OSError, ValueError, KeyError) as e:
            return None, ('InvalidResultFile', f"Could not read {completed_file} ({e})")

    error_file = error_file_path(results_dir, bfs)
    if error_file.is_file():
        try:
            error = read_json(error_file)
            error_file.unlink()
            return None, (error['error_type'], error['error_message'])
        except (OSError, ValueError, KeyError):
            pass

    if exit_code == 0:
        return None, ('MissingResults', f"'{COMPLETED_FILE}' was not created.")
    return None, ('ProcessTerminated', describe_exit_code(exit_code))

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True) # immediate output, also if redirected to a file (nohup)

    script_dir = SCRIPT_PATH.parent
    root_dir = (script_dir / ROOT_DIR).resolve()
    results_dir = (root_dir / RESULTS_DIR_NAME).resolve()
    bfs_list_file = (script_dir / BFS_LIST_FILE).resolve()

    # -------------------------------------------------------------------------
    # Check input:
    if N_PARALLEL_RUNS < 1 or THREADS_PER_TASK < 1:
        raise ValueError("N_PARALLEL_RUNS and THREADS_PER_TASK must be at least 1.")

    bfs_list = read_bfs_list(bfs_list_file)

    from district_energy_model import dem_constants as C
    from district_energy_model.input_files import inputs as inp

    check_config_dict(CONFIG_DICT, inp.scen_techs)

    if CONFIG_DICT.get('wind_power', {}).get('v_e_wp_national_recalc', False):
        raise ValueError(
            "CONFIG_DICT: 'v_e_wp_national_recalc' overwrites a shared data file "
            "and must not be used in parallel runs. Use run_dem_local.py instead."
            )

    munic_names = load_munic_names(root_dir)

    # -------------------------------------------------------------------------
    # Results directory and status of the municipalities:
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / LOG_DIR_NAME).mkdir(exist_ok=True)

    completed = load_completed(results_dir)
    failed = load_failed(results_dir, completed)

    settings = check_and_save_settings(results_dir, root_dir, bfs_list_file, results_exist=bool(completed))

    todo = []
    for bfs in bfs_list:
        if bfs in completed:
            continue
        if bfs in C.munics_omit:
            failed[bfs] = failed_row(bfs, munic_names.get(bfs, ''), 'Omitted',
                                     "Municipality is on the list of municipalities "
                                     "to omit (munics_omit in dem_constants.py).")
        elif bfs not in munic_names:
            failed[bfs] = failed_row(bfs, '', 'UnknownBFS',
                                     "BFS number not found in the municipality meta data.")
        else:
            todo.append(bfs)

    write_summary(results_dir, completed)
    write_failed(results_dir, failed)

    n_with_results = sum(bfs in completed for bfs in bfs_list)
    if hasattr(os, 'sched_getaffinity'): # Linux: cores available to this process
        n_cores = len(os.sched_getaffinity(0))
    else:
        n_cores = os.cpu_count()

    print("==============================================================")
    print("DEM parallel run")
    print("--------------------------------------------------------------")
    print(f"Municipalities in list:          {len(bfs_list)}")
    print(f"  results exist (skipped):       {n_with_results}")
    print(f"  omitted / unknown BFS number:  {len(bfs_list) - n_with_results - len(todo)}")
    print(f"  to be run:                     {len(todo)}")
    print(f"Parallel runs x solver threads:  {N_PARALLEL_RUNS} x {THREADS_PER_TASK} (CPU cores: {n_cores})")
    print(f"Results directory:               {results_dir}")
    print("==============================================================")
    if N_PARALLEL_RUNS * THREADS_PER_TASK > n_cores:
        print(f"WARNING: {N_PARALLEL_RUNS} x {THREADS_PER_TASK} threads exceed the {n_cores} "
              f"CPU cores; the runs will slow each other down.")

    if not todo:
        write_runtime_files(results_dir, settings, completed)
        print("Nothing to run.")
        return

    # -------------------------------------------------------------------------
    # Run municipalities in parallel:

    # Environment of the worker processes: limit threads of numerical libraries
    # (numpy etc.) to THREADS_PER_TASK; write log files in UTF-8.
    env = os.environ.copy()
    for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        env[var] = str(THREADS_PER_TASK)
    env['PYTHONIOENCODING'] = 'utf-8'

    # Stop on SIGTERM (e.g. 'kill <pid>') in the same way as on Ctrl+C:
    def sigterm_handler(signum, frame):
        raise KeyboardInterrupt
    previous_sigterm_handler = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, sigterm_handler)

    queue = list(todo)
    running = {} # {BFS number: (process, start time)}
    n_completed = 0
    n_failed = 0
    t_last_start = 0.0
    session_status = 'finished'

    # Record this session (total runtime = sum of all sessions):
    t_session = time.time()
    t_runtime_update = t_session
    session = {
        'started':now(),
        'duration_min':0.0,
        'completed':0,
        'failed':0,
        'n_parallel_runs':N_PARALLEL_RUNS,
        'threads_per_task':THREADS_PER_TASK,
        'status':'running',
        }
    settings['sessions'].append(session)
    write_runtime_files(results_dir, settings, completed)

    try:
        while queue or running:
            # Start next municipality:
            if (queue and len(running) < N_PARALLEL_RUNS
                    and time.time() - t_last_start >= LAUNCH_INTERVAL):
                bfs = queue.pop(0)
                process = start_worker(
                    worker_args(bfs, munic_names[bfs], root_dir, results_dir),
                    results_dir,
                    env
                    )
                running[bfs] = (process, time.time())
                t_last_start = time.time()
                print(f"{now()} | started   BFS {bfs:>4} {munic_names[bfs]}"
                      f"  [running: {len(running)}, waiting: {len(queue)}]")

            # Check for finished municipalities:
            for bfs, (process, t_start) in list(running.items()):
                exit_code = process.poll()
                if exit_code is None:
                    continue
                del running[bfs]
                runtime_min = round((time.time() - t_start)/60, 2)

                row, error = evaluate_run(results_dir, bfs, exit_code)
                if row is not None:
                    completed[bfs] = row
                    failed.pop(bfs, None)
                    n_completed += 1
                    write_summary(results_dir, completed)
                    status = f"completed BFS {bfs:>4} {munic_names[bfs]} ({runtime_min:.1f} min)"
                else:
                    log_file = f"{LOG_DIR_NAME}/{log_file_path(results_dir, bfs).name}"
                    failed[bfs] = failed_row(bfs, munic_names[bfs], error[0], error[1],
                                             exit_code, runtime_min, log_file)
                    n_failed += 1
                    message = (error[1].strip().splitlines() or [''])[0][:200]
                    status = (f"FAILED    BFS {bfs:>4} {munic_names[bfs]} ({runtime_min:.1f} min): "
                              f"{error[0]}: {message} -> see {log_file}")
                write_failed(results_dir, failed)

                print(f"{now()} | {status}  [completed: {n_completed}, failed: {n_failed}, "
                      f"remaining: {len(queue) + len(running)}]")

            # Update runtime information regularly (in case this process is
            # killed without a final update, e.g. by 'kill -9'):
            if time.time() - t_runtime_update >= RUNTIME_UPDATE_INTERVAL:
                session.update(duration_min=round((time.time() - t_session)/60, 2),
                               completed=n_completed, failed=n_failed)
                write_runtime_files(results_dir, settings, completed)
                t_runtime_update = time.time()

            time.sleep(POLL_INTERVAL)

    except BaseException as e:
        # Ctrl+C, SIGTERM, or unexpected error: stop all running municipalities
        for process, _ in running.values():
            kill_process_tree(process)
        if not isinstance(e, KeyboardInterrupt):
            session_status = 'error'
            raise
        session_status = 'interrupted'

    finally:
        signal.signal(signal.SIGTERM, previous_sigterm_handler or signal.SIG_DFL)
        write_summary(results_dir, completed)
        write_failed(results_dir, failed)
        session.update(duration_min=round((time.time() - t_session)/60, 2),
                       completed=n_completed, failed=n_failed, status=session_status)
        write_runtime_files(results_dir, settings, completed)

    n_without_results = sum(bfs not in completed for bfs in bfs_list)
    _, average_min, total_min = runtime_stats(completed, settings['sessions'])

    print("==============================================================")
    if session_status == 'interrupted':
        print(f"Interrupted after {session['duration_min']:.1f} min. Running "
              f"municipalities were stopped; restart the script to continue.")
    else:
        print(f"Finished after {session['duration_min']:.1f} min.")
    print("--------------------------------------------------------------")
    print(f"Completed in this session:       {n_completed}")
    print(f"Failed in this session:          {n_failed}")
    print(f"Municipalities with results:     {len(bfs_list) - n_without_results} / {len(bfs_list)}")
    if n_without_results:
        print(f"Without results:                 {n_without_results} (failed ones: see {FAILED_FILE})")
    if average_min is not None:
        print(f"Average runtime per munic.:      {average_min:.2f} min")
    print(f"Total runtime (all sessions):    {total_min:.2f} min (see {RUNTIME_FILE})")
    print(f"Results directory:               {results_dir}")
    print("==============================================================")


if __name__ == "__main__":
    if WORKER_FLAG in sys.argv[1:]:
        sys.exit(run_worker())
    main()
