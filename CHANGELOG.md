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


### Fixed
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
