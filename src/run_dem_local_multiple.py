# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 10:15:29 2025

@author: UeliSchilt
"""

"""
For running DEM locally using the source code.
Difference to run_dem_local.py:
    - Multiple municipalities can be run in a loop.
    - The input is not provided in .yaml files, but directly here in the sctipt
      (only the input deviation from default values)
"""

import ast
import pandas as pd

from district_energy_model.model import launch

canton = 'ZG'

root_dir = '..'

# File containing munic numbers:
ggdenr_list_file = f'../config/config_files/tmp_ggdenr_lists_cantons/ggdenr_list_{canton}.txt'
# File containing munic names:
munic_list_file = f'../config/config_files/tmp_ggdenr_lists_cantons/munic_list_{canton}.txt'

# Read list from .txt file:
with open(ggdenr_list_file, "r", encoding="utf-8") as f1:
    ggdenr_list = ast.literal_eval(f1.read())
with open(munic_list_file, "r", encoding="utf-8") as f2:
    munic_list = ast.literal_eval(f2.read())
    
munic_qty = len(ggdenr_list)
    
rows = []
idx_red = 0
    
for idx, GGDENR in enumerate(ggdenr_list):    
    munic_name = munic_list[idx]
    
    print("\n")
    print(f"///////////// ----- {idx+1}/{munic_qty} ----- /////////////")
    print("\n")
    
    if GGDENR == 2391 or GGDENR == 5391:
        # Staatswald Galm und C'za Cadenazzo/Monteceneri (keine richtigen Gemeinden)
        idx_red += 1

    else:
        # Input deviating from default input:
        config_dict_ = {
            'simulation':{
                'number_of_days':365,
                'district_number':GGDENR,
                'generate_plots':False,
                'save_results':True
                }
            }
        
        my_model = launch(
            root_dir=root_dir,
            config_files=False,
            config_dict=config_dict_
            )  
            
        res_annual = my_model.annual_results()
        
        folder_idx = idx - idx_red
        
        # Build one row
        row = {"GGDENR": GGDENR, "munic_name": munic_name, "Output folder": folder_idx}
        row.update(res_annual)
        rows.append(row)
        
        del res_annual
        del my_model
    
    
df_results = pd.DataFrame(rows)
    
# Enforce column order (GGDENR, munic_name first)
cols = ["GGDENR", "munic_name", "Output folder"] + [c for c in df_results.columns if c not in ("GGDENR", "munic_name", "Output folder")]
df_results = df_results[cols]

df_results.to_csv(f"{root_dir}/annual_results_canton_{canton}.csv")

# Columns to exclude from totals
exclude_cols = ["GGDENR", "munic_name", "Output folder"]

# Select numeric columns except excluded ones
sum_cols = [c for c in df_results.columns if c not in exclude_cols]

# Compute totals
totals = df_results[sum_cols].sum(numeric_only=True)

# Save to txt file
totals_file = f"{root_dir}/annual_results_canton_{canton}_TOTALS.txt"

with open(totals_file, "w", encoding="utf-8") as f:
    for col, val in totals.items():
        f.write(f"{col}: {val}\n")

# print(df_results.head())

