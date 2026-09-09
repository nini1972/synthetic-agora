import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def simulate_kuramoto_explosive(N, K0, alpha=0.6, sigma=0.008, dt=0.05, steps=600, clustered=False, n_clusters=4):
    np.random.seed(None)
    # Natural frequencies
    omega = np.random.normal(0, 1.0, N)
    
    # Phase initialization
    if clustered:
        # Assign to distinct cluster centers
        centers = np.linspace(-np.pi, np.pi, n_clusters, endpoint=False)
        cluster_assignment = np.random.choice(n_clusters, size=N)
        theta = centers[cluster_assignment] + np.random.normal(0, 0.15, N)
    else:
        theta = np.random.uniform(-np.pi, np.pi, N)
        
    for step in range(steps):
        # Order parameter R e^{i psi}
        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        psi = np.angle(z)
        
        K_eff = K0 * (R ** alpha)
        
        # Mean field approximation for speed: (K/N) sum sin(theta_j - theta_i) = K * R * sin(psi - theta_i)
        dtheta = omega + K_eff * R * np.sin(psi - theta)
        
        noise = sigma * np.sqrt(dt) * np.random.normal(0, 1.0, N) if sigma > 0 else 0
        theta = theta + dtheta * dt + noise
        
    # Measure final R over last 50 steps
    final_R = []
    for step in range(50):
        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        psi = np.angle(z)
        K_eff = K0 * (R ** alpha)
        dtheta = omega + K_eff * R * np.sin(psi - theta)
        noise = sigma * np.sqrt(dt) * np.random.normal(0, 1.0, N) if sigma > 0 else 0
        theta = theta + dtheta * dt + noise
        final_R.append(R)
        
    return np.mean(final_R)

def sweep_Kc(N_list, seeds_per_N=8):
    K0_grid = np.linspace(0.4, 3.2, 29)
    results = {}
    
    print("Starting Finite-Size Scaling sweep...")
    for N in N_list:
        kc_seeds = []
        for s in range(seeds_per_N):
            r_curve = []
            for K0 in K0_grid:
                r_val = simulate_kuramoto_explosive(N, K0, alpha=0.6, sigma=0.008, dt=0.05, steps=500, clustered=False)
                r_curve.append(r_val)
            r_curve = np.array(r_curve)
            # Find smallest K0 where R > 0.5
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

def test_cluster_resistance(N=100, seeds=10):
    K0_grid = np.linspace(0.5, 3.0, 26)
    r_unif_all = []
    r_clust_all = []
    
    for s in range(seeds):
        r_unif = [simulate_kuramoto_explosive(N, K0, alpha=0.6, sigma=0.008, dt=0.05, steps=500, clustered=False) for K0 in K0_grid]
        r_clust = [simulate_kuramoto_explosive(N, K0, alpha=0.6, sigma=0.008, dt=0.05, steps=500, clustered=True, n_clusters=4) for K0 in K0_grid]
        r_unif_all.append(r_unif)
        r_clust_all.append(r_clust)
        
    return K0_grid, np.mean(r_unif_all, axis=0), np.mean(r_clust_all, axis=0)

if __name__ == "__main__":
    N_list = [20, 40, 80, 150, 300, 600, 1000]
    scaling_data = sweep_Kc(N_list, seeds_per_N=8)
    
    # Fit power law log(Kc) = log(A) + beta * log(N)
    log_N = np.log([n for n in N_list])
    log_Kc = np.log([scaling_data[n]['mean'] for n in N_list])
    fit = np.polyfit(log_N, log_Kc, 1)
    beta = fit[0]
    A = np.exp(fit[1])
    
    print(f"Fitted Power Law: Kc(N) = {A:.3f} * N^{beta:.3f}")
    
    # Test cluster resistance
    K0_grid, r_unif, r_clust = test_cluster_resistance(N=150, seeds=8)
    
    # Plotting
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=150)
    
    # Subplot 1: Finite Size Scaling
    N_arr = np.array(N_list)
    Kc_means = np.array([scaling_data[n]['mean'] for n in N_list])
    Kc_stds = np.array([scaling_data[n]['std'] for n in N_list])
    
    axes[0].errorbar(N_arr, Kc_means, yerr=Kc_stds, fmt='o', color='#1f77b4', ecolor='#aec7e8', elinewidth=2, capsize=4, label='Empirical Simulation (World B)')
    N_dense = np.linspace(15, 1200, 200)
    axes[0].plot(N_dense, A * (N_dense**beta), 'r--', label=f'Fit: $K_c(N) = {A:.3f} N^{{{beta:.3f}}}$')
    axes[0].plot(N_dense, 0.496 * (N_dense**0.235), 'g:', label='World A Dossier #009: $0.496 N^{0.235}$')
    axes[0].axhspan(1.40, 1.82, color='orange', alpha=0.15, label='Agora Ratified Band [1.40, 1.82]')
    axes[0].set_xscale('log')
    axes[0].set_yscale('log')
    axes[0].set_xlabel('Population Size N (log scale)')
    axes[0].set_ylabel('Critical Coupling $K_c$ (log scale)')
    axes[0].set_title('Finite-Size Scaling Law: $K_c(N) \sim N^\\beta$')
    axes[0].grid(True, which="both", ls="--", alpha=0.4)
    axes[0].legend(loc='upper left', fontsize=8.5)
    
    # Subplot 2: Real-Cluster Resistance Effect
    axes[1].plot(K0_grid, r_unif, 'o-', color='#2ca02c', label='Uniform Random Initialization')
    axes[1].plot(K0_grid, r_clust, 's-', color='#d62728', label='4-Cluster Latent Structure')
    axes[1].axhline(0.5, color='gray', linestyle=':', label='Synchronization Threshold $R=0.5$')
    axes[1].set_xlabel('Feedback Coupling Amplitude $K_0$')
    axes[1].set_ylabel('Asymptotic Order Parameter $R$')
    axes[1].set_title('Real-Cluster Resistance Effect ($N=150$)')
    axes[1].grid(True, ls="--", alpha=0.4)
    axes[1].legend(loc='lower right', fontsize=8.5)
    
    plt.tight_layout()
    plt.savefig('shared_agora/artifacts/hyp019_finite_size_scaling_kuramoto.png')
    
    # Save JSON summary
    out_json = {
        'scaling_fit': {'A': float(A), 'beta': float(beta)},
        'data': scaling_data,
        'dossier_009_comparison': {
            'world_a_A': 0.496,
            'world_a_beta': 0.235,
            'concurrence': bool(abs(beta - 0.235) < 0.05)
        }
    }
    with open('shared_agora/artifacts/hyp019_finite_size_scaling_kuramoto.json', 'w') as f:
        json.dump(out_json, f, indent=2)
    print("Execution complete. Artifacts saved successfully.")
