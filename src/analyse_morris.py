#!/usr/bin/env python3
"""Morris screening analysis for a study run by run_dem_local_sensitivities.py.

    python analyse_morris.py [--study-dir DIR]

Writes to the study directory:
    key_outputs.csv            the six key outputs of every completed run
    morris_indices.csv         mu*, mu, sigma and a 95% bootstrap interval of mu*
                               per municipality, output and parameter
    morris_<municipality>.html mu*-sigma charts, one panel per output
    morris_overview.html       relative importance (mu* / largest mu*) heatmaps

Reading the indices: parameter values are normalised to 0..1 over their Morris
range, so mu* is roughly the average absolute change of an output when the
parameter moves across its whole range (in the output's units). A large sigma
relative to mu* means the effect is non-linear or depends on other parameters.

Works on partial studies: an elementary effect is used when both of its runs
completed; outputs are recomputed from the saved run files on every call.
"""
import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

COMPLETE = {'succeeded', 'completed_unverified'}
OUTPUTS = {
    'total_system_cost_CHF': 'Total system cost [CHF/a]',
    'co2_emissions_kg': 'CO₂ emissions [kg/a]',
    'hp_capacity_kW': 'Heat pump capacity [kW_th]',
    'tes_capacity_kWh': 'TES capacity [kWh]',
    'pv_rooftop_capacity_kWp': 'PV rooftop capacity [kWp]',
    'electricity_import_kWh': 'Electricity import [kWh/a]',
}
PARAMETER_LABELS = {
    'electricity_tariff': 'Electricity tariff',
    'electricity_export_tariff': 'Export tariff',
    'quality_factor_multiplier': 'HP quality factor',
    'gas_price': 'Gas price',
    'oil_price': 'Oil price',
    'co2_price': 'CO₂ price',
    'hp_capex_multiplier': 'HP capex',
    'tes_capex_multiplier': 'TES capex',
    'pv_capex_multiplier': 'PV capex',
    'space_heating_multiplier': 'Space heating',
    'interest_rate': 'Interest rate',
}
HP_TECHS = {'heat_pump_old', 'heat_pump_one_to_one_replacement', 'heat_pump_new'}
PV_TECH = re.compile(r'solar_pvrooftop_installation_(\d+)_(?:un)?occupied')
BOOTSTRAP_SAMPLES = 1000

# Chart styling (light surface, single series blue, sequential blue ramp).
SURFACE, INK, INK_SECONDARY, MUTED, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#898781', '#e1e0d9'
SERIES = '#2a78d6'
SEQUENTIAL = [[0.0, '#cde2fb'], [0.25, '#86b6ef'], [0.5, '#3987e5'], [0.75, '#1c5cab'], [1.0, '#0d366b']]
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def capacities(path, column):
    """Sum a Calliope capacity CSV per technology (the part after the last '::')."""
    result = defaultdict(float)
    if path.exists():
        frame = pd.read_csv(path, index_col=0)
        for loc_tech, value in frame[column].items():
            if pd.notna(value):
                result[str(loc_tech).split('::')[-1]] += float(value)
    return result


def key_outputs(attempt):
    costs = json.loads((attempt / 'costs.json').read_text(encoding='utf-8'))
    info = json.loads((attempt / 'model_info.json').read_text(encoding='utf-8'))
    scale = float(info['calliope_energy_scaling_factor'])
    pv_scaling = info['pv_rooftop_capex_scaling']
    energy = capacities(attempt / 'energy_cap.csv', 'energy_cap')
    storage = capacities(attempt / 'storage_cap.csv', 'storage_cap')
    pv_kwp = 0.0
    for tech, cap in energy.items():
        match = PV_TECH.fullmatch(tech)
        if match:
            pv_kwp += cap * float(pv_scaling[int(match.group(1))])
    grid_import = pd.read_csv(attempt / 'hourly_results.csv.gz', usecols=['m_e'])['m_e'].sum()
    return {
        'total_system_cost_CHF': float(costs['monetary']['total']),
        'co2_emissions_kg': float(costs['co2']['total']),
        'hp_capacity_kW': sum(energy.get(tech, 0.0) for tech in HP_TECHS) * scale,
        'tes_capacity_kWh': storage.get('tes_decentralised', 0.0) * scale,
        'pv_rooftop_capacity_kWp': pv_kwp * scale,
        'electricity_import_kWh': float(grid_import),
    }


def load_runs(study):
    manifest = json.loads((study / 'study_manifest.json').read_text(encoding='utf-8'))
    rows = []
    for run in manifest['runs']:
        morris = run.get('morris', {})
        row = {'run_id': run['run_id'], 'municipality': run['municipality']['name'],
               'case': run['case'], 'group': run['group'],
               'trajectory': morris.get('trajectory'), 'step': morris.get('step'),
               'changed': morris.get('changed'), 'levels': morris.get('levels'),
               **run['parameters']}
        status_path = study / run['run_id'] / 'status.json'
        status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {}
        row['status'] = status.get('status', 'pending')
        if row['status'] in COMPLETE:
            # Resolve relative to the study, so a copied/moved study still works.
            attempt = study / run['run_id'] / Path(status['attempt_dir']).name
            try:
                row.update(key_outputs(attempt))
            except Exception as error:  # keep analysing the other runs
                print('WARNING: could not read outputs of %s: %s' % (run['run_id'], error))
        rows.append(row)
    return manifest, pd.DataFrame(rows)


