"""Simulation runs (no optimisation): energy balances, scenarios, costs and emissions."""
import numpy as np
import pandas as pd
import pytest

from conftest import ROOT, cost_overview, requires_data

ALL_SCENARIOS = {'demand_side': True, 'fossil_heater_retrofit': True, 'pv_integration': True,
                 'wind_integration': True, 'nuclear_phaseout': True, 'battery_energy_storage': True}


def heat_generation(df):
    cols = [c for c in df.columns if c.startswith('v_h_')
            and not any(s in c for s in ['_pot', '_cons', '_exp', '_remain', '_kWhpkW'])]
    return df[cols].sum(axis=1)


@requires_data
@pytest.mark.parametrize('cfg', [
    {},
    {'scenarios': ALL_SCENARIOS},
    {'scenarios': {'demand_side': True},
     'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050}}},
    {'oil_boiler': {'deployment': False}},  # deployment is only relevant for optimisation
])
def test_heat_balance_and_finite_results(run_dem, cfg):
    df = run_dem(cfg).hourly_results()
    num = df.select_dtypes('number')
    assert np.isfinite(num.to_numpy()).all()
    assert np.allclose(heat_generation(df) - df['d_h_unmet'], df['d_h'], atol=0.1)


@requires_data
def test_fossil_heater_retrofit_updates_fuel_and_emissions(run_dem):
    base = run_dem({})
    fhr = run_dem({'scenarios': {'fossil_heater_retrofit': True}})
    yr = fhr.annual_results()
    assert yr['v_h_ob_yr'] == pytest.approx(0, abs=1) and yr['v_h_gb_yr'] == pytest.approx(0, abs=1)
    assert yr['m_oil_yr'] == pytest.approx(0, abs=1) and yr['m_gas_yr'] == pytest.approx(0, abs=1)
    assert cost_overview(fhr)['co2'] < 0.5 * cost_overview(base)['co2']


@requires_data
def test_v_co2_tot_matches_cost_module(run_dem):
    for cfg in [{}, {'scenarios': {'demand_side': True}}]:
        model = run_dem(cfg)
        assert model.annual_results()['v_co2_tot_yr'] == pytest.approx(cost_overview(model)['co2'], rel=1e-6)


@requires_data
def test_unused_wet_biomass_is_not_charged(run_dem):
    costs = run_dem({}).total_cost()
    assert costs['monetary_breakdown']['wet_biomass'] == pytest.approx(0.0)


@requires_data
def test_heat_pump_cop_independent_of_number_of_days(run_dem):
    cfg = {'scenarios': {'fossil_heater_retrofit': True}}
    short = run_dem(cfg, days=7).hourly_results()
    full = run_dem(cfg, days=365).hourly_results().iloc[:168]
    assert short['v_h_hp'].sum() == pytest.approx(full['v_h_hp'].sum(), rel=1e-9)
    assert short['u_e_hp'].sum() == pytest.approx(full['u_e_hp'].sum(), rel=1e-3)


@requires_data
def test_future_climate_without_total_renovation(run_dem):
    ds = {'scenarios': {'demand_side': True},
          'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050},
                          'heat_generator_renovation': True, 'ev_integration': False}}
    today = run_dem({}, days=365)  # first: independent of launch() modifying the defaults
    no_renov = run_dem(ds | {'demand_side': ds['demand_side'] | {'total_renovation': False}}, days=365)
    rate0 = run_dem(ds | {'demand_side': ds['demand_side'] | {'total_renovation': True,
                                                              'use_constant_total_renovation_rate': True,
                                                              'constant_total_renovation_rate': 0.0}}, days=365)
    assert no_renov.annual_results()['d_h_yr'] == pytest.approx(rate0.annual_results()['d_h_yr'], rel=1e-9)
    assert no_renov.annual_results()['d_h_yr'] != pytest.approx(today.annual_results()['d_h_yr'], rel=1e-3)


@requires_data
def test_cop_mode_from_file(run_dem, tmp_path):
    cop = 3.0 + 0.5 * np.sin(np.arange(8760) / 24 * 2 * np.pi)
    pd.DataFrame({'cop': cop}).to_feather(tmp_path / 'cop.feather')
    df = run_dem({'heat_pump': {'cop_mode': 'from_file',
                                'cop_timeseries_file_path': str(tmp_path / 'cop.feather')}}).hourly_results()
    assert np.allclose(df['cops_hp_existing'], cop[:len(df)])


@requires_data
def test_pv_efficiency_scales_potential(run_dem):
    lo = run_dem({'solar_pvrooftop': {'eta_overall': 0.1}}).annual_results()
    hi = run_dem({'solar_pvrooftop': {'eta_overall': 0.3}}).annual_results()
    assert lo['v_e_pvrooftop_yr'] == pytest.approx(hi['v_e_pvrooftop_yr'])  # existing PV
    remain = lambda a: a['v_e_pvrooftop_pot_yr'] - a['v_e_pvrooftop_yr']
    assert remain(hi) / remain(lo) == pytest.approx(3.0, rel=1e-6)
    assert lo['v_h_solarthermalrooftop_pot_yr'] == pytest.approx(hi['v_h_solarthermalrooftop_pot_yr'])


