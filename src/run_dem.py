# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 11:43:49 2023

@author: UeliSchilt
"""

# import pandas as pd
import os
# import time

# -----------------------------------------------------------------------------
# Change working directory to script location (here: 'src' directory):
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
# -----------------------------------------------------------------------------

import dem

# Generic input file:
# -----------------------
import input_files.inputs as inp


print("==============================")
print("Process started ...")
print("------------------------------")
print('\nModel Start')

# Create instance of district energy model (dem):
dem_inst = dem.DistrictEnergyModel(
    arg_com_nr = inp.com_nr,
    # base_tech_data = inp.base_tech_data,
    scen_techs=inp.scen_techs,
    toggle_energy_balance_tests = inp.toggle_energy_balance_tests
    )

dem_inst.run(
    scen_techs = inp.scen_techs,
    toggle_load_pareto_results = inp.toggle_load_pareto_results,
    # toggle_create_pareto_monetary_vs_co2 = inp.toggle_create_pareto_monetary_vs_co2,
    toggle_save_results = inp.toggle_save_results,
    toggle_plot = inp.toggle_plot,
    # N_pareto = inp.N_pareto
    # N_pareto = []
    )

print("------------------------------")
print("Process completed.")
print("==============================")