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


def annuity_factor(lifetime_years, interest_rate):
    if interest_rate == 0:
        return 1 / lifetime_years
    else:
        i = interest_rate
        n = lifetime_years
        af = i/(1 - (1 + i) ** -n)
        
        return af 


def calculate_total_anual_costs(tech_instances):
    total_anual_costs = {"heat": {}, "electricity": {}}
    
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
            tac = annualized_capex + opex + energy_costs - energy_revenue

            
            output_carrier = get_var(tech_instances[tech], "_output_carrier", "output_carrier", default=_MISSING)
            if output_carrier[0] == "h":
                total_anual_costs["heat"][tech] = tac
            elif output_carrier[0] == "e":
                total_anual_costs["electricity"][tech] = tac
            
    
    total_anual_costs["heat"]["total"] = sum(total_anual_costs["heat"].values())
    total_anual_costs["electricity"]["total"] = sum(total_anual_costs["electricity"].values())
    return total_anual_costs

def calculate_levelized_cost_of_energy(tech_instances, time_horizon):
    lcoe = {"heat": {}, "electricity": {}}
    for tech in tech_instances:
        cost = 0
        energy_produced = 0
        if tech != "solar_pvrooftop" and tech != "solarthermal_rooftop" and tech != "pile_of_berries":  # !!! this should be adapted to the actual technologies included in the model
            if tech != "grid_supply":
                for year in range(time_horizon):
                    cost += (1/(1 + tech_instances[tech]._interest_rate) ** year)*( tech_instances[tech].get_total_capex() + tech_instances[tech].get_total_maintenance() + tech_instances[tech].get_energy_costs())
                    energy_produced = (1/(1 + tech_instances[tech]._interest_rate) ** year) * tech_instances[tech]._v_h.sum()  
        output_carrier = get_var(tech_instances[tech], "_output_carrier", "output_carrier", default=_MISSING)
        if output_carrier[0] == "h":
            lcoe["heat"][tech] = cost / energy_produced if energy_produced > 0 else float('inf')
        elif output_carrier[0] == "e":
            lcoe["electricity"][tech] = cost / energy_produced if energy_produced > 0 else float('inf')
        

    lcoe["heat"]["total"] = sum(lcoe["heat"].values())
    lcoe["electricity"]["total"] = sum(lcoe["electricity"].values())    
    return lcoe


def get_total_costs(tech_instances, time_horizon):
    return {"TAC": calculate_total_anual_costs(tech_instances), "LCOE": calculate_levelized_cost_of_energy(tech_instances, time_horizon)}

