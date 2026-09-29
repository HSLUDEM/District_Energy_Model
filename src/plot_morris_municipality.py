#!/usr/bin/env python3
"""Publication figures of the Morris mu*-sigma charts, one file per output.

    python plot_morris_municipality.py --study-dir <Morris study directory> [--municipality Luzern] [--out-dir DIR]

Reads morris_indices.csv written by analyse_morris.py and writes, per output,
morris_<municipality>_<output>.png (600 dpi) and .svg (editable text).
Figure size 6.3 x 2.7 in, so that three figures fit above each other on a page.
Needs pandas and matplotlib only.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from plot_morris_overview import MUNICIPALITY_LABELS, OUTPUT_LABELS, PARAMETER_LABELS  # noqa: E402

# Base unit per output and the unit names for factors 1, 1e3, 1e6, 1e9.
UNITS = {
    'total_system_cost_CHF': ['CHF/a', 'kCHF/a', 'MCHF/a', 'GCHF/a'],
    'co2_emissions_kg': ['kg/a', 't/a', 'kt/a', 'Mt/a'],
    'hp_capacity_kW': ['kW$_\\mathrm{th}$', 'MW$_\\mathrm{th}$', 'GW$_\\mathrm{th}$', 'TW$_\\mathrm{th}$'],
    'tes_capacity_kWh': ['kWh', 'MWh', 'GWh', 'TWh'],
    'pv_rooftop_capacity_kWp': ['kWp', 'MWp', 'GWp', 'TWp'],
    'electricity_import_kWh': ['kWh/a', 'MWh/a', 'GWh/a', 'TWh/a'],
}
SERIES, INK, INK_SECONDARY, MUTED, GRID = '#2a78d6', '#0b0b0b', '#52514e', '#898781', '#e1e0d9'
LABEL_THRESHOLD = 0.1          # label points with relative mu* >= this value
FIGSIZE = (6.3, 2.7)


def scale_for(values, output):
    top = float(np.nanmax(values)) if np.isfinite(values).any() else 0.0
    power = 0
    while power < 3 and top >= 1000 ** (power + 1):
        power += 1
    return 1000.0 ** power, UNITS[output][power]


def place_labels(ax, fig, texts):
    """Nudge overlapping labels vertically (simple repel, in display space)."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    placed = []
    for text in sorted(texts, key=lambda t: -t.get_position()[1]):
        for _ in range(40):
            box = text.get_window_extent(renderer).expanded(1.05, 1.15)
            if not any(box.overlaps(other) for other in placed):
                break
            x, y = text.get_position()
            dy = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.035
            text.set_position((x, y - dy))
        placed.append(text.get_window_extent(renderer))


def plot_output(data, output, municipality, path_stem):
    fig, ax = plt.subplots(figsize=FIGSIZE, constrained_layout=True)
    factor, unit = scale_for(np.r_[data['mu_star_ci_high'], data['sigma']], output)
    mu = data['mu_star'].to_numpy() / factor
    sigma = data['sigma'].fillna(0).to_numpy() / factor
    low = (data['mu_star'] - data['mu_star_ci_low']).to_numpy() / factor
    high = (data['mu_star_ci_high'] - data['mu_star']).to_numpy() / factor
    extent = 1.12 * float(np.nanmax(np.r_[mu + high, sigma, 1e-12]))
    ax.plot([0, extent], [0, extent], color=MUTED, linewidth=0.8, linestyle=':', zorder=1)
    ax.text(extent * 0.985, extent * 0.93, r'$\sigma = \mu^*$', color=MUTED, fontsize=7,
            ha='right', va='top', bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=0.6))
    ax.errorbar(mu, sigma, xerr=[low, high], fmt='none', ecolor=MUTED, elinewidth=0.8, zorder=2)
    ax.scatter(mu, sigma, s=26, color=SERIES, edgecolors='white', linewidths=0.8, zorder=3)
    texts = []
    for (_, row), x, y in zip(data.iterrows(), mu, sigma):
        if row['mu_star_relative'] >= LABEL_THRESHOLD:
            texts.append(ax.text(x + extent * 0.012, y + extent * 0.02, PARAMETER_LABELS[row['parameter']],
                                 fontsize=7, color=INK_SECONDARY, ha='left', va='bottom', zorder=4,
                                 bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=0.6)))
    ax.set_xlim(0, extent)
    ax.set_ylim(0, extent)
    ax.set_xlabel(r'$\mu^*$ (%s)' % unit)
    ax.set_ylabel(r'$\sigma$ (%s)' % unit)
    ax.set_title('%s – %s' % (MUNICIPALITY_LABELS.get(municipality, municipality), OUTPUT_LABELS[output]),
                 color=INK, loc='left')
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK_SECONDARY, length=3)
    place_labels(ax, fig, texts)
    for suffix, options in (('png', {'dpi': 600}), ('svg', {})):
        fig.savefig('%s.%s' % (path_stem, suffix), facecolor='white', **options)
    plt.close(fig)
    print('written: %s.png/.svg' % path_stem)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--study-dir', type=Path, required=True, help='Directory containing morris_indices.csv.')
    parser.add_argument('--municipality', default='Luzern', help='Municipality name as in the results (default: Luzern).')
    parser.add_argument('--out-dir', type=Path, default=None, help='Output directory (default: study directory).')
    args = parser.parse_args()
    table = pd.read_csv(args.study_dir / 'morris_indices.csv')
    table = table[(table['municipality'] == args.municipality) & table['mu_star'].notna()]
    if table.empty:
        raise SystemExit('No Morris indices for municipality %r.' % args.municipality)
    out_dir = args.out_dir or args.study_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 8, 'axes.titlesize': 9, 'svg.fonttype': 'none',
    })
    slug = ''.join(c if c.isalnum() else '_' for c in args.municipality)
    for output in OUTPUT_LABELS:
        data = table[table['output'] == output]
        if not data.empty:
            plot_output(data, output, args.municipality, out_dir / ('morris_%s_%s' % (slug, output)))


if __name__ == '__main__':
    main()
