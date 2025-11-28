# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 14:12:06 2023

@author: UeliSchilt
"""

"""
Import classes of the various technologies.
"""

import numpy as np

from district_energy_model import dem_constants as C

#------------------------------------------------------------------------------
# Generation
from district_energy_model.techs.dem_tech_grid_supply import GridSupply
  
#------------------------------------------------------------------------------
# Conversion
from district_energy_model.techs.dem_tech_solar_pv import SolarPV
from district_energy_model.techs.dem_tech_solar_thermal import SolarThermal
from district_energy_model.techs.dem_tech_wind_power import WindPower
from district_energy_model.techs.dem_tech_hydro_power import HydroPower
from district_energy_model.techs.dem_tech_heat_pump import HeatPump
from district_energy_model.techs.dem_tech_electric_heater import ElectricHeater
from district_energy_model.techs.dem_tech_heat_exchanger import HeatExchanger    
from district_energy_model.techs.dem_tech_oil_boiler import OilBoiler
from district_energy_model.techs.dem_tech_gas_boiler import GasBoiler
from district_energy_model.techs.dem_tech_wood_boiler import WoodBoiler
from district_energy_model.techs.dem_tech_district_heating import DistrictHeating
from district_energy_model.techs.dem_tech_biomass import Biomass
from district_energy_model.techs.dem_tech_biomass import HydrothermalGasification
from district_energy_model.techs.dem_tech_biomass import WoodGasificationUpgrade
from district_energy_model.techs.dem_tech_biomass import AnaerobicDigestionUpgrade
from district_energy_model.techs.dem_tech_biomass import AnaerobicDigestionUpgradeHydrogen
from district_energy_model.techs.dem_tech_biomass import AnaerobicDigestionCHP
from district_energy_model.techs.dem_tech_biomass import WoodGasificationUpgradeHydrogen
from district_energy_model.techs.dem_tech_biomass import WoodGasificationCHP
from district_energy_model.techs.dem_tech_hydrogen import HydrogenProduction
from district_energy_model.techs.dem_tech_chp_gt import CHPGasTurbine
from district_energy_model.techs.dem_tech_gas_turbine_cp import GasTurbineCP
from district_energy_model.techs.dem_tech_steam_turbine import SteamTurbine
from district_energy_model.techs.dem_tech_wood_boiler_sg import WoodBoilerSG
from district_energy_model.techs.dem_tech_waste_to_energy import WasteToEnergy
from district_energy_model.techs.dem_tech_heat_pump_cp import HeatPumpCP
from district_energy_model.techs.dem_tech_heat_pump_cp_lt import HeatPumpCPLT
from district_energy_model.techs.dem_tech_oil_boiler_cp import OilBoilerCP
from district_energy_model.techs.dem_tech_wood_boiler_cp import WoodBoilerCP
from district_energy_model.techs.dem_tech_gas_boiler_cp import GasBoilerCP
from district_energy_model.techs.dem_tech_waste_heat import WasteHeat
from district_energy_model.techs.dem_tech_waste_heat_low_temperature import WasteHeatLowTemperature

#------------------------------------------------------------------------------
# Storage
from district_energy_model.techs.dem_tech_thermal_energy_storage import ThermalEnergyStorage
from district_energy_model.techs.dem_tech_thermal_energy_storage_dc import ThermalEnergyStorageDC
from district_energy_model.techs.dem_tech_battery_energy_storage import BatteryEnergyStorage
from district_energy_model.techs.dem_tech_gas_tank_energy_storage import GasTankEnergyStorage
from district_energy_model.techs.dem_tech_hydrogen_energy_storage import HydrogenEnergyStorage

from district_energy_model.techs.dem_tech_pile_of_berries import PileOfBerries

#------------------------------------------------------------------------------
# Other
from district_energy_model.techs.dem_tech_other import Other





