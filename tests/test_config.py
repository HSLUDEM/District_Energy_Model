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
    {'heat_pump_cp': {'instance_2': {'deploymnt': True}}},
])
def test_config_dict_unknown_key_raises(run_dem, cfg):
    with pytest.raises(KeyError):
        run_dem(cfg, days=1)


def test_yaml_open_dict_and_new_instance(tmp_path):
    from district_energy_model import dem_helper
    from district_energy_model.input_files import inputs as inp
    import copy
    (tmp_path / 'meta_data.yaml').write_text(
        'custom_district:\n  scaling_factors:\n    space_heating_demand_estimation_kWh: 2.0\n')
    (tmp_path / 'technologies.yaml').write_text(
        'heat_pump_cp:\n  instance_2:\n    deployment: true\n')
    st = dem_helper.update_scen_techs_from_yaml(tmp_path, copy.deepcopy(inp.scen_techs))
    assert st['meta_data']['custom_district']['scaling_factors'] == {'space_heating_demand_estimation_kWh': 2.0}
    assert st['heat_pump_cp']['instance_2']['deployment'] is True
    # Defaults of the new instance are taken from instance_1:
    assert st['heat_pump_cp']['instance_2']['capital_cost'] == inp.scen_techs['heat_pump_cp']['instance_1']['capital_cost']


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
