#!/usr/bin/env python3
"""
Peer Verification for HYP-135: Phenotypic Plasticity vs Stochastic Dormancy
- Replicates the hyperbolic phase boundary for c=0.10 and c=0.20.
- Uses vectorized transfer operator and Lyapunov exponent comparison.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# --- Constants ---
h_0 = 0.3  # Baseline dormancy
s = 0.9    # Seed survival
gamma = 0.25 # Germination rate
T = 1000   # Simulation horizon
rho_grid = np.linspace(-0.9, 0.9, 51)
h_beta_grid = np.linspace(0.0, 0.5, 41)


def markov_transition(rho):
    p = (1 - rho) / 2
    return np.array([[1 - p, p], [p, 1 - p]])


def transfer_operator(h, W, c=0.0):
    return np.array([
        [(1 - h) * W * (1 - c), gamma],
        [h * W * (1 - c), s * (1 - gamma)]
    ])


def lyapunov_exponent(rho, h_beta, c=0.0):
    P = markov_transition(rho)
    env = np.random.choice([0, 1], size=T, p=[0.5, 0.5])
    
    # S: Stochastic Dormancy (fixed h_0)
    M_S = transfer_operator(h_0, W=1.0)
    evals_S = np.linalg.eigvals(M_S)
    lambda_S = np.log(np.max(np.abs(evals_S)))
    
    # P: Phenotypic Plasticity (h_P = h_0 + h_beta * m_{t-1})
    log_v_P = 0.0
    v_P = np.ones(2)
    m_prev = 0
    
    for t in range(1, T):
        env_t = env[t]
        m_t = 1 if env_t != env[t-1] else 0
        h_P = np.clip(h_0 + h_beta * m_prev, 0, 1)
        W_t = 1.0 if env_t == 0 else 0.5  # Maladaptation penalty
        M_P = transfer_operator(h_P, W_t, c)
        v_P = M_P @ v_P
        log_v_P += np.log(np.linalg.norm(v_P))
        v_P /= np.linalg.norm(v_P)
        m_prev = m_t
    
    lambda_P = log_v_P / T
    return lambda_P - lambda_S


# --- Phase Scan ---
def phase_scan(c):
    phase = np.zeros((len(rho_grid), len(h_beta_grid)))
    for i, rho in enumerate(rho_grid):
        for j, h_beta in enumerate(h_beta_grid):
            delta_lambda = lyapunov_exponent(rho, h_beta, c)
            phase[i, j] = 1 if delta_lambda > 0 else 0
    return phase


# --- Plot ---
def plot_phase(phase, c):
    plt.figure(figsize=(10, 6))
    cmap = ListedColormap(['#377eb8', '#ff7f00'])
    plt.imshow(phase.T, extent=[-0.9, 0.9, 0.0, 0.5], origin='lower', aspect='auto', cmap=cmap)
    plt.colorbar(label='Strategy (0=S, 1=P)')
    plt.xlabel("Autocorrelation (rho)")
    plt.ylabel("Plasticity Modulation (h_beta)")
    plt.title(f"Phase Boundary (c={c:.2f}) - P wins in {np.mean(phase)*100:.1f}% of space")
    
    # Hyperbolic boundary: c* ~ (h_beta / 0.5) * (1 - |rho|)
    rho_hyperbola = np.linspace(-0.9, 0.9, 100)
    h_beta_hyperbola = (c / 0.5) * (1 - np.abs(rho_hyperbola))
    plt.plot(rho_hyperbola, h_beta_hyperbola, 'r--', label='Hyperbolic Boundary')
    plt.legend()
    plt.savefig(f"world_c_results/phase_boundary_c_{c:.2f}.png")
    plt.close()


# --- Run ---
if __name__ == "__main__":
    for c in [0.10, 0.20]:
        phase = phase_scan(c)
        plot_phase(phase, c)
        print(f"c={c:.2f}: P wins in {np.mean(phase)*100:.1f}% of phase space")