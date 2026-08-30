"""
Updated Replication: Kuramoto Hysteresis Under α=2 and σ ∈ [0, 0.5]
================================================================
Purpose: Verify the hysteresis claim in HYP-009 (K_c ≈ 1.42, α=2, σ ∈ [0, 0.5]).
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_kuramoto_hysteresis_study():
    np.random.seed(42)
    N = 200
    K0_vals = np.linspace(1.0, 2.0, 60)  # Focus on K_c ≈ 1.42
    alpha = 2.0  # Updated to match HYP-009 claim
    dt = 0.02
    steps = 1500
    
    # Natural frequencies from standard normal
    omega = np.random.normal(0, 1.0, N)
    
    noise_levels = [0.0, 0.1, 0.2, 0.5]  # Updated to match HYP-009 claim
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
    fig, axes = plt.subplots(1, 4, figsize=(24, 5))
    
    for idx, sigma in enumerate(noise_levels):
        ax = axes[idx]
        rf = results[sigma]['forward']
        rb = results[sigma]['backward']
        
        ax.plot(K0_vals, rf, 'o-', color='#e74c3c', label='Forward Sweep', markersize=3, alpha=0.8)
        ax.plot(K0_vals, rb, 's-', color='#2980b9', label='Backward Sweep', markersize=3, alpha=0.8)
        ax.fill_between(K0_vals, rf, rb, color='#9b59b6', alpha=0.2, label='Hysteresis Area')
        
        ax.set_title(f"Noise $\sigma = {sigma}$", fontsize=12, fontweight='bold')
        ax.set_xlabel("$K_0$", fontsize=11)
        ax.set_ylabel(r"Order Parameter $R = |\langle e^{i\theta} \rangle|$", fontsize=11)
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(fontsize=9, loc='upper left')
        
        # Mark K_c ≈ 1.42
        ax.axvline(x=1.42, color='k', linestyle='--', alpha=0.7, label='$K_c \approx 1.42$')
    
    plt.suptitle("Kuramoto Hysteresis Under $K(t) = K_0 R(t)^2$ (α=2): Focus on $K_c \approx 1.42$", 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    out_path = "../../shared_agora/artifacts/kuramoto_hysteresis_verification_updated.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Updated replication complete. Plot saved to {out_path}")

if __name__ == '__main__':
    run_kuramoto_hysteresis_study()