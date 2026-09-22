"""
Empirical Test: Distributional vs Dynamical Origin of band_frac

This test addresses the fork in the road between:
- HYP-031 (CANON_VERIFIED): C = 316/763 = 0.414 is a universal DYNAMICAL ceiling on band_frac
- HYP-048 (UNVERIFIED, from_embassy): C = 316/763 is just the uniform distribution reference value; 
  band_frac is fundamentally DISTRIBUTIONAL, not dynamical

Test strategy:
1. Confirm C = 316/763 for the Adler equation (PRF-012 verified, PRF-015 refuted)
2. For the Kuramoto model, use DIFFERENT frequency distributions 
   (uniform, Gaussian, bimodal, exponential) and measure the resulting band_frac
   - If band_frac varies significantly with distribution shape => HYP-048 distributional claim is supported
   - If band_frac is always bounded by C regardless of distribution => dynamical ceiling holds
3. Check: does the uniform distribution give exactly 0.4 (not 0.414)?

Note: The "band_frac" here is the fraction of oscillators whose individual R_i (or |r_i|)
falls in [0.3, 0.7], computed from the order parameter trajectory.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot plt
import json

# ---- 1. Confirm Adler ceiling C = 316/763 ----
print("=" * 70)
print("PART 1: CONFIRM ADLER CEILING C = 316/763")
print("=" * 70)

R_lo, R_hi = 0.3, 0.7
delta_lo = (R_hi**2 + 1) / (2 * R_hi)
delta_hi = (R_lo**2 + 1) / (2 * R_lo)
C_correct = (delta_hi - delta_lo) / delta_hi
C_prf015 = (delta_hi - delta_lo) / (delta_hi - delta_lo + 1)

print(f"delta_lo = {delta_lo:.10f} = {149}/{140}")
print(f"delta_hi = {delta_hi:.10f} = {109}/{60}")
print(f"Correct ceiling C = (delta_hi - delta_lo)/delta_hi = {C_correct:.10f} = 316/763")
print(f"PRF-015 ceiling    = (delta_hi - delta_lo)/(delta_hi - delta_lo + 1) = {C_prf015:.10f}")
print(f"Uniform integral  = ∫_0.3^0.7 dx = 0.4 (note: this is NOT 316/763)")
print(f"  So HYP-048's claim that C=316/763 is the 'uniform reference value' needs scrutiny:")
print(f"  ∫_0.3^0.7 dx = 0.4 ≠ 0.414155")
print()

# ---- 2. Distributional test: different frequency distributions ----
print("=" * 70)
print("PART 2: DISTRIBUTIONAL TEST (Kuramoto with different frequency distributions)")
print("=" * 70)

def simulate_kuramoto(N, freqs, K, dt=0.05, t_trans=50, t_meas=100, n_seeds=3):
    """
    Simulate Kuramoto model with given frequency distribution.
    Returns the time-averaged order parameter trajectory R(t) and 
    the per-oscillator 'participation' metric |<e^{iθ_j}>|.
    """
    results = []
    for seed in range(n_seeds):
        np.random.seed(seed)
        theta = np.random.uniform(0, 2*np.pi, N)
        R_values = []
        for step in range(int((t_trans + t_meas) / dt)):
            # Coupling term
            r_complex = np.mean(np.exp(1j * theta))
            R_inst = np.abs(r_complex)
            if step * dt >= t_trans:
                R_values.append(R_inst)
            # Update
            theta += dt * (freqs + K * np.sin(np.angle(r_complex) - theta))
        results.append(np.array(R_values))
    return np.array(results)  # shape: (n_seeds, t_meas/dt)

def compute_band_frac_from_R(R_values, R_lo=0.3, R_hi=0.7):
    """band_frac = fraction of time R(t) spends in [R_lo, R_hi]"""
    flattened = R_values.flatten()
    count = np.sum((flattened >= R_lo) & (flattened <= R_hi))
    return count / len(flattened)

# Define frequency distributions
N = 500
distributions = {
    'uniform_1': lambda: np.random.uniform(-1, 1, N),
    'gaussian': lambda: np.random.normal(0, 1/np.sqrt(3), N),  # same std as uniform[-1,1]
    'bimodal': lambda: np.concatenate([np.random.normal(-0.5, 0.1, N//2), 
                                         np.random.normal(0.5, 0.1, N//2)]),
    'exponential_shifted': lambda: np.random.exponential(0.5, N) - 0.25,
    'cauchy': lambda: np.random.standard_cauchy(N) * 0.5,
}

# Also compute what HYP-048 means by "uniform distribution reference value"
# For a uniform distribution of delta in [1, delta_hi], the band_frac would be
# (delta_hi - delta_lo) / (delta_hi - 1), which is different from (delta_hi - delta_lo)/delta_hi
uniform_reference_1 = (delta_hi - delta_lo) / delta_hi  # PRF-012's value = 0.414
uniform_reference_2 = (delta_hi - delta_lo) / (delta_hi - 1)  # different normalization
print(f"Uniform reference (PRF-012 constraint): {uniform_reference_1:.10f}")
print(f"Uniform ref (delta in [1,delta_hi]):    {uniform_reference_2:.10f}")
print(f"Simple integral ∫_R_lo^R_hi dR = R_hi - R_lo = {R_hi - R_lo:.1f}")
print()

results_summary = {}

for dist_name, dist_func in distributions.items():
    print(f"\n--- Distribution: {dist_name} ---")
    np.random.seed(42)  # for reproducibility of frequencies
    freqs = dist_func()
    
    # Sweep K
    K_values = np.linspace(0.1, 10.0, 100)
    band_fracs = []
    
    for K in K_values:
        R_vals = simulate_kuramoto(N, freqs, K, n_seeds=2)
        bf = compute_band_frac_from_R(R_vals, R_lo, R_hi)
        band_fracs.append(bf)
    
    band_fracs = np.array(band_fracs)
    max_bf = np.max(band_fracs)
    K_max = K_values[np.argmax(band_fracs)]
    
    print(f"  Max band_frac = {max_bf:.6f} at K = {K_max:.3f}")
    print(f"  band_frac > C_correct? {'YES' if max_bf > C_correct + 0.01 else 'NO'}")
    
    results_summary[dist_name] = {
        'max_band_frac': max_bf,
        'K_at_max': K_max,
        'exceeds_ceiling': max_bf > C_correct + 0.01
    }

print("\n" + "=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)
print(f"{'Distribution':<25} {'Max band_frac':>15} {'Exceeds C':>12}")
print("-" * 55)
for name, info in results_summary.items():
    print(f"{name:<25} {info['max_band_frac']:>15.6f} {'YES' if info['exceeds_ceiling'] else 'no':>12}")

print(f"\nPRF-012 ceiling C = {C_correct:.6f}")
print(f"PRF-015 ceiling   = {C_prf015:.6f}")

# ---- 3. Key question for HYP-048 ----
# HYP-048 claims band_frac depends on distribution shape, implying it's not a 
# dynamical ceiling but a distributional measure. Let's check if different 
# distributions give very different band_frac values.
spread = max([info['max_band_frac'] for info in results_summary.values()]) - \
         min([info['max_band_frac'] for info in results_summary.values()])
print(f"\nSpread of max band_frac across distributions: {spread:.6f}")
print(f"If spread is large => band_frac IS distribution-dependent (supports HYP-048)")
print(f"If band_frac is always bounded by C => dynamical ceiling holds (supports HYP-031)")

# ---- Save results ----
results_json = {
    'C_correct': float(C_correct),
    'C_prf015': float(C_prf015),
    'R_lo': R_lo,
    'R_hi': R_hi,
    'delta_lo': float(delta_lo),
    'delta_hi': float(delta_hi),
    'distribution_results': results_summary,
    'spread': float(spread)
}
with open('shared_agora/artifacts/adler_distributional_test.json', 'w') as f:
    json.dump(results_json, f, indent=2)
print("\nResults saved to shared_agora/artifacts/adler_distributional_test.json")
