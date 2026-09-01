"""
Replication: EMP-029 (Multi-Timescale R_cross Power Law Refutation)
================================================================
Purpose: Verify the claim that R_cross(Δω) is FLAT (γ ~ 0) in a two-cluster Kuramoto model.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_r_cross_verification():
    np.random.seed(42)
    N_per = 30  # Oscillators per cluster
    N = 2 * N_per
    dt = 0.05
    T = 40
    steps = int(T / dt)
    
    # Regime A: alpha=2, Gaussian intra-cluster dispersion, sigma=0.1, K0=2.0
    alpha = 2.0
    sigma_intra = 0.1
    K0 = 2.0
    
    # Frequency gap range
    delta_omega_vals = np.linspace(0.1, 3.0, 20)
    R_cross_vals = []
    
    for delta_omega in delta_omega_vals:
        # Two clusters: +delta_omega/2 and -delta_omega/2
        omega = np.zeros(N)
        omega[:N_per] = delta_omega / 2 + np.random.normal(0, sigma_intra, N_per)
        omega[N_per:] = -delta_omega / 2 + np.random.normal(0, sigma_intra, N_per)
        
        # Random initial phases
        theta = np.random.uniform(-np.pi, np.pi, N)
        
        # Simulate
        for _ in range(steps):
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            psi = np.angle(z)
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta)
            theta += dtheta * dt
        
        # Compute R_cross: |<exp(i(phi_fast - phi_slow))>|
        z_fast = np.mean(np.exp(1j * theta[:N_per]))
        z_slow = np.mean(np.exp(1j * theta[N_per:]))
        R_cross = np.abs(z_fast * np.conj(z_slow))
        R_cross_vals.append(R_cross)
    
    # Fit power law: log(R_cross) = log(C) - gamma * log(delta_omega)
    log_dw = np.log(delta_omega_vals)
    log_R = np.log(R_cross_vals)
    A = np.vstack([-log_dw, np.ones_like(log_dw)]).T
    gamma, log_C = np.linalg.lstsq(A, log_R, rcond=None)[0]
    
    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(delta_omega_vals, R_cross_vals, 'o-', color='#e74c3c', label=f'R_cross (γ_fit = {gamma:.4f})')
    plt.plot(delta_omega_vals, np.exp(log_C) * delta_omega_vals ** (-gamma), '--', color='#2980b9', label=f'Fit: γ = {gamma:.4f}')
    plt.xlabel("Frequency Gap Δω", fontsize=12)
    plt.ylabel("R_cross = |<exp(i(φ_fast - φ_slow))>|", fontsize=12)
    plt.title("Two-Cluster Kuramoto: R_cross vs Δω (Regime A: α=2, Gaussian)", fontsize=14, fontweight='bold')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(fontsize=10)
    plt.tight_layout()
    
    out_path = "../../shared_agora/artifacts/verify_emp029_r_cross.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Replication complete. Plot saved to {out_path}")
    print(f"Fitted γ = {gamma:.4f} (should be ~0 for flat R_cross)")

if __name__ == '__main__':
    run_r_cross_verification()