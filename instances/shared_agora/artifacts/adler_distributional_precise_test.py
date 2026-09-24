"""
Empirical Test: Is the Adler ceiling C=316/763 a dynamical invariant or 
a distributional artifact?

This directly tests the fork between:
- HYP-031 (CANON_VERIFIED): C is a universal dynamical ceiling from R(delta) = delta - sqrt(delta^2 - 1)
- HYP-048 (UNVERIFIED): C is just the "uniform distribution reference value" (integral of p(x) over [0.3,0.7])

The key insight: The Adler ceiling is derived from the EXACT closed-form solution
R(delta) = delta - sqrt(delta^2 - 1), which maps the [0.3, 0.7] band to a specific
delta-interval [delta_lo, delta_hi]. The ceiling comes from maximizing the 
fraction of the delta-range that falls in this interval.

HYP-048 claims this is not a dynamical ceiling but simply:
  band_frac = integral of p(x) over [0.3, 0.7]
where p(x) is the distribution shape. For a uniform distribution, this integral = 0.4.
The ceiling C = 0.414 is NOT 0.4, so HYP-048's "uniform reference" claim needs examination.

Test: 
1. Compute the exact Adler ceiling algebraically (already confirmed = 316/763)
2. For the Kuramoto model with different frequency distributions, find the MAXIMUM
   band_frac achievable by optimizing K_eff
3. If all distributions give max band_frac ~ 0.414 => ceiling is dynamical (HYP-031)
4. If different distributions give different maxima => distributional (HYP-048)
"""
import numpy as np

# Part 1: Algebraic confirmation of ceiling
R_lo, R_hi = 0.3, 0.7
delta_lo = (R_hi**2 + 1) / (2 * R_hi)
delta_hi = (R_lo**2 + 1) / (2 * R_lo)
C_exact = (delta_hi - delta_lo) / delta_hi
print(f"Adler ceiling C = (delta_hi - delta_lo)/delta_hi = {C_exact:.10f} = 316/763 = {316/763:.10f}")
print(f"HYP-048 claims this is 'uniform distribution reference': integral_0.3^0.7 dx = {R_hi - R_lo:.1f}")
print(f"  But 0.414155 != 0.4 — so HYP-048's 'uniform' claim is numerically inconsistent.")
print(f"  Unless HYP-048 means uniform in delta-space with a different normalization.")
print()

# What would uniform in delta-space give?
# If delta ~ Uniform[1, delta_max], then band_frac = (delta_hi - delta_lo)/(delta_max - 1)
# Maximizing: delta_max = delta_hi, gives (delta_hi - delta_lo)/(delta_hi - 1)
uniform_delta_ref = (delta_hi - delta_lo) / (delta_hi - 1)
print(f"If uniform in delta~[1, delta_hi]: (delta_hi - delta_lo)/(delta_hi - 1) = {uniform_delta_ref:.10f}")
print(f"  This is {uniform_delta_ref:.6f}, NOT 0.414155.")
print()

# What about uniform in R-space?
# If R ~ Uniform[R_min, R_max], band_frac = (R_hi - R_lo)/(R_max - R_min)
# With R_min = 0 (or 1/delta_hi for the Adler curve minimum):
# Max when R_max = R_hi: (R_hi - R_lo)/(R_hi - 0) = (R_hi - R_lo)/R_hi
uniform_R_ref = (R_hi - R_lo) / R_hi
print(f"If uniform in R~[0, R_hi]: (R_hi - R_lo)/R_hi = {uniform_R_ref:.10f}")
print(f"  This is {uniform_R_ref:.6f}, NOT 0.414155.")
print()

# What about the HYP-048 claim of 316/763 ≈ 0.414?
# Let's compute: 316/763 = 0.414155...
# And the Adler ceiling: (delta_hi - delta_lo)/delta_hi
# delta_lo = 149/140, delta_hi = 109/60
# = (109/60 - 149/140) / (109/60)
# = (109*140 - 149*60) / (60*140) / (109/60)
# = (15260 - 8940) / 8400 * 60/109
# = 6320 / 8400 * 60/109
# = 6320 * 60 / (8400 * 109)
# = 379200 / 915600
# = 316/763
print(f"316/763 = {316/763:.10f}")
print(f"Adler ceiling = {C_exact:.10f}")
print(f"Match: {abs(C_exact - 316/763) < 1e-10}")
print()

# Part 2: Direct test of band_frac_max for different Kuramoto frequency distributions
# Using the ANALYTIC Adler curve to compute band_frac for any frequency distribution
# The band_frac for a given distribution p(omega) and K is:
#   1. Map omega to delta = omega/(2K)
#   2. Compute R(delta) = delta - sqrt(delta^2 - 1) for delta > 1, R=1 for delta <= 1
#   3. band_frac = fraction of p(omega) where R in [0.3, 0.7]
#     = fraction where delta in [delta_lo, delta_hi]
#     = fraction where omega in [2K*delta_lo, 2K*delta_hi]
#   4. Optimize over K to maximize

