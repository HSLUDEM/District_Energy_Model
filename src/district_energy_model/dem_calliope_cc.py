# -*- coding: utf-8 -*-
"""
Created on Fri Aug 22 16:58:21 2025

@author: UeliSchilt
"""

"""
Calliope Custom Constraints (CC).

See: https://calliope.readthedocs.io/en/stable/user/advanced_constraints.html#user-defined-custom-constraints

"""

from pyomo.environ import ConcreteModel, Var, Binary
import pyomo.core as po
from calliope.backend.pyomo.util import get_param
import numpy as np

from district_energy_model import dem_constants as C


def tes_sites_lt_no_conversion_without_charging_constraint(model, ts_len, sites_list):
    #This constraint tries to ensure that the TES devices are not misused to convert 
    # ht heat to lt heat and then use a heat pump directly (i.e. no abuse of heat pumplt)
    # as electric boiler

    for site_entry in sites_list:

        if site_entry['rel_size_t_levels']['ltlt'] > 0:
                
            constraint_name = site_entry['name']+'_'+'ltlt_loading_constraint'
            constraint_sets = ['timesteps']
            

            
            def ltlt_loading_constraint_rule(backend_model, timestep):

                charging_current = backend_model.carrier_con['X1::tes_site_'
                                                                +site_entry['name']+'_ltlt::heat_tes_site_'
                                                                +site_entry['name']+'_ltlt', timestep]
                av_current_for_charging = 0
                if site_entry['connected_techs']['lt']: # the conversion from heatlt only exists with connected lt techs
                    av_current_for_charging += backend_model.carrier_prod['X1::conv_'
                                                                            +site_entry['name']+'_heatlt_to_heat_tes_site_'
                                                                            +site_entry['name']+'_ltlt::heat_tes_site_'
                                                                            +site_entry['name']+'_ltlt', timestep]
                av_current_for_charging += backend_model.carrier_prod['X1::conv_'
                                                                        +site_entry['name']+'_htht_to_'
                                                                        +site_entry['name']+'_ltlt::heat_tes_site_'
                                                                        +site_entry['name']+'_ltlt', timestep]
                av_current_for_charging += backend_model.carrier_prod['X1::conv_'
                                                                        +site_entry['name']+'_htlt_to_'
                                                                        +site_entry['name']+'_ltlt::heat_tes_site_'
                                                                        +site_entry['name']+'_ltlt', timestep]
                return -charging_current == av_current_for_charging
                    
            model.backend.add_constraint(
                constraint_name,
                constraint_sets,
                ltlt_loading_constraint_rule
                )
            

        if site_entry['rel_size_t_levels']['htlt'] > 0:

                
            constraint_name = site_entry['name']+'_'+'htlt_loading_constraint'
            constraint_sets = ['timesteps']
            

            
            def ltlt_loading_constraint_rule(backend_model, timestep):

                charging_current = backend_model.carrier_con['X1::tes_site_'+
                                                                site_entry['name']+'_htlt::heat_tes_site_'+
                                                                site_entry['name']+'_htlt', timestep]
                if site_entry['rel_size_t_levels']['ltlt'] > 0:
                    # Heat from the ht techs on the htlt carrier charges the htlt level or, via the conversion, the ltlt level
                    # (carrier_con is negative for both):
                    charging_current += backend_model.carrier_con['X1::conv_'+
                                                                site_entry['name']+'_htlt_to_'+
                                                                site_entry['name']+'_ltlt::heat_tes_site_'+
                                                                site_entry['name']+'_htlt', timestep]
                
                av_current_for_charging = sum([backend_model.carrier_prod['X1::conv_'
                                                                            +site_entry['name']+'_heat_'
                                                                            +shortname_of_tech+'_to_heat_tes_site_'
                                                                            +site_entry['name']+'_htlt::heat_tes_site_'
                                                                            +site_entry['name']+'_htlt', timestep] 
                                                                            for shortname_of_tech in site_entry['connected_techs']['ht']])
                return -charging_current == av_current_for_charging
            
                    
            model.backend.add_constraint(
                constraint_name,
                constraint_sets,
                ltlt_loading_constraint_rule
                )


    return model



def tes_sites_minimum_size_constraints(model, ts_len, sites_list, energy_scaling_factor): #implements size constraints on the TES devices
    #Ensures minimum size (needs additonal variable, which is binary)


    constraints_to_generate_noninteger = []
    constraints_to_generate_integer = []

    for i in range(len(sites_list)):

        flag = True

        site_entry = sites_list[i]

        entries = ['htht', 'htlt', 'ltlt']

        for level in entries:

            if (site_entry['rel_size_t_levels'][level] > 0):
                
                if (site_entry['capacity_kWh_min'] > 0) and flag:
                    constraints_to_generate_integer.append({
                        'sitestr': 'tes_site_'+site_entry['name']+'_'+level,
                        'min': site_entry['capacity_kWh_min']*site_entry['rel_size_t_levels'][level],
                        'max': site_entry['capacity_kWh_max']*site_entry['rel_size_t_levels'][level],
                        'force_deployment': site_entry['force_deployment']
                        })
                    flag = False
                else:
                    constraints_to_generate_noninteger.append({
                        'sitestr': 'tes_site_'+site_entry['name']+'_'+level,
                        'max': site_entry['capacity_kWh_max']*site_entry['rel_size_t_levels'][level],
                        })
    

    for i in range(len(constraints_to_generate_integer)):

    

        constraint_dict = constraints_to_generate_integer[i]



        constraint_name_max = 'tes_sites_size_constraint_tes_site_'+constraint_dict['sitestr']+'_max'
        constraint_name_min = 'tes_sites_size_constraint_tes_site_'+constraint_dict['sitestr']+'_min'
        constraint_name_forced_deployment = 'tes_sites_size_constraint_tes_site_'+constraint_dict['sitestr']+'_forced_deployment'
        varname_binary = 'tes_sites_size_constraint_tes_site_'+constraint_dict['sitestr']+'_binaryvar'
        constraint_sets = ['loc_techs_store']

        if model._backend_model.component(varname_binary) is None:
            model._backend_model.add_component(varname_binary, Var(model._backend_model.loc_techs_store, within=Binary))


        def tes_sites_size_constraint_max_rule(backend_model, loc_tech):


            cap = backend_model.storage_cap['X1::'+constraint_dict['sitestr']]

            binary_var = backend_model.component(varname_binary)  

            return cap <= constraint_dict['max']*binary_var[loc_tech] / energy_scaling_factor
        
        def tes_sites_size_constraint_min_rule(backend_model, loc_tech):

            cap = backend_model.storage_cap['X1::'+constraint_dict['sitestr']]

            binary_var = backend_model.component(varname_binary)  

            return cap >= constraint_dict['min']*binary_var[loc_tech]  / energy_scaling_factor


        model.backend.add_constraint(
            constraint_name_max,
            constraint_sets,
            tes_sites_size_constraint_max_rule
            )
        model.backend.add_constraint(
            constraint_name_min,
            constraint_sets,
            tes_sites_size_constraint_min_rule
            )
        
        if constraint_dict['force_deployment']:
                
            def tes_sites_forced_deployment_rule(backend_model, loc_tech):

                binary_var = backend_model.component(varname_binary)  

                return 1 == binary_var[loc_tech] 

            model.backend.add_constraint(
                constraint_name_forced_deployment,
                constraint_sets,
                tes_sites_forced_deployment_rule
                )



    for i in range(len(constraints_to_generate_noninteger)):
                    
        constraint_dict = constraints_to_generate_noninteger[i]

        constraint_name = 'tes_sites_size_constraint_tes_site_'+constraint_dict['sitestr']
        constraint_sets = ['loc_techs_store']

        def tes_sites_size_constraint_rule(backend_model, loc_tech):

            cap = backend_model.storage_cap['X1::'+constraint_dict['sitestr']]

            return cap <= constraint_dict['max'] / energy_scaling_factor
        
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            tes_sites_size_constraint_rule
            )

    
    return model