def elementary_effects(runs, levels_count):
    """Yield (municipality, parameter, output, effect) for each usable step."""
    morris = runs[runs['group'] == 'morris'].sort_values(['municipality', 'trajectory', 'step'])
    for (municipality, _), trajectory in morris.groupby(['municipality', 'trajectory']):
        records = trajectory.to_dict('records')
        for previous, current in zip(records, records[1:]):
            if current['step'] != previous['step'] + 1:
                continue
            name = current['changed']
            dx = (current['levels'][name] - previous['levels'][name]) / (levels_count - 1)
            for output in OUTPUTS:
                y0, y1 = previous.get(output), current.get(output)
                if y0 is not None and y1 is not None and np.isfinite(y0) and np.isfinite(y1):
                    yield municipality, name, output, (y1 - y0) / dx


def morris_indices(runs, names, levels_count):
    effects = defaultdict(list)
    for municipality, name, output, effect in elementary_effects(runs, levels_count):
        effects[(municipality, output, name)].append(effect)
    rng = np.random.default_rng(0)
    rows = []
    for municipality in runs['municipality'].unique():
        for output in OUTPUTS:
            for name in names:
                ee = np.array(effects.get((municipality, output, name), []), dtype=float)
                row = {'municipality': municipality, 'output': output, 'parameter': name,
                       'n_effects': len(ee), 'mu': np.nan, 'mu_star': np.nan, 'sigma': np.nan,
                       'mu_star_ci_low': np.nan, 'mu_star_ci_high': np.nan}
                if len(ee):
                    boot = np.abs(rng.choice(ee, size=(BOOTSTRAP_SAMPLES, len(ee)))).mean(axis=1)
                    row.update(mu=ee.mean(), mu_star=np.abs(ee).mean(),
                               sigma=ee.std(ddof=1) if len(ee) > 1 else np.nan,
                               mu_star_ci_low=np.percentile(boot, 2.5),
                               mu_star_ci_high=np.percentile(boot, 97.5))
                rows.append(row)
    table = pd.DataFrame(rows)
    group = table.groupby(['municipality', 'output'])['mu_star']
    top = group.transform('max')
    table['mu_star_relative'] = np.where(top > 0, table['mu_star'] / top, 0.0)
    table['rank'] = group.rank(ascending=False, method='min')
    return table


def style(fig, title, height):
    fig.update_layout(title=dict(text=title, font=dict(size=16, color=INK)), height=height,
                      paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                      font=dict(family=FONT, color=INK_SECONDARY, size=12),
                      margin=dict(l=60, r=30, t=90, b=60), showlegend=False,
                      hoverlabel=dict(bgcolor=SURFACE, font=dict(family=FONT, color=INK)))
    fig.update_xaxes(gridcolor=GRID, linecolor=MUTED, zeroline=False, rangemode='tozero')
    fig.update_yaxes(gridcolor=GRID, linecolor=MUTED, zeroline=False, rangemode='tozero')
    fig.update_annotations(font=dict(size=13, color=INK))


def plot_municipality(table, municipality, path):
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    fig = make_subplots(rows=2, cols=3, subplot_titles=list(OUTPUTS.values()),
                        horizontal_spacing=0.08, vertical_spacing=0.16)
    for i, output in enumerate(OUTPUTS):
        data = table[(table['municipality'] == municipality) & (table['output'] == output)
                     & table['mu_star'].notna()]
        row, col = i // 3 + 1, i % 3 + 1
        if data.empty:
            continue
        labels = [PARAMETER_LABELS.get(p, p) for p in data['parameter']]
        # Label only the influential parameters; all are named in the hover.
        shown = [label if rel >= 0.1 else '' for label, rel in zip(labels, data['mu_star_relative'])]
        sigma = data['sigma'].fillna(0.0)
        # Same range on both axes keeps the sigma = mu* reference line at 45 degrees;
        # the padding leaves room for labels of the largest effects.
        extent = 1.3 * float(max(data['mu_star_ci_high'].max(), data['mu_star'].max(), sigma.max(), 0.0))
        extent = extent if extent > 0 else 1.0
        fig.add_trace(go.Scatter(x=[0, extent], y=[0, extent], mode='lines',
                                 line=dict(color=MUTED, width=1, dash='dot'), hoverinfo='skip'),
                      row=row, col=col)
        fig.add_trace(go.Scatter(
            x=data['mu_star'], y=sigma, mode='markers+text', text=shown, cliponaxis=False,
            textposition='top center', textfont=dict(color=INK_SECONDARY, size=11),
            marker=dict(size=10, color=SERIES, line=dict(color=SURFACE, width=2)),
            error_x=dict(type='data', symmetric=False, color=MUTED, thickness=1, width=0,
                         array=(data['mu_star_ci_high'] - data['mu_star']).fillna(0.0),
                         arrayminus=(data['mu_star'] - data['mu_star_ci_low']).fillna(0.0)),
            customdata=[[label, int(n), float(mu), int(rank) if pd.notna(rank) else None]
                        for label, n, mu, rank in zip(labels, data['n_effects'], data['mu'], data['rank'])],
            hovertemplate=('<b>%{customdata[0]}</b><br>μ* = %{x:,.4g}<br>σ = %{y:,.4g}'
                           '<br>μ = %{customdata[2]:,.4g}<br>rank %{customdata[3]}'
                           '<br>effects used: %{customdata[1]}<extra></extra>')),
            row=row, col=col)
        fig.update_xaxes(title_text='μ* (mean absolute effect)', range=[0, extent], row=row, col=col)
        fig.update_yaxes(title_text='σ (spread of effects)', range=[0, extent], row=row, col=col)
    style(fig, 'Morris screening – %s (dotted line: σ = μ*; bars: 95%% interval of μ*)'
          % municipality, 820)
    fig.write_html(path, include_plotlyjs=True, default_width='100%')


