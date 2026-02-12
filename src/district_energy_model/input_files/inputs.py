# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 15:02:00 2024

@author: UeliSchilt
"""

import pandas as pd
import numpy as np

# Community:
com_nr = 2762 # Allschwil (Switzerland)

# -----------------------------------------------------------------------------
toggle_plot = True

toggle_save_results = True

toggle_energy_balance_tests = True # !ONLY SET TO FALSE FOR TESTING!


# -----------------------------------------------------------------------------
# Creating a pareto front:
toggle_load_pareto_results = False # overrides toggle_create_pareto... and loads results from file instead

# -----------------------------------------------------------------------------

pvpf = 30 # [%] pv potential factor (pvpf)
wppf = 0 # [%] wp potential factor (wppf) wind power
fhrp = 100 # [%] fossil heater replacement factor (fhrp)
ehrp = 100 # [%] electric heater replacement factor (ehrp)


tes_cap = 'inf' #12 # 0.20 # [GWh] TES capacity *1000'000 kWh; Forsthaus: 12-15GWh
tes_ic = 0.0 # [-] TES initial charge (fraction of total storage capacity)
tesdc_cap = 'inf' #10 # 0.20 # [GWh] TES (decentralised) capacity *1000'000 kWh;
# tesdc_cap = 10 # 0.20 # [GWh] TES (decentralised) capacity *1000'000 kWh;


tesdc_ic = 0.0 # [-] TES (decentralised) initial charge (fraction of total storage capacity)
bes_cap = 'inf' #0.20 # [GWh] BES capacity *1000'000 kWh
# bes_cap = 0.2 #0.20 # [GWh] BES capacity *1000'000 kWh

bes_ic = 0.0 # [-] TES initial charge (fraction of total storage capacity)
gtes_cap = 'inf' #1e6 # [GWh] BES capacity *1000'000 kWh
gtes_ic = 0.0 # [-] TES initial charge (fraction of total storage capacity)

ws_cap = 'inf' #1e6 # [GWh] WS capacity *1000'000 kWh
ws_ic = 0.0 # [-] WS initial charge (fraction of total storage capacity)

hes_cap = 'inf' #1e6 # [GWh] BES capacity *1000'000 kWh
hes_ic = 0.0 # [-] TES initial charge (fraction of total storage capacity)

tech_cap_default = 1e32 # [kW]

hv_oil = 42.9 # [MJ/kg] Heating value (lower) of oil
hv_gas = 46.0 # [MJ/kg] Heating value (lower) of gas
hv_wood = 15.0 # [MJ/kg] Heating value (lower) of wood
hv_msw = 12.0 # [MJ/kg] Heating value (lower) of municipal solid waste; https://vbsa.ch/artikel/aggregierte-zahlen-der-kehricht-verwertungs-anlagen-der-schweiz

oil_price = 1.00 # 1.00 # [CHF/l] Oil price
gas_price = 0.13 #0.15 #0.13 # [CHF/kWh] price of natural gas # see: https://gaspreise.preisueberwacher.ch/web/index.asp
wood_price = 0.5 # [CHF/kg] price of wood
msw_price = -0.30 # [CHF/kg] price of municipal solid waste (msw); negative because it is a revenue.
dh_tariff = 0.13 # [CHF/kWh_th] district heating tariff
wh_tariff = 0.01 # [CHF/kWh_th]
whlt_tariff = 0.01 # [CHF/kWh_th]

grid_tariff_CHFpkWh = 0.29 # [CHF/kWh] electricity tariff

interest_rate = 0.025

virtual_export_tariff_pv = 0.0
virtual_export_tariff_wind = 0#-0.0001
virtual_export_tariff_biomass = 0#-0.0002
virtual_export_tariff_hydro = 0#-0.0003

force_asynchronous_storage = True
no_force_asynchronous_storage_export_subsidy = 1e-5


coptest = np.zeros((24*365))+30.0
coptest[20] = 1.0

# master_path = paths.simulation_data_dir + paths.master_file
# master_file = pd.read_feather(master_path)

# EGID_List = master_file.loc[:100000, 'EGID']
# EGID_List = []
# EGID_List = master_file.loc[:9000, 'EGID']
# EGID_List = []

# Scenario input:
# (consider creating input in YAML file)
scen_techs = {
    'meta_data':{
        'custom_district':{
            'implemented': False,
            # 'EGID_List': EGID_List,
            'EGID_List': [],
            'custom_district_name':'Test_Scenario',
            
            }
        },
    'heat_pump':{ #hp
        'deployment':True,
        # 'deployment':False,
        'kW_th_max':'inf',
        'lifetime':25,
        'interest_rate':interest_rate,
        'capex': 6000, # [CHF/kWth]
        'capex_one_to_one_replacement': 2000, #[CHF/kWth]
        'maintenance_cost': 10, # [CHF/kW/year]
        'fixed_demand_share':False, # If set to 'True', a fixed share (per timestep) of the total heat demand will be served by this tech
        'fixed_demand_share_val':0.0, # [-] Only relevant if fixed_demand_share == True; the share(per timestep) of the total heat demand served by this tech; ensure that resource and max. cap are set accordingly
        'only_allow_existing':False, # Only relevant for optimisation; if set to 'True', only the existing (allready installed) capacity can be used; CAREFUL: Avoid conflict with fixed_demand_share.
        
        'cop_mode': "location_based", # "from_file", "constant", "location_based"
        'cop_timeseries_file_path': 'input_files/cop_timeseries_test.feather',
        'cop_constant_value': 5.5,
        'quality_factor_ashp_new' : 0.4,
        'quality_factor_ashp_old' : 0.4,
        'quality_factor_gshp_new' : 0.48,
        'quality_factor_gshp_old' : 0.48,
        },

    'electric_heater':{ # eh
        'deployment':True,
        # 'deployment':False,
        'kW_max':'inf',
        'lifetime':25,
        'interest_rate':interest_rate,
        'replacement_factor':ehrp/100,
        'capex':0.0, # No new electric heaters allowed
        'capex_one_to_one_replacement': 500, #[CHF/kWth]
        'maintenance_cost': 0, # [CHF/kW/year]
        'fixed_demand_share':False, # If set to 'True', a fixed share (per timestep) of the total heat demand will be served by this tech
        'fixed_demand_share_val':0.0, # [-] Only relevant if fixed_demand_share == True; the share(per timestep) of the total heat demand served by this tech;
        },
              
    'oil_boiler':{ # ob
        'deployment':True,
        # 'deployment':False,
        'kW_th_max':'inf',
        'hv_oil_MJpkg':hv_oil, # 42.9, # [MJ/kg] Heating value (lower) of oil
        'eta':0.85,
        'oil_price_CHFpl':oil_price, # 1.00, # [CHF/l] Oil price; see: https://www.migrol.ch/de/energie-w%C3%A4rme/heiz%C3%B6lpreisentwicklung/preisindex/
        'lifetime':25,
        'interest_rate':interest_rate,
        'replacement_factor':fhrp/100,
        'capex':3000,
        'capex_one_to_one_replacement': 1500, #[CHF/kWth]
        'maintenance_cost': 30, # [CHF/kW/year]
        'fixed_demand_share':False, # If set to 'True', a fixed share (per timestep) of the total heat demand will be served by this tech
        'fixed_demand_share_val':0.0, # [-] Only relevant if fixed_demand_share == True; the share(per timestep) of the total heat demand served by this tech;
        'only_allow_existing':False, # Only relevant for optimisation; if set to 'True', only the existing (allready installed) capacity can be used; CAREFUL: Avoid conflict with fixed_demand_share.
        },
    
    'gas_boiler':{ # gb
        'deployment':True,
        # 'deployment':False,
        'kW_th_max':'inf',
        'hv_gas_MJpkg':hv_gas, # 46.0, # [MJ/kg] Heating value (lower) of gas
        'eta':0.90,
        'gas_price_CHFpkWh':gas_price, # [CHF/kWh] price of gas
        'lifetime':25,
        'interest_rate':interest_rate,
        'replacement_factor':fhrp/100,
        'capex':2500, # [CHF/kW_th]
        'capex_one_to_one_replacement': 1000, #[CHF/kWth]
        'maintenance_cost': 25, # [CHF/kW/year]
        'fixed_demand_share':False, # If set to 'True', a fixed share (per timestep) of the total heat demand will be served by this tech
        'fixed_demand_share_val':0.0, # [-] Only relevant if fixed_demand_share == True; the share(per timestep) of the total heat demand served by this tech;
        'only_allow_existing':False, # Only relevant for optimisation; if set to 'True', only the existing (allready installed) capacity can be used; CAREFUL: Avoid conflict with fixed_demand_share.
        },
                              
    'wood_boiler':{ # wb
        'deployment':True,
        # 'deployment':False,
        'kW_th_max':'inf',
        'hv_wood_MJpkg':hv_wood, # [MJ/kg] Heating value (lower) of wood
        'eta':0.80,
        'wood_price_CHFpkg':wood_price, # [CHF/kg] price of wood
        'lifetime':25,
        'interest_rate':interest_rate,
        'replacement_factor':fhrp/100,
        'capex': 4500,
        'capex_one_to_one_replacement': 2000, #[CHF/kWth]
        'maintenance_cost': 50, # [CHF/kW/year]
        'fixed_demand_share':False, # If set to 'True', a fixed share (per timestep) of the total heat demand will be served by this tech
        'fixed_demand_share_val':0.0, # [-] Only relevant if fixed_demand_share == True; the share(per timestep) of the total heat demand served by this tech;
        'only_allow_existing':False, # Only relevant for optimisation; if set to 'True', only the existing (allready installed) capacity can be used; CAREFUL: Avoid conflict with fixed_demand_share.
        },
                              
    'district_heating':{ # dh
        'deployment':True,
        # 'deployment':False, # 
        'demand_share_type':'free', # Constraint type in regard to what share of the demand will be supplied by district heating; options: 'fixed', 'min', 'max', 'free'
        'demand_share_val':0.5, # [-] The value of the share of district heating; e.g. 0.5 for 50%; relevant for types 'fixed', 'min', or 'max'
        'import_kW_th_max':'inf', # Heat import capacity
        'grid_kW_th_max':'inf',
        'investment_dh_grid_per_m': 400, # [CHF / m]
        'maintenance_cost_dh_grid_per_m' : 5, # [CHF / m / year]
        'closeness_based_dh_expansio_cost' : True,
        'capex' : 1000, #[CHF/kW] relevant if and only if closeness_based_dh_expansio_cost==False
        'maintenance_cost' : 10, # [CHF/kW/year] relevant if and only if closeness_based_dh_expansio_cost==False

        'tariff_CHFpkWh':dh_tariff, # 0.15, # Average from "Faktenblatt Thermische Netze"; only used for import
        'co2_intensity': 0.108,
        'lifetime':25,
        'interest_rate':interest_rate,
        # 'capex':10000 # NOT YET IMPLEMENTED
        'heat_sources':{ # only applies to optimisation scenario
            'import':True,
            'chp_gt':True, # if True, tech chp_gt must be deployed
            'steam_turbine':True, # if True, tech steam_turbine must be deployed
            'waste_to_energy':True, # if True, tech waste_to_energy must be deployed,
            'heat_pump_cp':True, # if True, tech heat_pump_cp must be deployed !!! TECH NOT YET IMPLEMENTED !!!
            'heat_pump_cp_lt':True, # 
            'oil_boiler_cp' :True,
            'electric_heater_cp' :True,
            'wood_boiler_cp' :True,
            'gas_boiler_cp' :True,
            'waste_heat': True,
            'biomass': True
            },
        },
    
    'solar_pvrooftop':{ # pv
        'deployment':True,
        'kWp_max':'inf', 
        'eta_overall': 0.23*0.95,
        'lifetime':25,
        'base_capex':3000, #capex per installed kWp power. This is not the same as the peak of the solar PV production.
        'base_maintenance_cost': 6.45,
        'interest_rate':interest_rate,
        'export_subsidy': 0 if force_asynchronous_storage else no_force_asynchronous_storage_export_subsidy,
        'only_use_installed':False,
        },
        
    'solarthermal_rooftop':{ # solar
        'deployment':True, 
        'kW_th_max':'inf',
        'eta_overall':0.7,
        'lifetime':25,
        'interest_rate':interest_rate,
        'base_capex': 2857, # [CHF/kW_th]
        'base_capex_one_to_one_replacement': 1000*0, #[CHF/kW_th] does nothing
        'base_maintenance_cost': 10, # [CHF/kW_th/year]
        'export_subsidy': 0 if force_asynchronous_storage else no_force_asynchronous_storage_export_subsidy,
        'only_use_installed': False
        },

    
    'wind_power':{ # wp
        'deployment':True,
        # 'deployment':False,
        'kWp_max': tech_cap_default,
        'kWp_max_systemwide': 'inf',
        'lifetime':25,
        'capex_CHFpkWp': 2075, # 1400,
        'maintenance_cost': 11.3, # [CHF/kW/year]
        'interest_rate':interest_rate,
        'potential_integration_factor':wppf/100,
        'virtual_export_tariff':virtual_export_tariff_wind,
        'export_subsidy': 0 if force_asynchronous_storage else no_force_asynchronous_storage_export_subsidy,
        'wind_power_installed_allocation': 'local', # options: 'national', 'local'
        'v_e_wp_national_recalc':False # Set to True for recalculation of hourly national wind power profile of installed capacity; default should be False.
        # 'profile_type':'total' # options: 'annual', 'winter', 'total' !!! NOT USED !!!
        },
    
    'hydro_power':{ # hydro # Fokus auf "local" hydro_power !!! MUSS NOCH IN dem_tech.py IMPLEMENTIERT WERDEN!!!
        'deployment':True,
        # 'deployment':False,
        'kWp_max':'inf',
        'existing_decentralised':True, # NOCH NICHT IMPLEMENTIERT
        'lifetime':25,
        'capex':0,
        'maintenance_cost': 130, # [CHF/kW/year]
        'interest_rate':interest_rate,
        'virtual_export_tariff':virtual_export_tariff_hydro,
        'export_subsidy': 0 if force_asynchronous_storage else no_force_asynchronous_storage_export_subsidy,
        },
       
    'grid_supply':{ # grid
        'deployment':True,
        # 'deployment':False,
        'kW_max':'inf',
        'tariff_CHFpkWh':grid_tariff_CHFpkWh, #0.29, # [CHF/kWh] electricity tariff !!! MUST BE CHANGED TO A TIME SERIES
        'co2_intensity':0.128,
        'lifetime':25,
        'interest_rate':interest_rate
        },
              
    'tes':{ # tes (thermal energy storage) (large scale, connected to District Heating Network)
        'deployment':False,
        'force_asynchronous_prod_con': force_asynchronous_storage,
        # 'deployment':False,
        'eta_chg_dchg': 0.95, # 0.95 * 0.95 = 0.9025 round trip efficiency
        'tes_gamma':0.001,
        'capacity_kWh':tes_cap*1e6 if tes_cap != 'inf' else 'inf',
        'force_cap_max':False, # implement max. storage capacity (kWh)
        'chg_dchg_per_cap_max':0.1, # max. charge/discharge (kW) per storage cap (kWh) per timestep
        'initial_charge':tes_ic,
        'optimized_initial_charge': True, #optimize the intial=final sos. This disables initial_charge
        'connections':{
            # 'heat_pump':False, # connection to decentralised heat pumps; usually when dh is not connected
            'district_heating_network':True,
            'district_heat_import':True,
            'chp_gt':True,
            'steam_turbine':True,
            'waste_to_energy':True,
            'oil_boiler_cp':True,
            'electric_heater_cp':True,
            'wood_boiler_cp':True,
            'gas_boiler_cp':True,
            'heat_pump_cp':True, # heat pump central plant
            'heat_pump_cp_lt':True, # heat pump central plant
            'waste_heat': False,
            'biomass': True
            },
        'lifetime':25,
        'capex':1.67, # [CHF/kWh_th]
        'maintenance_cost': 0, # [CHF/kWh_th/year]
        'interest_rate':interest_rate
        },

    'tes_sites':{ # tes sites (thermal energy storage) (large scale, connected to District Heating Network): sites with different properties
        'deployment':False,
        'force_asynchronous_prod_con': force_asynchronous_storage,
        'list_generation_mode': 'stub', #options: 'stub'
        'generation_function_parameters': {},
        'interest_rate':interest_rate
        },

    'tes_decentralised':{ # tesdc
        'deployment':False,
        'force_asynchronous_prod_con': force_asynchronous_storage,
        # 'deployment':False,
        'eta_chg_dchg': 0.95, # 0.95 * 0.95 = 0.9025 round trip efficiency
        'tes_gamma':0.001,
        'capacity_kWh':tesdc_cap*1e6 if tesdc_cap != 'inf' else 'inf',
        'chg_dchg_per_cap_max':0.1, # max. charge/discharge (kW) per storage cap (kWh) per timestep
        'initial_charge':tesdc_ic,
        'optimized_initial_charge': True, #optimize the intial=final sos. This disables initial_charge
        'connections':{
            'heat_pump':True, # connection to decentralised heat pumps; usually when dh is not connected
            'solar_thermal':False, # CONNECTION NOT YET IMPLEMENTED
            },
        'lifetime':25,
        'capex':3.0, #1.67, # [CHF/kWh_th]
        'maintenance_cost': 0.02, # [CHF/kW/year]
        'interest_rate':interest_rate
        },
              
    'bes':{ # bes (battery energy storage)
        'deployment':True,
        'force_asynchronous_prod_con': force_asynchronous_storage,
        # 'deployment':False,
        'eta_chg_dchg':0.95, # 0.95 * 0.95 = 0.9025 round trip efficiency
        'bes_gamma':0.001,
        'capacity_kWh':bes_cap*1e6 if bes_cap != 'inf' else 'inf',
        'chg_dchg_per_cap_max':0.1, # max. charge/discharge (kW) per storage cap (kWh) per timestep
        'initial_charge':bes_ic,
        'optimized_initial_charge': True, #optimize the intial=final sos. This disables initial_charge
        'lifetime':10,
        'interest_rate':interest_rate,
        'capex':500, # [CHF/kWh_el]
        'maintenance_cost': 2.0, # [CHF/kW/year]
        },
    
    'gtes':{ # gtes (gas tank energy storage) (large tank with gas)
        'deployment':True,
        'force_asynchronous_prod_con': force_asynchronous_storage,
        # 'deployment':False,
        'eta_chg_dchg':0.95, # 0.95 * 0.95 = 0.9025 round trip efficiency
        'gtes_gamma':0.0,
        'capacity_kWh':gtes_cap*1e6 if gtes_cap != 'inf' else 'inf',
        'chg_dchg_per_cap_max':0.1, # max. charge/discharge (kW) per storage cap (kWh) per timestep
        'initial_charge':gtes_ic,
        'optimized_initial_charge': True, #optimize the intial=final sos. This disables initial_charge
        'lifetime':25,
        'interest_rate':interest_rate,
        'capex':0.2, # [CHF/(gas unit?)]
        'maintenance_cost': 0.01, # [CHF/kW/year]
        },

    'ws':{ # ws (Wood storage) (piles of wood somewhere in the forest)
        'deployment':True,
        'force_asynchronous_prod_con': True,
        # 'deployment':False,
        'eta_chg_dchg': 1.0,
        'ws_gamma':0.0,
        'capacity_kWh':ws_cap*1e6 if ws_cap != 'inf' else 'inf',
        'chg_dchg_per_cap_max':0.1, # max. charge/discharge (kW) per storage cap (kWh) per timestep
        'initial_charge':ws_ic,
        'optimized_initial_charge': True, #optimize the intial=final sos. This disables initial_charge
        'lifetime':50,
        'interest_rate':interest_rate,
        'capex':0.0, # [CHF/(kWh)] --> costs are part of wood price
        'maintenance_cost': 0.0, # [CHF/kW/year] --> costs are part of wood price
        },

    'hes':{ # hes (hydrogen energy storage) (large tank with hydrogen?)
        'deployment':True,
        'force_asynchronous_prod_con': force_asynchronous_storage,
        # 'deployment':False,
        'eta_chg_dchg':0.95, # 0.95 * 0.95 = 0.9025 round trip efficiency
        'hes_gamma':0.0,
        'capacity_kWh':hes_cap*1e6 if hes_cap != 'inf' else 'inf',
        'chg_dchg_per_cap_max':0.1, # max. charge/discharge (kW) per storage cap (kWh) per timestep
        'initial_charge':1.0,#hes_ic,
        'optimized_initial_charge': True, #optimize the intial=final sos. This disables initial_charge
        'lifetime':25,
        'interest_rate':interest_rate,
        'capex':15.0, # [CHF/(gas unit?)]
        'maintenance_cost': 1.0, # [CHF/kW/year]
        },



    'biomass':{ # bm
        'deployment':True, # Must be set to True, if any of the biomass techs below is set to True
        # 'deployment':False,
        },


    
    'hydrothermal_gasification':{ # hg
        'deployment':True,
        # 'deployment':False,
        'color': '#3A880A',
        'efficiency': 0.6,
        'capacity_kWh': 'inf',
        'lifetime': 25,
        'om_cost': 0, #Carrier Consumption Cost
        'capital_cost': 8268,
        'maintenance_cost': 10, # [CHF/kW/year]
        'interest_rate': interest_rate
        },
    
    'anaerobic_digestion_upgrade':{ # agu
        'deployment':True,
        # 'deployment':False,
        'color': '#FF00FF',
        'efficiency': 0.3,
        'capacity_kWh': 'inf',
        'lifetime': 25,
        'om_cost': 0, #Carrier Consumption Cost
        'capital_cost': 1053,
        'maintenance_cost': 10, # [CHF/kW/year]
        'interest_rate': interest_rate
        },
    
    'anaerobic_digestion_upgrade_hydrogen':{ # aguh
        'deployment':True,
        # 'deployment':False,
        'color': '#90037F',
        'fluid': False,
        'methane_percentage': 0.6,
        'efficiency_primary': 0.3,
        'efficiency_secondary': 0.8395,
        'capacity_kWh': 'inf',
        'lifetime': 25,
        'om_cost': 0, #Carrier Consumption Cost (electricity?)
        'capital_cost': 1834, # [CHF/kW chem LHV] # 1900,
        'maintenance_cost': 10, # [CHF/kW/year]
        'interest_rate': interest_rate
        },
    
    'anaerobic_digestion_chp':{ # aguc
        'deployment':True,
        # 'deployment':False,
        'color': '#90037F',
        'efficiency_electricity': 0.13,
        'efficiency_heat': 0.145,
        'capacity_kWh': 'inf',
        'lifetime': 25,
        'om_cost': 0,
        'capital_cost': 1776,
        'maintenance_cost': 10, # [CHF/kW/year]
        'interest_rate': interest_rate
        },
    
    'wood_gasification_upgrade':{ # wgu
        'deployment':False,
        # 'deployment':False,
        'color':'#904D11',
        'efficiency': 0.625,
        'fluid': True,
        'capacity_kWh': 'inf',
        'lifetime': 25,
        'interest_rate': interest_rate,
        'capital_cost': 2315, # [CHF/kW chem LHV]
        'maintenance_cost': 10, # [CHF/kW/year]
        },
    
    'wood_gasification_upgrade_hydrogen':{ # wguh
        'deployment':False,
        # 'deployment':False,
        'color': '#C67125',
        'fluid': True,
        'methane_percentage': 0.6,
        'efficiency_primary': 0.625,
        'efficiency_secondary': 0.8395,
        'capacity_kWh': 'inf',
        'lifetime': 25,
        'om_cost': 0,
        'capital_cost': 2706, # [CHF/kW chem LHV]
        'maintenance_cost': 10, # [CHF/kW/year]
        'interest_rate': interest_rate
        },
    
    'wood_gasification_chp':{ # wguc
        # 'deployment':True,
        'deployment':False,
        'color': '#FF7800',
        'efficiency_electricity': 0.275,
        'efficiency_heat': 0.3625,
        'capacity_kWh': 'inf',
        'lifetime': 25,
        'om_cost': 0,
        'capital_cost': 3942,
        'maintenance_cost': 43.2, # [CHF/kW/year]
        'interest_rate': interest_rate
        },
    
    'hydrogen_production':{ # hydp
        'deployment':True,
        # 'deployment':False,
        'color': '#1A8FD2',
        'efficiency': 0.8,
        'capacity_kWh': 'inf',
        'lifetime': 25,
        'om_cost': 0,
        'capital_cost': 600,
        'maintenance_cost': 10, # [CHF/kW/year]
        'interest_rate': interest_rate
        },
    
    'chp_gt':{ # chp_gt
        # 'deployment':True,
        'deployment':False,
        'deployment':False,
        'deploy_existing':False, # 'If set to 'true', existing gas turbine will be deployable. [!!!NOT YET IMPLEMENTED]
        'kW_el_max':'inf',#tech_cap_default, # [kW_el] Maximum electrical power output of newly built CHP gas turbines
        'force_cap_max':False, # implement max. capacity (kW)
        'hv_gas_MJpkg':hv_gas, # [MJ/kg] Heating value (lower) of gas
        'eta_el':0.35,
        'htp_ratio':1.5, # [-] heat-to-power (htp) ratio (kW_h/kW_el)
        'gas_price_CHFpkWh':gas_price, # [CHF/kWh] price of gas
        'lifetime':25,
        'capital_cost':5000, # [CHF/kW_el]
        'maintenance_cost': 10, # [CHF/kW/year]
        'interest_rate':interest_rate,

        'allow_heat_export': True,
        'heat_export_subsidy': 1e-5
        },
    
    'gas_turbine_cp':{ # gtcp # cp = central plant
        # 'deployment':True,
        'deployment':False,
        'kW_el_max': 'inf',#tech_cap_default, # [kW_el] Maximum electrical power output; Forsthaus: 46MW
        'force_cap_max':False, # implement max. capacity (kW)
        'cap_min_use':0.0, # [-] Share of capacity to be forced [0.0-1.0]; Default: 0.0
        'hv_gas_MJpkg':hv_gas, # [MJ/kg] Heating value (lower) of gas
        'eta_el':0.35,
        'htp_ratio':1.5, # [-] heat-to-power (htp) ratio (kW_th/kW_el)
        # 'gas_price_CHFpkWh':gas_price, # [CHF/kWh] price of gas
        'lifetime':25,
        'capital_cost':5000.0, # [CHF/kW_el] # TO BE VERIFIED
        'maintenance_cost': 40.1, # [CHF/kW/year]
        'interest_rate':interest_rate,
        },
    
    'steam_turbine':{ # st
        # 'deployment':True,
        'deployment':False,
        'kW_el_max': 'inf',#tech_cap_default, # [kW_el] Maximum electrical power output; Forsthaus: 27MW
        'force_cap_max':False, # implement max. capacity (kW)
        'grid_charges': 0.0, #Cost of grid usage for this electricity
        'cap_min_use':0.0, # [-] Share of capacity to be forced [0.0-1.0]; Default: 0.0
        'eta_el':0.35,
        'htp_ratio':1.5, # [-] heat-to-power (htp) ratio (kW_h/kW_el)
        'lifetime':25,
        'capital_cost':5000.0, # [CHF/kW_el]
        'maintenance_cost': 10, # [CHF/kW/year]
        'interest_rate':interest_rate,   

        'allow_heat_export': True,
        'heat_export_subsidy': 1e-5
     
        },
    
    'wood_boiler_sg':{ # wbsg # converting wood to steam; must be coupled with steam turbine : Wood boiler steam Generator
        # 'deployment':True,
        'deployment':False,
        'kW_h_max': 'inf',#tech_cap_default, # [kW_th] Maximum power output in the form of steam
        'force_cap_max':False, # implement max. capacity (kW)
        'wood_input_cap_type':'free', # Options: 'free', 'max', 'fixed'; type of input capacity (kg wood) constraint (alternative max kW-capacity)
        'wood_input_cap_kg':112e6, # [kg] Annual wood input capacity (only relevant for wood_input_cap_type 'max' or 'fixed')
        'cap_min_use':0.0, # [-] Share of capacity use to be forced [0.0-1.0]; Default: 0.0
        'hv_wood_MJpkg':hv_wood, # [MJ/kg] Heating value (lower) of wood
        'eta':0.80,
        'wood_price_CHFpkg':wood_price, # [CHF/kg] price of wood
        'lifetime':25,
        'capital_cost':150*30, # [CHF/kW_th] # TO BE VERIFIED https://www.energie-experten.org/heizung/blockheizkraftwerk-bhkw/blockheizkraftwerk-kosten
        'maintenance_cost': 5, # [CHF/kW/year]
        'interest_rate':interest_rate,
        },

    'oil_boiler_cp':{ # obcp
        'deployment':True,
        # 'deployment':False,
        'kW_th_max':'inf',
        'hv_oil_MJpkg':hv_oil, # 42.9, # [MJ/kg] Heating value (lower) of oil
        'eta':0.85,
        'oil_price_CHFpl':oil_price, # 1.00, # [CHF/l] Oil price; see: https://www.migrol.ch/de/energie-w%C3%A4rme/heiz%C3%B6lpreisentwicklung/preisindex/
        'lifetime':25,
        'interest_rate':interest_rate,
        'capex':2000.0,
        'maintenance_cost': 1.26, # [CHF/kW/year]
        },

    'electric_heater_cp':{ # ehcp
        'deployment':True,
        'kW_th_max':'inf',
        'eta':0.98,
        'lifetime':30,
        'interest_rate':interest_rate,
        'capex':100.0,
        'maintenance_cost': 0.5, # [CHF/kW/year]
        },

    'wood_boiler_cp':{ # wbcp
        'deployment':True,
        # 'deployment':False,
        'kW_th_max': 'inf',
        'hv_wood_MJpkg':hv_wood, # [MJ/kg] Heating value (lower) of wood
        'eta':0.85,
        'lifetime':25,
        'interest_rate':interest_rate,
        'capex':2000.0,
        'maintenance_cost': 1.26, # [CHF/kW/year]
        },


    'waste_heat':{ # wh
        'deployment':False,
        'capex': 0.0,
        'maintenance_cost': 0.0,
        'lifetime':25,
        'timeseries_file_path': '',
        'co2_intensity':0.0, # [kgCO2/kWh]
        'tariff_CHFpkWh': wh_tariff, # [CHF / kWh]
        'interest_rate':interest_rate,
        },

    'waste_heat_low_temperature':{ # whlt
        'deployment':False,
        'capex': 0.0,
        'maintenance_cost': 0.0,
        'lifetime':25,
        'timeseries_file_path': '',
        'co2_intensity':0.0, # [kgCO2/kWh]
        'tariff_CHFpkWh': whlt_tariff, # [CHF / kWh]
        'interest_rate':interest_rate,
        },

    
    'gas_boiler_cp':{ # gbcp
        'deployment':False,
        # 'deployment':False,
        'kW_th_max':'inf',
        'hv_gas_MJpkg':hv_gas, # 46.0, # [MJ/kg] Heating value (lower) of gas
        'eta':0.9,
        'gas_price_CHFpkWh':gas_price, # [CHF/kWh] price of gas
        'lifetime':25,
        'interest_rate':interest_rate,
        # 'replacement_factor':fhrp/100,
        'capex':2000, # [CHF/kW_th]
        'maintenance_cost': 1.26, # [CHF/kW/year]
        # 'fixed_demand_share':False, # If set to 'True', a fixed share (per timestep) of the total heat demand will be served by this tech
        # 'fixed_demand_share_val':0.0, # [-] Only relevant if fixed_demand_share == True; the share(per timestep) of the total heat demand served by this tech;
        # 'only_allow_existing':False, # Only relevant for optimisation; if set to 'True', only the existing (allready installed) capacity can be used; CAREFUL: Avoid conflict with fixed_demand_share.
        },

    
    'waste_to_energy':{ # wte
        # 'deployment':True,
        'deployment':False,
        'kW_el_max': 'inf',#tech_cap_default, # [kW_el] Maximum electrical power output; Forsthaus: 16MW #
        'force_cap_max':False, # implement max. capacity (kW) #
        'cap_min_use':0.0, # [-] Share of capacity to be forced [0.0-1.0]; Default: 0.0
        'hv_msw_MJpkg':hv_msw, # [MJ/kg] Heating value (lower) of municipal solid waste
        'eta_el':0.35,
        'htp_ratio':1.5, # [-] heat-to-power (htp) ratio (kW_h/kW_el)
        'msw_price_CHFpkg':msw_price, # [CHF/kg] price of msw (will be negative --> revenue)
        'lifetime':25,
        'capital_cost':2000.0, # [CHF/kW_el] # TO BE VERIFIED
        'maintenance_cost': 119, # [CHF/kW/year]
        'interest_rate':interest_rate,        
        },
    
    'heat_pump_cp_lt':{ # hpcplt
        # 'deployment':True,
        'deployment':False,
        'kW_th_max': 'inf',#tech_cap_default,
        'force_cap_max':False, # implement max. capacity (kW)
        'cap_min_use':0.0, # [-] Share of capacity to be forced [0.0-1.0]; Default: 0.0
        'cop':8.0,
        'lifetime':25,
        'capital_cost':2000.0, # [CHF/kW_th] # TO BE VERIFIED
        'maintenance_cost': 10, # [CHF/kW/year]
        'interest_rate':interest_rate,   
        },

    'heat_pump_cp':{ # hpcp
        # 'deployment':True,
        'deployment':True,
        'kW_th_max': 'inf',#tech_cap_default,
        'force_cap_max':False, # implement max. capacity (kW)
        'cap_min_use':0.0, # [-] Share of capacity to be forced [0.0-1.0]; Default: 0.0
        'lifetime':25,
        'capital_cost':2000.0, # [CHF/kW_th] # TO BE VERIFIED
        'maintenance_cost': 10, # [CHF/kW/year]
        'interest_rate':interest_rate,

        'cop_mode': 'temperature_based', #option 'temperature_based', 'constant', 'from_file', 'from_file_adjusted_to_spf'
        'cop_timeseries_file_path': coptest,
        'cop_constant_value': 3.0,
        'spf_to_target': 3.5,

        'cop_source_temperature': 'air_temperature', #choices: 'constant_temperature', 'air temperature'
        'cop_source_constant_temperature_value': 5,
        'cop_hot_temperature': 'constant_temperature',
        'cop_hot_temperature_constant_temperature_value': 70,
        'quality_factor': 0.5
        },

    'other':{ # other
        'deployment':True
        },
              
    'scenarios':{
        'demand_side': False,
        # 'demand_side':True,
        'fossil_heater_retrofit':False,
        # 'fossil_heater_retrofit':True,
        'pv_integration':False,
        # 'pv_integration':True,
        'wind_integration':False,
        # 'wind_integration':True,
        'thermal_energy_storage':False,
        # 'thermal_energy_storage':True,
        'nuclear_phaseout':False,

        'battery_energy_storage': False,

        },
                             
    'optimisation':{ # note: objective weights will be overriden in case of pareto front computation (i.e. toggle_create_pareto_monetary_vs_co2 = True)
        'enabled':False,
        'clustering':False,
        'pareto_monetary_co2':False, # Compute Pareto front; overrides objective weights below; optimisation must be enabled (True)
        'N_pareto':6, # Number of points on the Pareto Front (min. 2)
        'objective_monetary':1.0, # 0.00001 NOTE: When optimising for emissions, make objective_monetary a small value (1e-5) as opposed to 0. Otherwise it can result in "artificial solutions", e.g. implementing capactiy that is not used, resulting in disproportionately large costs.
        'objective_co2':0.0,
        'objective_ess':0.0, # energy self-sufficiency
        'objective_tss':0.0, # thermal self-sufficiency
        'calliope_energy_scaling_factor': 1.0, #scales all the energy values by a constant factor e.g. kW -> MW
        'bigM_value':1e6, # Default: 1e9; cost of unmet demand; large value makes model convergence slow; https://calliope.readthedocs.io/en/stable/user/building.html#allowing-for-unmet-demand
        'solver': 'gurobi', #'cbc'
        'solver_option_NumericFocus':1, # Default: 0; https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameternumericfocus
        'solver_option_TimeLimit':36000, # [s] 'Infinity', # Default: 'Infinity'; https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#timelimit
        'solver_option_Presolve':-1, # Default: -1; https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#presolve
        'solver_option_Aggregate':1, # Default: 1; https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#aggregate
        'solver_option_FeasibilityTol':1e-2, # Default: 1e-6; https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#feasibilitytol
        'solver_option_MIPGap':1e-4, # [-] Default: 1e-4; https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#mipgap
        'MIPGap_increase':False, # [-] If set to True, MIPGap will be increased to 0.01 if a storage technology is activated in order to avoid numerical problems.
        'save_math_model':False, # math. model formulations in .lp file; can take long to produce and result in large file;
        'save_calliope_files':False, # Print Calliope input and results in csv files
        },
    
    'simulation':{
        'number_of_days':365, # Simulation timeframe, starting on 1 Jan
        'district_number':com_nr,
        'generate_plots':toggle_plot,
        'save_results':toggle_save_results,
        # 'results_dir':''
        # 'timeframe':['2050-01-01', '2050-01-31'], # NOT YET IMPLEMENTED
        # 'ts_resolution':60 # [min] timestep resolution # NOT YET IMPLEMENTED
        },
    
    'demand_side':{ # only applies if ['scenarios]['demand_side'] == True
        'year': 2023, # Options: 2023, 2030, 2040, 2050
        'rcp_scenario':'RCP26',
        'ts_type':'tas_median',
        'ev_integration':True,
        'ev_integration_factor':100, # [%] share of electric vehicle in total fleet
        'ev_flexibility': True, # only in combination with optimisation

        'total_renovation': True,
        'use_constant_total_renovation_rate': True,
        'renovation_scenario' : 'renovation_low',
        'constant_total_renovation_rate': 0.018,
        'total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios': {
            'v_h_eh' : 0.0, 'v_h_hp' : 0.8, 'v_h_dh' : 0.05, 'v_h_gb' : 0.05, 'v_h_ob' : 0.05,
            'v_h_wb' : 0.05, 'v_h_solar' : 0.0, 'v_h_other' : 0.0 },
        'total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios': {
            'v_hw_eh' : 0.05, 'v_hw_hp' : 0.0, 'v_hw_dh' : 0.95, 
            'v_hw_gb' : 0.0, 'v_hw_ob' : 0.0, 'v_hw_wb' : 0.0, 
            'v_hw_solar' : 0.0, 'v_hw_other' : 0.0 },
        
        'heat_generator_renovation': True, #retrofit old heat generators. Affects buildings without total renovation. 
                        # Only has effects when optimization is enabled. Forces a CAPEX for one-to-one replacement.
        'act_on_fossil_heater_retrofit': False
        },

    'nuclear_phaseout':{
        'nuclear_power_plant_powers' :[1010, 1233, 365, 365], #Gösgen, Leibstadt, Beznau I, Beznau II
        'nuclear_power_plant_shutdown_years' :[2039, 2045, 2033, 2032],#Gösgen, Leibstadt, Beznau I, Beznau II
    },

    'fossil_heater_retrofit':{
        'electric_boiler_replacement_factor' : ehrp/100, #in fossil heater retrofit scenario, share of electric_heaters that are replaced
        'gas_boiler_replacement_factor' : fhrp/100, #in fossil heater retrofit scenario, share of gas_boilers that are replaced
        'oil_boiler_replacement_factor' : fhrp/100, #in fossil heater retrofit scenario, share of oil_boilers that are replaced
    },

    'pv_integration':{
        'pv_techs_to_act_on': [
            'solar_pvrooftop'
            ],
        'potential_integration_factor' : {
            'solar_pvrooftop': [pvpf/100, pvpf/100, pvpf/100, pvpf/100]
            }, 
    },

    'wind_integration':{
        'potential_integration_factor' : wppf/100, #Potential integration factor for wind
    },

    'thermal_energy_storage_scenario': {
        'capacity_kWh': 0,
        'initial_charge': 0.5,
    },

    'battery_energy_storage_scenario': {
        'capacity_kWh': 1e4,
        'initial_charge': 0.5,
    },
    
    'supply':{
        
        #Oil
        'hv_oil_MJpkg':hv_oil, # [MJ/kg] Heating value (lower) of oil
        'oil_price_CHFpl':oil_price, # [CHF/l] Oil price
        'oil_import':True,
        'co2_content_oil': 0.301,

        #Gas
        'hv_gas_MJpkg':hv_gas, # [MJ/kg] Heating value (lower) of gas
        'gas_price_CHFpkWh':gas_price, # [CHF/kWh] price of gas
        'gas_import':True,
        'co2_content_gas': 0.228,

        #Wood
        'hv_wood_MJpkg':hv_wood, # [MJ/kg] Heating value (lower) of wood
        'wood_price_CHFpkg_local':wood_price, # [CHF/kg] price of wood (local)
        'wood_price_CHFpkg_imported':wood_price, # [CHF/kg] price of wood (imported)
        'wood_import':True, # if set to True, wood can be imported
        'co2_content_local_wood': 0.027,
        'co2_content_imported_wood': 0.027, #TODOTODO find value

        #Wet biomass
        'co2_content_wet_biomass': 0.0,

        #Municipal solid waste
        'hv_msw_MJpkg':hv_msw, # [MJ/kg] Heating value (lower) of municipal solid waste
        'msw_price_CHFpkg':msw_price, # [CHF/kg] price of municipal solid waste (msw); negative because it is a revenue.
        'msw_share_fossile': 0.478, # https://www.bafu.admin.ch/dam/en/sd-web/NlGIhzJ8OW0t/CO2_Emissionsfaktoren_THG_Inventar.pdf 
        'co2_content_msw': 0.3312, #co2 content of msw # https://www.bafu.admin.ch/dam/en/sd-web/NlGIhzJ8OW0t/CO2_Emissionsfaktoren_THG_Inventar.pdf
        'annual_msw_supply':'inf', # [kg] Annual municipal solid waste supply; Options: float value or 'inf'

        }

    }

# -----------------------------------------------------------------------------
# Sources for input data:
# Heating values (oil, gas, wood): Gesamtenergiestatistik 2022, Appendice 2
#   https://www.bfe.admin.ch/bfe/de/home/versorgung/statistik-und-geodaten/energiestatistiken/gesamtenergiestatistik.html
