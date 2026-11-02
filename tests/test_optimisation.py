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


def _tes_site(**kw):
    site = {'name': 'PTES_1', 'exclusion_group': None, 'force_deployment': True, 'color': [122, 73, 14],
            'type': 'simple_fully_stratified_three_temperature_levels',
            'rel_size_t_levels': {'ltlt': 0.6, 'htlt': 0.2, 'htht': 0.2},
            'capacity_kWh_min': 20000, 'capacity_kWh_max': 60000, 'capex_base': 600000, 'capex_per_kWh': 2.0,
            'maintenance_cost_base': 1000, 'maintenance_cost_per_kWh': 0.05,
            'storage_loss_rate': {'ltlt': 0.001, 'htlt': 0.001, 'htht': 0.002},
            'eta_chg_dchg': {'ltlt': 0.9, 'htlt': 0.9, 'htht': 0.9}, 'lifetime': 30.0, 'interest_rate': 0.025,
            'chg_dchg_per_cap_max': 0.1, 'connected_techs': {'lt': ['heatlt'], 'ht': ['obcp', 'dhimp']}}
    return site | kw


def _tes_cfg(*sites):
    return {'tes_sites': {'deployment': True, 'list_generation_mode': 'externally_controlled',
                          'generation_function_parameters': {'list_of_tes_options': list(sites)}},
            'oil_boiler_cp': {'deployment': True}, 'district_heating': {'heat_sources': {'oil_boiler_cp': True}}}


def test_tes_site_fixed_costs_independent_of_energy_scaling(run_dem):
    cfg = _tes_cfg(_tes_site())
    obj = [run_dem(cfg | {'optimisation': OPT | {'calliope_energy_scaling_factor': s}}, days=2).total_cost()['objective']['total']
           for s in [1, 1000]]
    assert obj[1] == pytest.approx(obj[0], rel=1e-6)


def test_tes_site_base_costs_only_with_minimum_size(run_dem, tmp_path):
    # capex_base and maintenance_cost_base only apply if capacity_kWh_min > 0, in the optimisation and the cost module
    import numpy as np
    import pandas as pd
    hours = np.arange(8760)
    pd.DataFrame({'v': 3000*(hours % 24 < 8)}).to_feather(tmp_path / 'whlt.feather')  # night-time waste heat, worth storing
    site = _tes_site(force_deployment=False, capacity_kWh_min=0, capacity_kWh_max=1e5, capex_per_kWh=0.01)
    cfg = _tes_cfg(site)
    cfg['waste_heat_low_temperature'] = {'deployment': True, 'timeseries_file_path': str(tmp_path / 'whlt.feather')}
    cfg['heat_pump_cp_lt'] = {'deployment': True}
    cfg['district_heating']['heat_sources']['heat_pump_cp_lt'] = True
    model = run_dem(cfg | {'optimisation': OPT}, days=2)
    assert sum(model.tech_instances['tes_sites'].get_output_max()) > 0
    tes_costs = model.total_cost()['Kostenmodul']['monetary_breakdown']['tes_sites']
    assert tes_costs['annualized_capex'] < 0.01 * 600000 * 2 / 365
    assert cost_overview(model)['monetary']['total'] == pytest.approx(model.total_cost()['objective']['total'], rel=1e-6, abs=1)


@pytest.mark.parametrize('sites, match', [
    ([_tes_site(), _tes_site(force_deployment=False)], 'unique'),
    ([_tes_site(capacity_kWh_min=60000, capacity_kWh_max=20000)], 'capacity_kWh_min'),
    ([_tes_site(rel_size_t_levels={'ltlt': 0.0, 'htlt': 0.0, 'htht': 0.0})], 'rel_size_t_levels'),
    ([_tes_site(rel_size_t_levels={'ltlt': 1.2, 'htlt': -0.2, 'htht': 0.0})], 'rel_size_t_levels'),
    ([_tes_site(rel_size_t_levels={'ltlt': 0.6, 'htlt': 0.6, 'htht': 0.6})], 'add up to 1'),
], ids=['duplicate-names', 'min-above-max', 'no-level', 'negative-level', 'shares-not-adding-up-to-1'])
def test_invalid_tes_site_definitions_raise(run_dem, sites, match):
    with pytest.raises(ValueError, match=match):
        run_dem(_tes_cfg(*sites) | {'optimisation': OPT}, days=2)


