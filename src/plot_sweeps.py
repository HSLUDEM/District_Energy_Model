#!/usr/bin/env python3
"""Publication figures of the parameter sweeps (tornado, 2D grid, conditional sweeps).

    python plot_sweeps.py --study-dir <sweep study directory> [--municipality Luzern]
                          [--outputs total_system_cost_CHF ...] [--out-dir DIR]

Reads tornado.csv, sweep_curves.csv and key_outputs.csv (written by
analyse_sweeps.py) and study_manifest.json. Writes per municipality and output:
  sweep_<m>_<output>_tornado      6.3 x 3.6 in  (tornado + grid fit on one page)
  sweep_<m>_<output>_grid         6.3 x 3.6 in
  sweep_<m>_<output>_response     6.3 x 8.0 in  (one panel per parameter, one page)
  sweep_<m>_<output>_conditional  6.3 x 7.6 in  (one page incl. caption)
each as .png (600 dpi) and .svg (editable text). Needs pandas and matplotlib.
"""
import argparse
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from plot_morris_overview import CMAP, MUNICIPALITY_LABELS, OUTPUT_LABELS, PARAMETER_LABELS, text_colour  # noqa: E402
from plot_morris_municipality import GRID, INK, INK_SECONDARY, MUTED, scale_for  # noqa: E402

# Axis label and display factor per parameter (CO2 price shown in CHF/t, interest in %).
DISPLAY = {
    'electricity_tariff': ('Electricity import tariff (CHF/kWh)', 1),
    'electricity_export_tariff': ('Electricity export tariff (CHF/kWh)', 1),
    'quality_factor_multiplier': ('Heat-pump quality factor (× reference)', 1),
    'gas_price': ('Natural gas price (CHF/kWh)', 1),
    'oil_price': ('Heating oil price (CHF/l)', 1),
    'co2_price': ('CO$_2$ price (CHF/t)', 1000),
    'hp_capex_multiplier': ('Heat-pump investment cost (× reference)', 1),
    'tes_capex_multiplier': ('TES investment cost (× reference)', 1),
    'pv_capex_multiplier': ('PV investment cost (× reference)', 1),
    'space_heating_multiplier': ('Space-heating demand (× reference)', 1),
    'interest_rate': ('Interest rate (%)', 100),
}
SHORT = {'electricity_tariff': 'Import tariff', 'electricity_export_tariff': 'Export tariff',
         'oil_price': 'Oil price', 'co2_price': 'CO$_2$ price', 'gas_price': 'Gas price'}
UNIT = {'electricity_tariff': 'CHF/kWh', 'electricity_export_tariff': 'CHF/kWh', 'oil_price': 'CHF/l',
        'co2_price': 'CHF/t', 'gas_price': 'CHF/kWh', 'interest_rate': '%'}
LOWER, UPPER, REFERENCE_COLOUR = '#eb6834', '#2a78d6', '#2a78d6'
CONDITION_COLOURS = {'low': '#eb6834', 'high': '#1baf7a'}


def style_axes(ax):
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK_SECONDARY, length=3)


def save(fig, stem):
    for suffix, options in (('png', {'dpi': 600}), ('svg', {})):
        fig.savefig('%s.%s' % (stem, suffix), facecolor='white', **options)
    plt.close(fig)
    print('written: %s.png/.svg' % stem)


def display_value(name, value):
    label = '%g' % round(value * DISPLAY[name][1], 6)
    return '%s %s' % (label, UNIT[name]) if name in UNIT else '%s× reference' % label


