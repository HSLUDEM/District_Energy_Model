import pandas as pd
import numpy as np

kelvin_offset = 273.15

temptable_radiators = { #source: "Set the heating curve correctly" by BFE Energie-Schweiz
    1980 : np.array([[-8, 15], [65, 25]]), #before 1980
    1990 : np.array([[-8, 15], [55, 25]]), #1980-2000
    2000 : np.array([[-8, 15], [55, 25]]), #1980-2000
    2010 : np.array([[-8, 15], [45, 25]]), #2000-2010
    2100 : np.array([[-8, 15], [37.5, 21]]), #2010-2100
}
temptable_underfloorheating = { #source: "Set the heating curve correctly" by BFE Energie-Schweiz
    1980 : np.array([[-8, 15], [42.5, 25]]), #before 1990
    1990 : np.array([[-8, 15], [42.5, 25]]), #before 1990
    2000 : np.array([[-8, 15], [35, 25]]), #1990-2010
    2010 : np.array([[-8, 15], [35, 25]]), #1990-2010
    2100 : np.array([[-8, 15], [32.5, 21]]), #2010-2100
}

temptable_mapping = {year: 
                       1980 if year < 1980 
                       else (1990 if year < 1990 
                             else (2000 if year < 2000 
                                   else (2010 if year < 2010
                                         else 2100)))
                                                for year in np.arange(1600, 2100,1)}

tempfunctions_radiators = {x : lambda t, x2=x:  
                           ((temptable_radiators[x2][1][1]-temptable_radiators[x2][1][0])
                            /(temptable_radiators[x2][0][1]-temptable_radiators[x2][0][0]))
                           *(t-temptable_radiators[x2][0][0])+temptable_radiators[x2][1][0]  
                           for x in temptable_radiators.keys()}
tempfunctions_underfloorheating = {x: (lambda t, x2=x: 
                           ((temptable_underfloorheating[x2][1,1]-temptable_underfloorheating[x2][1,0])
                            /(temptable_underfloorheating[x2][0,1]-temptable_underfloorheating[x2][0,0]))
                           *(t-temptable_underfloorheating[x2][0,0])+temptable_underfloorheating[x2][1,0])
                           for x in temptable_underfloorheating.keys()}

gbaup_to_gbauj = {8011 : 1910,
                  8012 : 1932,
                  8013 : 1953,
                  8014 : 1966,
                  8015 : 1976,
                  8016 : 1983,
                  8017 : 1988,
                  8018 : 1993,
                  8019 : 1998,
                  8020 : 2003,
                  8021 : 2008,
                  8022 : 2013,
                  8023 : 2020}

temp_dhw = 55 # Temperatur DHW - hoch genug zum Legionellen-Killen

temp_brine = 5.0-3.0*np.cos(np.linspace(0, 2*np.pi, 24*365)-2*np.pi*(31+28)/365) # Brine temperature

share_brine_air_hp_existing = {"air_to_water" : 0.66, "brine_to_water": 0.34}
share_brine_air_hp_new = {"air_to_water" : 0.72, "brine_to_water": 0.28}

brine_to_water_keys_gwr = [7510, 7511, 7512, 7513]
air_to_water_keys_gwr = [7501]

smaller1 = lambda x: (x<1)*x + (x >= 1)
relu = lambda x: x * (x>0)
share_underfloor = lambda year : smaller1(relu((year-1970)*(0.5/30)))

COP_MAX_FACTOR = 20.0 #COP of individual systems is capped at 20 * quality_factor (e.g. for quality_factor = 0.4 -> 8)


# tempfunctions_radiators = 

def calculateHPCP_COP(paths,
                      tech_instance,
                      weather_year,
                      com_nr):
      weather_data = pd.read_feather(paths.weather_data_delta_method_dir + str(com_nr) + ".feather")[weather_year].to_numpy()
      
      hot_temp = kelvin_offset+tech_instance._cop_hot_temperature_constant_temperature_value + np.zeros(len(weather_data))
      low_temp = kelvin_offset+tech_instance._cop_source_constant_temperature_value if tech_instance._cop_source_temperature == 'constant_temperature' else kelvin_offset+weather_data

      carnot_eff = hot_temp / (hot_temp - low_temp)

      carnot_eff[carnot_eff > COP_MAX_FACTOR] = COP_MAX_FACTOR

      return tech_instance._quality_factor* carnot_eff



