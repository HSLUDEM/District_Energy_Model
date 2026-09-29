#!/usr/bin/env python3
"""Tables and charts for a sweep study run by run_dem_sweeps.py.

    python analyse_sweeps.py [--study-dir DIR]

Writes to the study directory:
    key_outputs.csv               the six key outputs of every completed run
    sweep_curves.csv              output vs. parameter for every sweep (long format)
    tornado.csv                   output range per parameter over its full sweep
    sweeps_<municipality>.html    per output: a tornado chart, one panel per
                                  parameter (including conditional sweeps), 2D grids

A curve consists of all completed runs in which only the swept parameter differs
from the base point (reference, or reference with the condition applied), so
points from different blocks and extensions are combined automatically.
Works on partial studies.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse_morris as am  # noqa: E402

CONDITION_COLOURS = {'reference': am.SERIES, 'low': '#eb6834', 'high': '#1baf7a'}
REFERENCE_RING = am.INK


def label(name):
    return am.PARAMETER_LABELS.get(name, name)


def curve(runs, parameter, base, names, output):
    mask = runs['status'].isin(am.COMPLETE)
    for other in names:
        if other != parameter:
            mask &= np.isclose(runs[other].astype(float), float(base[other]), rtol=0, atol=1e-9)
    data = runs[mask]
    if output not in data:
        return data.iloc[0:0]
    return data[data[output].notna()].sort_values(parameter)


def conditions(manifest):
    """Unique (parameter, context_name, context_value, role) from conditional runs."""
    found = {}
    for run in manifest['runs']:
        context = run.get('sweep', {}).get('context')
        if context:
            (name, value), = context.items()
            low, high = run['settings']['MORRIS_PARAMETERS'][name]
            role = 'low' if np.isclose(value, low) else 'high'
            found[(run['sweep']['parameter'], name, float(value))] = role
    return found


def grids(manifest):
    """{(px, py): (x values, y values)} of the 2D grids in the design."""
    found = {}
    for run in manifest['runs']:
        meta = run.get('sweep', {})
        if meta.get('grid'):
            xs, ys = found.setdefault(tuple(meta['grid']), (set(), set()))
            xs.update(round(float(v), 10) for v in meta['grid_values'][0])
            ys.update(round(float(v), 10) for v in meta['grid_values'][1])
    return found


def tables(runs, manifest, names, reference):
    curve_rows, tornado_rows = [], []
    conds = conditions(manifest)
    for municipality in runs['municipality'].unique():
        local = runs[runs['municipality'] == municipality]
        for output in am.OUTPUTS:
            for p in names:
                bases = [('reference', reference)] + [
                    ('%s = %g' % (c, v), dict(reference, **{c: v}))
                    for (q, c, v) in conds if q == p]
                for condition, base in bases:
                    data = curve(local, p, base, names, output)
                    for _, row in data.iterrows():
                        curve_rows.append({'municipality': municipality, 'output': output, 'parameter': p,
                                           'condition': condition, 'parameter_value': row[p],
                                           'output_value': row[output], 'run_id': row['run_id']})
                    if condition == 'reference' and len(data) >= 2:
                        tornado_rows.append({
                            'municipality': municipality, 'output': output, 'parameter': p,
                            'n_points': len(data), 'min': data[output].min(), 'max': data[output].max(),
                            'range': data[output].max() - data[output].min(),
                            'at_lowest_value': data[output].iloc[0], 'at_highest_value': data[output].iloc[-1]})
    return pd.DataFrame(curve_rows), pd.DataFrame(tornado_rows)


def tornado_figure(tornado, runs, municipality, output, reference_value):
    import plotly.graph_objects as go
    data = tornado[(tornado['municipality'] == municipality) & (tornado['output'] == output)]
    data = data.sort_values('range')
    fig = go.Figure(go.Bar(
        y=[label(p) for p in data['parameter']], x=data['range'], base=data['min'], orientation='h',
        marker=dict(color=am.SERIES, line=dict(color=am.SURFACE, width=2)),
        customdata=[[float(a), float(b), float(c), float(d), int(n)] for a, b, c, d, n in zip(
            data['min'], data['max'], data['at_lowest_value'], data['at_highest_value'], data['n_points'])],
        hovertemplate=('<b>%{y}</b><br>min %{customdata[0]:,.4g} – max %{customdata[1]:,.4g}'
                       '<br>at lowest parameter value: %{customdata[2]:,.4g}'
                       '<br>at highest parameter value: %{customdata[3]:,.4g}'
                       '<br>points: %{customdata[4]}<extra></extra>')))
    if reference_value is not None:
        fig.add_vline(x=reference_value, line=dict(color=am.MUTED, width=1, dash='dot'),
                      annotation_text='reference', annotation_font_color=am.INK_SECONDARY)
    am.style(fig, 'Range of %s over each parameter\'s full range (others at reference)'
             % am.OUTPUTS[output], 110 + 34 * max(len(data), 1))
    fig.update_xaxes(rangemode='normal', title_text=am.OUTPUTS[output])
    fig.update_yaxes(rangemode='normal', gridcolor=am.SURFACE)
    return fig


def panels_figure(runs, municipality, output, names, reference, conds):
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    cols = 5
    rows = -(-len(names) // cols)
    # One y-scale for all panels, so slopes are directly comparable.
    fig = make_subplots(rows=rows, cols=cols, shared_yaxes='all', subplot_titles=[label(p) for p in names],
                        horizontal_spacing=0.03, vertical_spacing=0.18)
    local = runs[runs['municipality'] == municipality]
    shown = set()
    for i, p in enumerate(names):
        row, col = i // cols + 1, i % cols + 1
        bases = [('reference', 'Reference conditions', reference)] + [
            (role, '%s %s (%g)' % (label(c), role, v), dict(reference, **{c: v}))
            for (q, c, v), role in conds.items() if q == p]
        for role, name, base in bases:
            data = curve(local, p, base, names, output)
            if data.empty:
                continue
            fig.add_trace(go.Scatter(
                x=data[p], y=data[output], mode='lines+markers', name=name, legendgroup=name,
                showlegend=name not in shown,
                line=dict(color=CONDITION_COLOURS[role], width=2),
                marker=dict(size=8, color=CONDITION_COLOURS[role], line=dict(color=am.SURFACE, width=2)),
                hovertemplate=('<b>%s</b><br>%s = %%{x:.4g}<br>%s = %%{y:,.4g}<extra>%s</extra>'
                               % (label(p), label(p), am.OUTPUTS[output], name))), row=row, col=col)
            shown.add(name)
        ref_run = local[(local['group'] == 'reference') & local['status'].isin(am.COMPLETE)]
        if not ref_run.empty and output in ref_run:
            fig.add_trace(go.Scatter(
                x=[reference[p]], y=[ref_run[output].iloc[0]], mode='markers', name='Reference run',
                legendgroup='Reference run', showlegend='Reference run' not in shown,
                marker=dict(size=14, symbol='circle-open', color=REFERENCE_RING, line=dict(width=2)),
                hoverinfo='skip'), row=row, col=col)
            shown.add('Reference run')
    am.style(fig, '%s – %s vs. each parameter (others at reference)' % (municipality, am.OUTPUTS[output]),
             300 * rows + 140)
    fig.update_layout(showlegend=True, margin=dict(b=90),
                      legend=dict(orientation='h', x=0, y=-0.08, yanchor='top',
                                  font=dict(color=am.INK_SECONDARY)))
    fig.update_xaxes(rangemode='normal')
    fig.update_yaxes(rangemode='normal')
    fig.update_yaxes(title_text=am.OUTPUTS[output], col=1)
    return fig


def grid_figure(runs, municipality, output, names, reference, pair, values):
    import plotly.graph_objects as go
    px, py = pair
    xs, ys = values
    local = runs[runs['municipality'] == municipality]
    mask = local['status'].isin(am.COMPLETE)
    # Only the grid's own values; sweep points on the same axes are left out.
    mask &= local[px].astype(float).round(10).isin(xs) & local[py].astype(float).round(10).isin(ys)
    for other in names:
        if other not in pair:
            mask &= np.isclose(local[other].astype(float), float(reference[other]), rtol=0, atol=1e-9)
    data = local[mask]
    if output not in data or data[output].dropna().empty:
        return None
    table = data.pivot_table(index=py, columns=px, values=output, aggfunc='mean')
    fig = go.Figure(go.Heatmap(
        z=table.values, x=['%.4g' % v for v in table.columns], y=['%.4g' % v for v in table.index],
        colorscale=am.SEQUENTIAL, xgap=2, ygap=2,
        colorbar=dict(title=dict(text=am.OUTPUTS[output], font=dict(color=am.INK_SECONDARY)),
                      tickfont=dict(color=am.INK_SECONDARY)),
        hovertemplate=('%s = %%{x}<br>%s = %%{y}<br>%s = %%{z:,.4g}<extra></extra>'
                       % (label(px), label(py), am.OUTPUTS[output]))))
    am.style(fig, '%s – %s over %s × %s (others at reference)'
             % (municipality, am.OUTPUTS[output], label(px), label(py)), 460)
    fig.update_xaxes(title_text=label(px), type='category', showgrid=False)
    fig.update_yaxes(title_text=label(py), type='category', showgrid=False)
    return fig


def write_page(path, title, sections):
    html = ['<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>%s</title>' % title,
            '<style>body{margin:16px;background:%s;color:%s;font-family:%s}'
            'h1{font-size:20px;font-weight:600}h2{font-size:16px;font-weight:600;margin-top:32px;'
            'color:%s}p{color:%s;font-size:14px;max-width:70ch}</style></head><body>'
            % (am.SURFACE, am.INK, am.FONT, am.INK, am.INK_SECONDARY),
            '<h1>%s</h1><p>Each output: a tornado chart (range over each parameter\'s full range), '
            'one panel per parameter, and 2D grids if the study contains any. '
            'Hover over points for exact values.</p>' % title]
    first = True
    for heading, figures in sections:
        html.append('<h2>%s</h2>' % heading)
        for fig in figures:
            html.append(fig.to_html(full_html=False, include_plotlyjs=first, default_width='100%',
                                    config={'responsive': True}))
            first = False
    html.append('</body></html>')
    Path(path).write_text('\n'.join(html), encoding='utf-8')


def main():
    default_study = None
    try:
        from run_dem_sweeps import STUDY_DIR as default_study
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--study-dir', type=Path, default=default_study,
                        help='Study directory (default: STUDY_DIR of run_dem_sweeps.py).')
    args = parser.parse_args()
    if args.study_dir is None:
        parser.error('--study-dir is required.')
    study = args.study_dir.resolve()
    manifest, runs = am.load_runs(study)
    reference_runs = [run for run in manifest['runs'] if run['group'] == 'reference']
    if not reference_runs:
        raise SystemExit('No reference run in this study manifest.')
    reference = reference_runs[0]['parameters']
    names = list(reference_runs[0]['settings']['MORRIS_PARAMETERS'])
    conds = conditions(manifest)

    runs[[c for c in runs.columns if c != 'levels']].to_csv(study / 'key_outputs.csv', index=False, encoding='utf-8-sig')
    curves, tornado = tables(runs, manifest, names, reference)
    curves.to_csv(study / 'sweep_curves.csv', index=False, encoding='utf-8-sig')
    tornado.to_csv(study / 'tornado.csv', index=False, encoding='utf-8-sig')

    done = runs['status'].isin(am.COMPLETE)
    print('Runs completed: %d of %d.' % (done.sum(), len(runs)))
    for municipality in runs['municipality'].unique():
        local = runs[(runs['municipality'] == municipality) & done]
        ref_run = local[local['group'] == 'reference']
        sections = []
        for output in am.OUTPUTS:
            reference_value = (float(ref_run[output].iloc[0])
                               if not ref_run.empty and output in ref_run else None)
            figures = []
            if not tornado.empty:
                figures.append(tornado_figure(tornado, runs, municipality, output, reference_value))
            figures.append(panels_figure(runs, municipality, output, names, reference, conds))
            for pair, values in grids(manifest).items():
                fig = grid_figure(runs, municipality, output, names, reference, pair, values)
                if fig is not None:
                    figures.append(fig)
            sections.append((am.OUTPUTS[output], figures))
        slug = ''.join(c if c.isalnum() else '_' for c in municipality)
        write_page(study / ('sweeps_%s.html' % slug), 'Parameter sweeps – %s' % municipality, sections)
        if not tornado.empty:
            print('\n%s: largest output range per output' % municipality)
            for output, text in am.OUTPUTS.items():
                data = tornado[(tornado['municipality'] == municipality) & (tornado['output'] == output)]
                data = data[data['range'] > 0].sort_values('range', ascending=False).head(3)
                ranking = ', '.join('%s (%.3g)' % (label(p), r) for p, r in zip(data['parameter'], data['range']))
                print('  %-30s %s' % (text, ranking or 'no variation yet'))
    print('\nWritten to %s: key_outputs.csv, sweep_curves.csv, tornado.csv, sweeps_*.html' % study)


if __name__ == '__main__':
    main()
