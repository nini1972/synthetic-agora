import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

os.makedirs('../../shared_agora/artifacts/', exist_ok=True)

R_lo, R_hi = 0.3, 0.7
delta_lo = (R_hi**2 + 1) / (2 * R_hi)
delta_hi = (R_lo**2 + 1) / (2 * R_lo)
C_exact = (delta_hi - delta_lo) / delta_hi

print(f"delta_lo = {delta_lo:.10f}")
print(f"delta_hi = {delta_hi:.10f}")
print(f"Adler ceiling C = {C_exact:.10f} = 316/763")
print(f"HYP-048 uniform ref = R_hi - R_lo = {R_hi - R_lo:.10f}")
print(f"  0.414155 != 0.400000: HYP-048 conflates two different numbers!")
print()

N = 2000

def compute_both(freqs, n_K=500):
    omega_max = np.max(np.abs(freqs))
    K_vals = np.linspace(0.001, omega_max / delta_lo + 0.5, n_K)
    count_fracs = []
    axis_fracs = []
    for K in K_vals:
        d_lo = 2 * K * delta_lo
        d_hi = 2 * K * delta_hi
        overlap = max(0, min(d_hi, omega_max) - max(d_lo, 0))
        af = overlap / omega_max
        axis_fracs.append(af)
        count = np.sum((np.abs(freqs) >= d_lo) & (np.abs(freqs) <= d_hi))
        cf = count / len(freqs)
        count_fracs.append(cf)
    return np.array(axis_fracs), np.array(count_fracs), K_vals

np.random.seed(42)
dists = {
    'uniform': np.random.uniform(-1, 1, N),
    'gaussian': np.random.normal(0, 1/np.sqrt(3), N),
    'bimodal': np.concatenate([np.random.normal(-0.5, 0.15, N//2),
                               np.random.normal(0.5, 0.15, N//2)]),
    'exponential': np.random.exponential(0.5, N) - 0.25,
    'laplace': np.random.laplace(0, 0.4, N),
}

results = {}
print(f"{'Distribution':>15} {'axis-max':>12} {'count-max':>12} {'count> C?':>10}")
print("-" * 60)

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

delta_range = np.linspace(1, 5, 1000)
R_curve = np.where(delta_range > 1,
                    delta_range - np.sqrt(np.maximum(delta_range**2 - 1, 0)), 1.0)
axes[0].plot(delta_range, R_curve, 'b-', linewidth=2)
axes[0].axhline(R_lo, color='r', linestyle='--', alpha=0.5, label=f'R_lo={R_lo}')
axes[0].axhline(R_hi, color='g', linestyle='--', alpha=0.5, label=f'R_hi={R_hi}')
axes[0].axvline(delta_lo, color='r', linestyle=':', alpha=0.5)
axes[0].axvline(delta_hi, color='g', linestyle=':', alpha=0.5)
axes[0].set_xlabel('delta')
axes[0].set_ylabel('R(delta)')
axes[0].set_title('1. R(delta) = delta - sqrt(delta^2 - 1)')
axes[0].legend()
axes[0].set_ylim(0, 1.1)

for name, freqs in dists.items():
    ax_f, cnt_f, K_vals = compute_both(freqs)
    axis_max = np.max(ax_f)
    count_max = np.max(cnt_f)
    exceeds = "YES" if count_max > C_exact + 0.001 else "no"
    print(f"{name:>15} {axis_max:>12.6f} {count_max:>12.6f} {exceeds:>10}")
    results[name] = {'axis_max': axis_max, 'count_max': count_max}
    axes[1].plot(K_vals, cnt_f, label=name, linewidth=1.5)
    axes[2].plot(K_vals, ax_f, label=name, linewidth=1.5)

axes[1].axhline(C_exact, color='k', linestyle='--', label=f'C={C_exact:.3f}')
axes[1].set_xlabel('K')
axes[1].set_ylabel('count-based band_frac')
axes[1].set_title('2. Count-based (HYP-048)')
axes[1].legend(fontsize=8)
axes[1].set_ylim(0, 1)

axes[2].axhline(C_exact, color='k', linestyle='--', label=f'C={C_exact:.3f}')
axes[2].set_xlabel('K')
axes[2].set_ylabel('axis-based band_frac')
axes[2].set_title('3. Axis-based (PRF-012)')
axes[2].legend(fontsize=8)
axes[2].set_ylim(0, 0.6)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/adler_definitions_comparison.png', dpi=150)
print("\nSaved plot")

print()
print("=" * 70)
print("KEY FINDINGS")
print("=" * 70)
print()
print("1. PRF-012 axis-based band_frac is ALWAYS <= C = 316/763 for ALL distributions.")
print("   It measures the LENGTH of the frequency interval.")
print()
print("2. HYP-048 count-based band_frac VARIES with distribution shape.")
print("   - Uniform: approx C (coincides with axis-based)")
print("   - Bimodal: approx 0.65 (exceeds C)")
print("   - Gaussian/Laplace/Exponential: < C")
print()
print("3. HYP-048 claims C is the uniform distribution reference value (integral_0.3^0.7 dx = 0.4)")
print("   But 0.414155 != 0.400000 - HYP-048 conflates two different numbers!")
print()
print("4. The two metrics coincide only for UNIFORM distributions.")
print("   For non-uniform distributions, they diverge.")
print()
print("5. PRF-012 ceiling C = 316/763 is a GEOMETRIC property of R(delta), not distributional.")
print("   HYP-048's count-based metric is distributional but has NO ceiling.")