def tes_sites_exclusion_constraint(model, ts_len, sites_list):

    exclusion_group_constraints_to_generate = {}
    

    for i in range(len(sites_list)):

        flag = True

        site_entry = sites_list[i]

        if site_entry['capacity_kWh_min'] ==0 and site_entry['exclusion_group'] != None:
            raise ValueError("TES_Site exclusion constraint can only be implemented if a minimum size is given. Please remove the Exclusion_group parameter or define a minimum size.")

        entries = ['htht', 'htlt', 'ltlt']

        for level in entries:

            if (site_entry['rel_size_t_levels'][level] > 0):
                
                if (site_entry['capacity_kWh_min'] > 0) and flag:
                    
                    if site_entry['exclusion_group'] != None:
                        if not site_entry['exclusion_group'] in exclusion_group_constraints_to_generate.keys():
                            exclusion_group_constraints_to_generate[site_entry['exclusion_group']] = []
                        
                        exclusion_group_constraints_to_generate[site_entry['exclusion_group']].append('tes_site_'+site_entry['name']+'_'+level)

                    flag = False
                else:
                    ...

    for k in exclusion_group_constraints_to_generate.keys():

        constraint_name = 'tes_sites_exclusion_constraint_'+k
        constraint_sets = ['loc_techs_store']

        def tes_sites_exclusion_rule(backend_model, loc_tech):

            val_to_bound = sum([backend_model.component('tes_sites_size_constraint_tes_site_'+x+'_binaryvar')[loc_tech] for x in exclusion_group_constraints_to_generate[k]])

            return val_to_bound <= 1

        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            tes_sites_exclusion_rule
            )

    return model

def tes_sites_minimum_size_cost(model, monetary_weight, ts_len, sites_list, energy_scaling_factor): 

    #This function applies a binary cost to devices with minimum size
    #i.e. if a site has a minimum size, for all devices that are above this minimum size, a given capex is applied

    integer_size = []

    bm = model._backend_model
    active_objs = list(bm.component_data_objects(po.Objective, active = True))
    assert len(active_objs) == 1
    obj = active_objs[0]


    for i in range(len(sites_list)):

        flag = True
        site_entry = sites_list[i]

        entries = ['htht', 'htlt', 'ltlt']

        for level in entries:

            if (site_entry['rel_size_t_levels'][level] > 0):
                

                if site_entry['capacity_kWh_min'] > 0 and flag:
                    integer_size.append({
                        'sitestr': 'tes_site_'+site_entry['name']+'_'+level,
                        'capex_base': site_entry['capex_base'],
                        'maintenance_cost_base': site_entry['maintenance_cost_base'],
                        'interest_rate': site_entry['interest_rate'],
                        'lifetime': site_entry['lifetime']
                        })
                    
                    flag = False

    

    for i in range(len(integer_size)):
        
        value_dict = integer_size[i]

        varname_binary = 'tes_sites_size_constraint_tes_site_'+value_dict['sitestr']+'_binaryvar'


        interest_rate = value_dict['interest_rate']
        lifetime=  value_dict['lifetime']

        annuity_factor = ((((1+interest_rate)**lifetime) * interest_rate)/(((1+interest_rate)**lifetime) - 1) 
                          if interest_rate > 0 
                          else 1.0/lifetime)

        binary_var = bm.component(varname_binary)


        # Fixed costs per site [CHF], independent of the (scaled) capacity,
        # i.e. not multiplied with the energy scaling factor:
        obj.expr = obj.expr + value_dict['capex_base'] * annuity_factor * binary_var['X1::'+value_dict['sitestr']] * (ts_len/(365*24)) * monetary_weight
        obj.expr = obj.expr + value_dict['maintenance_cost_base'] * binary_var['X1::'+value_dict['sitestr']] * (ts_len/(365*24)) * monetary_weight
        
    active_objs[0] = obj

    return model


def tes_sites_size_ratios_constraints(model, ts_len, sites_list): #implements size constraints on the TES devices
    #Ensures that C_ltlt / alpha_ltlt  = C_htlt / alpha_htlt  = C_htht / alpha_htht (for those with alpha != 0)

    for i in range(len(sites_list)):
        site_entry = sites_list[i]

        combinations = [['htht', 'htlt'], ['htht', 'ltlt'], ['htlt', 'ltlt']]

        for [high_T_level, low_T_level] in combinations:

            if ((site_entry['rel_size_t_levels'][high_T_level] > 0) 
                and (site_entry['rel_size_t_levels'][low_T_level] > 0)):

                constraint_name = 'tes_sites_size_ratios_constraint_tes_site_'+site_entry['name']+'_'+high_T_level+'_to_'+low_T_level
                constraint_sets = []

                def tes_sites_size_ratios_constraint_rule(backend_model):

                    high_T_val = (backend_model.storage_cap['X1::tes_site_'+site_entry['name']+'_'+high_T_level] 
                                  / site_entry['rel_size_t_levels'][high_T_level])
                    low_T_val = (backend_model.storage_cap['X1::tes_site_'+site_entry['name']+'_'+low_T_level] 
                                 / site_entry['rel_size_t_levels'][low_T_level])

                    return high_T_val == low_T_val
                
                model.backend.add_constraint(
                    constraint_name,
                    constraint_sets,
                    tes_sites_size_ratios_constraint_rule
                    )

    
    return model

