# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 11:32:14 2026

@author: UeliSchilt
"""
"""
Demand Resonse (DR) Flexibility
"""

"""
TMP Script workflow and methods

1. Cluster
    - Return: number of clusters; list of df_cluster_yr (per cluster one df)

For each cluster:
    1. Compute aggregated thermal capacity C_cluster
    2. Compute virtual storage size
    3. Compute heat loss rate r based on H-value (C-weighted function?)
    4. Compute annual heat demand (PROFILE AS WELL?)
    5. Compute lower annual heat demand

"""

import pandas as pd
import numpy as np

from sklearn_extra.cluster import KMedoids
from sklearn.preprocessing import StandardScaler

from district_energy_model import dem_constants as C

class BuildingInertiaFlexibility:
    
    def __init__(
            self,
            df_com_yr,
            yearly_heat_demand_col,
            delta_T_flex,
            no_of_clusters
            ):
        """
        

        Parameters
        ----------
        df_com_yr : dataframe
            dataframe with row-entry per building (annual values).
        delta_T_flex : float
            Accepted deviation from setpoint room-temperature (upwards and
            downwards) [degC]. Example: delta_T_flex = 2.0 degC with setpoint
            at 22.0 degC: The temperature can deviate between 20.0 and 24.0
            degC.
        no_of_clusters : int
            Number of clusters into which buildings are grouped according to
            their thermal characteristics.

        Returns
        -------
        None.

        """        
        
        self.df_com_yr = df_com_yr
        self.delta_T_flex = delta_T_flex
        
        self.H_header = 'H_W_per_K'
        self.C_header = 'C_MJ_per_K'
        self.yearly_heat_demand_col = yearly_heat_demand_col

        self._no_of_clusters = no_of_clusters

        # Lists to store metrics for each cluster:
        self._list_C_cluster = [] # Aggregated thermal capacity [MJ/K]
        self._list_H_cluster = [] # Heat loss rate [W/K]
        self._list_E_vs_cluster = [] # virtual storage (vs) capacity [kWh]
        self._list_d_h_yr_cluster = [] # annual heat demand [kWh]
        self._list_r_cluster = [] # Additional heat loss rate [kWh_loss/kWh_stored] per timestep
        self._list_delta_loss_max = [] # Max. additional loss from upwards flexibility

        self._list_u_h_vs_max = [] # [kWh] charge limit (per timestep)
        self._list_v_h_vs_max = [] # [kWh] discharge limit (per timestep)
        
        self._list_cap = [] # [kWh] storage capacities        
        self._list_u_h = [] # [kWh] virtual storage input
        self._list_v_h = [] # [kWh] virtual storage output
        self._list_q_h = [] # [kWh] stored energy
        self._list_l_q_h = [] # storage losses [kWh]
        self._list_dq_h_pos = [] # [kWh] state of storage increases (i.e., positive)
        self._list_dq_h_neg = [] # [kWh] state of storage decreases (i.e., negative)
        self._list_sos = [] # state of storage [-]        
        
        self._cap_tot = 0 # [kWh] virtual storage capacity across all clusters        
        self._u_h_tot = [] # [kWh] virtual storage input across all clusters
        self._v_h_tot = [] # [kWh] virtual storage output across all clusters
        self._q_h_tot = [] # [kWh] stored energy across all clusters
        self._l_q_h_tot = [] # virtual storage losses [kWh] across all clusters
        self._dq_h_pos_tot = []
        self._dq_h_neg_tot = []
        self._sos_tot = [] # state of storage [-] across all clusters
        
        # Compute clusters:
        self._list_df_cluster_yr = self.__cluster_buildings()
        
        # Compute cluster metrics (i.e., populate lists):
        self.compute_cluster_metrics()
        
    def update_df_results(self, df):
        
        # Update timeseries for each cluster of buildings (i.e., for each virtual storage):
        for i in range(self._no_of_clusters):
            df[f'u_h_vs_{i}'] = self.get_list_u_h()[i]
            df[f'v_h_vs_{i}'] = self.get_list_v_h()[i]
            df[f'q_h_vs_{i}'] = self.get_list_q_h()[i]
            df[f'l_q_h_vs_{i}'] = self.get_list_l_q_h()[i]
            df[f'dq_h_vs_pos{i}'] = self.get_list_dq_h_pos()[i]
            df[f'dq_h_vs_neg{i}'] = self.get_list_dq_h_neg()[i]
            df[f'sos_vs_{i}'] = self.get_list_sos()[i]

        # Update aggregated values across all clusters:
        df['u_h_vs_tot'] = self.get_u_h_tot()
        df['v_h_vs_tot'] = self.get_v_h_tot()
        df['q_h_vs_tot'] = self.get_q_h_tot()
        df['l_q_h_vs_tot'] = self.get_l_q_h_tot()
        df['dq_h_vs_pos_tot'] = self.get_dq_h_pos_tot()
        df['dq_h_vs_neg_tot'] = self.get_dq_h_neg_tot()
        df['sos_vs_tot'] = self.get_sos_tot()

        return df
    
    def reduce_timeframe(self, n_days):
        """
        Reduce the hourly timeseries to the first n days.

        Parameters
        ----------
        n_days : int
            Number of days (starting at the first day of the year).

        Returns
        -------
        None.

        """
        
        n_hours = n_days*24
        
        # Update timeseries for each cluster of buildings (i.e., for each virtual storage):
        for i in range(self._no_of_clusters):        
            self._list_u_h[i] = self._list_u_h[i][:n_hours]
            self._list_v_h[i] = self._list_v_h[i][:n_hours]
            self._list_q_h[i] = self._list_q_h[i][:n_hours]
            self._list_l_q_h[i] = self._list_l_q_h[i][:n_hours]
            self._list_dq_h_pos[i] = self._list_dq_h_pos[i][:n_hours]
            self._list_dq_h_neg[i] = self._list_dq_h_neg[i][:n_hours]
            self._list_sos[i] = self._list_sos[i][:n_hours]
            
        self._u_h_tot = self._u_h_tot[:n_hours]
        self._v_h_tot = self._v_h_tot[:n_hours]
        self._q_h_tot = self._q_h_tot[:n_hours]
        self._l_q_h_tot = self._l_q_h_tot[:n_hours]
        self._dq_h_pos_tot = self._dq_h_pos_tot[:n_hours]
        self._dq_h_neg_tot = self._dq_h_neg_tot[:n_hours]
        self._sos_tot = self._sos_tot[:n_hours]
        
    def compute_cluster_metrics(self):
        
        for df_cluster_yr in self._list_df_cluster_yr:
            
            # print(df_cluster_yr.info())
            # print(df_cluster_yr.head())
            
            C_cluster = df_cluster_yr[self.C_header].sum()
            H_cluster = df_cluster_yr[self.H_header].sum() # [W/K]
            r_cluster = H_cluster / (C_cluster*C.CONV_MJ_to_kWh*1e3) # [kWh_loss/kWh_stored] per timestep
            E_vs_cluster = 2*C_cluster*self.delta_T_flex*C.CONV_MJ_to_kWh # [kWh]; factor 2 because we need upward and downward flexibility
            d_h_yr_cluster = df_cluster_yr[self.yearly_heat_demand_col].sum()
            delta_loss_max = r_cluster*0.5*E_vs_cluster
            u_h_vs_max = H_cluster*self.delta_T_flex*1000 # [kWh] charge limit (per timestep)
            v_h_vs_max = u_h_vs_max # [kWh] discharge limit (per timestep)
            
            self._list_C_cluster.append(C_cluster)
            self._list_H_cluster.append(H_cluster)
            self._list_r_cluster.append(r_cluster)
            self._list_E_vs_cluster.append(E_vs_cluster)
            self._list_d_h_yr_cluster.append(d_h_yr_cluster)
            self._list_delta_loss_max.append(delta_loss_max)
            self._list_u_h_vs_max.append(u_h_vs_max)
            self._list_v_h_vs_max.append(v_h_vs_max)
            
    def generate_df_metrics(self):
        
        dict_metrics = {
            'C_cluster_MJ_per_K':self._list_C_cluster,
            'H_cluster_W_per_K':self._list_H_cluster,
            'E_vs_cluster_kWh':self._list_E_vs_cluster,
            'd_h_yr_cluster_kWh':self._list_d_h_yr_cluster,
            'r_cluster_kWh_loss_per_kWh_stored':self._list_r_cluster,
            'delta_loss_max_cluster_kWh':self._list_delta_loss_max,
            # 'cap_cluster_kWh':self._list_cap,
            }
        
        df = pd.DataFrame(dict_metrics)
        
        return df
            
    def create_techs_dict(self, techs_dict, color):
        """
        Create virtual storage tech in Calliope (one per building cluster).

        Parameters
        ----------
        techs_dict : TYPE
            DESCRIPTION.
        color : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        # Loop through building clusters:
        for i in range(self._no_of_clusters):

            E_vs = self._list_E_vs_cluster[i] # virtual storage (vs) capacity [kWh]
            r_cluster = self._list_r_cluster[i] # Additional heat loss rate [kWh_loss/kWh_stored] per timestep
            u_h_vs_max = self._list_u_h_vs_max[i]
        
            # Compute initial storage charge (50% of total capacity):
            ic = 0.5
        
            techs_dict[f'virtual_storage_flex_{i}'] = {}
                
            techs_dict[f'virtual_storage_flex_{i}'] = {
                'essentials':{
                    'name':f'Flexibility - Virtual Storage {i}',
                    'color':color,
                    'parent':'storage',
                    'carrier_in':'heat',
                    'carrier_out':'heat',
                    },
                'constraints':{
                    'storage_initial':ic,
                    'storage_cap_equals':E_vs,
                    'storage_loss':r_cluster,
                    'energy_eff': 1.0,
                    'energy_cap_equals': u_h_vs_max, # charge/discharge capacity
                    'lifetime': 25,
                    # 'force_asynchronous_prod_con':True,
                    },
                'costs':{
                    'monetary':{
                        'om_prod':0.0,
                        'storage_cap':0.0,
                        'interest_rate':0.0,
                        'om_annual':0.0
                        },
                    'emissions_co2':{
                        'om_prod':0.0
                        }
                    }
                }
        
        return techs_dict
        
    def __cluster_buildings(self):
        """
        Cluster buildings based on thermal dynamics properties. Each cluster
        of buildings will be treated as a single building in the MILP model.
        Clustering method: K-medoids.
        https://scikit-learn-extra.readthedocs.io/en/stable/generated/sklearn_extra.cluster.KMedoids.html

        Returns
        -------
        no_of_clusters : int
            Number of clusters.
        list_df_cluster_yr : list of df
            List of dataframes. Each dataframe is a subset of df_com_yr,
            containing the data pertaining to the respective cluster of
            buildings.

        """
        CLUSTER_COL = 'cluster_label'
        
        # Cluster metrics (will be calculated to log and scaled):
        metr_1 = self.C_header
        metr_2 = self.H_header
        # Other options: tau, GBAUP, ...
        
        # Guard against non-positive values (log undefined)
        mask_valid =\
            (self.df_com_yr[metr_1] > 0) & (self.df_com_yr[metr_2] > 0)
        if not mask_valid.all():
            # Keep invalid rows but mark as NaN cluster
            self.df_com_yr.loc[~mask_valid, CLUSTER_COL] = np.nan
        
        df_valid = self.df_com_yr.loc[mask_valid, [metr_1, metr_2]].copy()
        
        X = np.column_stack([
            np.log(df_valid[metr_1].to_numpy(dtype=float)),
            np.log(df_valid[metr_2].to_numpy(dtype=float)),
        ])
        
        # Optional but recommended: scale features so log(C) and log(H) contribute comparably
        X_scaled = StandardScaler().fit_transform(X)
        
        # Cluster (K-medoids)
        kmedoids = KMedoids(
            n_clusters=self._no_of_clusters,
            metric="euclidean",
            init="k-medoids++",
            random_state=0,
        )
        
        labels = kmedoids.fit_predict(X_scaled)
        
        # Write labels back to the original dataframe
        self.df_com_yr.loc[mask_valid, CLUSTER_COL] = labels
        self.df_com_yr[CLUSTER_COL] =\
            self.df_com_yr[CLUSTER_COL].astype("Int64")  # nullable int
        
        # Create list of per-cluster dataframes
        list_df_cluster_yr = [
            self.df_com_yr[self.df_com_yr[CLUSTER_COL] == i].copy()
            for i in range(self._no_of_clusters)
        ]
        
        # list_df_cluster_yr = [self.df_com_yr.copy()] # FOR TESTING
        
        return list_df_cluster_yr
        
    def __compute_cluster_capacity(self):
        """
        

        Returns
        -------
        C_cluster : float
            DESCRIPTION.

        """
        C_cluster = ...
        
        return C_cluster
    
    def __compute_list_l_q_h(self):
        self._list_l_q_h = []
        for i, q_h in enumerate(self._list_q_h):
            l_q_h = np.array(q_h*self._list_r_cluster[i])
            self._list_l_q_h.append(l_q_h)
        self._l_q_h_tot = np.sum(self._list_l_q_h, axis=0)
        
    def __compute_list_dq_h(self):
        self._list_dq_h_pos = []
        self._list_dq_h_neg = []
        for i, l_q_h in enumerate(self._list_l_q_h):
            dq_h = np.array(
                -l_q_h
                + self.get_list_u_h()[i]
                - self.get_list_v_h()[i]
                )
            dq_h_pos = np.where(dq_h > 0, dq_h, 0)
            dq_h_neg = np.where(dq_h < 0, -dq_h, 0)
            
            self._list_dq_h_pos.append(dq_h_pos)
            self._list_dq_h_neg.append(dq_h_neg)
            
        self._dq_h_pos_tot = np.sum(self._list_dq_h_pos, axis=0)
        self._dq_h_neg_tot = np.sum(self._list_dq_h_neg, axis=0)

    def len_test(self,items):
        if len(items)==0:
            raise ValueError()
        
    def num_test(self,var):
        # if isinstance(var, float)==False:
        if isinstance(var, (int, float, np.integer))==False:
            raise ValueError()
    
    def update_list_u_h(self, list_u_h_updated):
        # if len(list_u_h_updated) != len(self._list_u_h):
        #     raise ValueError()
        self._list_u_h = []
        for u_h in list_u_h_updated:
            self._list_u_h.append(np.array(u_h))
            
        self._u_h_tot = np.sum(self._list_u_h, axis=0)
        
    def update_list_v_h(self, list_v_h_updated):
        # if len(list_v_h_updated) != len(self._list_v_h):
        #     raise ValueError()
        self._list_v_h = []
        for v_h in list_v_h_updated:
            self._list_v_h.append(np.array(v_h))
        
        self._v_h_tot = np.sum(self._list_v_h, axis=0)
        
    def update_list_q_h(self, list_q_h_updated):
        # if len(list_q_h_updated) != len(self._list_q_h):
        #     raise ValueError()
        self._list_q_h = []
        for q_h in list_q_h_updated:
            self._list_q_h.append(np.array(q_h))
            
        self.__compute_list_l_q_h()        
        self.__compute_list_dq_h()
        
        self._q_h_tot = np.sum(self._list_q_h, axis=0)

    def update_list_sos(self, list_sos_updated):
        # if len(list_sos_updated) != len(self._list_sos):
        #     raise ValueError()        
        self._list_sos = list_sos_updated    
        
        self._sos_tot = np.sum(self._list_sos, axis=0)

    def update_list_cap(self, list_cap_updated):
        # for cap in list_cap_updated:
        #     self.num_test(cap)
        self._list_cap = list_cap_updated
        
        self._cap_tot = float(sum(self._list_cap))
        
    def get_no_of_clusters(self):
        self.num_test(self._no_of_clusters)
        return self._no_of_clusters
    
    def get_list_df_cluster_yr(self):
        self.len_test(self._list_df_cluster_yr)
        return self._list_df_cluster_yr
    
    def get_list_C_cluster(self):
        self.len_test(self._list_C_cluster)
        return self._list_C_cluster
    
    def get_list_H_cluster(self):
        self.len_test(self._list_H_cluster)
        return self._list_H_cluster
    
    def get_list_E_vs_cluster(self):
        self.len_test(self._list_E_vs_cluster)
        return self._list_E_vs_cluster
    
    def get_list_d_h_yr_cluster(self):
        self.len_test(self._list_d_h_yr_cluster)
        return self._list_d_h_yr_cluster
    
    def get_list_r_cluster(self):
        self.len_test(self._list_r_cluster)
        return self._list_r_cluster
    
    def get_list_delta_loss_max(self):
        self.len_test(self._list_delta_loss_max)
        return self._list_delta_loss_max
    
    def get_list_u_h_vs_max(self):
        self.len_test(self._list_u_h_vs_max)
        return self._list_u_h_vs_max
    
    def get_list_v_h_vs_max(self):
        self.len_test(self._list_v_h_vs_max)
        return self._list_v_h_vs_max
    
    def get_list_cap(self):
        self.len_test(self._list_cap)
        return self._list_cap

    def get_list_u_h(self):
        self.len_test(self._list_u_h)
        return self._list_u_h
    
    def get_list_v_h(self):
        self.len_test(self._list_v_h)
        return self._list_v_h
    
    def get_list_q_h(self):
        self.len_test(self._list_q_h)
        return self._list_q_h
    
    def get_list_l_q_h(self):
        self.len_test(self._list_l_q_h)
        return self._list_l_q_h
    
    def get_list_dq_h_pos(self):
        self.len_test(self._list_dq_h_pos)
        return self._list_dq_h_pos
    
    def get_list_dq_h_neg(self):
        self.len_test(self._list_dq_h_neg)
        return self._list_dq_h_neg
    
    def get_list_sos(self):
        self.len_test(self._list_sos)
        return self._list_sos
    
    def get_cap_tot(self):
        self.len_test(self._cap_tot)
        return self._cap_tot
    
    def get_u_h_tot(self):
        self.len_test(self._u_h_tot)
        return self._u_h_tot
    
    def get_v_h_tot(self):
        self.len_test(self._v_h_tot)
        return self._v_h_tot
    
    def get_q_h_tot(self):
        self.len_test(self._q_h_tot)
        return self._q_h_tot
    
    def get_l_q_h_tot(self):
        self.len_test(self._l_q_h_tot)
        return self._l_q_h_tot
    
    def get_dq_h_pos_tot(self):
        self.len_test(self._dq_h_pos_tot)
        return self._dq_h_pos_tot
    
    def get_dq_h_neg_tot(self):
        self.len_test(self._dq_h_neg_tot)
        return self._dq_h_neg_tot
    
    def get_sos_tot(self):
        self.len_test(self._sos_tot)
        return self._sos_tot
        
