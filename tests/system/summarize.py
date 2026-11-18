import json, glob, sys, os
import pandas as pd
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
from _common import WORK  # noqa: E402
names = sys.argv[1:]
rows = {}
for f in sorted(glob.glob(f'{WORK}/results/*.json')):
    d = json.load(open(f))
    if names and d['name'] not in names: continue
    r = dict(d.get('annual', {}))
    c = d.get('costs', {})
    if isinstance(c, dict):
        m = c.get('monetary'); r['cost_CHF'] = m.get('total') if isinstance(m, dict) else m
        r['cost_co2'] = c.get('co2')
    r['status'] = d['status']
    rows[d['name']] = r
df = pd.DataFrame(rows).T
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
cols = [c for c in ['status','d_h_yr','d_e_yr','v_h_hp_yr','v_h_ob_yr','v_h_gb_yr','v_h_eh_yr','v_h_dh_yr','v_e_pvrooftop_yr','v_e_wp_yr','d_e_ev_yr','m_e_yr','f_e_yr','m_oil_yr','m_gas_yr','v_co2_tot_yr','cost_CHF','cost_co2','d_h_unmet_yr','d_e_unmet_yr'] if c in df]
num = df[cols].drop(columns='status').apply(pd.to_numeric, errors='coerce')
print(pd.concat([df['status'], (num/1000).round(1)], axis=1).to_string())
