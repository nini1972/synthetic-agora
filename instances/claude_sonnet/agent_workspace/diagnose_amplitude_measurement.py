#!/usr/bin/env python3
"""
Diagnostic: Why is A(γ) approximately constant instead of decreasing with γ?

Hypothesis: The "transient amplitude" measured as max(R) during T=200 may be
conflating two different phenomena:
1. Initial finite-N fluctuation amplitude (what EMP-163 means)
2. Partial synchronization transients that occur even if the system doesn't lock

Let me measure the INITIAL peak (first local maximum within t<50) vs global maximum.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def kuramoto_reflexive_trajectory(K0, a, gamma, N=300, T_max=200, dt=0.05, seed=42):
    """Run full trajectory and return R(t)."""
    np.random.seed(seed)
    theta = np.random.uniform(0, 2*np.pi, N)
    u = np.random.uniform(0, 1, N)
    omega = gamma * np.tan(np.pi * (u - 0.5))
    
    R_trajectory = []
    t_trajectory = []
    
    for step in range(int(T_max / dt)):
        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        Psi = np.angle(z)
        
        R_trajectory.append(R)
        t_trajectory.append(step * dt)
        
        # RK4 step
        def derivs(th):
            z_local = np.mean(np.exp(1j * th))
            R_local = np.abs(z_local)
            Psi_local = np.angle(z_local)
            K = K0 * (R_local ** a)
            return omega + K * R_local * np.sin(Psi_local - th)
        
        k1 = derivs(theta)
        k2 = derivs(theta + 0.5*dt*k1)
        k3 = derivs(theta + 0.5*dt*k2)
        k4 = derivs(theta + dt*k3)
        
        theta = (theta + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)) % (2*np.pi)
    
    return np.array(t_trajectory), np.array(R_trajectory)

# Test two extreme cases
K0, a = 5.0, 2.0
gamma_low = 0.1  # Should lock easily
gamma_high = 0.85  # Should not lock

print("=" * 70)
print("DIAGNOSTIC: Transient Amplitude Measurement")
print("=" * 70)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for i, (gamma, label) in enumerate([(gamma_low, "γ=0.1 (easy lock)"),
                                      (gamma_high, "γ=0.85 (hard/no lock)")]):
    
    # Run multiple seeds
    for seed in range(5):
        t, R = kuramoto_reflexive_trajectory(K0, a, gamma, seed=seed)
        
        # Plot full trajectory
        axes[i, 0].plot(t, R, alpha=0.6, linewidth=1)
        
        # Zoom to early time
        mask = t < 50
        axes[i, 1].plot(t[mask], R[mask], alpha=0.6, linewidth=1)
    
    axes[i, 0].set_xlabel('Time t')
    axes[i, 0].set_ylabel('Order parameter R(t)')
    axes[i, 0].set_title(f'{label} - Full Trajectory', fontsize=11, weight='bold')
    axes[i, 0].grid(True, alpha=0.3)
    axes[i, 0].axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Lock threshold')
    axes[i, 0].legend()
    
    axes[i, 1].set_xlabel('Time t')
    axes[i, 1].set_ylabel('Order parameter R(t)')
    axes[i, 1].set_title(f'{label} - Early Dynamics (t<50)', fontsize=11, weight='bold')
    axes[i, 1].grid(True, alpha=0.3)
    axes[i, 1].axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Lock threshold')

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/diagnose_amplitude_trajectories.png', dpi=150)
print("📊 Trajectory diagnostic saved: diagnose_amplitude_trajectories.png")

# Now measure different amplitude definitions
print("\n" + "=" * 70)
print("Comparing Amplitude Definitions")
print("=" * 70)

gamma_values = [0.1, 0.4, 0.5, 0.6, 0.7, 0.85, 1.0]
n_seeds = 16

results = {
    'gamma': [],
    'R_global_max': [],
    'R_early_max': [],  # Max in first t<20
    'R_initial': []  # R at t=0
}

for gamma in gamma_values:
    R_global = []
    R_early = []
    R_init = []
    
    for seed in range(n_seeds):
        t, R = kuramoto_reflexive_trajectory(K0, a, gamma, T_max=200, seed=seed)
        
        R_global.append(np.max(R))
        
        # Early max (t < 20)
        early_mask = t < 20
        if np.any(early_mask):
            R_early.append(np.max(R[early_mask]))
        
        R_init.append(R[0])
    
    results['gamma'].append(gamma)
    results['R_global_max'].append(np.mean(R_global))
    results['R_early_max'].append(np.mean(R_early))
    results['R_initial'].append(np.mean(R_init))
    
    print(f"γ={gamma:.2f}:  R_init={np.mean(R_init):.4f}, R_early={np.mean(R_early):.3f}, R_global={np.mean(R_global):.3f}")

print("\n⚠️  KEY INSIGHT:")
print("If R_init is approximately constant (~1/√N ≈ 0.058), but R_early varies,")
print("then the 'true' transient amplitude should be R_early, not R_global.")
print("\nEMP-163 likely measures the FIRST excursion from the incoherent state,")
print("not the global maximum over the entire simulation window.")
print("=" * 70)
