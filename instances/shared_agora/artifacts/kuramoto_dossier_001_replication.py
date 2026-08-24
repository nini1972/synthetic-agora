"""
Optimized vectorized simulation of Kuramoto Oscillator Criticality & Hysteresis
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_simulation_fast(N=100, K0_vals=np.linspace(0.5, 5.0, 20), alpha=2.0, sigma=0.02, 
                             dist='gaussian', gamma=1.0, dt=0.05, T_settle=30.0, T_measure=15.0):
    np.random.seed(42)
    
    if dist == 'gaussian':
        omega = np.random.normal(0, gamma, N)
    else:
        u = np.random.uniform(0.05, 0.95, N)
        omega = gamma * np.tan(np.pi * (u - 0.5))
        
    steps_settle = int(T_settle / dt)
    steps_meas = int(T_measure / dt)
    
    forward_R = []
    backward_R = []
    
    # Forward Sweep (incoherent init)
    theta = np.random.uniform(-np.pi, np.pi, N)
    for K0 in K0_vals:
        for _ in range(steps_settle):
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            psi = np.angle(z)
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta)
            noise = sigma * np.sqrt(dt) * np.random.randn(N)
            theta = theta + dtheta * dt + noise
            
        R_samples = []
        for _ in range(steps_meas):
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            psi = np.angle(z)
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta)
            noise = sigma * np.sqrt(dt) * np.random.randn(N)
            theta = theta + dtheta * dt + noise
            R_samples.append(R)
        forward_R.append(np.mean(R_samples))
        
    # Backward Sweep (coherent init)
    theta = np.zeros(N)
    for K0 in reversed(K0_vals):
        for _ in range(steps_settle):
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            psi = np.angle(z)
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta)
            noise = sigma * np.sqrt(dt) * np.random.randn(N)
            theta = theta + dtheta * dt + noise
            
        R_samples = []
        for _ in range(steps_meas):
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            psi = np.angle(z)
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta)
            noise = sigma * np.sqrt(dt) * np.random.randn(N)
            theta = theta + dtheta * dt + noise
            R_samples.append(R)
        backward_R.append(np.mean(R_samples))
    backward_R.reverse()
    
    return np.array(forward_R), np.array(backward_R)

def main():
    K0_vals = np.linspace(0.5, 5.0, 20)
    print("Running Linear Kuramoto (alpha=0)...")
    f_lin, b_lin = kuramoto_simulation_fast(alpha=0.0, K0_vals=K0_vals)
    print("Running Non-linear Kuramoto (alpha=1)...")
    f_nl1, b_nl1 = kuramoto_simulation_fast(alpha=1.0, K0_vals=K0_vals)
    print("Running Strong Feedback (alpha=2)...")
    f_nl2, b_nl2 = kuramoto_simulation_fast(alpha=2.0, K0_vals=K0_vals)
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    
    # 1. Linear Control
    axes[0].plot(K0_vals, f_lin, 'o-', color='#3498db', label='Forward Sweep')
    axes[0].plot(K0_vals, b_lin, 's--', color='#e74c3c', label='Backward Sweep')
    axes[0].set_title("Standard Linear ($K = K_0$)\nContinuous / 2nd-Order", fontweight='bold')
    axes[0].set_xlabel("Coupling $K_0$")
    axes[0].set_ylabel("Order Parameter $R$")
    axes[0].grid(True, linestyle='--', alpha=0.6)
    axes[0].legend()
    
    # 2. Alpha = 1
    axes[1].plot(K0_vals, f_nl1, 'o-', color='#3498db', label='Forward Sweep')
    axes[1].plot(K0_vals, b_nl1, 's--', color='#e74c3c', label='Backward Sweep')
    axes[1].set_title(r"Adaptive Feedback ($K = K_0 \cdot R$)" + "\nDiscontinuous First-Order Hysteresis", fontweight='bold')
    axes[1].set_xlabel("Coupling $K_0$")
    axes[1].set_ylabel("Order Parameter $R$")
    axes[1].grid(True, linestyle='--', alpha=0.6)
    axes[1].legend()
    
    # 3. Alpha = 2
    axes[2].plot(K0_vals, f_nl2, 'o-', color='#3498db', label='Forward Sweep')
    axes[2].plot(K0_vals, b_nl2, 's--', color='#e74c3c', label='Backward Sweep')
    axes[2].set_title(r"High-Order Feedback ($K = K_0 \cdot R^2$)" + "\nSubcritical Bistability", fontweight='bold')
    axes[2].set_xlabel("Coupling $K_0$")
    axes[2].set_ylabel("Order Parameter $R$")
    axes[2].grid(True, linestyle='--', alpha=0.6)
    axes[2].legend()
    
    plt.suptitle("Inter-World Dossier #001: Kuramoto Resonance Criticality & Hysteresis Verification", 
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    out_path = "../../shared_agora/artifacts/kuramoto_dossier_001_replication.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Artifact successfully saved to {out_path}")
    print(f"Alpha=1 Max Hysteresis Gap: {np.max(b_nl1 - f_nl1):.4f}")
    print(f"Alpha=2 Max Hysteresis Gap: {np.max(b_nl2 - f_nl2):.4f}")

if __name__ == '__main__':
    main()
