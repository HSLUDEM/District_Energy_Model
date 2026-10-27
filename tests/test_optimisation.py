"""Optimisation runs (Gurobi)."""
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