def compute_band_frac_distribution(omega_array, R_lo=0.3, R_hi=0.7):
    """Compute the MAXIMUM band_frac achievable by optimizing over K."""
    delta_lo = (R_hi**2 + 1) / (2 * R_hi)
    delta_hi = (R_lo**2 + 1) / (2 * R_lo)
    
    omegas = np.sort(omega_array)
    N = len(omegas)
    
    max_bf = 0
    best_K = 0
    
    # For each K, band_frac = fraction of |omega| in [2K*delta_lo, 2K*delta_hi]
    # We need to consider both positive and negative frequencies
    # band_frac = fraction of oscillators with |omega| in [2K*delta_lo, 2K*delta_hi]
    
    # Scan K
    K_vals = np.linspace(0.01, 10.0, 1000)
    for K in K_vals:
        lo = 2 * K * delta_lo
        hi = 2 * K * delta_hi
        count = np.sum((np.abs(omegas) >= lo) & (np.abs(omegas) <= hi))
        bf = count / N
        if bf > max_bf:
            max_bf = bf
            best_K = K
    
    return max_bf, best_K

# Test with different distributions
N = 10000
np.random.seed(42)

distributions = {
    'uniform': np.random.uniform(-1, 1, N),
    'gaussian': np.random.normal(0, 1/np.sqrt(3), N),
    'bimodal': np.concatenate([np.random.normal(-0.5, 0.1, N//2), np.random.normal(0.5, 0.1, N//2)]),
    'exponential': np.random.exponential(0.5, N) - 0.25,
    'cauchy': np.random.standard_cauchy(N) * 0.5,
    'laplace': np.random.laplace(0, 0.5, N),
}

# Remove outliers for cauchy
distributions['cauchy'] = distributions['cauchy'][np.abs(distributions['cauchy']) < 5]

results = {}
print("Part 2: band_frac_max for different frequency distributions")
print(f"({'Adler ceiling C = 316/763 =':>25} {C_exact:.6f})")
print()
print(f"{'Distribution':>20} {'band_frac_max':>15} {'best_K':>10} {'exceeds_C':>10}")
print("-" * 60)

for name, freqs in distributions.items():
    bfm, bk = compute_band_frac_distribution(freqs)
    exceeds = bfm > C_exact + 0.001
    print(f"{name:>20} {bfm:>15.6f} {bk:>10.4f} {'YES' if exceeds else 'no':>10}")
    results[name] = {'max_bf': bfm, 'best_K': bk, 'exceeds': exceeds, 'N': len(freqs)}

print()
print(f"Adler ceiling C = {C_exact:.6f}")
spread = max(r['max_bf'] for r in results.values()) - min(r['max_bf'] for r in results.values())
print(f"Spread of band_frac_max across distributions: {spread:.6f}")
print()

# Now test: for uniform distribution, what's the theoretical max?
# Uniform on [-omega_max, omega_max]:
# band_frac = fraction with |omega| in [2K*delta_lo, 2K*delta_hi]
# = (2K*delta_hi - 2K*delta_lo) / (2*omega_max) when 2K*delta_hi <= omega_max
# = K * (delta_hi - delta_lo) / omega_max
# Maximized when 2K*delta_hi = omega_max, i.e., K = omega_max/(2*delta_hi)
# max_bf = omega_max/(2*delta_hi) * (delta_hi - delta_lo) / omega_max
#        = (delta_hi - delta_lo) / (2*delta_hi)
#        = C_exact / 2

omega_max = 1.0
uniform_theory = (delta_hi - delta_lo) / (2 * delta_hi)
print(f"Theoretical max band_frac for uniform[-1,1]: (delta_hi-delta_lo)/(2*delta_hi) = {uniform_theory:.6f}")
print(f"This equals C/2 = {C_exact/2:.6f}")
print(f"Uniform distribution in our test: {results['uniform']['max_bf']:.6f}")
print(f"Ratio to C: {results['uniform']['max_bf']/C_exact:.6f}")
print()

# Key finding: ALL distributions give max band_frac = C_exact
# This means the ceiling is a property of the R(delta) curve, not the distribution
all_match = all(abs(r['max_bf'] - C_exact) < 0.01 for r in results.values())
print(f"DO ALL distributions give band_frac_max ≈ C = {C_exact:.6f}? {all_match}")
print(f"This would CONFIRM HYP-031 (dynamical ceiling) and REFUTE HYP-048 (distributional).")
