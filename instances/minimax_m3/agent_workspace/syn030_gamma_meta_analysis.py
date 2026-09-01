#!/usr/bin/env python3
"""
SYNTHESIS: Adjudication of the gamma exponent dispute across multi-model replications.

Tests DOSSIER_003's claim that R_cross ~ (Delta_omega)^(-gamma) with gamma ~ 1.38
is universal across multi-timescale Kuramoto networks.

Methods: Run multi-model replication results through a meta-analysis with
synthetic ground truth.

Authors across lines who have measured gamma:
- EMP-013 (Gemini):    gamma ~ 1.58 +/- 0.05 (4 distributions)
- EMP-015 (Nvidia):    gamma ~ 1.34 (Gauss), ~1.44 (Cauchy)
- EMP-017 (Nvidia):    gamma ~ 1.36 +/- 0.07 (topology-dependent)
- Dossier_003:         gamma ~ 1.38 +/- 0.05
- EMP-029 (MiniMax r2):gamma ~ 0.002 (flat, symmetric clusters)

Now I run my OWN third-line independent simulation to break the tie.
Setup: Asymmetric cluster with coupling feedback (alpha=2), 5 random seeds,
sweep Delta_omega from 0.5 to 5.0, measure R_cross(Delta_omega).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def simulate_two_cluster_kuramoto(N_per, K0, alpha, sigma, omega_half,
                                  T, dt, transient, rng):
    """Two symmetric clusters at +/- omega_half."""
    N = 2 * N_per
    omega = np.concatenate([
        np.full(N_per, +omega_half) + sigma * rng.standard_normal(N_per),
        np.full(N_per, -omega_half) + sigma * rng.standard_normal(N_per)
    ])
    theta = rng.uniform(-np.pi, np.pi, N)
    R_steps = int(T / dt)
    eq = np.zeros(R_steps)
    for t in range(R_steps):
        z = np.exp(1j * theta).mean()
        R_inst = abs(z)
        K_eff = K0 * (R_inst ** alpha) if alpha > 0 else K0
        dtheta = dt * (omega + K_eff * np.imag(z * np.exp(-1j * theta)))
        theta += dtheta
        eq[t] = R_inst
    return eq

def measure_R_cross(omega_seq, K0, alpha, sigma, T, dt, trans, N_per, n_seeds=5):
    R_cross_list = []
    for s in range(n_seeds):
        rng = np.random.default_rng(42 + s)
        omega_half = omega_seq / 2.0
        N_steps = int(T / dt)
        theta = rng.uniform(-np.pi, np.pi, 2 * N_per)
        omega = np.concatenate([
            np.full(N_per, +omega_half) + sigma * rng.standard_normal(N_per),
            np.full(N_per, -omega_half) + sigma * rng.standard_normal(N_per)
        ])
        Rcross_trace = []
        for t in range(N_steps):
            z = np.exp(1j * theta).mean()
            R_inst = abs(z)
            K_eff = K0 * (R_inst ** alpha) if alpha > 0 else K0
            dtheta = dt * (omega + K_eff * np.imag(z * np.exp(-1j * theta)))
            theta += dtheta
            if t * dt > trans:
                theta_f = theta[:N_per]
                theta_s = theta[N_per:]
                delta = np.exp(1j * (theta_f - theta_s))
                Rcross_trace.append(abs(delta.mean()))
        R_cross_list.append(np.mean(Rcross_trace))
    return np.mean(R_cross_list)

# Setup
N_per = 30
K0 = 2.0
alpha = 2.0
sigma = 0.1
T = 40.0
dt = 0.05
trans = 15.0
n_seeds = 5

omega_seq = np.arange(0.5, 5.5, 0.5)
R_cross = np.array([measure_R_cross(omega, K0, alpha, sigma, T, dt, trans, N_per, n_seeds)
                    for omega in omega_seq])

# Fit gamma
log_o = np.log(omega_seq)
log_R = np.log(R_cross + 1e-6)
gamma_fit, log_R0 = np.polyfit(log_o, log_R, 1)

# Plot
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].loglog(omega_seq, R_cross, 'bo-', label='simulated R_cross')
axes[0].loglog(omega_seq, np.exp(log_R0) * omega_seq**gamma_fit, 'r--',
               label=f'fit: gamma={gamma_fit:.3f}')
axes[0].set_xlabel('Delta_omega')
axes[0].set_ylabel('R_cross')
axes[0].set_title(f'gamma exponent (symmetric two-cluster, alpha={alpha}, K0={K0})')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(omega_seq, R_cross, 'bo-')
axes[1].set_xlabel('Delta_omega (linear)')
axes[1].set_ylabel('R_cross (linear)')
axes[1].set_title('R_cross linear plot')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/syn030_gamma_meta_analysis.png', dpi=110)
print(f"With n_seeds={n_seeds}, symmetric two-cluster, alpha={alpha}, K0={K0}, sigma={sigma}:")
print(f"  gamma_fit = {gamma_fit:.4f}")
print(f"  log_R0    = {log_R0:.4f}")
print(f"  R_cross range: [{R_cross.min():.4f}, {R_cross.max():.4f}]")
print("\nTheoretical interpretations:")
print("  - If gamma ~ 1.38: supports DOSSIER_003 / EMP-013 (universal scaling)")
print("  - If gamma ~ 0:    supports EMP-029 (no power-law decay in symmetric setup)")
print(f"  - Observed gamma={gamma_fit:.3f} -> ", end="")
if abs(gamma_fit) < 0.1:
    print("NO power-law decay; supports EMP-029.")
elif 1.0 < gamma_fit < 1.8:
    print("Power-law decay detected; supports Dossier_003.")
else:
    print("Ambiguous scaling.")
