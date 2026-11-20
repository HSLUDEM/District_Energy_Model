# District Energy Model (DEM): code audit

<!-- FOOTER: DEM code audit, 10 November 2026, branch feature/national-generation-profiles (commit fb47d46) -->

Date: 10 November 2026. Branch: feature/national-generation-profiles, commit fb47d46.

## 1. Summary

The audit found seven confirmed bugs that change results without raising an error, further defects confirmed by reading the code, several suspected issues, and a number of modelling inconsistencies.

The four most serious findings affect optimisation results directly:

1. Existing heating capacity is subtracted twice when heat generator renovation is active. Investment costs are overstated.
2. Unmet demand is only reported for electricity and heat. On all other carriers (gas, wood, hydrogen, low-temperature heat and others) it is ignored, so an infeasible balance can look like a valid result.
3. The reported total monetary cost contains the penalty for unmet demand.
4. Pareto runs reuse data that the previous point has modified. The points of one Pareto front are computed for different demands and different existing capacities.

We recommend fixing these four first.

No code or data was changed during the audit. Paths in this report are relative to src/district_energy_model/.

## 2. Scope and method

| Item | Status |
|---|---|
| Model driver, demand, supply, energy balance, scenarios, costs, COP calculation, flexibility | Read in full |
| Calliope coupling and custom constraints | Read in full |
| Technology classes | Most read in full; see "not audited" |
| Full-year simulation, Allschwil (2762) | Run |
| 7-day and 14-day optimisations (Gurobi) | Run |
| Unit tests of individual functions | Run |
| Input data consistency | Checked |
| Full-year optimisation | Not possible: killed on the test machine (7 GB RAM) |
| dem_output.py (plotting), TES sites, gas, wood and hydrogen storages, custom districts, parallel runner | Not audited |

The repository contains no test suite, so there were no existing tests to execute. Findings on the optimisation rest on short runs (7 and 14 days) and on reading the code.

Each finding is marked as one of:

- **Confirmed by test**: reproduced in a model run or a unit test.
- **Confirmed by reading**: follows directly from the code, not run.
- **Suspected**: plausible, needs a decision or a check against the source.

## 3. Confirmed bugs (by test)

### 3.1 Existing heating capacity is subtracted twice

Severity: high.

- Where: techs/dem_tech_core.py, lines 180 to 210. Called from dem_costs.py line 69 and again from dem_calliope.py lines 2634, 2671, 2686, 2722 and 2759.
- What: get_needs_replacement_cap() overwrites self.existing with "existing minus replacement". The second call subtracts the replacement amount again.
- Affected runs: optimisations with the demand-side scenario and heat_generator_renovation (on by default). This includes the 2035 and 2050 study setup.

Evidence from a 2040 optimisation for Allschwil:

| Technology | Existing | Up for replacement | Passed to optimiser (old + one-to-one) | Lost |
|---|---|---|---|---|
| Heat pump | 3,236 kW | 1,082 kW | 1,072 + 1,082 kW | 1,082 kW |
| Gas boiler | 27,350 kW | 9,897 kW | 7,555 + 9,897 kW | 9,897 kW |
| Oil boiler | 15,002 kW | 4,513 kW | 5,976 + 4,513 kW | 4,513 kW |

In a unit test with 100% up for replacement, the second call returns zero for both existing and one-to-one capacity. All capacity must then be bought at the full "new" capex.

Impact: investment costs are overstated and the choice between keeping, replacing and switching heating systems is biased.

### 3.2 Unmet demand on most carriers is never reported

Severity: high.

- Where: dem_calliope.py, lines 1893 to 1974; dem_helper.py, line 441.
- What: only the electricity and heat carriers are read from Calliope's unmet_demand result. Gas, wood, oil, hydrogen, steam, low-temperature heat and others are ignored.

Evidence: the low-temperature central heat pump was forced to supply district heating, with no low-temperature source in the model. The result showed 428 MWh of heat pump output using 374 MWh of low-temperature heat that does not exist. Reported unmet demand was 0. No warning and no balance error was raised.

Impact: an infeasible fuel or source balance is covered by slack and looks like a valid result.

### 3.3 Total monetary cost includes the unmet-demand penalty

Severity: high when unmet demand occurs.

- Where: dem_calliope.py, lines 2202 to 2204.
- What: the total is recomputed from the objective value, which contains bigM times unmet demand.

Evidence: in the run of section 3.2 the reported total was 3.74e11 CHF. Calliope's own cost sum was 983,837 CHF.

Impact: the balance test accepts unmet demand up to 0.1% of annual demand. At 1e6 CHF/kWh, 100 kWh of unmet demand adds 1e8 CHF to the reported cost.

### 3.4 Pareto runs leak state between points

Severity: high for Pareto results.

- Where: dem.py, lines 1929 to 1933; dem_demand.py, lines 1204 to 1205.
- What: before each Pareto point the base scenario is rebuilt from building and meta data that the previous scenario has already modified. The building-period code GBAUP is blended towards 8023 again on each pass.

Evidence from repeating the reset sequence (2040, no optimisation):

