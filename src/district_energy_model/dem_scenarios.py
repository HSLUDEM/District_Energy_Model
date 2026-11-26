# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 07:19:20 2023

@author: UeliSchilt
"""

"""
Functions to create scenarios for the district energy model.

"""

import copy

import numpy as np
import warnings

from district_energy_model import dem_helper
from district_energy_model import dem_energy_balance as dem_eb
from district_energy_model import dem_constants as C

# pd.options.mode.chained_assignment = None

def scenario_heater_electric_to_hp(energy_demand, scen_techs, tech_instances):    
    """
    Function to adjust energy system balance in case of direct electric heater replacement
    by heat pumps.
    
    Requirements:
        - scen_techs['heat_pump']['deployment'] == True
    
    Parameters
    ----------
    Returns
    -------
    n/a
    """
    tech_heat_pump = tech_instances['heat_pump']
    tech_grid_supply = tech_instances['grid_supply']
    tech_electric_heater = tech_instances['electric_heater']

    replacement_factor = scen_techs['fossil_heater_retrofit']['electric_boiler_replacement_factor']

    #--------------------------------------------------------------------------
    # Adjust energy accounting of heating technologies:        
    v_h_eh = tech_electric_heater.get_v_h()
    u_e_eh = tech_electric_heater.get_u_e()

    tmp_v_h_shifted = v_h_eh*replacement_factor # [kWh] heat generation shifted from electric heater to heat pump
    tmp_u_e_shifted = u_e_eh*replacement_factor # [kWh] electricity consumption reduced at electric heater

    # Update electric heater:
    v_h_eh_updated = v_h_eh - tmp_v_h_shifted
    tech_electric_heater.update_v_h(v_h_eh_updated)
    
    # Update heat pump:
    v_h_hp = tech_heat_pump.get_v_h()
    u_e_hp = tech_heat_pump.get_u_e()
    v_h_hp_updated = v_h_hp + tmp_v_h_shifted
    tech_heat_pump.update_v_h(v_h_hp_updated)
    # Apply the same replacement to the full-year reference, which is kept
    # separately from the shortened and later storage-modified HP time series.
    energy_demand.transfer_annual_heat_to_hp('electric_heater', replacement_factor)
    u_e_hp_updated = tech_heat_pump.get_u_e()
    tmp_u_e_additional = u_e_hp_updated - u_e_hp - tmp_u_e_shifted

    #--------------------------------------------------------------------------
    # Update total electricity demand:

    tmp_d_e = energy_demand.get_d_e() + tmp_u_e_additional
    energy_demand.update_d_e(tmp_d_e)
    
    tmp_d_e_h = energy_demand.get_d_e_h() + tmp_u_e_additional
    energy_demand.update_d_e_h(tmp_d_e_h)
    
    #--------------------------------------------------------------------------
    # Update local electricity mix:
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances) #ACHTUNG ACHTUNG ACHTUNG, HIER KÖNNTEN FEHLER SEIN!
    tech_grid_supply.update_m_e(tech_grid_supply.get_m_e()) #ACHTUNG ACHTUNG ACHTUNG, HIER KÖNNTEN FEHLER SEIN
    tech_grid_supply.compute_m_e_cbimport()
    
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply) 
    
    del tmp_v_h_shifted
    del tmp_u_e_additional


def scenario_heater_oil_to_hp(energy_demand, scen_techs, tech_instances):    
    """
    Function to adjust energy system balance in case of oil boiler replacement
    by heat pumps.
    
    Requirements:
        - scen_techs['heat_pump']['deployment'] == True
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    tech_oil_boiler : instance of OilBoiler class.
        Instance of oil boiler
    tech_heat_pump : instance of HeatPump class.
        Instance of heat pump
    tech_solar_pv : instance of SolarPV class
        Instance of solar pv.
    tech_wind_power: instance of WindPower class
        Instance of wind power.
    tech_biomass: instance of Biomass class.
        Instance of biomass.
    tech_grid_supply : instance of GridSupply class
        Instance of grid supply.

    Returns
    -------
    n/a
    """
    tech_heat_pump = tech_instances['heat_pump']
    tech_grid_supply = tech_instances['grid_supply']
    tech_oil_boiler = tech_instances['oil_boiler']

    replacement_factor = scen_techs['fossil_heater_retrofit']['oil_boiler_replacement_factor']

    #--------------------------------------------------------------------------
    # Adjust energy accounting of heating technologies:        
    v_h_ob = tech_oil_boiler.get_v_h()
        
    tmp_v_h_shifted = v_h_ob*replacement_factor # [kWh] heat generation shifted from oil boiler to heat pump
    
    # Update oil boiler:
    v_h_ob_updated = v_h_ob - tmp_v_h_shifted
    tech_oil_boiler.update_v_h(v_h_ob_updated)
    
    # Update heat pump:
    v_h_hp = tech_heat_pump.get_v_h()
    u_e_hp = tech_heat_pump.get_u_e()
    v_h_hp_updated = v_h_hp + tmp_v_h_shifted
    tech_heat_pump.update_v_h(v_h_hp_updated)
    # Keep the annual fleet reference consistent with oil-to-HP replacement.
    energy_demand.transfer_annual_heat_to_hp('oil_boiler', replacement_factor)
    u_e_hp_updated = tech_heat_pump.get_u_e()
    tmp_u_e_additional = u_e_hp_updated - u_e_hp

    #--------------------------------------------------------------------------
    # Update total electricity demand:
    tmp_d_e = energy_demand.get_d_e() + tmp_u_e_additional
    energy_demand.update_d_e(tmp_d_e)
    
    tmp_d_e_h = energy_demand.get_d_e_h() + tmp_u_e_additional
    energy_demand.update_d_e_h(tmp_d_e_h)
    
    #--------------------------------------------------------------------------
    # Update local electricity mix:
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances)
    tech_grid_supply.update_m_e(tech_grid_supply.get_m_e())
    
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply) 
    
    del tmp_v_h_shifted
    del tmp_u_e_additional
    
    
def scenario_heater_gas_to_hp(energy_demand, scen_techs, tech_instances):    
    """
    Function to adjust energy system balance in case of gas boiler replacement
    by heat pumps.
    
    Requirements:
        - scen_techs['heat_pump']['deployment'] == True
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dataframe with resulting hourly values
    tech_gas_boiler : instance of GasBoiler class
        Instance of gas boiler.
    tech_heat_pump : instance of HeatPump class.
        Instance of heat pump.
    tech_solar_pv : instance of SolarPV class
        Instance of solar pv.
    tech_wind_power: instance of WindPower class
        Instance of wind power.
    tech_biomass: instance of Biomass class
        Instance of biomass.
    tech_grid_supply : instance of GridSupply class
        Instance of grid supply.

    Returns
    -------
    n/a
    """
    
    tech_heat_pump = tech_instances['heat_pump']
    tech_grid_supply = tech_instances['grid_supply']
    tech_gas_boiler = tech_instances['gas_boiler']

    replacement_factor = scen_techs['fossil_heater_retrofit']['gas_boiler_replacement_factor']


    #--------------------------------------------------------------------------
    # Adjust energy accounting of heating technologies:        
    v_h_gb = tech_gas_boiler.get_v_h()        
    tmp_v_h_shifted = v_h_gb*replacement_factor # [kWh] heat generation shifted from oil boiler to heat pump
    
    # Update oil boiler:
    v_h_gb_updated = v_h_gb - tmp_v_h_shifted
    tech_gas_boiler.update_v_h(v_h_gb_updated)
    
    # Update heat pump:
    v_h_hp = tech_heat_pump.get_v_h()
    u_e_hp = tech_heat_pump.get_u_e()
    v_h_hp_updated = v_h_hp + tmp_v_h_shifted
    tech_heat_pump.update_v_h(v_h_hp_updated)
    # Keep the annual fleet reference consistent with gas-to-HP replacement.
    energy_demand.transfer_annual_heat_to_hp('gas_boiler', replacement_factor)
    u_e_hp_updated = tech_heat_pump.get_u_e()
    tmp_u_e_additional = u_e_hp_updated - u_e_hp
    
    #--------------------------------------------------------------------------
    # Update total electricity demand:    
    tmp_d_e = energy_demand.get_d_e() + tmp_u_e_additional
    energy_demand.update_d_e(tmp_d_e)
    
    tmp_d_e_h = energy_demand.get_d_e_h() + tmp_u_e_additional
    energy_demand.update_d_e_h(tmp_d_e_h)
    
    #--------------------------------------------------------------------------
    # Update local electricity mix:
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances)
    tech_grid_supply.update_m_e(tech_grid_supply.get_m_e())
    
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply)
    
    del tmp_v_h_shifted
    del tmp_u_e_additional
    
    
def scenario_pv_integration(energy_demand, scen_techs, tech_instances):
    """
    Function to adjust energy system balance in case of solar pv integration.
    A specified share of the additional solar pv potential is integrated.
    
    Requirements:
        - scen_techs['solar_pv']['deployment'] == True
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    tech_solar_pv : instance of SolarPV class
        Instance of solar pv.
    tech_wind_power: instance of WindPower class
        Instance of wind power.
    
    tech_grid_supply : instance of GridSupply class
        Instance of grid supply.

    Returns
    -------
    n/a
    """
    techs_solar_pv_to_integrate = scen_techs["pv_integration"]["pv_techs_to_act_on"]

    tech_grid_supply = tech_instances['grid_supply']

    for key in techs_solar_pv_to_integrate:
        ...
        tech_solar_pv = tech_instances[key]
        pvpifs = scen_techs["pv_integration"]["potential_integration_factor"][key]
        if len(pvpifs) != tech_solar_pv.get_num_installations():
            raise ValueError('pv_integration scenario: number of provided ' \
            'pv integration factors does not agree ' \
            'with number of installations (',len(pvpifs), 
            '!=',tech_solar_pv.get_num_installations(), ') for ' \
            'installation type ', key  )
        
        v_e_pvs = tech_solar_pv.get_v_e_from_installations()
        v_e_pv_pot_remain = tech_solar_pv.get_v_e_pot_remain_from_installations()

        v_e_pv_updated = []

        for i in range(len(pvpifs)):

            v_e_pv_updated.append(v_e_pvs[i] + v_e_pv_pot_remain[i]*pvpifs[i])

        tech_solar_pv.update_v_e(v_e_pv_updated)

    #--------------------------------------------------------------------------
    # Update local electricity mix:
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances)
    
    # Update import:
    tech_grid_supply.update_m_e(tech_grid_supply.get_m_e())
    #--------------------------------------------------------------------------
    # Run test for solar pv:    
    df_column_1 = tech_solar_pv.get_v_e()
    df_column_2 = tech_solar_pv.get_v_e_exp() + tech_solar_pv.get_v_e_cons()
    value_1 = df_column_1.sum()
    value_2 = df_column_2.sum()
    
    dem_eb.energy_balance_test(
        value_1=value_1,
        value_2=value_2,
        description='solar pv balance'
        )
    dem_eb.energy_balance_df_test(
        df_column_1=df_column_1,
        df_column_2=df_column_2,
        description='solar pv balance'
        )    
    dem_helper.positive_values_test(
        df_values=tech_solar_pv.get_v_e_pot_remain(),
        description='remaining solar pv potential'
        )
    
    
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply)    
    
def scenario_wind_integration(energy_demand, scen_techs, tech_instances):    
    """
    Function to adjust energy system balance in case of wind power integration.
    A specified share of the additional wind power potential is integrated.
    
    Requirements:
        - scen_techs['wind_power']['deployment'] == True
        - scen_techs['solar_pv']['deployment'] == True
    
    Parameters
    ----------
    scen_techs : dictionary
        Dictionary containing info about technologies.
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    tech_solar_pv : instance of SolarPV class
        Instance of solar pv.
    tech_wind_power: instance of WindPower class
        Instance of wind power.
    tech_grid_supply : instance of GridSupply class
        Instance of grid supply.

    Returns
    -------
    n/a
    """
    
    tech_wind_power = tech_instances['wind_power']
    tech_grid_supply = tech_instances['grid_supply']
    
    #--------------------------------------------------------------------------
    # Adjust energy accounting of technologies:
    wppif = scen_techs["wind_integration"]["potential_integration_factor"]

    # Integrate the share of the remaining potential (within the capacity
    # limits of wind_power); also stores the new capacity for the costs:
    tech_wind_power.integrate_potential(wppif)
    
    #--------------------------------------------------------------------------
    # Update local electricity mix:
    dem_eb.get_local_electricity_mix(energy_demand, tech_instances)
    
    # Update import:
    tech_grid_supply.update_m_e(tech_grid_supply.get_m_e())
        
    #--------------------------------------------------------------------------
    # Run tests for import:
    __test_import_balance(tech_grid_supply)   

def scenario_nuclear_phaseout(
        scen_techs,
        tech_instances,
        df_scen,
        ):
    npp_powers = scen_techs["nuclear_phaseout"]["nuclear_power_plant_powers"]

    planned_shutdown = scen_techs["nuclear_phaseout"]["nuclear_power_plant_shutdown_years"]
    
    if scen_techs['scenarios']['demand_side'] and scen_techs['demand_side']['simulation_year']['type'] == 'future':
        year = scen_techs['demand_side']['simulation_year']['future_year']
    else:
        year = C.CURRENT_YEAR

    tech_grid_supply = tech_instances['grid_supply']

    power_nuc_tot = np.sum(npp_powers)
    powers_still_available = np.sum([npp_powers[i] 
                                    if year < planned_shutdown[i] 
                                    else 0.0 
                                    for i in range(len(planned_shutdown))])

    nuclear_fraction = powers_still_available / power_nuc_tot

    # The limit of the Swiss nuclear part of the import is reduced (also for
    # all later updates of the import, e.g. after the optimisation); the
    # missing nuclear electricity is covered by cross-border import:
    tech_grid_supply.set_nuclear_limit_factor(nuclear_fraction)

    __test_import_balance(tech_grid_supply)   



def __report_net_storage_discharge(label, q_initial, q_final):
    """
    The manual storage scenarios have no cyclic condition: energy stored
    at the start but not at the end is not paid for by any technology.
    """
    if q_initial - q_final > 1.0:
        print(f"\nWARNING: {label} ends {q_initial - q_final:.0f} kWh below its "
              "initial charge. This energy comes from the initial charge and is "
              "not produced (nor paid for) by any technology. Consider "
              "initial_charge = 0.")


# Legacy single-storage scenario flag -> (storage technology, settings block
# with its size and initial charge):
LEGACY_STORAGE_SCENARIOS = {
    'battery_energy_storage': ('bes', 'battery_energy_storage_scenario'),
    'thermal_energy_storage': ('tes_decentralised', 'thermal_energy_storage_scenario'),
    }


def legacy_storage_scenario_config(scen_techs, legacy_scenario, tech_instances):
    """
    Prepare a legacy single-storage scenario ('battery_energy_storage' or
    'thermal_energy_storage') to run as the combined storage scenario
    (scenario_battery_plus_thermal_energy_storage) with only that storage.

    The storage is sized by the legacy settings block (capacity_kWh,
    initial_charge), as in the former single-storage scenarios: these are
    written to the combined scenario's own sizes (storages.<tech>) of the
    copy; the other storage gets size 0 and does not take part, even if it
    is deployed. The technologies' settings (capacity_kWh_max = optimiser's
    maximum, deployment) are not changed. All other settings (losses,
    efficiency, charge rate, electricity_supply_order, storage_priority,
    heat_pump_tes_min_electric_power_kW, heat_pump_tes_capacity_factor) are
    those of the combined scenario.

    scen_techs is not modified (it is saved with the results); the returned
    deep copy is the configuration of the redirected run.

    Returns
    -------
    dict
        Copy of scen_techs for scenario_battery_plus_thermal_energy_storage.
    """
    tech, settings_key = LEGACY_STORAGE_SCENARIOS[legacy_scenario]

    # As before, the storage technology itself must be deployed:
    dem_helper.check_tech_for_scenario(
        techs=[tech], scenario=legacy_scenario, scen_techs=scen_techs)

    settings = scen_techs[settings_key]
    cap = settings['capacity_kWh']
    ic = settings['initial_charge']
    # Both legacy scenarios allow zero capacity as a no-storage reference.
    # The combined validator warns and its controller skips storage dispatch.
    if (isinstance(cap, bool) or not isinstance(cap, (int, float))
            or not np.isfinite(cap) or cap < 0):
        raise ValueError(
            f"{settings_key}.capacity_kWh must be a finite nonnegative number "
            f"in the '{legacy_scenario}' scenario. Selected value: {cap!r}.")
    if (isinstance(ic, bool) or not isinstance(ic, (int, float))
            or not 0.0 <= ic <= 1.0):
        raise ValueError(
            f"{settings_key}.initial_charge must be between 0 and 1. "
            f"Selected value: {ic!r}.")

    combined = 'scenario_battery_plus_thermal_energy_storage'
    redirected = copy.deepcopy(scen_techs)
    for flag in LEGACY_STORAGE_SCENARIOS:
        redirected['scenarios'][flag] = False
    redirected['scenarios'][combined] = True
    # Scenario sizes: only this storage takes part (size 0 = not active),
    # the technologies (capacity_kWh_max, deployment) are not changed:
    for other, _ in LEGACY_STORAGE_SCENARIOS.values():
        redirected[combined]['storages'][other] = {
            'capacity_kWh': float(cap) if other == tech else 0.0,
            'initial_charge': float(ic) if other == tech else 0.0,
            }

    try:
        dem_helper.validate_scenario_battery_plus_thermal_energy_storage(
            redirected, warn_single_storage=False)
    except ValueError as e:
        raise ValueError(
            f"Scenario '{legacy_scenario}' runs as {combined} with only "
            f"{tech}: {e}") from e

    return redirected


def scenario_battery_plus_thermal_energy_storage(energy_demand, tech_instances, scen_techs):
    """Dispatch each store once per priority pass; all timestep energies are kWh.

    Local generation covers demand before either store discharges. TES-first
    replaces the remaining HP-supplied heat before using BES electricity;
    BES-first supplies the deficit before TES is considered. The grid supplies
    the final deficit.
    """
    # Read the scenario settings without changing the caller's configuration.
    config = scen_techs['scenario_battery_plus_thermal_energy_storage']
    order = config['electricity_supply_order']
    # Check the mix contract before changing any technology state. Some model
    # generator objects exist even when their deployment or production is zero.
    supported = {'solar_pvrooftop', 'solar_pvalpine', 'wind_power', 'biomass', 'hydro_power'}
    omitted = supported.intersection(tech_instances) - set(order)
    if omitted:
        raise ValueError(f'electricity_supply_order omits present generators: {sorted(omitted)}.')
    # A zero-size reference run needs only the ordinary electricity allocation.
    # Skip HP COP preparation and storage updates so unused devices cannot
    # introduce errors or change the building heat supply in this case.
    if not dem_helper.active_combined_storages(scen_techs):
        for key in ('bes', 'tes_decentralised'):
            if key in tech_instances:
                tech_instances[key].set_scenario_cap(0.0)
        dem_eb.get_local_electricity_mix(
            energy_demand, tech_instances, with_bes=False,
            electricity_supply_order=order)
        grid = tech_instances['grid_supply']
        grid.update_m_e(grid.get_m_e())
        return

    demand = np.array(energy_demand.get_d_e(), dtype=float, copy=True)
    heating_electricity = np.array(energy_demand.get_d_e_h(), dtype=float, copy=True)
    count = len(demand)

    # Reject invalid series before dispatch so NaNs cannot silently become flows.
    def series(values, name):
        values = np.array(values, dtype=float, copy=True)
        if values.shape != (count,) or not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f'{name} must contain {count} finite nonnegative hourly values.')
        return values

    demand = series(demand, 'electricity demand')
    heating_electricity = series(heating_electricity, 'heating electricity')
    if count == 0:
        raise ValueError('The combined storage scenario needs at least one timestep.')

    # Sum actual local generation; the electricity-mix function allocates its
    # consumption and exports by source after storage operation is known.
    renewable = np.zeros(count)
    for key in order:
        if key in tech_instances:
            renewable += series(tech_instances[key].get_v_e(), key)

    # Read the fixed storage properties once. Hourly flows, state and losses
    # are written through the same per-hour setters as the BES-only scenario.
    # Sizes and initial charges are this scenario's own settings (storages);
    # the technologies' capacity_kWh_max is only the optimiser's maximum.
    # The scenario size is also the capacity the cost module charges.
    stores = {}
    for key in dem_helper.active_combined_storages(scen_techs):
        tech = tech_instances[key]
        size = config['storages'][key]
        cap = float(size['capacity_kWh'])
        tech.set_scenario_cap(cap)
        stores[key] = {
            'tech': tech, 'cap': cap, 'eta': tech.get_eta_chg_dchg(),
            'gamma': tech.get_gamma(),
            'limit': cap * scen_techs[key]['chg_dchg_per_cap_max'],
            'initial': cap * float(size['initial_charge']),
        }

    # Prepare the effective COP once, as in the existing TES-only scenario;
    # update_v_h_i then uses that same conversion ratio throughout dispatch.
    hp = tech_instances.get('heat_pump')
    hp_heat = series(hp.get_v_h(), 'HP heat') if hp is not None else np.zeros(count)
    cops = np.ones(count)
    if hp is not None:
        hp.calculate_effective_cops()
        cops = np.array([hp.heat_output(1.0, i) for i in range(count)])
        if not np.isfinite(cops).all() or (cops < 1).any():
            raise ValueError('TES heat-pump operation requires finite COP values >= 1.')
    hp_limit = float(scen_techs['heat_pump']['kW_th_max'])
    if 'tes_decentralised' in stores:
        # Freeze a full-year, pre-storage reference. Never infer it from this
        # run's shortened HP series or from HP output after charging the TES.
        annual_peak = energy_demand.get_annual_hp_peak_kW()
        hp_limit = min(hp_limit, annual_peak * config['heat_pump_tes_capacity_factor'])
        # Report both thermal powers once so the inferred fleet capacity can
        # be checked in the normal run_dem_local console output.
        print(f' HP annual building-heating peak: {annual_peak:.3f} kW_th; '
              f'total HP limit for TES dispatch: {hp_limit:.3f} kW_th')
        if annual_peak == 0 and stores['tes_decentralised']['cap'] > 0:
            warnings.warn(
                'Combined storage: annual HP building-heating peak is zero; '
                'HP charging of TES is disabled because no fleet capacity '
                'can be inferred.', UserWarning, stacklevel=2)

    # Walk forward in time; standing losses occur between consecutive hours,
    # while the first hour starts at the explicitly configured initial charge.
    for i in range(count):
        for key, store in stores.items():
            tech = store['tech']
            previous = ((tech.get_q_e() if key == 'bes' else tech.get_q_h())[i - 1]
                        if i else store['initial'])
            loss = previous * store['gamma'] if i else 0.0
            store.update(previous=previous, loss=loss, level=previous - loss,
                         charge=0.0, discharge=0.0)
            # As in BES-only, write the transition loss to the preceding hour;
            # the final loss entry remains zero because no next hour is run.
            if key == 'bes':
                tech.update_q_e_i(i, store['level'])
                tech.update_l_q_e_i(i, 0.0)
                if i:
                    tech.update_l_q_e_i(i - 1, loss)
            else:
                tech.update_q_h_i(i, store['level'])
                tech.update_l_q_h_i(i, 0.0)
                if i:
                    tech.update_l_q_h_i(i - 1, loss)

        # Visit each discharging technology once in the requested priority.
        # Both stores serve only demand not covered by local generation.
        bes_output = 0.0
        for key in config['storage_priority']['discharge']:
            if key not in stores:
                continue
            store = stores[key]
            available = min(store['limit'], store['level'] * store['eta'])
            if key == 'bes':
                bes_output = min(max(demand[i] - renewable[i], 0.0), available)
                store['discharge'] = bes_output
                store['level'] -= bes_output / store['eta']
                continue

            # TES supplies heat directly to replace HP output; it does not run
            # the HP on discharge or replace any building electric-heater heat.
            # Reserve local generation for demand before replacing HP heat.
            # TES-first therefore reduces the HP deficit before BES supplies it;
            # BES-first also reserves electricity already delivered by BES.
            remaining_import = max(demand[i] - renewable[i] - bes_output, 0.0)
            replaced = min(hp_heat[i], available, remaining_import * cops[i])
            hp_heat[i] -= replaced
            saved_electricity = replaced / cops[i]
            demand[i] -= saved_electricity
            heating_electricity[i] -= saved_electricity
            store['discharge'] = replaced
            store['level'] -= replaced / store['eta']

        # Charge from remaining local surplus only. Each storage is visited once;
        # a store that discharged this hour is never charged in the same hour.
        surplus = max(renewable[i] - demand[i], 0.0)
        for key in config['storage_priority']['charge']:
            if key not in stores or surplus <= 0:
                continue
            store = stores[key]
            if store['discharge'] > 0:
                continue
            headroom = max(store['cap'] - store['level'], 0.0) / store['eta']
            feasible = min(store['limit'], headroom)
            if key == 'bes':
                charged = min(surplus, feasible)
                store['charge'] = charged
                store['level'] += charged * store['eta']
                surplus -= charged
                continue

            # Only the HP charges TES, using remaining renewable surplus within
            # the existing HP thermal-power, TES charging-rate and space limits.
            # Hourly timesteps make electrical kWh equal to average input kW.
            electric_input = min(surplus, feasible / cops[i],
                                 max(hp_limit - hp_heat[i], 0.0) / cops[i])
            minimum = config['heat_pump_tes_min_electric_power_kW']
            # A positive threshold must be exceeded by the feasible input;
            # zero disables the threshold. Unused surplus goes to the next store.
            if electric_input <= 0 or (minimum > 0 and electric_input <= minimum):
                continue
            heat_input = electric_input * cops[i]
            hp_heat[i] += heat_input
            store['charge'] = heat_input
            store['level'] += heat_input * store['eta']
            # HP input includes TES charging, so record its electricity once.
            demand[i] += electric_input
            heating_electricity[i] += electric_input
            surplus = max(surplus - electric_input, 0.0)

        # Check this hour's ledger before writing the final flows and state.
        # Losses and efficiencies are unchanged; only their recording now uses
        # the established per-hour interface instead of a separate bulk writer.
        for key, store in stores.items():
            charged = store['charge']
            discharged = store['discharge']
            level = store['level']
            eta = store['eta']
            expected = store['previous'] - store['loss'] + charged * eta - discharged / eta
            if (not np.isclose(expected, level, atol=1e-8, rtol=1e-10)
                    or level < -1e-8 or level > store['cap'] + 1e-8):
                raise ValueError('Combined storage dispatch violates a storage energy balance.')

            # Use the BES-only update sequence: input, output, stored energy,
            # charging/discharging losses, then fractional state of charge.
            tech = store['tech']
            if key == 'bes':
                tech.update_u_e_i(i, charged)
                tech.update_v_e_i(i, discharged)
                tech.update_q_e_i(i, level)
                tech.update_l_u_e_i(i, charged * (1.0 - eta))
                tech.update_l_v_e_i(i, discharged * (1.0 / eta - 1.0))
            else:
                tech.update_u_h_i(i, charged)
                tech.update_v_h_i(i, discharged)
                tech.update_q_h_i(i, level)
                tech.update_l_u_h_i(i, charged * (1.0 - eta))
                tech.update_l_v_h_i(i, discharged * (1.0 / eta - 1.0))
            tech.update_sos_i(i, level / store['cap'] if store['cap'] > 0 else 0.0)

        # Update HP and demand in the same hour, as in TES-only. The HP setter
        # also updates its electrical input and environmental heat contribution.
        if demand[i] < -1e-8 or heating_electricity[i] < -1e-8:
            raise ValueError('Combined storage dispatch produced negative demand.')
        if hp is not None:
            hp.update_v_h_i(i, hp_heat[i])
        energy_demand.update_d_e_i(i, max(demand[i], 0.0))
        energy_demand.update_d_e_h_i(i, max(heating_electricity[i], 0.0))

    # Report unpaid initial energy using the same warning as the single-store
    # scenarios, separately for each deployed store after its final timestep.
    for key, store in stores.items():
        tech = store['tech']
        final_energy = tech.get_q_e()[-1] if key == 'bes' else tech.get_q_h()[-1]
        label = 'Combined BES scenario' if key == 'bes' else 'Combined TES scenario'
        __report_net_storage_discharge(label, store['initial'], final_energy)

    # Refresh annual totals after the hourly demand updates. BES charging is
    # added separately by the mix function, preserving its existing contract.
    energy_demand.update_d_e(np.maximum(demand, 0.0))
    energy_demand.update_d_e_h(np.maximum(heating_electricity, 0.0))
    dem_eb.get_local_electricity_mix(
        energy_demand, tech_instances, with_bes='bes' in stores,
        electricity_supply_order=order)
    grid = tech_instances['grid_supply']
    grid.update_m_e(grid.get_m_e())

def __test_import_balance(tech_grid_supply):
    
    #--------------------------------------------------------------------------
    # Run tests for import:

    sum_a = dem_helper.get_m_e_ch_sum(tech_grid_supply)

    sum_b = (
        sum(tech_grid_supply.get_m_e_ch())
        + sum(tech_grid_supply.get_m_e_cbimport())
        )

    dem_eb.energy_balance_test(
        sum(tech_grid_supply.get_m_e_ch()),
        sum_a,
        'electricity mix'
        )

    dem_eb.energy_balance_test(sum(tech_grid_supply.get_m_e()),
                                   sum_b,
                                   'electricity import'
                                   )

    dem_eb.energy_balance_df_test(
        tech_grid_supply.get_m_e(),
        tech_grid_supply.get_m_e_ch() + tech_grid_supply.get_m_e_cbimport(),
        'electricity import df'
        )     

    dem_helper.positive_values_test(tech_grid_supply.get_m_e(),
                                    'total import'
                                    )
    dem_helper.positive_values_test(tech_grid_supply.get_m_e_ch(),
                                    'swiss import'
                                    )
    dem_helper.positive_values_test(tech_grid_supply.get_m_e_cbimport(),
                                    'cross-border import'
                                    )
