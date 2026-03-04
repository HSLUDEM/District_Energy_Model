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
                av_current_for_charging = (backend_model.carrier_prod['X1::conv_'
                                                                        +site_entry['name']+'_heatlt_to_heat_tes_site_'
                                                                        +site_entry['name']+'_ltlt::heat_tes_site_'
                                                                        +site_entry['name']+'_ltlt', timestep])
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
                    charging_current -= backend_model.carrier_con['X1::conv_'+
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

def tes_sites_minimum_size_cost(model, ts_len, sites_list, energy_scaling_factor): 

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
                
                obj.expr = obj.expr + site_entry['maintenance_cost_per_kWh'] * bm.storage_cap['X1::tes_site_'+site_entry['name']+'_'+level] * (ts_len/(365*24))


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
        lifetime=  site_entry['lifetime']

        annuity_factor = ((((1+interest_rate)**lifetime) * interest_rate)/(((1+interest_rate)**lifetime) - 1) 
                          if interest_rate > 0 
                          else 1.0/lifetime)

        binary_var = bm.component(varname_binary)


        obj.expr = obj.expr + value_dict['capex_base'] * annuity_factor * binary_var['X1::'+value_dict['sitestr']] * (ts_len/(365*24)) * energy_scaling_factor
        obj.expr = obj.expr + value_dict['maintenance_cost_base'] * binary_var['X1::'+value_dict['sitestr']] * (ts_len/(365*24)) * energy_scaling_factor
        
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
                    backend_model.carrier_con['X1::demand_electricity_ev_pd::electricity', ts[i + 1]] # Pyomo Sets are 1-indexed
                    + backend_model.carrier_con['X1::demand_electricity_ev_delta::electricity', ts[i + 1]]
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
                backend_model.carrier_prod['X1::flexibility_ev::flexible_electricity', ts[i + 1]] # Pyomo Sets are 1-indexed
                )
            
            d_e_ev_i = (
                backend_model.carrier_con['X1::demand_electricity_ev_pd::electricity', ts[i + 1]] # Pyomo Sets are 1-indexed
                + backend_model.carrier_con['X1::demand_electricity_ev_delta::electricity', ts[i + 1]]
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
                backend_model.carrier_prod['X1::flexibility_ev::flexible_electricity', ts[i + 1]] # Pyomo Sets are 1-indexed
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
                    backend_model.carrier_prod['X1::flexibility_ev::flexible_electricity', ts[i + 1]] # Pyomo Sets are 1-indexed
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