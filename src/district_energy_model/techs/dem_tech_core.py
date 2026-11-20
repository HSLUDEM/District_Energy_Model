# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 12:50:32 2024

@author: UeliSchilt
"""

"Parent class for tech classes."
import numpy as np
import warnings

class TechCore():
    
    @staticmethod
    def check_hourly_timeseries(values, n_hours, description):
        """
        Check an hourly input time series: it must cover the simulated
        period (n_hours) and contain no missing or negative values.
        """
        values = np.asarray(values, dtype=float)
        if len(values) < n_hours:
            raise ValueError(
                f"{description}: the time series has {len(values)} values, "
                f"but the simulated period has {n_hours} hours."
                )
        values = values[:n_hours]
        if not np.all(np.isfinite(values)):
            i = int(np.argmax(~np.isfinite(values)))
            raise ValueError(
                f"{description}: the time series contains missing or "
                f"non-finite values (first in hour {i})."
                )
        if np.any(values < 0.0):
            i = int(np.argmax(values < 0.0))
            raise ValueError(
                f"{description}: the time series contains negative values "
                f"(first in hour {i}: {values[i]})."
                )
        return values
    
    def __init__(self, tech_dict):
        
        """
        Initialise technology parameters.
        
        Parameters
        ----------
            
        tech_dict : dict
            Dictionary with technology parameters (subset of scen_techs).
    
        Returns
        -------
        n/a
        """
        
        # Initialize properties:
        # self.update_tech_properties(tech_dict)
        
        # Carrier types:
        # --> to be implemented in child classes
        
        # Accounting:
        # --> to be implemented in child classes
        
    def update_tech_properties(self, tech_dict):
        """
        Updates the technology properties based on a new tech_dict.
        
        Parameters
        ----------
        tech_dict : dict
            Dictionary with updated technology parameters.

        Returns
        -------
        None
        """
        
        # Update tech dict:
        self.__tech_dict = tech_dict
        
        # Tests:
        # --> To be implemented in child classes
        
        # Properties:
        # --> To be implemented in child classes


    def update_df_results(self, df):
        
        ...
        
        # --> To be implemented in child class
        
        return df
    
    def len_test(self,flow):
        if len(flow)==0:
            raise ValueError()
            
    def num_test(self,var):
        if isinstance(var, (int, float, np.integer))==False:
            raise ValueError()
            
    # def num_test_inf(self, var):
    #     if not (isinstance(var, (int, float, np.integer)) or np.isinf(var)):
    #         raise ValueError("var must be numeric or inf")
    
    def num_test_inf(self, var):
        if isinstance(var, str) and var.lower() in ('inf', '-inf'):
            return  # allow string forms of infinity
        if not (isinstance(var, (int, float, np.integer)) or np.isinf(var)):
            raise ValueError("var must be numeric or inf")

            
    def get_maintenance_cost(self): #per unit kW oder kWh, depending on the technology
        return self._maintenance_cost*sum([(1.0/((1+self._interest_rate)**(i+1))) for i in range(self._lifetime)])
    
    
    def get_energy_costs(self):
        return 0
        # --> To be implemented in child class

    def get_energy_revenue(self):
        return 0
        # --> To be implemented in child class

    def set_cost_basis(self, optimisation):
        """
        Set by the cost module before it reads the costs of this technology.
        optimisation=True: the costs of an optimisation result; maximum
        capacities (e.g. capacity_kWh_max of storages, updated to the optimised
        capacity) and forced capacities (force_cap_max) are built capacities.
        optimisation=False (simulation): only operated capacity causes capex
        and maintenance; maxima are limits of the optimisation only. Forced
        capacities (force_cap_max) are deployed by the user and cost in full
        in simulations too.
        """
        self._costs_from_optimisation = bool(optimisation)

    def costs_from_optimisation(self):
        # Default (cost basis not set): as an optimisation, i.e. the former behaviour.
        return getattr(self, '_costs_from_optimisation', True)

    def _cap_is_built(self):
        # Finite capacity _cap (e.g. capacity_kWh_max of storages) costed in full: in optimisations
        # (optimised capacity) and, if forced (force_cap_max), also in simulations.
        return (hasattr(self, '_cap') and self._cap != 'inf'
                and (self.costs_from_optimisation() or bool(getattr(self, '_force_cap_max', False))))

    def get_total_capex(self):
        if not hasattr(self, "_capex"):
            return 0

        if self._cap_is_built():
            # Never negative (as in the branch below), e.g. if the existing
            # capacity were ever larger than the selected capacity:
            return self._capex*(0.0, self.get_cap() - self.existing)

        if hasattr(self, "_capex_one_to_one_replacement"):
            total_capacity = self.get_output().max()
            if total_capacity <= self.existing:
                return 0
            elif total_capacity <= self.needs_replacement + self.existing:
                return self._capex_one_to_one_replacement*(total_capacity - self.existing)
            else:
                new_capex = self._capex*(self.get_output().max() - self.existing - self.needs_replacement)
                replacement_capex = self._capex_one_to_one_replacement*self.needs_replacement
                return replacement_capex + new_capex
        else: 
            new_capex = self._capex*(self.get_installed_cap() - self.existing)
            if new_capex < 0:
                new_capex = 0
            total_capex = new_capex
        return total_capex
    
    def get_total_maintenance(self):
        if not hasattr(self, "_maintenance_cost"):
            return 0
        if self._cap_is_built():
            return self._maintenance_cost*self.get_cap()
        if hasattr(self, '_maintenance_cost'):
            return self._maintenance_cost*self.get_installed_cap()
        elif hasattr(self, 'maintenance_cost'):
            return self.maintenance_cost*self.get_output().max()

    def set_replacement_rates(self, replacement_rate, existing_rate, reference_peak):
        """
        Heat generator renovation (demand_side.heat_generator_renovation):
        set the shares of the old heat generators, used by
        apply_replacement_to_remaining_stock() (see
        demand_side.heat_generator_replacement_rates / _existing_rates).
        Each heat generator only serves its own building, so the shares refer
        to the heat demand of this heat generator type after the demand side
        scenario, and are applied to its peak output at that point
        (reference_peak). Output added by later scenarios is new capacity.

        replacement_rate: share of the reference peak served by old heat
            generators at the end of their lifetime (one-to-one replacement
            in the same building).
        existing_rate: share of the reference peak served by old heat
            generators that keep running (existing capacity without capex).
        reference_peak: peak output after the demand side scenario [kW].
        """
        self._replacement_rate = float(replacement_rate)
        self._existing_rate = float(existing_rate)
        self._replacement_reference_peak = max(float(reference_peak), 0.0)

    def get_replacement_rate(self):
        return getattr(self, '_replacement_rate', None)

    def get_existing_rate(self):
        return getattr(self, '_existing_rate', None)

    def get_replacement_reference_peak(self):
        return getattr(self, '_replacement_reference_peak', None)

    def apply_replacement_to_remaining_stock(self):
        """
        Heat generator renovation: set the old stock of this heat generator
        type (called once, before calculate_replacement_cap(), see
        dem_costs.get_replacement_capacities):
        - one-to-one replacement: replacement rate * reference peak,
        - existing without capex: existing rate * reference peak,
        - any peak output above that is new capacity.
        calculate_replacement_cap() expects the old stock (existing +
        replacement) in self.existing and the replaced part in the power up
        for replacement. Techs without replacement rates are left unchanged.
        """
        if not hasattr(self, '_replacement_rate') or not hasattr(self, 'existing'):
            return
        self._power_up_for_replacement = self._replacement_rate*self._replacement_reference_peak
        self.existing = (self._replacement_rate + self._existing_rate)*self._replacement_reference_peak


    # def initialise_zero(self, variables, n_days):
    #     n_hours = n_days*24
        
    #     for var in variables:
    #         var = np.array([0]*n_hours)
    
    # def initialise_zero(self, variable, n_days):
    #     n_hours = n_days*24
    #     variable = np.array([0]*n_hours)

 
    def get_installed_cap(self):
        # Capacity for the cost module: the peak output (the optimiser builds the capacity it uses),
        # unless a technology forces a larger capacity (overridden there).
        return self.get_output().max()

    def get_output(self):
        # First check for storage variables, then for flow variables:
        for attr in ["_q_h", "_q_gas", "_q_wd", "_q_hyd", "_q_e"]:
            if hasattr(self, attr):
                return getattr(self, attr)
        for attr in ['_v_e', '_v_h', '_v_hlt', '_m_e', '_v_gas', '_v_hyd', '_v_steam']: 
            if hasattr(self, attr):
                return getattr(self, attr)
        raise AttributeError(f"No storage or flow variable found in the technology object {self}")
    
    def get_v_max(self, debug=False):
        # Maximum capacity: the first of these attributes the tech has, else 'inf'.
        # Same unit as self.existing (get_output().max()): kW for generators,
        # kWh for storages (_cap; get_output() returns the storage level).
        for attr in ['_v_h_max', 'v_max', 'kw_max', 'kW_el_max', '_cap', '_p_max']:
            if hasattr(self, attr):
                return getattr(self, attr)
        # None of the attributes exists:
        if debug:
            warnings.warn(f"No max_capacity attribute found returning 'inf' for object {self}")
        return 'inf'
    
    def get_power_up_for_replacement(self):
        if hasattr(self, '_power_up_for_replacement'):
            return self._power_up_for_replacement
        else:
            return False
    
    def get_only_allow_existing(self):
        if hasattr(self, '_only_allow_existing'):
            return self._only_allow_existing
        else:
            return False
        
    def get_existing(self):
        self.existing = self.get_output().max()

    def calculate_replacement_cap(self, debug=False):
        """
        Split the existing capacity into a capex-free part and a part that
        needs one-to-one replacement, and compute the capacity left for new
        installations.

        The results are stored in self.existing (overwritten with the
        capex-free part), self.needs_replacement and self.cap_new, and the
        returned triple is kept for get_replacement_caps().

        Must be called only once per scenario (see
        dem_costs.get_replacement_capacities): it reads self.existing and
        overwrites it, so a second call would subtract the replacement
        share again. Use get_replacement_caps() to read the results.
        """
        if hasattr(self, 'existing'):
            energy_cap_old = self.existing
        else:
            self._replacement_caps = (0, 0, self.get_v_max())
            return self._replacement_caps
        needs_replacement = self.get_power_up_for_replacement()

        energy_cap_zero_capex = energy_cap_old-needs_replacement if energy_cap_old>=needs_replacement else 0.0
        energy_cap_low_capex = needs_replacement if energy_cap_old>=needs_replacement else energy_cap_old
        
        if self.get_only_allow_existing():
            cap_one_to_one_replacement = 0.0
            cap_new = 0.0
        else:
            cap_one_to_one_replacement = energy_cap_low_capex
            if self.get_v_max() == 'inf':
                cap_new = 'inf'
            else:
                cap_new = self.get_v_max() - cap_one_to_one_replacement - energy_cap_zero_capex
        
        if self.get_v_max() != 'inf':
            if cap_new < 0.0:
                cap_one_to_one_replacement += cap_new
                cap_new = 0.0
            if cap_one_to_one_replacement < 0.0:
                energy_cap_zero_capex += cap_one_to_one_replacement
                cap_one_to_one_replacement = 0.0
            if energy_cap_zero_capex <= 0.0:
                energy_cap_zero_capex = 0.0
            
        self.existing = energy_cap_zero_capex
        self.needs_replacement = cap_one_to_one_replacement
        self.cap_new = cap_new
        self._replacement_caps = (energy_cap_zero_capex, cap_one_to_one_replacement, cap_new)

        if debug:
            print(f"Energy cap old: {energy_cap_old}")
            print(f"Needs replacement: {needs_replacement}")
            print(f"Energy cap zero capex: {energy_cap_zero_capex}")
            print(f"Energy cap low capex: {energy_cap_low_capex}")
            print(f"Cap one to one replacement: {cap_one_to_one_replacement}")
            print(f"Cap new: {cap_new}")

        return energy_cap_zero_capex, cap_one_to_one_replacement, cap_new

    def get_replacement_caps(self):
        """
        Return the result of the (single) call of calculate_replacement_cap():
        (energy_cap_zero_capex, cap_one_to_one_replacement, cap_new).
        """
        if not hasattr(self, '_replacement_caps'):
            raise RuntimeError(
                f"Replacement capacities of {type(self).__name__} have not "
                "been computed yet (call calculate_replacement_cap() once, "
                "see dem_costs.get_replacement_capacities)."
                )
        return self._replacement_caps