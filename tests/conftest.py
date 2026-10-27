"""
Shared fixtures for the DEM regression tests.

The tests run the model on real input data. Set DEM_TEST_ROOT to a
directory containing the 'data' folder (default: repository root).
Optimisation tests are skipped if Gurobi is not available.
"""
import contextlib
import copy
import io
import os
from pathlib import Path

import pytest

ROOT = Path(os.environ.get('DEM_TEST_ROOT', Path(__file__).resolve().parents[1]))
HAS_DATA = (ROOT / 'data' / 'master_data' / 'meta_data_general.feather').is_file()


def _has_gurobi():
    try:
        import gurobipy  # noqa: F401
        return True
    except ImportError:
        return False


requires_data = pytest.mark.skipif(not HAS_DATA, reason=f'no input data in {ROOT}/data')
requires_solver = pytest.mark.skipif(not _has_gurobi(), reason='Gurobi not available')

OPT = {'enabled': True, 'solver_option_Threads': 4}


def deep_update(base, extra):
    out = copy.deepcopy(base)
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_update(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


@pytest.fixture
def run_dem(tmp_path):
    """Run DEM with a config_dict (7 days, Allschwil, no output files by default)."""
    from district_energy_model.model import launch

    def _run(cfg=None, days=7, quiet=True, **launch_kwargs):
        config = deep_update(
            {'simulation': {'number_of_days': days, 'district_number': 2762,
                            'generate_plots': False, 'save_results': False}},
            cfg or {})
        kwargs = dict(root_dir=str(ROOT), config_files=False, config_dict=config,
                      output_dir=str(tmp_path / 'out'))
        kwargs.update(launch_kwargs)
        if quiet:
            with contextlib.redirect_stdout(io.StringIO()):
                return launch(**kwargs)
        return launch(**kwargs)

    return _run


def cost_overview(model):
    """Cost module totals (simulation and optimisation)."""
    costs = model.total_cost()
    if 'Kostenmodul' in costs:
        costs = costs['Kostenmodul']
    return costs['cost_overview']
