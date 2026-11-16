"""Simulation runs (no optimisation): energy balances, scenarios, costs and emissions."""
import numpy as np
import pandas as pd
import pytest

from conftest import ROOT, cost_overview, deep_update, requires_data

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
def test_constant_renovation_rate_splits_by_weight(run_dem):
    # A3: with the constant renovation rate the building period GBAUP must not be averaged
    # with 8023 (renovation counted twice: 100 % of space heating with the new-building profile
    # in 2050). Old buildings (GBAUP <= 8015) get the new profile by their renovation weight.
    ds = {'scenarios': {'demand_side': True},
          'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050}}}
    no_renov = run_dem(ds | {'demand_side': ds['demand_side'] | {'total_renovation': False}})
    model = run_dem(ds)  # defaults: constant rate 0.018
    gbaup = no_renov.df_com_yr['GBAUP'].astype(float)  # building periods (codes 8011-8023)
    df = model.df_com_yr
    d = df['d_h_s_yr_future_renov_adjusted']
    w = df['total_renovation_flag'].astype(float)
    old = gbaup <= 8015
    assert 0.2 < (d * w).sum() / d.sum() < 0.6  # mean renovation weight (Allschwil 2050: 0.38)
    ed = model.energy_demand
    share_new = ed._d_h_s_new_yr / d.sum()
    lower = (d[gbaup > 8015].sum() + (d[old] * w[old]).sum()) / d.sum()
    upper = lower + d[gbaup.isna()].sum() / d.sum()  # buildings without GBAUP (A4)
    assert lower - 1e-9 <= share_new <= upper + 1e-9
    assert share_new < 0.8  # before: 1.0
    assert ed._d_h_s_new_yr + ed._d_h_s_old_yr == pytest.approx(d.sum(), rel=0.02)
    assert df['GBAUP'].astype(float).fillna(0).equals(gbaup.fillna(0))  # period codes not averaged


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
def test_annual_share_plot_shows_pv_and_other_heat(run_dem, tmp_path):
    model = run_dem({'simulation': {'generate_plots': True, 'save_results': True},
                     'scenarios': {'pv_integration': True}})
    yr, out = model.annual_results(), model.results_path
    shares = {t['name']: t['y'][0] for t in _plot_traces(f'{out}/heat_electricity_yr.html')}
    assert shares['Solar PV'] > 0 and yr['v_e_pvrooftop_cons_yr'] > 0
    assert shares['Other'] > 0 and yr['v_h_other_yr'] > 0


@requires_data
def test_hp_cop_without_division_warning(run_dem):
    # GitHub issues #53 and #66: the heating curves reach the outdoor temperature above 15 degC
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings('error', message='divide by zero', category=RuntimeWarning)
        run_dem(days=1)



def _temperature_gap_hours(com_nr, year, n_hours):
    raw = pd.read_feather(f'{ROOT}/data/weather_data/community_files/{com_nr}.feather')[year].to_numpy()
    gap = np.where(np.isnan(raw))[0]
    return gap[gap < n_hours]


@requires_data
def test_temperature_gaps_stop_the_model(run_dem):
    # GitHub issue #59: municipality 4511 has no temperatures for 507 hours of 2016 (hours 921-4566)
    with pytest.raises(ValueError, match='FAULTY TEMPERATURE DATA'):
        run_dem({'simulation': {'district_number': 4511}}, days=1)


@requires_data
def test_temperature_gaps_allowed_give_cop_2(run_dem):
    # GitHub issue #59: with allow_temperature_data_gaps a (red) warning, COP 2.0 in the gaps
    hours = _temperature_gap_hours(4511, 2016, 60 * 24)
    assert len(hours) > 24
    with pytest.warns(UserWarning, match='FAULTY TEMPERATURE DATA') as w:
        model = run_dem({'simulation': {'district_number': 4511, 'allow_temperature_data_gaps': True}}, days=60)
    assert any(str(x.message).startswith('\033[91m') for x in w)
    hp = model.tech_instances['heat_pump']
    for cop in [hp._cops_existing, hp._cops_new]:
        assert np.all(cop[hours] == 2.0)  # before: 1.0 (NaN replaced)
        assert not np.isnan(cop).any()


def _df_com_old_mask(df):
    return df['GBAUP'].isna() | (df['GBAUP'] <= 8015)


def _raw_building_period(com_nr):
    """GBAUP and GBAUJ of the master data (before the fill), indexed by EGID."""
    com = pd.read_feather(ROOT / 'data/master_data/master_data_general.feather',
                          columns=['EGID', 'GGDENR', 'GBAUP', 'GBAUJ'])
    return com.loc[com['GGDENR'] == com_nr].set_index('EGID')


@requires_data
def test_buildings_without_building_period_keep_their_space_heating(run_dem):
    # A4: 62 of 2055 buildings of Wuerenlingen have no GBAUP (21 % of the space heating). With the
    # constant renovation rate (default), GBAUP became <NA> (Int64) and these buildings were in
    # neither the old nor the new group: -17 % space heating in the hourly profile (2050).
    model = run_dem({'simulation': {'district_number': 4047},
                     'scenarios': {'demand_side': True},
                     'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050}}}, days=365)
    df = model.df_com_yr
    assert _raw_building_period(4047)['GBAUP'].isna().sum() > 0
    buildings = df['d_h_s_yr_future_renov_adjusted'].sum()
    assert model.energy_demand._d_h_s.sum() == pytest.approx(buildings, rel=1e-6)
    assert model.annual_results()['d_h_s_yr'] == pytest.approx(buildings, rel=1e-6)


@requires_data
def test_buildings_without_building_period_count_as_old(run_dem):
    # A28: without demand side (float GBAUP), compute_d_h_yr() put buildings without GBAUP into
    # the new group (12 degC), while add_future_demand_col() scaled them as old (15 degC).
    # Both treat them as old now (as if built before 1919).
    model = run_dem({'simulation': {'district_number': 4047}}, days=1)
    df = model.df_com_yr
    raw = _raw_building_period(4047)
    old = df['EGID'].map(raw['GBAUP'].isna() | (raw['GBAUP'] <= 8015)).astype(bool)
    sh = df['space_heating_demand_estimation_kWh']
    assert sh[df['EGID'].map(raw['GBAUP'].isna()).astype(bool)].sum() > 0
    assert model.energy_demand._d_h_s_old_yr == pytest.approx(sh[old].sum(), rel=1e-9)
    assert model.energy_demand._d_h_s_new_yr == pytest.approx(sh[~old].sum(), rel=1e-9)


@requires_data
def test_buildings_without_building_period_get_the_oldest_period(run_dem):
    # A4: buildings without GBAUP (and without GBAUJ, as all of them in the master data) get
    # 8011 (before 1919). The cached community file keeps the raw data.
    model = run_dem({'simulation': {'district_number': 4047}}, days=1)
    df = model.df_com_yr.set_index('EGID')
    raw = _raw_building_period(4047)
    missing = raw.index[raw['GBAUP'].isna() & raw['GBAUJ'].isna()]
    assert len(missing) > 0
    assert df['GBAUP'].notna().all()
    assert (df.loc[missing, 'GBAUP'] == 8011).all()
    given = raw.index[raw['GBAUP'].notna()]
    assert (df.loc[given, 'GBAUP'] == raw.loc[given, 'GBAUP']).all()
    cache = pd.read_csv(f"{model.paths.com_data_dir}{model.com_name_}.csv", usecols=['GBAUP'])
    assert cache['GBAUP'].isna().sum() == len(missing)


def test_building_period_from_construction_year():
    # A4: GBAUP from GBAUJ by the GWR classes (8011 before 1919, ..., 8023 from 2016).
    from district_energy_model.dem_demand import fill_building_period
    years = [1500, 1918, 1919, 1945, 1946, 1960, 1961, 1970, 1971, 1980, 1981, 1985, 1986, 1990,
             1991, 1995, 1996, 2000, 2001, 2005, 2006, 2010, 2011, 2015, 2016, 2024]
    expected = [8011, 8011] + [p for p in range(8012, 8023) for _ in (0, 1)] + [8023, 8023]
    df = pd.DataFrame({'GBAUJ': years + [np.nan, 1990], 'GBAUP': [np.nan] * len(years) + [np.nan, 8014]})
    out = fill_building_period(df)
    assert out['GBAUP'].tolist() == expected + [8011, 8014]  # given GBAUP is kept
    assert df['GBAUP'].isna().sum() == len(years) + 1  # input unchanged


@requires_data
def test_building_period_from_construction_year_matches_master_data():
    # A4: the GBAUJ -> GBAUP mapping reproduces GBAUP of all buildings that have both.
    from district_energy_model.dem_demand import gbaup_from_gbauj
    com = pd.read_feather(ROOT / 'data/master_data/master_data_general.feather', columns=['GBAUP', 'GBAUJ']).dropna()
    assert (gbaup_from_gbauj(com['GBAUJ']) == com['GBAUP']).all()


@requires_data
def test_buildings_lost_in_old_new_split_raise(run_dem, monkeypatch):
    # A4: a split that loses buildings (here: no fill, <NA> in both groups, as before the fix)
    # must stop the model instead of silently reducing the space heating demand.
    from district_energy_model import dem_demand
    monkeypatch.setattr(dem_demand, 'fill_building_period', lambda df: df)
    monkeypatch.setattr(dem_demand, 'is_old_building', lambda gbaup: gbaup.astype('Int64') <= 8015)
    with pytest.raises(ValueError, match=r'municipality 4047.*do not add up.*Missing'):
        run_dem({'simulation': {'district_number': 4047}}, days=1)


def _dh_grid_costs(model, days):
    """District heating grid costs (annualised capex, maintenance) of the cost module, scaled to a year."""
    dh = model.total_cost()['monetary_breakdown']['district_heating']
    return dh['annualized_capex'] * 365 / days, dh['opex'] * 365 / days


@requires_data
def test_simulation_charges_existing_district_heating_grid(run_dem):
    # A7: simulations had no grid costs (maintenance of the existing grid missing)
    model = run_dem({}, days=7)
    dh = model.tech_instances['district_heating']
    peak = dh.get_v_h().max()
    assert 0 < peak <= dh._kW_th_max_grid_categories[0]  # existing grid suffices
    capex, opex = _dh_grid_costs(model, 7)
    assert capex == pytest.approx(0.0)
    assert opex == pytest.approx(dh._maintenance_cost_grid_categories[0] * peak, rel=1e-9)  # ~7.3 CHF/kW/a
    assert opex > 0


_DH70_SH = {'v_h_eh': 0.0, 'v_h_hp': 0.15, 'v_h_dh': 0.7, 'v_h_gb': 0.05, 'v_h_ob': 0.05,
            'v_h_wb': 0.05, 'v_h_solar': 0.0, 'v_h_other': 0.0}
_DH70 = {'scenarios': {'demand_side': True},
         'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050},
                         'total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios': _DH70_SH}}


def _dh_categories(model):
    from district_energy_model.dem_costs import annuity_factor
    dh = model.tech_instances['district_heating']
    af = annuity_factor(dh._lifetime, dh._interest_rate)
    return (dh, dh._kW_th_max_grid_categories, dh._investment_cost_grid_categories,
            dh._maintenance_cost_grid_categories, af)


@requires_data
def test_simulation_charges_district_heating_grid_expansion(run_dem):
    # A7: renovated buildings reassigned to district heating (70 %, 2050) expand the grid; the
    # expansion beyond the existing grid was free in simulations. Default input
    # district_heating.simulation_grid_category_fill = 'cheapest_first'.
    model = run_dem(_DH70, days=7)
    dh, caps, inv, mnt, af = _dh_categories(model)
    expansion = dh.get_v_h().max() - caps[0]
    # Hand calculation: existing grid full, the expansion in the expansion category with the
    # lowest annual cost per kW (as the optimiser chooses), if it fits there
    cheapest = min(range(1, len(caps)), key=lambda i: inv[i] * af + mnt[i])
    assert 0 < expansion <= caps[cheapest]
    capex, opex = _dh_grid_costs(model, 7)
    assert capex == pytest.approx(inv[cheapest] * expansion * af, rel=1e-9)
    assert opex == pytest.approx(mnt[0] * caps[0] + mnt[cheapest] * expansion, rel=1e-9)
    assert capex > 0


@requires_data
def test_simulation_grid_expansion_in_category_order(run_dem):
    # A7: with 'category_order' the expansion fills category 1 (nearest buildings) first, then 2
    model = run_dem(deep_update(_DH70, {'district_heating': {'simulation_grid_category_fill': 'category_order'}}),
                    days=7)
    dh, caps, inv, mnt, af = _dh_categories(model)
    expansion = dh.get_v_h().max() - caps[0]
    cat1 = min(expansion, caps[1])
    cat2 = expansion - cat1
    assert cat1 > 0 and 0 < cat2 <= caps[2]  # Allschwil, 7 days: category 1 full, rest in 2
    assert [v.max() for v in dh.get_v_h_by_categories()] == pytest.approx([caps[0], cat1, cat2, 0.0], rel=1e-9)
    capex, opex = _dh_grid_costs(model, 7)
    assert capex == pytest.approx((inv[1] * cat1 + inv[2] * cat2) * af, rel=1e-9)
    assert opex == pytest.approx(mnt[0] * caps[0] + mnt[1] * cat1 + mnt[2] * cat2, rel=1e-9)


@requires_data
def test_invalid_grid_category_fill_raises(run_dem):
    with pytest.raises(ValueError, match='simulation_grid_category_fill'):
        run_dem({'district_heating': {'simulation_grid_category_fill': 'nearest'}}, days=1)


_TES_LEGACY = {'scenarios': {'pv_integration': True, 'thermal_energy_storage': True},
               'tes_decentralised': {'deployment': True},
               'thermal_energy_storage_scenario': {'capacity_kWh': 2e4, 'initial_charge': 0.2}}


@requires_data
def test_thermal_energy_storage_scenario_has_losses_and_charge_rate_limit(run_dem):
    # A15: the manual TES scenario runs as the combined storage scenario with
    # only tes_decentralised (losses, efficiency and charge rate apply).
    model = run_dem(_TES_LEGACY, days=365)
    df = model.hourly_results()
    cap = 2e4
    rate = model.scen_techs['tes_decentralised']['chg_dchg_per_cap_max'] * cap
    assert df['u_h_tesdc'].sum() > 0
    assert df['u_h_tesdc'].max() <= rate + 1e-6
    assert df['v_h_tesdc'].max() <= rate + 1e-6
    assert df['q_h_tesdc'].max() <= cap + 1e-6
    losses = df[['l_u_h_tesdc', 'l_v_h_tesdc', 'l_q_h_tesdc']].sum()
    assert (losses > 0).all()
    # The user's configuration is not changed by the redirect:
    assert model.scen_techs['scenarios']['thermal_energy_storage'] is True
    assert model.scen_techs['scenarios']['scenario_battery_plus_thermal_energy_storage'] is False
    assert model.scen_techs['bes']['deployment'] is True


@requires_data
def test_legacy_storage_scenarios_equal_combined_scenario_with_one_storage(run_dem):
    combined = {'scenarios': {'pv_integration': True,
                              'scenario_battery_plus_thermal_energy_storage': True}}
    cases = [
        (_TES_LEGACY,
         {'tes_decentralised': {'deployment': True, 'capacity_kWh_max': 2e4, 'initial_charge': 0.2},
          'bes': {'deployment': False}}),
        ({'scenarios': {'pv_integration': True, 'battery_energy_storage': True},
          'tes_decentralised': {'deployment': True, 'capacity_kWh_max': 5e4},  # not used
          'battery_energy_storage_scenario': {'capacity_kWh': 5e4, 'initial_charge': 0.2}},
         {'bes': {'capacity_kWh_max': 5e4, 'initial_charge': 0.2}}),
    ]
    for legacy_cfg, combined_cfg in cases:
        legacy = run_dem(legacy_cfg, days=365).hourly_results()
        direct = run_dem({**combined, **combined_cfg}, days=365).hourly_results()
        cols = [c for c in direct.columns if c in legacy.columns]
        assert len(cols) >= len(direct.columns) - 3
        # dtypes of the zero columns of a non-deployed storage differ (int/float)
        pd.testing.assert_frame_equal(legacy[cols], direct[cols], check_dtype=False)


@requires_data
def test_both_legacy_storage_scenarios_point_to_combined_scenario(run_dem):
    with pytest.raises(NotImplementedError,
                       match='scenarios.scenario_battery_plus_thermal_energy_storage'):
        run_dem({'scenarios': {'thermal_energy_storage': True, 'battery_energy_storage': True},
                 'tes_decentralised': {'deployment': True},
                 'thermal_energy_storage_scenario': {'capacity_kWh': 2e4}}, days=1)


def _generator_renovation(year, **demand_side):
    return {'scenarios': {'demand_side': True},
            'demand_side': {'simulation_year': {'type': 'future', 'future_year': year},
                            'heat_generator_renovation': True, **demand_side}}


@requires_data
def test_generator_renovation_charges_replacement_of_remaining_boilers(run_dem):
    # A6: the replacement capex was only charged for the peak above the base (pre-scenario) capacity
    # minus the replaced part; after renovation and in a warmer climate the boiler peaks stay below it,
    # so replacing end-of-life boilers was free. In 2050 all existing boilers are at the end of their
    # lifetime: the whole remaining stock (= peak after the scenarios) needs one-to-one replacement.
    from district_energy_model import dem_constants as C
    model = run_dem(_generator_renovation(2050))
    for tech in ['oil_boiler', 'gas_boiler']:
        assert model.scen_techs[tech]['lifetime'] <= 2050 - C.RENOVATION_YEAR
        t = model.tech_instances[tech]
        peak = t.get_output().max()
        assert peak > 0
        assert t.needs_replacement == pytest.approx(peak, rel=1e-9), tech
        assert t.existing == pytest.approx(0, abs=1e-6), tech
        assert t.get_total_capex() == pytest.approx(t._capex_one_to_one_replacement * peak, rel=1e-9), tech


@requires_data
def test_generator_renovation_replaces_end_of_life_share_of_remaining_stock(run_dem, monkeypatch):
    # A6: replacement = end-of-life share (by age, weighted with the base heat demand) of the stock
    # remaining after the scenarios (min(base capacity, peak)); the rest is existing without capex.
    from district_energy_model import dem_constants as C, dem_costs
    base = {}
    orig_old = dem_costs.get_old_capacities

    def old_capacities(tech_instances, debug=False):
        out = orig_old(tech_instances, debug)
        base.update({t: tech_instances[t].existing for t in ['oil_boiler', 'gas_boiler']})
        return out

    monkeypatch.setattr(dem_costs, 'get_old_capacities', old_capacities)
    year = 2040
    model = run_dem(_generator_renovation(year, total_renovation=False))
    df, st = model.df_com_yr, model.scen_techs
    names = {'eh': 'electric_heater', 'hp': 'heat_pump', 'dh': 'district_heating', 'gb': 'gas_boiler',
             'ob': 'oil_boiler', 'wb': 'wood_boiler', 'solar': 'solarthermal_rooftop'}
    lifetimes = {f'v_h_{k}': st[t]['lifetime'] for k, t in names.items()} | {'v_h_other': 1.0}
    lifetime = df['Heating_System'].map(lifetimes)
    end_of_life_year = df['GBAUJ'] + lifetime
    recently_built = end_of_life_year >= C.RENOVATION_YEAR
    end_of_life = ((year - C.RENOVATION_YEAR) / lifetime).clip(upper=1.0)
    end_of_life[recently_built] = (year > end_of_life_year[recently_built]).astype(float)
    end_of_life = end_of_life.fillna(1.0)
    for k, tech in [('ob', 'oil_boiler'), ('gb', 'gas_boiler')]:
        weight = (df['space_heating_demand_estimation_kWh'].where(df['Heating_System'] == f'v_h_{k}', 0.0).fillna(0.0)
                  + df['DHW_demand_estimation_kWh'].where(df['Hot_Water_System'] == f'v_hw_{k}', 0.0).fillna(0.0))
        share = (weight * end_of_life).sum() / weight.sum()
        assert 0.1 < share < 0.99
        t = model.tech_instances[tech]
        remaining = min(base[tech], t.get_output().max())
        assert t.needs_replacement == pytest.approx(share * remaining, rel=1e-9), tech
        assert t.existing == pytest.approx((1 - share) * remaining, rel=1e-9), tech
        assert t.get_total_capex() == pytest.approx(t._capex_one_to_one_replacement * share * remaining, rel=1e-9), tech


@requires_data
@pytest.mark.parametrize('demand_side', [
    {'simulation_year': {'type': 'current'}},
    {'simulation_year': {'type': 'future', 'future_year': 2050}, 'total_renovation': False},
    {'simulation_year': {'type': 'future', 'future_year': 2050}},
])
def test_short_demand_side_simulation_equals_first_days_of_full_year(run_dem, demand_side):
    # A10: the time series were cut to number_of_days before the demand-side scenario, so the
    # heat pump category totals (existing / one-to-one / new) were sums over the simulated days
    # while getRelativeSharesOfHPCategories compares them with annual values: in short runs
    # almost all heat pump heat counted as 'new' (7 days: +22 % heat pump electricity).
    cfg = {'scenarios': {'demand_side': True}, 'demand_side': demand_side}
    short = run_dem(cfg, days=7).hourly_results().select_dtypes('number')
    full = run_dem(cfg, days=365).hourly_results().select_dtypes('number').iloc[:len(short)]
    assert len(short) == 7 * 24
    assert short['u_e_hp'].sum() > 0
    assert short['u_e_hp'].sum() == pytest.approx(full['u_e_hp'].sum(), rel=1e-9)
    cols = [c for c in short.columns if c in full.columns]
    assert set(cols) == set(short.columns)
    np.testing.assert_allclose(short[cols].to_numpy(float), full[cols].to_numpy(float), rtol=1e-9, atol=1e-6)


@requires_data
def test_district_heating_categories_independent_of_number_of_days(run_dem):
    # A12: with total renovation, the district heating grid categories were sized with the peak
    # heat demand of the simulated days (7 days in 2050: 2,616/4,630/11,927/3,427 kW instead of
    # 4,774/8,452/21,770/6,256 kW), i.e. the grid capex per kW depended on number_of_days.
    cfg = {'scenarios': {'demand_side': True},
           'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050},
                           'total_renovation': True}}
    cats = {}
    for days in [7, 365]:
        dh = run_dem(cfg, days=days).tech_instances['district_heating']
        cats[days] = (list(dh._kW_th_max_grid_categories), list(dh._investment_cost_grid_categories))
    assert sum(cats[365][0]) > 0
    np.testing.assert_allclose(cats[7][0], cats[365][0], rtol=1e-9)
    np.testing.assert_allclose(cats[7][1], cats[365][1], rtol=1e-9)


@requires_data
def test_existing_capacities_are_annual_peaks_in_short_simulations(run_dem, monkeypatch):
    # A11: existing capacities (dem_costs.get_old_capacities) were the peaks of the simulated
    # days (7 days: heat pumps 1,890 kW instead of 3,450 kW), so short runs paid for existing
    # capacity again.
    from district_energy_model import dem_costs
    techs = ['heat_pump', 'oil_boiler', 'gas_boiler', 'wood_boiler', 'electric_heater', 'district_heating']
    existing = []
    orig_old = dem_costs.get_old_capacities

    def old_capacities(tech_instances, debug=False):
        out = orig_old(tech_instances, debug)
        existing.append({t: tech_instances[t].existing for t in techs})
        return out

    monkeypatch.setattr(dem_costs, 'get_old_capacities', old_capacities)
    full = run_dem({}, days=365).hourly_results()
    run_dem({}, days=7)
    assert existing[0]['heat_pump'] == pytest.approx(full['v_h_hp'].max(), rel=1e-9)
    for t in techs:
        assert existing[1][t] == pytest.approx(existing[0][t], rel=1e-9), t
