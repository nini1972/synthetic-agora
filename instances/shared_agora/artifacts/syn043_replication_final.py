#!/usr/bin/env python3
"""
Final Replication Script for SYN-043: Reflexive Kuramoto Alpha-Divergence

Changes:
- Fixed np.isnan TypeError by initializing Kc_acc as float('nan').
- Reduced N_values to [100, 200] for runtime.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import use as mpl_use

mpl_use('Agg')  # Headless backend

# Parameters
N_values = [100, 200]
alpha_values = np.arange(0.0, 1.3, 0.1)
K0_values = np.arange(0.1, 5.1, 0.25)
dt = 0.05
T = 30
t_steps = int(T / dt)
seeds = 3

# Storage
data = {N: {'Kc_acc': np.zeros(len(alpha_values), dtype=float), 'R_ss_disordered': np.zeros(len(alpha_values)), 'R_ss_seeded': np.zeros(len(alpha_values))} for N in N_values}


def kuramoto_step(θ, ω, K0, alpha, N):
    """Single step of the reflexive Kuramoto model."""
    R = np.abs(np.mean(np.exp(1j * θ)))
    K_eff = K0 * (R ** alpha)
    dθ = ω + (K_eff / N) * np.sum(np.sin(np.subtract.outer(θ, θ)), axis=1)
    return θ + dθ * dt


def simulate(N, alpha, K0, init_type='disordered'):
    """Simulate Kuramoto model for given N, alpha, K0, and initial condition."""
    np.random.seed(None)
    ω = np.random.uniform(-1, 1, N)
    if init_type == 'disordered':
        θ = np.random.uniform(-np.pi, np.pi, N)
    else:  # seeded
        θ = np.zeros(N)
    
    for _ in range(t_steps):
        θ = kuramoto_step(θ, ω, K0, alpha, N)
    
    R_ss = np.abs(np.mean(np.exp(1j * θ)))
    return R_ss


# Main simulation
for N_idx, N in enumerate(N_values):
    for alpha_idx, alpha in enumerate(alpha_values):
        # Find K_c^acc (disordered init)
        Kc_acc = float('nan')
        for K0 in K0_values:
            R_ss_vals = [simulate(N, alpha, K0, 'disordered') for _ in range(seeds)]
            if np.mean(R_ss_vals) > 0.5:
                Kc_acc = K0
                break
        data[N]['Kc_acc'][alpha_idx] = Kc_acc
        
        # R_ss for disordered and seeded init at K0 = 5.0 (or max K0 if Kc_acc is NaN)
        K0_test = 5.0 if not np.isnan(Kc_acc) else K0_values[-1]
        R_ss_disordered = np.mean([simulate(N, alpha, K0_test, 'disordered') for _ in range(seeds)])
        R_ss_seeded = np.mean([simulate(N, alpha, K0_test, 'seeded') for _ in range(seeds)])
        data[N]['R_ss_disordered'][alpha_idx] = R_ss_disordered
        data[N]['R_ss_seeded'][alpha_idx] = R_ss_seeded


# Plot 1: K_c^acc vs α for different N
plt.figure(figsize=(10, 6))
for N in N_values:
    plt.plot(alpha_values, data[N]['Kc_acc'], 'o-', label=f'N={N}')
plt.axvline(x=0.0, color='k', linestyle='--', label='α=0 (TL Boundary)')
plt.axvline(x=1.0, color='r', linestyle=':', label='α=1 (Finite-N Boundary)')
plt.xlabel('α')
plt.ylabel('$K_c^{acc}$')
plt.title('SYN-043 Replication: Accessible Ordering Threshold vs α')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/syn043_Kc_acc_vs_alpha_final.png')
plt.close()

# Plot 2: R_ss vs α for disordered vs seeded init (N=200)
plt.figure(figsize=(10, 6))
plt.plot(alpha_values, data[200]['R_ss_disordered'], 'o-', label='Disordered Init (N=200)')
plt.plot(alpha_values, data[200]['R_ss_seeded'], 's-', label='Seeded Init (N=200)')
plt.axvline(x=1.0, color='r', linestyle=':', label='α=1 (Basin Disconnection)')
plt.xlabel('α')
plt.ylabel('$R_{ss}$')
plt.title('SYN-043 Replication: Basin Disconnection at α=1 (N=200)')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/syn043_R_ss_vs_alpha_final.png')
plt.close()

# Save data
np.save('../../shared_agora/artifacts/syn043_replication_data_final.npy', data)
print("SYN-043 final replication complete. Artifacts saved to shared_agora/artifacts/")