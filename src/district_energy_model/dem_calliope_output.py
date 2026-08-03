# -*- coding: utf-8 -*-
"""Calliope 0.7 result extraction for the District Energy Model."""

from __future__ import annotations

import numpy as np


class CalliopeResults07:
    """Dimension-aware access to Calliope 0.7 result variables."""

    def __init__(self, results):
        self.results = results

    def _array(self, variable, **selectors):
        data = self.results[variable]
        valid_selectors = {
            dim: value
            for dim, value in selectors.items()
            if dim in data.dims or dim in data.coords
        }
        return data.sel(**valid_selectors)

    @staticmethod
    def _split_flow_key(key):
        node, tech, carrier = key.split("::", 2)
        return node, tech, carrier

    @staticmethod
    def _split_node_carrier_key(key):
        node, carrier = key.split("::", 1)
        return node, carrier

    def flow_out(self, node, tech, carrier):
        return self._array("flow_out", nodes=node, techs=tech, carriers=carrier).values

    def flow_in(self, node, tech, carrier):
        return self._array("flow_in", nodes=node, techs=tech, carriers=carrier).values

    def flow_export(self, node, tech, carrier):
        return self._array("flow_export", nodes=node, techs=tech, carriers=carrier).values

    def storage(self, node, tech):
        return self._array("storage", nodes=node, techs=tech).values

    def storage_cap(self, node, tech):
        return self._array("storage_cap", nodes=node, techs=tech).values

    def unmet_demand(self, node, carrier):
        return self._array("unmet_demand", nodes=node, carriers=carrier).values

    def flow_out_key(self, key):
        return self.flow_out(*self._split_flow_key(key))

    def flow_in_key(self, key):
        return self.flow_in(*self._split_flow_key(key))

    def flow_export_key(self, key):
        return self.flow_export(*self._split_flow_key(key))

    def storage_key(self, key):
        node, tech = key.split("::", 1)
        return self.storage(node, tech)

    def storage_cap_key(self, key):
        node, tech = key.split("::", 1)
        return self.storage_cap(node, tech)

    def unmet_demand_key(self, key):
        return self.unmet_demand(*self._split_node_carrier_key(key))


def _objective_function_value(opt_results):
    if "objective_function_value" not in opt_results.attrs:
        raise KeyError(
            "Calliope results are missing attrs['objective_function_value']; "
            "cannot derive total monetary costs reliably."
        )
    return float(opt_results.attrs["objective_function_value"])


