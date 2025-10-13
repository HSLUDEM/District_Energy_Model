# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 12:20:38 2024

@author: UeliSchilt
"""

#Relevant years:

DATA_YEAR = 2025 # Year in which data was acquired, used e.g. for renovation rates
METEO_YEAR = 2023 # Year used for meteorological data as "present"

# -----------------------------------------------------------------------------
# Universal fixed constants:

CONV_MJ_to_kWh = 1000/3600 # Conversion from [MJ] to [kWh]
CONV_kWh_to_MJ = 1/CONV_MJ_to_kWh

# -----------------------------------------------------------------------------
# Material properties:

DENSITY_oil_kgpl = 0.9 # Density of oil [kg/l]

# -----------------------------------------------------------------------------
# Grid import
# !!! TMP: MUST BE IMPLEMENTED DYNAMICALLY !!!

# Swiss electricity mix:
# Source: BFE, Schweizerische Elektrizitätsstatistik 2021 (Fig. 1)
#share_hydro = (26.4 + 35.1)*0.01 # 0.01 as conversion to percentage
#share_nuclear = 28.9*0.01
#share_conventional_chp = 1.9*0.01
#share_renewable_chp = 1.7*0.01
#share_renewable_other = 6.0*0.01

# =============================================================================
# 2022: NOT USED ANYMORE!!!
SHARE_HYDRO = (24.4 + 28.4)*0.01 # 0.01 as conversion to percentage
SHARE_NUCLEAR = 36.4*0.01
SHARE_CONVENTIONAL_CHP = 1.4*0.01
SHARE_RENEWABLE_CHP = 1.7*0.01
SHARE_RENEWABLE_OTHER = 7.7*0.01

SHARE_RENEWABLE_IMPORT = 0.2 # [-] share of renewable electricity of cross-border imported electricity
# =============================================================================

# -----------------------------------------------------------------------------
# District Heating:
    


# -----------------------------------------------------------------------------
# Timeframe for generating weather files from meteostat (dem_demand.meteostat_weather_data(...)):
tf_meteostat_start = '2020-01-01 00:00'
tf_meteostat_end = '2022-12-31 23:00'
# tf_meteostat_start = '2023-01-01 00:00'
# tf_meteostat_end = '2023-12-31 23:00'

# -----------------------------------------------------------------------------
# Munics to omit: (due to not really being munics)
munics_omit = [
    5391, # Comunanza Cadenazzo_Monteceneri
    2391, # Staatswald Galm
    ]


# -----------------------------------------------------------------------------
# Error metrics

# Accepted (acc) difference in energy balances:
DIFF_ACC = 0.1
DIFF_SUM_ACC = 1.0 # 5.0 # 1.0 # 0.15

# Accepted negative values:
NEG_ACC = -0.1