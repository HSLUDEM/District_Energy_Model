# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 10:15:29 2025

@author: UeliSchilt
"""

"""
For running DEM locally using the source code.
"""

from district_energy_model.model import launch

root_dir = '.'

if __name__ == "__main__":
    my_model = launch(root_dir=root_dir)
    
    # res_hourly = my_model.hourly_results()
    # res_annual = my_model.annual_results()
    # res_cost = my_model.total_cost()
    
    # print(res_hourly.info())
    # print(res_annual)
    # print(res_cost)
