# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 14:12:26 2024

@author: UeliSchilt
"""
_MISSING = object()

def get_var(obj, *names, default=_MISSING):
    """
    Safely read an attribute from an instance when its name is inconsistent
    across classes.

    Works for:
    - instance attributes
    - class variables
    - inherited class variables
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

def get_installed_capacity():
    return None


def get_new_installations():
    return None


def annuity_factor(lifetime_years, interest_rate=0.05):
    if interest_rate == 0:
        return 1 / lifetime_years
    else:
        r = interest_rate
        t = lifetime_years
        af = (r*(1 + r)**t)/((1 + r)**t - 1)
        
        return af 


def calculate_total_anual_costs(tech_instances):
    total_anual_costs = {"heat": {}, "electricity": {}}
    total_heat_generation = 0
    total_electricity_generation = 0
    
    for tech in tech_instances:
        capex = 0
        opex = 0
        energy_revenue = 0
        energy_costs = 0
        if tech != "solar_pvrooftop" and tech != "solarthermal_rooftop" and tech != "pile_of_berries":  # !!! this should be adapted to the actual technologies included in the model
            if tech != "grid_supply":
                capex = tech_instances[tech].get_total_capex()
                opex = tech_instances[tech].get_total_maintenance()
                energy_revenue = tech_instances[tech].get_energy_revenue()
            energy_costs = tech_instances[tech].get_energy_costs()
            

            annualized_capex = capex*annuity_factor(tech_instances[tech]._lifetime, tech_instances[tech]._interest_rate)
            tac = annualized_capex + opex + energy_costs

            
            output_carrier = get_var(tech_instances[tech], "_output_carrier", "output_carrier", default=_MISSING)
            if output_carrier[0] == "h":
                total_anual_costs["heat"][tech] = tac
                total_heat_generation += get_var(tech_instances[tech], "_v_h").sum()
            elif output_carrier[0] == "e":
                total_anual_costs["electricity"][tech] = tac
                total_electricity_generation += get_var(tech_instances[tech], "_v_e", "_m_e").sum()
            else:
                raise AttributeError("carrier must be 'heat' or 'electricity'")
            
    
    total_anual_costs["heat"]["total"] = sum(total_anual_costs["heat"].values())
    total_anual_costs["electricity"]["total"] = sum(total_anual_costs["electricity"].values())

    tlc_electricity = 58572988.004325114/total_electricity_generation 
    tlc_heat = 58572988.004325114/total_heat_generation
    # tlc_electricity = total_anual_costs["electricity"]["total"]/total_electricity_generation
    # tlc_heat = total_anual_costs["heat"]["total"]/total_heat_generation
    total = total_anual_costs["heat"]["total"] + total_anual_costs["electricity"]["total"]

    return {"electricity_tlc": tlc_electricity, "heat_tlc": tlc_heat,"total": total}

def calculate_levelized_cost_of_energy(tech_instances, number_of_days):

    lcoe = {"heat": {}, "electricity": {}}

    total_heat_cost = 0
    total_heat_produced = 0

    total_electricity_cost = 0
    total_electricity_produced = 0

    for tech in tech_instances:
        cost = 0
        energy_produced = 0
        if tech != "solar_pvrooftop" and tech != "solarthermal_rooftop" and tech != "pile_of_berries":  # !!! this should be adapted to the actual technologies included in the model
            if tech != "grid_supply":
                for year in range(int(number_of_days/365)):
                    cost += (1/(1 + tech_instances[tech]._interest_rate) ** year)*( tech_instances[tech].get_total_capex() + tech_instances[tech].get_total_maintenance() + tech_instances[tech].get_energy_costs())
                    energy_produced += (1/(1 + tech_instances[tech]._interest_rate) ** year) * tech_instances[tech]._v_h.sum()  
        
        output_carrier = get_var(tech_instances[tech], "_output_carrier", "output_carrier", default=_MISSING)
        if output_carrier[0] == "h":
            lcoe["heat"][tech] = cost / energy_produced if energy_produced > 0 else float('inf')
            total_heat_cost += cost
            total_heat_produced += energy_produced
        elif output_carrier[0] == "e":
            lcoe["electricity"][tech] = cost / energy_produced if energy_produced > 0 else float('inf')
            total_electricity_cost += cost
            total_electricity_produced += energy_produced

    lcoe["heat"]["total"] = total_heat_cost/total_heat_produced if total_heat_produced > 0 else float('inf')
    # lcoe["heat"]["total_XXX"] = 0
    lcoe["electricity"]["total"] = total_electricity_cost/total_electricity_produced if total_electricity_produced > 0 else float('inf')
 
    return None


def get_total_costs(tech_instances, number_of_days):
    return calculate_total_anual_costs(tech_instances)
    # return {"TAC": calculate_total_anual_costs(tech_instances), "LCOE": calculate_levelized_cost_of_energy(tech_instances, number_of_days)}


def calculate_CO2_emissions(tech_instances):

    # Work in Progress...
    # Calculate emissions from fossil fuels at import from the Supply Class / What about lifecycle emissions?
    # CO2 intensity for technologies defined in tech dict
    #
    # Do not double count energy from storage technologies

    co2_emissions = {}
    for tech in tech_instances:
        co2_emissions[tech] = tech_instances[tech].get_co2_emissions()
    
    return co2_emissions