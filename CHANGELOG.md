# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0-dev0] - YYYY-MM-DD

### Added

- Separation of electricity demand components: residential, industry, services, losses, and hydropower pumping
- Syncronised historic weather and demand data to same year
- Demand side response: flexibility from building inertia via virtual storage for heat pump and district heating
- Deep Geothermal Technology
- Cost calculation module for manual scenarios
- Added possibility to call run_dem_local.py with location of input_file, config_files and output_files
- Added heatlt heat balance plot
- Add consideration of construction period in calculation of space heating heat demand profile.
- Added grid export as technology with timeseries for prices and emissions (emissions of export yield negative emissions!)
- Added manual heat demand, to allow for a manual heat demand timeseries to be added to the demand
- Added manual district functionality that loads data from user-provided files to model a user-defined district.
- Added PV Alpine
- Added PV-Alpine and electricity feedin to Sankey diagram
- Added possibility to pass list of possible sites to TES_Sites tech via input_file
- Added possibility to add several waste heat / waste heat low temperature sources with different properties.
- Added run_dem_local_parallel.py to run multiple municipalities in parallel (list of BFS numbers in a .yaml file). Interrupted batches can be continued by restarting the script.
- Added solver option `solver_option_Threads` (number of Gurobi threads; default: 0 = automatic).
- Added national generation (`national_generation`): hourly profiles of a flexible set of national generators (e.g. nuclear, hydro, alpine PV, agri PV, wind, gas plant) allocated to the municipality are used as an upper bound for supply. Unused generation is reported as curtailment. National generation cannot be exported and is used before cross-border import (binary constraints in the optimisation). An error is raised if a national generator and its local counterpart (e.g. hydro_power) are both switched on. See doc/national_generation.pdf.
- Added output file capacities.csv (optimisation runs with save_results): optimised capacities (Calliope energy_cap [kW] and storage_cap [kWh]) per technology, split into existing, one-to-one replacement and new capacity where available.
- Added municipal retail electricity tariffs: new default `grid_supply` `tariff_mode` `munic_file` reads the tariff of the municipality and simulated year from `data/electricity/electricity_tariff_munic.feather` (CHF/kWh, excl. VAT; ElCom data, 2016-2027). If the simulated year is not in the file, the last year is used (with a warning). The modes `const` and `timeseries` remain available (`file` is deprecated, use `timeseries`). New inputs: `tariff_munic_filepath`, `tariff_year`, `tariff_factor`.
- National generators use the tariff of `grid_supply` by default: `cost_CHFpkWh` can be omitted or set to `grid_tariff`; a number sets a different cost.
- `grid_supply` `co2_intensity_mode` `file`: a relative `co2_intensity_timeseries_filepath` is now relative to `root_dir` (before: the working directory). An error is raised if the file is missing, the path is empty, or the timeseries has fewer than 8760 values.

### Fixed
- Cost module in simulations: technologies that are not operated (e.g. central storages with a finite `capacity_kWh_max`, central plants with `kW_el_max`) no longer cause capex or maintenance; maxima are limits of the optimisation only. Capacities forced with `force_cap_max` are deployed and cost in full (capex and maintenance) in simulations too. Optimisation costs unchanged.
- Changes of the `grid_supply` tariff in a scenario are applied (previously, the tariff timeseries was not updated).
- Configuration YAML files are checked for valid keywords. An error is thrown if a keyword is invalid (e.g., due to incorrect spelling). Previously, the simulation just continued.
  – Adjust upper and lower flexibility bounds if EV integration is <100% in optimization scenario (previously leading to an error).