def tornado(tornado_table, reference_value, output, municipality, stem):
    data = tornado_table.sort_values('range')
    factor, unit = scale_for(np.r_[data['max'], reference_value], output)
    fig, ax = plt.subplots(figsize=(6.3, 3.6), constrained_layout=True)
    ref = reference_value / factor
    for y, (_, row) in enumerate(data.iterrows()):
        low, high = row['at_lowest_value'] / factor, row['at_highest_value'] / factor
        vmin, vmax = row['min'] / factor, row['max'] / factor
        # Whisker for the full range of the sweep (visible when non-monotonic).
        ax.plot([vmin, vmax], [y, y], color=MUTED, linewidth=0.8, zorder=1)
        # Both bars on the same line; if they lie on the same side of the
        # reference, the longer one is drawn first so both remain visible.
        bars = sorted([(low - ref, LOWER), (high - ref, UPPER)], key=lambda b: -abs(b[0]))
        for z, (width, colour) in enumerate(bars):
            ax.barh(y, width, left=ref, height=0.6, color=colour, zorder=2 + z)
    ax.axvline(ref, color=INK, linewidth=0.8, zorder=3)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels([PARAMETER_LABELS[p] for p in data['parameter']])
    ax.set_xlabel('%s (%s)' % (OUTPUT_LABELS[output], unit))
    ax.set_title('%s – %s' % (MUNICIPALITY_LABELS.get(municipality, municipality), OUTPUT_LABELS[output]),
                 loc='left', color=INK)
    style_axes(ax)
    ax.grid(axis='y', visible=False)
    ax.tick_params(axis='y', length=0)
    handles = [Line2D([], [], color=LOWER, linewidth=6, label='Parameter at lower bound'),
               Line2D([], [], color=UPPER, linewidth=6, label='Parameter at upper bound'),
               Line2D([], [], color=MUTED, linewidth=0.8, label='Range over full sweep'),
               Line2D([], [], color=INK, linewidth=0.8, label='Reference (%.3g %s)' % (ref, unit))]
    ax.legend(handles=handles, loc='lower right', fontsize=7, frameon=True, framealpha=0.9, edgecolor='none')
    save(fig, stem)


def grid_plot(runs, reference, pair, values, output, municipality, stem):
    px, py = pair
    xs, ys = (np.array(v, dtype=float) for v in values)
    local = runs.copy()
    mask = local[px].round(10).isin(np.round(xs, 10)) & local[py].round(10).isin(np.round(ys, 10))
    for other, ref_value in reference.items():
        if other not in pair:
            mask &= np.isclose(local[other].astype(float), float(ref_value), rtol=0, atol=1e-9)
    table = local[mask].pivot_table(index=py, columns=px, values=output, aggfunc='mean')
    table = table.reindex(index=ys, columns=xs)
    factor, unit = scale_for(table.to_numpy(dtype=float).ravel(), output)
    z = table.to_numpy(dtype=float) / factor
    fx, fy = DISPLAY[px][1], DISPLAY[py][1]
    dx, dy = (xs[1] - xs[0]) * fx, (ys[1] - ys[0]) * fy
    x_edges = np.r_[xs * fx - dx / 2, xs[-1] * fx + dx / 2]
    y_edges = np.r_[ys * fy - dy / 2, ys[-1] * fy + dy / 2]
    fig, ax = plt.subplots(figsize=(6.3, 3.6), constrained_layout=True)
    vmin, vmax = np.nanmin(z), np.nanmax(z)
    mesh = ax.pcolormesh(x_edges, y_edges, np.ma.masked_invalid(z), cmap=CMAP, vmin=vmin, vmax=vmax,
                         edgecolors='white', linewidth=1.5)
    for (i, j), value in np.ndenumerate(z):
        if np.isfinite(value):
            ax.text(xs[j] * fx, ys[i] * fy, '%.3g' % value, ha='center', va='center', fontsize=7,
                    color=text_colour((value - vmin) / (vmax - vmin) if vmax > vmin else 0))
    ax.plot(reference[px] * fx, reference[py] * fy, marker='o', markersize=8, markerfacecolor='none',
            markeredgecolor=INK, markeredgewidth=1.2, linestyle='none', label='Reference')
    ax.set_xticks(xs * fx)
    ax.set_xticklabels(['%g' % round(v, 4) for v in xs * fx])
    ax.set_yticks(ys * fy)
    ax.set_yticklabels(['%g' % round(v, 4) for v in ys * fy])
    ax.set_xlim(x_edges[0], x_edges[-1])
    ax.set_ylim(y_edges[0], y_edges[-1])
    ax.set_xlabel(DISPLAY[px][0])
    ax.set_ylabel(DISPLAY[py][0])
    ax.set_title('%s – %s' % (MUNICIPALITY_LABELS.get(municipality, municipality), OUTPUT_LABELS[output]),
                 loc='left', color=INK)
    ax.tick_params(length=0, colors=INK_SECONDARY)
    for spine in ax.spines.values():
        spine.set_visible(False)
    colorbar = fig.colorbar(mesh, ax=ax, pad=0.02, aspect=25)
    colorbar.set_label('%s (%s)' % (OUTPUT_LABELS[output], unit), color=INK_SECONDARY)
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(length=0, colors=INK_SECONDARY)
    ax.legend(loc='lower right', bbox_to_anchor=(1, 1.0), fontsize=7, frameon=False, borderaxespad=0.2)
    save(fig, stem)