def get_optimal_output_df(optimiser, opt_results):
    """
    Write the results of the Calliope optimisation to a dataframe of the same
    format as df_scen.
    
    Parameters
    ----------
    opt_results : xarray
        Results from calliope optimisation.
            
    Returns
    -------
    df_scen_opt : panda dataframe
        Dataframe with resulting hourly values.
    dict_yr_scen_opt : dictionary
        Dictionary with reulting annual values.
    dict_total_costs : dictionary
        Dictionary with resulting total costs split by type (e.g. monetary,
        co2) and energy carrier (e.g. heat, electricity).
        (incl. levelised cost)
        
        
    """
    
    # ---------------------------------------------------------------------       
    self = optimiser
    access = CalliopeResults07(opt_results)
    flow_out = access.flow_out
    flow_in = access.flow_in
    flow_export = access.flow_export
    storage = access.storage
    storage_cap = access.storage_cap
    unmet_demand = access.unmet_demand
    flow_out_key = access.flow_out_key
    flow_in_key = access.flow_in_key
    flow_export_key = access.flow_export_key
    storage_key = access.storage_key
    storage_cap_key = access.storage_cap_key
    unmet_demand_key = access.unmet_demand_key

    n_hours = len(self.energy_demand.get_d_e())
    null_array = np.array([0.0]*n_hours)

    # -------------------------------------------------------------------------
    # Virtual storage for flexibility:
    # flex_label
    if self.building_inertia_flex_flag:
        # Lists to store the values for each virtual storage (one per activated technology)
        list_u_h_vs = []
        list_v_h_vs = []
        list_q_h_vs = []
        list_sos_vs = []
        list_E_vs = []
        
        list_u_h_vs_drain = []
        list_v_h_vs_drain = []
        list_q_h_vs_drain = []
        list_sos_vs_drain = []
        
        
        # Initialise energy flows:
        u_h_vs_tot = null_array.copy()
        v_h_vs_tot = null_array.copy()
        q_h_vs_tot = null_array.copy()
        E_vs_tot = 0.0
        
        u_h_vs_drain_tot = null_array.copy()
        v_h_vs_drain_tot = null_array.copy()
        q_h_vs_drain_tot = null_array.copy()
        
        flex_systems = self.building_inertia_flex.get_flex_systems()
        
        for key, acr in flex_systems.items():
            # key: full tech name (e.g., 'heat_pump', 'district_heating')
            # acr: acronym (e.g., 'hp', 'dh')

            u_h_vs_i_ = flow_in_key(f'X1::virtual_storage_flex_{acr}::heat_vs_{acr}') * self.energy_scaling_factor
            v_h_vs_i_ = flow_out_key(f'X1::virtual_storage_flex_{acr}::heat_vs_{acr}') * self.energy_scaling_factor

            u_h_vs_drain_i = flow_in_key(f'X1::virtual_storage_drain_{acr}::heat_vs_{acr}') * self.energy_scaling_factor
            v_h_vs_drain_i = flow_out_key(f'X1::virtual_storage_drain_{acr}::heat_vs_{acr}') * self.energy_scaling_factor
            
            # Adjust charging and discharging of virtual storage based on drain:
            u_h_vs_i = u_h_vs_i_ - v_h_vs_drain_i
            v_h_vs_i = v_h_vs_i_ - u_h_vs_drain_i
            
            q_h_vs_i = storage_key(f'X1::virtual_storage_flex_{acr}') * self.energy_scaling_factor
            E_vs_i = float(storage_cap_key(f'X1::virtual_storage_flex_{acr}')) * self.energy_scaling_factor
 
            q_h_vs_drain_i = storage_key(f'X1::virtual_storage_drain_{acr}') * self.energy_scaling_factor
            E_vs_drain_i = float(storage_cap_key(f'X1::virtual_storage_drain_{acr}')) * self.energy_scaling_factor
            
            if E_vs_i > 0:
                sos_vs_i = q_h_vs_i / E_vs_i                    
            else:
                sos_vs_i = q_h_vs_i*0
                
            if E_vs_drain_i > 0:
                sos_vs_drain_i = q_h_vs_drain_i / E_vs_drain_i                    
            else:
                sos_vs_drain_i = q_h_vs_drain_i*0
                                    
            list_u_h_vs.append(u_h_vs_i)
            list_v_h_vs.append(v_h_vs_i)
            list_q_h_vs.append(q_h_vs_i)
            list_sos_vs.append(sos_vs_i)
            list_E_vs.append(E_vs_i)
            
            list_u_h_vs_drain.append(u_h_vs_drain_i)
            list_v_h_vs_drain.append(v_h_vs_drain_i)
            list_q_h_vs_drain.append(q_h_vs_drain_i)
            list_sos_vs_drain.append(sos_vs_drain_i)
                
            u_h_vs_tot += u_h_vs_i
            v_h_vs_tot += v_h_vs_i                
            q_h_vs_tot += q_h_vs_i
            E_vs_tot += E_vs_i
            
            u_h_vs_drain_tot += u_h_vs_drain_i
            v_h_vs_drain_tot += v_h_vs_drain_i                
            q_h_vs_drain_tot += q_h_vs_drain_i

        self.building_inertia_flex.update_list_u_h(list_u_h_vs)
        self.building_inertia_flex.update_list_v_h(list_v_h_vs)
        self.building_inertia_flex.update_list_q_h(list_q_h_vs)            
        self.building_inertia_flex.update_list_sos(list_sos_vs)
        self.building_inertia_flex.update_list_E_vs(list_E_vs)     
        
        self.building_inertia_flex.update_list_u_h_drain(list_u_h_vs_drain)
        self.building_inertia_flex.update_list_v_h_drain(list_v_h_vs_drain)
        self.building_inertia_flex.update_list_q_h_drain(list_q_h_vs_drain)            
        self.building_inertia_flex.update_list_sos_drain(list_sos_vs_drain)
    
    # ---------------------------------------------------------------------
    # Extract hourly values as numpy arrays:
    
    # ! CHECK NEGATIVE / POSITIVE !!!
    # ! HOW IS ADDITIONAL ELECTRICITY DEMAND HANDLED? !!!
    # ! WHAT IF TECH IS DEACTIVATED?
    
    # -------------------
    # Heat pump:
    if 'heat_pump' in self.tech_list:                    
        v_h_hp_old = flow_out_key('X1::heat_pump_old::heat_hp') * self.energy_scaling_factor
        v_h_hp_one_to_one_replacement = flow_out_key('X1::heat_pump_one_to_one_replacement::heat_hp') * self.energy_scaling_factor
        v_h_hp_new = flow_out_key('New_Techs::heat_pump_new::heat_hp') * self.energy_scaling_factor
       
        u_e_hp_old = flow_in_key('X1::heat_pump_old::electricity') * self.energy_scaling_factor
        u_e_hp_one_to_one_replacement = flow_in_key('X1::heat_pump_one_to_one_replacement::electricity') * self.energy_scaling_factor
        u_e_hp_new = flow_in_key('New_Techs::heat_pump_new::electricity') * self.energy_scaling_factor

        v_h_hp = v_h_hp_old + v_h_hp_one_to_one_replacement + v_h_hp_new
        u_e_hp = u_e_hp_old + u_e_hp_one_to_one_replacement + u_e_hp_new
        u_h_hp = v_h_hp - u_e_hp

        self.tech_heat_pump.update_v_h_u_h_u_e(v_h_hp, u_h_hp, u_e_hp)

    else:            
        u_e_hp = null_array.copy()
        u_h_hp = null_array.copy()
        v_h_hp = null_array.copy()
    

    # -------------------
    # Electric heater:
    if 'electric_heater' in self.tech_list:
        v_h_eh = flow_out_key('X1::electric_heater_old::heat') * self.energy_scaling_factor               
        self.tech_electric_heater.update_v_h(v_h_eh)
        u_e_eh = self.tech_electric_heater.get_u_e()
    else:
        u_e_eh = null_array.copy()

    # -------------------
    # Oil boiler:
    if 'oil_boiler' in self.tech_list:
        v_h_ob = (
            flow_out_key('X1::oil_boiler_old::heat') * self.energy_scaling_factor
            + flow_out_key('New_Techs::oil_boiler_new::heat') * self.energy_scaling_factor
            + flow_out_key('X1::oil_boiler_one_to_one_replacement::heat') * self.energy_scaling_factor
            )
        self.tech_oil_boiler.update_v_h(v_h_ob)
    
    # -------------------
    # Gas boiler:
    if 'gas_boiler' in self.tech_list:
        v_h_gb = (
            flow_out_key('X1::gas_boiler_old::heat') * self.energy_scaling_factor
            + flow_out_key('New_Techs::gas_boiler_new::heat') * self.energy_scaling_factor
            + flow_out_key('X1::gas_boiler_one_to_one_replacement::heat') * self.energy_scaling_factor
            )
        self.tech_gas_boiler.update_v_h(v_h_gb)

    # -------------------
    # Wood boiler:
    if 'wood_boiler' in self.tech_list:
        v_h_wb = (
            flow_out_key('X1::wood_boiler_old::heat') * self.energy_scaling_factor
            + flow_out_key('New_Techs::wood_boiler_new::heat') * self.energy_scaling_factor
            + flow_out_key('X1::wood_boiler_one_to_one_replacement::heat') * self.energy_scaling_factor
            )
        self.tech_wood_boiler.update_v_h(v_h_wb)

    # -------------------
    # District heating:
    if 'district_heating' in self.tech_list:
        
        v_h_dh = flow_out_key('X1::district_heating_hub_0::heat') * self.energy_scaling_factor
        for i in range(self.tech_district_heating.dhn_qty -1):
            v_h_dh += flow_out_key('X1::district_heating_hub_'+str(i+1)+'::heat') * self.energy_scaling_factor
        
        for i in range(self.tech_district_heating.dhn_qty):
            v_h_of_category = flow_out_key('X1::district_heating_hub_'+str(i)+'::heat') * self.energy_scaling_factor
            self.tech_district_heating.update_v_h_by_categories(v_h_of_category)
        
        self.tech_district_heating.update_v_h(v_h_dh)

        m_h_dh = flow_out_key('X1::district_heating_import::heat_dhimp') * self.energy_scaling_factor
        self.tech_district_heating.update_m_h(m_h_dh)

    # -------------------
    # Solar thermal:
    if 'solar_thermal' in self.tech_list:
        v_h_solar =\
            (
                flow_out_key('New_Techs::solar_thermal_new::heat') * self.energy_scaling_factor
                + flow_out_key('Old_Solar_Thermal::solar_thermal_old::heat') * self.energy_scaling_factor
                
                )
        self.tech_solar_thermal.update_v_h(v_h_solar)
            
    # -------------------
    # Other (unknown) sources:
    if 'other' in self.tech_list:
        v_h_other = null_array.copy()
        self.tech_other.update_v_h(v_h_other) # !!! CURRENTLY LEAVE AS IS. MUST LATER BE HANDLED DIFFERENTLY !!!

    # -------------------
    # Solar PV:
    # if 'solar_pv' in self.tech_list:
    #     if self.tech_solar_pv.get_only_use_installed():
    #         v_e_pv =\
    #             flow_out_key('Old_Solar_PV::solar_pv_old::electricity')
    #         v_e_pv_cons = (
    #             v_e_pv
    #             -flow_export_key('Old_Solar_PV::solar_pv_old::electricity')
    #             )
    #         v_e_pv_exp =\
    #             flow_export_key('Old_Solar_PV::solar_pv_old::electricity')
            
    #     else:
    #         v_e_pv = (
    #             flow_out_key('New_Techs::solar_pv_new::electricity') +
    #             flow_out_key('Old_Solar_PV::solar_pv_old::electricity')
    #             )
    #         v_e_pv_cons = (
    #             v_e_pv
    #             -flow_export_key('New_Techs::solar_pv_new::electricity')
    #             -flow_export_key('Old_Solar_PV::solar_pv_old::electricity')
    #             )
    #         v_e_pv_exp = (
    #             flow_export_key('New_Techs::solar_pv_new::electricity') + 
    #             flow_export_key('Old_Solar_PV::solar_pv_old::electricity')
    #             )
    #     if 'solar_thermal' in self.tech_list:
    #         self.tech_solar_pv.update_v_e(
    #                 v_e_updated=v_e_pv,
    #                 tech_solar_thermal=self.tech_solar_thermal,
    #                 consider_solar_thermal=True
    #                 )
    #     else:
    #         self.tech_solar_pv.update_v_e(
    #                 v_e_updated=v_e_pv,
    #                 consider_solar_thermal=False
    #                 )
            
    #     self.tech_solar_pv.update_v_e_cons(v_e_pv_cons)
    #     self.tech_solar_pv.update_v_e_exp(v_e_pv_exp)


    # -------------------
    # Solar PV rooftop:
    if 'solar_pvrooftop' in self.tech_list:

        pvrooftop_cats = self.tech_solar_pvrooftop.get_num_installations()

        if self.tech_solar_pvrooftop.get_only_use_installed():

            v_e_pvrooftop_s = [self.energy_scaling_factor*flow_out_key('solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity') 
                       for i in range(pvrooftop_cats)]

            v_e_pvrooftop_s_cons = [v_e_pvrooftop_s[i] - self.energy_scaling_factor*flow_export_key('solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity') 
                       for i in range(pvrooftop_cats)]

            v_e_pvrooftop_s_exp = [self.energy_scaling_factor*flow_export_key('solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity') 
                       for i in range(pvrooftop_cats)]
            
        else:

            v_e_pvrooftop_s = [self.energy_scaling_factor*flow_out_key('solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity') 
                       + self.energy_scaling_factor*flow_out_key('solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_unoccupied'+'::electricity')
                       for i in range(pvrooftop_cats)]

            v_e_pvrooftop_s_cons = [v_e_pvrooftop_s[i] - self.energy_scaling_factor*flow_export_key('solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity') 
                            - self.energy_scaling_factor*flow_export_key('solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_unoccupied'+'::electricity') 
                       for i in range(pvrooftop_cats)]

            v_e_pvrooftop_s_exp = [self.energy_scaling_factor*flow_export_key('solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_occupied'+'::electricity') 
                           + self.energy_scaling_factor*flow_export_key('solar_pvrooftop_installation_'+str(i)+'::solar_pvrooftop_installation_'+str(i)+'_unoccupied'+'::electricity')
                       for i in range(pvrooftop_cats)]
        
        self.tech_solar_pvrooftop.update_v_e(v_e_pvrooftop_s)
        self.tech_solar_pvrooftop.update_v_e_cons(v_e_pvrooftop_s_cons)
        self.tech_solar_pvrooftop.update_v_e_exp(v_e_pvrooftop_s_exp)

    if 'solarthermal_rooftop' in self.tech_list:

        solarthermal_rooftop_cats = self.tech_solarthermal_rooftop.get_num_installations()

        # if self.tech_solarthermal_rooftop.get_only_use_installed():

            # v_h_solarthermalrooftop_s = [flow_out_key('solarthermal_rooftop_installation_'+str(i)+'::solarthermal_rooftop_installation_'+str(i)+'_occupied'+'::heat_hp') 
            #            for i in range(solarthermal_rooftop_cats)]

            # v_h_solarthermalrooftop_s_cons = [v_h_pvrooftop_s[i] - flow_export_key('solarthermal_rooftop_installation_'+str(i)+'::solarthermal_rooftop_installation_'+str(i)+'_occupied'+'::heat_hp') 
            #            for i in range(solarthermal_rooftop_cats)]

            # v_h_solarthermalrooftop_s_exp = [flow_export_key('solarthermal_rooftop_installation_'+str(i)+'::solarthermal_rooftop_installation_'+str(i)+'_occupied'+'::heat_hp') 
            #            for i in range(solarthermal_rooftop_cats)]
            
        # else:
        if True:

            # print(opt_results['flow_out'])
            # print(type(opt_results['flow_out']))
            # exit()

            v_h_solarthermalrooftop_s = [self.energy_scaling_factor*flow_out_key('solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_occupied'+'::heat_hp') 
                       + self.energy_scaling_factor*flow_out_key('solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_unoccupied'+'::heat_hp')
                       for i in range(solarthermal_rooftop_cats)]

            v_h_solarthermalrooftop_s_cons = [v_h_solarthermalrooftop_s[i] - self.energy_scaling_factor*flow_export_key('solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_occupied'+'::heat_hp') 
                            - self.energy_scaling_factor*flow_export_key('solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_unoccupied'+'::heat_hp') 
                       for i in range(solarthermal_rooftop_cats)]

            v_h_solarthermalrooftop_s_exp = [self.energy_scaling_factor*flow_export_key('solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_occupied'+'::heat_hp') 
                           + self.energy_scaling_factor*flow_export_key('solar_pvrooftop_installation_'+str(i)+'::solar_solarthermalrooftop_installation_'+str(i)+'_unoccupied'+'::heat_hp')
                       for i in range(solarthermal_rooftop_cats)]
        
        self.tech_solarthermal_rooftop.update_v_h(v_h_solarthermalrooftop_s)
        self.tech_solarthermal_rooftop.update_v_h_cons(v_h_solarthermalrooftop_s_cons)
        self.tech_solarthermal_rooftop.update_v_h_exp(v_h_solarthermalrooftop_s_exp)   

    else:
        ...

        # self.tech_solarthermal_rooftop.update_v_h(null_array.copy())
        # self.tech_solarthermal_rooftop.update_v_h_cons(null_array.copy())
        # self.tech_solarthermal_rooftop.update_v_h_exp(null_array.copy())   

        # raise Exception("Not implemented")

    #ALPINE PV 

    if 'solar_pvalpine' in self.tech_list:

        pvalpine_cats = self.tech_solar_pvalpine.get_num_installations()

        # print(opt_results['flow_out'].coords)
        # print(opt_results['flow_out'])

        # exit()

        if self.tech_solar_pvalpine.get_only_use_installed():

            v_e_pvalpine_s = [self.energy_scaling_factor*flow_out_key('solar_pvalpine_installation_'+str(i)+'::solar_pvalpine_installation_'+str(i)+'_occupied'+'::electricity') 
                       for i in range(pvalpine_cats)]

            v_e_pvalpine_s_cons = [v_e_pvalpine_s[i] - self.energy_scaling_factor*flow_export_key('solar_pvalpine_installation_'+str(i)+'::solar_pvalpine_installation_'+str(i)+'_occupied'+'::electricity') 
                       for i in range(pvalpine_cats)]

            v_e_pvalpine_s_exp = [self.energy_scaling_factor*flow_export_key('solar_pvalpine_installation_'+str(i)+'::solar_pvalpine_installation_'+str(i)+'_occupied'+'::electricity') 
                       for i in range(pvalpine_cats)]
            
        else:

            v_e_pvalpine_s = [self.energy_scaling_factor*flow_out_key('solar_pvalpine_installation_'+str(i)+'::solar_pvalpine_installation_'+str(i)+'_occupied'+'::electricity') 
                       + self.energy_scaling_factor*flow_out_key('solar_pvalpine_installation_'+str(i)+'::solar_pvalpine_installation_'+str(i)+'_unoccupied'+'::electricity')
                       for i in range(pvalpine_cats)]

            v_e_pvalpine_s_cons = [v_e_pvalpine_s[i] - self.energy_scaling_factor*flow_export_key('solar_pvalpine_installation_'+str(i)+'::solar_pvalpine_installation_'+str(i)+'_occupied'+'::electricity') 
                            - self.energy_scaling_factor*flow_export_key('solar_pvalpine_installation_'+str(i)+'::solar_pvalpine_installation_'+str(i)+'_unoccupied'+'::electricity') 
                       for i in range(pvalpine_cats)]

            v_e_pvalpine_s_exp = [self.energy_scaling_factor*flow_export_key('solar_pvalpine_installation_'+str(i)+'::solar_pvalpine_installation_'+str(i)+'_occupied'+'::electricity') 
                           + self.energy_scaling_factor*flow_export_key('solar_pvalpine_installation_'+str(i)+'::solar_pvalpine_installation_'+str(i)+'_unoccupied'+'::electricity')
                       for i in range(pvalpine_cats)]
        
        self.tech_solar_pvalpine.update_v_e(v_e_pvalpine_s)
        self.tech_solar_pvalpine.update_v_e_cons(v_e_pvalpine_s_cons)
        self.tech_solar_pvalpine.update_v_e_exp(v_e_pvalpine_s_exp)






    # -----------
    # Wind power:
    if 'wind_power' in self.tech_list:
        v_e_wp = (
            flow_out_key('loc_wp_winter::wind_power_old::wp_electricity')*self.energy_scaling_factor
            + flow_out_key('loc_wp_winter::wind_power_new::wp_electricity')*self.energy_scaling_factor
            + flow_out_key('loc_wp_annual::wind_power_old::wp_electricity')*self.energy_scaling_factor
            + flow_out_key('loc_wp_annual::wind_power_new::wp_electricity')*self.energy_scaling_factor
            )
        v_e_wp_exp = (
            flow_export_key('loc_wp_winter::wind_power_old::wp_electricity')*self.energy_scaling_factor
            + flow_export_key('loc_wp_winter::wind_power_new::wp_electricity')*self.energy_scaling_factor
            + flow_export_key('loc_wp_annual::wind_power_old::wp_electricity')*self.energy_scaling_factor
            + flow_export_key('loc_wp_annual::wind_power_new::wp_electricity')*self.energy_scaling_factor
            )
        v_e_wp_cons = (v_e_wp - v_e_wp_exp)
        self.tech_wind_power.update_v_e(v_e_wp)
        self.tech_wind_power.update_v_e_exp(v_e_wp_exp)
        self.tech_wind_power.update_v_e_cons(v_e_wp_cons)

    #--------
    #Hydrothermal Gasification
    if 'hydrothermal_gasification' in self.tech_list:
        v_gas_hg = flow_out_key('New_Techs::hydrothermal_gasification::gas')*self.energy_scaling_factor
        self.tech_hydrothermal_gasification.update_v_gas(v_gas_hg)            
        # u_wet_bm_hg = self.tech_hydrothermal_gasification.get_u_wet_bm()
    
    else:
        v_gas_hg = null_array.copy()
        # u_wet_bm_hg = null_array.copy()
    
    #--------
    #Anaerobic Digesion Upgrade
    if 'anaerobic_digestion_upgrade' in self.tech_list:
        v_gas_agu = flow_out_key('New_Techs::anaerobic_digestion_upgrade::gas')*self.energy_scaling_factor
        self.tech_anaerobic_digestion_upgrade.update_v_gas(v_gas_agu)            
        u_wet_bm_agu = self.tech_anaerobic_digestion_upgrade.get_u_wet_bm()
    
    else:
        v_gas_agu = null_array.copy()
        u_wet_bm_agu = null_array.copy()
        
    #--------
    #Anaerobic Digestion Upgrade Hydrogen
    if 'anaerobic_digestion_upgrade_hydrogen' in self.tech_list:
        u_wet_bm_aguh = flow_in_key('New_Techs::anaerobic_digestion_upgrade_hydrogen::wet_biomass')*self.energy_scaling_factor
        u_e_aguh = flow_in_key('New_Techs::anaerobic_digestion_upgrade_hydrogen::electricity')*self.energy_scaling_factor
        u_hyd_aguh = flow_in_key('New_Techs::anaerobic_digestion_upgrade_hydrogen::hydrogen')*self.energy_scaling_factor
        v_gas_aguh = flow_out_key('New_Techs::anaerobic_digestion_upgrade_hydrogen::gas')*self.energy_scaling_factor
        v_h_aguh = flow_out_key('New_Techs::anaerobic_digestion_upgrade_hydrogen::heat_biomass')*self.energy_scaling_factor
        self.tech_anaerobic_digestion_upgrade_hydrogen.update_u_wet_bm(u_wet_bm_aguh)
        self.tech_anaerobic_digestion_upgrade_hydrogen.update_u_e(u_e_aguh)
        self.tech_anaerobic_digestion_upgrade_hydrogen.update_u_hyd(u_hyd_aguh)
        self.tech_anaerobic_digestion_upgrade_hydrogen.update_v_gas(v_gas_aguh)
        self.tech_anaerobic_digestion_upgrade_hydrogen.update_v_h(v_h_aguh)
        
    else:
        u_wet_bm_aguh = null_array.copy()
        u_e_aguh = null_array.copy()
        u_hyd_aguh = null_array.copy()
        v_gas_aguh = null_array.copy()
        v_h_aguh = null_array.copy()
    
    #--------
    #Anaerobic Digestion CHP
    if 'anaerobic_digestion_chp' in self.tech_list:
        u_wet_bm_aguc = flow_in_key('New_Techs::anaerobic_digestion_chp::wet_biomass')*self.energy_scaling_factor
        v_e_aguc = flow_out_key('New_Techs::anaerobic_digestion_chp::electricity')*self.energy_scaling_factor
        v_h_aguc = flow_out_key('New_Techs::anaerobic_digestion_chp::heat_biomass')*self.energy_scaling_factor
        v_e_aguc_exp = flow_export_key('New_Techs::anaerobic_digestion_chp::electricity')*self.energy_scaling_factor
        self.tech_anaerobic_digestion_chp.update_u_wet_bm(u_wet_bm_aguc)
        self.tech_anaerobic_digestion_chp.update_v_e(v_e_aguc)
        self.tech_anaerobic_digestion_chp.update_v_h(v_h_aguc)
        self.tech_anaerobic_digestion_chp.update_v_e_exp(v_e_aguc_exp)
        
    else:
        u_wet_bm_aguc = null_array.copy()
        v_e_aguc = null_array.copy()
        v_h_aguc = null_array.copy()
        v_e_aguc_exp = null_array.copy()
        
    #--------
    #Wood Gasification Upgrade
    if 'wood_gasification_upgrade' in self.tech_list:
        u_wd_wgu = flow_in_key('New_Techs::wood_gasification_upgrade::wood')*self.energy_scaling_factor
        u_e_wgu = flow_in_key('New_Techs::wood_gasification_upgrade::electricity')*self.energy_scaling_factor
        v_gas_wgu = flow_out_key('New_Techs::wood_gasification_upgrade::gas')*self.energy_scaling_factor
        v_h_wgu = flow_out_key('New_Techs::wood_gasification_upgrade::heat_biomass')*self.energy_scaling_factor
        self.tech_wood_gasification_upgrade.update_u_wd(u_wd_wgu)
        self.tech_wood_gasification_upgrade.update_u_e(u_e_wgu)
        self.tech_wood_gasification_upgrade.update_v_gas(v_gas_wgu)
        self.tech_wood_gasification_upgrade.update_v_h(v_h_wgu)
        
    else:
        u_wd_wgu = null_array.copy()
        u_e_wgu = null_array.copy()
        v_gas_wgu = null_array.copy()
        v_h_wgu = null_array.copy()
        
    #--------
    #Wood Gasification Upgrade Hydrogen
    if 'wood_gasification_upgrade_hydrogen' in self.tech_list:
        u_wd_wguh = flow_in_key('New_Techs::wood_gasification_upgrade_hydrogen::wood')*self.energy_scaling_factor
        u_e_wguh = flow_in_key('New_Techs::wood_gasification_upgrade_hydrogen::electricity')*self.energy_scaling_factor
        u_hyd_wguh = flow_in_key('New_Techs::wood_gasification_upgrade_hydrogen::hydrogen')*self.energy_scaling_factor
        v_gas_wguh = flow_out_key('New_Techs::wood_gasification_upgrade_hydrogen::gas')*self.energy_scaling_factor
        v_h_wguh = flow_out_key('New_Techs::wood_gasification_upgrade_hydrogen::heat_biomass')*self.energy_scaling_factor
        self.tech_wood_gasification_upgrade_hydrogen.update_u_wd(u_wd_wguh)
        self.tech_wood_gasification_upgrade_hydrogen.update_u_e(u_e_wguh)
        self.tech_wood_gasification_upgrade_hydrogen.update_u_hyd(u_hyd_wguh)
        self.tech_wood_gasification_upgrade_hydrogen.update_v_gas(v_gas_wguh)
        self.tech_wood_gasification_upgrade_hydrogen.update_v_h(v_h_wguh)
        
    else:
        u_wd_wguh = null_array.copy()
        u_e_wguh = null_array.copy()
        u_hyd_wguh = null_array.copy()
        v_gas_wguh = null_array.copy()
        v_h_wguh = null_array.copy()
        
    #--------
    #Wood Gasification CHP
    if 'wood_gasification_chp' in self.tech_list:
        u_wd_wguc = flow_in_key('New_Techs::wood_gasification_chp::wood')*self.energy_scaling_factor
        v_e_wguc = flow_out_key('New_Techs::wood_gasification_chp::electricity')*self.energy_scaling_factor
        v_h_wguc = flow_out_key('New_Techs::wood_gasification_chp::heat_biomass')*self.energy_scaling_factor
        v_e_wguc_exp = flow_export_key('New_Techs::wood_gasification_chp::electricity')*self.energy_scaling_factor
        self.tech_wood_gasification_chp.update_u_wd(u_wd_wguc)
        self.tech_wood_gasification_chp.update_v_e(v_e_wguc)
        self.tech_wood_gasification_chp.update_v_h(v_h_wguc)
        self.tech_wood_gasification_chp.update_v_e_exp(v_e_wguc_exp)
        
    else:
        u_wd_wguc = null_array.copy()
        v_e_wguc = null_array.copy()
        v_h_wguc = null_array.copy()
        v_e_wguc_exp = null_array.copy()
        
    #--------
    #Hydrogen Production
    if 'hydrogen_production' in self.tech_list:
        v_hyd_hydp = flow_out_key('New_Techs::hydrogen_production::hydrogen')*self.energy_scaling_factor
        self.tech_hydrogen_production.update_v_hyd(v_hyd_hydp)
        u_e_hydp = self.tech_hydrogen_production.get_u_e()
    else:
        v_hyd_hydp = null_array.copy()
        u_e_hydp = null_array.copy()
        
    #------------------
    # Biomass Totals
    if 'biomass' in self.tech_list:
        v_e_bm = v_e_aguc + v_e_wguc
        v_e_bm_exp = v_e_aguc_exp + v_e_wguc_exp
        v_e_bm_cons = v_e_bm - v_e_bm_exp
        v_h_bm = v_h_aguh + v_h_aguc + v_h_wgu + v_h_wguh + v_h_wguc
        self.tech_biomass.update_v_e(v_e_bm)
        self.tech_biomass.update_v_e_exp(v_e_bm_exp)
        self.tech_biomass.update_v_e_cons(v_e_bm_cons)
        self.tech_biomass.update_v_h(v_h_bm)

    #------------------
    # Biomass Supply
    s_wet_bm_prev = self.supply.get_s_wet_bm()
    s_wd_prev = self.supply.get_s_wd()

    s_wet_bm_rem = (
        s_wet_bm_prev
        - flow_out_key('Limited_Supplies::wet_biomass_supply::wet_biomass')*self.energy_scaling_factor
        )

    s_wd_rem = (
        s_wd_prev
        - flow_out_key('Limited_Supplies::wood_supply::wood')*self.energy_scaling_factor
        )

    s_wet_bm = flow_out_key('Limited_Supplies::wet_biomass_supply::wet_biomass')*self.energy_scaling_factor
    s_wd = flow_out_key('Limited_Supplies::wood_supply::wood')*self.energy_scaling_factor        
    self.supply.update_s_wet_bm(s_wet_bm)
    self.supply.update_s_wd(s_wd)
    self.supply.update_s_wet_bm_rem(s_wet_bm_rem)
    self.supply.update_s_wd_rem(s_wd_rem)
    
    # ------------------- 
    # Hydro Power (local):
    if 'hydro_power' in self.tech_list:
        v_e_hydro = (
            flow_out_key('X1::hydro_power::electricity')*self.energy_scaling_factor
            )
        v_e_hydro_cons = (
            v_e_hydro
            -flow_export_key('X1::hydro_power::electricity')*self.energy_scaling_factor
            )
        v_e_hydro_exp = (
            flow_export_key('X1::hydro_power::electricity')*self.energy_scaling_factor
            )
        self.tech_hydro_power.update_v_e(v_e_hydro)
        self.tech_hydro_power.update_v_e_cons(v_e_hydro_cons)
        self.tech_hydro_power.update_v_e_exp(v_e_hydro_exp)
        
    # -------------------
    # CHP gas turbine:
    if 'chp_gt' in self.tech_list:
        v_e_chp_gt = flow_out_key('X1::chp_gt_new::electricity')*self.energy_scaling_factor
        v_h_chp_gt = flow_out_key('X1::chp_gt_new::heat_chpgt')*self.energy_scaling_factor
        v_h_chp_gt_waste = flow_export_key('X1::chp_gt_new::heat_chpgt')*self.energy_scaling_factor
        v_h_chp_gt_con = v_h_chp_gt - v_h_chp_gt_waste
        
        self.tech_chp_gt.update_v_e(v_e_chp_gt)
        self.tech_chp_gt.update_v_h(v_h_chp_gt)
        self.tech_chp_gt.update_v_h_waste(v_h_chp_gt_waste)
        self.tech_chp_gt.update_v_h_con(v_h_chp_gt_con)

        if self.tech_chp_gt.get_deploy_existing():
            # TO BE IMPLEMENTED
            raise Exception("Existing CHP plants not yet implemented in Calliope get_optimal_output_df()!")
            
    # -------------------
    # Gas turbine (central plant):
    if 'gas_turbine_cp' in self.tech_list:
        v_e_gtcp = flow_out_key('X1::gas_turbine_cp_exist::electricity')*self.energy_scaling_factor
        v_steam_gtcp = flow_out_key('X1::gas_turbine_cp_exist::steam')*self.energy_scaling_factor
        v_steam_gtcp_surp = flow_export_key('X1::gas_turbine_cp_exist::steam')*self.energy_scaling_factor
        v_steam_gtcp_con = v_steam_gtcp - v_steam_gtcp_surp
        self.tech_gas_turbine_cp.update_v_e(v_e_gtcp)
        self.tech_gas_turbine_cp.update_v_steam(v_steam_gtcp)
        self.tech_gas_turbine_cp.update_v_steam_surp(v_steam_gtcp_surp)
        self.tech_gas_turbine_cp.update_v_steam_con(v_steam_gtcp_con)
        
    # -------------------
    # Wood boiler (steam generator):
    if 'wood_boiler_sg' in self.tech_list:
        v_steam_wbsg = flow_out_key('X1::wood_boiler_sg_exist::steam')*self.energy_scaling_factor
        self.tech_wood_boiler_sg.update_v_steam(v_steam_wbsg)
        
    # -------------------
    # Steam turbine:
    if 'steam_turbine' in self.tech_list:
        v_e_st = flow_out_key('X1::steam_turbine_exist::electricity')*self.energy_scaling_factor
        v_h_st = flow_out_key('X1::steam_turbine_exist::heat_st')*self.energy_scaling_factor
        v_h_st_waste = flow_export_key('X1::steam_turbine_exist::heat_st')*self.energy_scaling_factor
        v_h_st_con = v_h_st - v_h_st_waste

        self.tech_steam_turbine.update_v_e(v_e_st)
        self.tech_steam_turbine.update_v_h(v_h_st)
        self.tech_steam_turbine.update_v_h_waste(v_h_st_waste)
        self.tech_steam_turbine.update_v_h_con(v_h_st_con)



        if 'gas_turbine_cp' in self.tech_list:
            self.tech_steam_turbine.compute_v_e_gtcp(self.tech_gas_turbine_cp)
            self.tech_steam_turbine.compute_v_h_gtcp(self.tech_gas_turbine_cp)
        if 'wood_boiler_sg' in self.tech_list:
            self.tech_steam_turbine.compute_v_e_wbsg(self.tech_wood_boiler_sg)
            self.tech_steam_turbine.compute_v_h_wbsg(self.tech_wood_boiler_sg)
        
    # -------------------
    # Waste-to-energy plant:
    if 'waste_to_energy' in self.tech_list:
        v_e_wte = flow_out_key('X1::waste_to_energy_exist::electricity')*self.energy_scaling_factor
        v_h_wte = flow_out_key('X1::waste_to_energy_exist::heat_wte')*self.energy_scaling_factor
        v_h_wte_waste = flow_export_key('X1::waste_to_energy_exist::heat_wte')*self.energy_scaling_factor
        v_h_wte_con = v_h_wte - v_h_wte_waste
        
        self.tech_waste_to_energy.update_v_e(v_e_wte)
        self.tech_waste_to_energy.update_v_h(v_h_wte)
        self.tech_waste_to_energy.update_v_h_waste(v_h_wte_waste)
        self.tech_waste_to_energy.update_v_h_con(v_h_wte_con)


    # -------------------
    # Heat pump (central plant):
    if 'heat_pump_cp' in self.tech_list:
        v_h_hpcp = flow_out_key('X1::heat_pump_cp_exist::heat_hpcp')*self.energy_scaling_factor
        self.tech_heat_pump_cp.update_v_h(v_h_hpcp)
        u_e_hpcp = self.tech_heat_pump_cp.get_u_e()
    
    else:            
        u_e_hpcp = null_array.copy()

    # -------------------
    # Heat pump (central plant, from low temperature heat):
    if 'heat_pump_cp_lt' in self.tech_list:
        v_h_hpcplt = flow_out_key('X1::heat_pump_cp_lt_exist::heat_hpcplt')*self.energy_scaling_factor
        self.tech_heat_pump_cp_lt.update_v_h(v_h_hpcplt)
        u_e_hpcplt = self.tech_heat_pump_cp_lt.get_u_e()

    else:            
        u_e_hpcplt = null_array.copy()

    # -------------------
    # Oil boiler (central plant):
    if 'oil_boiler_cp' in self.tech_list:
        v_h_obcp = flow_out_key('X1::oil_boiler_cp_exist::heat_obcp')*self.energy_scaling_factor
        self.tech_oil_boiler_cp.update_v_h(v_h_obcp)
        # u_oil_obcp = self.tech_oil_boiler_cp.get_u_oil()
    
    # else:            
        # u_oil_obcp = null_array.copy()

    # -------------------
    # Electric heater (central plant):
    if 'electric_heater_cp' in self.tech_list:
        v_h_ehcp = flow_out_key('X1::electric_heater_cp_exist::heat_ehcp')*self.energy_scaling_factor
        self.tech_electric_heater_cp.update_v_h(v_h_ehcp)
        u_e_ehcp = self.tech_electric_heater_cp.get_u_e()
    else:
        u_e_ehcp = null_array.copy()

    # -------------------
    # Wood boiler (central plant):
    if 'wood_boiler_cp' in self.tech_list:
        v_h_wbcp = flow_out_key('X1::wood_boiler_cp_exist::heat_wbcp')*self.energy_scaling_factor
        self.tech_wood_boiler_cp.update_v_h(v_h_wbcp)

    # -------------------
    # Deep_Geothermal
    if 'deep_geothermal' in self.tech_list:

        v_h_dgt = flow_out_key('X1::deep_geothermal_exists::heat_dgt')*self.energy_scaling_factor
        self.tech_deep_geothermal.update_v_h(v_h_dgt)

    # -------------------
    # Heat_demand_manual
    if 'heat_demand_manual' in self.tech_list:

        d_h_m = flow_in_key('X1::heat_demand_manual_exists::heat')*self.energy_scaling_factor
        self.tech_heat_demand_manual.update_d_h(d_h_m)

    # -------------------
    # Waste_heat
    if 'waste_heat' in self.tech_list:
        # rasa = flow_out_key('X1::waste_heat_exists')
        # print(rasa)
        # exit()

        v_h_wh = flow_out_key('X1::waste_heat_exists::heat_wh')*self.energy_scaling_factor
        self.tech_waste_heat.update_v_h(v_h_wh)

    # -------------------
    # Waste_heat_low_temperature
    if 'waste_heat_low_temperature' in self.tech_list:

        v_hlt_whlt = flow_out_key('X1::waste_heat_low_temperature_exists::heatlt')*self.energy_scaling_factor
        self.tech_waste_heat_low_temperature.update_v_hlt(v_hlt_whlt)
        
    # -------------------
    # Gas boiler (central plant):
    if 'gas_boiler_cp' in self.tech_list:
        v_h_gbcp = flow_out_key('X1::gas_boiler_cp_exist::heat_gbcp')*self.energy_scaling_factor
        self.tech_gas_boiler_cp.update_v_h(v_h_gbcp)

    # -------------------
    # Resources import:
    m_oil = (
        flow_out_key('New_Techs::oil_supply::oil')*self.energy_scaling_factor
        + flow_out_key('X1::oil_supply::oil')*self.energy_scaling_factor
        )
    m_gas = (
        flow_out_key('New_Techs::gas_supply::gas')*self.energy_scaling_factor
        + flow_out_key('X1::gas_supply::gas')*self.energy_scaling_factor
        )
    m_wd = (
        flow_out_key('New_Techs::wood_supply_import::wood')*self.energy_scaling_factor
        + flow_out_key('X1::wood_supply_import::wood')*self.energy_scaling_factor
        )
    self.supply.update_m_oil(m_oil)
    self.supply.update_m_gas(m_gas)
    self.supply.update_m_wd(m_wd)
    

    # -------------------
    # Demand:

    if (
            self.scen_techs['scenarios']['demand_side']
            and self.scen_techs['demand_side']['ev_integration']
            and self.scen_techs['demand_side']['ev_flexibility']
            ):
        
        d_e_ev = (
            flow_in_key('X1::demand_electricity_ev_pd::electricity')*self.energy_scaling_factor
            + flow_in_key('X1::demand_electricity_ev_delta::electricity')*self.energy_scaling_factor
            )
        # tmp_dict = {
        #     'd_e_ev_pd':flow_in_key('X1::demand_electricity_ev_pd::electricity'),
        #     'd_e_ev_delta':flow_in_key('X1::demand_electricity_ev_delta::electricity'),
        #     'd_e_ev':d_e_ev,
        #     'd_e_ev_cp':self.energy_demand.get_d_e_ev_cp(),
        #     'flexibility_ev':flow_out_key('X1::flexibility_ev::flexible_electricity'),
        #     }
        # tmp_df_ev = pd.DataFrame(tmp_dict)
        # tmp_df_ev.to_csv('tmp_results_for_testing/df_d_e_ev.csv')
    else:
        d_e_ev = flow_in_key('X1::demand_electricity_ev::electricity')*self.energy_scaling_factor
    
    d_e = (
        flow_in_key('X1::demand_electricity_baseline::electricity')*self.energy_scaling_factor
        # flow_in_key('X1::demand_electricity_ev::electricity')
        + d_e_ev
        + u_e_hp
        + u_e_eh
        + u_e_ehcp
        + u_e_hpcp
        + u_e_hpcplt
        + u_e_aguh
        + u_e_wgu
        + u_e_wguh
        + u_e_hydp
        )         
    d_e_baseline = (
        flow_in_key('X1::demand_electricity_baseline::electricity')*self.energy_scaling_factor
        )        
    d_e_h = u_e_hp + u_e_eh + u_e_hpcp + u_e_hpcplt + u_e_ehcp

    # flex_label
    if self.building_inertia_flex_flag:
        d_h = self.energy_demand.get_d_h()
        losses = np.zeros(len(d_h)) # losses of virtual storages (are part of heat demand)
        flex_systems = self.building_inertia_flex.get_flex_systems()
        for i, (key, acr) in enumerate(flex_systems.items()):
            # key: full tech name (e.g., 'heat_pump')
            # acr: acronym (e.g., 'hp' for heat pump)
            losses = losses + self.building_inertia_flex.get_list_l_q_h()[i]

        d_h_flex = (
            flow_in_key('X1::demand_heat::heat')*self.energy_scaling_factor
            + losses
            )

    else:
        d_h = flow_in_key('X1::demand_heat::heat')*self.energy_scaling_factor
        d_h_flex = d_h
    
    self.energy_demand.update_d_e(d_e)
    self.energy_demand.update_d_e_baseline(d_e_baseline)
    self.energy_demand.update_d_e_h(d_e_h)
    self.energy_demand.update_d_e_ev(d_e_ev)
    self.energy_demand.update_d_h(d_h)
    self.energy_demand.update_d_h_flex(d_h_flex)
    
    # Unmet demand:

    d_e_unmet = (
        unmet_demand_key('X1::electricity')*self.energy_scaling_factor
        + unmet_demand_key('New_Techs::electricity')*self.energy_scaling_factor
        )
        
    d_h_unmet = (
        unmet_demand_key('X1::heat')*self.energy_scaling_factor
        # + unmet_demand_key('X1::heat_tes')
        + unmet_demand_key('New_Techs::heat')*self.energy_scaling_factor
        )
    
    if 'heat_pump' in self.tech_list:
        d_h_unmet += (
            unmet_demand_key('X1::heat_hp')*self.energy_scaling_factor
            + unmet_demand_key('New_Techs::heat_hp')*self.energy_scaling_factor
            # + unmet_demand_key('loc_wp_annual::heat_hp')*self.energy_scaling_factor
            # + unmet_demand_key('loc_wp_winter::heat_hp')*self.energy_scaling_factor
            + unmet_demand_key('solar_pvrooftop_installation_0::heat_hp')*self.energy_scaling_factor
            + unmet_demand_key('solar_pvrooftop_installation_1::heat_hp')*self.energy_scaling_factor
            + unmet_demand_key('solar_pvrooftop_installation_2::heat_hp')*self.energy_scaling_factor
            + unmet_demand_key('solar_pvrooftop_installation_3::heat_hp')*self.energy_scaling_factor
            )
    
        if 'wind_power' in self.tech_list:
            d_h_unmet += (
                + unmet_demand_key('loc_wp_annual::heat_hp')*self.energy_scaling_factor
                + unmet_demand_key('loc_wp_winter::heat_hp')*self.energy_scaling_factor
                )
    
    d_h_unmet_dhn = np.array([0.0]*len(d_h_unmet))
    
    if 'district_heating' in self.tech_list:
        d_h_unmet_dhn += (
            unmet_demand_key('X1::heat_dh')*self.energy_scaling_factor
            + unmet_demand_key('X1::heat_dhimp')*self.energy_scaling_factor
            )
    
    if 'steam_turbine' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_st')*self.energy_scaling_factor
        
    if 'tes' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_tes')*self.energy_scaling_factor

    if 'tes_sites' in self.tech_list:

        for loc in self.tech_tes_sites.get_list_of_sitekeys():
            for x in loc:
                if x.endswith("ht"):
                    d_h_unmet_dhn += unmet_demand_key('X1::heat_'+x)*self.energy_scaling_factor

    if 'waste_to_energy' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_wte')*self.energy_scaling_factor
        
    if 'heat_pump_cp' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_hpcp')*self.energy_scaling_factor

    if 'heat_pump_cp_lt' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_hpcplt')*self.energy_scaling_factor

    if 'oil_boiler_cp' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_obcp')*self.energy_scaling_factor

    if 'electric_heater_cp' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_ehcp')*self.energy_scaling_factor

    if 'wood_boiler_cp' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_wbcp')*self.energy_scaling_factor

    if 'waste_heat' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_wh')*self.energy_scaling_factor

    if 'deep_geothermal' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_dgt')*self.energy_scaling_factor

    if 'gas_boiler_cp' in self.tech_list:
        d_h_unmet_dhn += unmet_demand_key('X1::heat_gbcp')*self.energy_scaling_factor

    self.energy_demand.update_d_e_unmet(d_e_unmet)
    self.energy_demand.update_d_h_unmet(d_h_unmet)
    self.energy_demand.update_d_h_unmet_dhn(d_h_unmet_dhn)

    # -------------------
    # Electricity import:
    if 'grid_supply' in self.tech_list:
        m_e =\
            flow_out_key('Grid_Connection_Node::grid_supply::electricity')*self.energy_scaling_factor
            
        # Recalculate electricity mix:
        self.tech_grid_supply.update_m_e(m_e)

    if 'grid_export' in self.tech_list:
        f_e =\
            flow_in_key('Grid_Connection_Node::grid_export::electricity')*self.energy_scaling_factor
            
        # Recalculate electricity mix:
        self.tech_grid_export.update_f_e(f_e)

    # -------------------
    # Thermal energy storage: # LOSSES TO BE ADDED
    if 'tes' in self.tech_list:
        v_h_tes = flow_out_key('X1::tes::heat_tes')*self.energy_scaling_factor
        u_h_tes = flow_in_key('X1::tes::heat_tes')*self.energy_scaling_factor
        q_h_tes = storage_key('X1::tes')*self.energy_scaling_factor
        cap_tes = float(storage_cap_key('X1::tes')*self.energy_scaling_factor)

        self.tech_tes.update_v_h(v_h_tes)
        self.tech_tes.update_u_h(u_h_tes)
        self.tech_tes.update_q_h(q_h_tes)
        if cap_tes > 0:
            self.tech_tes.update_sos(q_h_tes / cap_tes)
        else:
            self.tech_tes.update_sos(q_h_tes *0)
        self.tech_tes.update_cap(cap_tes)

