# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 14:12:26 2024

@author: UeliSchilt, Tim Zurbriggen
"""

_MISSING = object()


def get_var(obj, *names, default=_MISSING):
    """
    Return the first existing attribute from an object among several candidate names.

    This helper is used where equivalent attributes are named differently across
    technology classes. It tries each name in order and returns the first match.

    Parameters
    ----------
    obj : object
        Object from which the attribute should be read.
    *names : str
        Candidate attribute names to try in order.
    default : any, optional
        Value to return if none of the attributes exist. If not provided,
        an AttributeError is raised.

    Returns
    -------
    any
        Value of the first matching attribute, or `default` if given and no
        attribute is found.

    Raises
    ------
    AttributeError
        If none of the requested attributes exist and no default is provided.

    Notes
    -----
    This works for:
    - instance attributes
    - class attributes
    - inherited class attributes
    """
    for name in names:
        value = getattr(obj, name, _MISSING)
        if value is not _MISSING:
            return value

    if default is not _MISSING:
        return default

    raise AttributeError(
        f"{type(obj).__name__} instance has none of attributes: {names}"
    )


def annuity_factor(lifetime_years, interest_rate=0.05):
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


def calculate_total_anual_costs(tech_instances, number_of_days):
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

    Returns
    -------
    dict
        Dictionary with aggregated monetary cost indicators:
        {
            "electricity_tlc": float,
            "heat_tlc": float,
            "total": float
        }

    Notes
    -----
    Cost calculation includes:
    - annualized CAPEX
    - maintenance / OPEX
    - energy costs
    - energy revenues

    Technologies are classified as:
    - storage, if one of the storage state variables exists
    - heat-producing, if output carrier starts with "h"
    - electricity-producing, if output carrier starts with "e"

    Special cases in current implementation:
    - "pile_of_berries" is skipped
    - "grid_supply" excludes CAPEX, maintenance, and revenue calculation

    Important assumptions / limitations:
    - division by zero may occur if no heat or electricity is generated
    - debug print statements are currently active
    - function name contains a typo ("anual" instead of "annual")
    """
    total_anual_costs = {"heat": {}, "electricity": {}, "storage": {}}
    total_heat_generation = 0
    total_electricity_generation = 0

    for tech in tech_instances:
        print(tech, tech_instances[tech])
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

            annualized_capex = (
                capex
                * annuity_factor(
                    tech_instances[tech]._lifetime,
                    tech_instances[tech]._interest_rate,
                )
                
            )
            print(annualized_capex, opex, energy_costs, energy_revenue)
            tac = (
                (annualized_capex + opex) * (number_of_days / 365)
                + energy_costs
                - energy_revenue
            )

            output_carrier = get_var(
                tech_instances[tech],
                "_output_carrier",
                "output_carrier",
                default=_MISSING,
            )
            if get_var(
                tech_instances[tech],
                "_q_h",
                "_q_gas",
                "_q_wd",
                "_q_hyd",
                "_q_e",
                default=None,
            ) is not None:
                total_anual_costs["storage"][tech] = tac
            elif output_carrier[0] == "h":
                total_anual_costs["heat"][tech] = tac
                total_heat_generation += get_var(tech_instances[tech], "_v_h").sum()
            elif output_carrier[0] == "e":
                total_anual_costs["electricity"][tech] = tac
                total_electricity_generation += get_var(
                    tech_instances[tech], "_v_e", "_m_e"
                ).sum()
                print(get_var(tech_instances[tech], "_v_e", "_m_e").sum())
            else:
                raise AttributeError(
                    "carrier must be 'heat' or 'electricity', or 'storage'"
                )

    print(total_electricity_generation)
    total_anual_costs["heat"]["total"] = sum(total_anual_costs["heat"].values())
    total_anual_costs["electricity"]["total"] = sum(
        total_anual_costs["electricity"].values()
    )
    total_anual_costs["storage"]["total"] = sum(total_anual_costs["storage"].values())

    tlc_electricity = (
        total_anual_costs["electricity"]["total"] / total_electricity_generation
    )
    tlc_heat = total_anual_costs["heat"]["total"] / total_heat_generation
    total = (
        total_anual_costs["heat"]["total"]
        + total_anual_costs["electricity"]["total"]
        + sum(total_anual_costs["storage"].values())
    )

    # tlc_electricity = 1685020.0745715834/total_electricity_generation
    # tlc_heat = 1685020.0745715834/total_heat_generation

    return {"electricity_tlc": tlc_electricity, "heat_tlc": tlc_heat, "total": total}


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
    return {
        "monetary": calculate_total_anual_costs(tech_instances, number_of_days),
        "co2": calculate_CO2_emissions(supply, tech_instances),
    }
    # return {"TAC": calculate_total_anual_costs(tech_instances), "LCOE": calculate_levelized_cost_of_energy(tech_instances, number_of_days)}


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
    - storage-related double counting is noted but not fully resolved
    - total emissions are divided by total heat and electricity generation
      separately, which may not reflect detailed source allocation
    - division by zero may occur if no heat or electricity is generated
    """
    # Work in Progress...
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
                sum(supply.supply_tech_dict["annual_msw_supply"])
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
        total_electricity_generation += sum(
            get_var(tech_instances[tech], "_v_e", "_m_e", default=[0])
        )

    co2_emissions["total"] = sum(co2_emissions.values())
    co2_emissions["electricity_tlc"] = (
        co2_emissions["total"] / total_electricity_generation
    )
    co2_emissions["heat_tlc"] = co2_emissions["total"] / total_heat_generation

    return {
        "electricity_tlc": co2_emissions["electricity_tlc"],
        "heat_tlc": co2_emissions["heat_tlc"],
        "total": co2_emissions["total"],
    }