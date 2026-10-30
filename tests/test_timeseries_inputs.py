"""Waste heat and manual heat demand time series; input validation; unmet demand reporting."""
import numpy as np
import pandas as pd
import pytest

from conftest import OPT, requires_data, requires_solver

pytestmark = [requires_data]

HOURS = np.arange(8760)


def _feather(path, values, col='v'):
    pd.DataFrame({col: values}).to_feather(path)
    return str(path)


@pytest.fixture
def wh_file(tmp_path):
    # distinct hourly values, so a time shift or wrong scaling is visible
    return _feather(tmp_path / 'wh.feather', 400 + 250*np.sin(2*np.pi*HOURS/24) + 3*(HOURS % 168))


@pytest.fixture
def hdm_file(tmp_path):
    return _feather(tmp_path / 'hdm.feather', 300 + 200*np.sin(2*np.pi*(HOURS-6)/24)**2 + 2*(HOURS % 168))


def _wh(path, **kw):
    return {'waste_heat': {'deployment': True, 'timeseries_file_path': path, **kw},
            'district_heating': {'heat_sources': {'waste_heat': True}}}


@requires_solver
def test_waste_heat_follows_its_time_series(run_dem, wh_file):
    model = run_dem(_wh(wh_file, tariff_CHFpkWh=0.0, co2_intensity=0.05) | {'optimisation': OPT}, days=3)
    df = model.hourly_results()
    expected = pd.read_feather(wh_file).to_numpy()[:72, 0]
    np.testing.assert_allclose(df['v_h_resource_wh'], expected)
    assert (df['v_h_wh'] <= df['v_h_resource_wh'] + 1e-3).all()
    assert df['v_h_wh'].sum() > 0
    np.testing.assert_allclose(df['v_co2_wh'], 0.05*df['v_h_wh'], atol=1e-6)


@requires_solver
def test_manual_heat_demand_follows_its_time_series(run_dem, hdm_file):
    model = run_dem({'heat_demand_manual': {'deployment': True, 'demand_mode': 'file', 'timeseries_file_path': hdm_file},
                     'optimisation': OPT}, days=3)
    df = model.hourly_results()
    np.testing.assert_allclose(df['d_h_m'], pd.read_feather(hdm_file).to_numpy()[:72, 0], rtol=1e-6)
    assert model.annual_results()['d_h_unmet_yr'] == pytest.approx(0, abs=1)


def test_manual_heat_demand_in_simulation_raises(run_dem, hdm_file):
    with pytest.raises(ValueError, match='only supported in optimisations'):
        run_dem({'heat_demand_manual': {'deployment': True, 'demand_mode': 'file', 'timeseries_file_path': hdm_file}}, days=2)


@requires_solver
@pytest.mark.parametrize('kind', ['csv', 'empty', 'short', 'nan', 'negative'])
def test_invalid_waste_heat_time_series_raise(run_dem, tmp_path, wh_file, kind):
    values = pd.read_feather(wh_file).to_numpy()[:, 0].copy()
    if kind == 'csv':
        path = str(tmp_path / 'wh.csv'); pd.DataFrame({'v': values}).to_csv(path, index=False)
    elif kind == 'empty':
        path = ''
    elif kind == 'short':
        path = _feather(tmp_path / 's.feather', values[:30])
    elif kind == 'nan':
        values[5] = np.nan; path = _feather(tmp_path / 'n.feather', values)
    else:
        values[5] = -1.0; path = _feather(tmp_path / 'm.feather', values)
    with pytest.raises(ValueError, match='waste_heat.timeseries_file_path'):
        run_dem(_wh(path) | {'optimisation': OPT}, days=2)


@requires_solver
def test_invalid_manual_heat_demand_time_series_raises(run_dem, tmp_path, hdm_file):
    values = pd.read_feather(hdm_file).to_numpy()[:, 0].copy()
    values[5] = -1.0
    path = _feather(tmp_path / 'm.feather', values)
    with pytest.raises(ValueError, match='negative values'):
        run_dem({'heat_demand_manual': {'deployment': True, 'demand_mode': 'file', 'timeseries_file_path': path},
                 'optimisation': OPT}, days=2)


def test_reassignment_rates_must_add_up_to_one(run_dem):
    key = 'total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios'
    rates = {'v_h_eh': 0.0, 'v_h_hp': 0.9, 'v_h_dh': 0.05, 'v_h_gb': 0.05, 'v_h_ob': 0.05, 'v_h_wb': 0.05,
             'v_h_solar': 0.0, 'v_h_other': 0.0}
    cfg = {'scenarios': {'demand_side': True},
           'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050}, 'total_renovation': True, key: rates}}
    with pytest.raises(ValueError, match='add up to 1'):
        run_dem(cfg, days=2)
    rates['v_h_hp'] = 0.8
    run_dem(cfg, days=2)


def test_negative_value_check_accepts_solver_size_deviations():
    from district_energy_model import dem_helper
    df = pd.DataFrame({'pot': [4e5, 0.0], 'remain': [-0.12, 0.0]})
    dem_helper.positive_values_test_df(df, 'df', error_accepted=-0.1, relative_error_accepted=1e-6)
    with pytest.raises(Exception, match='negative values'):
        dem_helper.positive_values_test_df(df.assign(remain=[-5.0, 0.0]), 'df', error_accepted=-0.1,
                                           relative_error_accepted=1e-6)


@requires_solver
def test_unmet_demand_on_internal_carriers_is_reported(run_dem, tmp_path):
    # Infeasible: heat pumps limited to existing capacity, building inertia flexibility;
    # the solver also places unmet demand on the virtual storage carrier.
    wh = _feather(tmp_path / 'wh.feather', np.full(8760, 500.0))
    cfg = {'simulation': {'district_number': 2549},
           'scenarios': {'demand_side': True, 'wind_integration': True},
           'wind_integration': {'potential_integration_factor': 0.2},
           'heat_pump': {'only_allow_existing': True}, 'oil_boiler': {'eta': 0.85}, 'solar_pvrooftop': {'eta_overall': 0.15},
           'optimisation': OPT | {'solver_option_FeasibilityTol': 1e-6},
           'steam_turbine': {'deployment': True}, 'wood_boiler_sg': {'deployment': True},
           'district_heating': {'heat_sources': {'steam_turbine': True, 'waste_heat': True}},
           'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2030},
                           'dr_flexibility_building_inertia': True, 'ev_integration': False},
           'waste_heat': {'deployment': True, 'timeseries_file_path': wh, 'tariff_CHFpkWh': 0.02}}
    with pytest.raises(RuntimeError, match='internal energy carriers'):
        run_dem(cfg, days=7)