def conditional(curves, reference, reference_value, output, municipality, stem):
    pairs = []
    for condition in curves['condition'].unique():
        match = re.match(r'(\w+) = (.+)', condition)
        if match:
            for parameter in curves.loc[curves['condition'] == condition, 'parameter'].unique():
                if (parameter, match.group(1)) not in pairs:
                    pairs.append((parameter, match.group(1)))
    pairs.sort(key=lambda pc: list(DISPLAY).index(pc[0]))
    if not pairs:
        return
    values = np.r_[curves['output_value'], reference_value]
    factor, unit = scale_for(values, output)
    rows = -(-len(pairs) // 2)
    fig = plt.figure(figsize=(6.3, 7.6), layout='constrained')
    subfigs = np.atleast_1d(fig.subfigures(rows, 1))
    axes = []
    for r, subfig in enumerate(subfigs):
        row_axes = subfig.subplots(1, 2)
        for ax, (parameter, _) in zip(row_axes, pairs[2 * r:2 * r + 2]):
            ax.set_xlabel(DISPLAY[parameter][0])
        axes.extend(row_axes)
    axes = np.array(axes)
    for ax, (parameter, cond) in zip(axes, pairs):
        fx = DISPLAY[parameter][1]
        ref_curve = curves[(curves['parameter'] == parameter) & (curves['condition'] == 'reference')]
        ref_curve = ref_curve.sort_values('parameter_value')
        ax.plot(ref_curve['parameter_value'] * fx, ref_curve['output_value'] / factor, color=REFERENCE_COLOUR,
                marker='o', markersize=3.5, linewidth=1.4)
        low, high = settings_range(cond)
        shown = {}
        for condition in sorted(curves.loc[curves['parameter'] == parameter, 'condition'].unique()):
            match = re.match(r'(\w+) = (.+)', condition)
            if not match or match.group(1) != cond:
                continue
            value = float(match.group(2))
            role = 'low' if np.isclose(value, low) else 'high'
            shown[role] = value
            data = curves[(curves['parameter'] == parameter) & (curves['condition'] == condition)]
            data = data.sort_values('parameter_value')
            ax.plot(data['parameter_value'] * fx, data['output_value'] / factor, color=CONDITION_COLOURS[role],
                    marker='o', markersize=3.5, linewidth=1.4)
        ax.plot(reference[parameter] * fx, reference_value / factor, marker='o', markersize=7,
                markerfacecolor='none', markeredgecolor=INK, markeredgewidth=1.0, linestyle='none')
        # Subtitle with the condition values in the order lower / reference / upper.
        fc = DISPLAY[cond][1]
        if np.isclose(low, reference[cond]):
            parts = ['%g (ref.)' % round(low * fc, 6)]
        else:
            parts = ['%g' % round(shown.get('low', low) * fc, 6), '%g' % round(reference[cond] * fc, 6)]
        parts.append('%g' % round(shown.get('high', high) * fc, 6))
        ax.set_title('%s: %s %s' % (SHORT.get(cond, PARAMETER_LABELS[cond]), ' / '.join(parts),
                                    UNIT.get(cond, '× reference')),
                     loc='left', color=INK, fontsize=8)
        ax.set_ylabel('%s (%s)' % (OUTPUT_LABELS[output], unit))
        style_axes(ax)
    for ax in axes[len(pairs):]:
        ax.axis('off')
    handles = [Line2D([], [], color=CONDITION_COLOURS['low'], marker='o', markersize=3.5, linewidth=1.4,
                      label='Condition at lower bound'),
               Line2D([], [], color=REFERENCE_COLOUR, marker='o', markersize=3.5, linewidth=1.4,
                      label='Condition at reference'),
               Line2D([], [], color=CONDITION_COLOURS['high'], marker='o', markersize=3.5, linewidth=1.4,
                      label='Condition at upper bound'),
               Line2D([], [], marker='o', markersize=7, markerfacecolor='none', markeredgecolor=INK,
                      linestyle='none', label='Reference run')]
    legend_title = ('Panel titles: conditioning parameter and its\nvalues at lower / reference / upper bound;\n'
                    'x-axis: swept parameter')
    if len(pairs) < len(axes):
        legend = axes[-1].legend(handles=handles, loc='center', frameon=False, fontsize=7.5,
                                 title=legend_title, title_fontsize=7)
    else:
        legend = fig.legend(handles=handles, loc='outside lower center', ncol=4, frameon=False, fontsize=7.5,
                            title=legend_title, title_fontsize=7)
    legend.get_title().set_color(INK_SECONDARY)
    fig.suptitle('%s – %s' % (MUNICIPALITY_LABELS.get(municipality, municipality), OUTPUT_LABELS[output]),
                 x=0.01, ha='left', color=INK, fontsize=9)
    save(fig, stem)


def response(curves, reference, reference_value, output, municipality, stem):
    """One panel per parameter (others at reference), common y-axis for comparable slopes."""
    data = curves[curves['condition'] == 'reference']
    parameters = [p for p in DISPLAY if p in set(data['parameter'])]
    factor, unit = scale_for(np.r_[data['output_value'], reference_value], output)
    cols, rows = 3, -(-(len(parameters) + 1) // 3)
    fig, axes = plt.subplots(rows, cols, figsize=(6.3, 8.0), sharey=True, constrained_layout=True)
    axes = axes.ravel()
    for ax, parameter in zip(axes, parameters):
        fx = DISPLAY[parameter][1]
        curve = data[data['parameter'] == parameter].sort_values('parameter_value')
        ax.plot(curve['parameter_value'] * fx, curve['output_value'] / factor, color=REFERENCE_COLOUR,
                marker='o', markersize=3, linewidth=1.3)
        ax.plot(reference[parameter] * fx, reference_value / factor, marker='o', markersize=6.5,
                markerfacecolor='none', markeredgecolor=INK, markeredgewidth=1.0, linestyle='none')
        ax.set_title(PARAMETER_LABELS[parameter], loc='left', color=INK, fontsize=8)
        ax.set_xlabel(UNIT.get(parameter, '× reference'), fontsize=7.5)
        style_axes(ax)
    for ax in axes[::cols]:
        ax.set_ylabel('%s (%s)' % (OUTPUT_LABELS[output], unit))
    for ax in axes[len(parameters):]:
        ax.axis('off')
    axes[-1].legend(handles=[Line2D([], [], color=REFERENCE_COLOUR, marker='o', markersize=3, linewidth=1.3,
                                    label='Response, other parameters\nat reference values'),
                             Line2D([], [], marker='o', markersize=6.5, markerfacecolor='none',
                                    markeredgecolor=INK, linestyle='none', label='Reference run')],
                    loc='center', frameon=False, fontsize=7.5)
    fig.suptitle('%s – %s' % (MUNICIPALITY_LABELS.get(municipality, municipality), OUTPUT_LABELS[output]),
                 x=0.01, ha='left', color=INK, fontsize=9)
    save(fig, stem)


_RANGES = {}


def settings_range(name):
    return _RANGES[name]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--study-dir', type=Path, required=True)
    parser.add_argument('--municipality', default='Luzern')
    parser.add_argument('--outputs', nargs='+', default=list(OUTPUT_LABELS))
    parser.add_argument('--out-dir', type=Path, default=None)
    args = parser.parse_args()
    study = args.study_dir
    out_dir = args.out_dir or study / 'figures_svg_png'
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
                         'font.size': 8, 'axes.titlesize': 9, 'svg.fonttype': 'none'})

    manifest = json.loads((study / 'study_manifest.json').read_text(encoding='utf-8'))
    reference_run = [r for r in manifest['runs'] if r['group'] == 'reference'][0]
    reference = reference_run['parameters']
    _RANGES.update({k: tuple(v) for k, v in reference_run['settings']['MORRIS_PARAMETERS'].items()})
    grids = {}
    for run in manifest['runs']:
        meta = run.get('sweep', {})
        if meta.get('grid'):
            grids[tuple(meta['grid'])] = meta['grid_values']
    runs = pd.read_csv(study / 'key_outputs.csv')
    runs = runs[(runs['municipality'] == args.municipality) & runs['status'].isin(['succeeded', 'completed_unverified'])]
    curves = pd.read_csv(study / 'sweep_curves.csv')
    torn = pd.read_csv(study / 'tornado.csv')
    slug = ''.join(c if c.isalnum() else '_' for c in args.municipality)
    for output in args.outputs:
        ref_value = float(runs.loc[runs['group'] == 'reference', output].iloc[0])
        stem = out_dir / ('sweep_%s_%s' % (slug, output))
        tornado(torn[(torn['municipality'] == args.municipality) & (torn['output'] == output)],
                ref_value, output, args.municipality, '%s_tornado' % stem)
        for pair, values in grids.items():
            grid_plot(runs, reference, pair, values, output, args.municipality, '%s_grid' % stem)
        local_curves = curves[(curves['municipality'] == args.municipality) & (curves['output'] == output)]
        response(local_curves, reference, ref_value, output, args.municipality, '%s_response' % stem)
        conditional(local_curves, reference, ref_value, output, args.municipality, '%s_conditional' % stem)


if __name__ == '__main__':
    main()
