# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 09:29:04 2024

@author: Somesh
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import average, complete, fcluster
from scipy.spatial.distance import pdist
import scipy.spatial.distance as sps
import triangle as tr
import concave_hull as ch

def get_clusters_complete(com_file, max_distance):
    
    # arg = com_file['GKAT'].isin([1020, 1030, 1040])
    # com_file_clustering = com_file.loc[arg]
    com_file_clustering = com_file
    
    x = com_file_clustering['GKODE']
    y = com_file_clustering['GKODN']
    
    x = np.array(x)
    y = np.array(y)
    
    points = np.array([x, y]).T
    
    dist = pdist(points)
    Z = complete(dist)
    cluster_num = fcluster(Z, max_distance, criterion = 'distance')
    
    # com_file['cluster_number'] = cluster_num
    com_file['cluster_number'] = 0
    com_file.loc[:, 'cluster_number'] = cluster_num
    
    return com_file, cluster_num, points

def get_cluster_vertices(com_file):
    
    x = com_file.groupby('cluster_number')['GKODE'].mean().round().astype(int)
    y = com_file.groupby('cluster_number')['GKODN'].mean().round().astype(int)
    com_locs = np.array([x, y]).T

    indexes = ch.concave_hull_indexes(com_locs)
    segs = np.array([indexes[:-1], indexes[1:]]).T
    segs = np.concatenate((segs, [[segs[0, 0], segs[-1, -1]]]), axis = 0)

    data = {'vertices':com_locs,
            'segments':segs}

    t = tr.triangulate(data, 'p')

    triangles = t['triangles']
    vertices1 = np.array([triangles[:, 0], triangles[:, 1]]).T
    vertices2 = np.array([triangles[:, 1], triangles[:, 2]]).T
    vertices3 = np.array([triangles[:, 2], triangles[:, 0]]).T
    
    vertices = np.vstack((vertices1, vertices2, vertices3))
    vertices = np.unique(np.sort(vertices), axis = 0)

    points_start = com_locs[vertices[:, 0]]
    points_end = com_locs[vertices[:, 1]]
    vertex_lengths = np.linalg.norm(points_end - points_start, axis = 1)
    
    return vertices, vertex_lengths