- Minor bugfixes
- Bug in dem_tech_district_heating.py: 100% district heating share was not possible. This has been corrected.
- Pareto front: every point now starts from the building and municipality data as loaded. Previously, the demand-side scenario of the previous point had changed the data, so that all points after the first used a different heat demand and different existing capacities. Results of pareto fronts with the demand-side scenario change.
- Pareto front: every point runs the same result checks as a single optimisation (unmet demand, negative values, energy balances) and contains the cost module results (`Kostenmodul`), the optimised capacities (`df_capacities`) and its own copy of `scen_techs`.
- Pareto front: `optimisation.N_pareto` must be an integer of at least 2, and `optimisation.pareto_monetary_co2: True` requires `optimisation.enabled: True` (error instead of a late crash or a silent simulation).
- Pareto front: the scenario of each point is prepared in the same way as for a single optimisation. Previously, it was prepared as for a simulation, so technologies with `deployment: False` remained available to the optimiser, alpine PV was never added, and the heat generators of renovated buildings were reassigned with the rates for manual scenarios. New argument `run_optimisation` of `generate_scenario()` (default True).
- Optimisation: the monetary total costs no longer contain the penalty for unmet demand (`bigM_value` per kWh). Previously, every kWh of unmet demand added `bigM_value` CHF to the reported total (divided by `objective_monetary`, i.e. 100,000 times more when optimising for CO2). The penalty is reported separately as `objective` → `unmet_demand_penalty`. Costs added by custom constraints (minimum size of TES sites) remain in the total.
- Optimisation: a warning is printed if the result contains unused supply (forced generation that could not be used or exported), which was not reported before.
- Wind power costs in simulations: capex and maintenance are based on the capacity added by the wind integration scenario (new capacity) and the existing capacity. Previously, the capacity was estimated from the hourly generation, which overestimated it by up to a factor of 14 (e.g. Allschwil: 187 MW instead of 13.75 MW), charged capex for existing wind power, gave negative capex with `wind_power_installed_allocation: national`, and depended on `number_of_days`. With the `national` allocation, existing wind power is not charged (as in the optimisation).
- Wind integration scenario: the integrated capacity respects `wind_power.kWp_max` (applied to the potential with annual and with winter profile separately) and `kWp_max_systemwide` (total local capacity), as in the optimisation. Existing wind power above a limit is kept; no new capacity is added in this case.
- Split of grid import into Swiss production (`m_e_ch_*`) and cross-border import (`m_e_cbimport`) no longer depends on the order of the scenarios. The Swiss part of each hour and source is limited to its value in the base split (today's demand and existing plants). A decrease of the import reduces cross-border import first; an increase first refills the Swiss part up to its limit, then adds cross-border import. Previously, the Swiss part was never refilled, so every later increase counted as cross-border import. The nuclear phase-out lowers the nuclear limit and therefore also applies after the optimisation. Only the reported mix is affected (costs and CO2 use the total import).
- Building inertia flexibility: the loss of the virtual storage is hour-dependent, r_t = r * min(1, d_h_s / delta). At the neutral state (storage half full) the loss is min(delta, d_h_s) and equals the reduction of the heat demand lower limit. Previously, the loss was delta in every hour with space heating, also in mild hours where the lower limit could only be reduced by d_h_s, which added about 1 % extra heat per year even without using the flexibility. Calliope's storage balance of the virtual storage is replaced by a custom constraint with the hourly loss rate (Calliope 0.6 only supports a constant storage_loss). The reported virtual storage losses (l_q_h_vs_*) now follow the storage balance of the optimisation (loss in hour t from the storage level of hour t-1). The constraint "virtual storage half full on average" is weighted by the hourly loss rate and uses the storage level of the previous hour (sum r_t*q_(t-1) >= 0.5*E_vs*sum r_t); this ensures that at least the heat demand without flexibility is supplied (previously, the unweighted average allowed low storage levels in mild hours to be compensated in cold hours, which added extra heat).
- Optimisation with `grid_supply` `deployment: False` stopped with an AttributeError. An error with a clear message is now raised at the start of the run: `grid_supply` is required for optimisation (it provides the grid connection). `grid_export` `kW_max` is not used (the grid connection capacity is `grid_supply` `kW_max`, which limits import and export); a warning is printed if it is set.
- Community files in `data/community_data/` (cached building data of a municipality) were never updated: after a change of the master data, the old building data was used without notice. The size and modification time of the master files are now stored next to each community file (`<name>.master_data.json`); if they differ from the current master files, or the info file is missing (community files created before this fix), the community file is rebuilt and a message is printed. Building a community file now reads only the municipality's rows of the general master file (about 4 s instead of 10 s; same data).
- Cost module: the CAPEX of technologies with a fixed capacity (storages, `capacity_kWh_max` or optimised `storage_cap`) is limited to zero from below, as for all other technologies. No effect on current results (existing storage capacity is always zero).
- `TechCore.get_v_max()` checked only the first capacity attribute (`_v_h_max`) and returned 'inf' for all other technologies; it now checks all listed attributes. No effect on current results (the value is not used for the affected technologies).

### Changed

- Compatibility with Calliope version 0.6.10 (previously 0.6.8)
- Input files structure
- Required input data

### Removed

- Inputs `demand_side` `rcp_scenario` and `ts_type`: they had no effect (the future space heating demand is scaled with heating degree days from the temperature data of the simulated year). YAML config files or a `config_dict` that still contain them now stop with an "unknown key" error; remove the two keys. The commented-out old HDD scaling function in dem_demand.py, the only code that used them, was deleted.

## [0.1.0] – 2026-03-23

Stable release.

## [0.1.0-rc2] – 2025-12-23

First stable release.

## [0.1.0-rc1] – 2025-12-09

...

## [0.1.0-rc0] – 2025-11-25

...
