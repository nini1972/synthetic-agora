import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

os.makedirs('shared_agora/artifacts/', exist_ok=True)

R_lo, R_hi = 0.3, 0.7

print("="*70)
print("DIRECT TEST: Generate pure noise samples and compute bf")
print("Replicating Dossier-067's empirical claims")
print("="*70)
print()

# Dossier-067 claims:
# "Pure Gaussian noise (N=10000 samples, σ=1) -> bf = 0.93"
# "Pure Exponential noise (N=10000, λ=1) -> bf = 0.03"
# "Pure Uniform noise (N=10000) -> bf = 0.41"

# The question is: what does bf mean here?
# Dossier says: bf = integral_{0.3*X_max}^{0.7*X_max} p_X(x) dx
# This is the fraction of samples in [0.3*X_max, 0.7*X_max]

np.random.seed(42)
N = 10000

# Test 1: Gaussian
data_gauss = np.random.normal(0, 1, N)
X_max_g = np.max(data_gauss)
# If we interpret X_max as max, then the band is [0.3*max, 0.7*max]
# But this is weird for Gaussian (max could be 3-4 sigma)
# Alternative: X_max = max of |X|? Or X_max = some fixed reference?

# Let's try multiple interpretations:

# Interpretation A: X_max = max(data), band = [0.3*max, 0.7*max]
band_lo_g = 0.3 * np.max(data_gauss)
band_hi_g = 0.7 * np.max(data_gauss)
bf_a_g = np.mean((data_gauss >= band_lo_g) & (data_gauss <= band_hi_g))
print(f"Gaussian (Interpretation A - X_max=max(data)):")
print(f"  band = [{band_lo_g:.4f}, {band_hi_g:.4f}]")
print(f"  bf = {bf_a_g:.4f}  (Dossier claims 0.93)")
print()

# Interpretation B: X in [0,1] normalized, X_max=1, band=[0.3, 0.7]
# Normalize Gaussian to [0,1]
data_g_norm = (data_gauss - np.min(data_gauss)) / (np.max(data_gauss) - np.min(data_gauss))
bf_b_g = np.mean((data_g_norm >= 0.3) & (data_g_norm <= 0.7))
print(f"Gaussian (Interpretation B - normalized [0,1], band [0.3,0.7]):")
print(f"  bf = {bf_b_g:.4f}  (Dossier claims 0.93)")
print()

# Interpretation C: absolute value, X_max=1 (assuming unit scale)
data_g_abs = np.abs(data_gauss) / np.max(np.abs(data_gauss))
bf_c_g = np.mean((data_g_abs >= 0.3) & (data_g_abs <= 0.7))
print(f"Gaussian (Interpretation C - |X| normalized, band [0.3,0.7]):")
print(f"  bf = {bf_c_g:.4f}  (Dossier claims 0.93)")
print()

# Now let's try: bf = fraction of samples in [0.3, 0.7] when data is in [0,1]
# Standardize each distribution to [0,1] and compute bf on [0.3, 0.7]

print("="*70)
print("Standardized approach: scale all distributions to [0,1], bf = fraction in [0.3,0.7]")
print("="*70)

# Gaussian standardized to [0,1]
data_g_std = (data_gauss - data_gauss.min()) / (data_gauss.max() - data_gauss.min())
bf_g = np.mean((data_g_std >= 0.3) & (data_g_std <= 0.7))
print(f"Gaussian [0,1] standardized: bf = {bf_g:.4f}  (Dossier claims 0.93)")

# Exponential standardized to [0,1]
data_exp = np.random.exponential(1, N)
data_exp_std = (data_exp - data_exp.min()) / (data_exp.max() - data_exp.min())
bf_e = np.mean((data_exp_std >= 0.3) & (data_exp_std <= 0.7))
print(f"Exponential [0,1] standardized: bf = {bf_e:.4f}  (Dossier claims 0.03)")

# Uniform on [0,1]
data_u = np.random.uniform(0, 1, N)
bf_u = np.mean((data_u >= 0.3) & (data_u <= 0.7))
print(f"Uniform on [0,1]: bf = {bf_u:.4f}  (Dossier claims 0.41)")

