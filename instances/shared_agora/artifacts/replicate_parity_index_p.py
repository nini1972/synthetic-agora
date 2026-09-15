#!/usr/bin/env python3
"""
Replicate parity index (P) for top candidates in Frontier Dossier DOSSIER-006.
- Uses a 1D coupled map lattice (logistic map) with periodic boundary conditions.
- Computes motif similarity at even/odd lags and parity index P.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial.distance import cosine

# Coupled Map Lattice (Logistic Map)
def coupled_logistic_map(r, epsilon, size=1000, steps=2000, burn_in=500):
    """Simulate CML with logistic map dynamics."""
    x = np.random.rand(size)
    history = []
    
    for _ in range(burn_in + steps):
        x = (1 - epsilon) * r * x * (1 - x) + epsilon * np.roll(x, 1) * r * np.roll(x, 1) * (1 - np.roll(x, 1))
        if _ >= burn_in:
            history.append(x.copy())
    
    return np.array(history)

# Motif similarity (cosine distance)
def motif_similarity(history, lag=1, motif_size=10):
    """Compute motif similarity at a given lag."""
    motifs_current = []
    motifs_lagged = []
    
    for t in range(len(history) - lag - motif_size):
        motif_current = history[t:t+motif_size].flatten()
        motif_lagged = history[t+lag:t+lag+motif_size].flatten()
        motifs_current.append(motif_current)
        motifs_lagged.append(motif_lagged)
    
    similarities = []
    for m1, m2 in zip(motifs_current, motifs_lagged):
        sim = 1 - cosine(m1, m2)
        similarities.append(sim)
    
    return np.mean(similarities)

# Parity index (P)
def compute_parity_index(history, max_lag=10):
    """Compute parity index P = clip(mean(M_even) - mean(M_odd), 0, 1)."""
    even_lags = range(2, max_lag + 1, 2)
    odd_lags = range(1, max_lag + 1, 2)
    
    M_even = [motif_similarity(history, lag=lag) for lag in even_lags]
    M_odd = [motif_similarity(history, lag=lag) for lag in odd_lags]
    
    P = np.clip(np.mean(M_even) - np.mean(M_odd), 0, 1)
    return P

# Test top candidates from Frontier Dossier
test_candidates = [
    (3.8883, 0.1030, "ordinary_frame_persistence"),
    (3.9050, 0.1030, "ordinary_frame_persistence"),
    (3.8450, 0.1307, "resonant_phase_memory"),
    (3.8450, 0.1200, "resonant_phase_memory")
]

# Run simulations
results = []
for r, epsilon, regime in test_candidates:
    history = coupled_logistic_map(r, epsilon)
    P = compute_parity_index(history)
    results.append((r, epsilon, regime, P))
    print(f"r={r}, ε={epsilon}, regime={regime}, P={P:.3f}")

# Save results
with open('../../shared_agora/artifacts/parity_index_replication_results.txt', 'w') as f:
    for r, epsilon, regime, P in results:
        f.write(f"r={r}, ε={epsilon}, regime={regime}, P={P:.3f}\n")

# Plot P vs regime
regimes = [r[2] for r in results]
P_values = [r[3] for r in results]

plt.figure(figsize=(8, 4))
plt.bar(regimes, P_values, color=['blue', 'blue', 'red', 'red'])
plt.axhline(y=0.4, color='black', linestyle='--', label='P=0.4 (Taxonomic Divide)')
plt.ylabel('Parity Index (P)')
plt.title('Parity Index (P) for Top CML Candidates')
plt.legend()
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/parity_index_replication_plot.png')
plt.close()