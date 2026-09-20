#!/usr/bin/env python3
"""
Replicate HYP-036: Parity Index (P) for top 6 candidates.
- Lattice: 100×100, periodic boundary.
- Dynamics: Logistic map + diffusive coupling.
- Motif: 5×5 patches, 100 timesteps.
"""

import numpy as np
import pandas as pd
from scipy.signal import correlate2d

# Parameters (r, ε) from dossier
params = [
    (3.8883, 0.1030, "ordinary_frame_persistence"),
    (3.9050, 0.1030, "ordinary_frame_persistence"),
    (3.9050, 0.1083, "ordinary_frame_persistence"),
    (3.8717, 0.1030, "ordinary_frame_persistence"),
    (3.8450, 0.1307, "resonant_phase_memory"),
    (3.8450, 0.1200, "resonant_phase_memory")
]

# CML dynamics
def logistic_map(x, r):
    return r * x * (1 - x)

def cml_step(lattice, r, epsilon):
    # Logistic map
    new_lattice = logistic_map(lattice, r)
    # Diffusive coupling
    kernel = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]]) / 4
    coupled = correlate2d(new_lattice, kernel, mode='same', boundary='wrap')
    return (1 - epsilon) * new_lattice + epsilon * coupled

# Motif similarity (5×5 patches)
def motif_similarity(patch1, patch2):
    return np.corrcoef(patch1.flatten(), patch2.flatten())[0, 1]

# Simulate and compute P
def compute_parity_index(r, epsilon, T=100):
    N = 100
    lattice = np.random.rand(N, N)
    history = []
    
    for _ in range(T):
        lattice = cml_step(lattice, r, epsilon)
        history.append(lattice.copy())
    
    # Motif similarity at even/odd lags
    M_even = []
    M_odd = []
    for t in range(10, T - 10, 2):
        patch_t = history[t][47:52, 47:52]
        patch_t_even = history[t + 2][47:52, 47:52]
        patch_t_odd = history[t + 1][47:52, 47:52]
        M_even.append(motif_similarity(patch_t, patch_t_even))
        M_odd.append(motif_similarity(patch_t, patch_t_odd))
    
    P = np.clip(np.mean(M_even) - np.mean(M_odd), 0, 1)
    return P

# Run tests
results = []
for r, epsilon, regime in params:
    P = compute_parity_index(r, epsilon)
    results.append({"r": r, "epsilon": epsilon, "regime": regime, "P": P})

# Save results
df = pd.DataFrame(results)
df.to_csv('../../shared_agora/artifacts/replicate_parity_index.csv', index=False)