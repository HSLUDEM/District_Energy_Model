# Changelog
All notable changes to this project will be documented in this file.

## [latest] - YYYY-MM-DD

### Added
- Demand side response: flexibility from building inertia via virtual storage
- Deep Geothermal Technology
- Cost calculation module for manual scenarios
- Added possibility to call run_dem_local.py with location of input_file, config_files and output_files
- Added heatlt heat balance plot
- Add consideration of construction period in calculation of space heating heat demand profile.
- Added grid export as technology with timeseries for prices and emissions (emissions of export yield negative emissions!)


### Fixed
- Configuration YAML files are checked for valid keywords. An error is thrown if a keyword is invalid (e.g., due to incorrect spelling). Previously, the simulation just continued.
– Adjust upper and lower flexibility bounds if EV integration is <100% in optimization scenario (previously leading to an error).
- Minor bugfixes 

### Changed
- Compatibility with Calliope version 0.6.10 (previously 0.6.8)

## [0.1.0-rc2] – 2025-12-23
First stable release.

## [0.1.0-rc1] – 2025-12-09
...

## [0.1.0-rc0] – 2025-11-25
...