def tes_sites_charge_constraints(model, ts_len, sites_list):
    #Ensures that the TES charging and discharging respects the stratification and temperature order
        
    for i_site in range(len(sites_list)):
        site_entry = sites_list[i_site]

        combinations = [['htht', 'htlt'], ['htht', 'ltlt'], ['htlt', 'ltlt']]

        for [high_T_level, low_T_level] in combinations:

            if ((site_entry['rel_size_t_levels'][high_T_level] > 0) 
                and (site_entry['rel_size_t_levels'][low_T_level] > 0)):

                constraint_name = 'tes_sites_site_charge_constraint_tes_site_'+site_entry['name']+'_'+high_T_level+'_to_'+low_T_level
                constraint_sets = ['timesteps']

                def tes_sites_charge_constraint_rule(backend_model, timestep):
                    
                    high_T_val = (backend_model.storage['X1::tes_site_'+site_entry['name']+'_'+high_T_level, timestep] 
                                / site_entry['rel_size_t_levels'][high_T_level])
                    low_T_val = (backend_model.storage['X1::tes_site_'+site_entry['name']+'_'+low_T_level, timestep] 
                                / site_entry['rel_size_t_levels'][low_T_level])

                    return high_T_val <= low_T_val
                
                model.backend.add_constraint(
                    constraint_name,
                    constraint_sets,
                    tes_sites_charge_constraint_rule
                    )

    
    return model


def ev_flexibility_constraints(model, ts_len, n_days, energy_demand, energy_scaling_factor):
    """
    

    Parameters
    ----------
    model : Callipe model
        Calliope model instance.
    ts_len : int
        Total number of timesteps.
    n_days : int
        Total number of days.
    energy_demand : class instance
        Instance of EnergyDemand class.

    Returns
    -------
    Calliope model
        Calliope model instance.

    """    
    # Constraint: Daily EV electricity demand
    # -----------------------------------------
    
    for day in range(n_days): # create one constraint per day:
        
        constraint_name = f'd_e_ev_dy_constraint_{day}'        
        constraint_sets = []
        
        def d_e_ev_dy_constraint_rule(backend_model):
            
            ts = backend_model.timesteps # retrieve timesteps            

            tmp_sum = 0 # daily sum
            hr = 0 # hour of the day
            while hr < 24:
                i = day*24 + hr # absolute timestep
                tmp_sum += (
                    backend_model.carrier_con['X1::demand_electricity_ev_pd::electricity', ts.at(i + 1)] # Pyomo Sets are 1-indexed
                    + backend_model.carrier_con['X1::demand_electricity_ev_delta::electricity', ts.at(i + 1)]
                    )
                hr+=1
            
            # Daily EV demand must match daily base profile (cp) demand:
            return tmp_sum == -energy_demand.get_d_e_ev_cp_dy()[day] /energy_scaling_factor
                 
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            d_e_ev_dy_constraint_rule
            )

    # Constraint: Daily EV flexible demand
    # --------------------------------------
    
    # Absoulute value linearisation for flexibility (deviation from base profile):
        
    for i in range(ts_len):

        constraint_name = f'ev_flex_var_constraint_{i}'
        constraint_sets = []
        
        def ev_flex_var_constraint_rule(backend_model):
            
            ts = backend_model.timesteps
            
            # Variable to limit energy shift from base profile (cp) in positive direction:
            pos_delta_i_max = (
                backend_model.carrier_prod['X1::flexibility_ev::flexible_electricity', ts.at(i + 1)] # Pyomo Sets are 1-indexed
                )
            
            d_e_ev_i = (
                backend_model.carrier_con['X1::demand_electricity_ev_pd::electricity', ts.at(i + 1)] # Pyomo Sets are 1-indexed
                + backend_model.carrier_con['X1::demand_electricity_ev_delta::electricity', ts.at(i + 1)]
                )
            
            d_e_ev_cp_i = -energy_demand.get_d_e_ev_cp()[i] / energy_scaling_factor
            
            delta_i = d_e_ev_i - d_e_ev_cp_i
            
            return pos_delta_i_max >= delta_i
        
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            ev_flex_var_constraint_rule
            )
        
        constraint_name = f'ev_flex_pos_constraint_{i}'
        constraint_sets = []
        
        def ev_flex_pos_constraint_rule(backend_model):
            
            ts = backend_model.timesteps
            
            # Variable to limit energy shift from base profile (cp) in positive direction:
            pos_delta_i_max = (
                backend_model.carrier_prod['X1::flexibility_ev::flexible_electricity', ts.at(i + 1)] # Pyomo Sets are 1-indexed
                )
            
            return pos_delta_i_max >= 0.0
        
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            ev_flex_pos_constraint_rule
            )

    for day in range(n_days): # create one constraint per day:
        
        constraint_name = f'f_e_ev_dy_constraint_{day}'        
        constraint_sets = []
        
        def f_e_ev_dy_constraint_rule(backend_model):
            
            ts = backend_model.timesteps # retrieve timesteps            

            pos_delta_i_max_sum = 0 # daily sum of deviation in positive direction
            hr = 0 # hour of the day
            while hr < 24:
                i = day*24 + hr # absolute timestep
                
                # Variable to limit energy shift from base profile (cp) in positive direction:
                pos_delta_i_max = (
                    backend_model.carrier_prod['X1::flexibility_ev::flexible_electricity', ts.at(i + 1)] # Pyomo Sets are 1-indexed
                    )
                
                pos_delta_i_max_sum += pos_delta_i_max
                
                hr+=1
                
            f_e_ev_pot_dy = energy_demand.get_f_e_ev_pot_dy()[day] / energy_scaling_factor
            
            # Daily EV flexible demand limitation:
            return pos_delta_i_max_sum <= f_e_ev_pot_dy
                 
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            f_e_ev_dy_constraint_rule
            )
    
    return model

