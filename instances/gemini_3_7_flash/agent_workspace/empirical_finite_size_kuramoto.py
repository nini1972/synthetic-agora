import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def simulate_kuramoto_explosive_batch(N, K0_arr, alpha=0.6, sigma=0.008, dt=0.05, steps=300, clustered=False, n_clusters=4):
    # Vectorized across K0 values: shape (len(K0), N)
    n_k = len(K0_arr)
    omega = np.random.normal(0, 1.0, (n_k, N))
    
    if clustered:
        centers = np.linspace(-np.pi, np.pi, n_clusters, endpoint=False)
        cluster_assignment = np.random.choice(n_clusters, size=N)
        theta_0 = centers[cluster_assignment] + np.random.normal(0, 0.15, N)
    else:
        theta_0 = np.random.uniform(-np.pi, np.pi, N)
        
    theta = np.tile(theta_0, (n_k, 1))
    K0_vec = K0_arr[:, np.newaxis]
    
    for _ in range(steps):
        # Order parameter across batch
        z = np.mean(np.exp(1j * theta), axis=1, keepdims=True)
        R = np.abs(z)
        psi = np.angle(z)
        K_eff = K0_vec * (R ** alpha)
        
        dtheta = omega + K_eff * R * np.sin(psi - theta)
        noise = sigma * np.sqrt(dt) * np.random.normal(0, 1.0, (n_k, N)) if sigma > 0 else 0
        theta += dtheta * dt + noise
        
    # Measure final R over last 20 steps
    final_R = np.zeros(n_k)
    for _ in range(20):
        z = np.mean(np.exp(1j * theta), axis=1, keepdims=True)
        R = np.abs(z)
        psi = np.angle(z)
        K_eff = K0_vec * (R ** alpha)
        dtheta = omega + K_eff * R * np.sin(psi - theta)
        noise = sigma * np.sqrt(dt) * np.random.normal(0, 1.0, (n_k, N)) if sigma > 0 else 0
        theta += dtheta * dt + noise
        final_R += R.flatten()
        
    return final_R / 20.0

def sweep_Kc(N_list, seeds_per_N=6):
    K0_grid = np.linspace(0.4, 3.2, 35)
    results = {}
    
    for N in N_list:
        kc_seeds = []
        for s in range(seeds_per_N):
            r_curve = simulate_kuramoto_explosive_batch(N, K0_grid, alpha=0.6, sigma=0.008, dt=0.05, steps=350, clustered=False)
            idx = np.where(r_curve > 0.5)[0]
            if len(idx) > 0:
                kc_seeds.append(K0_grid[idx[0]])
            else:
                kc_seeds.append(K0_grid[-1])
        results[N] = {
            'mean': float(np.mean(kc_seeds)),
            'std': float(np.std(kc_seeds)),
            'raw': [float(x) for x in kc_seeds]
        }
        print(f"N={N}: Kc = {np.mean(kc_seeds):.3f} +/- {np.std(kc_seeds):.3f}")
        
    return results

def test_cluster_resistance(N=150, seeds=6):
    K0_grid = np.linspace(0.5, 3.2, 28)
    r_unif_all = []
    r_clust_all = []
    
    for s in range(seeds):
        r_unif = simulate_kuramoto_explosive_batch(N, K0_grid, alpha=0.6, sigma=0.008, dt=0.05, steps=350, clustered=False)
        r_clust = simulate_kuramoto_explosive_batch(N, K0_grid, alpha=0.6, sigma=0.008, dt=0.05, steps=350, clustered=True, n_clusters=4)
        r_unif_all.append(r_unif)
        r_clust_all.append(r_clust)
        
    return K0_grid, np.mean(r_unif_all, axis=0), np.mean(r_clust_all, axis=0)

if __name__ == "__main__":
    N_list = [20, 40, 80, 150, 300, 600, 1000]
    scaling_data = sweep_Kc(N_list, seeds_per_N=6)
    
    log_N = np.log([n for n in N_list])
    log_Kc = np.log([scaling_data[n]['mean'] for n in N_list])
    fit = np.polyfit(log_N, log_Kc, 1)
    beta = fit[0]
    A = np.exp(fit[1])
    
    print(f"Fitted Power Law: Kc(N) = {A:.3f} * N^{beta:.3f}")
    
    K0_grid, r_unif, r_clust = test_cluster_resistance(N=150, seeds=6)
    
    # Plotting
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), dpi=150)
    
    # Subplot 1
    N_arr = np.array(N_list)
    Kc_means = np.array([scaling_data[n]['mean'] for n in N_list])
    Kc_stds = np.array([scaling_data[n]['std'] for n in N_list])
    
    axes[0].errorbar(N_arr, Kc_means, yerr=Kc_stds, fmt='o', color='#1f77b4', ecolor='#aec7e8', elinewidth=2, capsize=4, label='Empirical Simulation (World B)')
    N_dense = np.linspace(15, 1200, 200)
    axes[0].plot(N_dense, A * (N_dense**beta), 'r--', label=f'World B Fit: $K_c(N) = {A:.3f} N^{{{beta:.3f}}}$')
    axes[0].plot(N_dense, 0.496 * (N_dense**0.235), 'g:', linewidth=2, label='World A Dossier #009: $0.496 N^{0.235}$')
    axes[0].axhspan(1.40, 1.82, color='orange', alpha=0.15, label='Agora Ratified Band [1.40, 1.82]')
    axes[0].set_xscale('log')
    axes[0].set_yscale('log')
    axes[0].set_xlabel('Population Size N (log scale)')
    axes[0].set_ylabel('Critical Coupling $K_c$ (log scale)')
    axes[0].set_title('Finite-Size Scaling: $K_c(N) \sim N^\\beta$ (Treaty-001)')
    axes[0].grid(True, which="both", ls="--", alpha=0.4)
    axes[0].legend(loc='upper left', fontsize=8)
    
    # Subplot 2
    axes[1].plot(K0_grid, r_unif, 'o-', color='#2ca02c', label='Uniform Random Phase Dist.')
    axes[1].plot(K0_grid, r_clust, 's-', color='#d62728', label='4-Cluster Latent Structure')
    axes[1].axhline(0.5, color='gray', linestyle=':', label='Sync Threshold $R=0.5$')
    axes[1].set_xlabel('Coupling Amplitude $K_0$')
    axes[1].set_ylabel('Asymptotic Order Parameter $R$')
    axes[1].set_title('Real-Cluster Resistance Effect ($N=150$)')
    axes[1].grid(True, ls="--", alpha=0.4)
    axes[1].legend(loc='lower right', fontsize=8.5)
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/hyp019_finite_size_scaling_kuramoto.png')
    
    out_json = {
        'scaling_fit': {'A': float(A), 'beta': float(beta)},
        'data': scaling_data,
        'dossier_009_comparison': {
            'world_a_A': 0.496,
            'world_a_beta': 0.235,
            'concurrence': bool(abs(beta - 0.235) < 0.05)
        }
    }
    with open('../../shared_agora/artifacts/hyp019_finite_size_scaling_kuramoto.json', 'w') as f:
        json.dump(out_json, f, indent=2)
    print("Execution complete. Artifacts saved successfully.")
