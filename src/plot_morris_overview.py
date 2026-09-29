#!/usr/bin/env python3
"""Publication figure of the Morris screening overview (relative mu*).

    python plot_morris_overview.py --study-dir <Morris study directory> [--out-dir DIR]

Reads morris_indices.csv written by analyse_morris.py and writes
morris_overview.png (600 dpi) and morris_overview.svg (text kept as editable
text). Needs pandas and matplotlib only (matplotlib is not part of the DEM
environment).
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_rgb  # noqa: E402

MUNICIPALITY_LABELS = {'Luzern': 'Lucerne'}
PARAMETER_LABELS = {
    'electricity_tariff': 'Electricity import tariff',
    'electricity_export_tariff': 'Electricity export tariff',
    'quality_factor_multiplier': 'Heat-pump quality factor',
    'gas_price': 'Natural gas price',
    'oil_price': 'Heating oil price',
    'co2_price': 'CO$_2$ price',
    'hp_capex_multiplier': 'Heat-pump investment cost',
    'tes_capex_multiplier': 'TES investment cost',
    'pv_capex_multiplier': 'PV investment cost',
    'space_heating_multiplier': 'Space-heating demand',
    'interest_rate': 'Interest rate',
}
OUTPUT_LABELS = {
    'total_system_cost_CHF': 'Total system cost',
    'co2_emissions_kg': 'CO$_2$ emissions',
    'hp_capacity_kW': 'Heat-pump capacity',
    'tes_capacity_kWh': 'TES capacity',
    'pv_rooftop_capacity_kWp': 'PV capacity',
    'electricity_import_kWh': 'Electricity import',
}
# Sequential single-hue ramp (light = low influence, dark = high influence).
CMAP = LinearSegmentedColormap.from_list(
    'blues', ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'])
INK, INK_SECONDARY = '#0b0b0b', '#52514e'
LABEL_THRESHOLD = 0.05        # smaller values are left blank (negligible)


def text_colour(value):
    r, g, b = to_rgb(CMAP(value))
    return 'white' if 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.5 else INK


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--study-dir', type=Path, required=True, help='Directory containing morris_indices.csv.')
    parser.add_argument('--out-dir', type=Path, default=None, help='Output directory (default: study directory).')
    args = parser.parse_args()
    table = pd.read_csv(args.study_dir / 'morris_indices.csv')
    out_dir = args.out_dir or args.study_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({
        'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 8, 'svg.fonttype': 'none', 'axes.titlesize': 9,
    })
    municipalities = list(dict.fromkeys(table['municipality']))
    parameters = [p for p in PARAMETER_LABELS if p in set(table['parameter'])]
    outputs = [o for o in OUTPUT_LABELS if o in set(table['output'])]

    fig, axes = plt.subplots(1, len(municipalities), figsize=(7.2, 4.1), sharey=True,
                             constrained_layout=True)
    axes = np.atleast_1d(axes)
    for ax, municipality in zip(axes, municipalities):
        data = table[table['municipality'] == municipality]
        z = (data.pivot(index='parameter', columns='output', values='mu_star_relative')
             .reindex(index=parameters, columns=outputs).to_numpy(dtype=float))
        # pcolormesh keeps the cells as vector shapes in the SVG; the white
        # cell edges form the gaps between cells.
        image = ax.pcolormesh(np.arange(len(outputs) + 1) - 0.5, np.arange(len(parameters) + 1) - 0.5,
                              np.ma.masked_invalid(z), cmap=CMAP, vmin=0, vmax=1,
                              edgecolors='white', linewidth=1.5)
        ax.set_xlim(-0.5, len(outputs) - 0.5)
        ax.set_ylim(len(parameters) - 0.5, -0.5)
        for (row, col), value in np.ndenumerate(z):
            if np.isfinite(value) and value >= LABEL_THRESHOLD:
                ax.text(col, row, '%.2f' % value, ha='center', va='center', fontsize=6.5,
                        color=text_colour(value))
        ax.set_xticks(range(len(outputs)))
        ax.set_xticklabels([OUTPUT_LABELS[o] for o in outputs], rotation=45, ha='right',
                           rotation_mode='anchor')
        ax.set_yticks(range(len(parameters)))
        ax.set_yticklabels([PARAMETER_LABELS[p] for p in parameters])
        ax.tick_params(which='both', length=0, colors=INK_SECONDARY)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(MUNICIPALITY_LABELS.get(municipality, municipality), color=INK)
    colorbar = fig.colorbar(image, ax=axes, shrink=0.75, aspect=25, pad=0.02,
                            ticks=[0, 0.25, 0.5, 0.75, 1])
    colorbar.set_label(r'Relative $\mu^*$ ($\mu^*$ / largest $\mu^*$ per output)', color=INK_SECONDARY)
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(length=0, colors=INK_SECONDARY)

    for suffix, options in (('png', {'dpi': 600}), ('svg', {})):
        path = out_dir / ('morris_overview.' + suffix)
        fig.savefig(path, bbox_inches='tight', facecolor='white', **options)
        print('written:', path)


if __name__ == '__main__':
    main()
