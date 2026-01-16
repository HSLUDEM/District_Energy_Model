# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 10:17:25 2023

@author: UeliSchilt
"""

"""
- Generate plots and graphs
- Save output to files (csv, svg, res, ... )

"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

#import plotly.io as io
#io.renderers.default='svg' # set the default renderer to svg to display figures as static images

"""----------------------------------------------------------------------------
RESULTS:
"""

def input_to_file(dir_path, list_input_data, filename = 'input_data.csv'):
    
    """
    Writes input data to a dataframe and saves it in a csv file.
    
    Parameters
    ----------
        
    dir_path : string
        path to directory where file should be saved.
    list_input_data : list
        list containing input data. List must be generated using
        get_input_data() method from DistrictEnergyModel class in dem module.
    filename : string
        name of csv file. Must contain extension. (e.g. input_data.csv)

    Returns
    -------
    n/a
    """
    
    df = pd.DataFrame(list_input_data, columns=['parameter','value','description'])
    
    if dir_path == '':
        file = filename
    else:
        file = dir_path + '/' + filename
    
    df.to_csv(file)
    
    
def scen_techs_to_file(dir_path,
                       dict_scen_techs,
                       filetype = 'yaml',
                       filename = 'scen_techs'):
    
    """
    Writes chosen scenario technologies with parameters to a file and
    stores it in dir_path directory. File type can be chosen (.txt or .yaml).
    
    Parameters
    ----------
        
    dir_path : string
        Path to directory where file should be saved.
    dict_scen_techs : dictionary
        Dictionary with scenario factors used as model input.
    file_type: string
        Type of output file. Options: 'txt', 'yaml'
    filename : string
        Name of generated file. Must not contain extension.

    Returns
    -------
    n/a
    """
    
    if filetype == 'txt':
    
        dictionary = dict_scen_techs
        
        file = dir_path + '/' + filename + '.txt'
        
        with open(file, 'w') as f: 
            for key, value in dictionary.items():
                f.write('%s: %s\n' % (key, value))
                
    elif filetype == 'yaml':
            
        import yaml
        
        file_path = dir_path + '/' + filename + '.yaml'
        data = dict_scen_techs
        
        """Save a dictionary to a YAML file."""
        with open(file_path, 'w') as file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False)


def hourly_results_to_file(dir_path, df_scen, filename = 'hourly_results.csv'):
    
    """
    Writes hourly results to a csv file.
    
    Parameters
    ----------
        
    dir_path : string
        Path to directory where file should be saved.
    df_scen : pandas dataframe
        Dataframe with hourly values.
    filename : string
        Name of csv file. Must contain extension.

    Returns
    -------
    n/a
    """

    if dir_path == '':
        file = filename
    else:
        file = dir_path + '/' + filename
    
    df_scen.to_csv(file)
    
    
def annual_results_to_file(dir_path,
                           dict_yr,
                           filename = 'annual_results.txt'):
    
    """
    Writes annual results to a .txt file and stores it in
    dir_path directory.
    
    Parameters
    ----------
        
    dir_path : string
        Path to directory where file should be saved.
    dict_yr : dictionary
        Dictionary containing annual results. It is generated using
        the generate_scenario() method of the DistrictEnergyModel class
        in dem module.
    filename : string
        Name of txt file. Must contain extension (.txt).

    Returns
    -------
    n/a
    """
    
    dictionary = dict_yr
    
    file = dir_path + '/' + filename
    
    with open(file, 'w') as f: 
        for key, value in dictionary.items():
            f.write('%s: %s\n' % (key, value))

"""----------------------------------------------------------------------------
OPTIMISATION RESULTS:
"""

def total_costs_to_file(dir_path,
                        dict_total_costs,
                        filename = 'total_costs.txt'):
    """
    Writes total costs (incl. levelised costs) to a .txt file and stores it in
    dir_path directory.
    
    Parameters
    ----------
        
    dir_path : string
        Path to directory where file should be saved.
    dict_total_costs : dictionary
        Dictionary containing annual results. It is generated using
        the generate_scenario() method of the DistrictEnergyModel class
        in dem module.
    filename : string
        Name of txt file. Must contain extension (.txt).

    Returns
    -------
    n/a
    """
    
    dictionary = dict_total_costs
    
    file = dir_path + '/' + filename
    
    with open(file, 'w') as f: 
        for key, value in dictionary.items():
            f.write('%s: %s\n' % (key, value))
            
def pareto_metrics_to_csv_SUPERSEDED(
        dir_path,
        pareto_results,
        filename = 'pareto_metrics.csv'
        ):
    """
    Write the metrics of a multi-objective optimisation to a csv file.

    Parameters
    ----------
    dir_path : string
        Path to directory where file should be saved.
    pareto_results : list
        List of dicts containing the results from the pareto study.
    filename : str, optional
        Name of csv file. Must contain extension (.csv).
        The default is 'pareto_metrics.csv'.

    Returns
    -------
    None.

    """
    
    obj_weight_monetary = []
    obj_weight_co2 = []
    obj_value_monetary = []
    obj_value_co2 = []
    
    for res in pareto_results:
        obj_weight_monetary.append(res['obj_weight_monetary'])
        obj_weight_co2.append(res['obj_weight_co2'])
        obj_value_monetary.append(
            res['dict_total_costs']['monetary']['total']
            )
        obj_value_co2.append(
            res['dict_total_costs']['co2']['total']
            )
        
    dict_pareto_metrics = {
        'obj_weight_monetary':obj_weight_monetary,
        'obj_weight_co2':obj_weight_co2,
        'obj_value_monetary':obj_value_monetary,
        'obj_value_co2':obj_value_co2
        }
    
    df_pareto_metrics = pd.DataFrame(dict_pareto_metrics)
    
    file = dir_path + '/' + filename
    
    df_pareto_metrics.to_csv(file)
    
    
def pareto_metrics_to_csv(dir_path,
                          pareto_results,
                          filename = 'pareto_metrics.csv'
                          ):
    """
    Write the metrics of a multi-objective optimisation to a csv file.

    Parameters
    ----------
    dir_path : string
        Path to directory where file should be saved.
    pareto_results : list
        List of dicts containing the results from the pareto study.
    filename : str, optional
        Name of csv file. Must contain extension (.csv).
        The default is 'pareto_metrics.csv'.

    Returns
    -------
    None.

    """

    eps_n = []
    obj_value_monetary = []
    obj_value_co2 = []
    
    for res in pareto_results:
        eps_n.append(res['eps_n'])
        obj_value_monetary.append(
            res['dict_total_costs']['monetary']['total']
            )
        obj_value_co2.append(
            res['dict_total_costs']['co2']['total']
            )
        
    dict_pareto_metrics = {
        'eps_n':eps_n,
        'obj_value_monetary':obj_value_monetary,
        'obj_value_co2':obj_value_co2
        }
    
    df_pareto_metrics = pd.DataFrame(dict_pareto_metrics)
    
    file = dir_path + '/' + filename
    
    df_pareto_metrics.to_csv(file)
    
    
            
"""----------------------------------------------------------------------------
PLOTS:
"""

#%% Plot formatting


#------------------------------------------------------------------------------
# File formats:

# toggle_svg = True
toggle_svg = False
toggle_html = True


#------------------------------------------------------------------------------
# Initialise opacity:
opac = 1.0
opac_red_factor = 0.5 # reduced opacity 

#------------------------------------------------------------------------------
# Define colors:
# See: https://www.webucator.com/article/python-color-constants-module/
# See: https://johndecember.com/html/spec/colorrgbadec.html

col_renewable = f'rgba(50,205,50,{opac})' # 'limegreen'
col_nonrenewable = f'rgba(165, 42, 42,{opac})' # 'brown'

col_demand_electricity = 'black'
col_demand_ev_bounds = 'red'
col_demand_ev = 'green'
col_demand_heat = 'black'
col_demand_unmet = f'rgba(240,240,235,{opac})' # OESilver
col_demand_unmet_dhn = f'rgba(191,195,201,{opac})' # 

col_pv = f'rgba(238,238,0,{opac})' # 'yellow2'
col_pv_exp = f'rgba(238,238,0,{opac*opac_red_factor})' # 'yellow2'
col_wp =  f'rgba(102, 51, 153,{opac})'
col_wp_exp =  f'rgba(102, 51, 153,{opac*opac_red_factor})'
col_bm = f'rgba(0,112,0,{opac})'
col_bm_exp = f'rgba(0,112,0,{opac*opac_red_factor})'
col_hydro = f'rgba(0,0,255,{opac})'
col_hydro_exp = f'rgba(0,0,255,{opac*opac_red_factor})'
col_chp_gt = f'rgba(22,255,202,{opac})'
col_gtcp = f'rgba(255,204,0,{opac})'
col_gtcp_con = f'rgba(255,204,0,{opac})'
col_gtcp_waste = f'rgba(255,204,0,{opac*opac_red_factor})'

col_st = f'rgba(255,35,0,{opac})'
col_wte_con = f'rgba(162,213,117,{opac})'
col_wte_waste = f'rgba(162,213,117,{opac*opac_red_factor})'

col_chp_gt_con = f'rgba(22,255,202,{opac})'
col_chp_gt_waste = f'rgba(22,255,202,{opac*opac_red_factor})'

col_local_import = f'rgba(30,144,255,{opac})' # 'dodgerblue1'

col_cross_border_import = f'rgba(119,136,153,{opac})' # 'lightslategray'
col_CH_hydro = f'rgba(0,178,238,{opac})' # 'deepskyblue2'
col_CH_nuclear = f'rgba(205,133,0,{opac})' # 'orange3'
col_CH_wind =  f'rgba(140,20,252,{opac*opac_red_factor})'
col_CH_biomass = f'rgba(50,205,50,{opac})' # 'limegreen'
col_CH_other = f'rgba(162,205,90,{opac})' # 'darkolivegreen3'

col_heat_pump = f'rgba(134, 7, 32,{opac})' # '#860720'
col_heat_pump_cp = f'rgba(134, 7, 100,{opac})' # '#860720'
col_heat_pump_cp_lt = f'rgba(94, 7, 134,{opac})' # '#860720'
col_oil_boiler_cp = f'rgba(255,64,64,{opac})' # brown1
col_electric_heater_cp = f'rgba(102,205,170,{opac})' # aquamarine3
col_wood_boiler_cp = f'rgba(175,52,31,{opac})' # 

col_waste_heat = f'rgba(105, 92, 89,{opac})' # brown1
col_waste_heat_low_temperature = f'rgba(155, 186, 201,{opac})' # brown1

col_gas_boiler_cp = f'rgba(255,97,3,{opac})' # cadmiumorange
col_tes_chg = f'rgba(239, 0, 140,{opac*opac_red_factor})' # '#EF008C'
col_tes_dchg = f'rgba(239, 0, 140,{opac})' # '#EF008C'
col_tesdc_chg = f'rgba(239, 0, 100,{opac*opac_red_factor})' # '#EF008C'
col_tesdc_dchg = f'rgba(239, 0, 100,{opac})' # '#EF008C'
col_bes_chg = f'rgba(34, 153, 84,{opac*opac_red_factor})' # '#EF008C'
col_bes_dchg = f'rgba(34, 153, 84,{opac})' # '#EF008C'
col_electric_heater = f'rgba(102,205,170,{opac})' # aquamarine3
col_oil_boiler = f'rgba(255,64,64,{opac})' # brown1
col_gas_boiler = f'rgba(255,97,3,{opac})' # cadmiumorange
col_wood_boiler = f'rgba(205,133,0,{opac})' # 'orange3'
col_wood_boiler_sg = f'rgba(184,76,40,{opac})' #
col_wood_boiler_sg_con = f'rgba(184,76,40,{opac})' #
col_wood_boiler_sg_waste = f'rgba(184,76,40,{opac*opac_red_factor})' #

col_district_heating = f'rgba(0,178,238,{opac})' # 'deepskyblue2'
col_solar_thermal = f'rgba(238,238,0,{opac})' # 'yellow2'
col_solar_thermal_waste = f'rgba(238,238,0,{opac*opac_red_factor})' # 'yellow2'
col_other =  f'rgba(119,136,153,{opac})' # 'lightslategray'
col_hydrothermal_gasification = f'rgba(0,255,193,{opac})'

# -----------------------------------------------------------------------------
# Colors for Matplotlib:
    
# Initialize opacity
opac = 1.0
opac_red_factor = 0.5  # reduced opacity

# Define colors for Matplotlib
col_mpl_renewable = (50/255, 205/255, 50/255, opac)
col_mpl_nonrenewable = (165/255, 42/255, 42/255, opac)

col_mpl_demand_electricity = 'black'
col_mpl_demand_heat = 'black'
col_mpl_demand_unmet = (240/255, 240/255, 235/255, opac)
col_mpl_demand_unmet_dhn = (191/255, 195/255, 201/255, opac)

col_mpl_pv = (238/255, 238/255, 0/255, opac)
col_mpl_pv_exp = (238/255, 238/255, 0/255, opac * opac_red_factor)
col_mpl_wp = (102/255, 51/255, 153/255, opac)
col_mpl_wp_exp = (102/255, 51/255, 153/255, opac * opac_red_factor)
col_mpl_bm = (0/255, 112/255, 0/255, opac)
col_mpl_bm_exp = (0/255, 112/255, 0/255, opac * opac_red_factor)
col_mpl_hydro = (0/255, 0/255, 255/255, opac)
col_mpl_hydro_exp = (0/255, 0/255, 255/255, opac * opac_red_factor)
col_mpl_chp_gt = (22/255, 255/255, 202/255, opac)

col_mpl_gtcp = (255/255, 204/255, 0/255, opac)
col_mpl_gtcp_con = (255/255, 204/255, 0/255, opac)
col_mpl_gtcp_waste = (255/255, 204/255, 0/255, opac * opac_red_factor)

col_mpl_st = (255/255, 35/255, 0/255, opac)
col_mpl_wte_con = (162/255, 213/255, 117/255, opac)
col_mpl_wte_waste = (162/255, 213/255, 117/255, opac * opac_red_factor)

col_mpl_chp_gt_con = (22/255, 255/255, 202/255, opac)
col_mpl_chp_gt_waste = (22/255, 255/255, 202/255, opac * opac_red_factor)

col_mpl_local_import = (30/255, 144/255, 255/255, opac)
col_mpl_cross_border_import = (119/255, 136/255, 153/255, opac)
col_mpl_CH_hydro = (0/255, 178/255, 238/255, opac)
col_mpl_CH_nuclear = (205/255, 133/255, 0/255, opac)
col_mpl_CH_wind = (140/255, 20/255, 252/255, opac * opac_red_factor)
col_mpl_CH_biomass = (50/255, 205/255, 50/255, opac)
col_mpl_CH_other = (162/255, 205/255, 90/255, opac)

col_mpl_heat_pump = (134/255, 7/255, 32/255, opac)
col_mpl_heat_pump_cp = (134/255, 7/255, 100/255, opac)
col_mpl_heat_pump_cp_lt = (94/255, 7/255, 134/255, opac)

col_mpl_oil_boiler_cp = (255/255, 64/255, 64/255, opac)
col_mpl_electric_heater_cp = (102/255, 205/255, 170/255, opac)
col_mpl_wood_boiler_cp = (175/255, 52/255, 31/255, opac)

col_mpl_gas_boiler_cp = (255/255, 97/255, 3/255, opac)
col_mpl_waste_heat = (105/255, 92/255, 89/255, opac)
col_mpl_waste_heat_low_temperature = (155/255, 186/255, 201/255, opac)


col_mpl_tes_chg = (239/255, 0/255, 140/255, opac * opac_red_factor)
col_mpl_tes_dchg = (239/255, 0/255, 140/255, opac)
col_mpl_tesdc_chg = (239/255, 0/255, 100/255, opac * opac_red_factor)
col_mpl_tesdc_dchg = (239/255, 0/255, 100/255, opac)
col_mpl_bes_chg = (34/255, 153/255, 84/255, opac * opac_red_factor)
col_mpl_bes_dchg = (34/255, 153/255, 84/255, opac)
col_mpl_electric_heater = (102/255, 205/255, 170/255, opac)
col_mpl_oil_boiler = (255/255, 64/255, 64/255, opac)
col_mpl_gas_boiler = (255/255, 97/255, 3/255, opac)
col_mpl_wood_boiler = (205/255, 133/255, 0/255, opac)
col_mpl_wood_boiler_sg = (184/255, 76/255, 40/255, opac)
col_mpl_wood_boiler_sg_con = (184/255, 76/255, 40/255, opac)
col_mpl_wood_boiler_sg_waste = (184/255, 76/255, 40/255, opac* opac_red_factor)
col_mpl_district_heating = (0/255, 178/255, 238/255, opac)
col_mpl_solar_thermal = (238/255, 238/255, 0/255, opac)
col_mpl_other = (119/255, 136/255, 153/255, opac)
col_mpl_hydrothermal_gasification = (0/255, 255/255, 193/255, opac)


