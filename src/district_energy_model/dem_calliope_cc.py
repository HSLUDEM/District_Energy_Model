# -*- coding: utf-8 -*-
"""
Created on Fri Aug 22 16:58:21 2025

@author: UeliSchilt
"""

"""
Calliope Custom Constraints (CC).

See: https://calliope.readthedocs.io/en/stable/user/advanced_constraints.html#user-defined-custom-constraints

"""

def ev_flexibility_constraints(model, ts_len, n_days, energy_demand):
    
    # Constraint: Daily EV electricity demand
    # -----------------------------------------
    
    for day in range(n_days): # create one constraint per day:
        
        constraint_name = f'd_e_ev_dy_constraint_{day}'        
        constraint_sets = ['loc_techs_demand']
        
        def d_e_ev_dy_constraint_rule(backend_model, loc_tech):
            
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
            return tmp_sum == -energy_demand.get_d_e_ev_cp_dy()[day]
                 
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
        constraint_sets = ['loc_techs']
        
        def ev_flex_var_constraint_rule(backend_model, loc_tech):
            
            ts = backend_model.timesteps
            
            # Variable to limit energy shift from base profile (cp) in positive direction:
            pos_delta_i_max = (
                backend_model.carrier_prod['X1::flexibility_ev::flexible_electricity', ts[i + 1]] # Pyomo Sets are 1-indexed
                )
            
            d_e_ev_i = (
                backend_model.carrier_con['X1::demand_electricity_ev_pd::electricity', ts[i + 1]] # Pyomo Sets are 1-indexed
                + backend_model.carrier_con['X1::demand_electricity_ev_delta::electricity', ts[i + 1]]
                )
            
            d_e_ev_cp_i = -energy_demand.get_d_e_ev_cp()[i]
            
            delta_i = d_e_ev_i - d_e_ev_cp_i
            
            return pos_delta_i_max >= delta_i
        
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            ev_flex_var_constraint_rule
            )
        
        constraint_name = f'ev_flex_pos_constraint_{i}'
        constraint_sets = ['loc_techs']
        
        def ev_flex_pos_constraint_rule(backend_model, loc_tech):
            
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
        constraint_sets = ['loc_techs']
        
        def f_e_ev_dy_constraint_rule(backend_model, loc_tech):
            
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
                
            f_e_ev_pot_dy = energy_demand.get_f_e_ev_pot_dy()[day]
            
            # Daily EV flexible demand limitation:
            return pos_delta_i_max_sum <= f_e_ev_pot_dy
                 
        model.backend.add_constraint(
            constraint_name,
            constraint_sets,
            f_e_ev_dy_constraint_rule
            )
    
    return model