def calculateCOPs(
        paths,
        df_com_yr, 
        quality_factor_ashp_new, 
        quality_factor_ashp_old,
        quality_factor_gshp_new, 
        quality_factor_gshp_old, 
        com_nr, 
        dem_demand, 
        weather_year,
        consider_renovation_effects = False,
        total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios = {
                  'v_h_eh' : 0.0,
                  'v_h_hp' : 0.8, 'v_h_dh' : 0.05, 'v_h_gb' : 0.05, 
                  'v_h_ob' : 0.05, 'v_h_wb' : 0.05, 'v_h_solar' : 0.0, 
                  'v_h_other' : 0.0 }, 
        total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios = {
                  'v_hw_eh' : 0.1,
                  'v_hw_hp' : 0.7, 'v_hw_dh' : 0.05, 'v_hw_gb' : 0.05,
                  'v_hw_ob' : 0.05,'v_hw_wb' : 0.05,'v_hw_solar' : 0.0,
                  'v_hw_other' : 0.0 },
        optimisation_enabled = True,
        ):
      

      if not consider_renovation_effects:
            df_com_yr["total_renovation_flag"] = 0.0
            df_com_yr["heat_generator_replacement_flag"] = 0.0
            df_com_yr["d_h_s_yr_future_renov_adjusted"] = df_com_yr["heat_energy_demand_estimate_kWh_combined"]

      reassignment_dict_sh = {'v_h_eh' : 0.0,
                                'v_h_hp' : 0.0, 
                                'v_h_dh' : 0.0, 
                                'v_h_gb' : 0.0,
                                'v_h_ob' : 0.0,
                                'v_h_wb' : 0.0,
                                'v_h_solar' : 0.0,
                                'v_h_other' : 1.0 } if optimisation_enabled else total_renovation_heat_generator_reassignment_rates_space_heating_for_manual_scenarios
      reassignment_dict_dhw = {'v_hw_eh' : 0.0,
                                'v_hw_hp' : 0.0, 
                                'v_hw_dh' : 0.0, 
                                'v_hw_gb' : 0.0,
                                'v_hw_ob' : 0.0,
                                'v_hw_wb' : 0.0,
                                'v_hw_solar' : 0.0,
                                'v_hw_other' : 1.0 } if optimisation_enabled else total_renovation_heat_generator_reassignment_rates_dhw_for_manual_scenarios




      df_com_yr["heat_pump_share_air_to_water"] = 0.0
      df_com_yr["heat_pump_share_brine_to_water"] = 0.0

      df_com_yr.loc[(df_com_yr["Heating_System"] == "v_h_hp") & 
                        (df_com_yr["GENH1"].isin(brine_to_water_keys_gwr)), "heat_pump_share_brine_to_water"] = 1.0
      df_com_yr.loc[(df_com_yr["Heating_System"] == "v_h_hp") & 
                        (df_com_yr["GENH1"].isin(brine_to_water_keys_gwr)), "heat_pump_share_air_to_water"] = 0.0

      df_com_yr.loc[(df_com_yr["Heating_System"] == "v_h_hp") & 
                        (df_com_yr["GENH1"].isin(air_to_water_keys_gwr)), "heat_pump_share_brine_to_water"] = 0.0
      df_com_yr.loc[(df_com_yr["Heating_System"] == "v_h_hp") & 
                        (df_com_yr["GENH1"].isin(air_to_water_keys_gwr)), "heat_pump_share_air_to_water"] = 1.0

      df_com_yr.loc[(df_com_yr["Heating_System"] == "v_h_hp") & 
                        (~(df_com_yr["GENH1"].isin(air_to_water_keys_gwr+brine_to_water_keys_gwr))), 
                        "heat_pump_share_brine_to_water"] = share_brine_air_hp_existing["brine_to_water"]
      df_com_yr.loc[(df_com_yr["Heating_System"] == "v_h_hp") & 
                        (~(df_com_yr["GENH1"].isin(air_to_water_keys_gwr+brine_to_water_keys_gwr))), 
                        "heat_pump_share_air_to_water"] = share_brine_air_hp_existing["air_to_water"]


      df_com_yr.loc[~(df_com_yr["Heating_System"] == "v_h_hp"), "heat_pump_share_brine_to_water"] = share_brine_air_hp_new["brine_to_water"]
      df_com_yr.loc[~(df_com_yr["Heating_System"] == "v_h_hp"), "heat_pump_share_air_to_water"] = share_brine_air_hp_new["air_to_water"]

      df_com_yr["construction_year_for_hp_cop"] = df_com_yr["GBAUJ"]
      df_com_yr.loc[df_com_yr["GBAUJ"].isna(), "construction_year_for_hp_cop"] = df_com_yr.loc[df_com_yr["GBAUJ"].isna(), "GBAUP"].map(gbaup_to_gbauj)
      df_com_yr.loc[df_com_yr["construction_year_for_hp_cop"].isna(), "construction_year_for_hp_cop"] = 1910

      df_com_yr["construction_year_for_hp_cop_heating_curve"] = df_com_yr["construction_year_for_hp_cop"].map(temptable_mapping)
      df_com_yr.loc[df_com_yr["construction_year_for_hp_cop_heating_curve"].isna(), "construction_year_for_hp_cop_heating_curve"] = temptable_mapping[1910]

      df_com_yr["construction_year_for_hp_cop_heating_curve_after_total_renovation"] = max(temptable_mapping.values())
      df_com_yr["share_underfloor"] = share_underfloor(df_com_yr["construction_year_for_hp_cop"])      
      df_com_yr["share_radiators"] = 1.0 - df_com_yr["share_underfloor"]




      diss_types = df_com_yr[["share_underfloor", "share_radiators"]].to_numpy()

      hp_style = df_com_yr[["heat_pump_share_air_to_water", "heat_pump_share_brine_to_water"]].to_numpy()

      already_existing_dummies = pd.get_dummies(~(df_com_yr["Heating_System"] == "v_h_hp"))
      already_existing_dummies = already_existing_dummies.reindex(columns=[False, True], fill_value=0)
      already_existing_dummies["One-to-One"] = 0
      already_existing_dummies_columnorder = already_existing_dummies.columns 
      already_existing = already_existing_dummies.to_numpy().astype("float") #Order: Already Existing | Not already existing | Already existing but up for renewal

      already_existing_dhw_dummies = pd.get_dummies(~(df_com_yr["Hot_Water_System"] == "v_hw_hp"))
      already_existing_dhw_dummies = already_existing_dhw_dummies.reindex(columns=[False, True], fill_value=0)
      already_existing_dhw_dummies["One-to-One"] = 0
      already_existing_dhw_dummies_columnorder = already_existing_dhw_dummies.columns
      already_existing_dhw = already_existing_dhw_dummies.to_numpy().astype("float") #Order: Already Existing | Not already existing | Already existing but up for renewal


      construction_year_for_heating_curve_dummies = pd.get_dummies(
            df_com_yr["construction_year_for_hp_cop_heating_curve"]
            )
      construction_year_for_heating_curve_dummies = construction_year_for_heating_curve_dummies.reindex(columns=list(np.unique(list(temptable_mapping.values()))), fill_value=0)
      construction_year_for_heating_curve_dummies_columns = construction_year_for_heating_curve_dummies.columns
      construction_year_for_heating_curve = construction_year_for_heating_curve_dummies.to_numpy().astype("float")
      
      probability_array = (diss_types[:,:,np.newaxis, np.newaxis, np.newaxis]
                           *hp_style[:,np.newaxis,:, np.newaxis, np.newaxis]
                           *already_existing[:, np.newaxis, np.newaxis, :, np.newaxis]
                           *construction_year_for_heating_curve[:, np.newaxis, np.newaxis, np.newaxis, :]
                           )
      
      probability_array_dhw = hp_style[:,:,np.newaxis]*already_existing_dhw[:,np.newaxis,:]



      if consider_renovation_effects:
            total_renovation_flag = df_com_yr["total_renovation_flag"].to_numpy().astype("float")

            heat_generator_replacement_flag = df_com_yr["heat_generator_replacement_flag"].to_numpy().astype("float")
            weather_year_underfloor_share = share_underfloor(weather_year)

            probability_array = (
                  probability_array*(1-(total_renovation_flag+heat_generator_replacement_flag)[:, np.newaxis, np.newaxis, np.newaxis, np.newaxis])


                  +total_renovation_flag[:, np.newaxis, np.newaxis, np.newaxis, np.newaxis]
                  *np.sum(probability_array, axis = (1,3,4))[:, np.newaxis, :, np.newaxis, np.newaxis]
                  *np.array([0,1.0-reassignment_dict_sh["v_h_hp"],reassignment_dict_sh["v_h_hp"]])[np.newaxis, np.newaxis, np.newaxis, :, np.newaxis] #old new one-to-one
                  *np.array([0,0,0,0,1])[np.newaxis, np.newaxis, np.newaxis, np.newaxis, :] # age-type of building
                  *np.array(
                        [weather_year_underfloor_share, 1-weather_year_underfloor_share] # share underfloor
                        )[np.newaxis, :, np.newaxis, np.newaxis, np.newaxis]
                  *already_existing[:,0][:,np.newaxis, np.newaxis, np.newaxis, np.newaxis]

                  +total_renovation_flag[:, np.newaxis, np.newaxis, np.newaxis, np.newaxis]
                  *np.sum(probability_array, axis = (1,3,4))[:, np.newaxis, :, np.newaxis, np.newaxis]
                  *np.array([0,1,0])[np.newaxis, np.newaxis, np.newaxis, :, np.newaxis] #old new one-to-one
                  *np.array([0,0,0,0,1])[np.newaxis, np.newaxis, np.newaxis, np.newaxis, :] # age-type of building
                  *np.array(
                        [weather_year_underfloor_share, 1-weather_year_underfloor_share] # share underfloor
                        )[np.newaxis, :, np.newaxis, np.newaxis, np.newaxis]
                  *already_existing[:,1][:,np.newaxis, np.newaxis, np.newaxis, np.newaxis]

                  +heat_generator_replacement_flag[:, np.newaxis, np.newaxis, np.newaxis, np.newaxis]
                  *np.sum(probability_array, axis = (3,))[:, :, :, np.newaxis, :]
                  *np.array([0,0,1])[np.newaxis, np.newaxis, np.newaxis, :, np.newaxis]
                  *already_existing[:,0][:,np.newaxis, np.newaxis, np.newaxis, np.newaxis]

                  +heat_generator_replacement_flag[:, np.newaxis, np.newaxis, np.newaxis, np.newaxis]
                  *np.sum(probability_array, axis = (3,))[:, :, :, np.newaxis, :]
                  *np.array([0,1,0])[np.newaxis, np.newaxis, np.newaxis, :, np.newaxis]
                  *already_existing[:,1][:,np.newaxis, np.newaxis, np.newaxis, np.newaxis]

                  )

            

            probability_array_dhw = (
                  probability_array_dhw*(1-(total_renovation_flag+heat_generator_replacement_flag)[:, np.newaxis, np.newaxis])
                  
                  +(total_renovation_flag)[:, np.newaxis, np.newaxis]
                  *np.sum(probability_array_dhw, axis = 2)[:,:,np.newaxis]
                  *np.array([0,1.0-reassignment_dict_dhw["v_hw_hp"],reassignment_dict_dhw["v_hw_hp"]])[np.newaxis, np.newaxis, :]
                  *already_existing_dhw[:,0][:,np.newaxis,np.newaxis]

                  +(total_renovation_flag)[:, np.newaxis, np.newaxis]
                  *np.sum(probability_array_dhw, axis = 2)[:,:,np.newaxis]
                  *np.array([0,1,0])[np.newaxis, np.newaxis, :]
                  *already_existing_dhw[:,1][:,np.newaxis,np.newaxis]

                  +(heat_generator_replacement_flag)[:, np.newaxis, np.newaxis]
                  *np.sum(probability_array_dhw, axis = 2)[:,:,np.newaxis]
                  *np.array([0,0,1])[np.newaxis, np.newaxis, :]
                  *already_existing_dhw[:,0][:,np.newaxis,np.newaxis]

                  +(heat_generator_replacement_flag)[:, np.newaxis, np.newaxis]
                  *np.sum(probability_array_dhw, axis = 2)[:,:,np.newaxis]
                  *np.array([0,1,0])[np.newaxis, np.newaxis, :]
                  *already_existing_dhw[:,1][:,np.newaxis,np.newaxis]

            )

            # print("SHARES (SF) = ", np.sum(probability_array[:,:,:,:,:], axis = (0,1,2,4)))
            # print("SHARES (DHW) = ", np.sum(probability_array_dhw[:,:,:], axis = (0,1)))


      energy_array = probability_array*(df_com_yr["d_h_s_yr_future_renov_adjusted"].to_numpy()[:, np.newaxis, np.newaxis, np.newaxis, np.newaxis])
      energy_array_dhw = probability_array_dhw*(df_com_yr["dhw_estimation_kWh_combined"].to_numpy()[:, np.newaxis, np.newaxis])
            
      energy_vals = np.nansum(energy_array, axis=0)
      energy_vals_dhw = np.nansum(energy_array_dhw, axis = 0)

      sh_profile = dem_demand.get_d_h_s() / dem_demand.get_d_h_s_yr()
      dhw_profile = dem_demand.get_d_h_hw() / dem_demand.get_d_h_hw_yr()

      weather_data = pd.read_feather(paths.weather_data_delta_method_dir + str(com_nr) + ".feather")[weather_year].to_numpy()
      weather_data = weather_data[:len(sh_profile)]
      temp_brine_ = temp_brine[:len(sh_profile)]



      vorlauf_radiators = {x : tempfunctions_radiators[x](weather_data) for x in tempfunctions_radiators.keys()}
      vorlauf_underfloor = {x : tempfunctions_underfloorheating[x](weather_data) for x in tempfunctions_underfloorheating.keys()}

      carnot_eff_radiators_air_to_water = {x : (kelvin_offset+vorlauf_radiators[x])/(vorlauf_radiators[x]-weather_data) for x in vorlauf_radiators.keys()}
      carnot_eff_radiators_brine_to_water = {x : (kelvin_offset+vorlauf_radiators[x])/(vorlauf_radiators[x]-temp_brine_) for x in vorlauf_radiators.keys()}

      carnot_eff_underfloorheating_air_to_water = {x : (kelvin_offset+vorlauf_underfloor[x])/(vorlauf_underfloor[x]-weather_data) for x in vorlauf_underfloor.keys()}
      carnot_eff_underfloorheating_brine_to_water = {x : (kelvin_offset+vorlauf_underfloor[x])/(vorlauf_underfloor[x]-temp_brine_) for x in vorlauf_underfloor.keys()}

      carnot_eff_dhw_air_to_water =(kelvin_offset+temp_dhw)/(temp_dhw-weather_data)
      carnot_eff_dhw_brine_to_water = (kelvin_offset+temp_dhw)/(temp_dhw-temp_brine_)

      for x in vorlauf_radiators.keys():
            carnot_eff_radiators_air_to_water[x][weather_data > 15] = COP_MAX_FACTOR
            carnot_eff_radiators_brine_to_water[x][weather_data > 15] = COP_MAX_FACTOR

            carnot_eff_radiators_air_to_water[x][carnot_eff_radiators_air_to_water[x] > COP_MAX_FACTOR] = COP_MAX_FACTOR
            carnot_eff_radiators_brine_to_water[x][carnot_eff_radiators_brine_to_water[x] > COP_MAX_FACTOR] = COP_MAX_FACTOR

      for x in vorlauf_underfloor.keys():
            carnot_eff_underfloorheating_air_to_water[x][weather_data > 15] = COP_MAX_FACTOR
            carnot_eff_underfloorheating_brine_to_water[x][weather_data > 15] = COP_MAX_FACTOR

            carnot_eff_underfloorheating_air_to_water[x][carnot_eff_underfloorheating_air_to_water[x] > COP_MAX_FACTOR] = COP_MAX_FACTOR
            carnot_eff_underfloorheating_brine_to_water[x][carnot_eff_underfloorheating_brine_to_water[x] > COP_MAX_FACTOR] = COP_MAX_FACTOR

      carnot_effs_all = np.zeros((len(sh_profile), 2,2,5)) # Dimensions: Time, diss_type, hp_style, construction_year_cat
      for diss_is_radiator in [False, True]:
            for hp_style_is_brine_to_water in [False, True]:
                  for construction_year_cat_index in range(len(construction_year_for_heating_curve_dummies_columns)):
                        construction_year_cat = construction_year_for_heating_curve_dummies_columns[construction_year_cat_index]
                        
                        if diss_is_radiator and hp_style_is_brine_to_water:
                              current_line = carnot_eff_radiators_brine_to_water[construction_year_cat]
                        elif diss_is_radiator and not hp_style_is_brine_to_water:
                              current_line = carnot_eff_radiators_air_to_water[construction_year_cat]
                        elif (not diss_is_radiator) and hp_style_is_brine_to_water:
                              current_line = carnot_eff_underfloorheating_brine_to_water[construction_year_cat]
                        elif (not diss_is_radiator) and not hp_style_is_brine_to_water:
                              current_line = carnot_eff_underfloorheating_air_to_water[construction_year_cat]

                        carnot_effs_all[:, int(diss_is_radiator), int(hp_style_is_brine_to_water), construction_year_cat_index] = \
                              current_line
                        
      effs_all_old = carnot_effs_all * (np.array([quality_factor_ashp_old, quality_factor_gshp_old])[np.newaxis, np.newaxis, :, np.newaxis])
      effs_all_new = carnot_effs_all * (np.array([quality_factor_ashp_new, quality_factor_gshp_new])[np.newaxis, np.newaxis, :, np.newaxis])

      carnot_effs_all_dhw = np.array([carnot_eff_dhw_air_to_water, carnot_eff_dhw_brine_to_water]).T
      effs_all_dhw_old = carnot_effs_all_dhw * (np.array([quality_factor_ashp_old, quality_factor_gshp_old])[np.newaxis, :])
      effs_all_dhw_new = carnot_effs_all_dhw * (np.array([quality_factor_ashp_new, quality_factor_gshp_new])[np.newaxis, :])

      energy_vals_profiled = sh_profile[:, np.newaxis, np.newaxis, np.newaxis, np.newaxis] * energy_vals[np.newaxis, :, :, :, :]
      energy_vals_dhw_profiled = dhw_profile[:, np.newaxis, np.newaxis] * energy_vals_dhw[np.newaxis, :, :]
      
      #energy_vals_profiled: second-to-last index gives existence: 0=already hp, 1=not-yet hp
      #energy_vals_dhw_profiled: last index gives existence: 0=already hp, 1=not-yet hp

      total_heat_produced_existing_hps = (
            np.sum(energy_vals_profiled[:,:,:,0,:], axis = (1,2,3))
            +np.sum(energy_vals_dhw_profiled[:,:,0], axis = (1,))
            )
      total_heat_produced_new_hps = (
            np.sum(energy_vals_profiled[:,:,:,1,:], axis = (1,2,3))
            +np.sum(energy_vals_dhw_profiled[:,:,1], axis = (1,))
            )
      total_heat_produced_one_to_one_replacement_hps = (
            np.sum(energy_vals_profiled[:,:,:,2,:], axis = (1,2,3))
            +np.sum(energy_vals_dhw_profiled[:,:,2], axis = (1,))
            )


      electricity_consumed_existing_hps = np.sum(
            energy_vals_profiled[:,:,:,0,:] 
            / effs_all_old, 
            axis = (1,2,3)
            ) + np.sum(
            energy_vals_dhw_profiled[:,:,0] 
            / effs_all_dhw_old,
            axis = (1)
            )
      
      electricity_consumed_new_hps = np.sum(
            energy_vals_profiled[:,:,:,1,:] 
            / effs_all_new, 
            axis = (1,2,3)
            ) + np.sum(
            energy_vals_dhw_profiled[:,:,1] 
            / effs_all_dhw_new,
            axis = (1)
            )
      electricity_consumed_one_to_one_replacement_hps = np.sum(
            energy_vals_profiled[:,:,:,2,:] 
            / effs_all_new, 
            axis = (1,2,3)
            ) + np.sum(
            energy_vals_dhw_profiled[:,:,2] 
            / effs_all_dhw_new,
            axis = (1)
            )


      # print("JAZ (existing) = ", np.sum(total_heat_produced_existing_hps)/np.sum(electricity_consumed_existing_hps))
      # print("JAZ (new) = ", np.sum(total_heat_produced_new_hps)/np.sum(electricity_consumed_new_hps))
      # print("JAZ (one-to-one replacement) = ", np.sum(total_heat_produced_one_to_one_replacement_hps)/np.sum(electricity_consumed_one_to_one_replacement_hps))

      cops_existing = total_heat_produced_existing_hps/electricity_consumed_existing_hps
      cops_new = total_heat_produced_new_hps/electricity_consumed_new_hps
      with np.errstate(invalid='ignore', divide='ignore'):
          cops_one_to_one = total_heat_produced_one_to_one_replacement_hps/electricity_consumed_one_to_one_replacement_hps

      df_com_yr = df_com_yr.drop(columns = ['heat_pump_share_air_to_water', 
                                'heat_pump_share_brine_to_water', 
                                'construction_year_for_hp_cop', 
                                'construction_year_for_hp_cop_heating_curve', 
                                'construction_year_for_hp_cop_heating_curve_after_total_renovation', 
                                'share_underfloor', 
                                'share_radiators'])
      if not consider_renovation_effects:
            df_com_yr = df_com_yr.drop(columns=["total_renovation_flag", "heat_generator_replacement_flag"])

      return cops_existing, cops_new, cops_one_to_one, np.sum(total_heat_produced_existing_hps), np.sum(total_heat_produced_new_hps), np.sum(total_heat_produced_one_to_one_replacement_hps)


