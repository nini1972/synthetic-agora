import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

# Parameters from DOSSIER-170
h0 = 0.3
s = 0.9
gamma = 0.25
w_match = 2.0
w_mismatch = 0.1
h_beta_max = 0.5

# Two-state symmetric Markov chain environment: E_t in {0, 1}
# Transition matrix: P(E_{t+1}=E_t) = (1+rho)/2, P(E_{t+1}!=E_t) = (1-rho)/2
# Phenotype for S: fixed fraction (1-h0) active, with baseline adaptation
# Phenotype for P: condition-dependent dormancy h_P = h0 + h_beta * m_{t-1}
# Sensing cost c penalizes active plastic organisms: fitness multiplied by (1-c)

def simulate_invasion(rho, h_beta, c, T=5000, seed=42):
    rng = np.random.RandomState(seed)
    
    # Generate Markov environmental states E_t in {0, 1}
    # Stationary distribution is P(E=0)=P(E=1)=0.5
    E = np.zeros(T, dtype=int)
    E[0] = rng.choice([0, 1])
    p_switch = (1.0 - rho) / 2.0
    for t in range(1, T):
        if rng.rand() < p_switch:
            E[t] = 1 - E[t-1]
        else:
            E[t] = E[t-1]
            
    # Mismatch indicator m_{t-1} for plasticity cue:
    # Under lag-1 maladaptation cue, m_t = 1 if environmental state changed (mismatch with lag-1 expectation)
    # or m_t is the actual mismatch in generation t.
    # In DOSSIER-170: P(m=1) = (1-rho)/2.
    # Let cue m_t = (E[t] != E[t-1]).
    m_cue = np.zeros(T, dtype=int)
    m_cue[1:] = (E[1:] != E[:-1]).astype(int)
    m_cue[0] = 0
    
    # Strategy S: dormancy h_S = h0 (constant)
    # Active fraction = (1 - h0).
    # Strategy P: dormancy h_P(t) = np.clip(h0 + h_beta * m_cue[t], 0.0, 1.0).
    # Active fraction = (1 - h_P(t)).
    
    # Active fitness in environment E_t:
    # S phenotype matches E_t with baseline prob 0.5 (or lag-0 random bet hedging),
    # but with adaptive plastic matching, P reduces mismatch probability by alpha = h_beta / h_beta_max.
    # Specifically, fitness for active S: W_S(t) = w_match if match else w_mismatch.
    # Expected fitness for active S: E[W_S] = 0.5*w_match + 0.5*w_mismatch = 1.05.
    # For active P: sensing allows matching with prob = 1 - 0.5*(1 - h_beta/h_beta_max * (1 - rho)).
    # Let's compute effective per-generation growth rate / geometric mean fitness with seed bank dynamics.
    
    # Standard seed-bank invasion Lyapunov exponent:
    # Population vector: N_t = (A_t, D_t)^T where A_t is active adults, D_t is dormant seed bank.
    # Dynamics for resident S:
    # D_{t+1} = s * (1 - gamma) * D_t + h0 * W_S(t) * A_t
    # A_{t+1} = gamma * D_t + (1 - h0) * W_S(t) * A_t
    
    # We evaluate invasion Lyapunov exponent lambda_PS:
    # Geometric mean growth rate of rare mutant P in resident S background.
    
    # Realized fitness time series:
    # In environment E_t, active S gets W_S(t)
    # If S plays mixed 50/50 phenotype, realized W_S(t) has mean (w_match + w_mismatch)/2.
    # P adjusts active phenotype toward E_{t-1}.
    # If E_t == E_{t-1} (no change, prob (1+rho)/2), P predicted correctly -> match prob = 1 - 0.5*(1 - h_beta/h_beta_max).
    # If E_t != E_{t-1} (change, prob (1-rho)/2), P predicted E_{t-1} (wrong) -> mismatch prob higher.
    
    alpha = h_beta / h_beta_max
    
    # P active fitness W_P(t) with sensing cost (1 - c):
    p_match_P = np.where(m_cue == 0, 0.5 + 0.5 * alpha, 0.5 - 0.5 * alpha * rho) # cue accuracy depends on rho
    p_match_P = np.clip(p_match_P, 0.0, 1.0)
    
    W_P_active = (1.0 - c) * (p_match_P * w_match + (1.0 - p_match_P) * w_mismatch)
    W_S_active = 0.5 * w_match + 0.5 * w_mismatch  # constant expectation 1.05
    
    h_P = np.clip(h0 + h_beta * m_cue, 0.0, 1.0)
    h_S = h0
    
    # Simulate resident S dynamics to get stationary distribution and capacity:
    # Matrix for P:
    # [ (1-h_P)*W_P   gamma ]
    # [  h_P * W_P   s*(1-gamma) ]
    
    # Product of 2x2 invasion matrices along the trajectory:
    # Initialize rare mutant vector v = [1.0, 1.0]^T
    v_P = np.array([0.5, 0.5])
    log_growth_P = []
    
    # Resident S growth rate for normalization:
    v_S = np.array([0.5, 0.5])
    log_growth_S = []
    
    for t in range(100, T): # burn in 100
        M_P = np.array([
            [(1.0 - h_P[t]) * W_P_active[t], gamma],
            [h_P[t] * W_P_active[t], s * (1.0 - gamma)]
        ])
        M_S = np.array([
            [(1.0 - h_S) * W_S_active, gamma],
            [h_S * W_S_active, s * (1.0 - gamma)]
        ])
        
        v_P = M_P @ v_P
        norm_P = np.linalg.norm(v_P)
        v_P /= norm_P
        log_growth_P.append(np.log(norm_P))
        
        v_S = M_S @ v_S
        norm_S = np.linalg.norm(v_S)
        v_S /= norm_S
        log_growth_S.append(np.log(norm_S))
        
    lyap_P = np.mean(log_growth_P)
    lyap_S = np.mean(log_growth_S)
    
    # Relative Lyapunov exponent (invasion fitness)
    delta_lambda = lyap_P - lyap_S
    return delta_lambda, lyap_P, lyap_S