def plot_overview(table, names, path):
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    municipalities = list(table['municipality'].unique())
    fig = make_subplots(rows=1, cols=len(municipalities), subplot_titles=municipalities,
                        horizontal_spacing=0.04, shared_yaxes=True)
    ylabels = [PARAMETER_LABELS.get(p, p) for p in names]
    xlabels = [label.split(' [')[0] for label in OUTPUTS.values()]
    for i, municipality in enumerate(municipalities, 1):
        data = table[table['municipality'] == municipality]
        z = [[data[(data['parameter'] == p) & (data['output'] == o)]['mu_star_relative'].iloc[0]
              for o in OUTPUTS] for p in names]
        mu_star = [[data[(data['parameter'] == p) & (data['output'] == o)]['mu_star'].iloc[0]
                    for o in OUTPUTS] for p in names]
        fig.add_trace(go.Heatmap(
            z=z, x=xlabels, y=ylabels, zmin=0, zmax=1, colorscale=SEQUENTIAL, xgap=2, ygap=2,
            showscale=(i == len(municipalities)),
            colorbar=dict(title=dict(text='μ* / max μ*', font=dict(color=INK_SECONDARY)),
                          tickfont=dict(color=INK_SECONDARY)),
            customdata=mu_star,
            hovertemplate=('<b>%{y}</b> → %{x}<br>relative μ* = %{z:.2f}'
                           '<br>μ* = %{customdata:,.4g}<extra></extra>')),
            row=1, col=i)
        fig.update_xaxes(tickangle=-40, row=1, col=i)
    style(fig, 'Relative importance of parameters per output (1 = most influential parameter for that output)',
          560)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False, autorange='reversed')
    fig.write_html(path, include_plotlyjs=True, default_width='100%')


def main():
    default_study = None
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from run_dem_local_sensitivities import STUDY_DIR as default_study
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--study-dir', type=Path, default=default_study,
                        help='Study directory (default: STUDY_DIR of run_dem_local_sensitivities.py).')
    args = parser.parse_args()
    if args.study_dir is None:
        parser.error('--study-dir is required.')
    study = args.study_dir.resolve()
    manifest, runs = load_runs(study)
    morris_runs = [run for run in manifest['runs'] if 'morris' in run]
    if not morris_runs:
        raise SystemExit('No Morris runs in this study manifest.')
    names = list(morris_runs[0]['morris']['levels'])
    levels_count = int(morris_runs[0]['settings']['MORRIS_LEVELS'])

    output_columns = [c for c in runs.columns if c != 'levels']
    runs[output_columns].to_csv(study / 'key_outputs.csv', index=False, encoding='utf-8-sig')
    table = morris_indices(runs, names, levels_count)
    table.to_csv(study / 'morris_indices.csv', index=False, encoding='utf-8-sig')

    done = runs['status'].isin(COMPLETE)
    print('Runs completed: %d of %d.' % (done.sum(), len(runs)))
    for municipality in runs['municipality'].unique():
        slug = ''.join(c if c.isalnum() else '_' for c in municipality)
        plot_municipality(table, municipality, study / ('morris_%s.html' % slug))
        print('\n%s: top 3 parameters by mu* (effects used per parameter in brackets)' % municipality)
        for output, label in OUTPUTS.items():
            data = table[(table['municipality'] == municipality) & (table['output'] == output)]
            data = data[data['mu_star'] > 0].sort_values('mu_star', ascending=False).head(3)
            ranking = ', '.join('%s (%d)' % (PARAMETER_LABELS.get(p, p), n)
                                for p, n in zip(data['parameter'], data['n_effects']))
            print('  %-30s %s' % (label, ranking or 'no non-zero effects yet'))
    plot_overview(table, names, study / 'morris_overview.html')
    print('\nWritten to %s: key_outputs.csv, morris_indices.csv, morris_*.html' % study)


if __name__ == '__main__':
    main()