| Pass | Annual heat demand | Heat pump heat in base scenario |
|---|---|---|
| 1 | 111.38 GWh | 8.1 GWh |
| 2 | 110.36 GWh | 33.7 GWh |
| 3 | 109.97 GWh | not recorded |

Impact: points on one Pareto front are computed for different demands and different existing capacities.

Related: blending GBAUP is arithmetic on a categorical code. A building flips from "old" to "new" at an arbitrary weight.

### 3.5 Deep geothermal capacity limit equals the capex value

Severity: medium.

- Where: techs/dem_tech_deep_geothermal.py, line 164.
- What: energy_cap_max is set to self._capex. The limit is 25,000 kW because capex is 25,000 CHF/kW. There is no other resource limit.

### 3.6 get_v_max only checks the first attribute

Severity: medium.

- Where: techs/dem_tech_core.py, line 156.
- What: the "else: return 'inf'" sits inside the loop. A technology with kW_el_max = 500 returns 'inf'.

### 3.7 Waste heat profiles that are not .feather load as zeros

Severity: medium.

- Where: techs/dem_tech_waste_heat.py, line 117, and the low-temperature variant.
- What: there is no else branch. A .npy profile was replaced by zeros without a message.

## 4. Defects confirmed by reading

| Finding | Where | Effect |
|---|---|---|
| PV kWp_max is ignored | techs/dem_tech_solar_pv_installation.py, line 101 | Stored as _v_max, never used in the optimisation. Same for solar thermal. |
| rcp_scenario and ts_type have no effect | dem_demand.py, lines 1060 to 1108 | Passed through, not used. |
| Fixed demand shares omit one-to-one replacement technologies | dem_calliope.py, lines 4061, 4071, 4081 | The "fixed" share of oil, gas and wood boilers can be exceeded. |
| Central heat pump lookups use the wrong key | dem_demand.py, line 397; dem_calliope.py, line 1948 | 'heat_pump_cp' never matches; instances are named heat_pump_cp_instance_... |
| Forced capacities not divided by the energy scaling factor | dem_calliope.py, line 2950 (hydro); CHP gas turbine; low-temperature heat pump | Only matters if the factor is not 1. |
| Nuclear phase-out only changes the reported import mix | dem_scenarios.py, line 374 | Grid CO2 uses one constant intensity, so emissions and costs do not change. |

## 5. Suspected issues

- **Hydrogen-upgrade biomass technologies** (techs/dem_tech_biomass.py, lines 703 and 1401). Hydrogen is consumed, but the gas yield equals the variant without hydrogen, because efficiency_primary is used instead of the combined efficiency. The hydrogen energy disappears.
- **Rooftop PV maintenance** (input_files/inputs.py, line 240). The value 0.03 is applied as CHF/kW/year. In the base run this gave 348 CHF/year for about 11.6 MW. Alpine PV uses 13.0. This looks like a unit error and favours rooftop PV.
- **Local wood potential.** The national sum is 59.5 TWh (Zürich 336 GWh, Winterthur 413 GWh). This appears to be several times the published sustainable wood potential. Source and units should be checked.
- **Partial-year runs with the demand-side scenario.** Heat pump category thresholds are summed over the shortened period but compared with annualised output.

## 6. Modelling and physical inconsistencies

- **Wood is matched hour by hour against a flat profile** (dem_supply.py, line 383). In the base run 0.73 GWh was "imported" although the local potential (2.93 GWh) exceeded demand (2.39 GWh).
- **Existing solar thermal follows the heat demand profile** in simulation. It produces at night and peaks in winter.
- **The manual thermal storage scenario** has no losses and no power limit, and charges through a heat pump with unlimited capacity (dem_scenarios.py, line 929).
- **Partial-year runs** take existing capacity and the PV peak from the simulated window. A 14-day January run gave 3,870 kW existing PV instead of about 10,000 kW, which understates PV capex.
- **District heating storage loss** of 0.1% per hour (input_files/inputs.py, line 355) leaves about 11% after three months. This rules out seasonal storage.
- **Building-inertia flexibility.** In hours with little space heating, holding the neutral state needs more heat than the baseline.
- **Import split.** Any increase in import is attributed entirely to cross-border import, and the split depends on the order of scenarios.

## 7. Checks that passed

- **Input data.** Heat-system shares in the meta data sum to the totals. Tariffs and profiles have no missing values. No pumping demand falls in cantons with a zero pumping profile. EV charging bounds are ordered correctly.
- **Formulations.** The national generation constraints, the EV flexibility constraints, storage efficiencies, and the energy scaling of costs and time series are consistent as far as they could be traced.
- **Balances.** The base simulation passes its own electricity and heat balance tests.

## 8. Recommended order of work

1. Fix findings 3.1 to 3.4. They affect optimisation and Pareto results directly.
2. Fix 3.5 to 3.7 and the defects in section 4. Each is a small, local change.
3. Decide on the suspected issues in section 5; these need a check against the data sources.
4. Add a small regression test suite. A full-year simulation for one municipality runs in under a second and already exercises the balance tests.
5. Repeat the optimisation checks with a full-year run on a machine with more memory.
