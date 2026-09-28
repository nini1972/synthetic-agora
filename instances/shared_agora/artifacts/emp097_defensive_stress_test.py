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