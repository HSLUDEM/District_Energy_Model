import io, contextlib, os, sys
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
from _common import ROOT  # noqa: E402
from district_energy_model.model import launch
sim = {'number_of_days': 2, 'district_number': 2762, 'generate_plots': False, 'save_results': False}
def run(cfg):
    with contextlib.redirect_stdout(io.StringIO()):
        m = launch(root_dir=ROOT, config_files=False, config_dict=cfg)
    yr = m.annual_results()
    return m, round(yr['v_e_pvrooftop_yr']), round(yr['v_h_ob_yr']), round(yr['v_h_hp_yr'])
_, *a = run({'simulation': dict(sim)})
print('run 1 (defaults)                  pv, ob, hp =', a)
_, *b = run({'simulation': dict(sim), 'scenarios': {'pv_integration': True, 'fossil_heater_retrofit': True}})
print('run 2 (pv_integration + fhr)      pv, ob, hp =', b)
m, *c = run({'simulation': dict(sim)})
print('run 3 (defaults again)            pv, ob, hp =', c)
print('run 3 scen_techs scenarios:', m.scen_techs['scenarios'])