# MODULE TESTING:
test_code = False
save_plots = False
if test_code:
    ...
    GGDENAME = 'Allschwil'
    df_master_path = r'C:\Users\UeliSchilt\OneDrive - Hochschule Luzern\97_DEM_testing\data\master_data\simulation_data\df_master_sim.feather'
    
    if 'df_master' not in globals():        
        df_master = pd.read_feather(df_master_path)
    else:
        print("df_master already loaded.")
    
    df_com_yr = df_master[df_master['GGDENAME']==GGDENAME]
    
    yearly_heat_demand_col = 'heat_energy_demand_estimate_kWh_combined'
    
    flex_inst = BuildingInertiaFlexibility(
        df_com_yr=df_com_yr,
        yearly_heat_demand_col=yearly_heat_demand_col,
        delta_T_flex=2.0,
        no_of_clusters=5
        )
    
    N_CLUSTERS = 5
    COL_C = "C_MJ_per_K"
    COL_H = "H_W_per_K"
    CLUSTER_COL = "cluster_label"
        
    # PLOT:
    import matplotlib.pyplot as plt
    
    # Drop rows with NA clusters
    df_plot = df_com_yr.dropna(subset=[CLUSTER_COL]).copy()
    
    # Convert to plain int (important!)
    df_plot[CLUSTER_COL] = df_plot[CLUSTER_COL].astype(int)
    
    s_ = 10

    # 1) C vs H
    plt.figure()
    sc = plt.scatter(
        df_plot[COL_C],
        df_plot[COL_H],
        c=df_plot[CLUSTER_COL],
        s=s_,
        alpha=0.7
    )
    plt.xlabel("C [MJ/K")
    plt.ylabel("H [W/K]")
    plt.title("C vs H (clustered)")
    plt.colorbar(sc, label="Cluster")
    plt.tight_layout()    
    if save_plots:
        plt.savefig(
            "../../scatter_C_vs_H.png",
            dpi=300,
            bbox_inches="tight"
        )
    plt.show()
    
    # 2) log(C) vs log(H)
    plt.figure()
    sc = plt.scatter(
        np.log(df_plot[COL_C]),
        np.log(df_plot[COL_H]),
        c=df_plot[CLUSTER_COL],
        s=s_,
        alpha=0.7
    )
    plt.xlabel("log(C)")
    plt.ylabel("log(H)")
    plt.title("log(C) vs log(H) (clustered)")
    plt.colorbar(sc, label="Cluster")
    plt.tight_layout()   
    if save_plots:
        plt.savefig(
            "../../scatter_logC_vs_logH.png",
            dpi=300,
            bbox_inches="tight"
        )
    plt.show()
    
# cluster_dfs = flex_inst.get_list_df_cluster_yr()
# print(cluster_dfs[0].info())
















