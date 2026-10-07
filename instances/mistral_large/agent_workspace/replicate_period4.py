#!/usr/bin/env python3
"""
Replicate the Period-4 Symbolic Order in coupled logistic map lattices to verify HYP-100.

System:
    x_i^{t+1} = (1-ε)r x_i^t(1-x_i^t) + (ε/2)[r x_{i-1}^t(1-x_{i-1}^t) + r x_{i+1}^t(1-x_{i+1}^t)]

Parameters: r=3.863, ε=0.132, N=100, T=2000
"""

import numpy as np
import matplotlib.pyplot as plt

# Configure matplotlib for headless execution
plt.switch_backend('Agg')

# Parameters
r = 3.863
epsilon = 0.132
N = 100  # System size
T = 2000  # Time steps
threshold = 0.5

# Initialize lattice
x = np.random.rand(N)

# Store symbolic dynamics
symbolic = np.zeros((T, N), dtype=int)

# Simulate
for t in range(T):
    x_prev = x.copy()
    for i in range(N):
        left = x_prev[i-1] if i > 0 else x_prev[-1]
        right = x_prev[i+1] if i < N-1 else x_prev[0]
        x[i] = (1 - epsilon) * r * x_prev[i] * (1 - x_prev[i]) + \
               (epsilon / 2) * (r * left * (1 - left) + r * right * (1 - right))
    symbolic[t] = (x > threshold).astype(int)

# Compute motif consistency at lags mod 4
def motif_consistency(lag):
    matches = 0
    total = 0
    for t in range(T - lag):
        for i in range(N):
            if symbolic[t, i] == symbolic[t + lag, i]:
                matches += 1
            total += 1
    return matches / total if total > 0 else 0

lags = [0, 1, 2, 3]
consistency = [motif_consistency(4 * k + lag) for lag in lags for k in range(1, (T - lag) // 4)]
consistency = [np.mean(consistency[i::4]) for i in range(4)]

# Phase contrast metric
C4 = consistency[0] - consistency[2]

# Plot motif consistency
plt.figure(figsize=(8, 5))
plt.bar(range(4), consistency, color=['blue', 'orange', 'green', 'red'])
plt.xticks(range(4), [f'lag ≡ {i} mod 4' for i in range(4)])
plt.ylabel('Motif Consistency')
plt.title(f'Period-4 Symbolic Order (C4 = {C4:.3f})')
plt.savefig('period4_motif_consistency.png')

# Save results
results = {
    "r": r,
    "epsilon": epsilon,
    "N": N,
    "T": T,
    "consistency": consistency,
    "C4": C4
}
np.save('period4_results.npy', results)

print("Replication complete. Artifacts saved:")
print(f"- period4_motif_consistency.png (C4 = {C4:.3f})")
print("- period4_results.npy")