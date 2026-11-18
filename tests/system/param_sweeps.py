"""
Parameter sweeps: each sweep varies one parameter and states the expected
direction of a result metric.

    python param_sweeps.py make  <cases.txt>      -> case file for run_cases.py
    python param_sweeps.py check [prefix]          -> evaluate _work/results/<prefix><case>.json

Metrics: 'a:<key>' annual result, 'cost'/'co2' = DEM cost module totals,
'obj' = optimisation objective (Calliope).
Relations: 'inc'/'dec' (strictly monotone in the listed order),
'eq' (all equal within 1e-6 relative), 'change' (not all equal).
"""
import json
import os
import sys

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from _common import ROOT, WORK, PYTHON, MASTER_DATA, run_env  # noqa: E402
I = f'{T}/inputs'
OPT = {'optimisation': {'enabled': True, 'solver_option_Threads': 4}}
FHR = {'scenarios': {'fossil_heater_retrofit': True}}
DS50 = {'scenarios': {'demand_side': True},
        'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050}}}

# (id, base config, parameter path, values, metric, relation)
SWEEPS = [
    # --- simulation: technology parameters ---
    ('sim_ob_eta', {}, 'oil_boiler.eta', [0.95, 0.85, 0.6], 'a:m_oil_yr', 'inc'),
    ('sim_gb_eta', {}, 'gas_boiler.eta', [0.95, 0.9, 0.6], 'a:m_gas_yr', 'inc'),
    ('sim_wb_eta', {}, 'wood_boiler.eta', [0.95, 0.8, 0.5], 'a:u_wd_wb_yr', 'inc'),
    ('sim_hp_cop_const', {'heat_pump': {'cop_mode': 'constant'}}, 'heat_pump.cop_constant_value', [2.0, 3.5, 5.0], 'a:u_e_hp_yr', 'dec'),
    ('sim_hp_qf_ashp_old', {}, 'heat_pump.quality_factor_ashp_old', [0.3, 0.4, 0.5], 'a:u_e_hp_yr', 'dec'),
    ('sim_hp_qf_gshp_new_fhr', FHR, 'heat_pump.quality_factor_gshp_new', [0.3, 0.48, 0.6], 'a:u_e_hp_yr', 'dec'),
    ('sim_pv_eta', {}, 'solar_pvrooftop.eta_overall', [0.15, 0.2185, 0.3], 'a:v_e_pvrooftop_yr', 'inc'),
    ('sim_st_eta', {}, 'solarthermal_rooftop.eta_overall', [0.5, 0.7, 0.9], 'a:v_h_solarthermalrooftop_yr', 'inc'),
    ('sim_hp_maint', {}, 'heat_pump.maintenance_cost', [10, 32, 60], 'cost', 'inc'),
    ('sim_dh_tariff', {}, 'district_heating.tariff_CHFpkWh', [0.08, 0.13, 0.2], 'cost', 'inc'),
    ('sim_dh_co2', {}, 'district_heating.co2_intensity', [0.05, 0.108, 0.2], 'co2', 'inc'),
    ('sim_grid_tariff', {}, 'grid_supply.constant_tariff_CHFpkWh', [0.2, 0.29, 0.4], 'cost', 'inc'),
    ('sim_grid_co2', {}, 'grid_supply.constant_co2_intensity', [0.05, 0.097, 0.2], 'co2', 'inc'),
    ('sim_grid_tariff_file', {}, 'grid_supply.tariff_mode', ['const', 'file'], 'cost', 'change'),
    # --- simulation: supply vs. duplicated tech-level fuel parameters ---
    ('sim_supply_oil_price', {}, 'supply.oil_price_CHFpl', [0.8, 1.0, 1.5], 'cost', 'inc'),
    ('sim_tech_oil_price', {}, 'oil_boiler.oil_price_CHFpl', [0.8, 1.0, 1.5], 'cost', 'inc'),
    ('sim_supply_gas_price', {}, 'supply.gas_price_CHFpkWh', [0.1, 0.13, 0.2], 'cost', 'inc'),
    ('sim_tech_gas_price', {}, 'gas_boiler.gas_price_CHFpkWh', [0.1, 0.13, 0.2], 'cost', 'inc'),
    ('sim_supply_hv_oil', {}, 'supply.hv_oil_MJpkg', [38.0, 42.9, 46.0], 'cost', 'dec'),
    ('sim_tech_hv_oil', {}, 'oil_boiler.hv_oil_MJpkg', [38.0, 42.9, 46.0], 'cost', 'dec'),
    ('sim_supply_wood_price', {}, 'supply.wood_price_CHFpkg_imported', [0.3, 0.5, 1.0], 'cost', 'inc'),
    ('sim_tech_wood_price', {}, 'wood_boiler.wood_price_CHFpkg', [0.3, 0.5, 1.0], 'cost', 'inc'),
    ('sim_supply_co2_oil', {}, 'supply.co2_content_oil', [0.2, 0.301, 0.4], 'co2', 'inc'),
    ('sim_supply_co2_gas', {}, 'supply.co2_content_gas', [0.15, 0.228, 0.3], 'co2', 'inc'),
    ('sim_supply_wood_import', {}, 'supply.wood_import', [True, False], 'a:m_wd_yr', 'change'),
    # --- simulation: scenarios ---
    ('sim_pv_factor', {'scenarios': {'pv_integration': True}}, 'pv_integration.potential_integration_factor.solar_pvrooftop', [[0.2]*4, [0.5]*4, [0.9]*4], 'a:v_e_pvrooftop_yr', 'inc'),
    ('sim_wind_factor', {'scenarios': {'wind_integration': True}}, 'wind_integration.potential_integration_factor', [0.2, 0.5, 0.9], 'a:v_e_wp_yr', 'inc'),
    ('sim_fhr_oil', FHR, 'fossil_heater_retrofit.oil_boiler_replacement_factor', [0.2, 0.5, 1.0], 'a:v_h_ob_yr', 'dec'),
    ('sim_fhr_gas', FHR, 'fossil_heater_retrofit.gas_boiler_replacement_factor', [0.2, 0.5, 1.0], 'a:v_h_gb_yr', 'dec'),
    ('sim_fhr_eh', FHR, 'fossil_heater_retrofit.electric_boiler_replacement_factor', [0.2, 0.5, 1.0], 'a:v_h_eh_yr', 'dec'),
    ('sim_bes_cap', {'scenarios': {'battery_energy_storage': True, 'pv_integration': True}}, 'battery_energy_storage_scenario.capacity_kWh', [1e3, 1e4, 1e5], 'a:v_e_bes_yr', 'inc'),
    ('sim_bes_eta', {'scenarios': {'battery_energy_storage': True, 'pv_integration': True}}, 'bes.eta_chg_dchg', [0.8, 0.95, 1.0], 'a:m_e_yr', 'dec'),
    ('sim_tes_cap', {'scenarios': {'thermal_energy_storage': True, 'pv_integration': True}, 'tes_decentralised': {'deployment': True}}, 'thermal_energy_storage_scenario.capacity_kWh', [1e3, 1e4, 1e5], 'a:v_h_tesdc_yr', 'inc'),
    ('sim_ev_factor', DS50, 'demand_side.ev_integration_factor', [25, 50, 100], 'a:d_e_ev_yr', 'inc'),
    ('sim_renov_rate', DS50, 'demand_side.constant_total_renovation_rate', [0.005, 0.018, 0.03], 'a:d_h_yr', 'dec'),
    ('sim_renov_scenario', {'scenarios': {'demand_side': True}, 'demand_side': {'simulation_year': {'type': 'future', 'future_year': 2050}, 'use_constant_total_renovation_rate': False}}, 'demand_side.renovation_scenario', ['renovation_low', 'renovation_base', 'renovation_high'], 'a:d_h_yr', 'dec'),
    ('sim_future_year', {'scenarios': {'demand_side': True}, 'demand_side': {'simulation_year': {'type': 'future'}, 'total_renovation': False, 'heat_generator_renovation': False}}, 'demand_side.simulation_year.future_year', [2030, 2040, 2050], 'a:d_h_yr', 'change'),
    ('sim_nuclear_year', {'scenarios': {'nuclear_phaseout': True, 'demand_side': True}, 'demand_side': {'simulation_year': {'type': 'future'}}}, 'demand_side.simulation_year.future_year', [2030, 2040, 2050], 'a:m_e_ch_nuclear_yr', 'dec'),
    ('sim_interest', {}, 'solarthermal_rooftop.interest_rate', [0.0, 0.025, 0.08], 'cost', 'inc'),
    # --- optimisation ---
    ('opt_bigM', OPT, 'optimisation.bigM_value', [1e5, 1e6, 1e7], 'obj', 'eq'),
    ('opt_hp_capex', OPT, 'heat_pump.capex', [1000, 3018, 8000], 'a:v_h_hp_yr', 'dec'),
    ('opt_grid_tariff', OPT, 'grid_supply.constant_tariff_CHFpkWh', [0.15, 0.29, 0.6], 'a:m_e_yr', 'dec'),
    ('opt_pv_capex', OPT, 'solar_pvrooftop.base_capex', [0, 2079, 6000], 'a:v_e_pvrooftop_yr', 'dec'),
    ('opt_pvalpine_capex', {**OPT, 'simulation': {'district_number': 3851}}, 'solar_pvalpine.base_capex', [0, 4370], 'a:v_e_pvalpine_yr', 'dec'),
    ('opt_wind_capex', OPT, 'wind_power.capex_CHFpkWp', [500, 2190, 8000], 'a:v_e_wp_yr', 'dec'),
    ('opt_wind_max_sys', OPT, 'wind_power.kWp_max_systemwide', [0, 2000, 'inf'], 'a:v_e_wp_yr', 'inc'),
    ('opt_hp_kWmax', OPT, 'heat_pump.kW_th_max', [5000, 20000, 'inf'], 'a:v_h_hp_yr', 'inc'),
    ('opt_dh_max', {**OPT, 'district_heating': {'demand_share_type': 'max'}}, 'district_heating.demand_share_val', [0.0, 0.05, 0.1], 'a:v_h_dh_yr', 'inc'),
    ('opt_eh_fixed', {**OPT, 'electric_heater': {'fixed_demand_share': True}}, 'electric_heater.fixed_demand_share_val', [0.0, 0.02, 0.05], 'a:v_h_eh_yr', 'inc'),
    ('opt_gb_fixed', {**OPT, 'gas_boiler': {'fixed_demand_share': True}}, 'gas_boiler.fixed_demand_share_val', [0.0, 0.2, 0.4], 'a:v_h_gb_yr', 'inc'),
    ('opt_wb_fixed', {**OPT, 'wood_boiler': {'fixed_demand_share': True}}, 'wood_boiler.fixed_demand_share_val', [0.0, 0.02, 0.05], 'a:v_h_wb_yr', 'inc'),
    ('opt_co2_weight', OPT, 'optimisation.objective_co2', [0.0, 1.0, 10.0], 'co2', 'dec'),
    ('opt_bes_capex', OPT, 'bes.capex', [0, 586, 5000], 'a:v_e_bes_yr', 'dec'),
    ('opt_chp_force', {**OPT, 'chp_gt': {'deployment': True, 'force_cap_max': True}, 'district_heating': {'heat_sources': {'chp_gt': True}}}, 'chp_gt.kW_el_max', [100, 500, 1000], 'a:v_e_chpgt_yr', 'inc'),
    ('opt_gtcp_min_use', {**OPT, 'gas_turbine_cp': {'deployment': True, 'force_cap_max': True, 'kW_el_max': 500}, 'steam_turbine': {'deployment': True}, 'district_heating': {'heat_sources': {'steam_turbine': True}}}, 'gas_turbine_cp.cap_min_use', [0.0, 0.5, 1.0], 'a:v_e_gtcp_yr', 'inc'),
    ('opt_ev_flex', {**OPT, 'scenarios': {'demand_side': True}}, 'demand_side.ev_flexibility', [False, True], 'obj', 'dec'),
    ('opt_drflex_dT', {**OPT, 'scenarios': {'demand_side': True}, 'demand_side': {'dr_flexibility_building_inertia': True}}, 'demand_side.dr_flexibility_building_inertia_dT', [0.5, 2.0, 4.0], 'obj', 'dec'),
    ('opt_drflex_rate', {**OPT, 'scenarios': {'demand_side': True}, 'demand_side': {'dr_flexibility_building_inertia': True, 'dr_flexibility_building_inertia_max_overheating_rate': {'max_virtual_storage_loss_rate': False}}}, 'demand_side.dr_flexibility_building_inertia_max_overheating_rate.max_heating_system_cap', [False, True], 'obj', 'change'),
    ('opt_oil_import', {**OPT, 'heat_pump': {'capex': 50000}}, 'supply.oil_import', [True, False], 'a:m_oil_yr', 'dec'),
    ('opt_gas_import', {**OPT, 'heat_pump': {'capex': 50000}}, 'supply.gas_import', [True, False], 'a:m_gas_yr', 'dec'),
    ('opt_wood_import', {**OPT, 'heat_pump': {'capex': 50000}}, 'supply.wood_import', [True, False], 'a:m_wd_yr', 'dec'),
    ('opt_tes_initial', {**OPT, 'tes_decentralised': {'deployment': True, 'optimized_initial_charge': False}}, 'tes_decentralised.initial_charge', [0.0, 0.5], 'obj', 'change'),
    ('opt_hpcp_cop_mode', {**OPT, 'heat_pump_cp': {'deployment': True, 'capital_cost': 100}, 'heat_pump': {'capex': 20000}, 'district_heating': {'heat_sources': {'heat_pump_cp': True}}}, 'heat_pump_cp.cop_mode', ['constant', 'temperature_based', 'from_file', 'from_file_adjusted_to_spf'], 'a:u_e_hpcp_yr', 'change'),
    ('opt_interest', OPT, 'interest_rate_all', [0.0, 0.025, 0.08], 'obj', 'inc'),
]


def set_path(cfg, path, value):
    keys = path.split('.')
    node = cfg
    for k in keys[:-1]:
        node = node.setdefault(k, {})
    node[keys[-1]] = value


def make(out):
    with open(out, 'w') as f:
        for sid, base, path, values, metric, rel in SWEEPS:
            for i, v in enumerate(values):
                cfg = json.loads(json.dumps(base))
                cfg.setdefault('simulation', {})['save_results'] = False
                if path == 'interest_rate_all':
                    for tech in ['heat_pump', 'electric_heater', 'oil_boiler', 'gas_boiler', 'wood_boiler',
                                 'district_heating', 'solar_pvrooftop', 'solarthermal_rooftop', 'wind_power',
                                 'hydro_power', 'bes']:
                        set_path(cfg, f'{tech}.interest_rate', v)
                else:
                    set_path(cfg, path, v)
                if path == 'grid_supply.tariff_mode' and v == 'file':
                    set_path(cfg, 'grid_supply.tariff_timeseries_filepath', f'{I}/tariff.feather')
                if path == 'heat_pump_cp.cop_mode' and v.startswith('from_file'):
                    set_path(cfg, 'heat_pump_cp.cop_timeseries_file_path', f'{I}/cop.feather')
                f.write(f"sw_{sid}__{i}\t{json.dumps(cfg)}\t\n")


def metric_value(d, metric):
    c = d.get('costs') or {}
    k = c['Kostenmodul']['cost_overview'] if 'Kostenmodul' in c else c
    if metric == 'obj':
        return (c.get('objective') or {}).get('total')
    if metric == 'cost':
        return (k.get('monetary') or {}).get('total')
    if metric == 'co2':
        return k.get('co2')
    return d.get('annual', {}).get(metric[2:])


def check(prefix=''):
    import math
    rows = []
    for sid, base, path, values, metric, rel in SWEEPS:
        vals, errs = [], []
        for i in range(len(values)):
            try:
                d = json.load(open(f'{WORK}/results/{prefix}sw_{sid}__{i}.json'))
            except FileNotFoundError:
                errs.append(f'{i}: missing'); vals.append(None); continue
            if d['status'] != 'OK':
                errs.append(f"{values[i]}: {d.get('error', '')[:90]}"); vals.append(None); continue
            vals.append(metric_value(d, metric))
        ok_vals = [v for v in vals if v is not None]
        status = 'ERROR' if errs else 'OK'
        if not errs:
            if any(isinstance(v, float) and math.isnan(v) for v in ok_vals):
                status = 'NaN'
            else:
                eq = lambda a, b: abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))
                pairs = list(zip(ok_vals, ok_vals[1:]))
                if rel == 'inc':
                    good = all(b > a and not eq(a, b) for a, b in pairs)
                elif rel == 'dec':
                    good = all(b < a and not eq(a, b) for a, b in pairs)
                elif rel == 'eq':
                    good = all(eq(a, b) for a, b in pairs)
                else:
                    good = not all(eq(a, b) for a, b in pairs)
                status = 'OK' if good else 'UNEXPECTED'
        fmt = lambda v: 'None' if v is None else f'{v:.6g}'
        rows.append((status, sid, path, rel, metric, ', '.join(fmt(v) for v in vals), '; '.join(errs)))
    for r in rows:
        print(f'{r[0]:10s} {r[1]:24s} {r[2]:60s} {r[3]:6s} {r[4]:28s} [{r[5]}] {r[6]}')
    print({s: sum(r[0] == s for r in rows) for s in ['OK', 'UNEXPECTED', 'ERROR', 'NaN']})


if __name__ == '__main__':
    if sys.argv[1] == 'make':
        make(sys.argv[2])
    else:
        check(sys.argv[2] if len(sys.argv) > 2 else '')
