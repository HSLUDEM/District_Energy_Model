"""Optimisation runs (Gurobi)."""
import shutil

import pytest

from conftest import OPT, cost_overview, requires_data, requires_solver

pytestmark = [requires_data, requires_solver]


@pytest.mark.parametrize('district', [2762, 2549, 448])  # Allschwil, Kammersrohr, Villeret (wind export)
def test_cost_module_matches_objective(run_dem, district):
    model = run_dem({'simulation': {'district_number': district}, 'optimisation': OPT})
    objective = model.total_cost()['objective']['total']
    assert cost_overview(model)['monetary']['total'] == pytest.approx(objective, rel=0.01, abs=100)
    assert model.annual_results()['v_co2_tot_yr'] == pytest.approx(cost_overview(model)['co2'], rel=1e-6)


def test_pareto_front(run_dem, tmp_path):
    from district_energy_model.input_files import inputs as inp
    cfg = {'simulation': {'save_results': True},
           'optimisation': OPT | {'pareto_monetary_co2': True, 'N_pareto': 3}}
    model = run_dem(cfg, days=2)
    eps = [r['eps_n'] for r in model.pareto_results]
    cost = [r['dict_total_costs']['monetary']['total'] for r in model.pareto_results]
    assert len(eps) == 3 and eps == sorted(eps)
    assert cost[0] >= cost[-1] - 1e-6
    # Saved results can be loaded again:
    inp.toggle_load_pareto_results = True
    try:
        loaded = run_dem(cfg, days=2)
    finally:
        inp.toggle_load_pareto_results = False
    assert len(loaded.pareto_results) == 3


def test_wind_systemwide_cap(run_dem):
    wind = [run_dem({'wind_power': {'kWp_max_systemwide': cap}, 'optimisation': OPT}).annual_results()['v_e_wp_yr']
            for cap in [0, 2000, 6000]]
    assert wind[0] == pytest.approx(0, abs=1)
    assert wind[2] == pytest.approx(3 * wind[1], rel=1e-3)


def test_waste_to_energy_unbounded_input_rejected(run_dem):
    cfg = {'waste_to_energy': {'deployment': True}, 'optimisation': OPT,
           'district_heating': {'heat_sources': {'waste_to_energy': True}}}
    with pytest.raises(ValueError, match='unbounded'):
        run_dem(cfg, days=2)
    model = run_dem(cfg | {'supply': {'annual_msw_supply': 1e6}})
    assert model.annual_results()['d_h_unmet_yr'] == pytest.approx(0, abs=1)


def test_deployment_false_removes_tech_in_optimisation(run_dem):
    model = run_dem({'oil_boiler': {'deployment': False}, 'optimisation': OPT}, days=2)
    assert 'oil_boiler' not in model.tech_instances
    assert model.annual_results()['d_h_unmet_yr'] == pytest.approx(0, abs=1)


def test_deployment_false_with_manual_scenario(run_dem):
    model = run_dem({'oil_boiler': {'deployment': False}, 'scenarios': {'pv_integration': True},
                     'optimisation': OPT}, days=2)
    assert model.annual_results()['d_h_unmet_yr'] == pytest.approx(0, abs=1)


def test_building_inertia_flexibility_without_district_heating(run_dem):
    model = run_dem({'district_heating': {'deployment': False}, 'scenarios': {'demand_side': True},
                     'demand_side': {'dr_flexibility_building_inertia': True}, 'optimisation': OPT}, days=2)
    assert model.annual_results()['u_h_vs_dh_yr'] == pytest.approx(0, abs=1e-3)


def test_tes_site_fixed_costs_independent_of_energy_scaling(run_dem):
    site = {'name': 'PTES_1', 'exclusion_group': None, 'force_deployment': True, 'color': [122, 73, 14],
            'type': 'simple_fully_stratified_three_temperature_levels',
            'rel_size_t_levels': {'ltlt': 0.6, 'htlt': 0.2, 'htht': 0.2},
            'capacity_kWh_min': 20000, 'capacity_kWh_max': 60000, 'capex_base': 600000, 'capex_per_kWh': 2.0,
            'maintenance_cost_base': 1000, 'maintenance_cost_per_kWh': 0.05,
            'storage_loss_rate': {'ltlt': 0.001, 'htlt': 0.001, 'htht': 0.002},
            'eta_chg_dchg': {'ltlt': 0.9, 'htlt': 0.9, 'htht': 0.9}, 'lifetime': 30.0, 'interest_rate': 0.025,
            'chg_dchg_per_cap_max': 0.1, 'connected_techs': {'lt': ['heatlt'], 'ht': ['obcp', 'dhimp']}}
    cfg = {'tes_sites': {'deployment': True, 'list_generation_mode': 'externally_controlled',
                         'generation_function_parameters': {'list_of_tes_options': [site]}},
           'oil_boiler_cp': {'deployment': True}, 'district_heating': {'heat_sources': {'oil_boiler_cp': True}}}
    obj = [run_dem(cfg | {'optimisation': OPT | {'calliope_energy_scaling_factor': s}}, days=2).total_cost()['objective']['total']
           for s in [1, 1000]]
    assert obj[1] == pytest.approx(obj[0], rel=1e-6)


@pytest.mark.skipif(shutil.which('cbc') is None, reason='CBC not on PATH')
def test_cbc_receives_its_own_option_names(run_dem, capfd):
    model = run_dem({'optimisation': {'enabled': True, 'solver': 'cbc', 'solver_option_TimeLimit': 600}},
                    days=2, quiet=False)
    out = capfd.readouterr().out
    assert 'No match for' not in out
    assert '-seconds 600' in out
    assert model.annual_results()['d_h_unmet_yr'] == pytest.approx(0, abs=1)


def test_pareto_front_with_building_inertia_flexibility(run_dem):
    model = run_dem({'scenarios': {'demand_side': True}, 'demand_side': {'dr_flexibility_building_inertia': True},
                     'optimisation': OPT | {'pareto_monetary_co2': True, 'N_pareto': 3}}, days=2)
    assert len(model.pareto_results) == 3