def building_inertia_flex_constraints(
        model,
        ts_len,
        energy_demand,
        building_inertia_flex,
        energy_scaling_factor,
        fixed_share_techs
        ):
    """
    Custom constraint: ensures that the cummulative annual heat demand in a
    flexibility scenario is equal or larger than the cummulative annual base demand.
    Avoids permanently lowering setpoint temperature as an optimal solution.

    Parameters
    ----------
    model : Callipe model
        Calliope model instance.
    ts_len : int
        Total number of timesteps.
    energy_demand : class instance
        Instance of EnergyDemand class.
    building_inertia_flex: class instance
        Instance of BuildingInertiaFlexibility class.

    Returns
    -------
    Calliope model
        Calliope model instance.

    """        
    
    flex_systems = building_inertia_flex.get_flex_systems()    
    E_vs_tot_max = building_inertia_flex.get_E_vs_tot_max()
    E_vs_tot = building_inertia_flex.get_E_vs_tot()
    r_tot = building_inertia_flex.get_r_tot()
    r_ts = building_inertia_flex.get_r_ts() # hourly loss rate of the virtual storages
    mcr_vs = building_inertia_flex.get_mcr_vs()
    
    # d_h = energy_demand.get_d_h()
    d_h_s = energy_demand.get_d_h_s()
    d_h_flex_ll = energy_demand.get_d_h_flex_ll()
    d_h_flex_ul = energy_demand.get_d_h_flex_ul()
    # d_h_s_flex_ll = energy_demand.get_d_h_s_flex_ll()
    flex_flag = energy_demand.get_flex_flag()
    vs_drain_flag = energy_demand.get_vs_drain_flag()
    
    # =========================================================================
    # Create factory functions for constraint rules:
    # ---------------------------------------------
    
    def make_flex_capacity_constraint_rule():
        
        def flex_capacity_constraint_rule(backend_model):
            """
            The sum of capacities of all virtual storages must equal the total
            flexible capacity (E_vs_tot).
            """
            
            cap_sum = 0.0
            for key_, acr_ in flex_systems.items():
                # key: full tech name (e.g., 'heat_pump', 'district_heating')
                # acr: acronym (e.g., 'hp', 'dh')
                cap_tech = backend_model.storage_cap[f'X1::virtual_storage_flex_{acr_}']*energy_scaling_factor
                cap_sum += cap_tech
                
            # E_vs_tot = building_inertia_flex.get_E_vs_tot()
            
            return cap_sum == E_vs_tot
        
        return flex_capacity_constraint_rule
    
    def make_d_h_flex_upper_limit_constraint_rule(ts_i):
        
        def d_h_flex_upper_limit_constraint_rule(backend_model):
            """
            The flexible demand must be smaller or equal to the upper
            flexibility boundary at any given timestep.
            """
            
            ts = backend_model.timesteps # retrieve timesteps
            
            q_h_vs_tot_i = 0.0
            for key_, acr_ in flex_systems.items():
                # key: full tech name (e.g., 'heat_pump', 'district_heating')
                # acr: acronym (e.g., 'hp', 'dh')
                q_h_vs_tech_i = (
                    backend_model.
                    storage[
                        f'X1::virtual_storage_flex_{acr_}',
                        ts.at(ts_i + 1) # Pyomo is 1-indexed
                        ]*energy_scaling_factor
                    )
                q_h_vs_tot_i += q_h_vs_tech_i
                
            if r_ts[ts_i] == 0:
                # No space heating demand: no loss (the virtual storage is
                # empty, see q_h_vs_low_demand_constraint); no constraint:
                return po.Constraint.Skip

            d_h_flex_i = d_h_flex_ll[ts_i] + q_h_vs_tot_i*r_ts[ts_i]

            return d_h_flex_i <= d_h_flex_ul[ts_i]
        
        return d_h_flex_upper_limit_constraint_rule
    
    def make_q_h_vs_constraint_rule(acr):
        
        def q_h_vs_constraint_rule(backend_model):
            """
            Rule: On average, each virtual storage must be half full (which
            is the neutral (i.e., nominal) state without over- or underheating).
            The average is weighted by the hourly loss rate r_t and uses the
            storage level of the previous timestep, from which the loss of
            timestep t is computed (storage balance):
                sum_t r_t*q_(t-1) >= 0.5*E_vs*sum_t r_t
            At half full, the loss r_t*0.5*E_vs equals the reduction of the
            lower limit of the heat demand (min(delta, d_h_s)). Summed over
            all virtual storages, the heat supplied minus the heat demand
            without flexibility is sum_t r_t*(q_(t-1) - 0.5*E_vs_tot), so
            this rule ensures that at least the same amount of heat is
            delivered as without flexibility. Timesteps without space heating
            demand have r_t = 0 and are not included.
            """
            ts = backend_model.timesteps # retrieve timesteps
            loc_tech = f'X1::virtual_storage_flex_{acr}'
            E_vs_tech = backend_model.storage_cap[loc_tech]*energy_scaling_factor

            lhs = 0.0 # [kWh] loss-rate-weighted sum of storage levels
            r_sum = 0.0 # [-] sum of loss rates
            for ts_i_ in range(ts_len):
                if r_ts[ts_i_] == 0:
                    continue
                if ts_i_ > 0:
                    q_prev = backend_model.storage[loc_tech, ts.at(ts_i_)]*energy_scaling_factor # Pyomo Sets are 1-indexed
                elif cyclic_storage:
                    q_prev = backend_model.storage[loc_tech, ts.at(-1)]*energy_scaling_factor
                else:
                    q_prev = get_param(backend_model, 'storage_initial', loc_tech)*E_vs_tech
                lhs += r_ts[ts_i_]*q_prev
                r_sum += r_ts[ts_i_]
                   
            return lhs >= 0.5*E_vs_tech*r_sum
        
        return q_h_vs_constraint_rule
    
    def make_q_h_vs_low_demand_constraint_rule(ts_i):
        
        def q_h_vs_low_demand_constraint_rule(backend_model):
            """
            Where the space heating demand (d_h_s) is 0, the storage level must
            be 0. when there. This decouples the space heating demand
            from DHW, because building inertia cannot be used for DHW heating.
            """
            ts = backend_model.timesteps # retrieve timesteps
    
            q_h_vs_tot_i = 0 # [kWh] sum of flexible demand

            for key_, acr_ in flex_systems.items():
            # Total virtual storage capacity:
                q_h_vs_tot_i += (
                    backend_model.
                    storage[
                        f'X1::virtual_storage_flex_{acr_}',
                        ts.at(ts_i + 1) # Pyomo is 1-indexed
                        ]*energy_scaling_factor
                    )
            
            # lhs = q_h_vs_tot_i*r_tot
            # rhs = d_h_s[ts_i]
            
            return q_h_vs_tot_i == 0.0
            # return q_h_vs_tot_i == 0.5*E_vs_tot
            # return lhs <= rhs
        
        return q_h_vs_low_demand_constraint_rule
    
    # def make_virtual_storage_discharge_constraint_rule(acr):
        
    #     def virtual_storage_discharge_constraint_rule(backend_model):
            
    #         ts = backend_model.timesteps # retrieve timesteps
            
    #         v_h_vs_sum = sum(
    #             backend_model.carrier_prod[f"X1::virtual_storage_flex_{acr}::heat_vs_{acr}", t]
    #             for t in ts
    #             )*energy_scaling_factor
            
    #         return v_h_vs_sum == 0.0
        
    #     return virtual_storage_discharge_constraint_rule
    
    def make_q_h_vs_drain_constraint_rule(ts_i):
        
        def q_h_vs_drain_constraint_rule(backend_model):
            """
            If there is space heating demand, the virtual storage drain
            must be empty.
            """
            
            ts = backend_model.timesteps # retrieve timesteps
            
            q_h_vs_drain_tot_i = 0.0
            
            for key_, acr_ in flex_systems.items():
            # Total virtual storage capacity:
                q_h_vs_drain_tot_i += (
                    backend_model.
                    storage[
                        f'X1::virtual_storage_drain_{acr_}',
                        ts.at(ts_i + 1) # Pyomo is 1-indexed
                        ]*energy_scaling_factor
                    )
            
            if vs_drain_flag[ts_i] == 'idle' and d_h_s[ts_i] > 0:
                return q_h_vs_drain_tot_i == 0.0
            else:
                return q_h_vs_drain_tot_i <= E_vs_tot
        
        return q_h_vs_drain_constraint_rule                                
    
    def make_virtual_storage_discharge_constraint_rule(ts_i, acr):
        
        def virtual_storage_discharge_constraint_rule(backend_model):
            """
            Discharging of the virtual storage is only possible for moving
            heat to the virtual storage drain.
            """
            
            ts = backend_model.timesteps # retrieve timesteps
    
            v_h_vs_tech_i = backend_model.carrier_prod[
                f"X1::virtual_storage_flex_{acr}::heat_vs_{acr}",
                ts.at(ts_i + 1)
                ]*energy_scaling_factor
            
            u_h_vs_drain_tech_i = -backend_model.carrier_con[
                f"X1::virtual_storage_drain_{acr}::heat_vs_{acr}",
                ts.at(ts_i + 1)
                ]*energy_scaling_factor
            
            if vs_drain_flag[ts_i] in ['idle', 'empty']:
                return v_h_vs_tech_i == 0.0
            elif vs_drain_flag[ts_i] == 'fill':
                # return v_h_vs_tech_i <= E_vs_tot
                return v_h_vs_tech_i == u_h_vs_drain_tech_i
            else:
                raise ValueError(
                    "Value in vs_drain_flag must be 'idle', 'fill', or 'empty'"
                    )
        
        return virtual_storage_discharge_constraint_rule
    
    def make_virtual_storage_charge_constraint_rule(ts_i, acr):
        
        def virtual_storage_charge_constraint_rule(backend_model):
            """
            Set the max. charge rate of the virtual storage for each time step.
            The max. charge rate is either based on heating system (hs)
            capacity or loss rate (lr).
            """
            
            ts = backend_model.timesteps # retrieve timesteps
    
            u_h_vs_tech_i = -backend_model.carrier_con[
                f"X1::virtual_storage_flex_{acr}::heat_vs_{acr}",
                ts.at(ts_i + 1)
                ]*energy_scaling_factor
            
            # q_h_vs_drain_i = (
            #     backend_model
            #     .storage[f'X1::virtual_storage_drain_{acr}', ts.at(ts_i + 1)] # Pyomo Sets are 1-indexed
            #     *energy_scaling_factor 
            #     )
            
            v_h_vs_drain_tech_i = backend_model.carrier_prod[
                f"X1::virtual_storage_drain_{acr}::heat_vs_{acr}",
                ts.at(ts_i + 1)
                ]*energy_scaling_factor
            
            E_vs_tech_i = backend_model.storage_cap[
                f'X1::virtual_storage_flex_{acr}'
                ]*energy_scaling_factor
            
            # max. charge rate (mcr)
            if mcr_vs == 'hs': # based on heating system (hs) capacity
                mcr = 1.0
            elif mcr_vs == 'lr': # based on loss rate (lr)
                mcr = r_tot
            else:
                raise ValueError("mcr_vs must be 'hs' or 'lr'.")
            
            # if vs_drain_flag[ts_i] in ['idle', 'fill']:
            #     return u_h_vs_tech_i <= E_vs_tech_i*mcr
            if vs_drain_flag[ts_i] == 'idle':
                return u_h_vs_tech_i <= E_vs_tech_i*mcr
            elif vs_drain_flag[ts_i] == 'fill':
                return u_h_vs_tech_i == 0.0 # when the drain fills up, the vs can only be discharged
            elif vs_drain_flag[ts_i] == 'empty':
                # recharging from drain:
                return u_h_vs_tech_i <= v_h_vs_drain_tech_i + E_vs_tech_i*mcr
                # return u_h_vs_tech_i <= q_h_vs_drain_i*1.0 + E_vs_tech_i*mcr
            else:
                raise ValueError(
                    "Value in vs_drain_flag must be 'idle', 'fill', or 'empty'"
                    )
        
        return virtual_storage_charge_constraint_rule
    
    def make_virtual_storage_drain_charge_constraint_rule(ts_i, acr):
        
        def virtual_storage_drain_charge_constraint_rule(backend_model):
            """
            For each timestep, define if charging of the drain is allowed. It
            is only allowed when heat needs to be shifted from the virtual
            storage to the drain, which is when space heating demand goes to 0.
            """
            
            ts = backend_model.timesteps # retrieve timesteps
    
            u_h_vs_drain_tech_i = -backend_model.carrier_con[
                f"X1::virtual_storage_drain_{acr}::heat_vs_{acr}",
                ts.at(ts_i + 1)
                ]*energy_scaling_factor
            
            if vs_drain_flag[ts_i] in ['idle', 'empty']:
                return u_h_vs_drain_tech_i == 0.0
            elif vs_drain_flag[ts_i] == 'fill':
                return u_h_vs_drain_tech_i <= E_vs_tot
            else:
                raise ValueError(
                    "Value in vs_drain_flag must be 'idle', 'fill', or 'empty'"
                    )
        
        return virtual_storage_drain_charge_constraint_rule
    
    def make_virtual_storage_drain_discharge_constraint_rule(ts_i, acr):
        
        def virtual_storage_drain_discharge_constraint_rule(backend_model):
            """
            For each timestep, define if discharging of the drain is allowed.
            It is only allowed when heat needs to be shifted from the drain to
            the virtual storage to the drain, which is when space heating 
            comes back from being 0.
            """
            
            ts = backend_model.timesteps # retrieve timesteps
    
            v_h_vs_drain_tech_i = backend_model.carrier_prod[
                f"X1::virtual_storage_drain_{acr}::heat_vs_{acr}",
                ts.at(ts_i + 1)
                ]*energy_scaling_factor
            
            if vs_drain_flag[ts_i] in ['idle', 'fill']:
                return v_h_vs_drain_tech_i == 0.0
            elif vs_drain_flag[ts_i] == 'empty':
                return v_h_vs_drain_tech_i <= E_vs_tot
            else:
                raise ValueError(
                    "Value in vs_drain_flag must be 'idle', 'fill', or 'empty'"
                    )
        
        return virtual_storage_drain_discharge_constraint_rule
    
    def make_demand_share_constraint_rule(key, acr):
        
        def demand_share_constraint_rule(backend_model):
            """
            Allocate the demand share to the flexibility-enabled techs
            proportionally to their virtual storage capacity.
            """
            
            ts = backend_model.timesteps # retrieve timesteps

            # d_h_flex_ll_sum = energy_demand.get_d_h_flex_ll().sum()
            # E_vs_tot_max = building_inertia_flex.get_E_vs_tot_max()
            d_h_flex_ll_sum = d_h_flex_ll.sum()
            
            # Get the demand this tech is covering:
            if key=='heat_pump':
                v_h_sum = sum(
                    backend_model.carrier_prod['X1::heat_pump_hub::heat', t]
                    for t in ts
                    )*energy_scaling_factor
            elif key=='district_heating':
                # The number of district heating hubs depends on the grid cost
                # categories; without district heating there are none:
                dh_hubs = [
                    loc_tech_carrier
                    for loc_tech_carrier in backend_model.loc_tech_carriers_prod
                    if loc_tech_carrier.startswith('X1::district_heating_hub')
                    and loc_tech_carrier.endswith('::heat')
                    ]
                v_h_sum = sum(
                    backend_model.carrier_prod[loc_tech_carrier, t]
                    for loc_tech_carrier in dh_hubs
                    for t in ts
                    )*energy_scaling_factor
            else:
                msg = (
                    f"Tech {key} has not yet been implemented for demand response"
                    " flexibility."
                    )
                raise NotImplementedError(msg)
            
            E_vs_tech = backend_model.storage_cap[f'X1::virtual_storage_flex_{acr}']*energy_scaling_factor
                
            # lhs = E_vs_tech / E_vs_tot_max
            # rhs = v_h_sum / d_h_flex_ll_sum
            
            lhs = E_vs_tech * d_h_flex_ll_sum
            rhs = v_h_sum * E_vs_tot_max
            
            return lhs <= rhs
        
        return demand_share_constraint_rule
    
    def make_virtual_storage_balance_constraint_rule(ts_i, acr):
        
        def virtual_storage_balance_constraint_rule(backend_model):
            """
            Storage balance of the virtual storage with the hourly loss rate
            r_ts (replaces Calliope's balance_storage_constraint, which only
            supports a constant storage_loss). Same formulation as in
            Calliope 0.6.10 (calliope/backend/pyomo/constraints/
            energy_balance.py, balance_storage_constraint_rule) without
            clustering.
            """
            ts = backend_model.timesteps # retrieve timesteps
            t = ts.at(ts_i + 1) # Pyomo is 1-indexed
            loc_tech = f'X1::virtual_storage_flex_{acr}'
            loc_tech_carrier = f'{loc_tech}::heat_vs_{acr}'
            
            energy_eff = get_param(backend_model, 'energy_eff', (loc_tech, t))
            if po.value(energy_eff) == 0:
                carrier_prod = 0
            else:
                carrier_prod = backend_model.carrier_prod[loc_tech_carrier, t] / energy_eff
            carrier_con = backend_model.carrier_con[loc_tech_carrier, t] * energy_eff
            
            if ts_i == 0 and not cyclic_storage:
                storage_previous_step = (
                    get_param(backend_model, 'storage_initial', loc_tech)
                    * backend_model.storage_cap[loc_tech]
                    )
            else:
                previous_step = ts.at(-1) if ts_i == 0 else ts.at(ts_i)
                time_resolution = po.value(backend_model.timestep_resolution[previous_step])
                storage_previous_step = (
                    (1 - r_ts[ts_i]) ** time_resolution
                    ) * backend_model.storage[loc_tech, previous_step]
            
            return (
                backend_model.storage[loc_tech, t]
                == storage_previous_step - carrier_prod - carrier_con
                )
        
        return virtual_storage_balance_constraint_rule
    
    def make_virtual_storage_initial_constraint_rule(acr):
        
        def virtual_storage_initial_constraint_rule(backend_model):
            """
            Cyclic storage: the storage level carried from the last to the
            first timestep (after the loss of the first timestep) equals the
            initial storage level (replaces Calliope's
            storage_initial_constraint, which uses the constant storage_loss).
            """
            loc_tech = f'X1::virtual_storage_flex_{acr}'
            final_step = backend_model.timesteps.at(-1)
            time_resolution = po.value(backend_model.timestep_resolution[final_step])
            return (
                backend_model.storage[loc_tech, final_step]
                * ((1 - r_ts[0]) ** time_resolution)
                == get_param(backend_model, 'storage_initial', loc_tech)
                * backend_model.storage_cap[loc_tech]
                )
        
        return virtual_storage_initial_constraint_rule
    
    
    # =========================================================================
    # Add constraints to model:
    # ------------------------
    constraint_sets = []
    
    # Hourly loss rate of the virtual storages: Calliope's storage balance
    # (constant storage_loss) is replaced by the custom storage balance with
    # r_ts:
    backend_model_ = model._backend_model
    if hasattr(backend_model_, 'clusters'):
        raise NotImplementedError(
            "Building inertia flexibility is not implemented for clustered "
            "timeseries."
            )
    cyclic_storage = getattr(backend_model_, '__calliope_run_config')['cyclic_storage']
    
    for key, acr in flex_systems.items():
        loc_tech = f'X1::virtual_storage_flex_{acr}'
        for t in backend_model_.timesteps:
            backend_model_.balance_storage_constraint[loc_tech, t].deactivate()
        for ts_i in range(ts_len):
            model.backend.add_constraint(
                f"virtual_storage_balance_{acr}_ts_{ts_i}_constraint",
                constraint_sets,
                make_virtual_storage_balance_constraint_rule(ts_i, acr)
                )
        if (
                cyclic_storage
                and hasattr(backend_model_, 'storage_initial_constraint')
                and loc_tech in backend_model_.storage_initial_constraint
                ):
            backend_model_.storage_initial_constraint[loc_tech].deactivate()
            model.backend.add_constraint(
                f"virtual_storage_initial_{acr}_constraint",
                constraint_sets,
                make_virtual_storage_initial_constraint_rule(acr)
                )
    
    # Single constraints:
    # ------------------    
    constraint_name = 'flex_capacity_constraint'        
    model.backend.add_constraint(
        constraint_name,
        constraint_sets,
        make_flex_capacity_constraint_rule()
        )
    
    # Constraints per tech:
    # --------------------
    for key, acr in flex_systems.items():
        # key: full tech name (e.g., 'heat_pump', 'district_heating')
        # acr: acronym (e.g., 'hp', 'dh')

        constraint_name = f'q_h_vs_{acr}_constraint'        
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            make_q_h_vs_constraint_rule(acr)
            )
      
        # constraint_name = f'virtual_storage_discharge_{acr}_constraint'        
        # model.backend.add_constraint(
        #     constraint_name,
        #     constraint_sets,
        #     make_virtual_storage_discharge_constraint_rule(acr)
        #     )            
    
        constraint_name = f'demand_share_{acr}_constraint'        
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            make_demand_share_constraint_rule(key, acr)
            )
        
        # Constraints per tech and timestep:
        # ---------------------------------
        for ts_i, flag in enumerate(flex_flag):
            
            constraint_name = f"virtual_storage_charge_{acr}_ts_{ts_i}_constraint"
            model.backend.add_constraint(
                constraint_name,
                constraint_sets,
                make_virtual_storage_charge_constraint_rule(ts_i, acr)
                )
            
            constraint_name = f"virtual_storage_discharge_{acr}_ts_{ts_i}_constraint"        
            model.backend.add_constraint(
                constraint_name,
                constraint_sets,
                make_virtual_storage_discharge_constraint_rule(ts_i, acr)
                )
            
            constraint_name = f"virtual_storage_drain_charge_{acr}_ts_{ts_i}_constraint"
            model.backend.add_constraint(
                constraint_name,
                constraint_sets,
                make_virtual_storage_drain_charge_constraint_rule(ts_i, acr)
                )
            
            constraint_name = f"virtual_storage_drain_discharge_{acr}_ts_{ts_i}_constraint"
            model.backend.add_constraint(
                constraint_name,
                constraint_sets,
                make_virtual_storage_drain_discharge_constraint_rule(ts_i, acr)
                )

    # Constraints per timestep:
    # ------------------------
    for ts_i, flag in enumerate(flex_flag):
        
        constraint_name = f"d_h_flex_upper_limit_ts_{ts_i}_constraint"
        model.backend.add_constraint(
                    constraint_name,
                    constraint_sets,
                    make_d_h_flex_upper_limit_constraint_rule(ts_i)
                    )
        
        constraint_name = f"q_h_vs_drain_ts_{ts_i}_constraint"
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            make_q_h_vs_drain_constraint_rule(ts_i)
            )
        
        if flag:
            # Building inertia flexibility can be applied; no constraint required
            pass
        elif flag == False:
            # d_h_s = 0; virtual storage must be empty; constraint required
            
            constraint_name = f'q_h_vs_low_demand_ts_{ts_i}_constraint'
            model.backend.add_constraint(
                constraint_name,
                constraint_sets,
                make_q_h_vs_low_demand_constraint_rule(ts_i)
                )
    
    return model


