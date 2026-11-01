import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

# Vectorized simulation for DOSSIER-170
h0 = 0.3
s = 0.9
gamma = 0.25
w_match = 2.0
w_mismatch = 0.1
h_beta_max = 0.5

def run_vectorized_scan(costs, rhos, h_betas, T=1500, seed=42):
    rng = np.random.RandomState(seed)
    n_rho = len(rhos)
    n_hb = len(h_betas)
    
    # Generate Markov chains for all rhos simultaneously
    # E has shape (n_rho, T)
    E = np.zeros((n_rho, T), dtype=int)
    E[:, 0] = rng.choice([0, 1], size=n_rho)
    p_switch = (1.0 - rhos) / 2.0  # shape (n_rho,)
    
    rand_switches = rng.rand(n_rho, T)
    for t in range(1, T):
        switch = rand_switches[:, t] < p_switch
        E[:, t] = np.where(switch, 1 - E[:, t-1], E[:, t-1])
        
    m_cue = np.zeros((n_rho, T), dtype=int)
    m_cue[:, 1:] = (E[:, 1:] != E[:, :-1]).astype(int)
    
    # For each cost, compute the 2D grid of delta_lambda
    results = {}
    
    # Baseline active S fitness
    W_S_active = 0.5 * w_match + 0.5 * w_mismatch  # 1.05
    # S transition matrix M_S
    # [ (1-h0)*W_S   gamma ]
    # [  h0 * W_S   s*(1-gamma) ]
    M_S = np.array([
        [(1.0 - h0) * W_S_active, gamma],
        [h0 * W_S_active, s * (1.0 - gamma)]
    ])
    # Dominant eigenvalue of M_S is exact analytical Lyapunov exponent:
    evals_S = np.linalg.eigvals(M_S)
    lyap_S = np.log(np.max(evals_S))
    
    for c in costs:
        grid = np.zeros((n_hb, n_rho))
        for i_hb, hb in enumerate(h_betas):
            alpha = hb / h_beta_max
            # h_P has shape (n_rho, T)
            h_P = np.clip(h0 + hb * m_cue, 0.0, 1.0)
            
            # Match probability for P
            # shape (n_rho, T)
            p_match_P = np.where(m_cue == 0, 0.5 + 0.5 * alpha, 0.5 - 0.5 * alpha * rhos[:, None])
            p_match_P = np.clip(p_match_P, 0.0, 1.0)
            W_P_active = (1.0 - c) * (p_match_P * w_match + (1.0 - p_match_P) * w_mismatch)
            
            # Vectorized transfer matrix multiplication over time for each rho
            # v has shape (n_rho, 2)
            v = np.ones((n_rho, 2)) * 0.5
            log_growth = np.zeros(n_rho)
            
            # Burn-in
            burn = 50
            for t in range(T):
                # M_P for step t: shape (n_rho, 2, 2)
                a11 = (1.0 - h_P[:, t]) * W_P_active[:, t]
                a12 = np.full(n_rho, gamma)
                a21 = h_P[:, t] * W_P_active[:, t]
                a22 = np.full(n_rho, s * (1.0 - gamma))
                
                v_new0 = a11 * v[:, 0] + a12 * v[:, 1]
                v_new1 = a21 * v[:, 0] + a22 * v[:, 1]
                
                norms = np.sqrt(v_new0**2 + v_new1**2)
                v[:, 0] = v_new0 / norms
                v[:, 1] = v_new1 / norms
                
                if t >= burn:
                    log_growth += np.log(norms)
                    
            lyap_P = log_growth / (T - burn)
            grid[i_hb, :] = lyap_P - lyap_S
            
        results[str(c)] = grid
        
    return results

rhos = np.linspace(-0.9, 0.9, 51)
h_betas = np.linspace(0.0, 0.5, 41)
costs = [0.02, 0.05, 0.10, 0.20, 0.30]

print("Running fast vectorized phase scan...")
results = run_vectorized_scan(costs, rhos, h_betas, T=2000)

fig, axes = plt.subplots(1, 5, figsize=(22, 4.2), sharey=True)
for idx, c in enumerate(costs):
    ax = axes[idx]
    grid = results[str(c)]
    im = ax.imshow(grid, origin='lower', extent=[-0.9, 0.9, 0.0, 0.5], aspect='auto', cmap='coolwarm', vmin=-0.15, vmax=0.15)
    ax.contour(rhos, h_betas, grid, levels=[0.0], colors='black', linewidths=2)
    ax.set_title(f'Cost c = {c}', fontsize=12, fontweight='bold')
    ax.set_xlabel('Autocorrelation ρ')
    if idx == 0:
        ax.set_ylabel('Plasticity Slope $h_\\beta$')
    ax.grid(alpha=0.3)

fig.colorbar(im, ax=axes.ravel().tolist(), label='Invasion Lyapunov Exponent $\Delta \lambda = \lambda_P - \lambda_S$')
plt.suptitle('Multi-Cost Plasticity vs Dormancy Phase Diagram (DOSSIER-170 Formalization)', fontsize=14, fontweight='bold', y=1.02)
plot_path = '../../shared_agora/artifacts/plastic_dormancy_dossier170_phase_scan.png'
plt.savefig(plot_path, dpi=200, bbox_inches='tight')
print(f"Plot saved successfully to {plot_path}")

summary_data = {
    'rhos': rhos.tolist(),
    'h_betas': h_betas.tolist(),
    'costs': costs,
    'p_wins_fractions': {str(c): float(np.mean(results[str(c)] > 0)) for c in costs}
}
with open('../../shared_agora/artifacts/plastic_dormancy_metrics.json', 'w') as f:
    json.dump(summary_data, f, indent=2)
print("P wins fractions:", summary_data['p_wins_fractions'])
