#!/usr/bin/env python3
"""
Defensive Stress-Test for EMP-097: Entropy-Driven Rule Evolution in Self-Referential CA

Tests:
1. Noise Injection: 5% bit-flip noise per iteration.
2. Entropy Metric Sensitivity: Replace Shannon entropy with Tsallis entropy (q=2).
3. Rule Interpolation Artifacts: Use sigmoid interpolation between rule-sets.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import use as mpl_use
from scipy.ndimage import convolve

mpl_use('Agg')  # Headless backend

# Parameters
N = 20
T = 1000
seeds = 3  # Reduced for efficiency
noise_level = 0.05

# Rule-sets (Moore neighborhood)
RULE_GOL = np.array([0, 0, 1, 1, 0, 0, 0, 0, 0])  # Game of Life: B3/S23
RULE_CHAOS = np.array([0, 1, 0, 1, 1, 0, 1, 0, 0])  # Chaotic rule

# Kernel for Moore neighborhood
kernel = np.ones((3, 3), dtype=int)
kernel[1, 1] = 0


def shannon_entropy(grid):
    """Shannon entropy of a binary grid."""
    p = np.mean(grid)
    if p == 0 or p == 1:
        return 0.0
    return -p * np.log2(p) - (1 - p) * np.log2(1 - p)


def tsallis_entropy(grid, q=2):
    """Tsallis entropy (q=2) of a binary grid."""
    p = np.mean(grid)
    if p == 0 or p == 1:
        return 0.0
    return (1 - (p**q + (1 - p)**q)) / (q - 1)


def apply_rule(grid, rule):
    """Apply CA rule to grid."""
    neighbors = convolve(grid, kernel, mode='wrap')
    new_grid = np.zeros_like(grid)
    for i in range(3):
        for j in range(3):
            if i == 1 and j == 1:
                continue
            mask = (neighbors == (i * 3 + j))
            new_grid[mask] = rule[i * 3 + j]
    return new_grid