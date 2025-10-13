# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 14:12:06 2023

@author: UeliSchilt
"""

"""
Import classes of the various technologies.
"""

import numpy as np
import dem_constants as C

#------------------------------------------------------------------------------
# Generation
from techs.dem_tech_grid_supply import GridSupply
  
#------------------------------------------------------------------------------
# Conversion
from techs.dem_tech_solar_pv import SolarPV
from techs.dem_tech_solar_thermal import SolarThermal
from techs.dem_tech_wind_power import WindPower
from techs.dem_tech_hydro_power import HydroPower
from techs.dem_tech_heat_pump import HeatPump
from techs.dem_tech_electric_heater import ElectricHeater
from techs.dem_tech_heat_exchanger import HeatExchanger    
from techs.dem_tech_oil_boiler import OilBoiler
from techs.dem_tech_gas_boiler import GasBoiler
from techs.dem_tech_wood_boiler import WoodBoiler
from techs.dem_tech_district_heating import DistrictHeating
from techs.dem_tech_biomass import Biomass
from techs.dem_tech_biomass import HydrothermalGasification
from techs.dem_tech_biomass import WoodGasificationUpgrade
from techs.dem_tech_biomass import AnaerobicDigestionUpgrade
from techs.dem_tech_biomass import AnaerobicDigestionUpgradeHydrogen
from techs.dem_tech_biomass import AnaerobicDigestionCHP
from techs.dem_tech_biomass import WoodGasificationUpgradeHydrogen
from techs.dem_tech_biomass import WoodGasificationCHP
from techs.dem_tech_hydrogen import HydrogenProduction
from techs.dem_tech_chp_gt import CHPGasTurbine
from techs.dem_tech_gas_turbine_cp import GasTurbineCP
from techs.dem_tech_steam_turbine import SteamTurbine
from techs.dem_tech_wood_boiler_sg import WoodBoilerSG
from techs.dem_tech_waste_to_energy import WasteToEnergy
from techs.dem_tech_heat_pump_cp import HeatPumpCP
from techs.dem_tech_heat_pump_cp_lt import HeatPumpCPLT
from techs.dem_tech_oil_boiler_cp import OilBoilerCP
from techs.dem_tech_wood_boiler_cp import WoodBoilerCP
from techs.dem_tech_gas_boiler_cp import GasBoilerCP
from techs.dem_tech_waste_heat import WasteHeat
from techs.dem_tech_waste_heat_low_temperature import WasteHeatLowTemperature

#------------------------------------------------------------------------------
# Storage
from techs.dem_tech_thermal_energy_storage import ThermalEnergyStorage
from techs.dem_tech_thermal_energy_storage_dc import ThermalEnergyStorageDC
from techs.dem_tech_battery_energy_storage import BatteryEnergyStorage
from techs.dem_tech_gas_tank_energy_storage import GasTankEnergyStorage
from techs.dem_tech_hydrogen_energy_storage import HydrogenEnergyStorage

from techs.dem_tech_pile_of_berries import PileOfBerries

#------------------------------------------------------------------------------
# Other
from techs.dem_tech_other import Other





