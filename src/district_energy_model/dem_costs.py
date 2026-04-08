# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 14:12:26 2024

@author: UeliSchilt, Tim Zurbriggen
"""
import warnings
import district_energy_model.dem_constants as C

def annuity_factor(lifetime_years, interest_rate=0.025):
    """
    Calculate the annuity factor for annualizing investment costs.

    The annuity factor is used to convert a one-time capital expenditure into
    an equivalent annual cost over the asset lifetime.

    Parameters
    ----------
    lifetime_years : int or float
        Technical lifetime of the asset in years.
    interest_rate : float, optional
        Interest or discount rate used for annualization. Default is 0.05.

    Returns
    -------
    float
        Annuity factor.

    Notes
    -----
    If the interest rate is zero, the function returns `1 / lifetime_years`.
    Otherwise, it applies the standard annuity formula.

    Formula
    -------
    AF = (r * (1 + r)^t) / ((1 + r)^t - 1)

    where:
    - r = interest_rate
    - t = lifetime_years
    """
    if interest_rate == 0:
        return 1 / lifetime_years
    else:
        r = interest_rate
        t = lifetime_years
        af = (r * (1 + r) ** t) / ((1 + r) ** t - 1)

        return af
    
def get_old_capacities(tech_instances, debug=False):
    # Get existing capacities for all technologies and save them as attributes of the respective techs
    for tech in tech_instances:
        if debug:
            print(f"Preparing cost calculation for technology: {tech}")
        if tech != 'grid_supply' and tech != 'pile_of_berries':
            tech_instances[tech].get_existing()
        if debug:
            print(f"preparation of {tech} completed.\n")
    return 0

def get_one_to_one_replacement_capacities(tech_instances, debug=False):
    # Get replacement capacities for all technologies and save them as attributes of the respective techs
    for tech in tech_instances:
        if debug:
            print(f"Calculating replacement needs for technology: {tech}")
        if tech != 'grid_supply' and tech != 'pile_of_berries':
            tech_instances[tech].get_needs_replacement_cap()
        if debug:
            print(f"replacement calculation for {tech} completed.\n")
    return 0


def calculate_total_annual_costs(tech_instances, number_of_days, supply, debug=False):
    """
    Calculate total annualized monetary costs for all modeled technologies.

    The function aggregates technology costs into heat, electricity, and
    storage categories, then computes total levelized costs for heat and
    electricity based on total generated energy.

    Parameters
    ----------
    tech_instances : dict
        Dictionary of technology instances, keyed by technology name.
        Each technology is expected to provide cost methods and energy flow
        attributes used by this function.
    number_of_days : int or float
        Length of the modeled period in days. Fixed annual costs are scaled
        by `number_of_days / 365`.
    supply : object
        Supply object containing imported resource flows and cost data for energy cost calculation.

    Returns
    -------
    dict
        Dictionary with aggregated monetary cost indicators:
        {
            "total": total_annual_costs, 
            "levelized_cost_of_energy": levelized_cost_of_energy
        }
    
    dict 
        cost_breakdown: nested dictionary with detailed cost components for each technology


    Notes
    -----
    Cost calculation includes:
    - annualized CAPEX
    - maintenance / OPEX
    - energy costs
    - energy revenues


    Special cases in current implementation:
    - "pile_of_berries" is skipped
    - "grid_supply" excludes CAPEX, maintenance, and revenue calculation

    Important assumptions / limitations:
    - division by zero may occur if no heat and electricity is generated

    """
    total_annual_costs = 0
    total_energy_generation = 0
    # total_heat_generation = 0
    # total_electricity_generation = 0
    # total_electricity_cost = 0
    cost_breakdown = {}



    price_CHFpl=supply.supply_tech_dict['oil_price_CHFpl']
    hv_oil_MJpkg=supply.supply_tech_dict['hv_oil_MJpkg']
    hv_oil_MJpl = hv_oil_MJpkg*C.DENSITY_oil_kgpl # [MJ/l]
    hv_oil_kWhpl = hv_oil_MJpl*C.CONV_MJ_to_kWh
    price_CHFpkWh = price_CHFpl/hv_oil_kWhpl
    energy_costs = sum(supply._m_oil) * price_CHFpkWh
    total_annual_costs += energy_costs
    cost_breakdown["oil"] = energy_costs

    energy_costs = sum(supply._m_gas) * supply.supply_tech_dict["gas_price_CHFpkWh"]
    total_annual_costs += energy_costs
    cost_breakdown["gas"] = energy_costs    
    
    price_CHFpkg=supply.supply_tech_dict['wood_price_CHFpkg_local']
    hv_wood_MJpkg=supply.supply_tech_dict['hv_wood_MJpkg']
    hv_wood_kWhpkg=hv_wood_MJpkg*C.CONV_MJ_to_kWh
    price_CHFpkWh = price_CHFpkg/hv_wood_kWhpkg
    energy_costs = sum(supply._s_wd) * price_CHFpkWh
    total_annual_costs += energy_costs
    cost_breakdown["wood_local"] = energy_costs

    price_CHFpkg=supply.supply_tech_dict['wood_price_CHFpkg_imported']
    hv_wood_MJpkg=supply.supply_tech_dict['hv_wood_MJpkg']
    hv_wood_kWhpkg=hv_wood_MJpkg*C.CONV_MJ_to_kWh
    price_CHFpkWh = price_CHFpkg/hv_wood_kWhpkg
    energy_costs = sum(supply._m_wd) * price_CHFpkWh
    total_annual_costs += energy_costs
    cost_breakdown["wood_import"] = energy_costs
        
    energy_costs = sum(supply._s_wet_bm) * 0.001  # currently minimum miniscule cost to favor truly free resources (e.g. PV)
    total_annual_costs += energy_costs
    cost_breakdown["wet_biomass"] = energy_costs
    

    for tech in tech_instances:
        if debug:
            print(f"Calculating costs for technology: {tech}")
        capex = 0
        opex = 0
        energy_revenue = 0
        energy_costs = 0
        if tech != "pile_of_berries":  # !!! this should be adapted to the actual technologies included in the model    |||  and tech != "solar_pvrooftop" and tech != "solarthermal_rooftop"
            if tech != "grid_supply":
                capex = tech_instances[tech].get_total_capex()
                opex = tech_instances[tech].get_total_maintenance()
                energy_revenue = tech_instances[tech].get_energy_revenue()
            energy_costs = tech_instances[tech].get_energy_costs()

            if hasattr(tech_instances[tech], '_lifetime') and hasattr(tech_instances[tech], '_interest_rate'):
                annualized_capex = (
                    capex
                    * annuity_factor(
                        tech_instances[tech]._lifetime,
                        tech_instances[tech]._interest_rate,
                    )
                )
            elif hasattr(tech_instances[tech], '_lifetime') and not hasattr(tech_instances[tech], '_interest_rate'):
                warnings.warn("'interest_rate' attribute does not exist. Annuity factor was calculated with default interest rate of 0.025.")   
                annualized_capex = capex * annuity_factor(tech_instances[tech]._lifetime, interest_rate=0.025)
            else: 
                warnings.warn("'lifetime' attribute does not exist. Annualized capex was set to 0")
                annualized_capex = 0

            tac = (
                (annualized_capex + opex) * (number_of_days / 365)
                + energy_costs
                - energy_revenue
            )
            total_annual_costs += tac
            cost_breakdown[tech] = {
                "tac": tac,
                "annualized_capex": annualized_capex*(number_of_days / 365),
                "opex": opex * (number_of_days / 365),
                "energy_costs": energy_costs,
                "energy_revenue": energy_revenue,
                }

            if debug:
                print(f"  CAPEX: {capex:.2f} CHF")
                print(f"  OPEX: {opex*(number_of_days / 365):.2f} CHF/year")
                print(f"  Energy Costs: {energy_costs:.2f} CHF")
                print(f"  Energy Revenue: {energy_revenue:.2f} CHF")
                print(f"  Annualized CAPEX: {annualized_capex*(number_of_days / 365):.2f} CHF/year")
                print(f"  Total Annual Cost (scaled): {tac:.2f} CHF\n")

            # calculate total energy generation for levelized cost calculation, excluding storage technologies:
            storage_attributes = ['_q_e', '_q_h', '_q_gas', '_q_wd', 'q_hyd']
            if not any(hasattr(tech_instances[tech], attr) for attr in storage_attributes):
                if hasattr(tech_instances[tech], '_v_h'):
                    total_energy_generation += tech_instances[tech]._v_h.sum()
                    # total_heat_generation += tech_instances[tech]._v_h.sum()
                if hasattr(tech_instances[tech], '_v_e'):
                    total_energy_generation += tech_instances[tech]._v_e.sum()
                    # total_electricity_generation += tech_instances[tech]._v_e.sum()
                    # total_electricity_cost += tac
                elif hasattr(tech_instances[tech], '_m_e'):
                    total_energy_generation += tech_instances[tech]._m_e.sum()
                    # total_electricity_generation += tech_instances[tech]._m_e.sum()
                    # total_electricity_cost += tac

    # levelized_cost_of_energy = total_annual_costs/total_energy_generation
    # electricity_tlc = total_electricity_cost/total_electricity_generation
    # heat_tlc = total_annual_costs/total_heat_generation
        
   
    return {"total": total_annual_costs}, cost_breakdown


# def calculate_levelized_cost_of_energy(tech_instances, number_of_days):

#     lcoe = {"heat": {}, "electricity": {}}

#     total_heat_cost = 0
#     total_heat_produced = 0

#     total_electricity_cost = 0
#     total_electricity_produced = 0

#     for tech in tech_instances:
#         cost = 0
#         energy_produced = 0
#         if tech != "solar_pvrooftop" and tech != "solarthermal_rooftop" and tech != "pile_of_berries":  # !!! this should be adapted to the actual technologies included in the model
#             if tech != "grid_supply":
#                 for year in range(int(number_of_days/365)):
#                     cost += (1/(1 + tech_instances[tech]._interest_rate) ** year)*( tech_instances[tech].get_total_capex() + tech_instances[tech].get_total_maintenance() + tech_instances[tech].get_energy_costs())
#                     energy_produced += (1/(1 + tech_instances[tech]._interest_rate) ** year) * tech_instances[tech]._v_h.sum()

#         output_carrier = get_var(tech_instances[tech], "_output_carrier", "output_carrier", default=_MISSING)
#         if output_carrier[0] == "h":
#             lcoe["heat"][tech] = cost / energy_produced if energy_produced > 0 else float('inf')
#             total_heat_cost += cost
#             total_heat_produced += energy_produced
#         elif output_carrier[0] == "e":
#             lcoe["electricity"][tech] = cost / energy_produced if energy_produced > 0 else float('inf')
#             total_electricity_cost += cost
#             total_electricity_produced += energy_produced

#     lcoe["heat"]["total"] = total_heat_cost/total_heat_produced if total_heat_produced > 0 else float('inf')
#     # lcoe["heat"]["total_XXX"] = 0
#     lcoe["electricity"]["total"] = total_electricity_cost/total_electricity_produced if total_electricity_produced > 0 else float('inf')

#     return None


def get_total_costs(tech_instances, supply, number_of_days):
    """
    Return combined monetary and CO2 cost indicators for the current system.

    This is a wrapper function that calls the monetary cost calculation and
    the CO2 emissions calculation and returns both in a single dictionary.

    Parameters
    ----------
    tech_instances : dict
        Dictionary of technology instances.
    supply : object
        Supply object containing imported resource flows and CO2 intensity data.
    number_of_days : int or float
        Length of the modeled period in days.

    Returns
    -------
    dict
        Dictionary with the following structure:
        {
            "monetary": dict,
            "co2": dict
        }

        The "monetary" entry is produced by `calculate_total_anual_costs(...)`
        and the "co2" entry by `calculate_CO2_emissions(...)`.
    """
    monetary_costs, monetary_breakdown = calculate_total_annual_costs(tech_instances, number_of_days, supply)
    co2_emissions, co2_emissions_breakdown = calculate_CO2_emissions(supply, tech_instances)
    cost_overwiew = {
        "monetary": monetary_costs,
        "co2": co2_emissions,
    }
    return {"cost_overwiew": cost_overwiew, "monetary_breakdown": monetary_breakdown, "co2_breakdown": co2_emissions_breakdown}
    # return {"TAC": calculate_total_annual_costs(tech_instances), "LCOE": calculate_levelized_cost_of_energy(tech_instances, number_of_days)}


def calculate_CO2_emissions(supply, tech_instances):
    """
    Calculate total direct CO2 emissions and normalized emission indicators.

    The function estimates CO2 emissions from imported fuels and selected
    technologies, then derives total emissions per unit of generated heat
    and electricity.

    Parameters
    ----------
    supply : object
        Supply object containing imported energy/material flows and emission
        factors in `supply.supply_tech_dict`.
    tech_instances : dict
        Dictionary of technology instances, keyed by technology name.

    Returns
    -------
    dict
        Dictionary with aggregated CO2 indicators:
        {
            "electricity_tlc": float,
            "heat_tlc": float,
            "total": float
        }

    Notes
    -----
    Included emission sources currently are:
    - imported oil
    - imported gas
    - imported wood
    - local wood
    - wet biomass
    - municipal solid waste, if "waste_to_energy" is present
    - imported grid electricity, if "grid_supply" is present
    - district heating, if "district_heating" is present

    The function is marked in the code as work in progress.

    Current limitations:
    - lifecycle emissions are not included
    - total emissions are divided by total heat and electricity generation
      separately, which may not reflect detailed source allocation
    - division by zero may occur if no heat or electricity is generated
    """
    
    # Calculate emissions from fossil fuels at import from the Supply Class / What about lifecycle emissions?
    # CO2 intensity for technologies?
    #
    # Do not double count energy from storage technologies

    co2_emissions = {}
    total_heat_generation = 0
    total_electricity_generation = 0

    co2_emissions["emissions_oil"] = (
        sum(supply._m_oil) * supply.supply_tech_dict["co2_content_oil"]
    )
    co2_emissions["emissions_gas"] = (
        sum(supply._m_gas) * supply.supply_tech_dict["co2_content_gas"]
    )
    co2_emissions["emissions_wood_import"] = (
        sum(supply._m_wd) * supply.supply_tech_dict["co2_content_imported_wood"]
    )
    co2_emissions["emissions_wood_local"] = (
        sum(supply._s_wd) * supply.supply_tech_dict["co2_content_local_wood"]
    )
    co2_emissions["emissions_wet_bm"] = (
        sum(supply._s_wet_bm) * supply.supply_tech_dict["co2_content_wet_biomass"]
    )
    #co2_emissions["emissions_msw"] = sum(supply.supply_tech_dict['annual_msw_supply'])*supply.supply_tech_dict['co2_content_msw']*supply.supply_tech_dict['msw_share_fossile']
    for tech in tech_instances:
        if tech == "waste_to_energy":
            co2_emissions["emissions_msw"] = (
                sum(tech_instances["waste_to_energy"]._u_msw)
                * supply.supply_tech_dict["co2_content_msw"]
                * supply.supply_tech_dict["msw_share_fossile"]
            )
        if tech == "grid_supply":
            co2_emissions["emissions_grid"] = (
                sum(tech_instances["grid_supply"]._m_e)
                * tech_instances["grid_supply"]._co2_intensity
            )
        if tech == "district_heating":
            co2_emissions["district_heating"] = (
                sum(tech_instances["district_heating"]._m_h)
                * tech_instances["district_heating"]._co2_intensity
            )

    for tech in tech_instances:
        total_heat_generation += sum(getattr(tech_instances[tech], "_v_h", [0]))
        total_electricity_generation += sum(getattr(tech_instances[tech], "_v_e", [0])) 
        total_electricity_generation += sum(getattr(tech_instances[tech], "_m_e", [0]))


    co2_emissions_total = sum(co2_emissions.values())

    return co2_emissions_total, co2_emissions