# -----------------------------------------------------------------------------

#Define size of svg image:
svg_width = 1000
svg_height = 500

keys_add_negative_if_available = ['v_e_pv_exp', 
                                  'v_e_pvrooftop_exp',
                                  'v_e_wp_exp', 
                                  'v_e_bm_exp', 
                                  'v_e_hydro_exp', 
                                  'u_e_bes',
                                  'u_h_tes',
                                  'u_h_tesdc',
                                  'v_h_wte_waste',
                                  'v_h_chpgt_waste',
                                  'v_h_st_gtcp_waste',
                                  'v_h_st_wbsg_waste',
                                  'v_h_solarthermalrooftop_exp']


electricity_balance_y=[
    'v_e_pv_cons',
    'v_e_pv_exp_negative',
    'v_e_pvrooftop_cons',
    'v_e_pvrooftop_exp_negative',
    'v_e_wp_cons',
    'v_e_wp_exp_negative',
    'v_e_bm_cons',
    'v_e_bm_exp_negative',
    'v_e_hydro_cons',
    'v_e_hydro_exp_negative',
    'v_e_bes',       
    'u_e_bes_negative',
    'v_e_chpgt',    
    # 'v_e_st',
    # 'v_e_st_gtcp',
    'v_e_gtcp_total',
    'v_e_st_wbsg',
    'v_e_wte',
    'm_e_ch_hydro',
    'm_e_ch_nuclear',
    'm_e_ch_wind',
    'm_e_ch_biomass',
    'm_e_ch_other',
    'm_e_cbimport',
    'd_e_unmet',
    ]
    
electricity_balance_legend_labels = [
    'PV consumption',
    'PV export',
    'PV rooftop consumption',
    'PV rooftop export',
    'Wind consumption',
    'Wind export',
    'Biomass consumption',
    'Biomass export',
    'Local hydro consumption',
    'Local hydro export',
    'Battery discharging',
    'Battery charging',
    'Gas turbine CHP (small)',
    # 'Steam Turbine',
    'Gas turbine CC',
    'Wood CHP',
    'WtE CHP',
    'CH hydro',
    'CH nuclear',
    'CH wind',
    'CH biomass',
    'CH other',
    'Cross-border import',
    'Unmet demand',
    ]

electricity_balance_colors = [
    col_pv,
    col_pv_exp,
    col_pv,
    col_pv_exp,
    col_wp,
    col_wp_exp,
    col_bm,
    col_bm_exp,
    col_hydro,
    col_hydro_exp,
    col_bes_dchg,
    col_bes_chg,
    col_chp_gt,
    # col_gtcp,
    # col_st,
    col_gtcp,
    col_wood_boiler_sg,
    col_wte_con,
    col_CH_hydro,
    col_CH_nuclear,
    col_CH_wind,
    col_CH_biomass,
    col_CH_other,
    col_cross_border_import,    
    col_demand_unmet        
    ]

electricity_balance_colors_mpl = [
    col_mpl_pv,
    col_mpl_pv_exp,
    col_mpl_pv,
    col_mpl_pv_exp,
    col_mpl_wp,
    col_mpl_wp_exp,
    col_mpl_bm,
    col_mpl_bm_exp,
    col_mpl_hydro,
    col_mpl_hydro_exp,
    col_mpl_bes_dchg,
    col_mpl_bes_chg,
    col_mpl_chp_gt,
    # col_mpl_gtcp,
    # col_mpl_st,
    col_mpl_gtcp,
    col_mpl_wood_boiler_sg,
    col_mpl_wte_con,
    col_mpl_CH_hydro,
    col_mpl_CH_nuclear,
    col_mpl_CH_wind,
    col_mpl_CH_biomass,
    col_mpl_CH_other,
    col_mpl_cross_border_import,    
    col_mpl_demand_unmet        
    ]

heat_balance_y=[
    'v_h_hp',
    'v_h_tesdc',
    'v_h_eh',
    'v_h_ob',
    'v_h_gb',
    'v_h_wb',
    # 'v_h_dh',
    'm_h_dh',
    'v_h_solarthermalrooftop',
    'v_h_solarthermalrooftop_exp_negative',
    'v_h_chpgt_con',
    'v_h_chpgt_waste_negative',
    # 'v_h_st',
    'v_h_st_gtcp_con',
    'v_h_st_gtcp_waste_negative',
    'v_h_st_wbsg_con',
    'v_h_st_wbsg_waste_negative',
    'v_h_wte_con',
    'v_h_wte_waste_negative',
    'v_h_hpcp',
    'v_h_hpcplt',
    'v_h_obcp',
    'v_h_ehcp',
    'v_h_wbcp',
    'v_h_gbcp',
    'v_h_wh',
    'u_h_tes_negative',
    'v_h_tes',
    'u_h_tesdc_negative',
    'v_h_bm',
    'v_h_other',
    'd_h_unmet',
    'd_h_unmet_dhn',
    ]

heat_sources_dhn=[
    'm_h_dh',
    # 'v_h_chpgt',
    # 'v_h_st',
    'v_h_chpgt_con',
    'v_h_chpgt_waste_negative',
    'v_h_st_gtcp_con',
    'v_h_st_gtcp_waste_negative',
    'v_h_st_wbsg_con',
    'v_h_st_wbsg_waste_negative',
    'v_h_wte_con',
    'v_h_wte_waste_negative'
    'v_h_hpcp',
    'v_h_hpcplt',
    'v_h_obcp',
    'v_h_ehcp',
    'v_h_wbcp',
    'v_h_gbcp',
    'v_h_wh',
    'v_h_tes',
    'v_h_bm',
    'u_h_tes_negative',
    'd_h_unmet_dhn'
    ]
   
heat_balance_legend_labels = [
    'Heat pump',
    'TES (decentralised) discharging',
    'Electric heater',
    'Oil boiler',
    'Gas boiler',
    'Wood boiler',
    'District heat (other source)',
    # 'Heat import',
    # 'District heating',
    # 'District heat import',
    'Solar thermal (roof top)',
    'Solar thermal (roof top) surplus heat',
    'Gas turbine CHP (small)',
    'Gas turbine CHP (small) surplus heat',
    # 'Steam Turbine',
    'Gas turbine CC',
    'Gas turbine CC surplus heat',
    'Wood CHP',
    'Wood CHP surplus heat',
    'WtE CHP',
    'WtE CHP surplus heat',
    'Heat pump (large scale)',
    'Heat pump (large scale, from low temperature)',
    'Oil boiler (large scale)',
    'Electric heater (large scale)',
    'Wood boiler (large scale)',
    'Gas boiler (large scale)',
    'Waste heat',
    'TES (DHN) charging',
    'TES (DHN) discharging',
    'TES (decentralised) charging',
    'Biomass',
    'Other',
    'Unmet demand',
    'Unmet demand DHN',
    ]

heat_balance_colors = [
    col_heat_pump,
    col_tesdc_dchg,
    col_electric_heater,
    col_oil_boiler,
    col_gas_boiler,
    col_wood_boiler,
    col_district_heating,
    col_solar_thermal,
    col_solar_thermal_waste,
    col_chp_gt_con,
    col_chp_gt_waste,
    # col_st,
    col_gtcp_con,
    col_gtcp_waste,
    col_wood_boiler_sg_con,
    col_wood_boiler_sg_waste,
    col_wte_con,
    col_wte_waste,
    col_heat_pump_cp,
    col_heat_pump_cp_lt,
    col_oil_boiler_cp,
    col_electric_heater_cp,
    col_wood_boiler_cp,
    col_gas_boiler_cp,
    col_waste_heat,
    col_tes_chg,
    col_tes_dchg,
    col_tesdc_chg,
    col_bm,
    col_other,
    col_demand_unmet,
    col_demand_unmet_dhn,
    ]

heat_balance_colors_mpl = [
    col_mpl_heat_pump,
    col_mpl_tesdc_dchg,
    col_mpl_electric_heater,
    col_mpl_oil_boiler,
    col_mpl_gas_boiler,
    col_mpl_wood_boiler,
    col_mpl_district_heating,
    col_mpl_solar_thermal,
    col_mpl_solar_thermal,
    col_mpl_chp_gt,
    col_mpl_chp_gt,
    # col_mpl_st,
    col_mpl_gtcp,
    col_mpl_wood_boiler_sg,
    col_mpl_wte_con,
    col_mpl_wte_waste,
    col_mpl_heat_pump_cp,
    col_mpl_heat_pump_cp_lt,
    col_mpl_oil_boiler_cp,
    col_mpl_electric_heater_cp,
    col_mpl_wood_boiler_cp,
    col_mpl_gas_boiler_cp,
    col_mpl_waste_heat,
    col_mpl_tes_chg,
    col_mpl_tes_dchg,
    col_mpl_tesdc_chg,
    col_mpl_bm,
    col_mpl_other,
    col_mpl_demand_unmet,
    col_mpl_demand_unmet_dhn,
    ]

# Pattern for district heating network:
patterns = ['/', '\\', '|', '-', '+', 'x', 'o', '.']
pattern_index = 1
DHN_label = 'District heating network'

#%% Plot functions

#------------------------------------------------------------------------------
# Electricity balance:
    
def plot_electricity_balance_hourly(df_scen,
                                    dir_path,
                                    output_svg = False,
                                    output_html = False,
                                    filename = 'electricity_balance_hourly',
                                    timeframe = False,
                                    timeframe_start = '01-01',
                                    timeframe_end = '12-31',
                                    axes_font_size = 16,
                                    title_font_size = 24
                                    ):
    
    """
    Generates a stacked bar plot with the hourly electricity supply split by
    sources, hiding legend labels for columns that only contain zero values.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    

    df_plot = df_scen.copy()
    
    for x in keys_add_negative_if_available:
        if x in df_plot.columns:
            df_plot[x+'_negative'] = -df_plot[x]

    if 'v_e_gtcp' in df_plot.columns:
        df_plot['v_e_gtcp_total'] = df_plot['v_e_gtcp'] + df_plot['v_e_st_gtcp']
    
    # Convert from kWh to MWh:
    df_plot = df_plot/1000
    
    # Identify available columns
    valid_columns = df_plot.columns.intersection(electricity_balance_y).tolist()
        
    # Use zip to filter the lists based on valid_columns
    filtered_data = [
        (col, label, color) 
        for col, label, color in zip(electricity_balance_y, electricity_balance_legend_labels, electricity_balance_colors) 
        if col in valid_columns
    ]
    
    # Unzip the filtered data back into separate lists
    electricity_balance_y_, electricity_balance_legend_labels_, electricity_balance_colors_ = map(list, zip(*filtered_data))
    
    # Identify nonzero columns:
    nonzero_mask = df_plot[electricity_balance_y_].sum() != 0

    # Filter out zero-value columns
    y = [col for col, nz in zip(electricity_balance_y_, nonzero_mask) if nz]
    legend_labels = [label for label, nz in zip(electricity_balance_legend_labels_, nonzero_mask) if nz]
    colors = [color for color, nz in zip(electricity_balance_colors_, nonzero_mask) if nz]
    
    # Ensure the index is in datetime format
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
    fig = px.bar(
        df_plot, 
        x=df_plot.index,
        y=y,
        # labels={'x': 'Time'},
        title='Hourly Electricity Supply',
        category_orders={'x': df_plot.index},
        #height=500,
        #width=800
        )
    
    # Update each trace individually (color, label):
    for i, trace_name in enumerate(y):
        fig.update_traces(
            marker_color=colors[i],
            marker_line_width=0,
            selector=dict(name=trace_name),
            name = legend_labels[i]
            )
        
    fig.add_trace(go.Scatter(
        x=df_plot.index,
        y=df_plot['d_e'],
        mode='lines',
        line=dict(color=col_demand_electricity, width=1),
        name='Total electricity demand'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_plot.index,
        y=df_plot['d_e_hh'] + df_plot['d_e_ev'],
        mode='lines',
        line=dict(color=col_demand_electricity, width=1, dash='dash'),
        name='Electricity household + EV demand'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_plot.index,
        y=df_plot['d_e_hh'],
        mode='lines',
        line=dict(color=col_demand_electricity, width=1, dash='dot'),
        name='Electricity household demand'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_plot.index,
        y=df_plot['d_e_ev'],
        mode='lines',
        line=dict(color=col_demand_ev, width=1, dash='solid'),
        name='EV demand'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_plot.index,
        y=df_plot['d_e_ev_cp'],
        mode='lines',
        line=dict(color=col_demand_ev_bounds, width=1, dash='dot'),
        name='EV demand - base load'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_plot.index,
        y=df_plot['d_e_ev_pd'],
        mode='lines',
        line=dict(color=col_demand_ev_bounds, width=1, dash='dashdot'),
        name='EV demand - min. load'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_plot.index,
        y=df_plot['d_e_ev_pu'],
        mode='lines',
        line=dict(color=col_demand_ev_bounds, width=1, dash='longdashdot'),
        name='EV demand - max. load'
    ))
    
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
   
    
    fig.update_xaxes(
        # title_text='Hour of the year',
        title_text = '',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Electricity supply [MWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot
    
# def plot_electricity_balance_hourly_share(
#         df_scen,
#         dir_path,
#         output_svg=False,
#         output_html=True,
#         filename='electricity_balance_hourly_share',
#         timeframe=False,
#         timeframe_start='01-01',
#         timeframe_end='12-31',
#         axes_font_size=16,
#         title_font_size=24
#     ):
#     """
#     Generates a stacked area plot showing the share of electricity sources over time.

#     Parameters
#     ----------
#     df_scen : pandas dataframe
#         Dataframe containing hourly values for electricity sources.
#     dir_path : string
#         Path to directory where plots will be saved.
#     output_svg : bool
#         If set to 'True', a plot in .svg format will be generated. Default: False
#     output_html : bool
#         If set to 'True', a plot in .html format will be generated. Default: True
#     filename : string
#         Name of the generated plot file(s).
#     timeframe : bool
#         If set to 'True', only the selected timeframe will be plotted.
#     timeframe_start : string
#         Beginning of selected timeframe.
#     timeframe_end : string
#         End of selected timeframe.
#     axes_font_size : int
#         Font size for x- and y-axis labels, tick-mark labels, and legend labels.
#     title_font_size : int
#         Font size of the plot title.
#     """
    
#     df_plot = df_scen.copy()
    
#     # Ensure index is datetime
#     df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
#     # Define electricity source columns
#     electricity_sources = [
#         'v_e_pv_cons', 'v_e_wp_cons', 'v_e_bm_cons', 'v_e_hydro_cons',
#         'v_e_chpgt', 'v_e_gtcp', 'v_e_st', 'v_e_wte', 'm_e_ch_hydro',
#         'm_e_ch_nuclear', 'm_e_ch_wind', 'm_e_ch_biomass', 'm_e_ch_other', 'm_e_cbimport'
#     ]
    
#     # Compute shares
#     df_plot['total_electricity'] = df_plot[electricity_sources].sum(axis=1)
#     df_plot[electricity_sources] = df_plot[electricity_sources].div(df_plot['total_electricity'], axis=0)
#     df_plot.fillna(0, inplace=True)  # Replace NaN values with zero
    
#     # Identify nonzero columns
#     nonzero_mask = df_plot[electricity_sources].sum() != 0
#     y = [col for col, nz in zip(electricity_sources, nonzero_mask) if nz]
#     legend_labels = [label for label, nz in zip(electricity_balance_legend_labels, nonzero_mask) if nz]
#     colors = [color for color, nz in zip(electricity_balance_colors, nonzero_mask) if nz]
    
#     # Generate stacked area chart
#     fig = px.area(
#         df_plot,
#         x=df_plot.index,
#         y=y,
#         title='Hourly Share of Electricity Sources',
#         labels={'value': 'Share', 'index': 'Time'},
#     )
    
#     # Update each trace individually (color, label)
#     for i, trace_name in enumerate(y):
#         fig.update_traces(
#             line=dict(color=colors[i]),
#             name=legend_labels[i],
#             selector=dict(name=trace_name)
#     )
    
