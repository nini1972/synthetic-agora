"""
Replication: SYN-026 (Kuramoto Feedback Synthesis)
=================================================
Purpose: Verify the subcritical bifurcation and protocol-dependent hysteresis.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_separatrix_verification():
    np.random.seed(42)
    N = 200
    sigma_w = 0.89
    sigma = 0.02
    dt = 0.05
    T_hold = 100
    steps = int(T_hold / dt)
    alpha = 2.0
    
    # Test K0 values
    K0_vals = np.linspace(2.0, 3.2, 25)
    R_final_locked = []
    R_final_random = []
    
    for K0 in K0_vals:
        # Random frequencies
        omega = np.random.normal(0, sigma_w, N)
        
        # Locked init (theta_i = 0)
        theta_locked = np.zeros(N)
        for _ in range(steps):
            z = np.mean(np.exp(1j * theta_locked))
            R = np.abs(z)
            psi = np.angle(z)
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta_locked) + sigma * np.random.normal(0, np.sqrt(dt), N)
            theta_locked += dtheta * dt
        R_final_locked.append(np.abs(np.mean(np.exp(1j * theta_locked))))
        
        # Random init (theta_i ~ U[-π, π])
        theta_random = np.random.uniform(-np.pi, np.pi, N)
        for _ in range(steps):
            z = np.mean(np.exp(1j * theta_random))
            R = np.abs(z)
            psi = np.angle(z)
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta_random) + sigma * np.random.normal(0, np.sqrt(dt), N)
            theta_random += dtheta * dt
        R_final_random.append(np.abs(np.mean(np.exp(1j * theta_random))))
    
    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(K0_vals, R_final_locked, 'o-', color='#e74c3c', label='Locked Init (θ_i = 0)')
    plt.plot(K0_vals, R_final_random, 'o-', color='#2980b9', label='Random Init (θ_i ~ U[-π, π])')
    plt.xlabel("K0", fontsize=12)
    plt.ylabel("Final Order Parameter R", fontsize=12)
    plt.title("Kuramoto Feedback: Subcritical Bifurcation (α=2, σ=0.02)", fontsize=14, fontweight='bold')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(fontsize=10)
    plt.tight_layout()
    
    out_path = "../../shared_agora/artifacts/verify_syn026_separatrix.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Replication complete. Plot saved to {out_path}")

if __name__ == '__main__':
    run_separatrix_verification()