# Carriers of electricity that can leave the system via carrier_export:
ELECTRICITY_EXPORT_CARRIERS = ('electricity', 'wp_electricity')

def get_electricity_export_flows(backend_model):
    """
    Return the electricity export flows of the Calliope backend model.

    Returns
    -------
    export_ltcs : list of str
        loc::tech::carrier entries of carrier_export (tech-level export).
    grid_export_ltc : str or None
        loc::tech::carrier entry of the grid export tech (carrier_con), if
        present.
    """
    export_ltcs = []
    if hasattr(backend_model, 'loc_tech_carriers_export'):
        export_ltcs = [
            ltc for ltc in backend_model.loc_tech_carriers_export
            if ltc.split('::')[-1] in ELECTRICITY_EXPORT_CARRIERS
            ]
    
    grid_export_ltc = 'Grid_Connection_Node::grid_export::electricity'
    if grid_export_ltc not in backend_model.loc_tech_carriers_con:
        grid_export_ltc = None
    
    return export_ltcs, grid_export_ltc


def national_generation_no_export_constraints(
        model,
        national_techs,
        v_e_nat_pot,
        big_M_export,
        energy_scaling_factor
        ):
    """
    Prevent the export of national generation. In each timestep in which
    national generation is available, a binary variable decides whether
    national generation is used (1) or electricity is exported (0); both at the
    same time is not possible. Without this constraint, national generation
    could cover the local demand while local generation is exported, which
    is an export of national generation (e.g. if its cost or emissions are
    lower than the export revenue or export credit).

        sum_g P_nat,g(t) <= A(t) * b(t)
        E(t) <= M * (1 - b(t))

    P_nat,g: national generation used; A: available national generation;
    E: total electricity export (tech-level export and grid export);
    M: upper bound of the hourly export (big-M); b: binary variable.

    Parameters
    ----------
    model : Calliope model
        Calliope model instance (built with build_only = True).
    national_techs : list of str
        Names of the Calliope techs of the national generators.
    v_e_nat_pot : array
        Total available national generation per timestep [kWh].
    big_M_export : float
        Upper bound of the total electricity export per timestep [kWh].
    energy_scaling_factor : float
        Scaling factor of energy values in the Calliope model.

    Returns
    -------
    Calliope model
        Calliope model instance.
    """
    backend_model = model._backend_model
    
    export_ltcs, grid_export_ltc = get_electricity_export_flows(backend_model)
    
    if len(export_ltcs) == 0 and grid_export_ltc is None:
        # No export possible; no constraint required.
        return model
    
    national_ltcs = [
        f'Grid_Connection_Node::{tech}::electricity' for tech in national_techs
        ]
    
    # Timesteps with available national generation:
    ts_active = [i for i, val in enumerate(v_e_nat_pot) if val > 0]
    
    varname_binary = 'national_generation_use_binary'
    backend_model.add_component(varname_binary, Var(ts_active, within=Binary))
    binary = getattr(backend_model, varname_binary)
    
    big_M = big_M_export / energy_scaling_factor
    
    def make_national_use_constraint_rule(ts_i):
        def national_use_constraint_rule(backend_model):
            ts = backend_model.timesteps.at(ts_i + 1) # Pyomo Sets are 1-indexed
            p_nat = sum(backend_model.carrier_prod[ltc, ts] for ltc in national_ltcs)
            avail = v_e_nat_pot[ts_i] / energy_scaling_factor
            return p_nat <= avail * binary[ts_i]
        return national_use_constraint_rule
    
    def make_no_export_constraint_rule(ts_i):
        def no_export_constraint_rule(backend_model):
            ts = backend_model.timesteps.at(ts_i + 1) # Pyomo Sets are 1-indexed
            export = sum(backend_model.carrier_export[ltc, ts] for ltc in export_ltcs)
            if grid_export_ltc is not None:
                export += -backend_model.carrier_con[grid_export_ltc, ts] # carrier_con is negative
            return export <= big_M * (1 - binary[ts_i])
        return no_export_constraint_rule
    
    for ts_i in ts_active:
        model.backend.add_constraint(
            f'national_generation_use_ts_{ts_i}_constraint',
            [],
            make_national_use_constraint_rule(ts_i)
            )
        model.backend.add_constraint(
            f'national_generation_no_export_ts_{ts_i}_constraint',
            [],
            make_no_export_constraint_rule(ts_i)
            )
    
    return model