#     # Update layout
#     fig.update_layout(
#         plot_bgcolor='white',
#         title_x=0.5,
#         legend_title_text='',
#         title_font_size=title_font_size,
#         legend_font=dict(size=axes_font_size)
#     )
    
#     fig.update_xaxes(
#         title_text='',
#         mirror=True,
#         ticks='outside',
#         showline=True,
#         linecolor='black',
#         gridcolor='lightgrey',
#         title_font_size=axes_font_size,
#         tickfont=dict(size=axes_font_size),
#         tickformat="%d %b %H:%M"
#     )
    
#     fig.update_yaxes(
#         title_text='Share of Electricity Sources',
#         range=[0, 1],
#         mirror=True,
#         ticks='outside',
#         showline=True,
#         linecolor='black',
#         gridcolor='lightgrey',
#         title_font_size=axes_font_size,
#         tickfont=dict(size=axes_font_size)
#     )
    
#     # Save outputs
#     file_svg = dir_path + '/' + filename + '.svg'
#     file_html = dir_path + '/' + filename + '.html'
    
#     if output_svg:
#         fig.write_image(file_svg)
    
#     if output_html:
#         fig.write_html(file_html)
    
#     del df_plot
    
# def plot_electricity_balance_hourly_share(
#         df_scen,
#         dir_path,
#         output_svg = False,
#         output_html = True,
#         filename = 'electricity_balance_hourly_share',
#         timeframe = False,
#         timeframe_start = '01-01',
#         timeframe_end = '12-31',
#         axes_font_size = 16,
#         title_font_size = 24
#         ):
    
#     """
#     Generates a stacked area plot showing the share of electricity sources over time.
#     Hiding legend labels for columns that only contain zero values.
    
#     Parameters
#     ----------
#     df_scen : pandas dataframe
#         Dataframe with resulting hourly values.
#     dir_path : string
#         Path to directory, where plots shall be saved.
#     output_svg : bool
#         If set to 'True', a (static) plot in .svg format will be generated.
#         Default: False
#     output_svg : bool
#         If set to 'True', a (dynamic) plot in .html format will be generated.
#         Default: True
#     filename : string
#         Name of generated plot file(s).
#     timeframe : bool
#         If set to 'True', only the selected timeframe will be plotted.
#         [not yet implemented]
#     timeframe_start : string
#         Beginning of selected timeframe.
#         [not yet implemented]
#     timeframe_end : string
#         End of selected timeframe.
#         [not yet implemented]
#     axes_font_size : int
#         Font size for x- and y-axis labels, tick-mark labels, and legend
#         labels.
#     title_font_size : int
#         Font size of plot title.

#     Returns
#     -------
#     n/a
#     """
    
#     df_plot = df_scen.copy()
#     df_plot['v_e_pv_exp_negative'] = -df_plot['v_e_pv_exp']
#     df_plot['v_e_wp_exp_negative'] = -df_plot['v_e_wp_exp']
#     df_plot['v_e_bm_exp_negative'] = -df_plot['v_e_bm_exp']
#     df_plot['v_e_hydro_exp_negative'] = -df_plot['v_e_hydro_exp']
#     df_plot['u_e_bes_negative'] = -df_plot['u_e_bes']
    
#     # Convert from kWh to MWh:
#     df_plot = df_plot/1000
    
#     # Identify nonzero columns
#     nonzero_mask = df_plot[electricity_balance_y].sum() != 0

#     # Filter out zero-value columns
#     y = [col for col, nz in zip(electricity_balance_y, nonzero_mask) if nz]
#     legend_labels = [label for label, nz in zip(electricity_balance_legend_labels, nonzero_mask) if nz]
#     colors = [color for color, nz in zip(electricity_balance_colors, nonzero_mask) if nz]
    
#     # y = electricity_balance_y    
#     # legend_labels = electricity_balance_legend_labels
#     # colors = electricity_balance_colors
    
#     # Ensure the index is in datetime format
#     df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
#     # Stacked area chart:
#     fig = px.area(
#         df_plot, 
#         x=df_plot.index,
#         y=y,
#         # labels={'x': 'Time'},
#         title='Hourly Share of Electricity Supply',
#         category_orders={'x': df_plot.index},
#         #height=500,
#         #width=800
#         )
    
#     # Update each trace individually (color, label):
#     for i, trace_name in enumerate(y):
#         fig.update_traces(
#             marker_color=colors[i],
#             marker_line_width=0,
#             selector=dict(name=trace_name),
#             name = legend_labels[i]
#             )
        
#     # fig.add_trace(go.Scatter(
#     #     x=df_plot.index,
#     #     y=df_plot['d_e'],
#     #     mode='lines',
#     #     line=dict(color=col_demand_electricity, width=1),
#     #     name='Total electricity demand'
#     # ))
    
#     # fig.add_trace(go.Scatter(
#     #     x=df_plot.index,
#     #     y=df_plot['d_e_hh'] + df_plot['d_e_ev'],
#     #     mode='lines',
#     #     line=dict(color=col_demand_electricity, width=1, dash='dash'),
#     #     name='Electricity household + EV demand'
#     # ))
    
#     # fig.add_trace(go.Scatter(
#     #     x=df_plot.index,
#     #     y=df_plot['d_e_hh'],
#     #     mode='lines',
#     #     line=dict(color=col_demand_electricity, width=1, dash='dot'),
#     #     name='Electricity household demand'
#     # ))
    
#     fig.update_layout(
#         plot_bgcolor='white',
#         # bargap = 0.01,
#         # bargroupgap = 0.00,
#         title_x=0.5,  # Center the title
#         legend_title_text='',
#         title_font_size=title_font_size,
#         legend_font=dict(size=axes_font_size)
#         )
    
   
    
#     fig.update_xaxes(
#         # title_text='Hour of the year',
#         title_text = '',
#         title_standoff=0,
#         mirror=True,
#         ticks='outside',
#         showline=True,
#         linecolor='black',
#         gridcolor='lightgrey',
#         title_font_size=axes_font_size,
#         tickfont=dict(size=axes_font_size),
#         tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
#     )
#     fig.update_yaxes(
#         title_text='Electricity supply [MWh]',
#         title_standoff=0,
#         mirror=True,
#         ticks='outside',
#         showline=True,
#         linecolor='black',
#         gridcolor='lightgrey',
#         title_font_size=axes_font_size,
#         tickfont=dict(size=axes_font_size)
#     )
    
#     file_svg = dir_path + '/' + filename + '.svg'
#     file_html = dir_path + '/' + filename + '.html'
    
#     if output_svg == True:
#         fig.write_image(file_svg, width=svg_width, height=svg_height)
    
#     if output_html == True:
#         fig.write_html(file_html)
    
#     del df_plot

