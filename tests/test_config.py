"""Configuration handling (config_dict / YAML) and input validation."""
import pytest

from conftest import requires_data


@requires_data
def test_launch_does_not_modify_defaults(run_dem):
    from district_energy_model.input_files import inputs as inp
    run_dem({'scenarios': {'pv_integration': True, 'fossil_heater_retrofit': True}}, days=1)
    assert inp.scen_techs['scenarios']['pv_integration'] is False
    assert inp.scen_techs['scenarios']['fossil_heater_retrofit'] is False
    model = run_dem({}, days=1)
    assert model.scen_techs['scenarios']['pv_integration'] is False


@requires_data
@pytest.mark.parametrize('cfg', [
    {'solar_pv': {'potential_integration_factor': 0.7}},  # example from the documentation
    {'scenarios': {'pv_integraton': True}},
    {'heat_pump_cp': {'deploymnt': True}},
    {'heat_pump_cp': {'instance_1': {'deployment': True}}},  # instance dicts were replaced by lists
])
def test_config_dict_unknown_key_raises(run_dem, cfg):
    with pytest.raises(KeyError):
        run_dem(cfg, days=1)


def test_yaml_open_dict_and_list_parameters(tmp_path):
    from district_energy_model import dem_helper
    from district_energy_model.input_files import inputs as inp
    import copy
    (tmp_path / 'meta_data.yaml').write_text(
        'custom_district:\n  scaling_factors:\n    space_heating_demand_estimation_kWh: 2.0\n')
    (tmp_path / 'technologies.yaml').write_text(
        'heat_pump_cp:\n  deployment: true\n  cop_constant_value: [3.0, 4.0]\n')
    st = dem_helper.update_scen_techs_from_yaml(tmp_path, copy.deepcopy(inp.scen_techs))
    assert st['meta_data']['custom_district']['scaling_factors'] == {'space_heating_demand_estimation_kWh': 2.0}
    assert st['heat_pump_cp']['deployment'] is True
    assert st['heat_pump_cp']['cop_constant_value'] == [3.0, 4.0]
    # Two instances; single values apply to both:
    instances = dem_helper.expand_list_parameters(st['heat_pump_cp'], 'heat_pump_cp')
    assert [i['cop_constant_value'] for i in instances] == [3.0, 4.0]
    assert all(i['capital_cost'] == inp.scen_techs['heat_pump_cp']['capital_cost'] for i in instances)


@pytest.mark.parametrize('params', [{'kW_th_max': [100, 200], 'cop_constant_value': [3.0, 4.0, 5.0]},
                                    {'kW_th_max': []}])
def test_list_parameters_of_different_lengths_raise(params):
    from district_energy_model import dem_helper
    with pytest.raises(ValueError):
        dem_helper.expand_list_parameters({'deployment': True, **params}, 'heat_pump_cp')


@requires_data
@pytest.mark.parametrize('days', [0, 400, 7.5])
def test_number_of_days_validation(run_dem, days):
    with pytest.raises(ValueError, match='number_of_days'):
        run_dem({}, days=days)


@requires_data
@pytest.mark.parametrize('nr, match', [(99999, 'not found'), (2391, 'omit')])
def test_invalid_district_number(run_dem, nr, match):
    with pytest.raises(ValueError, match=match):
        run_dem({'simulation': {'district_number': nr}}, days=1)


def test_yaml_scientific_notation_and_inf(tmp_path):
    from district_energy_model import dem_helper
    from district_energy_model.input_files import inputs as inp
    import copy
    (tmp_path / 'solar_pvrooftop.yaml').write_text('kWp_max: 1e5\n')
    (tmp_path / 'supply.yaml').write_text('gas_price_CHFpkWh: 1e-1\n')
    (tmp_path / 'grid_supply.yaml').write_text('kW_max: .inf\n')
    st = dem_helper.update_scen_techs_from_yaml(tmp_path, copy.deepcopy(inp.scen_techs))
    # PyYAML reads 1e5 as a string (YAML 1.1):
    assert st['solar_pvrooftop']['kWp_max'] == 1e5
    assert st['supply']['gas_price_CHFpkWh'] == 0.1
    # The model uses 'inf' for unlimited values:
    assert st['grid_supply']['kW_max'] == 'inf'


def test_config_dict_float_inf_is_inf_string():
    from district_energy_model import dem_helper
    from district_energy_model.input_files import inputs as inp
    import copy
    st = dem_helper.update_scen_techs_from_config(copy.deepcopy(inp.scen_techs), {'grid_supply': {'kW_max': float('inf')}})
    assert st['grid_supply']['kW_max'] == 'inf'


@requires_data
def test_saved_scen_techs_can_be_loaded_again(run_dem, tmp_path):
    from district_energy_model import dem_helper
    from district_energy_model.input_files import inputs as inp
    import copy
    import shutil
    cfg = {'scenarios': {'demand_side': True}, 'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2040}},
           'simulation': {'save_results': True}}
    model = run_dem(cfg, days=1, output_dir=str(tmp_path / 'out'))
    cfg_dir = tmp_path / 'cfg'
    cfg_dir.mkdir()
    shutil.copy(f'{model.results_path}/scen_techs.yaml', cfg_dir / 'technologies.yaml')
    # The run adds demand_side.heat_generator_replacement_rates, which raised a KeyError here:
    st = dem_helper.update_scen_techs_from_yaml(cfg_dir, copy.deepcopy(inp.scen_techs))
    assert st['demand_side']['simulation_year']['future_year'] == 2040


@requires_data
def test_nested_output_dir_is_created(run_dem, tmp_path):
    model = run_dem({'simulation': {'save_results': True}}, days=1, output_dir=str(tmp_path / 'a' / 'b' / 'run'))
    assert (tmp_path / 'a' / 'b' / 'run' / 'hourly_results.csv').is_file()
    assert model.results_path == str(tmp_path / 'a' / 'b' / 'run')