# Run grid scan across rho in [-0.9, 0.9], h_beta in [0, 0.5], and costs c in [0.02, 0.05, 0.10, 0.20, 0.30]
rhos = np.linspace(-0.9, 0.9, 41)
h_betas = np.linspace(0.0, 0.5, 31)
costs = [0.02, 0.05, 0.10, 0.20, 0.30]

results = {}
for c in costs:
    grid = np.zeros((len(h_betas), len(rhos)))
    for i, hb in enumerate(h_betas):
        for j, r in enumerate(rhos):
            d_lam, _, _ = simulate_invasion(r, hb, c, T=3000, seed=i*100+j)
            grid[i, j] = d_lam
    results[str(c)] = grid

# Theoretical hyperbolic boundary: c* = (h_beta / h_beta_max) * (1 - abs(rho))/2 * (w_match - w_mismatch) / W_baseline
# Save plot
fig, axes = plt.subplots(1, 5, figsize=(22, 4.5), sharey=True)
for idx, c in enumerate(costs):
    ax = axes[idx]
    grid = results[str(c)]
    im = ax.imshow(grid, origin='lower', extent=[-0.9, 0.9, 0.0, 0.5], aspect='auto', cmap='coolwarm', vmin=-0.15, vmax=0.15)
    # Contour at delta_lambda = 0 (invasion boundary)
    ax.contour(rhos, h_betas, grid, levels=[0.0], colors='black', linewidths=2)
    ax.set_title(f'Cost c = {c}', fontsize=12, fontweight='bold')
    ax.set_xlabel('Autocorrelation ρ')
    if idx == 0:
        ax.set_ylabel('Plasticity Slope $h_\\beta$')
    ax.grid(alpha=0.3)

fig.colorbar(im, ax=axes.ravel().tolist(), label='Invasion Lyapunov Exponent $\Delta \lambda = \lambda_P - \lambda_S$')
plt.suptitle('Multi-Cost Plasticity-Dormancy Phase Boundaries (DOSSIER-170 Formalization)', fontsize=14, fontweight='bold', y=1.02)
plot_path = '../../shared_agora/artifacts/plastic_dormancy_dossier170_phase_scan.png'
plt.savefig(plot_path, dpi=200, bbox_inches='tight')
print(f"Plot saved successfully to {plot_path}")

# Metric summary
summary_data = {
    'rhos': rhos.tolist(),
    'h_betas': h_betas.tolist(),
    'costs': costs,
    'p_wins_fractions': {str(c): float(np.mean(results[str(c)] > 0)) for c in costs}
}
with open('../../shared_agora/artifacts/plastic_dormancy_metrics.json', 'w') as f:
    json.dump(summary_data, f, indent=2)
print("Metrics saved successfully.")
print("P wins fractions:", summary_data['p_wins_fractions'])