def test_tes_site_without_connected_lt_techs(run_dem):
    site = _tes_site(connected_techs={'lt': [], 'ht': ['obcp', 'dhimp']})
    model = run_dem(_tes_cfg(site) | {'optimisation': OPT}, days=2)
    assert sum(model.tech_instances['tes_sites'].get_output_max()) >= 20000 - 1e-3
    assert model.annual_results()['d_h_unmet_yr'] == pytest.approx(0, abs=1)


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


def test_building_inertia_flexibility_independent_of_energy_scaling(run_dem):
    cfg = {'scenarios': {'demand_side': True}, 'demand_side': {'dr_flexibility_building_inertia': True}}
    obj = [run_dem(cfg | {'optimisation': OPT | {'solver_option_FeasibilityTol': 1e-6,
                                                 'calliope_energy_scaling_factor': s}}, days=2).total_cost()['objective']['total']
           for s in [1, 0.5]]
    assert obj[1] == pytest.approx(obj[0], rel=1e-4)


def test_direct_wind_export_is_not_a_constraint_violation(run_dem):
    model = run_dem({'wind_power': {'export_subsidy': 0.1}, 'optimisation': OPT}, days=3)
    yr = model.annual_results()
    assert yr['v_e_wp_exp_yr'] > 0
    assert yr['v_e_wp_cons_yr'] + yr['v_e_wp_exp_yr'] == pytest.approx(yr['v_e_wp_yr'])


@pytest.mark.parametrize('scaling', [0.1, 10])
def test_hydro_power_independent_of_energy_scaling(run_dem, scaling):
    # Muotathal (1367): hydro power
    model = run_dem({'simulation': {'district_number': 1367},
                     'optimisation': OPT | {'solver_option_FeasibilityTol': 1e-6,
                                            'calliope_energy_scaling_factor': scaling}}, days=2)
    objective = model.total_cost()['objective']['total']
    assert cost_overview(model)['monetary']['total'] == pytest.approx(objective, rel=1e-4, abs=10)


def test_tes_site_ltlt_can_be_charged_via_the_htlt_carrier(run_dem, tmp_path, monkeypatch):
    # Close the alternative path ht techs -> htht carrier -> ltlt, so that ht heat can only reach the ltlt level
    # through the htlt carrier (conversion htlt -> ltlt).
    import numpy as np
    import pandas as pd
    from district_energy_model import dem_calliope_cc
    hours = np.arange(8760)
    pd.DataFrame({'v': 0.15 + 0.25*((hours % 24 >= 8) & (hours % 24 < 20))}).to_feather(tmp_path / 'tariff.feather')
    site = _tes_site(name='S1', rel_size_t_levels={'ltlt': 0.5, 'htlt': 0.5, 'htht': 0.0},
                     capacity_kWh_max=20000, capex_base=0, capex_per_kWh=0.0, maintenance_cost_base=0,
                     maintenance_cost_per_kWh=0, eta_chg_dchg={'ltlt': 0.95, 'htlt': 0.95, 'htht': 0.95},
                     chg_dchg_per_cap_max=0.2, connected_techs={'lt': ['heatlt'], 'ht': ['obcp', 'hpcp']})
    cfg = _tes_cfg(site)
    cfg['heat_pump_cp_lt'] = {'deployment': True}
    cfg['heat_pump_cp'] = {'instance_1': {'deployment': True}}
    cfg['district_heating']['heat_sources'] |= {'heat_pump_cp': True, 'heat_pump_cp_lt': True}
    cfg['grid_supply'] = {'tariff_mode': 'file', 'tariff_timeseries_filepath': str(tmp_path / 'tariff.feather')}
    cfg['optimisation'] = OPT

    def ltlt_charging():
        return run_dem(cfg, days=7).hourly_results()['u_hltlt_tes_site_S1'].sum()

    open_path = ltlt_charging()
    orig = dem_calliope_cc.tes_sites_charge_constraints

    def charge_constraints(model, ts_len, sites_list):
        model = orig(model, ts_len, sites_list)
        def close_rule(backend_model, timestep):
            return backend_model.carrier_prod['X1::conv_S1_htht_to_S1_ltlt::heat_tes_site_S1_ltlt', timestep] == 0
        model.backend.add_constraint('test_close_htht_to_ltlt', ['timesteps'], close_rule)
        return model

    monkeypatch.setattr(dem_calliope_cc, 'tes_sites_charge_constraints', charge_constraints)
    assert open_path > 10000
    assert ltlt_charging() > 0.8 * open_path