def national_generation_before_import_constraints(
        model,
        national_techs,
        v_e_nat_pot,
        big_M_import,
        energy_scaling_factor
        ):
    """
    Use national generation before cross-border import: in each timestep in
    which national generation is available, electricity can only be imported
    from the grid (grid_supply) if all available national generation is used.
    A binary variable decides whether grid import is allowed (1) or not (0):

        sum_g P_nat,g(t) >= A(t) * z(t)
        M(t) <= M_G * z(t)

    P_nat,g: national generation used (P_nat,g <= A_g, i.e. the first
    constraint implies P_nat,g = A_g for all generators if z = 1);
    A: available national generation; M: grid import; M_G: upper bound of the
    hourly grid import (big-M); z: binary variable.

    Parameters
    ----------
    model : Calliope model
        Calliope model instance (built with build_only = True).
    national_techs : list of str
        Names of the Calliope techs of the national generators.
    v_e_nat_pot : array
        Total available national generation per timestep [kWh].
    big_M_import : float
        Upper bound of the grid import per timestep [kWh].
    energy_scaling_factor : float
        Scaling factor of energy values in the Calliope model.

    Returns
    -------
    Calliope model
        Calliope model instance.
    """
    backend_model = model._backend_model
    
    grid_supply_ltc = 'Grid_Connection_Node::grid_supply::electricity'
    if grid_supply_ltc not in backend_model.loc_tech_carriers_prod:
        # No grid import possible; no constraint required.
        return model
    
    national_ltcs = [
        f'Grid_Connection_Node::{tech}::electricity' for tech in national_techs
        ]
    
    # Timesteps with available national generation:
    ts_active = [i for i, val in enumerate(v_e_nat_pot) if val > 0]
    
    varname_binary = 'national_generation_import_binary'
    backend_model.add_component(varname_binary, Var(ts_active, within=Binary))
    binary = getattr(backend_model, varname_binary)
    
    big_M = big_M_import / energy_scaling_factor
    
    def make_national_full_use_constraint_rule(ts_i):
        def national_full_use_constraint_rule(backend_model):
            ts = backend_model.timesteps.at(ts_i + 1) # Pyomo Sets are 1-indexed
            p_nat = sum(backend_model.carrier_prod[ltc, ts] for ltc in national_ltcs)
            avail = v_e_nat_pot[ts_i] / energy_scaling_factor
            return p_nat >= avail * binary[ts_i]
        return national_full_use_constraint_rule
    
    def make_import_constraint_rule(ts_i):
        def import_constraint_rule(backend_model):
            ts = backend_model.timesteps.at(ts_i + 1) # Pyomo Sets are 1-indexed
            return backend_model.carrier_prod[grid_supply_ltc, ts] <= big_M * binary[ts_i]
        return import_constraint_rule
    
    for ts_i in ts_active:
        model.backend.add_constraint(
            f'national_generation_full_use_ts_{ts_i}_constraint',
            [],
            make_national_full_use_constraint_rule(ts_i)
            )
        model.backend.add_constraint(
            f'national_generation_before_import_ts_{ts_i}_constraint',
            [],
            make_import_constraint_rule(ts_i)
            )
    
    return model
