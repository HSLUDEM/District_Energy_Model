"""Run one DEM case in-process: python run_case.py <name> '<json config_dict>' [yaml_config_dir]

Summary (status, annual results, costs, NaN/negative checks) in _work/results/<name>.json,
DEM output in _work/outputs/<name>/. Prefer run_cases.py, which runs each case in a fresh process."""
import json, sys, time, traceback, io, contextlib, os
import numpy as np

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
from _common import ROOT, WORK, expand  # noqa: E402
name, cfg = sys.argv[1], json.loads(expand(sys.argv[2]))
cfg_dir = expand(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else None
# Optional launch() keyword arguments (e.g. hist_data_year), not part of scen_techs:
launch_kwargs = cfg.pop('_launch', {})
cfg.setdefault('simulation', {})
cfg['simulation'].setdefault('number_of_days', 7)
cfg['simulation'].setdefault('district_number', 2762)
cfg['simulation'].setdefault('generate_plots', False)
cfg['simulation'].setdefault('save_results', True)
out = {'name': name, 'config': cfg, 'launch_kwargs': launch_kwargs}
t0 = time.time()
log = io.StringIO()
try:
    from district_energy_model.model import launch
    with contextlib.redirect_stdout(log):
        if cfg_dir:
            m = launch(root_dir=ROOT, config_dir=cfg_dir, output_dir=f'{WORK}/outputs/{name}', **launch_kwargs)
        else:
            m = launch(root_dir=ROOT, config_files=False, config_dict=cfg, output_dir=f'{WORK}/outputs/{name}', **launch_kwargs)
    out['status'] = 'OK'
    try:
        yr = m.annual_results()
        keys = ['d_e_yr','d_h_yr','d_h_unmet_yr','d_e_unmet_yr','m_e_yr','f_e_yr','v_h_hp_yr','v_h_ob_yr','v_h_gb_yr','v_h_wb_yr','v_h_eh_yr','v_h_dh_yr','v_h_solar_yr','v_e_pvrooftop_yr','v_e_wp_yr','v_e_hydro_yr','m_oil_yr','m_gas_yr','v_co2_tot_yr','d_e_ev_yr','v_e_bes_yr','u_e_bes_yr','v_h_tesdc_yr','u_h_tesdc_yr']
        out['annual'] = {k: float(v) for k, v in yr.items() if isinstance(v, (int, float, np.integer, np.floating))}
    except Exception as e:
        out['annual_err'] = repr(e)
    try:
        df = m.hourly_results()
        if hasattr(df, 'columns'):
            num = df.select_dtypes('number')
            bad = ~np.isfinite(num)
            neg_ok = ('sos', 'soc', 'd_e_ev_cp_dev', 'cops')
            neg = [c for c in num.columns if not c.startswith(neg_ok) and num[c].min() < -0.1]
            out['checks'] = {'nonfinite_cols': [c for c in num.columns if bad[c].any()], 'negative_cols': neg,
                             'n_hours': len(df)}
    except Exception as e:
        out['checks_err'] = repr(e)
    try:
        c = m.total_cost()
        out['costs'] = json.loads(json.dumps(c.get('cost_overview', c), default=str))
    except Exception as e:
        out['cost_err'] = repr(e)
except BaseException as e:
    out['status'] = 'FAIL'
    out['error'] = f'{type(e).__name__}: {e}'[:2000]
    out['traceback'] = traceback.format_exc()[-4000:]
out['runtime_s'] = round(time.time() - t0, 1)
out['log_tail'] = log.getvalue()[-3000:]
json.dump(out, open(f'{WORK}/results/{name}.json', 'w'), indent=1, default=str)
print(name, out['status'], out.get('error', '')[:300], f"{out['runtime_s']}s")
