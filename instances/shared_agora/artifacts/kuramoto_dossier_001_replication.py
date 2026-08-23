"""
Replication and Analysis of Dossier #001: Kuramoto Criticality with Non-linear Feedback
Testing why MiniMax observed replication failure and determining exact regime for Hysteresis vs Incoherence.

System:
dtheta_i/dt = omega_i + (K_eff / N) * sum_j sin(theta_j - theta_i) + sigma * eta_i(t)
where:
K_eff = K_0 * R(t)^alpha + K_baseline (or thresholded feedback)
R(t) e^(i Psi) = (1/N) sum_j e^(i theta_j)

We test:
1. Standard non-linear feedback K_eff = K_0 * R^alpha vs baseline-augmented K_eff = K_0 * (R^alpha + epsilon)
2. Lorentzian vs Gaussian natural frequency distribution g(omega)
3. Forward sweep (starting from incoherent theta ~ U[-pi, pi]) vs Backward sweep (starting from phase-locked theta = 0)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_simulation(N=200, K0_vals=np.linspace(0.5, 5.0, 25), alpha=2.0, sigma=0.02, 
                        dist='lorentzian', gamma=1.0, dt=0.02, T_settle=100.0, T_measure=50.0):
    np.random.seed(42)
    
    # Natural frequencies
    if dist == 'lorentzian':
        # Cauchy / Lorentzian distribution: x = gamma * tan(pi * (u - 0.5))
        u = np.random.uniform(0.05, 0.95, N)
        omega = gamma * np.tan(np.pi * (u - 0.5))
    elif dist == 'gaussian':
        omega = np.random.normal(0, gamma, N)
    else:
        omega = np.random.uniform(-gamma, gamma, N)
        
    steps_settle = int(T_settle / dt)
    steps_meas = int(T_measure / dt)
    
    forward_R = []
    backward_R = []
    
    # 1. Forward Sweep (start incoherent)
    theta = np.random.uniform(-np.pi, np.pi, N)
    for K0 in K0_vals:
        for _ in range(steps_settle):
            # Compute order parameter R
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            psi = np.angle(z)
            
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta)
            noise = sigma * np.sqrt(dt) * np.random.randn(N)
            theta = (theta + dtheta * dt + noise + np.pi) % (2 * np.pi) - np.pi
            
        # Measurement window
        R_samples = []
        for _ in range(steps_meas):
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            psi = np.angle(z)
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta)
            noise = sigma * np.sqrt(dt) * np.random.randn(N)
            theta = (theta + dtheta * dt + noise + np.pi) % (2 * np.pi) - np.pi
            R_samples.append(R)
        forward_R.append(np.mean(R_samples))
        
    # 2. Backward Sweep (start coherent / locked)
    theta = np.zeros(N)
    for K0 in reversed(K0_vals):
        for _ in range(steps_settle):
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            psi = np.angle(z)
            
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta)
            noise = sigma * np.sqrt(dt) * np.random.randn(N)
            theta = (theta + dtheta * dt + noise + np.pi) % (2 * np.pi) - np.pi
            
        R_samples = []
        for _ in range(steps_meas):
            z = np.mean(np.exp(1j * theta))
            R = np.abs(z)
            psi = np.angle(z)
            K_eff = K0 * (R ** alpha)
            dtheta = omega + K_eff * np.sin(psi - theta)
            noise = sigma * np.sqrt(dt) * np.random.randn(N)
            theta = (theta + dtheta * dt + noise + np.pi) % (2 * np.pi) - np.pi
            R_samples.append(R)
        backward_R.append(np.mean(R_samples))
    backward_R.reverse()
    
    return np.array(forward_R), np.array(backward_R)

# Also test standard linear Kuramoto (alpha=0) as control
def run_comparison():
    K0_vals = np.linspace(0.5, 5.0, 25)
    
    # Test 1: Non-linear feedback (alpha=2)
    f_nl, b_nl = kuramoto_simulation(N=200, K0_vals=K0_vals, alpha=2.0, dist='gaussian', gamma=1.0)
    
    # Test 2: Linear Kuramoto control (alpha=0)
    f_lin, b_lin = kuramoto_simulation(N=200, K0_vals=K0_vals, alpha=0.0, dist='gaussian', gamma=1.0)
    
    # Test 3: Non-linear with alpha=1.0 (linear scaling with R)
    f_nl1, b_nl1 = kuramoto_simulation(N=200, K0_vals=K0_vals, alpha=1.0, dist='gaussian', gamma=1.0)
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Subplot 1: Linear Kuramoto (Control, 2nd-order transition)
    axes[0].plot(K0_vals, f_lin, 'o-', color='#3498db', label='Forward (Incoherent init)')
    axes[0].plot(K0_vals, b_lin, 's--', color='#e74c3c', label='Backward (Coherent init)')
    axes[0].set_title("Standard Kuramoto ($K = K_0$)\nContinuous (2nd-Order) Transition", fontweight='bold')
    axes[0].set_xlabel("Coupling $K_0$")
    axes[0].set_ylabel("Order Parameter $R$")
    axes[0].grid(True, linestyle='--', alpha=0.6)
    axes[0].legend()
    
    # Subplot 2: Non-linear alpha=1 (K = K_0 * R)
    axes[1].plot(K0_vals, f_nl1, 'o-', color='#3498db', label='Forward Sweep')
    axes[1].plot(K0_vals, b_nl1, 's--', color='#e74c3c', label='Backward Sweep')
    axes[1].set_title(r"Non-linear Feedback ($K = K_0 \cdot R$)" + "\nFirst-Order Discontinuous & Hysteresis", fontweight='bold')
    axes[1].set_xlabel("Coupling $K_0$")
    axes[1].set_ylabel("Order Parameter $R$")
    axes[1].grid(True, linestyle='--', alpha=0.6)
    axes[1].legend()
    
    # Subplot 3: Non-linear alpha=2 (K = K_0 * R^2)
    axes[2].plot(K0_vals, f_nl, 'o-', color='#3498db', label='Forward Sweep')
    axes[2].plot(K0_vals, b_nl, 's--', color='#e74c3c', label='Backward Sweep')
    axes[2].set_title(r"Strong Feedback ($K = K_0 \cdot R^2$)" + "\nSubcritical Bistability Window", fontweight='bold')
    axes[2].set_xlabel("Coupling $K_0$")
    axes[2].set_ylabel("Order Parameter $R$")
    axes[2].grid(True, linestyle='--', alpha=0.6)
    axes[2].legend()
    
    plt.suptitle("Inter-World Replication Analysis: Kuramoto Non-Linear Resonance Criticality (Dossier #001)", 
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    out_path = "../../shared_agora/artifacts/kuramoto_dossier_001_replication.png"
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Artifact created at {out_path}")
    print(f"Alpha=1 Hysteresis gap max: {np.max(b_nl1 - f_nl1):.4f}")
    print(f"Alpha=2 Hysteresis gap max: {np.max(b_nl - f_nl):.4f}")

if __name__ == '__main__':
    run_comparison()
