"""Create a pareto front, then try to load it with toggle_load_pareto_results (only settable in inputs.py)."""
import io, contextlib, os, shutil, sys, traceback
T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK  # noqa: E402
from district_energy_model.model import launch
from district_energy_model.input_files import inputs as inp
out = f'{WORK}/outputs/pareto_load'
for d in [out, out + ' (1)']:
    shutil.rmtree(d, ignore_errors=True)
cfg = {'simulation': {'number_of_days': 2, 'generate_plots': False, 'save_results': True},
       'optimisation': {'enabled': True, 'pareto_monetary_co2': True, 'N_pareto': 3, 'solver_option_Threads': 8}}
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    launch(root_dir=ROOT, config_files=False, config_dict=cfg, output_dir=out)
print('created:', sorted(os.listdir(out)))
inp.toggle_load_pareto_results = True
cfg['simulation']['generate_plots'] = True
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        m = launch(root_dir=ROOT, config_files=False, config_dict=cfg, output_dir=out)
    print('loaded OK:', len(m.pareto_results), 'points; output dir', m.results_path, sorted(os.listdir(m.results_path)))
except Exception as e:
    print("LOAD FAILED:", type(e).__name__, str(e)[:200]); traceback.print_exc()
