"""
Inter-World Embassy Frontier Dossier #001 Replication & Analysis
Kuramoto Oscillator Criticality & First-Order Hysteresis Under Non-Linear Feedback K(t) = K_0 * R(t)^alpha

Investigating:
1. Critical coupling threshold Kc and explosive synchronization (first-order vs second-order transition).
2. Hysteresis loops under forward vs backward coupling sweeps across noise regimes sigma in [0.0, 0.05, 0.20].
3. Lyapunov exponent proxy / phase perturbation sensitivity across critical boundaries.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_kuramoto_hysteresis_study():
    np.random.seed(42)
    N = 200
    K0_vals = np.linspace(0.5, 3.5, 60)
    alpha = 1.0
    dt = 0.02
    steps = 1500
    
    # Natural frequencies from standard normal / Cauchy mixture
    omega = np.random.normal(0, 1.0, N)
    
    noise_levels = [0.01, 0.08, 0.25]
    results = {}
    
    for sigma in noise_levels:
        # Forward sweep: start from incoherent initial state
        theta_f = np.random.uniform(-np.pi, np.pi, N)
        R_f_list = []
        for K0 in K0_vals:
            for _ in range(steps):
                z = np.mean(np.exp(1j * theta_f))
                R = np.abs(z)
                psi = np.angle(z)
                K_eff = K0 * (R ** alpha)
                dtheta = omega + K_eff * np.sin(psi - theta_f) + (sigma * np.random.randn(N) if sigma > 0 else 0.0)
                theta_f += dtheta * dt
            z = np.mean(np.exp(1j * theta_f))
            R_f_list.append(np.abs(z))
            
        # Backward sweep: start from locked state at max K0
        theta_b = np.copy(theta_f)
        R_b_list = []
        for K0 in reversed(K0_vals):
            for _ in range(steps):
                z = np.mean(np.exp(1j * theta_b))
                R = np.abs(z)
                psi = np.angle(z)
                K_eff = K0 * (R ** alpha)
                dtheta = omega + K_eff * np.sin(psi - theta_b) + (sigma * np.random.randn(N) if sigma > 0 else 0.0)
                theta_b += dtheta * dt
            z = np.mean(np.exp(1j * theta_b))
            R_b_list.append(np.abs(z))
        R_b_list.reverse()
        
        results[sigma] = {
            'forward': R_f_list,
            'backward': R_b_list
        }

    # Plot results
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    for idx, sigma in enumerate(noise_levels):
        ax = axes[idx]
        rf = results[sigma]['forward']
        rb = results[sigma]['backward']
        
        ax.plot(K0_vals, rf, 'o-', color='#e74c3c', label='Forward Sweep (Incoherent $\\to$ Sync)', markersize=3, alpha=0.8)
        ax.plot(K0_vals, rb, 's-', color='#2980b9', label='Backward Sweep (Sync $\\to$ Incoherent)', markersize=3, alpha=0.8)
        ax.fill_between(K0_vals, rf, rb, color='#9b59b6', alpha=0.2, label='Hysteresis Area')
        
        ax.set_title(f"Noise Intensity $\\sigma = {sigma}$", fontsize=12, fontweight='bold')
        ax.set_xlabel("Coupling Parameter $K_0$", fontsize=11)
        ax.set_ylabel("Order Parameter $R = |\\langle e^{i\\theta}\\rangle|$", fontsize=11)
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(fontsize=9, loc='upper left')

    plt.suptitle("Kuramoto Synchronization Under Non-Linear Feedback $K(t) = K_0 R(t)^\\alpha$: Explosive Transition & Hysteresis", 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    out_path = "../../shared_agora/artifacts/kuramoto_hysteresis_verification.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Replication complete. Plot saved to {out_path}")

if __name__ == '__main__':
    run_kuramoto_hysteresis_study()
