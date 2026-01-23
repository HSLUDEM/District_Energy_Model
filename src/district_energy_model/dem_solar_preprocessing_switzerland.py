# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 07:19:20 2023

@author: PascalVecsei
"""

"""
Functions to obtain profiles for PV

"""


import pandas as pd
import numpy as np

NUM_GROUPS = 4 #number of different groups


EXISTING_EPPS_GROUP = 0 #Which of the groups is the group for existing solar installations?

#THESE PARAMETERS MUST BE THE SAME AS IN existing_pv_electricity_production_plants.py
EFFICIENCY_TO_USE = 0.18
BASE_IRRADIANCE = 1000.0


def obtain_com_roof_profile(com_nr, efficiency_overall, paths):

    efficiency = efficiency_overall

    path_roof_dat = paths.pv_roof_dir
    path_epps_unassigned = paths.pv_epps_unassigned_path

    path_pv_profile_file = path_roof_dat + "/" + str(com_nr) + "_pv_profiles_dach.feather"

    path_building_pv_dach = path_roof_dat + "/" + str(com_nr) + "_building_pv_dach.feather"

    epps_unassigned = pd.read_feather(path_epps_unassigned)

    pv_profiles = pd.read_feather(path_pv_profile_file)

    pv_building_data = pd.read_feather(path_building_pv_dach)



    epp_power_unassigned = 0.0
    epp_power_assigned_only_to_egid = 0.0
    if com_nr in epps_unassigned.index:
        com_line = epps_unassigned[epps_unassigned.index == com_nr].iloc[0]
        epp_power_unassigned = com_line["non_assigned_power"]
        epp_power_assigned_only_to_egid = com_line["only_assigned_to_egid_power"]

    results = {}

    for group_number in range(NUM_GROUPS):

        # print("GROUP = ", group_number)

        if group_number == EXISTING_EPPS_GROUP:
            efficiency = EFFICIENCY_TO_USE

        if 'per_group_wintersum_grouping_group_'+str(group_number)+'_sumprofile' in pv_profiles.columns:

            sumprofile = pv_profiles['per_group_wintersum_grouping_group_'+str(group_number)+'_sumprofile']

            energysum = pv_building_data['per_group_wintersum_grouping_group_'+str(group_number)+'_energysum'].sum()
            areasum = pv_building_data['per_group_wintersum_grouping_group_'+str(group_number)+'_areasum'].sum()

        else:
            sumprofile = np.zeros(8760)
            energysum = 0
            areasum = 0

        peakpower = areasum * BASE_IRRADIANCE * efficiency / 1000.0

        peakpower_profile = efficiency * np.max(sumprofile)

        capex_opex_increase_factor = peakpower / peakpower_profile

        pv_profile = sumprofile * efficiency

        if group_number == EXISTING_EPPS_GROUP and energysum > 0:
            pv_profile = ((peakpower + epp_power_assigned_only_to_egid + epp_power_unassigned)/peakpower) * pv_profile
        elif energysum == 0:
            pv_profile = 0* pv_profile
        results[group_number] = (pv_profile, capex_opex_increase_factor)

    return results

def obtain_custom_district_roof_profile(com_nrs, egid_list, efficiency_overall, paths):
    ...

    #calculate the roof profile for a 
    # custom district based on custom district 
    # (which can contain parts of different municipalities)

    distresults = {}

    group_profiles = [[] for _ in range(NUM_GROUPS)]
    area_sums = [[] for _ in range(NUM_GROUPS)]
    energy_sums = [[] for _ in range(NUM_GROUPS)]

    for com_nr in com_nrs:
        efficiency = efficiency_overall

        path_roof_dat = paths.pv_roof_dir

        path_epps_unassigned = paths.pv_epps_unassigned_dir + "/" + "solar_epps_not_assigned_to_roofs_powers.feather"

        path_pv_profile_file = path_roof_dat + "/" + str(com_nr) + "_pv_profiles_dach.feather"

        path_building_pv_dach = path_roof_dat + "/" + str(com_nr) + "_building_pv_dach.feather"

        epps_unassigned = pd.read_feather(path_epps_unassigned)

        pv_profiles = pd.read_feather(path_pv_profile_file)

        pv_building_data = pd.read_feather(path_building_pv_dach)

        pv_building_data_loc = pv_building_data[pv_building_data.index.isin(egid_list)]


        number_of_pcas_per_cat = [0 for i in range(NUM_GROUPS)]
        for s in pv_building_data_loc.columns:
            # print(s)
            if 'pca_prefactor' in s:
                group = int(s.split("group_")[-1].split("_")[0])
                prefn = int(s.split("prefactor_")[1])

                if number_of_pcas_per_cat[group] < prefn:
                    number_of_pcas_per_cat[group] = prefn
        
        for i in range(NUM_GROUPS):
            number_of_pcas_per_cat[i] += 1

        for group_number in range(NUM_GROUPS):
            sumprofile = pv_profiles['per_group_wintersum_grouping_group_'+str(group_number)+'_sumprofile'] * 0.0
            areasum = 0
            energysum = 0

            profiles = np.array([pv_profiles["per_group_wintersum_grouping_group_"+str(group_number)+"_pca_meanprofile"]]+
                      [pv_profiles["per_group_wintersum_grouping_group_"+str(group_number)+"_pca_componentprofile_"+str(_)] 
                      for _ in range(number_of_pcas_per_cat[group_number])])

            for i in range(len(pv_building_data_loc)):
                line = pv_building_data_loc.iloc[i]

                if line["per_group_wintersum_grouping_group_"+str(group_number)+"_energysum"] > 0:

                    prefs = np.array([1.0] 
                                     + [line["per_group_wintersum_grouping_group_"
                                             +str(group_number)
                                             +"_pca_prefactor_"+str(_)] 
                                             for _ in range(number_of_pcas_per_cat[group_number])])

                    profile_loc = np.abs(np.sum(prefs[:, np.newaxis] * profiles, axis = 0))
                    profile_loc = profile_loc/np.sum(profile_loc)
                    
                    sumprofile += profile_loc * line["per_group_wintersum_grouping_group_"+str(group_number)+"_energysum"]
                    areasum += line["per_group_wintersum_grouping_group_"+str(group_number)+"_areasum"]
                    energysum += line["per_group_wintersum_grouping_group_"+str(group_number)+"_energysum"]

            print(com_nr, group_number, areasum, energysum, energysum/areasum)

            area_sums[group_number].append(areasum)
            energy_sums[group_number].append(energysum)
            group_profiles[group_number].append(sumprofile)

    tot_area_sums = np.sum(area_sums, axis = 1)
    tot_energy_sums = np.sum(energy_sums, axis = 1)

    tot_group_profiles = np.sum(group_profiles, axis = 1)



    results = {}

    for group_number in range(NUM_GROUPS):

        # print("GROUP = ", group_number)

        if group_number == EXISTING_EPPS_GROUP:
            efficiency = EFFICIENCY_TO_USE

        sumprofile = tot_group_profiles[group_number]

        energysum = tot_energy_sums[group_number]
        areasum = tot_area_sums[group_number]

        peakpower = areasum * BASE_IRRADIANCE * efficiency / 1000.0

        peakpower_profile = efficiency * np.max(sumprofile)

        capex_opex_increase_factor = peakpower / peakpower_profile

        pv_profile = sumprofile * efficiency

        results[group_number] = (pv_profile, capex_opex_increase_factor)

    return results