# Biomass gas: gas import off and a small fixed share of decentral gas boilers force local gas production;
# biomass heat (by-product of some techs) goes to district heating.
_BIOMASS_GAS = {'supply': {'gas_import': False}, 'gas_boiler': {'fixed_demand_share': True, 'fixed_demand_share_val': 0.005},
                'district_heating': {'heat_sources': {'biomass': True}}}


@pytest.mark.parametrize('tech', ['wood_gasification_upgrade', 'anaerobic_digestion_upgrade_hydrogen'])
def test_cost_module_sizes_gas_upgrading_on_gas_output(run_dem, tech):
    cfg = _BIOMASS_GAS | {tech: {'deployment': True}, 'optimisation': OPT}
    if 'hydrogen' in tech:
        cfg['hydrogen_production'] = {'deployment': True}
    model = run_dem(cfg, days=2)
    assert model.annual_results()['m_gas_yr'] == pytest.approx(0, abs=1e-3)
    assert cost_overview(model)['monetary']['total'] == pytest.approx(model.total_cost()['objective']['total'], rel=1e-6, abs=1)


def test_cost_module_includes_om_cost_of_gasification(run_dem):
    cfg = _BIOMASS_GAS | {'hydrothermal_gasification': {'deployment': True, 'om_cost': 0.05}, 'optimisation': OPT}
    model = run_dem(cfg, days=2)
    assert model.annual_results()['u_wet_bm_hg_yr'] > 1000
    assert cost_overview(model)['monetary']['total'] == pytest.approx(model.total_cost()['objective']['total'], rel=1e-6, abs=1)


def test_cost_module_includes_hydrogen_production_capex(run_dem):
    cfg = _BIOMASS_GAS | {'anaerobic_digestion_upgrade_hydrogen': {'deployment': True},
                          'hydrogen_production': {'deployment': True}, 'optimisation': OPT}
    model = run_dem(cfg, days=2)
    hydp = model.tech_instances['hydrogen_production']
    cap = hydp.get_v_hyd().max()
    assert cap > 10
    r, n = hydp._interest_rate, hydp._lifetime
    expected = 4090 * cap * r * (1 + r)**n / ((1 + r)**n - 1) * 2 / 365
    costs = model.total_cost()['Kostenmodul']['monetary_breakdown']['hydrogen_production']
    assert costs['annualized_capex'] == pytest.approx(expected, rel=1e-6)


def test_biomass_heat_without_sink_is_curtailed_with_warning(run_dem, capfd):
    # Gas demand forces wood gasification; its heat by-product has no sink (biomass is no district heating source)
    cfg = {'supply': {'gas_import': False}, 'gas_boiler': {'fixed_demand_share': True, 'fixed_demand_share_val': 0.005},
           'wood_gasification_upgrade': {'deployment': True}, 'optimisation': OPT}
    model = run_dem(cfg, days=2, quiet=False)
    h = model.hourly_results()
    assert h['v_h_wgu'].sum() > 100
    assert h['v_h_bm_curt'].sum() == pytest.approx(h['v_h_wgu'].sum(), rel=1e-6)
    assert h['v_h_bm'].sum() == pytest.approx(0, abs=1e-3)
    assert 'curtailed' in capfd.readouterr().out


