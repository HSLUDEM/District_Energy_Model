"""
Run a case file, each case in a fresh process (results in _work/results/<name>.json).

    python run_cases.py <cases.txt> [workers] [name_prefix]

Case files are tab-separated: name, config_dict (JSON), optional YAML config directory.
'{HERE}' in a case file stands for this folder. The key "_launch" in a config_dict is passed
to launch() (e.g. {"_launch": {"hist_data_year": 2018}}). Set DEM_SRC to test another checkout.
"""
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
from _common import WORK, PYTHON, run_env  # noqa: E402

cases = [l.rstrip('\n').split('\t') for l in open(sys.argv[1]) if l.strip()]
workers = int(sys.argv[2]) if len(sys.argv) > 2 else 8
prefix = sys.argv[3] if len(sys.argv) > 3 else ''


def run(c):
    name = prefix + c[0]
    shutil.rmtree(f'{WORK}/outputs/{name}', ignore_errors=True)
    args = [PYTHON, f'{S}/run_case.py', name, c[1]] + ([c[2]] if len(c) > 2 and c[2] else [])
    r = subprocess.run(args, capture_output=True, text=True, env=run_env())
    open(f'{WORK}/results/{name}.stderr', 'w').write(r.stderr)
    return r.stdout.strip() or f'{name} CRASH {r.stderr.strip()[-300:]}'


with ThreadPoolExecutor(workers) as ex:
    for out in ex.map(run, cases):
        print(out, flush=True)
