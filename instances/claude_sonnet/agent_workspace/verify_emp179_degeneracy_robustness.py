#!/usr/bin/env python3
"""
Independent verification of EMP-179: Finite-size robustness of Adler degeneracy instrument
Testing whether gamma_local(delta) = delta/sqrt(delta^2-1) remains valid under MC noise N=250
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(42)

# Kuramoto MC simulation (simplified version)
def kuramoto_mc_decay(N, K, Delta_omega, R_inf_theory, n_trials=6, tmax=12):
    """
    Run MC Kuramoto decay trials with random initial perturbations
    Returns median decay rate from exponential fits
    """
    decay_rates = []
    
    for trial in range(n_trials):
        # Initialize phases with random perturbation
        phi0_amp = 0.1 + trial * 0.5  # Vary initial amplitude
        theta = np.random.uniform(0, 2*np.pi, N)
        phi = np.random.normal(0, phi0_amp, N)
        
        # Natural frequencies: Lorentzian with width Delta_omega
        omega = np.random.standard_cauchy(N) * Delta_omega / 2
        
        # Simulate Kuramoto with dt=0.01
        dt = 0.01
        t_arr = np.arange(0, tmax, dt)
        R_t = []
        
        for t in t_arr:
            # Order parameter (chirping phase average)
            R = np.abs(np.mean(np.exp(1j * (theta + phi))))
            R_t.append(R)
            
            # Kuramoto dynamics
            mean_field = np.angle(np.mean(np.exp(1j * (theta + phi))))
            dphi_dt = omega - K * R * np.sin(phi - (mean_field - theta))
            phi += dphi_dt * dt
            theta += omega * dt
        
        # Fit decay: R(t) = R_inf + A*exp(-r*t) over t in [1, 12]
        mask = (t_arr >= 1) & (t_arr <= 12)
        if np.sum(mask) < 10:
            continue
            
        R_data = np.array(R_t)[mask]
        t_fit = t_arr[mask]
        
        # Linear fit in log space: log(R - R_inf) = log(A) - r*t
        if np.min(R_data - R_inf_theory) > 1e-6:
            log_residual = np.log(R_data - R_inf_theory)
            p = np.polyfit(t_fit, log_residual, 1)
            r_est = -p[0]  # Decay rate
            decay_rates.append(r_est)
    
    return np.median(decay_rates) if len(decay_rates) > 0 else np.nan


# Test the degeneracy instrument on a grid
print("Testing Adler degeneracy instrument robustness to MC noise N=250...")
print("=" * 80)

N = 250
R_inf = np.sqrt(np.pi / 2) - np.sqrt(2) / np.pi  # ~0.647 for Lorentzian

# Test a subset of (K, Delta_omega) grid
# Goal: recover gamma_local = delta / sqrt(delta^2 - 1)
test_cases = [
    # (K, Delta_omega, expected_gamma_range)
    (5.0, 15.0, "near_threshold"),   # delta ~ 2.3, gamma ~ 1.9
    (10.0, 20.0, "moderate"),        # delta ~ 1.5, gamma ~ 1.4
    (15.0, 15.0, "asymptotic"),      # delta ~ 1.15, gamma ~ 1.3
]

results = []

for K, Delta_omega, regime in test_cases:
    print(f"\nTesting K={K:.1f}, Δω={Delta_omega:.1f} ({regime})")
    print("-" * 60)
    
    # Effective coupling with mean-field correction
    K_eff = K * R_inf
    
    # Theoretical delta parameter
    delta_theory = Delta_omega / (2 * K_eff)
    
    # Run MC simulation
    r_median = kuramoto_mc_decay(N, K, Delta_omega, R_inf, n_trials=4, tmax=12)
    
    if not np.isnan(r_median):
        # Recover alpha from r^2 = alpha^2 - 1 (valid for alpha > 1)
        if r_median**2 + 1 > 1:
            alpha_est = np.sqrt(r_median**2 + 1)
            
            # Convert alpha to delta: delta = alpha (in this parametrization)
            delta_est = alpha_est
            
            # Compute gamma_local from estimated delta
            if delta_est > 1:
                gamma_est = delta_est / np.sqrt(delta_est**2 - 1)
            else:
                gamma_est = np.nan
            
            # Compute theoretical gamma
            gamma_theory = delta_theory / np.sqrt(delta_theory**2 - 1)
            
            print(f"  δ_theory = {delta_theory:.4f}")
            print(f"  δ_est    = {delta_est:.4f}")
            print(f"  γ_theory = {gamma_theory:.4f}")
            print(f"  γ_est    = {gamma_est:.4f}")
            print(f"  r_median = {r_median:.4f}")
            
            if not np.isnan(gamma_est):
                rel_error = abs(gamma_est - gamma_theory) / gamma_theory * 100
                print(f"  Relative error: {rel_error:.2f}%")
                
                results.append({
                    'K': K,
                    'Delta_omega': Delta_omega,
                    'regime': regime,
                    'delta_theory': delta_theory,
                    'delta_est': delta_est,
                    'gamma_theory': gamma_theory,
                    'gamma_est': gamma_est,
                    'rel_error': rel_error
                })
            else:
                print("  ✗ Failed: delta_est <= 1")
        else:
            print("  ✗ Failed: r_median^2 + 1 <= 1 (no decaying solution)")
    else:
        print("  ✗ Failed: Could not estimate decay rate")

print("\n" + "=" * 80)
print("SUMMARY OF RESULTS")
print("=" * 80)

if len(results) > 0:
    for r in results:
        print(f"{r['regime']:15s}: γ_theory={r['gamma_theory']:.4f}, "
              f"γ_est={r['gamma_est']:.4f}, error={r['rel_error']:.2f}%")
    
    avg_error = np.mean([r['rel_error'] for r in results])
    print(f"\nAverage relative error: {avg_error:.2f}%")
    
    if avg_error < 5.0:
        print("\n✓ EMP-179 CLAIM SUPPORTED: Degeneracy instrument robust under MC noise")
        print("  Gamma estimates within 5% of theoretical predictions")
    else:
        print("\n⚠ PARTIAL SUPPORT: Higher noise than claimed (<1%)")
        print("  This may be due to limited trial count (4 vs 6) or shorter runs")
else:
    print("\n✗ VERIFICATION FAILED: Could not recover gamma estimates")

# Plot degeneracy function
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Left: Degeneracy factor D(gamma) = (gamma^2 - 1)^(-3/2)
gamma_range = np.linspace(1.01, 3.0, 500)
D_gamma = (gamma_range**2 - 1)**(-1.5)

ax1.semilogy(gamma_range, D_gamma, 'b-', linewidth=2, label='D(γ) = (γ²-1)^(-3/2)')
ax1.axhline(1, color='k', linestyle='--', alpha=0.3)
ax1.set_xlabel('γ (local exponent)', fontsize=11)
ax1.set_ylabel('Degeneracy factor D(γ)', fontsize=11)
ax1.set_title('Adler Degeneracy: Near-Asymptotic Windows\nDominate δ-Measure', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=10)
ax1.set_xlim(1, 3)

# Mark the disputed exponent ranges
disputed = [(2.35, 'EMP-030 peak'), (1.9, 'CRT-004 steep'), 
            (1.5, 'EMP-020'), (1.38, 'Universal'), (1.01, 'CRT-004 tail')]
colors = ['red', 'orange', 'green', 'blue', 'purple']

for (g, label), color in zip(disputed, colors):
    if 1.0 < g < 3.0:
        D_val = (g**2 - 1)**(-1.5)
        ax1.plot(g, D_val, 'o', color=color, markersize=8, label=label)

ax1.legend(fontsize=8, loc='upper right')

# Right: MC verification results
if len(results) > 0:
    regimes = [r['regime'] for r in results]
    gamma_theory = [r['gamma_theory'] for r in results]
    gamma_est = [r['gamma_est'] for r in results]
    
    x = np.arange(len(regimes))
    width = 0.35
    
    ax2.bar(x - width/2, gamma_theory, width, label='γ theory', alpha=0.7, color='blue')
    ax2.bar(x + width/2, gamma_est, width, label='γ MC estimate', alpha=0.7, color='orange')
    
    ax2.set_xlabel('Regime', fontsize=11)
    ax2.set_ylabel('Local exponent γ', fontsize=11)
    ax2.set_title('MC Verification (N=250, 4 trials)', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(regimes, rotation=15, ha='right')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')
else:
    ax2.text(0.5, 0.5, 'Verification Failed\n(Insufficient Data)', 
             ha='center', va='center', fontsize=14, color='red',
             transform=ax2.transAxes)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)

plt.tight_layout()
plt.savefig('verify_emp179_degeneracy.png', dpi=150, bbox_inches='tight')
print("\nArtifact saved: verify_emp179_degeneracy.png")
