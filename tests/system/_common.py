"""
Paths and environment shared by the system checks.

    DEM_TEST_ROOT   directory with the DEM 'data' folder (default: repository root)
    DEM_CHECK_WORK  where results and model outputs go (default: tests/system/_work)
    DEM_SRC         'src' folder of another DEM checkout to test (default: installed package)

The Gurobi licence is taken from the environment (GRB_LICENSE_FILE) as usual.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.environ.get('DEM_TEST_ROOT', os.path.join(HERE, '..', '..')))
WORK = os.path.abspath(os.environ.get('DEM_CHECK_WORK', os.path.join(HERE, '_work')))
INPUTS = os.path.join(HERE, 'inputs')
PYTHON = sys.executable
MASTER_DATA = os.path.join(ROOT, 'data', 'master_data', 'master_data_general.feather')
os.makedirs(os.path.join(WORK, 'results'), exist_ok=True)
os.makedirs(os.path.join(WORK, 'outputs'), exist_ok=True)


def run_env():
    """Environment for the DEM subprocesses (DEM_SRC first on the path, if set)."""
    env = dict(os.environ)
    if os.environ.get('DEM_SRC'):
        env['PYTHONPATH'] = os.environ['DEM_SRC'] + os.pathsep + env.get('PYTHONPATH', '')
    return env


def expand(text):
    """Replace the {HERE} placeholder in case files and input configs by this folder."""
    return text.replace('{HERE}', HERE)
