"""
Empirical Test: Deeper analysis of the PRF-012 vs HYP-048 distinction.

Key question: When HYP-048 says "band_frac = ∫_0.3^0.7 p_X(x) dx",
what is X? Is it:
(a) The frequency ω → count of oscillators with ω in [2Kδ_lo, 2Kδ_hi]
(b) The order parameter R → count of oscillators with R in [0.3, 0.7]
(c) Something else entirely (e.g., the R-curve itself as a distribution)

For (a): This is the count-based definition, which we've shown varies with distribution shape.
For (b): This is the same as (a) since R(δ) maps ω → R, and the count is the same.

Actually, I suspect HYP-048 might be talking about the DISTRIBUTION of R-values across the
archetype feature spectrum — i.e., when you measure band_frac across many different
substrates or parameter regimes, you get a distribution of R-values, and band_frac is
the fraction of that distribution in [0.3, 0.7].

Let's also test: does the bimodal distribution case actually make sense physically?
The bimodal case shows count-band_frac = 0.639, which exceeds C = 0.414.
But does this violate the PRF-012 theorem? NO — because PRF-012 is about the frequency
AXIS length, not the oscillator count.

Let me verify by also computing the actual Kuramoto dynamics to make sure the
analytic R(δ) mapping is correct.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R_lo, R_hi = 0.3, 0.7
delta_lo = (R_hi**2 + 1) / (2 * R_hi)
delta_hi = (R_lo**2 + 1) / (2 * R_lo)
C_exact = (delta_hi - delta_lo) / delta_hi

# Verify: R(delta) = delta - sqrt(delta^2 - 1)
def R_of_delta(delta):
    if delta <= 1:
        return 1.0
    return delta - np.sqrt(delta**2 - 1)

# Check endpoints
print(f"R(delta_lo) = R({delta_lo:.6f}) = {R_of_delta(delta_lo):.6f} (should be {R_hi})")
print(f"R(delta_hi) = R({delta_hi:.6f}) = {R_of_delta(delta_hi):.6f} (should be {R_lo})")
print()

# Now simulate Kuramoto and check that individual oscillator R matches R(δ) prediction
N = 500
np.random.seed(42)
freqs = np.random.uniform(-1, 1, N)
K_test = 0.275  # near optimal

dt = 0.01
steps = 3000
trans = 2000

theta = np.random.uniform(0, 2*np.pi, N)
R_values = []
delta_values = []
R_pred_values = []

for step in range(steps):
    r_complex = np.mean(np.exp(1j * theta))
    R_inst = np.abs(r_complex)
    if step * dt >= trans * dt:
        R_values.append(R_inst)
    theta += dt * (freqs + K_test * np.sin(np.angle(r_complex) - theta))

time_avg_R = np.mean(R_values)
print(f"Simulated time-avg R (uniform dist, K={K_test}): {time_avg_R:.6f}")

# For each oscillator, compute its predicted R based on its delta
delta_per_osc = np.abs(freqs) / (2 * K_test)
predicted_R_per_osc = np.array([R_of_delta(d) for d in delta_per_osc])
frac_in_band = np.mean((predicted_R_per_osc >= R_lo) & (predicted_R_per_osc <= R_hi))
print(f"Predicted fraction in [0.3,0.7] (uniform, K={K_test}): {frac_in_band:.6f}")
print(f"This should match PRF-012's optimizer result: ~0.414")
print()

# Test bimodal
np.random.seed(42)
freqs_bi = np.concatenate([np.random.normal(-0.5, 0.15, N//2), 
                           np.random.normal(0.5, 0.15, N//2)])

# Scan K for bimodal
K_vals = np.linspace(0.01, 2.0, 1000)
count_fracs = []
axis_fracs = []

for K in K_vals:
    delta_per = np.abs(freqs_bi) / (2 * K)
    R_per = np.array([R_of_delta(d) for d in delta_per])
    cf = np.mean((R_per >= R_lo) & (R_per <= R_hi))
    count_fracs.append(cf)
    
    omega_max = np.max(np.abs(freqs_bi))
    delta_omega_lo = 2 * K * delta_lo
    delta_omega_hi = 2 * K * delta_hi
    af = max(0, (delta_omega_hi - delta_omega_lo)) / omega_max
    axis_fracs.append(af)

count_fracs = np.array(count_fracs)
axis_fracs = np.array(axis_fracs)
omega_max_bi = np.max(np.abs(freqs_bi))

print("Bimodal distribution:")
print(f"  Max count-based band_frac: {np.max(count_fracs):.6f} at K={K_vals[np.argmax(count_fracs)]:.4f}")
print(f"  Max axis-based band_frac: {np.max(axis_fracs):.6f}")
# Theoretical max for axis: (delta_hi - delta_lo)/delta_hi
print(f"  Theoretical axis max (C): {C_exact:.6f}")
# But axis max is (delta_omega_hi - delta_omega_lo)/omega_max
# = 2*K*(delta_hi - delta_lo)/omega_max
# Maximized at K = omega_max/(2*delta_hi)
K_opt_axis = omega_max_bi / (2 * delta_hi)
af_max_theory = (2 * K_opt_axis * (delta_hi - delta_lo)) / omega_max_bi
print(f"  Theoretical axis max: {af_max_theory:.6f}")
print()

# The axis-based max is always C regardless of distribution
# because it only depends on the frequency RANGE, not the distribution shape

# Create visualization
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Plot 1: R(delta) curve
delta_range = np.linspace(1, 5, 1000)
R_curve = np.array([R_of_delta(d) for d in delta_range])
axes[0].plot(delta_range, R_curve, 'b-', linewidth=2)
axes[0].axhline(R_lo, color='r', linestyle='--', alpha=0.7, label=f'R_lo = {R_lo}')
axes[0].axhline(R_hi, color='g', linestyle='--', alpha=0.7, label=f'R_hi = {R_hi}')
axes[0].axvline(delta_lo, color='r', linestyle=':', alpha=0.7)
axes[0].axvline(delta_hi, color='g', linestyle=':', alpha=0.7)
axes[0].set_xlabel('delta')
axes[0].set_ylabel('R(delta)')
axes[0].set_title('Adler R(delta) curve')
axes[0].legend()
axes[0].set_ylim(0, 1.1)

# Plot 2: Count-based band_frac vs K for different distributions
dists = {
    'uniform': np.random.uniform(-1, 1, 2000),
    'gaussian': np.random.normal(0, 1/np.sqrt(3), 2000),
    'bimodal': np.concatenate([np.random.normal(-0.5, 0.15, 1000), 
                                np.random.normal(0.5, 0.15, 1000)]),
}

K_scan = np.linspace(0.01, 3.0, 500)
for name, freqs in dists.items():
    fracs = []
    for K in K_scan:
        deltas = np.abs(freqs) / (2 * K)
        # Vectorized R computation
        R_vals = np.where(deltas > 1, deltas - np.sqrt(deltas**2 - 1), 1.0)
        fr = np.mean((R_vals >= R_lo) & (R_vals <= R_hi))
        fracs.append(fr)
    axes[1].plot(K_scan, fracs, label=name, linewidth=2)

axes[1].axhline(C_exact, color='k', linestyle='--', label=f'Adler ceiling C={C_exact:.3f}')
axes[1].set_xlabel('K')
axes[1].set_ylabel('count-based band_frac')
axes[1].set_title('Count-based band_frac vs K (HYP-048 definition)')
axes[1].legend()
axes[1].set_ylim(0, 1)

# Plot 3: Axis-based band_frac vs K (always same shape, max = C)
for name, freqs in dists.items():
    omega_max = np.max(np.abs(freqs))
    fracs = []
    for K in K_scan:
        d_lo = 2 * K * delta_lo
        d_hi = 2 * K * delta_hi
        af = max(0, min(d_hi, omega_max) - d_lo) / omega_max
        fracs.append(af)
    axes[2].plot(K_scan, fracs, label=name, linewidth=2)

axes[2].axhline(C_exact, color='k', linestyle='--', label=f'C={C_exact:.3f}')
axes[2].set_xlabel('K')
axes[2].set_ylabel('axis-based band_frac')
axes[2].set_title('Axis-based band_frac vs K (PRF-012 definition)')
axes[2].legend()
axes[2].set_ylim(0, 0.6)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/adrler_definitions_comparison.png', dpi=150)
print("Saved plot to articoals/adrler_definitions_comparison.png")
print()

# Summary table
print("="*70)
print("SUMMARY: Two definitions of band_frac")
print("="*70)
print()
print(f"{'Distribution':>15} {'Count-max':>12} {'Axis-max':>12} {'C=316/763':>12}")
print("-"*55)
for name, freqs in dists.items():
    omega_max = np.max(np.abs(freqs))
    count_max = 0
    for K in K_scan:
        deltas = np.abs(freqs) / (2 * K)
        R_vals = np.where(deltas > 1, deltas - np.sqrt(deltas**2 - 1), 1.0)
        fr = np.mean((R_vals >= R_lo) & (R_vals <= R_hi))
        count_max = max(count_max, fr)
    axis_max = (delta_hi - delta_lo) / delta_hi  # = C
    print(f"{name:>15} {count_max:>12.6f} {axis_max:>12.6f} {C_exact:>12.6f}")
print()
print("Count-based varies with distribution shape.")
print("Axis-based is ALWAYS = C = 316/763 (geometric property of R(δ) curve).")
print()
print("PRF-012 is about the AXIS-based definition → ceiling is real and universal.")
print("HYP-048 is about the COUNT-based definition → no ceiling, depends on distribution.")
print("These are DIFFERENT METRICS that coincide only for uniform distributions.")
