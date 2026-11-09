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


### Fixed
- Changes of the `grid_supply` tariff in a scenario are applied (previously, the tariff timeseries was not updated).
- Configuration YAML files are checked for valid keywords. An error is thrown if a keyword is invalid (e.g., due to incorrect spelling). Previously, the simulation just continued.
– Adjust upper and lower flexibility bounds if EV integration is <100% in optimization scenario (previously leading to an error).
- Minor bugfixes
- Bug in dem_tech_district_heating.py: 100% district heating share was not possible. This has been corrected. 

### Changed
- Compatibility with Calliope version 0.6.10 (previously 0.6.8)
- Input files structure
- Required input data

## [0.1.0] – 2026-03-23
Stable release.

## [0.1.0-rc2] – 2025-12-23
First stable release.

## [0.1.0-rc1] – 2025-12-09
...

## [0.1.0-rc0] – 2025-11-25
...