@requires_data
def test_district_heating_tariff_in_costs(run_dem):
    lo = run_dem({'district_heating': {'tariff_CHFpkWh': 0.1}}).total_cost()
    hi = run_dem({'district_heating': {'tariff_CHFpkWh': 0.2}}).total_cost()
    e = lambda c: c['monetary_breakdown']['district_heating']['energy_costs']
    assert e(hi) == pytest.approx(2 * e(lo))


@requires_data
def test_no_nan_costs_without_pv_potential_groups(run_dem):
    model = run_dem({'simulation': {'district_number': 2549}})  # Kammersrohr
    assert np.isfinite(cost_overview(model)['monetary']['total'])


@requires_data
def test_custom_district_numeric_name(run_dem):
    com = pd.read_feather(ROOT / 'data/master_data/master_data_general.feather', columns=['EGID', 'GGDENR'])
    egids = [int(e) for e in com.loc[com['GGDENR'] == 2762, 'EGID'].iloc[:50]]
    model = run_dem({'meta_data': {'custom_district': {'implemented': True, 'EGID_List': egids,
                                                       'custom_district_name': 5}}}, days=1)
    assert model.annual_results()['d_h_yr'] > 0


@requires_data
def test_storage_scenario_has_no_free_initial_energy(run_dem):
    df = run_dem({'scenarios': {'thermal_energy_storage': True, 'pv_integration': True},
                  'tes_decentralised': {'deployment': True},
                  'thermal_energy_storage_scenario': {'capacity_kWh': 2e7}}).hourly_results()
    stored_at_start = df['q_h_tesdc'].iloc[0] - df['u_h_tesdc'].iloc[0] + df['v_h_tesdc'].iloc[0]
    assert df['v_h_tesdc'].sum() <= df['u_h_tesdc'].sum() + stored_at_start + 1e-6
    assert stored_at_start == pytest.approx(0, abs=1)


def _egids(*municipalities):
    com = pd.read_feather(ROOT / 'data/master_data/master_data_general.feather', columns=['EGID', 'GGDENR'])
    return [int(e) for e in com.loc[com['GGDENR'].isin(municipalities), 'EGID']]


@requires_data
def test_custom_district_of_whole_municipality_reproduces_it(run_dem):
    munic = run_dem({'simulation': {'district_number': 448}}).annual_results()  # Villeret
    custom = run_dem({'meta_data': {'custom_district': {
        'implemented': True, 'EGID_List': _egids(448), 'custom_district_name': 'all_448'}}}).annual_results()
    for key in ['d_e_yr', 'd_e_ind_yr', 'd_e_ser_yr', 'd_e_loss_yr', 'd_e_pump_yr', 's_wet_bm_yr',
                'd_h_yr', 'v_e_wp_yr', 'v_e_wp_pot_yr']:
        assert custom[key] == pytest.approx(munic[key], rel=1e-6, abs=1e-3), key


@requires_data
def test_custom_district_of_two_municipalities_wind(run_dem):
    a = run_dem({'simulation': {'district_number': 448}}).annual_results()
    b = run_dem({'simulation': {'district_number': 434}}).annual_results()
    ab = run_dem({'meta_data': {'custom_district': {
        'implemented': True, 'EGID_List': _egids(448, 434), 'custom_district_name': 'pair'}}}).annual_results()
    for key in ['v_e_wp_yr', 'v_e_wp_pot_yr']:
        assert ab[key] == pytest.approx(a[key] + b[key], rel=1e-6), key


@requires_data
def test_act_on_fossil_heater_retrofit_without_generator_renovation(run_dem):
    model = run_dem({'scenarios': {'demand_side': True},
                     'demand_side': {'act_on_fossil_heater_retrofit': True, 'heat_generator_renovation': False}}, days=2)
    assert model.annual_results()['d_h_yr'] > 0


def _plot_traces(path):
    import json
    import re
    html = open(path).read()
    data = re.search(r'Plotly\.newPlot\(\s*"[^"]+",\s*(\[.*?\])\s*,\s*\{', html, re.S).group(1)
    return json.loads(data)


@requires_data
def test_plots_show_pv_other_heat_and_storage_flows(run_dem, tmp_path):
    model = run_dem({'simulation': {'generate_plots': True, 'save_results': True},
                     'scenarios': {'pv_integration': True, 'thermal_energy_storage': True},
                     'tes_decentralised': {'deployment': True},
                     'thermal_energy_storage_scenario': {'capacity_kWh': 1e5}})
    yr, out = model.annual_results(), model.results_path
    shares = {t['name']: t['y'][0] for t in _plot_traces(f'{out}/heat_electricity_yr.html')}
    assert shares['Solar PV'] > 0 and yr['v_e_pvrooftop_cons_yr'] > 0
    assert shares['Other'] > 0 and yr['v_h_other_yr'] > 0
    cum = {t['name']: t['y'][-1] for t in _plot_traces(f'{out}/tes_and_bes_cumsum_hourly.html')}
    df = model.hourly_results()
    assert cum['q_h_tesdc charged'] == pytest.approx(df['u_h_tesdc'].sum() / 1000, rel=1e-6)
    assert cum['q_h_tesdc discharged'] == pytest.approx(df['v_h_tesdc'].sum() / 1000, rel=1e-6)
