# Changelog
All notable changes to this project will be documented in this file.

## [latest] - YYYY-MM-DD

### Added
- Demand side response: flexibility from building inertia via virtual storage

### Fixed
- Configuration YAML files are checked for valid keywords. An error is thrown if a keyword is invalid (e.g., due to incorrect spelling). Previously, the simulation just continued.
– Adjust upper and lower flexibility bounds if EV integration is <100% in optimization scenario (previously leading to an error).

### Changed
- Compatibility with Calliope version 0.6.10 (previously 0.6.8)

## [0.1.0-rc2] – 2025-12-23
First stable release.

## [0.1.0-rc1] – 2025-12-09
...

## [0.1.0-rc0] – 2025-11-25
...
