# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 11:43:49 2023

@author: UeliSchilt
"""

import os

# -----------------------------------------------------------------------------
# Change working directory to script location (here: 'src' directory):
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
# -----------------------------------------------------------------------------

import dem
import paths
import dem_helper

# Generic input file:
# -----------------------
import input_files.inputs as inp

print("==============================")
print("Process started ...")
print("------------------------------")
print('\nModel Start')


# Read input files and update scen_techs:
paths.input_files_dir

scen_techs = dem_helper.update_scen_techs_from_yaml(
    paths.input_files_dir,
    inp.scen_techs
    )

print(scen_techs.keys())


# Create instance of district energy model (dem):
dem_inst = dem.DistrictEnergyModel(
    arg_com_nr = scen_techs['simulation']['district_number'],
    scen_techs=scen_techs,
    toggle_energy_balance_tests = inp.toggle_energy_balance_tests
    )

dem_inst.run(
    scen_techs = scen_techs,
    toggle_load_pareto_results = inp.toggle_load_pareto_results,
    toggle_save_results = scen_techs['simulation']['save_results'],
    toggle_plot = scen_techs['simulation']['generate_plots']
    )

print("------------------------------")
print("Process completed.")
print("==============================")