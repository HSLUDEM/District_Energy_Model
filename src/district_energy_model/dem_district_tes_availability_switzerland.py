
# This script list for each district (selected as a multipolygon in geopandas!) the available TES options.
# This multipolygon __could__ be a GGDENR, in which case pre-processed data may be used.
# Currently, it is just a stub to define a structure for the data to be returned

#The storage defined here is for the moment assumed to be fully stratified, i.e. SOS(LTLT)>SOS(HTLT)>SOS(HTHT)∀t

#Importantly capex_base and maintenance_cost_base are ONLY applied if capacity_kWh_min > 0

def tes_availability_script_stub(params): #This is just a placeholder for future, better implementations

    list_of_tes_options = []

    # list_of_tes_options.append({
    #     'name': 'PTES_1',
    #     'color': (122,73,14),
    #     'type': 'simple_fully_stratified_three_temperature_levels', #TES-implementation (content of other entries can depend on this)
    #     'rel_size_t_levels': {'ltlt': 0.6, 'htlt': 0.2, 'htht': 0.2}, #relative shares of storage low-T-->low-T, high-T-->low-T, high-T-->high-T
    #     'capacity_kWh_min': 20000, #Minimum capacity of the TES
    #     'capacity_kWh_max': 40000, #Maximum capacity of the TES
    #     'capex_base': 95000*1.0, #Capex for installing the device (independent of size)
    #     'capex_per_kWh': 0.5, #size dependent share of capex
    #     'maintenance_cost_base': 10000, #Maintenance cost for having the device
    #     'maintenance_cost_per_kWh': 0.05, #Size-dependent share of the maintenance costs
    #     'storage_loss_rate': {
    #         'ltlt': 0.001, 
    #         'htlt': 0.001, 
    #         'htht': 0.002
    #         }, #Self-discharge rate of the TES (dependent on temperature cat)
    #     'eta_chg_dchg': {
    #         'ltlt': 0.9, 
    #         'htlt': 0.9, 
    #         'htht': 0.9
    #         }, #charging/discharging losses
    #     'lifetime': 30.0,
    #     'interest_rate': 0.025,
    #     # 'chg_dchg_per_cap_max': 0.02,
    #     'chg_dchg_per_cap_max': 0.02*5,
    #     'connected_techs': {
    #         'lt': ['heatlt'], #which lt-technologies are connected, there is always a ht->lt conversion tech.
    #         'ht': ['obcp', 'hpcplt', 'wh', 'hpcp', 'dhimp', 'ehcp'] #which ht-technologies are connected1
    #         },
    #     })
    
    # list_of_tes_options.append({
    #     'name': 'PTES_2',
    #     'color': (122,73,14),
    #     'type': 'simple_fully_stratified_three_temperature_levels', #TES-implementation (content of other entries can depend on this)
    #     'rel_size_t_levels': {'ltlt': 0.0, 'htlt': 0.5, 'htht': 0.5}, #relative shares of storage low-T-->low-T, high-T-->low-T, high-T-->high-T
    #     'capacity_kWh_min': 95000, #Minimum capacity of the TES
    #     'capacity_kWh_max': 1000000, #Maximum capacity of the TES
    #     'capex_base': 1e6*0, #Capex for installing the device (independent of size)
    #     'capex_per_kWh': 175.0, #size dependent share of capex
    #     'maintenance_cost_base': 1e5*0, #Maintenance cost for having the device
    #     'maintenance_cost_per_kWh': 0.1*0, #Size-dependent share of the maintenance costs
    #     'storage_loss_rate': {
    #         'ltlt': 0.001, 
    #         'htlt': 0.001, 
    #         'htht': 0.002
    #         }, #Self-discharge rate of the TES (dependent on temperature cat)
    #     'eta_chg_dchg': {
    #         'ltlt': 0.9, 
    #         'htlt': 0.9, 
    #         'htht': 0.9
    #         }, #charging/discharging losses
    #     'lifetime': 30.0,
    #     'interest_rate': 0.025,
    #     # 'chg_dchg_per_cap_max': 0.02,
    #     'chg_dchg_per_cap_max': 1.0,
    #     'connected_techs': {
    #         'lt': ['heatlt'], #which lt-technologies are connected, there is always a ht->lt conversion tech.
    #         'ht': ['obcp', 'hpcplt', 'wh', 'hpcp', 'dhimp', 'ehcp'] #which ht-technologies are connected1
    #         },
    #     })

    
    # list_of_tes_options.append({
    #     'name': 'BTES_1',
    #     'color': (237,206,85),
    #     'type': 'simple_fully_stratified_three_temperature_levels', #TES-implementation (content of other entries can depend on this)
    #     'rel_size_t_levels': {'ltlt': 0.5, 'htlt': 0.5, 'htht': 0.0}, #relative shares of storage low-T-->low-T, high-T-->low-T, high-T-->high-T
    #     'capacity_kWh_min': 0, #Minimum capacity of the TES
    #     'capacity_kWh_max': 30000, #Maximum capacity of the TES [kWh]
    #     'capex_base': 0*0, #Capex for installing the device (independent of size)
    #     'capex_per_kWh': 0.5, #size dependent share of capex
    #     'maintenance_cost_base': 0*0, #Maintenance cost for having the device
    #     'maintenance_cost_per_kWh': 0.1*0, #Size-dependent share of the maintenance costs
    #     'storage_loss_rate': {
    #         'ltlt': 0.001, 
    #         'htlt': 0.001, 
    #         'htht': 0
    #         }, #Self-discharge rate of the TES (dependent on temperature cat)
    #     'eta_chg_dchg': {
    #         'ltlt': 0.9, 
    #         'htlt': 0.9, 
    #         'htht': 0.0
    #         }, #charging/discharging losses
    #     'lifetime': 50.0,
    #     'interest_rate': 0.025,
    #     'chg_dchg_per_cap_max': 0.0005*20,
    #     'connected_techs': {
    #         'lt': ['heatlt'], #which lt-technologies are connected, there is always a ht->lt conversion tech.
    #         'ht': ['obcp', 'wh', 'hpcp', 'dhimp', 'ehcp'] #which ht-technologies are connected1
    #         },
    #     })

    return list_of_tes_options