# -------------------
    # Thermal energy storage sites: # LOSSES TO BE ADDED
    if 'tes_sites' in self.tech_list:

        list_of_sitekeys = self.tech_tes_sites.get_list_of_sitekeys()
        sites_list = self.tech_tes_sites.get_sites_list()


        for site_indexval in range(len(list_of_sitekeys)):
            sitekeys = list_of_sitekeys[site_indexval]
            for subsite in sitekeys:
                t = subsite.split("_")[-1]

                v_h_tessite = flow_out_key('X1::'+subsite+'::heat_'+subsite)*self.energy_scaling_factor
                u_h_tessite = flow_in_key('X1::'+subsite+'::heat_'+subsite)*self.energy_scaling_factor
                q_h_tessite = storage_key('X1::'+subsite)*self.energy_scaling_factor

                cap_tessite = float(storage_cap_key('X1::'+subsite)*self.energy_scaling_factor)

                

                self.tech_tes_sites.set_u_h_site_type(u_h_tessite, site_indexval, t)
                self.tech_tes_sites.set_v_h_site_type(v_h_tessite, site_indexval, t)
                self.tech_tes_sites.set_q_h_site_type(q_h_tessite, site_indexval, t)

                self.tech_tes_sites.set_cap_site_type(cap_tessite, site_indexval, t)
                if subsite[-4:] == 'ltlt':

                    name = sites_list[site_indexval]['name']
                    u_hht_to_hlt = (flow_out_key('X1::conv_'+name+'_htht_to_'+name+'_ltlt::heat_'+subsite)*self.energy_scaling_factor
                     +flow_out_key('X1::conv_'+name+'_htlt_to_'+name+'_ltlt::heat_'+subsite)*self.energy_scaling_factor)
                    self.tech_tes_sites.set_u_hht_to_hlt(
                        u_hht_to_hlt+self.tech_tes_sites.get_u_hht_to_hlt(site_indexval)
                        , site_indexval)
                if subsite[-4:] == 'htlt':
                    name = sites_list[site_indexval]['name']
                    
                    u_hht_to_hlt = flow_out_key('X1::conv_'+name+'_lt_to_'+'heatlt_htlt::heatlt')*self.energy_scaling_factor-v_h_tessite
                    self.tech_tes_sites.set_u_hht_to_hlt(
                        u_hht_to_hlt+self.tech_tes_sites.get_u_hht_to_hlt(site_indexval)
                        , site_indexval)



                self.tech_tes_sites.update_soc_site_type(site_indexval, t)
                self.tech_tes_sites.update_losses_site_type(site_indexval, t)


    # -------------------
    # Thermal energy storage - decentralised: # LOSSES TO BE ADDED
    if 'tes_decentralised' in self.tech_list:
        v_h_tesdc = flow_out_key('X1::tes_decentralised::heat_tesdc')*self.energy_scaling_factor
        u_h_tesdc = flow_in_key('X1::tes_decentralised::heat_tesdc')*self.energy_scaling_factor
        q_h_tesdc = storage_key('X1::tes_decentralised')*self.energy_scaling_factor
        cap_tesdc = float(storage_cap_key('X1::tes_decentralised')*self.energy_scaling_factor)

        self.tech_tes_decentralised.update_v_h(v_h_tesdc)
        self.tech_tes_decentralised.update_u_h(u_h_tesdc)
        self.tech_tes_decentralised.update_q_h(q_h_tesdc)
        if cap_tesdc > 0:
            self.tech_tes_decentralised.update_sos(q_h_tesdc / cap_tesdc)
        else:
            self.tech_tes_decentralised.update_sos(q_h_tesdc * 0)
        self.tech_tes_decentralised.update_cap(cap_tesdc)
    # -------------------
    # Battery energy storage:
    if 'bes' in self.tech_list:
        v_e_bes = flow_out_key('X1::bes::electricity')*self.energy_scaling_factor
        u_e_bes = flow_in_key('X1::bes::electricity')*self.energy_scaling_factor
        q_e_bes = storage_key('X1::bes')*self.energy_scaling_factor
        cap_bes = float(storage_cap_key('X1::bes')*self.energy_scaling_factor)

        self.tech_bes.update_v_e(v_e_bes)
        self.tech_bes.update_u_e(u_e_bes)
        self.tech_bes.update_q_e(q_e_bes)
        if cap_bes > 0:
            self.tech_bes.update_sos(q_e_bes / cap_bes)
        else:
            self.tech_bes.update_sos(q_e_bes *0)
        self.tech_bes.update_cap(cap_bes)

    # -------------------
    # Gas tank energy storage:
    if 'gtes' in self.tech_list:
        v_gas_gtes = flow_out_key('X1::gtes::gas')*self.energy_scaling_factor
        u_gas_gtes = flow_in_key('X1::gtes::gas')*self.energy_scaling_factor
        q_gas_gtes = storage_key('X1::gtes')*self.energy_scaling_factor
        cap_gtes = float(storage_cap_key('X1::gtes')*self.energy_scaling_factor)

        self.tech_gtes.update_v_gas(v_gas_gtes)
        self.tech_gtes.update_u_gas(u_gas_gtes)
        self.tech_gtes.update_q_gas(q_gas_gtes)
        if cap_gtes > 0:
            self.tech_gtes.update_sos(q_gas_gtes / cap_gtes)
        else:
            self.tech_gtes.update_sos(q_gas_gtes * 0)
        self.tech_gtes.update_cap(cap_gtes)

    # -------------------
    # Wood storage:
    if 'ws' in self.tech_list:
        v_wd_ws = flow_out_key('X1::ws::wood')*self.energy_scaling_factor
        u_wd_ws = flow_in_key('X1::ws::wood')*self.energy_scaling_factor
        q_wd_ws = storage_key('X1::ws')*self.energy_scaling_factor
        cap_ws = float(storage_cap_key('X1::ws')*self.energy_scaling_factor)

        self.tech_ws.update_v_wd(v_wd_ws)
        self.tech_ws.update_u_wd(u_wd_ws)
        self.tech_ws.update_q_wd(q_wd_ws)
        if cap_ws > 0:
            self.tech_ws.update_sos(q_wd_ws / cap_ws)
        else:
            self.tech_ws.update_sos(q_wd_ws * 0)
        self.tech_ws.update_cap(cap_ws)


    # -------------------
    # Hydrogen energy storage:
    if 'hes' in self.tech_list:

        # print(opt_results['flow_out'])
        # exit()

        v_hyd_hes = flow_out_key('New_Techs::hes::hydrogen')*self.energy_scaling_factor
        u_hyd_hes = flow_in_key('New_Techs::hes::hydrogen')*self.energy_scaling_factor
        q_hyd_hes = storage_key('New_Techs::hes')*self.energy_scaling_factor
        cap_hes = float(storage_cap_key('New_Techs::hes')*self.energy_scaling_factor)

        self.tech_hes.update_v_hyd(v_hyd_hes)
        self.tech_hes.update_u_hyd(u_hyd_hes)
        self.tech_hes.update_q_hyd(q_hyd_hes)
        if cap_hes > 0:
            self.tech_hes.update_sos(q_hyd_hes / cap_hes)
        else:
            self.tech_hes.update_sos(q_hyd_hes *0)

        self.tech_hes.update_cap(cap_hes)

    # -------------------------------------------------------------------------
    # Extract costs:
    
    objective_monetary = self.scen_techs['optimisation']['objective_monetary']
    objective_co2 = self.scen_techs['optimisation']['objective_co2']
    objective_ess = self.scen_techs['optimisation']['objective_ess']
    objective_tss = self.scen_techs['optimisation']['objective_tss']

    if objective_ess > 0 or objective_tss > 0:
        raise ValueError("objective_ess or objective_tss > 0: Not yet implemented.")

    if objective_monetary == 0:
        raise RuntimeWarning("objective_monetary set to 0. This leads to unreasonable results and makes it impossible to reliably determine total costs.")
    

    dict_total_costs = {}
    dict_total_costs['monetary'] = {}
    dict_total_costs['co2'] = {}
    dict_total_costs['objective'] = {}
    
    tmp_tlc = opt_results['total_levelised_cost'] # array; total levelised costs
    
    dict_total_costs['monetary']['electricity_tlc'] =\
        float(tmp_tlc.sel(carriers='electricity', costs='monetary').values)
    dict_total_costs['monetary']['heat_tlc'] =\
        float(tmp_tlc.sel(carriers='heat', costs='monetary').values)
    dict_total_costs['monetary']['total'] =\
        float(opt_results['cost'].sel(costs='monetary').values.sum())
        
    dict_total_costs['co2']['electricity_tlc'] =\
        float(tmp_tlc.sel(carriers='electricity', costs='emissions_co2').values)
    dict_total_costs['co2']['heat_tlc'] =\
        float(tmp_tlc.sel(carriers='heat', costs='emissions_co2').values)
    dict_total_costs['co2']['total'] =\
        float(opt_results['cost'].sel(costs='emissions_co2').values.sum())

    dict_total_costs['objective']['total'] =\
        _objective_function_value(opt_results)

    if objective_monetary > 0:
        dict_total_costs['monetary']['total'] =\
            (dict_total_costs['objective']['total'] - objective_co2*dict_total_costs['co2']['total'])/objective_monetary

    return dict_total_costs

