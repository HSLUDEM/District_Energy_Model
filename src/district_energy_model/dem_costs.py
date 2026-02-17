# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 14:12:26 2024

@author: UeliSchilt
"""
from district_energy_model import dem_demand
from district_energy_model.input_files import inputs as inp

oil_density = 0.85  # kg/L
fossil_heating_capacity = 0
eh_heating_capacity = 0
number_of_years = 0




def annuity_factor(lifetime_years, interest_rate):
    if interest_rate == 0:
        return 1 / lifetime_years
    else:
        i = interest_rate
        n = lifetime_years
        af = i/(1 - (1 + i) ** -n)
        
        return af 


def calculate_total_anual_costs(tech_instances, df_meta):
    total_anual_costs = {}
    
    for tech in tech_instances:
        capex = 0
        energy_revenue = 0
        if tech != "solar_pvrooftop" and tech != "solarthermal_rooftop" and tech != "pile_of_berries":  # !!! this should be adapted to the actual technologies included in the model
            installed_capacity = 1000  # !!! this should be calculated based on the demand values and the installed capacity of the technology

            #capex = tech_instances[tech]._capex*installed_capacity
            if tech != "grid_supply":
                opex = tech_instances[tech]._maintenance_cost*installed_capacity
                energy_revenue = tech_instances[tech].get_energy_revenue()
            else:
                opex = 0
            energy_costs = tech_instances[tech].get_energy_costs()
            

            annualized_capex = capex*annuity_factor(tech_instances[tech]._lifetime, tech_instances[tech]._interest_rate)

            tac = annualized_capex + opex + energy_costs - energy_revenue
            total_anual_costs[tech] = tac
    
    return total_anual_costs

# def calculate_levelized_cost_of_energy(tech_instances, time_horizon):
#     lcoe = {}
#     for tech in tech_instances:
#         cost = 0
#         for year in range(time_horizon):
#             cost += (1/(1 + tech._interest_rate) ** year) * (tech.get_total_capex() + tech.get_total_maintenance() + tech.get_energy_costs())
#             energy_produced = (1/(1 + tech._interest_rate) ** year) * tech.get_v_h()
#         lcoe[tech._name] = cost / energy_produced if energy_produced > 0 else float('inf')