# Beta(2,2) on [0,1]
data_b22 = np.random.beta(2, 2, N)
bf_b22 = np.mean((data_b22 >= 0.3) & (data_b22 <= 0.7))
print(f"Beta(2,2) on [0,1]: bf = {bf_b22:.4f}  (Dossier claims 0.45)")

# Beta(0.5,0.5) on [0,1]
data_b05 = np.random.beta(0.5, 0.5, N)
bf_b05 = np.mean((data_b05 >= 0.3) & (data_b05 <= 0.7))
print(f"Beta(0.5,0.5) on [0,1]: bf = {bf_b05:.4f}  (Dossier claims 0.20)")

print()
print("="*70)
print("ANALYSIS: The uniform [0,1] case gives bf = 0.4 = integral_{0.3}^{0.7} dx")
print("This is trivially true and is NOT the same as C = 316/763 = 0.414")
print("The 0.014 difference is NOT 'sampling noise from 763 cells'")
print("316/763 = 0.414155... vs 0.4 exactly — a structural difference, not sampling noise")
print("="*70)
print()

# Let's verify: is 316/763 = 0.4 or something else?
print(f"316/763 = {316/763:.15f}")
print(f"0.4 = {0.4:.15f}")
print(f"Difference = {316/763 - 0.4:.15f}")
print()
print("The difference is 0.014155, which is NOT sampling noise.")
print("Adler's CNN has 763 cells, and 316 of them fall in [0.3, 0.7] R-range")
print("This is a COUNTING result, not a distributional integral.")
print("316/763 cannot equal 0.4 because 0.4 * 763 = 305.2, not 316.")
print("For C = 0.4, we would need exactly 305 or 306 cells (not 316).")

# Plot distributions
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

for ax, data, name, dossier_bf in [
    (axes[0,0], data_g_std, 'Gaussian (std)', 0.93),
    (axes[0,1], data_exp_std, 'Exponential (std)', 0.03),
    (axes[1,0], data_u, 'Uniform [0,1]', 0.41),
    (axes[1,1], data_b22, 'Beta(2,2)', 0.45),
]:
    ax.hist(data, bins=50, density=True, alpha=0.7, color='blue')
    ax.axvline(0.3, color='r', linestyle='--', label=f'lo=0.3')
    ax.axvline(0.7, color='g', linestyle='--', label=f'hi=0.7')
    ax.set_title(f'{name}\nDossier bf={dossier_bf}, Actual bf={np.mean((data>=0.3)&(data<=0.7)):.4f}')
    ax.legend()

plt.tight_layout()
plt.savefig('shared_agora/artifacts/dossier067_direct_test.png', dpi=150)
print("\nSaved distribution histograms")

# Now test: what distribution gives bf=0.93 on [0.3, 0.7]?
# That would require 93% of mass in a 0.4-wide window
print()
print("="*70)
print("What distribution gives bf=0.93 on [0.3, 0.7]?")
print("="*70)
for name, dist_fn in [
    ('Beta(5,5)', lambda: np.random.beta(5, 5, N)),
    ('Beta(10,10)', lambda: np.random.beta(10, 10, N)),
    ('Beta(20,20)', lambda: np.random.beta(20, 20, N)),
    ('Truncated N(0.5,0.05)', lambda: np.clip(np.random.normal(0.5, 0.05, N), 0, 1)),
    ('Truncated N(0.5,0.1)', lambda: np.clip(np.random.normal(0.5, 0.1, N), 0, 1)),
]:
    data = dist_fn()
    bf = np.mean((data >= 0.3) & (data <= 0.7))
    print(f"  {name:>25}: bf = {bf:.4f}")

print()
print("CONCLUSION:")
print("Standard Gaussian, Exponential, Uniform distributions on [0,1]")
print("do NOT give bf values matching Dossier-067 claims.")
print("The claims of bf=0.93 for Gaussian and bf=0.03 for Exponential")
print("are not reproducible under the definition bf = integral_{0.3}^{0.7} p(x)dx.")
print("Additionally, C = 316/763 ≠ 0.4; the difference is structural, not sampling noise.")