def _dh_only(*techs, share=0.1, **kw):
    """District heating supplies a fixed share of the heat demand with the given central plants as only source."""
    cfg = {t: {'deployment': True} for t in techs}
    dh_sources = [t for t in techs if t not in ('gas_turbine_cp', 'wood_boiler_sg')]
    cfg['district_heating'] = {'demand_share_type': 'fixed', 'demand_share_val': share,
                               'heat_sources': {'import': False} | {t: True for t in dh_sources}}
    for k, v in kw.items():
        cfg[k] = cfg.get(k, {}) | v
    return cfg | {'optimisation': OPT}


@pytest.mark.parametrize('techs, key, waste', [(('chp_gt',), 'chp_gt', 'v_h_chpgt_waste'),
                                               (('wood_boiler_sg', 'steam_turbine'), 'steam_turbine', 'v_h_st_waste')])
def test_central_plant_without_heat_export(run_dem, techs, key, waste):
    model = run_dem(_dh_only(*techs, **{key: {'allow_heat_export': False}}), days=2)
    assert model.hourly_results()[waste].sum() == pytest.approx(0, abs=1e-6)
    assert model.annual_results()['d_h_unmet_yr'] == pytest.approx(0, abs=1)


def test_deep_geothermal_capacity_limit_is_kw_th_max_not_capex(run_dem):
    h = run_dem(_dh_only('deep_geothermal', 'gas_boiler_cp', share=0.5, deep_geothermal={'kW_th_max': 1000}), days=2).hourly_results()
    assert h['v_h_dgt'].max() == pytest.approx(1000, rel=1e-6)
    # A low capex must not limit the capacity (it was used as energy_cap_max):
    h = run_dem(_dh_only('deep_geothermal', 'gas_boiler_cp', share=0.5, deep_geothermal={'capex': 500.0}), days=2).hourly_results()
    assert h['v_h_dgt'].max() > 1000


def test_optimisation_with_all_central_plants_runs(run_dem):
    # Gurobi returns -0.05 kWh grid import in one hour (default FeasibilityTol), which failed with 'Not all values are >= 0 in m_e'
    techs = ('oil_boiler_cp', 'gas_boiler_cp', 'wood_boiler_cp', 'electric_heater_cp', 'chp_gt', 'gas_turbine_cp',
             'steam_turbine', 'wood_boiler_sg', 'waste_to_energy', 'deep_geothermal')
    model = run_dem(_dh_only(*techs, share=0.3, supply={'annual_msw_supply': 1e7}), days=7)
    assert model.hourly_results()['m_e'].min() >= 0


@pytest.mark.parametrize('scaling', [0.1, 10])
def test_chp_forced_capacity_independent_of_energy_scaling(run_dem, scaling):
    cfg = _dh_only('chp_gt', 'gas_boiler_cp', chp_gt={'kW_el_max': 100, 'force_cap_max': True})
    ref = run_dem(cfg, days=2)
    cfg['optimisation'] = OPT | {'calliope_energy_scaling_factor': scaling, 'solver_option_FeasibilityTol': 1e-6}
    model = run_dem(cfg, days=2)
    assert model.hourly_results()['v_e_chpgt'].max() <= 100 + 1e-3
    assert model.total_cost()['objective']['total'] == pytest.approx(ref.total_cost()['objective']['total'], rel=1e-4)


def test_cost_module_uses_forced_capacity_of_central_plants(run_dem):
    # Steam turbine forced to 300 kW, running at 240 kW (cap_min_use 0.8)
    cfg = _dh_only('wood_boiler_sg', 'steam_turbine', 'gas_boiler_cp',
                   steam_turbine={'kW_el_max': 300, 'force_cap_max': True, 'cap_min_use': 0.8})
    model = run_dem(cfg, days=2)
    assert model.hourly_results()['v_e_st'].max() < 300
    assert cost_overview(model)['monetary']['total'] == pytest.approx(model.total_cost()['objective']['total'], rel=1e-6, abs=1)


