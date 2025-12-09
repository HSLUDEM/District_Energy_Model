# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 11:43:49 2023

@author: UeliSchilt
"""

# import os

# -----------------------------------------------------------------------------
# Change working directory to script location (here: 'src' directory):
# abspath = os.path.abspath(__file__)
# dname = os.path.dirname(abspath)
# os.chdir(dname)
# -----------------------------------------------------------------------------

# import dem
# import paths
# import dem_helper

from district_energy_model import dem
from district_energy_model import dem_helper
from district_energy_model import dem_paths

# Generic input file:
# -----------------------
# import input_files.inputs as inp
from district_energy_model.input_files import inputs as inp

def launch(root_dir=None, config_files=True, config_dict=''):
    """
    root_dir: directory where the user provides `data/` and `config/` folders
    If None: use current working directory.
    """
    
    from pathlib import Path

    root_dir = str(Path(root_dir or ".").resolve())    
    
    print("\n==============================")
    print("Process started ...")
    print("------------------------------")
    print('\nGenerate model ...')
    
    paths = dem_paths.DEMPaths(root_dir)
    
    # Read input files and update scen_techs:
    paths.input_files_dir
    
    if config_files == True:
        # Read configurations from YAML files:
        scen_techs = dem_helper.update_scen_techs_from_yaml(
            paths.input_files_dir,
            inp.scen_techs
            )
    elif config_files == False:
        # Read configurations within Python API:
        scen_techs = dem_helper.update_scen_techs_from_config(
            inp.scen_techs,
            config_dict
            )
    
    # Create instance of district energy model (dem):
    dem_inst = dem.DistrictEnergyModel(
        paths = paths,
        arg_com_nr = scen_techs['simulation']['district_number'],
        scen_techs=scen_techs,
        toggle_energy_balance_tests = inp.toggle_energy_balance_tests
        )
    
    print("------------------------------")
    print('\nModel instance generated.')
    print("------------------------------")
    print('\nStart model run ...')
    
    dem_inst.run(
        scen_techs = scen_techs,
        toggle_load_pareto_results = inp.toggle_load_pareto_results,
        toggle_save_results = scen_techs['simulation']['save_results'],
        toggle_plot = scen_techs['simulation']['generate_plots']
        )
    
    print("\n------------------------------")
    print("Process completed.")
    print("==============================")
    sim_plt = scen_techs['simulation']['generate_plots']
    sim_res = scen_techs['simulation']['save_results']
    if sim_plt or sim_res:
        p_ = f"{str(dem_inst.results_path)}"
        print(f"\nOutput files saved to: {p_}")
        print("------------------------------")
    # print("==============================")
    
    return dem_inst

if __name__ == "__main__":
    launch()