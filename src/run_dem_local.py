# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 10:15:29 2025

@author: UeliSchilt
"""

"""
For running DEM locally using the source code.
"""
import argparse
from district_energy_model.model import launch

root_dir = '..'

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--input_file", type=str, default="district_energy_model.input_files.inputs")
    parser.add_argument("--config_files_dir", type=str, default="")
    parser.add_argument("--output_files_dir", type=str, default="")

    args = parser.parse_args()

    input_dir = args.input_file
    config_dir = args.config_files_dir
    output_dir = args.output_files_dir

    my_model = launch(root_dir=root_dir, 
                      input_dir = input_dir, 
                      config_dir=config_dir, 
                      output_dir=output_dir)
    
    # res_hourly = my_model.hourly_results()
    # res_annual = my_model.annual_results()
    # res_cost = my_model.total_cost()
    
    # print(res_hourly.info())
    # print(res_annual)
    # print(res_cost)