def plot_electricity_balance_daily(
        df_scen,
        dir_path,
        output_svg = False,
        output_html = True,
        filename = 'electricity_balance_daily',
        axes_font_size = 16,
        title_font_size = 24
        ):
    
    """
    Generates a stacked bar plot with the daily electricity supply split by
    sources.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()

    for x in keys_add_negative_if_available:
        if x in df_plot.columns:
            df_plot[x+'_negative'] = -df_plot[x]

    if 'v_e_gtcp' in df_plot.columns:
        df_plot['v_e_gtcp_total'] = df_plot['v_e_gtcp'] + df_plot['v_e_st_gtcp']
    
    
    # Convert from kWh to MWh:
    df_plot = df_plot/1000
    
    #--------------------------------------------------------------------------
    # Calculate daily sums:

    # Calculate the day number (starting from 0) for each entry
    df_plot['day'] = (df_plot.index // 24)  # 24 hours in a day

    # Group by day and calculate the sum for each day
    df_daily_sum = df_plot.groupby('day').sum()
        
    # Shift the index by 1 (to start at day 1)
    df_daily_sum.index = df_daily_sum.index + 1
    
    #--------------------------------------------------------------------------
    # Create plot:
    
    # Identify available columns
    valid_columns = df_plot.columns.intersection(electricity_balance_y).tolist()
    
    
    # Use zip to filter the lists based on valid_columns
    filtered_data = [
        (col, label, color) 
        for col, label, color in zip(electricity_balance_y, electricity_balance_legend_labels, electricity_balance_colors) 
        if col in valid_columns
    ]
    
    # Unzip the filtered data back into separate lists
    electricity_balance_y_, electricity_balance_legend_labels_, electricity_balance_colors_ = map(list, zip(*filtered_data))
    
    # Identify nonzero columns:
    nonzero_mask = df_plot[electricity_balance_y_].sum() != 0

    # Filter out zero-value columns
    y = [col for col, nz in zip(electricity_balance_y_, nonzero_mask) if nz]
    legend_labels = [label for label, nz in zip(electricity_balance_legend_labels_, nonzero_mask) if nz]
    colors = [color for color, nz in zip(electricity_balance_colors_, nonzero_mask) if nz]
    
    # Ensure the index is in datetime format
    df_daily_sum.index = pd.date_range(start='2050-01-01', periods=len(df_daily_sum), freq='D')   
    
    fig = px.bar(
        df_daily_sum, 
        x=df_daily_sum.index,
        y=y,
        labels={'x': 'Time'},
        title='Daily Electricity Supply',
        category_orders={'x': df_daily_sum.index},
        #height=500,
        #width=1000
        )
  
    # Update each trace individually (color, label):
    for i, trace_name in enumerate(y):
        fig.update_traces(
            marker_color=colors[i],
            marker_line_width=0,
            selector=dict(name=trace_name),
            name = legend_labels[i]
            )
    
    fig.add_trace(go.Scatter(
        x=df_daily_sum.index,
        y=df_daily_sum['d_e'],
        mode='lines',
        line=dict(color=col_demand_electricity, width=1),
        name='Total electricity demand'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_daily_sum.index,
        y=df_daily_sum['d_e_hh'] + df_daily_sum['d_e_ev'],
        mode='lines',
        line=dict(color=col_demand_electricity, width=1, dash='dash'),
        name='Electricity household + EV demand'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_daily_sum.index,
        y=df_daily_sum['d_e_hh'],
        mode='lines',
        line=dict(color=col_demand_electricity, width=1, dash='dot'),
        name='Electricity household demand'
    ))
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size),
        #yaxis=dict(range=[-400, 800]) # TEMPORARY (fixed y-axis range)
        )
        
    # Create a line plot and add it to the existing figure
    #y = ['d_e']
    #fig.add_trace(
    #    px.line(
    #        df_daily_sum,
    #        x=df_daily_sum.index,
    #        y=y,
    #        labels={'x': 'Time'},
    #        line_shape='linear',  # You can choose the line shape you prefer
    #    ).data[0]
    #)

    
    fig.update_xaxes(
        # title_text='Day of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b"  # Formats as '3 Jan'
    )
    fig.update_yaxes(
        title_text='Electricity supply [MWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot
    del df_daily_sum


def plot_electricity_balance_weekly(df_scen,
                                    dir_path,
                                    output_svg = False,
                                    output_html = True,
                                    filename = 'electricity_balance_weekly',
                                    axes_font_size = 16,
                                    title_font_size = 24
                                    ):
    
    """
    Generates a stacked bar plot with the weekly electricity supply split by
    sources.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()

    for x in keys_add_negative_if_available:
        if x in df_plot.columns:
            df_plot[x+'_negative'] = -df_plot[x]

    if 'v_e_gtcp' in df_plot.columns:
        df_plot['v_e_gtcp_total'] = df_plot['v_e_gtcp'] + df_plot['v_e_st_gtcp']
    
    # Convert from kWh to GWh:
    df_plot = df_plot/1000000
    
    #--------------------------------------------------------------------------
    # Calculate weekly sums:

    # Calculate the week number (starting from 0) for each entry
    df_plot['week'] = (df_plot.index // 168)  # 168 hours in a week (24 hours * 7 days)

    # Group by week and calculate the sum for each week
    df_weekly_sum = df_plot.groupby('week').sum()
    
    if len(df_weekly_sum) > 52:
        # Last week consists of fewer days
        # Remove the last row (i.e. week)
        df_weekly_sum = df_weekly_sum.drop(df_weekly_sum.index[-1])
        
    # Shift the index by 1 (to start at week 1)
    df_weekly_sum.index = df_weekly_sum.index + 1
    
    #--------------------------------------------------------------------------
    # Create plot:
        
    # Identify available columns
    valid_columns = df_plot.columns.intersection(electricity_balance_y).tolist()
    
    
    # Use zip to filter the lists based on valid_columns
    filtered_data = [
        (col, label, color) 
        for col, label, color in zip(electricity_balance_y, electricity_balance_legend_labels, electricity_balance_colors) 
        if col in valid_columns
    ]
    
    # Unzip the filtered data back into separate lists
    electricity_balance_y_, electricity_balance_legend_labels_, electricity_balance_colors_ = map(list, zip(*filtered_data))

    # # Identify nonzero columns
    nonzero_mask = df_plot[electricity_balance_y_].sum() != 0

    # Filter out zero-value columns
    y = [col for col, nz in zip(electricity_balance_y_, nonzero_mask) if nz]
    legend_labels = [label for label, nz in zip(electricity_balance_legend_labels_, nonzero_mask) if nz]
    colors = [color for color, nz in zip(electricity_balance_colors_, nonzero_mask) if nz]

    # Ensure the index is in datetime format
    df_weekly_sum.index = pd.date_range(start='2050-01-01', periods=len(df_weekly_sum), freq='W')
    
    fig = px.bar(
        df_weekly_sum, 
        x=df_weekly_sum.index,
        y=y,
        labels={'x': 'Time'},
        title='Weekly Electricity Supply',
        category_orders={'x': df_weekly_sum.index},
        #height=400,
        #width=1200
        )
    
    # Update each trace individually (color, label):
    for i, trace_name in enumerate(y):
        fig.update_traces(
            marker_color=colors[i],
            marker_line_width=0,
            selector=dict(name=trace_name),
            name = legend_labels[i]
            )
        
    fig.add_trace(go.Scatter(
        x=df_weekly_sum.index,
        y=df_weekly_sum['d_e'],
        mode='lines',
        line=dict(color=col_demand_electricity, width=1),
        name='Total electricity demand'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_weekly_sum.index,
        y=df_weekly_sum['d_e_hh'] + df_weekly_sum['d_e_ev'],
        mode='lines',
        line=dict(color=col_demand_electricity, width=1, dash='dash'),
        name='Electricity household + EV demand'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_weekly_sum.index,
        y=df_weekly_sum['d_e_hh'],
        mode='lines',
        line=dict(color=col_demand_electricity, width=1, dash='dot'),
        name='Electricity household demand'
    ))

    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )


    fig.update_xaxes(
        # title_text='Week of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b",  # Example: "03 Jan"
    )
    fig.update_yaxes(
        title_text='Electricity supply [GWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot
    del df_weekly_sum
    
#------------------------------------------------------------------------------
# Heat balance:
    
# def plot_heat_balance_hourly(df_scen,
#                              dir_path,
#                              output_svg = False,
#                              output_html = True,
#                              filename = 'heat_balance_hourly',
#                              timeframe = False,
#                              timeframe_start = '01-01',
#                              timeframe_end = '12-31',
#                              axes_font_size = 16,
#                              title_font_size = 24
#                              ):
#     """
#     Generates a stacked bar plot with the hourly heat supply split by
#     sources, adding patterns for columns in heat_sources_dhn.

#     Parameters
#     ----------
#     df_scen : pandas dataframe
#         Dataframe with resulting hourly values.
#     dir_path : string
#         Path to directory, where plots shall be saved.
#     output_svg : bool
#         If set to 'True', a (static) plot in .svg format will be generated.
#         Default: False
#     output_html : bool
#         If set to 'True', a (dynamic) plot in .html format will be generated.
#         Default: True
#     filename : string
#         Name of generated plot file(s).
#     timeframe : bool
#         If set to 'True', only the selected timeframe will be plotted.
#         [not yet implemented]
#     axes_font_size : int
#         Font size for labels.
#     title_font_size : int
#         Font size of plot title.

#     Returns
#     -------
#     n/a
#     """

#     df_plot = df_scen.copy()
#     df_plot['u_h_tes_negative'] = -df_plot['u_h_tes']

#     df_plot = df_plot / 1000  # Convert kWh to MWh

#     nonzero_mask = df_plot[heat_balance_y].sum() != 0
#     y = [col for col, nz in zip(heat_balance_y, nonzero_mask) if nz]
#     legend_labels = [label for label, nz in zip(heat_balance_legend_labels, nonzero_mask) if nz]
#     colors = [color for color, nz in zip(heat_balance_colors, nonzero_mask) if nz]

#     df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')

#     patterns = ['/', '\\', '|', '-', '+', 'x', 'o', '.']
#     pattern_index = 0

#     fig = px.bar(
#         df_plot,
#         x=df_plot.index,
#         y=y,
#         labels={'x': 'Time'},
#         title='Hourly Heat Supply',
#         category_orders={'x': df_plot.index},
#         pattern_shape_sequence=patterns  # Apply patterns
#     )

#     for i, trace_name in enumerate(y):
#         fig.update_traces(
#             marker_color=colors[i],
#             marker_line_width=0,
#             selector=dict(name=trace_name),
#             name=legend_labels[i],
#             marker_pattern_shape=patterns[pattern_index % len(patterns)] if trace_name in heat_sources_dhn else ''
#         )
#         if trace_name in heat_sources_dhn:
#             pattern_index += 1

#     fig.update_layout(
#         plot_bgcolor='white',
#         bargap=0.01,
#         bargroupgap=0.00,
#         barmode='stack',
#         title_x=0.5,
#         legend_title_text='',
#         title_font_size=title_font_size,
#         legend_font=dict(size=axes_font_size)
#     )

#     fig.update_xaxes(title_text='', tickformat="%d %b %H:%M")
#     fig.update_yaxes(title_text='Heat supply [MWh]')

#     file_svg = f"{dir_path}/{filename}.svg"
#     file_html = f"{dir_path}/{filename}.html"

#     if output_svg:
#         fig.write_image(file_svg, width=svg_width, height=svg_height)
#     if output_html:
#         fig.write_html(file_html)

#     del df_plot

    
def plot_heat_balance_hourly(df_scen,
                             dir_path,
                             output_svg = False,
                             output_html = True,
                             filename = 'heat_balance_hourly',
                             timeframe = False,
                             timeframe_start = '01-01',
                             timeframe_end = '12-31',
                             axes_font_size = 16,
                             title_font_size = 24
                             ):
    
    """
    Generates a stacked bar plot with the hourly heat supply split by
    sources.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()

    for x in keys_add_negative_if_available:
        if x in df_plot.columns:
            df_plot[x+'_negative'] = -df_plot[x]

    # Convert from kWh to MWh:
    df_plot = df_plot/1000
    
    # Identify available columns
    valid_columns = df_plot.columns.intersection(heat_balance_y).tolist()
        
    # Use zip to filter the lists based on valid_columns
    filtered_data = [
        (col, label, color) 
        for col, label, color in zip(heat_balance_y, heat_balance_legend_labels, heat_balance_colors) 
        if col in valid_columns
    ]
    
    # Unzip the filtered data back into separate lists
    heat_balance_y_, heat_balance_legend_labels_, heat_balance_colors_ = map(list, zip(*filtered_data))

    # Identify nonzero columns
    nonzero_mask = df_plot[heat_balance_y_].sum() != 0

    # Filter out zero-value columns
    y = [col for col, nz in zip(heat_balance_y_, nonzero_mask) if nz]
    legend_labels = [label for label, nz in zip(heat_balance_legend_labels_, nonzero_mask) if nz]
    colors = [color for color, nz in zip(heat_balance_colors_, nonzero_mask) if nz]
    
    # y = heat_balance_y
    # legend_labels = heat_balance_legend_labels
    # colors = heat_balance_colors
    
    # Ensure the index is in datetime format
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')

    # patterns = ['/', '\\', '|', '-', '+', 'x', 'o', '.']
    # pattern_index = 1    
    
    fig = px.bar(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='Hourly Heat Supply',
        category_orders={'x': df_plot.index},
        pattern_shape_sequence=patterns,  # Apply patterns
        #height=400,
        #width=1200
        )
    
    fig.add_trace(go.Bar(
        x=[None], y=[None],
        name=DHN_label,
        marker=dict(pattern_shape=patterns[pattern_index], color='white'),
        showlegend=True
    ))
   
    # Update each trace individually (color, label):
    for i, trace_name in enumerate(y):
        fig.update_traces(
            marker_color=colors[i],
            marker_line_width=0,
            selector=dict(name=trace_name),
            name = legend_labels[i],
            marker_pattern_shape=patterns[pattern_index % len(patterns)] if trace_name in heat_sources_dhn else ''
            )
        # if trace_name in heat_sources_dhn:
        #     pattern_index += 1
        
    # Remove patterns from legend only (keep in bars)
    # for trace in fig.data:
    #     if trace.name != "District heating network" and isinstance(trace, go.Bar):
    #         trace.update(showlegend=True, legendgrouptitle=dict(text=trace.name), marker=dict(pattern_shape=""))
        
    fig.add_trace(go.Scatter(
        x=df_plot.index,
        y=df_plot['d_h'],
        mode='lines',
        line=dict(color=col_demand_heat, width=1),
        name='Total heat demand'
    ))
    
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Time',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Heat supply [MWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot


def plot_heat_balance_daily(df_scen,
                             dir_path,
                             output_svg = False,
                             output_html = False,
                             filename = 'heat_balance_daily',
                             axes_font_size = 16,
                             title_font_size = 24
                             ):
    
    """
    Generates a stacked bar plot with the daily heat supply split by
    sources.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()

    for x in keys_add_negative_if_available:
        if x in df_plot.columns:
            df_plot[x+'_negative'] = -df_plot[x]


    # Convert from kWh to MWh:
    df_plot = df_plot/1000
    
    #--------------------------------------------------------------------------
    # Calculate weekly sums:

    # Calculate the day number (starting from 0) for each entry
    df_plot['day'] = (df_plot.index // 24)  # 24 hours in a day

    # Group by day and calculate the sum for each day
    df_daily_sum = df_plot.groupby('day').sum()
        
    # Shift the index by 1 (to start at day 1)
    df_daily_sum.index = df_daily_sum.index + 1
    
    #--------------------------------------------------------------------------
    # Create plot:
        
    # Identify available columns
    valid_columns = df_plot.columns.intersection(heat_balance_y).tolist()
        
    # Use zip to filter the lists based on valid_columns
    filtered_data = [
        (col, label, color) 
        for col, label, color in zip(heat_balance_y, heat_balance_legend_labels, heat_balance_colors) 
        if col in valid_columns
    ]
    
    # Unzip the filtered data back into separate lists
    heat_balance_y_, heat_balance_legend_labels_, heat_balance_colors_ = map(list, zip(*filtered_data))

    # # Identify nonzero columns
    nonzero_mask = df_plot[heat_balance_y_].sum() != 0

    # Filter out zero-value columns
    y = [col for col, nz in zip(heat_balance_y_, nonzero_mask) if nz]
    legend_labels = [label for label, nz in zip(heat_balance_legend_labels_, nonzero_mask) if nz]
    colors = [color for color, nz in zip(heat_balance_colors_, nonzero_mask) if nz]

    # # Filter out zero-value columns
    # y = [col for col, nz in zip(heat_balance_y, nonzero_mask) if nz]
    # legend_labels = [label for label, nz in zip(heat_balance_legend_labels, nonzero_mask) if nz]
    # colors = [color for color, nz in zip(heat_balance_colors, nonzero_mask) if nz]

    # Ensure the index is in datetime format
    df_daily_sum.index = pd.date_range(start='2050-01-01', periods=len(df_daily_sum), freq='D')
        
    fig = px.bar(
        df_daily_sum, 
        x=df_daily_sum.index,
        y=y,
        labels={'x': 'Time'},
        title='Daily Heat Supply',
        category_orders={'x': df_daily_sum.index},
        pattern_shape_sequence=patterns,
        #height=400,
        #width=1200
        )
    
    fig.add_trace(go.Bar(
        x=[None], y=[None],
        name=DHN_label,
        marker=dict(pattern_shape=patterns[pattern_index], color='white'),
        showlegend=True,
        ))
      
    # Update each trace individually (color, label):
    for i, trace_name in enumerate(y):
        fig.update_traces(
            marker_color=colors[i],
            marker_line_width=0,
            selector=dict(name=trace_name),
            name = legend_labels[i],
            marker_pattern_shape=patterns[pattern_index % len(patterns)] if trace_name in heat_sources_dhn else ''
            )

    fig.add_trace(go.Scatter(
        x=df_daily_sum.index,
        y=df_daily_sum['d_h'],
        mode='lines',
        line=dict(color=col_demand_heat, width=1),
        name='Total heat demand'
    ))
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Day of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b",  # Example: "03 Jan"
    )
    fig.update_yaxes(
        title_text='Heat supply [MWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot
    del df_daily_sum

# def plot_heat_balance_daily_mpl(df_scen,
#                                  dir_path,
#                                  output_svg = False,
#                                  output_png = False,
#                                  filename = 'heat_balance_daily',
#                                  axes_font_size = 16,
#                                  title_font_size = 24
#                                  ):
    
#     import matplotlib.pyplot as plt
    
#     df_plot = df_scen.copy()
#     if 'u_h_tes' in df_plot.columns:
#         df_plot['u_h_tes_negative'] = -df_plot['u_h_tes']
#     if 'u_h_tesdc' in df_plot.columns:
#         df_plot['u_h_tesdc_negative'] = -df_plot['u_h_tesdc']
#     if 'v_h_wte_waste' in df_plot.columns:
#         df_plot['v_h_wte_waste_negative'] = -df_plot['v_h_wte_waste']
    
#     # Convert from kWh to MWh:
#     df_plot = df_plot/1000
    
#     #--------------------------------------------------------------------------
#     # Calculate weekly sums:

#     # Calculate the day number (starting from 0) for each entry
#     df_plot['day'] = (df_plot.index // 24)  # 24 hours in a day

#     # Group by day and calculate the sum for each day
#     df_daily_sum = df_plot.groupby('day').sum()
        
#     # Shift the index by 1 (to start at day 1)
#     df_daily_sum.index = df_daily_sum.index + 1
    
#     #--------------------------------------------------------------------------
#     # Create plot:
        
#     # Identify available columns
#     valid_columns = df_plot.columns.intersection(heat_balance_y).tolist()
        
#     # Use zip to filter the lists based on valid_columns
#     filtered_data = [
#         (col, label, color) 
#         for col, label, color in zip(heat_balance_y, heat_balance_legend_labels, heat_balance_colors_mpl) 
#         if col in valid_columns
#     ]
    
#     # Unzip the filtered data back into separate lists
#     heat_balance_y_, heat_balance_legend_labels_, heat_balance_colors_ = map(list, zip(*filtered_data))

#     # # Identify nonzero columns
#     nonzero_mask = df_plot[heat_balance_y_].sum() != 0

#     # Filter out zero-value columns
#     y = [col for col, nz in zip(heat_balance_y_, nonzero_mask) if nz]
#     legend_labels = [label for label, nz in zip(heat_balance_legend_labels_, nonzero_mask) if nz]
#     colors = [color for color, nz in zip(heat_balance_colors_, nonzero_mask) if nz]

#     # # Filter out zero-value columns
#     # y = [col for col, nz in zip(heat_balance_y, nonzero_mask) if nz]
#     # legend_labels = [label for label, nz in zip(heat_balance_legend_labels, nonzero_mask) if nz]
#     # colors = [color for color, nz in zip(heat_balance_colors, nonzero_mask) if nz]

#     # Ensure the index is in datetime format
#     df_daily_sum.index = pd.date_range(start='2050-01-01', periods=len(df_daily_sum), freq='D')

#     # Create the plot
#     fig, ax = plt.subplots(figsize=(12, 6))
    
#     # Plot stacked bars
#     bottom = pd.Series(0, index=df_daily_sum.index)
#     for col, label, color in zip(y, legend_labels, colors):
#         ax.bar(df_daily_sum.index, df_daily_sum[col], bottom=bottom, label=label, color=color, width=1)
#         bottom += df_daily_sum[col]
    
#     # Plot heat demand line
#     ax.plot(df_daily_sum.index, df_daily_sum['d_h'], color=col_demand_heat, linewidth=1, label='Total heat demand')
    
#     # Style plot
#     ax.set_title('Daily Heat Supply', fontsize=title_font_size)
#     ax.set_ylabel('Heat supply [MWh]', fontsize=axes_font_size)
#     ax.tick_params(axis='x', labelsize=axes_font_size)
#     ax.tick_params(axis='y', labelsize=axes_font_size)
#     ax.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5)
#     ax.legend(fontsize=axes_font_size)
#     fig.autofmt_xdate()
    
#     # Save files
#     file_svg = f"{dir_path}/{filename}.svg"
#     file_png = f"{dir_path}/{filename}.png"
    
#     if output_svg:
#         fig.savefig(file_svg, format='svg', bbox_inches='tight')
    
#     if output_png:
#         fig.savefig(file_png, format='png', bbox_inches='tight',dpi=300)  # Always save PNG
    
#     plt.close(fig)


def plot_heat_balance_daily_mpl(df_scen,
                                 dir_path,
                                 output_svg=False,
                                 output_png=False,
                                 filename='heat_balance_daily',
                                 axes_font_size=16,
                                 title_font_size=24,
                                 custom_heat_balance=False,
                                 ):
    
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd

    df_plot = df_scen.copy()
    
    for x in keys_add_negative_if_available:
        if x in df_plot.columns:
            df_plot[x+'_negative'] = -df_plot[x]


    if custom_heat_balance:
        filename = 'dhn_heat_supply'
        heat_balance_y_0 = ['v_h_st_gtcp', 'v_h_st_wbsg', 'v_h_wte_con', 'v_h_wte_waste_negative', 'u_h_tes_negative', 'v_h_tes']
        # heat_balance_legend_labels_0 = ['Gas turbine CC', 'Wood CHP', 'WtE CHP', 'WtE CHP surplus heat', 'TES charging', 'TES discharging']
        heat_balance_legend_labels_0 = ['Gas turbine CC', 'Wood CHP', 'WtE CHP', 'WtE CHP surplus heat', 'TES charging', 'TES discharging']
        heat_balance_colors_mpl_0 = [
            col_mpl_gtcp,
            col_mpl_wood_boiler_sg,
            col_mpl_wte_con,
            col_mpl_wte_waste,
            col_mpl_tes_chg,
            col_mpl_tes_dchg,
            ]
    else:
        heat_balance_y_0 = heat_balance_y
        heat_balance_legend_labels_0 = heat_balance_legend_labels
        heat_balance_colors_mpl_0 = heat_balance_colors_mpl
        
    # Convert from kWh to MWh
    df_plot = df_plot / 1000

    # Calculate the day number (starting from 0) for each entry
    df_plot['day'] = (df_plot.index // 24)

    # Group by day and calculate the sum for each day
    df_daily_sum = df_plot.groupby('day').sum()
    df_daily_sum.index = pd.date_range(start='2050-01-01', periods=len(df_daily_sum), freq='D')

    # Filter and categorize positive and negative columns
    valid_columns = df_plot.columns.intersection(heat_balance_y_0).tolist()
    filtered_data = [
        (col, label, color)
        for col, label, color in zip(heat_balance_y_0, heat_balance_legend_labels_0, heat_balance_colors_mpl_0)
        if col in valid_columns
    ]
    heat_balance_y_, heat_balance_legend_labels_, heat_balance_colors_ = map(list, zip(*filtered_data))
    
    nonzero_mask = df_plot[heat_balance_y_].sum() != 0
    y = [col for col, nz in zip(heat_balance_y_, nonzero_mask) if nz]
    legend_labels = [label for label, nz in zip(heat_balance_legend_labels_, nonzero_mask) if nz]
    colors = [color for color, nz in zip(heat_balance_colors_mpl_0, nonzero_mask) if nz]

    # Separate positive and negative bars
    y_pos = [col for col in y if (df_daily_sum[col] >= 0).all()]
    y_neg = [col for col in y if col not in y_pos]

    legend_pos = [legend_labels[y.index(col)] for col in y_pos]
    legend_neg = [legend_labels[y.index(col)] for col in y_neg]
    colors_pos = [colors[y.index(col)] for col in y_pos]
    colors_neg = [colors[y.index(col)] for col in y_neg]

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot positive stacked bars
    bottom_pos = pd.Series(0, index=df_daily_sum.index)
    for col, label, color in zip(y_pos, legend_pos, colors_pos):
        ax.bar(df_daily_sum.index, df_daily_sum[col], bottom=bottom_pos, label=label, color=color, width=1)
        bottom_pos += df_daily_sum[col]

    # Plot negative stacked bars
    bottom_neg = pd.Series(0, index=df_daily_sum.index)
    for col, label, color in zip(y_neg, legend_neg, colors_neg):
        ax.bar(df_daily_sum.index, df_daily_sum[col], bottom=bottom_neg, label=label, color=color, width=1)
        bottom_neg += df_daily_sum[col]

    # Plot heat demand line
    if custom_heat_balance==False:
        if 'd_h' in df_daily_sum.columns:
            ax.plot(df_daily_sum.index, df_daily_sum['d_h'], color=col_demand_heat, linewidth=1, label='Total heat demand')
    elif custom_heat_balance==True:
        if 'd_h' in df_daily_sum.columns:
            ax.plot(df_daily_sum.index, df_daily_sum['d_h']*0.18, color=col_demand_heat, linewidth=1, label='DHN heat demand')

    # Style plot
    # ax.set_title('Daily Heat Supply', fontsize=title_font_size)
    ax.set_ylabel('Heat supply [MWh]', fontsize=axes_font_size)
    ax.tick_params(axis='x', labelsize=axes_font_size)
    ax.tick_params(axis='y', labelsize=axes_font_size)
    ax.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5)
    ax.set_xlim(df_daily_sum.index[0], df_daily_sum.index[-1])
    # fig.autofmt_xdate()

    # Format x-axis ticks as abbreviated month names
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    fig.autofmt_xdate(rotation=0)
    
    # Center-align month labels over ticks
    for label in ax.get_xticklabels():
        label.set_horizontalalignment('center')

    # Move legend outside plot
    ax.legend(
        fontsize=axes_font_size,
        # bbox_to_anchor=(1.02, 1),
        # loc='upper left',
        loc='upper center',
        borderaxespad=0
    )
    
    ymin, ymax = ax.get_ylim()
    y_range = ymax - ymin
    ax.set_ylim(ymin - 0.05 * y_range, ymax + 0.05 * y_range)

    # Save files
    file_svg = f"{dir_path}/{filename}.svg"
    file_png = f"{dir_path}/{filename}.png"

    if output_svg:
        fig.savefig(file_svg, format='svg', bbox_inches='tight')
    if output_png:
        fig.savefig(file_png, format='png', bbox_inches='tight', dpi=300)

    plt.close(fig)
    
    



def plot_heat_balance_weekly(df_scen,
                             dir_path,
                             output_svg = False,
                             output_html = False,
                             filename = 'heat_balance_weekly',
                             axes_font_size = 16,
                             title_font_size = 24
                             ):
    
    """
    Generates a stacked bar plot with the weekly heat supply split by
    sources.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()

    for x in keys_add_negative_if_available:
        if x in df_plot.columns:
            df_plot[x+'_negative'] = -df_plot[x]


    # Convert from kWh to GWh:
    df_plot = df_plot/1000000
    
    #--------------------------------------------------------------------------
    # Calculate weekly sums:

    # Calculate the week number (starting from 0) for each entry
    df_plot['week'] = (df_plot.index // 168)  # 168 hours in a week (24 hours * 7 days)

    # Group by week and calculate the sum for each week
    df_weekly_sum = df_plot.groupby('week').sum()
    
    if len(df_weekly_sum) > 52:
        # Last week consists of fewer days
        # Remove the last row (i.e. week)
        df_weekly_sum = df_weekly_sum.drop(df_weekly_sum.index[-1])
        
    # Shift the index by 1 (to start at week 1)
    df_weekly_sum.index = df_weekly_sum.index + 1
    
    #--------------------------------------------------------------------------
    # Create plot:
        
    # Identify available columns
    valid_columns = df_plot.columns.intersection(heat_balance_y).tolist()
        
    # Use zip to filter the lists based on valid_columns
    filtered_data = [
        (col, label, color) 
        for col, label, color in zip(heat_balance_y, heat_balance_legend_labels, heat_balance_colors) 
        if col in valid_columns
    ]
    
    # Unzip the filtered data back into separate lists
    heat_balance_y_, heat_balance_legend_labels_, heat_balance_colors_ = map(list, zip(*filtered_data))
    
    # # Identify nonzero columns
    nonzero_mask = df_plot[heat_balance_y_].sum() != 0

    # Filter out zero-value columns
    y = [col for col, nz in zip(heat_balance_y_, nonzero_mask) if nz]
    legend_labels = [label for label, nz in zip(heat_balance_legend_labels_, nonzero_mask) if nz]
    colors = [color for color, nz in zip(heat_balance_colors_, nonzero_mask) if nz]

    # # Filter out zero-value columns
    # y = [col for col, nz in zip(heat_balance_y, nonzero_mask) if nz]
    # legend_labels = [label for label, nz in zip(heat_balance_legend_labels, nonzero_mask) if nz]
    # colors = [color for color, nz in zip(heat_balance_colors, nonzero_mask) if nz]

    # Ensure the index is in datetime format
    df_weekly_sum.index = pd.date_range(start='2050-01-01', periods=len(df_weekly_sum), freq='W')
        
    fig = px.bar(
        df_weekly_sum, 
        x=df_weekly_sum.index,
        y=y,
        labels={'x': 'Time'},
        title='Weekly Heat Supply',
        category_orders={'x': df_weekly_sum.index},
        pattern_shape_sequence=patterns,
        #height=400,
        #width=1200
        )
    
    fig.add_trace(go.Bar(
        x=[None], y=[None],
        name=DHN_label,
        marker=dict(pattern_shape=patterns[pattern_index], color='white'),
        showlegend=True,
        ))
     
    # Update each trace individually (color, label):
    for i, trace_name in enumerate(y):
        fig.update_traces(
            marker_color=colors[i],
            marker_line_width=0,
            selector=dict(name=trace_name),
            name = legend_labels[i],
            marker_pattern_shape=patterns[pattern_index % len(patterns)] if trace_name in heat_sources_dhn else ''
            )

    fig.add_trace(go.Scatter(
        x=df_weekly_sum.index,
        y=df_weekly_sum['d_h'],
        mode='lines',
        line=dict(color=col_demand_heat, width=1),
        name='Total heat demand'
    ))
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )    
    fig.update_xaxes(
        # title_text='Week of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b",  # Example: "03 Jan"
    )
    fig.update_yaxes(
        title_text='Heat supply [GWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
        
    del df_plot
    del df_weekly_sum


def plot_tes_sos_hourly(df_scen,
                        dir_path,
                        output_svg = False,
                        output_html = False,
                        filename = 'tes_sos_hourly',
                        timeframe = False,
                        timeframe_start = '01-01',
                        timeframe_end = '12-31',
                        axes_font_size = 16,
                        title_font_size = 24
                        ):
    
    """
    Generates a line plot of the thermal energy storage state of charge.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()
    
    # Convert from kWh to MWh:
    df_plot = df_plot/1000
    
    # Ensure the index is in datetime format
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
    if 'q_h_tes' in df_plot.columns:
        pass
    else:
        df_plot['q_h_tes'] = 0
        
    y=['q_h_tes']

    fig = px.line(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='TES - Stored Energy (Hourly)',
        category_orders={'x': df_plot.index},
        #height=400,
        #width=1200
        )
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Hour of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Stored heat [MWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot

def plot_tes_cyclecount_hourly(df_scen,
                        dir_path,
                        output_svg = False,
                        output_html = True,
                        filename = 'tes_cyclecount_hourly',
                        timeframe = False,
                        timeframe_start = '01-01',
                        timeframe_end = '12-31',
                        axes_font_size = 16,
                        title_font_size = 24
                        ):
    
    """
    Generates a line plot of the thermal energy storage number of discharge cycles.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()
    
    #Calculation of the hourly differences in state of charge, take only positive values

    keywords = ['sos_tesdc', 'sos_tes']
    corresponding_ys = ['TES Cyclecount (decentralized)', 'TES Cyclecount (district heating)']
    data = {}
    y = []

    for k in range(len(keywords)):
        if keywords[k] in df_scen.columns:
            dt_loc = df_scen[keywords[k]].diff()[1:]
            dt_loc = ((dt_loc + np.abs(dt_loc))/2.0).cumsum()
            data[corresponding_ys[k]] = dt_loc
            y.append(corresponding_ys[k])
    # dt_tesdc = df_scen['sos_tesdc'].diff()[1:]
    # dt_tesdc = ((dt_tesdc + np.abs(dt_tesdc))/2.0).cumsum()
    
    # dt_tes = df_scen['sos_tes'].diff()[1:]
    # dt_tes = ((dt_tes + np.abs(dt_tes))/2.0).cumsum()

    df_plot = pd.DataFrame(data = data, index = df_scen.index[1:])
    
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
    fig = px.line(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='TES - Cycle count',
        category_orders={'x': df_plot.index},
        #height=400,
        #width=1200
        )
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Hour of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Cycle count [#]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot


def plot_tes_and_bes_cumsum_hourly(df_scen,
                        dir_path,
                        output_svg = False,
                        output_html = True,
                        filename = 'tes_and_bes_cumsum_hourly',
                        timeframe = False,
                        timeframe_start = '01-01',
                        timeframe_end = '12-31',
                        axes_font_size = 16,
                        title_font_size = 24
                        ):
    
    """
    Generates a line plot of the total charged energy both for the two TES types and BES, in one plot.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()
    
    pd.set_option('display.max_rows', 1000)

    data = {}

    keywords=['q_h_tesdc', 'q_h_tes', 'q_e_bes']
    colors = ['#1f77b4','#87CEEB','#d62728','#ff7f0e','#2ca02c','#66ff00']
    y = []
    colors_y = {}
    colorindex = 0
    for keyword in keywords:
        if keyword in df_scen.columns:
            dt_loc = df_scen[keyword].diff()[1:]/1000
            dt_loc = ((dt_loc + np.abs(dt_loc))/2.0).cumsum()
            data[keyword + " charged"] = dt_loc + df_scen[keyword].iloc[0]/1000

            dt_loc = df_scen[keyword].diff()[1:]/1000
            dt_loc = ((-dt_loc + np.abs(-dt_loc))/2.0).cumsum()
            data[keyword + " discharged"] = dt_loc

            y.append(keyword+ " charged")
            y.append(keyword+ " discharged")

            colors_y[keyword+ " charged"] = colors[colorindex]
            colorindex += 1
            colors_y[keyword+ " discharged"] = colors[colorindex]


            colorindex+= 1
  
    df_plot = pd.DataFrame(data = data, index = df_scen.index[1:])
    
    # Ensure the index is in datetime format
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
    # y=['q_h_tesdc', 'q_h_tes', 'q_e_bes']

    fig = px.line(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='TES and BES - Cumulative charged and discharged energy',
        category_orders={'x': df_plot.index},
        color_discrete_map= colors_y,
        #height=400,
        #width=1200
        )
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Hour of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Energy [MWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot


def plot_tesdc_sos_hourly(
        df_scen,
        dir_path,
        output_svg = False,
        output_html = False,
        filename = 'tesdc_sos_hourly',
        timeframe = False,
        timeframe_start = '01-01',
        timeframe_end = '12-31',
        axes_font_size = 16,
        title_font_size = 24
        ):
    
    """
    Generates a line plot of the thermal energy storage (decentralised) state
    of charge.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()
    
    # Convert from kWh to MWh:
    df_plot = df_plot/1000
    
    # Ensure the index is in datetime format
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
    if 'q_h_tesdc' in df_plot.columns:
        pass
    else:
        df_plot['q_h_tesdc'] = 0
    
    y=['q_h_tesdc']

    fig = px.line(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='TES - Stored Energy (Hourly)',
        category_orders={'x': df_plot.index},
        #height=400,
        #width=1200
        )
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Hour of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Stored heat [MWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot
    

def plot_bes_sos_hourly(df_scen,
                        dir_path,
                        output_svg = False,
                        output_html = False,
                        filename = 'bes_sos_hourly',
                        timeframe = False,
                        timeframe_start = '01-01',
                        timeframe_end = '12-31',
                        axes_font_size = 16,
                        title_font_size = 24
                        ):
    
    """
    Generates a line plot of the battery energy storage state of charge.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()
    
    # Convert from kWh to MWh:
    df_plot = df_plot/1000
    
    # Ensure the index is in datetime format
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
    if 'q_e_bes' in df_plot.columns:
        pass
    else:
        df_plot['q_e_bes'] = 0
    
    y=['q_e_bes']
        
    fig = px.line(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='BES - Stored Energy (Hourly)',
        category_orders={'x': df_plot.index},
        #height=400,
        #width=1200
        )
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Hour of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Stored electricity [MWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot


def plot_gtes_sos_hourly(df_scen,
                        dir_path,
                        output_svg = False,
                        output_html = False,
                        filename = 'gtes_sos_hourly',
                        timeframe = False,
                        timeframe_start = '01-01',
                        timeframe_end = '12-31',
                        axes_font_size = 16,
                        title_font_size = 24
                        ):
    
    """
    Generates a line plot of the gas tank energy storage state of charge.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()
    
    # Convert from kWh to MWh:
    df_plot = df_plot/1000
    
    # Ensure the index is in datetime format
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
    if 'q_gas_gtes' in df_plot.columns:
        pass
    else:
        df_plot['q_gas_gtes'] = 0
    
    y=['q_gas_gtes']
        
    fig = px.line(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='GTES - Stored Gas (Hourly)',
        category_orders={'x': df_plot.index},
        #height=400,
        #width=1200
        )
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Hour of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Stored gas [k gas unit]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot

def plot_ws_sos_hourly(df_scen,
                        dir_path,
                        output_svg = False,
                        output_html = False,
                        filename = 'ws_sos_hourly',
                        timeframe = False,
                        timeframe_start = '01-01',
                        timeframe_end = '12-31',
                        axes_font_size = 16,
                        title_font_size = 24
                        ):
    
    """
    Generates a line plot of the wood storage state of charge.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()
    
    # Convert from kWh to MWh:
    df_plot = df_plot/1000
    
    # Ensure the index is in datetime format
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='H')
    
    if 'q_wd_ws' in df_plot.columns:
        pass
    else:
        df_plot['q_wd_ws'] = 0
    
    y=['q_wd_ws']
        
    fig = px.line(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='WS - Stored Wood (Hourly)',
        category_orders={'x': df_plot.index},
        #height=400,
        #width=1200
        )
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Hour of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Stored wood [k wood unit]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot

def plot_hes_sos_hourly(df_scen,
                        dir_path,
                        output_svg = False,
                        output_html = False,
                        filename = 'hes_sos_hourly',
                        timeframe = False,
                        timeframe_start = '01-01',
                        timeframe_end = '12-31',
                        axes_font_size = 16,
                        title_font_size = 24
                        ):
    
    """
    Generates a line plot of the hydrogen energy storage state of charge.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()
    
    # Convert from kWh to MWh:
    df_plot = df_plot/1000
    
    # Ensure the index is in datetime format
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
    if 'q_hyd_hes' in df_plot.columns:
        pass
    else:
        df_plot['q_hyd_hes'] = 0
    
    y=['q_hyd_hes']
        
    fig = px.line(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='HES - Stored Hydrogen (Hourly)',
        category_orders={'x': df_plot.index},
        #height=400,
        #width=1200
        )
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Hour of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Stored hydrogen [k gas unit]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot



def plot_sankey_total(df_scen,
    dir_path,
    output_svg = False,
    output_html = False,
    filename = 'sankey',
    timeframe = False,
    timeframe_start = '01-01',
    timeframe_end = '12-31',
    axes_font_size = 16,
    title_font_size = 24,
    ):

    """
    Generates a sankey diagram representing the overall energy flows in the system.
    It does not distinguish between district heat and local heat.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """


    df_plot = df_scen.copy().sum(axis = 0)
    
    
    # Convert from kWh to MWh:
    df_plot = df_plot/1000

    # print(df_plot.index.values)

    #In- Out- Flows into or out of devices
    flows_to_consider = ['u_e_bes','u_gas_gtes','v_gas_gtes',
                         'u_wd_ws','v_wd_ws',
                         'u_hyd_hes','v_hyd_hes',
                         'u_e_eh','u_e_hp','u_e_hpcp','u_e_hpcplt','u_e_hydp',
                         'u_e_wguh','u_gas_chpgt','u_gas_gb','u_gas_gtcp',
                         'u_oil_obcp', 'u_gas_gbcp','u_e_ehcp', 
                         'u_wd_wbcp',
                         #'u_gas_gtcp_kg',
                         'u_h_tes','u_h_tesdc',
                         'u_msw_wte','u_oil_ob','u_steam_st',
                         'u_wd_wb', 
                         'v_h_eh', 'v_h_gb', 'v_h_hp', 
                         'v_h_hpcp', 
                         'v_h_hpcplt', 
                         'u_hlt_hpcplt', 'v_h_ob', 'v_h_solarthermalrooftop', 'v_h_tes', 
                         'v_h_tesdc', 'v_h_wb',  'v_h_obcp', 'v_h_ehcp',
                         'v_h_wbcp',
                         'v_h_gbcp',
                         'v_h_wguh', 'v_h_wte', 'v_e_bes',  
                         'v_e_chpgt', 'v_e_gtcp', 'v_e_hydro', 
                         'v_e_pv', 'v_e_st', 
                         'v_e_wp', 'v_e_wte', 'v_hyd_hydp', 'v_steam_gtcp',
                         'v_e_wguc','u_hyd_wguh',
                         'u_e_wgu','u_e_aguh','u_hyd_aguh',
                         'v_gas_agu','v_h_aguc', 
                         'v_h_aguh', 'v_gas_aguh', 'v_e_aguc',
                         'u_wd_wgu','u_wd_wguc','u_wd_wguh',
                         'v_gas_wgu', 'v_gas_wguh',
                         'v_h_wgu', 'v_h_wguc','v_gas_hg',
                         'v_steam_wbsg', 'u_wd_wbsg', 'v_h_other', 'v_h_wh',
                         'v_h_chpgt', 
                         'v_h_st', #'v_h_chpgt_waste', 'v_h_chpgt', 
                         'v_hlt_whlt',
                         ]

    env_heat_flows = ['u_h_hp', 'u_h_hpcp']



    #same, but when the energy carrier has two words (wet biomass)
    flows_to_consider_two_word_carrier = ['u_wet_bm_agu', 'u_wet_bm_aguc' ,
                                          'u_wet_bm_aguh', 'u_wet_bm_hg'] #'u_h_hpcp',

    #relevant devices
    link_nodes_to_consider = ['hp', 'aguh', 'bes', 'eh', 'hpcp', 'hpcplt',
                              'hydp', 'wgu', 'wguh', 'chpgt', 'gb', 
                              'gtcp', 'tes', 'tesdc', 'wte', 'ob', 
                              'st', 'wb', 'wguc', 'agu', 'hg', 'aguc', 
                              'bm', 'dh', 'solarthermalrooftop', 'hydro', 'pv', 'wp',
                              'obcp', 'gbcp', 'gtes', 
                              'ws','hes', 'wbsg', 
                              'wbcp', 'ehcp', 
                              'other',
                              'wh', 'whlt']
    
    #energy carriers
    carriers = ['e', 'h', 'gas', 'oil', 'wd', 'msw', 'hyd', 'steam', 'wet_bm', 'loss', 'hlt']
    exports = ['exp_'+c for c in carriers]
    carriercolors = ["#92D505", "#F00000", "#bd9200", "#663300", "#663300", "#000000", "#00b0f0", "#f7a315", "#663300", "#636363", "#ff00ff"]

    # input streams (import)
    inputs = ['m_e_cbimport', 
              'm_gas', 'm_h_dh']+['m_e_ch_biomass','m_e_ch_hydro','m_e_ch_nuclear','m_e_ch_other','m_e_ch_wind'] + ['m_wd', 's_wd']

    #output streams
    outputs = ['d_e_ev', 'd_e_hh', 'd_h_hw', 'd_h_s']
    outputs_inverted = ['d_e_unmet', 'd_h_unmet']

    #export streams
    export_streams = ['v_e_aguc_exp', 'v_e_bm_exp', 'v_e_hydro_exp', 'v_e_pv_exp', 'v_e_wguc_exp', 'v_e_wp_exp', 
                      'v_h_chpgt_waste', 'v_h_st_wbsg_waste', 'v_h_st_gtcp_waste']
    # heat_wastes = []

    listOfAllNodes = link_nodes_to_consider + carriers + inputs + outputs + outputs_inverted + ["env_heat"] + exports
    nodeNames = {'tes': 'TES', 'pv': 'PV', 'hyd': 'H₂', 'm_gas': 'Import Gas', 
                 'm_h_dh': 'Fernwärme', 'tesdc': 'TES dezentral', 
                 'm_e_ch': 'Strom CH', 'm_e_cbimport': 'Stromimport internat.', 
                 'hydro': 'Wasserkraft', 'bes': 'Batteriespeicher', 'exp_e': 'Export', 
                 'd_e_ev': 'Elektromobilität', 'd_e_hh': 'Stromverbrauch Haushalte', 
                 'd_h_s': 'Wärme Heizung', 'd_h_hw': 'Wärme Brauchwasser', 'h': 'Wärme', 
                 'oil': 'Öl', 'solarthermalrooftop': 'Solarthermie (aufdach)', 'ob': 'Ölkessel', 'wb': 'Holzkessel',
                 'gas': 'Gas', 'gb': 'Gaskessel', 'wte': 'KVA', 'wd': 'Holz',
                 'bm': 'Biomasse', 'wet_bm': 'Feuchte Biomasse', 'wp': 'Windkraft',
                 'gtcp': 'Gasturbine', 'msw': 'Kehricht', 'hydp': 'Elektrolyseur',
                 'steam': 'Dampf', 'st': 'Dampfturbine', 'e': 'Elektrizität', 
                 'hp': 'Wärmepumpe', 'eh': 'Elektroheizung', 'hpcp': 'Wärmepumpe (Fernwärme)',
                 'hpcplt': 'Wärmepumpe (Fernwärme, von nieder-T)',
                 'chpgt': 'WKK-Gasturbine', 'wgu': 'Holzvergaser', 'wguc': 'Holzvergaser-WKK', 
                 'aguc': 'Anaerobe Vergärungsanlage WKK', 'agu': 'Anaerobe Vergärungsanlage',
                 'hg': 'HG', 'wguh': 'Holzvergaser H₂-Upgrade', 
                 'aguh': 'Anaerobe Vergärungsanlage H₂-Upgrade',
                 'bmc': 'Biomasse-Umwandlung', 'gtes': 'Gas-Tank', 
                 'ws': 'Holzspeicher', 'hes' : 'Wasserstoff-Speicher', 
                 'm_e_ch_biomass': "Biomasse-Strom CH",'m_e_ch_hydro': 'Wasserkraft CH',
                 'm_e_ch_nuclear': "Kernkraft CH",
                 'm_e_ch_other': 'Andere Stromerzeugung CH',
                 'm_e_ch_wind': "Windkraft CH", 'd_e_unmet': 'Nicht befriedigte Stromnachfrage',
                 'd_h_unmet': 'Nicht befriedigte Wärmenachfrage', "env_heat": "Umweltwärme", 'other': 'Andere'}
    
    nodeNames = {'tes': 'TES', 'pv': 'PV', 'hyd': 'H₂', 'm_gas': 'Import Gas', 
                 'm_h_dh': 'Import District Heat', 'tesdc': 'TES decentralized', 
                 'm_e_ch': 'Electricity Import CH', 'm_e_cbimport': 'Electricity Import internat.', 
                 'hydro': 'Hydropower (local)', 'bes': 'Battery storage', 'exp_e': 'Export electricity', 
                 'exp_h': 'Export heat', 
                 'd_e_ev': 'Electric mobility', 'd_e_hh': 'Households', 
                 'd_h_s': 'Heat for space heating', 'd_h_hw': 'Heat for DHW', 'h': 'Heat', 
                 'oil': 'Oil', 'solarthermalrooftop': 'Solar thermal (on roof)', 'ob': 'Oil boiler', 'wb': 'Wood boiler',
                 'gas': 'Gas', 'gb': 'Gas boiler', 'wte': 'Waste-to-Energy', 'wd': 'Wood',
                 'bm': 'Biomass', 'wet_bm': 'Wet biomass', 'wp': 'Wind power',
                 'gtcp': 'Gas turbine', 'msw': 'Municipal solid waste', 'hydp': 'Electrolyser',
                 'steam': 'Steam', 'st': 'Steam turbine', 'e': 'Electricity', 
                 'hp': 'Heat pump', 'eh': 'Electric heater', 'hpcp': 'Heat pump (centralized)',
                 'hpcplt': 'Heat pump (centralized, from low-T heat)',
                 'chpgt': 'CHP Gas turbine', 'wgu': 'Wood gasification', 'wguc': 'Wood Gasification CHP', 
                 'aguc': 'Anaerobic digestion CHP', 'agu': 'Anaerobic digestion',
                 'hg': 'Hydrothermal gasification', 'wguh': 'Wood gasification H₂ upgrade', 
                 'aguh': 'Anaerobic digestion H₂ upgrade',
                 'bmc': 'Biomass conversion', 'obcp': 'Oil boiler (centralized)', 
                 'ehcp': 'Electric heater (centralized)', 
                 'gbcp': 'Gas boiler (centralized)', 'gtes': 'Gas tank', 
                 'ws': 'Wood storage', 'hes': 'Hydrogen storage', 
                 'm_e_ch_biomass': "Biomass electricity CH",'m_e_ch_hydro': 'Hydro power CH',
                 'm_e_ch_nuclear': "Nuclear power CH",
                 'm_e_ch_other': 'Other domestic electricity generation',
                 'm_e_ch_wind': "Wind power CH", 'd_e_unmet': 'Unmet electricity demand',
                 'd_h_unmet': 'Unmet heat demand', "env_heat": "Environmental heat", 'other': 'Other',
                 'wh': 'Waste heat', 'whlt': 'Waste heat (low temperature)', 'wbsg': 'Wood boiler (steam generator)', 
                 'wbcp': 'Wood boiler (central plant)', 'hlt': 'Heat (Low Temperature)',
                 'm_wd': 'Wood import', 's_wd': 'Local Wood Harvest'}

    specialColornames = {'d_e_hh': carriercolors[carriers.index('e')], 'd_e_ev': carriercolors[carriers.index('e')],
                         'd_h_s': carriercolors[carriers.index('h')], 'd_h_hw': carriercolors[carriers.index('h')], 
                         'm_gas': carriercolors[carriers.index('gas')], 'm_wd': carriercolors[carriers.index('wd')], 
                         'pv': '#f7b201', 'm_h_dh': carriercolors[carriers.index('h')], 'solarthermalrooftop': '#f7b201',
                         'm_e_ch': carriercolors[carriers.index('e')], 'm_e_cbimport': carriercolors[carriers.index('e')],
                         'd_e_unmet': '#1f1f1f', 'd_h_unmet': '#1f1f1f',
                         }
    
    nodeNameMapped = []
    colorsNodeNames = []


    for k in range(len(listOfAllNodes)):
        nodename = listOfAllNodes[k]
        if nodename in nodeNames.keys():
            nodeNameMapped.append(nodeNames[nodename])
        else:
            nodeNameMapped.append(nodename)

        if nodename in carriers:
            colorsNodeNames.append(carriercolors[carriers.index(nodename)])
        elif nodename in specialColornames.keys():
            colorsNodeNames.append(specialColornames[nodename])
        else:
            colorsNodeNames.append('#77c5d8')

    sources = []
    targets = []
    values = []
    colors = []

    sankeythreshold = 0.01 #minimum size of a stream for it to be plotted
    offset = 0.0 #offset, to make all the possible energy streams visible
    carrieropacity = 0.5

    def torgbop(hexcolor, opacity):
        h = hexcolor.lstrip('#')
        return "rgba"+str(tuple(list(tuple(int(h[i:i+2], 16) for i in (0, 2, 4)))+[opacity]))+""
    
    # print(torgbop('#77c5d8', 0.8))
    # exit()
    #calculate export streams
    for carrierindex in range(len(carriers)):
        c = carriers[carrierindex]
        totalexp = 0.0
        for keyword in export_streams:
            if keyword in df_plot.index:
                carrier = keyword.split('_')[1]
                if carrier == c:
                    totalexp += df_plot[keyword]+offset
        
        outputIndex = listOfAllNodes.index('exp_'+c)
        carrierIndex = listOfAllNodes.index(c)
        if totalexp > sankeythreshold:
            sources.append(carrierIndex)
            targets.append(outputIndex)
            values.append(totalexp)
            colors.append(torgbop(carriercolors[carrierindex], carrieropacity))

    #calculate useful output streams
    for keyword in outputs:

        # print(df_plot[keyword])

        carrier = keyword.split('_')[1]
        outputIndex = listOfAllNodes.index(keyword)
        carrierIndex = listOfAllNodes.index(carrier)
        if keyword in df_plot.index:
            if df_plot[keyword] > sankeythreshold:
                sources.append(carrierIndex)
                targets.append(outputIndex)
                values.append(df_plot[keyword]+offset)
                colors.append(torgbop(carriercolors[carriers.index(carrier)], carrieropacity))

    for keyword in outputs_inverted:

        # print(df_plot[keyword])

        carrier = keyword.split('_')[1]
        outputIndex = listOfAllNodes.index(keyword)
        carrierIndex = listOfAllNodes.index(carrier)
        if keyword in df_plot.index:
            if df_plot[keyword] > sankeythreshold:
                sources.append(outputIndex)
                targets.append(carrierIndex)
                values.append(df_plot[keyword]+offset)
                colors.append(torgbop(carriercolors[carriers.index(carrier)], carrieropacity))

    #calculate input streams
    for keyword in inputs:

        carrier = keyword.split('_')[1]

        inputIndex = listOfAllNodes.index(keyword)
        carrierIndex = listOfAllNodes.index(carrier)
        if keyword in df_plot.index:
            if df_plot[keyword] > sankeythreshold:
                sources.append(inputIndex)
                targets.append(carrierIndex)
                values.append(df_plot[keyword]+offset)
                colors.append(torgbop(carriercolors[carriers.index(carrier)], carrieropacity))


    #calculate input streams
    for keyword in env_heat_flows: #"u_h_hp", "u_h_hpcp"

        carrier = keyword.split('_')[1]
        device = keyword.split('_')[2]
        inputIndex = listOfAllNodes.index("env_heat")
        carrierIndex = listOfAllNodes.index(carrier)
        device_index = listOfAllNodes.index(device)

        if keyword in df_plot.index:
            if df_plot[keyword] > sankeythreshold:
                sources.append(inputIndex)
                targets.append(device_index)
                values.append(df_plot[keyword]+offset)
                colors.append(torgbop(carriercolors[carriers.index(carrier)], carrieropacity))

    # for keyword in :

    #     carrier = keyword.split('_')[1]

    #     inputIndex = listOfAllNodes.index(keyword)
    #     carrierIndex = listOfAllNodes.index(carrier)
    #     if keyword in df_plot.index:
    #         if df_plot[keyword] > sankeythreshold:
    #             sources.append(inputIndex)
    #             targets.append(carrierIndex)
    #             values.append(df_plot[keyword]+offset)
    #             colors.append(torgbop(carriercolors[carriers.index(carrier)], carrieropacity))



    #calculate internal flows
    for keyword in flows_to_consider:

        device = keyword.split('_')[2]
        carrier = keyword.split('_')[1]
        isIn = keyword.split('_')[0] == 'u'

        deviceIndex = listOfAllNodes.index(device)
        carrierIndex = listOfAllNodes.index(carrier)
        if keyword in df_plot.index:
            if df_plot[keyword] > sankeythreshold:
                if isIn:
                    sources.append(carrierIndex)
                    targets.append(deviceIndex)
                    values.append(df_plot[keyword]+offset)
                    colors.append(torgbop(carriercolors[carriers.index(carrier)], carrieropacity))
                else:
                    sources.append(deviceIndex)
                    targets.append(carrierIndex)
                    values.append(df_plot[keyword]+offset)
                    colors.append(torgbop(carriercolors[carriers.index(carrier)], carrieropacity))
    #calculate internal flow with two-word energy carrier (biomass_wet)
    for keyword in flows_to_consider_two_word_carrier:
        device = keyword.split('_')[3]
        carrier = keyword.split('_')[1]+"_"+keyword.split('_')[2]
        isIn = keyword.split('_')[0] == 'u'

        deviceIndex = listOfAllNodes.index(device)
        carrierIndex = listOfAllNodes.index(carrier)
        if keyword in df_plot.index:
            if df_plot[keyword] > sankeythreshold:
                if isIn:
                    sources.append(carrierIndex)
                    targets.append(deviceIndex)
                    values.append(df_plot[keyword]+offset)
                    colors.append(torgbop(carriercolors[carriers.index(carrier)], carrieropacity))
                else:
                    sources.append(deviceIndex)
                    targets.append(carrierIndex)
                    values.append(df_plot[keyword]+offset)
                    colors.append(torgbop(carriercolors[carriers.index(carrier)], carrieropacity))

    def calculateInflowOutflowDifference(sources, targets, values, symbol):
        if symbol in listOfAllNodes:
            symbolindex = listOfAllNodes.index(symbol)

            inflow = 0.0
            outflow = 0.0

            for i in range(len(sources)):
                if sources[i] == symbolindex:
                    outflow += values[i]
                if targets[i] == symbolindex:
                    inflow += values[i]

            return outflow-inflow
        return 0

    for nodename in nodeNames.keys():
        if nodename in link_nodes_to_consider:
            diff = calculateInflowOutflowDifference(sources, targets, values, nodename)
            if diff < 0:
                if abs(diff) > sankeythreshold:
                    sources.append(listOfAllNodes.index(nodename))
                    targets.append(listOfAllNodes.index("loss"))
                    values.append(abs(diff))
                    colors.append(torgbop("#888888", carrieropacity))

    #create basic sankey figure
    fig = go.Figure(data=[go.Sankey(
        node = dict(
        pad = 15,
        thickness = 20,
        line = dict(color = "black", width = 0.5),
        label = nodeNameMapped,
        color = colorsNodeNames,
        ),
        link = dict(
        source = sources,
        target = targets,
        value = values,
        color = colors
    ))])

    fig.update_layout(title_text="Energy flows", font_size=10)

    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)


# def plot_pareto_cost_vs_co2_SUPERSEDED(
#         pareto_results,
#         dir_path,
#         output_svg = False,
#         output_html = False,
#         filename = 'pareto_cost_co2',
#         axes_font_size = 16,
#         title_font_size = 24
#         ):
    
#     # Extract cost and CO2 values from pareto results:
#     weight_monetary = []
#     weight_co2 = []
#     # monetary_electricity_tlc = []
#     # monetary_heat_tlc = []
#     # co2_electricity_tlc = []
#     # co2_heat_tlc = []
    
#     cost_monetary = []
#     cost_co2 = []
    
#     for res in pareto_results:
        
#         weight_monetary.append(res['obj_weight_monetary'])
#         weight_co2.append(res['obj_weight_co2'])
#         # monetary_electricity_tlc.append(
#         #     res['dict_total_costs']['monetary']['electricity_tlc']
#         #     )
#         # monetary_heat_tlc.append(
#         #     res['dict_total_costs']['monetary']['heat_tlc']
#         #     )
#         # co2_electricity_tlc.append(
#         #     res['dict_total_costs']['co2']['electricity_tlc']
#         #     )
#         # co2_heat_tlc.append(
#         #     res['dict_total_costs']['co2']['heat_tlc']
#         #     )
        
#         cost_monetary.append(
#             res['dict_total_costs']['monetary']['total']
#             )
#         cost_co2.append(
#             res['dict_total_costs']['co2']['total']
#             )
        
#     # Create colormap based on weight_monetary
#     colors = np.array(weight_monetary)
#     min_color = min(colors)
#     max_color = max(colors)
#     norm_colors = (colors - min_color) / (max_color - min_color)  # Normalize colors
#     color_scale = [[i, f'rgb({255 - int(255*i)}, {int(255*i)}, 0)'] for i in norm_colors]  # Red to green colormap

        
#     # Create Pareto front plot
#     fig = go.Figure()
#     scatter = go.Scatter(
#         # x=co2_electricity_tlc,
#         # y=monetary_electricity_tlc,
#         x=cost_co2,
#         y=cost_monetary,
#         mode='markers',
#         name='Pareto Front',
#         marker=dict(size=10,
#                     color=colors,
#                     colorscale=color_scale,
#                     colorbar=dict(title='Weight Monetary',
#                                   title_font_size=14.0
#                                   ),
#                     line=dict(
#                         color='black',  # Border color
#                         width=1  # Border width
#                         )
#                     )
#         )
#     fig.add_trace(scatter)
    
#     fig.update_layout(
#         plot_bgcolor='white',
#         bargap = 0.01,
#         bargroupgap = 0.00,
#         title=dict(
#             text="Multi-Objective Optimisation",
#             x=0.5,  # Center the title horizontally
#             xanchor='center'  # Anchor the title at the center horizontally
#             ),
#         # xaxis_title="CO2 [kg/kWh]",
#         # yaxis_title="Levelised cost of electricity [CHF/kWh]",
#         font=dict(
#             family="Arial, sans-serif",
#             size=axes_font_size
#             )
#         )
    
#     fig.update_xaxes(
#         title_text='CO2 [kg]',
#         title_standoff=0,
#         mirror=True,
#         ticks='outside',
#         showline=True,
#         linecolor='black',
#         gridcolor='lightgrey',
#         title_font_size=axes_font_size,
#         tickfont=dict(size=axes_font_size)
#     )
    
#     fig.update_yaxes(
#         title_text='Total cost of energy [CHF]',
#         title_standoff=0,
#         mirror=True,
#         ticks='outside',
#         showline=True,
#         linecolor='black',
#         gridcolor='lightgrey',
#         title_font_size=axes_font_size,
#         tickfont=dict(size=axes_font_size)
#     )
    
    
#     file_svg = f"{dir_path}/{filename}.svg"
#     file_html = f"{dir_path}/{filename}.html"
    
#     if output_svg:
#         fig.write_image(file_svg)
    
#     if output_html:
#         fig.write_html(file_html)
        
    
# def plot_pareto_cost_vs_co2(
#         pareto_results,
#         dir_path,
#         output_svg = False,
#         output_html = False,
#         filename = 'pareto_cost_co2',
#         axes_font_size = 16,
#         title_font_size = 24
#         ):
    
#     # Extract cost and CO2 values from pareto results:
#     # eps_n = []    
#     cost_monetary = []
#     cost_co2 = []
    
#     for res in pareto_results:

#         # eps_n.append(res['eps_n'])
        
#         cost_monetary.append(
#             res['dict_total_costs']['monetary']['total']/1e6
#             )
#         cost_co2.append(
#             res['dict_total_costs']['co2']['total']/1e3
#             )
        
#     # Create colormap based on weight_monetary
#     # colors = np.array(eps_n)
#     # min_color = min(colors)
#     # max_color = max(colors)
#     # norm_colors = (colors - min_color) / (max_color - min_color)  # Normalize colors
#     # color_scale = [[i, f'rgb({255 - int(255*i)}, {int(255*i)}, 0)'] for i in norm_colors]  # Red to green colormap

        
#     # Create Pareto front plot
#     fig = go.Figure()
#     scatter = go.Scatter(
#         # x=co2_electricity_tlc,
#         # y=monetary_electricity_tlc,
#         x=cost_co2,
#         y=cost_monetary,
#         mode='markers',
#         name='Pareto Front',
#         marker=dict(size=10,
#                     color='grey',
#                     # color=colors,
#                     # colorscale=color_scale,
#                     # colorbar=dict(title='Epsilon [kgCO2]',
#                     #               title_font_size=14.0
#                     #               ),
#                     line=dict(
#                         color='black',  # Border color
#                         width=1  # Border width
#                         )
#                     )
#         )
#     fig.add_trace(scatter)
    
#     fig.update_layout(
#         plot_bgcolor='white',
#         bargap = 0.01,
#         bargroupgap = 0.00,
#         title=dict(
#             text="Multi-Objective Optimisation",
#             x=0.5,  # Center the title horizontally
#             xanchor='center'  # Anchor the title at the center horizontally
#             ),
#         # xaxis_title="CO2 [kg/kWh]",
#         # yaxis_title="Levelised cost of electricity [CHF/kWh]",
#         font=dict(
#             family="Arial, sans-serif",
#             size=axes_font_size
#             )
#         )
    
#     fig.update_xaxes(
#         title_text='CO2 equivalent [t]',
#         title_standoff=0,
#         mirror=True,
#         ticks='outside',
#         showline=True,
#         linecolor='black',
#         gridcolor='lightgrey',
#         title_font_size=axes_font_size,
#         tickfont=dict(size=axes_font_size)
#     )
    
#     fig.update_yaxes(
#         title_text='Cost of energy [Mio. CHF]',
#         title_standoff=0,
#         mirror=True,
#         ticks='outside',
#         showline=True,
#         linecolor='black',
#         gridcolor='lightgrey',
#         title_font_size=axes_font_size,
#         tickfont=dict(size=axes_font_size)
#     )
    
    
#     file_svg = f"{dir_path}/{filename}.svg"
#     file_html = f"{dir_path}/{filename}.html"
    
#     if output_svg:
#         fig.write_image(file_svg)
    
#     if output_html:
#         fig.write_html(file_html)
def plot_bes_cyclecount_hourly(df_scen,
                        dir_path,
                        output_svg = False,
                        output_html = True,
                        filename = 'bes_cyclecount_hourly',
                        timeframe = False,
                        timeframe_start = '01-01',
                        timeframe_end = '12-31',
                        axes_font_size = 16,
                        title_font_size = 24
                        ):
    
    """
    Generates a line plot of the battery energy storage cycle count.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    if not 'sos_bes' in df_scen.columns:
        return False
    

    #Difference in Charge between time steps
    df_plot = df_scen.copy()
    
    dt = df_scen['sos_bes'].diff()[1:]
    dt = ((dt + np.abs(dt))/2.0).cumsum()
    
    df_plot = pd.DataFrame(data = {'bes_cyclecount' : dt}, index = df_scen.index[1:])
    
    # Ensure the index is in datetime format
    df_plot.index = pd.date_range(start='2050-01-01', periods=len(df_plot), freq='h')
    
    y=['bes_cyclecount']

    fig = px.line(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='BES - Cycle count',
        category_orders={'x': df_plot.index},
        #height=400,
        #width=1200
        )
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )
    
    fig.update_xaxes(
        # title_text='Hour of the year',
        title_text='',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
        tickformat="%d %b %H:%M"  # Formats as '3 Jan 15:00'
    )
    fig.update_yaxes(
        title_text='Number of discharge cycles [#]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size),
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot

def plot_pareto_cost_vs_co2(
        pareto_results,
        dir_path,
        output_svg = False,
        output_html = False,
        filename = 'pareto_cost_co2',
        axes_font_size = 16,
        title_font_size = 24
        ):
    
    # Extract cost and CO2 values from pareto results: 
    cost_monetary = []
    cost_co2 = []
    
    for res in pareto_results:

        cost_monetary.append(
            res['dict_total_costs']['monetary']['total']/1e6
            )
        cost_co2.append(
            res['dict_total_costs']['co2']['total']/1e3
            )
        
    # Sort the points to ensure proper line connection
    sorted_pareto = sorted(zip(cost_co2, cost_monetary))
    sorted_cost_co2, sorted_cost_monetary = zip(*sorted_pareto)

    # Create Pareto front plot
    fig = go.Figure()
    scatter = go.Scatter(
        # x=co2_electricity_tlc,
        # y=monetary_electricity_tlc,
        x=cost_co2,
        y=cost_monetary,
        mode='markers',
        name='Pareto Front',
        marker=dict(size=10,
                    color='grey',
                    line=dict(
                        color='black',  # Border color
                        width=1  # Border width
                        )
                    )
        )
    fig.add_trace(scatter)
    
    # Add a dotted line connecting Pareto points
    line_trace = go.Scatter(
        x=sorted_cost_co2,
        y=sorted_cost_monetary,
        mode='lines',
        name='Pareto Front Line',
        line=dict(dash='dot', color='grey', width=2)
    )
    fig.add_trace(line_trace)
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title=dict(
            text="Multi-Objective Optimisation",
            x=0.5,  # Center the title horizontally
            xanchor='center'  # Anchor the title at the center horizontally
            ),
        # xaxis_title="CO2 [kg/kWh]",
        # yaxis_title="Levelised cost of electricity [CHF/kWh]",
        font=dict(
            family="Arial, sans-serif",
            size=axes_font_size
            ),
        showlegend=False,
        )
    
    fig.update_xaxes(
        title_text='CO2 equivalent [t]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    
    fig.update_yaxes(
        title_text='Cost of energy [Mio. CHF]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    
    
    file_svg = f"{dir_path}/{filename}.svg"
    file_html = f"{dir_path}/{filename}.html"
    
    if output_svg:
        fig.write_image(file_svg)
    
    if output_html:
        fig.write_html(file_html)
        
def plot_annual_heat_and_electricity(
        dict_yr,
        dir_path,
        output_svg = False,
        output_html = False,
        filename = 'heat_electricity_yr',
        axes_font_size = 16,
        title_font_size = 24
        ):
    # Add separate bars for BES and TES
    
    # Your data stored in a Python dictionary
    annual_vals = dict_yr
    
    if 'v_e_gtcp_yr' in dict_yr and 'v_e_st_gtcp_yr' in dict_yr:
        dict_yr['v_e_gtcp_total_yr'] = dict_yr['v_e_gtcp_yr'] + dict_yr['v_e_st_gtcp_yr']
    elif 'v_e_gtcp_yr' in dict_yr:
        dict_yr['v_e_gtcp_total_yr'] = dict_yr['v_e_gtcp_yr']
    elif 'v_e_st_gtcp_yr' in dict_yr:
        dict_yr['v_e_gtcp_total_yr'] = dict_yr['v_e_st_gtcp_yr']
    heat_keys = [
        'v_h_hp_yr',
        'v_h_eh_yr',
        'v_h_ob_yr',
        'v_h_gb_yr',
        'v_h_wb_yr',
        'm_h_dh_yr',
        'v_h_solarthermalrooftop_yr',
        'v_h_chpgt_yr',
        # 'v_h_st_yr',
        'v_h_st_gtcp_yr',
        'v_h_st_wbsg_yr',
        'v_h_wte_con_yr',
        'v_h_hpcp_yr',
        'v_h_hpcplt_yr',
        'd_h_unmet_yr',
        'd_h_unmet_dhn_yr',
        ]
    
    electricity_keys = [
        'v_e_pv_cons_yr',
        'v_e_wp_cons_yr',
        'v_e_bm_cons_yr',
        'v_e_hydro_cons_yr',
        'v_e_chpgt_yr',
        # 'v_e_gtcp_yr',
        # 'v_e_st_yr',
        'v_e_gtcp_total_yr',
        'v_e_st_wbsg_yr',
        'v_e_wte_yr',
        'm_e_yr',
        'd_e_unmet',
        ]
    
    heat_names = [
        'Heat pump',
        'Electric heater',
        'Oil boiler',
        'Gas boiler',
        'Wood boiler',
        'District heat (other source)',
        # 'Heat import',
        # 'District heating',
        # 'District heat import',
        'Solar thermal (rooftop)',
        'Gas turbine CHP (small)',
        # 'Steam turbine',
        'Gas turbine CC',
        'Wood CHP',
        'WtE CHP',
        'Heat pump (large scale)',
        'Heat pump (large scale, from low temperature heat)',
        'Unmet demand',
        'Unmet demand DHN',
        ]
    
    heat_sources_dhn=[
        'm_h_dh_yr',
        'v_h_chpgt_yr',
        # 'v_h_st',
        'v_h_st_gtcp_yr',
        'v_h_st_wbsg_yr',
        'v_h_wte_con_yr',
        'v_h_hpcp_yr',
        'v_h_hpcplt_yr',
        # 'v_h_tes_yr',
        # 'u_h_tes_negative_yr',
        'd_h_unmet_dhn_yr'
        ]
    
    electricity_names = [
        'Solar PV',
        'Wind power',
        'Biomass',
        'Hydro power',
        'Gas turbine CHP (small)',
        'Gas turbine CC',
        # 'Steam turbine',
        'Wood CHP',
        'WtE CHP',
        'Grid supply',
        'Unmet demand',
        ]
    
    duplicate_names = [
        'Gas turbine CHP (small)',
        'Gas turbine CC',
        # 'Steam turbine',
        'Wood CHP',
        'WtE CHP',
        'Unmet demand',
        ]
    
    heat_colors = [
        col_heat_pump,
        col_electric_heater,
        col_oil_boiler,
        col_gas_boiler,
        col_wood_boiler,
        col_district_heating,
        col_solar_thermal,
        col_chp_gt,
        # col_st,
        col_gtcp,
        col_wood_boiler_sg,
        col_wte_con,
        col_heat_pump_cp,
        col_heat_pump_cp_lt,
        col_demand_unmet,
        col_demand_unmet_dhn,
        ]
    
    electricity_colors = [
        col_pv,
        col_wp,
        col_bm,
        col_hydro,
        col_chp_gt,
        col_gtcp,
        col_wood_boiler_sg,
        # col_st,
        col_wte_con,
        col_cross_border_import,
        col_demand_unmet,
        ]
    # Calculate the total sum of heat and electricity values
    total_heat = sum(annual_vals.get(key,0) for key in heat_keys)
    total_electricity = sum(annual_vals.get(key,0) for key in electricity_keys)

    # Calculate percentages for heat and electricity
    heat_percentages = [annual_vals.get(key,0) / total_heat * 100 for key in heat_keys]
    electricity_percentages = [annual_vals.get(key,0) / total_electricity * 100 for key in electricity_keys]
    if 'v_h_tes_yr' in dict_yr:
        tes_percentage = dict_yr['v_h_tes_yr']/dict_yr['d_h_yr']*100
    else:
        tes_percentage = 0.0
    if 'v_h_tesdc_yr' in dict_yr:
        tesdc_percentage = dict_yr['v_h_tesdc_yr']/dict_yr['d_h_yr']*100
    else:
        tesdc_percentage = 0.0
    if 'v_e_bes_yr' in dict_yr:
        bes_percentage = dict_yr['v_e_bes_yr']/dict_yr['d_e_yr']*100
    else:
        bes_percentage = 0.0
    # Create subplots with one row and two columns
    fig = make_subplots(rows=1, cols=5, shared_yaxes=True, subplot_titles=("Heat", "", "Electricity", "", ""), horizontal_spacing=0.03)
    # Adding bars for heat
    for i, value in enumerate(heat_percentages):
        if value > 0.1:  # Check if value is larger than 0.1%
            show_legend = True
            if heat_names[i] in duplicate_names:
                show_legend = False
        else:
            show_legend = False
            
        # Determine if the heat source is in heat_sources_dhn
        pattern_shape = patterns[pattern_index] if heat_keys[i] in heat_sources_dhn else ""
        
        fig.add_trace(go.Bar(
            x=[''],
            y=[value],
            name = heat_names[i],
            # name=['Heat Pump', 'Electric Heater', 'Oil Boiler', 'Gas Boiler', 'Wood Boiler', 'District Heating', 'Solar Thermal', 'Gas Turbine CHP'][i],
            # marker_color=heat_colors[i],
            marker=dict(
                color=heat_colors[i],
                pattern_shape=pattern_shape  # Apply pattern if in heat_sources_dhn
                ),
            showlegend=show_legend, 
            width=0.8,
        ), row=1, col=1)
    if tes_percentage > 0.5:  # Check if value is larger than 0.1%
        show_legend = True
        
        fig.add_trace(go.Bar(
            x=['TES (DHN)'],
            y=[tes_percentage],
            name = 'Thermal Energy Storage (DHN)',
            marker_color=col_tes_dchg,
            showlegend=show_legend,
            width=0.5,
        ), row=1, col=2)
        
        fig.add_trace(go.Bar(
            x=['TES (DHN)'],
            y=[100-tes_percentage],
            name = '',
            marker_color= col_demand_unmet,
            # marker=dict(
            #     color='white',  # Fill color
            #     line=dict(color='grey', width=1)  # Border color and width
            # ),
            showlegend=False,
            width=0.5,
        ), row=1, col=2)
    else:
        show_legend = False
    if tesdc_percentage > 0.5:  # Check if value is larger than 0.1%
        show_legend = True
        
        fig.add_trace(go.Bar(
            x=['TES (decentralised)'],
            y=[tesdc_percentage],
            name = 'Thermal Energy Storage (decentralised)',
            marker_color=col_tesdc_dchg,
            showlegend=show_legend,
            width=0.5,
        ), row=1, col=2)
        
        fig.add_trace(go.Bar(
            x=['TES (decentralised)'],
            y=[100-tesdc_percentage],
            name = '',
            marker_color=col_demand_unmet,
            # marker=dict(
            #     color='white',  # Fill color
            #     line=dict(color='grey', width=1)  # Border color and width
            # ),
            showlegend=False,
            width=0.5,
        ), row=1, col=2)
    else:
        show_legend = False
    # Adding bars for electricity
    for i, value in enumerate(electricity_percentages):
        if value > 0.1:  # Check if value is larger than 0.1%
            show_legend = True
        else:
            show_legend = False
        fig.add_trace(go.Bar(
            x=[''],
            y=[value],
            name = electricity_names[i],
            # name=['Solar PV', 'Wind Power', 'Biomass', 'Hydro Power', 'Gas Turbine CHP', 'Grid Supply'][i],
            marker_color=electricity_colors[i],
            showlegend=show_legend,
            width=0.8,
        ), row=1, col=3)
  
    if bes_percentage > 0.5:  # Check if value is larger than 0.1%
        show_legend = True
        
        fig.add_trace(go.Bar(
            x=['Battery Storage'],
            y=[bes_percentage],
            name = 'Battery Energy Storage',
            marker_color=col_bes_dchg,
            showlegend=show_legend,
            width=0.5,
        ), row=1, col=4)
        
        fig.add_trace(go.Bar(
            x=['Battery Storage'],
            y=[100-bes_percentage],
            name = '',
            marker_color=col_demand_unmet,
            showlegend=False,
            width=0.5,
        ), row=1, col=4)
            
    else:
        show_legend = False    
        
    # Add a legend entry for District Heating Network (patterned bars)
    fig.add_trace(go.Bar(
        x=[''],  # Dummy x value
        y=[0],   # Dummy y value to make it appear in the legend
        name='District Heating Network',
        marker=dict(
            color='white',  # Invisible bar (legend only)
            pattern_shape=patterns[pattern_index],  # Same pattern used for DHN sources
            line=dict(color='grey')  # Ensure it's visible in the legend
        ),
        showlegend=True
    ), row=1, col=1)  # Place it in the first subplot (doesn't matter where)

    # Update layout
    fig.update_layout(
        width = 800,
        height = 500,
        barmode='stack',
        yaxis=dict(title='Annual Energy Consumption by Source [%]'),
        xaxis=dict(showticklabels=False),  # Remove x-axis tick labels
        plot_bgcolor='white'  # Set background color to white
    )

    file_svg = f"{dir_path}/{filename}.svg"
    file_html = f"{dir_path}/{filename}.html"
    
    if output_svg:
        fig.write_image(file_svg)
    if output_html:
        fig.write_html(file_html)

def plot_obj_weights_monetary_vs_co2(
        obj_weight_monetary,
        obj_weight_co2,
        dir_path,
        output_svg = False,
        output_html = False,
        filename = 'obj_weights'
        ):
    
    # Dictionary containing the values
    data_dict = {'obj_weight_monetary': obj_weight_monetary,
                 'obj_weight_co2': obj_weight_co2                 
                 }

    # Extracting values
    monetary_weight = data_dict['obj_weight_monetary']
    co2_weight = data_dict['obj_weight_co2']

    # Creating the horizontal bar chart
    fig = go.Figure()

    # Adding horizontal bar trace
    fig.add_trace(go.Bar(
        y=[""],  # Remove the label
        x=[monetary_weight],
        orientation='h',
        name='Monetary',
        marker=dict(color='blue'),
        text=[f'{monetary_weight:.2f}'],
        textposition='auto',
    ))

    fig.add_trace(go.Bar(
        y=[""],  # Remove the label
        x=[co2_weight],
        orientation='h',
        name='Emissions (CO2)',
        marker=dict(color='green'),
        text=[f'{co2_weight:.2f}'],
        textposition='auto',
        hoverinfo='x',
        base=[monetary_weight],  # Set the base to the monetary weight
    ))

    # Updating layout
    fig.update_layout(
        title="Multi-Objective Optimisation",  # Change the title
        xaxis_title="Objective weight",
        yaxis_title="",
        barmode='stack',  # Stacked bars
        height=230,  # Adjust the height here
        plot_bgcolor='white',  # Set background color to white
        title_x=0.5,  # Center the title horizontally
    )
    
    file_svg = f"{dir_path}/{filename}.svg"
    file_html = f"{dir_path}/{filename}.html"
    
    if output_svg:
        fig.write_image(file_svg)    
    if output_html:
        fig.write_html(file_html)
    
def plot_obj_values_monetary_vs_co2(
        pareto_results,
        dir_path,
        output_svg = False,
        output_html = False,
        filename = '00_obj_values_cost_co2',
        axes_font_size = 16,
        title_font_size = 24
        ):
    
    # Extract cost and CO2 values from pareto results:
    weight_monetary = []
    weight_co2 = []
    
    cost_monetary = []
    cost_co2 = []
    
    for res in pareto_results:
        
        weight_monetary.append(res['obj_weight_monetary'])
        weight_co2.append(res['obj_weight_co2'])        
        cost_monetary.append(res['dict_total_costs']['monetary']['total'])
        cost_co2.append(res['dict_total_costs']['co2']['total'])
    
    
    # Create the line plot with dots
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weight_monetary, y=cost_monetary, mode='lines+markers', name='Monetary'))
    fig.add_trace(go.Scatter(x=weight_monetary, y=cost_co2, mode='lines+markers', name='CO2', yaxis='y2'))
    
    # Add axis labels and legend
    fig.update_layout(title='Objectives Values: Monetary vs CO2',
                      title_x=0.5, title_xanchor='center',
                      xaxis=dict(title='Weight (Monetary)'),
                      yaxis=dict(title='Cost [CHF]'),
                      yaxis2=dict(title='CO2 [kg]', overlaying='y', side='right'),
                       legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.15, bgcolor='rgba(250,250,250,0.5)', bordercolor='grey', borderwidth=1,),
                      plot_bgcolor='white'
                      )
    
    fig.update_xaxes(
        # title_text='Day of the year',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        # gridcolor='lightgrey',
        # title_font_size=axes_font_size,
        # tickfont=dict(size=axes_font_size)
    )
    fig.update_yaxes(
        # title_text='Electricity supply [MWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        # gridcolor='lightgrey',
        # title_font_size=axes_font_size,
        # tickfont=dict(size=axes_font_size)
    )
    
    # Save the plot:
    file_svg = f"{dir_path}/{filename}.svg"
    file_html = f"{dir_path}/{filename}.html"
    
    if output_svg:
        fig.write_image(file_svg)    
    if output_html:
        fig.write_html(file_html)
    
    
def plot_biomethane_balance_hourly(df_scen,
                             dir_path,
                             output_svg = False,
                             output_html = False,
                             filename = 'biomethane_balance_hourly',
                             timeframe = False,
                             timeframe_start = '01-01',
                             timeframe_end = '12-31',
                             axes_font_size = 16,
                             title_font_size = 24
                             ):
    
    """
    Generates a stacked bar plot with the hourly heat supply split by
    sources.
    
    Parameters
    ----------
    df_scen : pandas dataframe
        Dataframe with resulting hourly values.
    dir_path : string
        Path to directory, where plots shall be saved.
    output_svg : bool
        If set to 'True', a (static) plot in .svg format will be generated.
        Default: False
    output_svg : bool
        If set to 'True', a (dynamic) plot in .html format will be generated.
        Default: True
    filename : string
        Name of generated plot file(s).
    timeframe : bool
        If set to 'True', only the selected timeframe will be plotted.
        [not yet implemented]
    timeframe_start : string
        Beginning of selected timeframe.
        [not yet implemented]
    timeframe_end : string
        End of selected timeframe.
        [not yet implemented]
    axes_font_size : int
        Font size for x- and y-axis labels, tick-mark labels, and legend
        labels.
    title_font_size : int
        Font size of plot title.

    Returns
    -------
    n/a
    """
    
    df_plot = df_scen.copy()
    
    y=[
       'v_biomethane_hg',
       'v_biomethane_wgu'
       ]
    
    legend_labels = [
                     'Hydrothermal Gasification',
                     'Wood Gasification Upgrade'
                     ]
    
    colors = [
              col_hydrothermal_gasification,
              col_hydro
              ]
    
    
    fig = px.bar(
        df_plot, 
        x=df_plot.index,
        y=y,
        labels={'x': 'Time'},
        title='Hourly Biomethane Supply',
        category_orders={'x': df_plot.index},
        #height=400,
        #width=1200
        )
    
    fig.update_layout(
        plot_bgcolor='white',
        bargap = 0.01,
        bargroupgap = 0.00,
        title_x=0.5,  # Center the title
        legend_title_text='',
        title_font_size=title_font_size,
        legend_font=dict(size=axes_font_size)
        )

    
    # Update each trace individually (color, label):
    for i, trace_name in enumerate(y):
        fig.update_traces(
            marker_color=colors[i],
            marker_line_width=0,
            selector=dict(name=trace_name),
            name = legend_labels[i]
            )

    
    fig.update_xaxes(
        title_text='Hour of the year',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    fig.update_yaxes(
        title_text='Heat supply [MWh]',
        title_standoff=0,
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey',
        title_font_size=axes_font_size,
        tickfont=dict(size=axes_font_size)
    )
    
    file_svg = dir_path + '/' + filename + '.svg'
    file_html = dir_path + '/' + filename + '.html'
    
    if output_svg == True:
        fig.write_image(file_svg, width=svg_width, height=svg_height)
    
    if output_html == True:
        fig.write_html(file_html)
    
    del df_plot
    
    
#%% Plot main function:
    
def plot(
        pareto_results_loaded,
        scenario_generated,
        pareto_results,
        pareto_results_generated,
        results_path,
        dict_yr_scen,
        df_scen,                
        ):
    if pareto_results_loaded == True:
        plot_pareto_cost_vs_co2(
            pareto_results=pareto_results,
            dir_path=results_path,
            output_svg=toggle_svg,
            output_html=toggle_html
            )
        for idx, res in enumerate(pareto_results):
            plot_annual_heat_and_electricity(
                dict_yr=pareto_results[idx]['dict_yr_scen'],
                dir_path=results_path,
                output_svg=toggle_svg,
                output_html=toggle_html,
                filename=f"opt{idx+1}_heat_electricity_yr"
                )
        if scenario_generated == True:
            plot_annual_heat_and_electricity(
                dict_yr=dict_yr_scen, 
                dir_path=results_path,
                output_svg=toggle_svg,
                output_html=toggle_html
                )
            plot_electricity_balance_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_heat_balance_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_electricity_balance_daily(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_heat_balance_daily(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_electricity_balance_weekly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_heat_balance_weekly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_tes_sos_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_tes_cyclecount_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_tes_and_bes_cumsum_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_tesdc_sos_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_bes_sos_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_gtes_sos_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
            plot_ws_sos_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )


            plot_hes_sos_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )



            plot_sankey_total(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )

            plot_bes_cyclecount_hourly(
                df_scen=df_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )

            plot_annual_heat_and_electricity(
                dict_yr=dict_yr_scen,
                dir_path=results_path,
                output_svg = toggle_svg,
                output_html = toggle_html,
                )
    elif pareto_results_generated == True:
        plot_pareto_cost_vs_co2(
            pareto_results=pareto_results,
            dir_path=results_path,
            output_svg=toggle_svg,
            output_html=toggle_html
            )
        for idx, res in enumerate(pareto_results):
            plot_annual_heat_and_electricity(
                dict_yr=pareto_results[idx]['dict_yr_scen'],
                dir_path=results_path,
                output_svg=toggle_svg,
                output_html=toggle_html,
                filename=f"opt{idx+1}_heat_electricity_yr"
                )
    elif scenario_generated == True:
        plot_annual_heat_and_electricity(
            dict_yr=dict_yr_scen, 
            dir_path=results_path,
            output_svg=toggle_svg,
            output_html=toggle_html
            )
        plot_electricity_balance_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        # plot_electricity_balance_hourly_share(
        #     df_scen=df_scen,
        #     dir_path=results_path,
        #     output_svg = toggle_svg,
        #     output_html = toggle_html,
        #     )
        plot_heat_balance_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        
        plot_electricity_balance_daily(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        plot_heat_balance_daily(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        plot_electricity_balance_weekly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        plot_heat_balance_weekly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        plot_tes_sos_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        plot_tes_cyclecount_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        
        plot_tes_and_bes_cumsum_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )

        plot_tesdc_sos_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        plot_bes_sos_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        plot_gtes_sos_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        plot_ws_sos_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )

        
        plot_hes_sos_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )


        plot_sankey_total(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
        plot_bes_cyclecount_hourly(
            df_scen=df_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
                )

        plot_annual_heat_and_electricity(
            dict_yr=dict_yr_scen,
            dir_path=results_path,
            output_svg = toggle_svg,
            output_html = toggle_html,
            )
    else:
        raise(Exception('No Scenario Generated to Plot'))
    
    