@pytest.mark.parametrize('tech', ['chp_gt', 'gas_turbine_cp', 'steam_turbine', 'waste_to_energy', 'wood_boiler_sg'])
def test_force_cap_max_requires_finite_capacity(run_dem, tech):
    techs = (tech, 'steam_turbine') if tech in ('gas_turbine_cp', 'wood_boiler_sg') else (tech,)
    with pytest.raises(ValueError, match='force_cap_max requires'):
        run_dem(_dh_only(*techs, **{tech: {'force_cap_max': True}}), days=2)


def test_alpine_pv_respects_kwp_max(run_dem):
    # Davos has a large alpine PV potential; with low capex the whole potential would be built
    model = run_dem({'simulation': {'district_number': 3851}, 'solar_pvalpine': {'base_capex': 100, 'kWp_max': 1000},
                     'optimisation': OPT}, days=2)
    assert 0 < model.hourly_results()['v_e_pvalpine'].max() <= 1000 + 1e-3


@pytest.mark.parametrize('key, limit, col', [('solar_pvrooftop', 'kWp_max', 'v_e_pvrooftop'),
                                             ('solarthermal_rooftop', 'kW_th_max', 'v_h_solarthermalrooftop')])
def test_rooftop_solar_capacity_limit(run_dem, key, limit, col):
    # A limit of 0 allows no new capacity: only the existing installations produce
    cheap = {'base_capex': 10}
    limited = run_dem({key: cheap | {limit: 0}, 'optimisation': OPT}, days=2).hourly_results()[col]
    existing = run_dem({key: cheap | {'only_use_installed': True}, 'optimisation': OPT}, days=2).hourly_results()[col]
    assert limited.sum() == pytest.approx(existing.sum(), rel=1e-6, abs=1e-3)


def test_cost_module_co2_includes_deep_geothermal(run_dem):
    model = run_dem(_dh_only('deep_geothermal', deep_geothermal={'co2_intensity': 0.05}), days=2)
    assert model.annual_results()['v_co2_dgt_yr'] > 0
    co2 = cost_overview(model)['co2']
    assert co2 == pytest.approx(model.annual_results()['v_co2_tot_yr'], rel=1e-6)
    assert co2 == pytest.approx(model.total_cost()['co2']['total'], rel=1e-6)


def test_grid_supply_kw_max_float_inf(run_dem):
    model = run_dem({'grid_supply': {'kW_max': float('inf')}, 'optimisation': OPT}, days=1)
    assert model.annual_results()['m_e_yr'] > 0


def test_storage_cumsum_plot_shows_flows(run_dem, tmp_path):
    # Storage with losses: the cumulative charged/discharged curves are the flows, not the level changes
    from test_simulation import _plot_traces
    model = run_dem({'simulation': {'generate_plots': True, 'save_results': True},
                     'tes_decentralised': {'deployment': True}, 'bes': {'deployment': True},
                     'optimisation': OPT}, days=2)
    cum = {t['name']: t['y'][-1] for t in _plot_traces(f'{model.results_path}/tes_and_bes_cumsum_hourly.html')}
    df = model.hourly_results()
    for q, u, v in [('q_h_tesdc', 'u_h_tesdc', 'v_h_tesdc'), ('q_e_bes', 'u_e_bes', 'v_e_bes')]:
        assert df[u].sum() > 1000 and df[v].sum() > 1000
        assert cum[f'{q} charged'] == pytest.approx(df[u].sum() / 1000, rel=1e-6)
        assert cum[f'{q} discharged'] == pytest.approx(df[v].sum() / 1000, rel=1e-6)


@pytest.mark.parametrize('scaling', [1000, 10000])
def test_feasibility_tol_with_large_energy_scaling(run_dem, scaling):
    # Default FeasibilityTol 1e-6 / scaling must stay within Gurobi's range (minimum 1e-9)
    model = run_dem({'optimisation': OPT | {'calliope_energy_scaling_factor': scaling}}, days=1)
    assert model.annual_results()['m_e_yr'] > 0
