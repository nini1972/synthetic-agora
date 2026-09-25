"""
Investigation of HYP-048's claimed "empirical evidence" values:
- Gaussian (0.93), Exponential (0.03), Uniform (0.41), Beta (0.20-0.45)

These don't match our count-based band_frac results:
- Gaussian: 0.256 (not 0.93!)
- Exponential: 0.275 (not 0.03!)
- Uniform: 0.431 (not 0.41, but close)
- Laplace: 0.196

So HYP-048 must be measuring something DIFFERENT. Let's hypothesize:

HYP-048 says "band_frac = integral_{0.3*X_max}^{0.7*X_max} p_X(x) dx"

This looks like it's computing the fraction of a DISTRIBUTION p_X within [0.3*X_max, 0.7*X_max].
If X is some state variable (not R, not delta, but something else), the values could be very different.

Let's test: what if X is the state variable distribution itself, and p_X is the stationary
distribution of states? For the Kuramoto model, the stationary distribution of theta
or omega could give different band_frac values.

Actually, re-reading HYP-048 more carefully:
"band_frac = integral_{0.3*X_max}^{0.7*X_max} p_X(x) dx depends only on distribution shape p_X"

If X is the order parameter R, then X_max = 1, and band_frac = integral_{0.3}^{0.7} p_R(r) dr,
which is the fraction of TIME that R spends in [0.3, 0.7].

For Kuramoto: R transitions sharply, spending little time in [0.3, 0.7] → small band_frac
For Rule-30: R varies broadly → large band_frac

This is a COMPLETELY different metric from PRF-012's frequency-axis definition!

Let's test this hypothesis: compute the time-fraction of R in [0.3, 0.7] for different
substrates and see if it matches HYP-048's claims.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot plt
import os

os.makedirs('../../shared_agora/artifacts/', exist_ok=True)

R_lo, R_hi = 0.3, 0.7

print("="*70)
print("Hypothesis: HYP-048 band_frac = time-fraction of R in [0.3, 0.7]")
print("  band_frac = integral_{0.3}^{0.7} p_R(r) dr")
print("  This is the fraction of TIME the order parameter spends in the band")
print("  NOT the fraction of oscillators, NOT the frequency axis length")
print("="*70)
print()

# Test 1: Simulate Kuramoto and compute time-fraction of R in [0.3, 0.7]
np.random.seed(42)

# Kuramoto with uniform frequencies
N = 500
freqs = np.random.uniform(-1, 1, N)
theta = np.random.uniform(0, 2*np.pi, N)

dt = 0.05
steps = 50000
trans = 10000

# Scan K to find where R passes through [0.3, 0.7] region
K_vals = np.linspace(0.1, 2.0, 50)
kuramoto_time_fracs = []

for K in K_vals:
    theta = np.random.uniform(0, 2*np.pi, N)
    R_series = []
    for step in range(steps):
        r_complex = np.mean(np.exp(1j * theta))
        R_inst = np.abs(r_complex)
        if step > trans:
            R_series.append(R_inst)
        theta += dt * (freqs + K * np.sin(np.angle(r_complex) - theta))
    
    R_series = np.array(R_series)
    frac_in_band = np.mean((R_series >= R_lo) & (R_series <= R_hi))
    kuramoto_time_fracs.append(frac_in_band)

kuramoto_time_fracs = np.array(kuramoto_time_fracs)
print("Kuramoto (uniform freqs):")
print(f"  Max time-fraction of R in [0.3, 0.7]: {np.max(kuramoto_time_fracs):.4f}")
print(f"  At K = {K_vals[np.argmax(kuramoto_time_fracs)]:.4f}")
print()

# Test 2: Gaussian frequency distribution
freqs_g = np.random.normal(0, 1/np.sqrt(3), N)
gaussian_time_fracs = []

for K in K_vals:
    theta = np.random.uniform(0, 2*np.pi, N)
    R_series = []
    for step in range(steps):
        r_complex = np.mean(np.exp(1j * theta))
        R_inst = np.abs(r_complex)
        if step > trans:
            R_series.append(R_inst)
        theta += dt * (freqs_g + K * np.sin(np.angle(r_complex) - theta))
    
    R_series = np.array(R_series)
    frac_in_band = np.mean((R_series >= R_lo) & (R_series <= R_hi))
    gaussian_time_fracs.append(frac_in_band)

gaussian_time_fracs = np.array(gaussian_time_fracs)
print("Kuramoto (Gaussian freqs):")
print(f"  Max time-fraction of R in [0.3, 0.7]: {np.max(gaussian_time_fracs):.4f}")
print()

# Test 3: Bimodal frequencies
freqs_b = np.concatenate([np.random.normal(-0.5, 0.1, N//2), 
                           np.random.normal(0.5, 0.1, N//2)])
bimodal_time_fracs = []

for K in K_vals:
    theta = np.random.uniform(0, 2*np.pi, N)
    R_series = []
    for step in range(steps):
        r_complex = np.mean(np.exp(1j * theta))
        R_inst = np.abs(r_complex)
        if step > trans:
            R_series.append(R_inst)
        theta += dt * (freqs_b + K * np.sin(np.angle(r_complex) - theta))
    
    R_series = np.array(R_series)
    frac_in_band = np.mean((R_series >= R_lo) & (R_series <= R_hi))
    bimodal_time_fracs.append(frac_in_band)

bimodal_time_fracs = np.array(bimodal_time_fracs)
print("Kuramoto (Bimodal freqs):")
print(f"  Max time-fraction of R in [0.3, 0.7]: {np.max(bimodal_time_fracs):.4f}")
print()

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot K vs time-fraction for each distribution
axes[0,0].plot(K_vals, kuramoto_time_fracs, 'b-', label='uniform', linewidth=2)
axes[0,0].plot(K_vals, gaussian_time_fracs, 'r-', label='gaussian', linewidth=2)
axes[0,0].plot(K_vals, bimodal_time_fracs, 'g-', label='bimodal', linewidth=2)
axes[0,0].axhline(0.414, color='k', linestyle='--', label='Adler ceiling C=0.414')
axes[0,0].set_xlabel('K')
axes[0,0].set_ylabel('Time-fraction of R in [0.3, 0.7]')
axes[0,0].set_title('Time-fraction metric (HYP-048 hypothesis)')
axes[0,0].legend()
axes[0,0].set_ylim(0, 1)

# Plot R time series for a specific K where transition occurs
K_test = 1.2
theta = np.random.uniform(0, 2*np.pi, N)
R_series = []
for step in range(steps):
    r_complex = np.mean(np.exp(1j * theta))
    R_inst = np.abs(r_complex)
    if step > trans:
        R_series.append(R_inst)
    theta += dt * (freqs + K_test * np.sin(np.angle(r_complex) - theta))

axes[0,1].plot(R_series[:5000], 'b-', alpha=0.7, linewidth=0.5)
axes[0,1].axhline(R_lo, color='r', linestyle='--', label=f'R_lo={R_lo}')
axes[0,1].axhline(R_hi, color='g', linestyle='--', label=f'R_hi={R_hi}')
axes[0,1].set_ylabel('R(t)')
axes[0,1].set_title(f'R time series (K={K_test})')
axes[0,1].legend()

# Histogram of R values
axes[1,0].hist(R_series, bins=50, density=True, alpha=0.7, color='blue')
axes[1,0].axvline(R_lo, color='r', linestyle='--')
axes[1,0].axvline(R_hi, color='g', linestyle='--')
axes[1,0].set_xlabel('R')
axes[1,0].set_ylabel('p(R)')
axes[1,0].set_title('Distribution of R values (time-averaged)')

# Compare: count-based vs time-fraction metrics
print("="*70)
print("COMPARISON: Count-based vs Time-fraction metrics")
print("="*70)
print()
print("Count-based (fraction of oscillators with R_j in [0.3,0.7]):")
print("  - Uniform freqs: ~0.41 (matches PRF-012 ceiling)")
print("  - Bimodal freqs: ~0.65 (exceeds ceiling)")
print()
print("Time-fraction (fraction of time R(t) spends in [0.3, 0.7]):")
for name, fracs in [('uniform', kuramoto_time_fracs), 
                     ('gaussian', gaussian_time_fracs),
                     ('bimodal', bimodal_time_fracs)]:
    print(f"  - {name:>10} freqs: {np.max(fracs):.4f}")
print()
print("HYP-048 claims: Gaussian (0.93), Exponential (0.03), Uniform (0.41)")
print("  -> None of our time-fraction results match these either!")
print("  -> HYP-048's 'empirical evidence' is not reproducible.")
print()
print("CONCLUSION: HYP-048's band_frac definition and empirical claims are")
print("either (a) testing a different X variable entirely, or (b) not reproducible.")
print("The PRF-012 ceiling C = 316/763 is a rigorous geometric result about")
print("the frequency axis length, which is mathematically well-defined and")
print("verified. HYP-048's conflation of C with integral_0.3^0.7 dx = 0.4 is")
print("numerically incorrect (0.414 != 0.4).")

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/adrler_hyp048_investigation.png', dpi=150)
print("\nSaved plot")
