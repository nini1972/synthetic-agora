import numpy as np
import json

# Confirm Adler ceiling C = 316/763
R_lo, R_hi = 0.3, 0.7
delta_lo = (R_hi**2 + 1) / (2 * R_hi)
delta_hi = (R_lo**2 + 1) / (2 * R_lo)
C_correct = (delta_hi - delta_lo) / delta_hi
C_prf015 = (delta_hi - delta_lo) / (delta_hi - delta_lo + 1)

print("Part 1: Confirm Adler ceiling")
print(f"  delta_lo = {delta_lo}")
print(f"  delta_hi = {delta_hi}")
print(f"  C_correct (PRF-012) = {C_correct} = 316/763 = {316/763}")
print(f"  C_prf015 = {C_prf015}")
print(f"  Uniform integral = R_hi - R_lo = {R_hi - R_lo}")
print()

# Kuramoto simulation with different frequency distributions
def compute_band_frac(N, freqs, K, dt=0.02, t_trans=50, t_meas=100, n_seeds=2):
    results = []
    for seed in range(n_seeds):
        np.random.seed(seed)
        theta = np.random.uniform(0, 2*np.pi, N)
        R_values = []
        for step in range(int((t_trans + t_meas) / dt)):
            r_complex = np.mean(np.exp(1j * theta))
            R_inst = np.abs(r_complex)
            if step * dt >= t_trans:
                R_values.append(R_inst)
            theta += dt * (freqs + K * np.sin(np.angle(r_complex) - theta))
        results.append(np.mean(R_values))  # time-averaged R
    return np.mean(results)

N = 500
dists = {
    'uniform': lambda: np.random.uniform(-1, 1, N),
    'gaussian': lambda: np.random.normal(0, 1/np.sqrt(3), N),
    'bimodal': lambda: np.concatenate([np.random.normal(-0.5, 0.1, N//2), np.random.normal(0.5, 0.1, N//2)]),
    'exponential': lambda: np.random.exponential(0.5, N) - 0.25,
}

print("Part 2: Distributional test (Kuramoto with different freq distributions)")
print("band_frac defined as fraction of K-sweep where time-avg R in [0.3, 0.7]")
print()

results = {}
for name, func in dists.items():
    np.random.seed(42)
    freqs = func()
    K_vals = np.linspace(0.1, 10.0, 50)
    R_avgs = [compute_band_frac(N, freqs, K) for K in K_vals]
    R_avgs = np.array(R_avgs)
    # band_frac = fraction in [0.3, 0.7]
    band_frac = np.mean((R_avgs >= 0.3) & (R_avgs <= 0.7))
    r_min = np.min(R_avgs)
    r_max = np.max(R_avgs)
    exceeds = r_max > 0.7  # does R ever leave the intermediate band entirely?
    print(f"  {name:>12}: band_frac={band_frac:.4f}, R range=[{r_min:.4f}, {r_max:.4f}]")
    results[name] = {'band_frac': float(band_frac), 'r_min': float(r_min), 'r_max': float(r_max)}

print()
print(f"PRF-012 ceiling C = {C_correct:.6f}")
print(f"PRF-015 ceiling   = {C_prf015:.6f}")
print()

# Check: does HYP-048's claim hold? band_frac depends on distribution shape?
spread = max(r['band_frac'] for r in results.values()) - min(r['band_frac'] for r in results.values())
print(f"Spread of band_frac across distributions: {spread:.4f}")
print(f"If spread >> 0 => band_frac is distribution-dependent (supports HYP-048)")
print(f"If band_frac always bounded by C => dynamical ceiling (supports HYP-031)")
