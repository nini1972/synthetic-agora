import matplotlib
matplotlib.use('Agg')
import numpy as np
import pandas as pd
from scipy.stats import linregress
# GoL configurations
configs = {
    'Block': [1, 0, 0, 0, 0, 0, 0, 0, 0],
    'Glider': [0, 1, 1, 0, 1, 0, 0, 0, 0],
    'R-pentomino': [0, 0, 1, 0, 1, 1, 0, 0, 0],
    'Random': np.random.choice([0,1], size=9, p=[0.5, 0.5])
}
# Lempel-Ziv complexity
def lz_complexity(seq):
    n = len(seq)
    seq = list(seq)
    i = 1
    j = 0
    complexity = 1
    while i < n:
        if seq[i] != seq[j]: 
            complexity += 1
            j = i
        i += 1
    return complexity
# Rolling window temporal LZ
def rolling_temporal_lz(grid, window=20):
    lz_values = []
    for i in range(len(grid) - window):
        window_seq = tuple(grid[i:i+window])
        lz_values.append(lz_complexity(window_seq))
    return np.array(lz_values)
# Spatial LZ on binary grid
def spatial_lz(grid):
    flat_grid = ''.join(map(str, grid.flatten()))
    return lz_complexity(flat_grid)
# Compute and plot
for config_name, config in configs.items():
    grid = np.array(config).reshape(3,3)
    # Add more code here
