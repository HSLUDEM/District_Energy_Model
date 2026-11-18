"""Extract plotly data from DEM html plots and compare with hourly results."""
import json, re, sys
import pandas as pd
out = sys.argv[1]
def figdata(path):
    h = open(path).read()
    m = re.search(r'Plotly\.newPlot\(\s*"[^"]+",\s*(\[.*?\])\s*,\s*\{', h, re.S)
    return json.loads(m.group(1))
df = pd.read_csv(f'{out}/hourly_results.csv', index_col=0)
s = figdata(f'{out}/sankey.html')[0]
labels = s['node']['label']; L = s['link']
flows = {(labels[a], labels[b]): v for a, b, v in zip(L['source'], L['target'], L['value'])}
print('sankey flows (MWh):'); [print(f'   {k[0]:>24s} -> {k[1]:<24s} {v/1e3 if v > 1e3 else v:10.1f}') for k, v in sorted(flows.items(), key=lambda x: -x[1])[:14]]
print('results: oil import %.1f MWh, gas import %.1f MWh, HP heat %.1f, HP el %.1f, grid import %.1f' % (df.m_oil.sum()/1e3, df.m_gas.sum()/1e3, df.v_h_hp.sum()/1e3, df.u_e_hp.sum()/1e3, df.m_e.sum()/1e3))
hb = figdata(f'{out}/heat_balance_daily.html')
print('heat_balance_daily traces (sum over days, MWh):', {t.get('name'): round(sum(v for v in t['y'] if v is not None)/1e3, 1) for t in hb if 'y' in t and sum(abs(v) for v in t['y'] if v is not None) > 0})
