# DEM system checks

Broad checks of the whole model on real input data, in addition to the pytest
regression tests in `tests/` (which pin individual bugs). The system checks run
many configurations, municipalities and weather years, and compare the results
with the inputs and with invariants (energy balances, conversion ratios,
capacity limits, cost module vs. optimisation objective, saved files vs.
in-memory results).

They are scripts, not pytest tests (file names `check_*.py`, so pytest does not
collect them): runs take minutes to hours, and some results need judgement.

## Requirements

- The DEM `data` folder in the repository root (or set `DEM_TEST_ROOT` to the
  directory containing `data`).
- Gurobi for the optimisation cases (`GRB_LICENSE_FILE` as usual). A few cases
  use `"solver": "cbc"` and fail without CBC on `PATH`.
- Run with the Python of the DEM environment.

Environment variables:

| variable | meaning | default |
|---|---|---|
| `DEM_TEST_ROOT` | directory with `data/` | repository root |
| `DEM_CHECK_WORK` | results and model outputs | `tests/system/_work` (git-ignored) |
| `DEM_SRC` | `src` folder of another checkout to test (e.g. a worktree) | installed package |

## Quick start

```bash
python tests/system/run_all.py                 # configuration matrix + 7 subsystem suites
python tests/system/run_all.py -w 16 -p main   # 16 workers, result prefix "main"
python tests/system/run_all.py --only ts,pv    # selected suites
python tests/system/run_all.py --only io       # output files / YAML round trip (slow)
python tests/system/run_all.py --check-only -p main   # re-check existing results
```

Each check prints one line per case: `ok`, `ISSUE ...` (a check failed),
`FAIL ...` (DEM raised) or `MISSING`. Some cases are meant to end in a
validation error or a reported infeasibility (e.g. `chain` `gas_hg_cap`), so a
`FAIL` needs a look at the case definition, not just a count. To compare two
versions, run both with different prefixes (and `DEM_SRC`) and diff the outputs.

## Subsystem suites

Each suite: `python tests/system/check_<x>.py run <prefix> <workers> [filter]`,
then `python tests/system/check_<x>.py check <prefix>`.

| suite | file | cases | checks |
|---|---|---|---|
| ts | `check_timeseries.py` | 55 | waste heat (HT/LT) and manual heat demand time series, hour by hour vs. inputs (`inputs/ts/`) |
| gt | `check_grid_tariffs.py` | 10 | grid tariff / export / CO2 time series: costs and emissions vs. inputs (usage: `check_grid_tariffs.py <prefix> [workers]`) |
| tes | `check_tes_sites.py` | 47 | TES sites: sizes, level splits, several sites, exclusion groups, invalid lists, costs |
| chain | `check_fuel_chains.py` | 30 | biomass / gas / hydrogen / wood chain: flow ratios, carrier balances, supply limits, costs |
| cplant | `check_central_plants.py` | 37 | central plants: conversion ratios, capacity limits, minimum use, heat and steam splits, costs |
| pv | `check_solar.py` | 33 | alpine / rooftop PV and solar thermal: potentials, capacity limits, consumption/export split, costs |
| scen | `check_scenarios.py` | 19 | wind integration, nuclear phase-out, battery scenario, hour by hour vs. the base run |
| io | `check_io.py` | 3 × pv/cplant/chain/tes/scen | config_dict vs. YAML vs. reloaded `scen_techs.yaml`; saved files vs. in-memory results |

## Case files (generic checks)

`python tests/system/run_cases.py <cases.txt> [workers] [name_prefix]` runs a
case file (tab-separated: name, `config_dict` JSON, optional YAML directory;
`{HERE}` stands for this folder, `"_launch"` holds `launch()` arguments such as
`hist_data_year`). Results are in `_work/results/<name>.json`. Then use
`python tests/system/fuzz.py check <name_prefix>` to classify them: OK, expected
validation error, unexpected error, or OK but suspicious (NaN/negative values,
unmet demand, cost module ≠ objective, CO2 mismatch).
`python tests/system/summarize.py [names...]` prints the key annual results.

| file | cases | content |
|---|---|---|
| `cases/matrix.txt` | 91 | scenarios, technologies, optimisation options, YAML configurations (Allschwil 2762) |
| `cases/all_municipalities.txt` | 2110 | 7-day simulation of every municipality |
| `cases/sample_municipalities.txt` | 108 | sample of municipalities with scenarios / optimisation |
| `cases/weather_years.txt` | 42 | weather years 2016 / 2018 / 2019 |
| `cases/sample_municipalities_and_years.txt` | 150 | municipalities × weather years |
| `cases/custom_districts.txt` | 20 | custom districts (EGID lists, several municipalities) |
| `cases/manual_districts.txt` | 6 | manual districts (`inputs/manual/`) |
| `cases/energy_scaling.txt` | 30 | Calliope energy scaling factors |

## Generated checks

- `fuzz.py make <n> <seed> <cases.txt>` / `fuzz_extended.py make <n> <seed> <cases.txt>`:
  random combinations of settings (the extended version adds energy scaling,
  flexibility, TES sites, waste heat, grid limits, ...). Run with `run_cases.py`,
  check with `fuzz.py check <prefix>`.
- `param_sweeps.py make <cases.txt>` / `param_sweeps.py check [prefix]`: each
  sweep varies one parameter and checks the expected direction of a result.
- `param_effect.py make|run|check <cases.txt>`: changes each numeric input alone
  and lists parameters without any effect on results or costs.

## Single checks

- `check_state_leak.py`: three `launch()` calls in one process give the same results.
- `check_pareto_reload.py`: create a pareto front and reload it.
- `check_plots.py <output_dir>`: data in the Sankey / balance plots vs. the hourly results.
- `run_case.py <name> '<config_dict>' [yaml_dir]`: one case in-process.

## Other folders

`inputs/`: time series, EGID lists, manual-district files and TES site
configurations. `yaml_configs/`: YAML test configurations used by `matrix.txt`.
