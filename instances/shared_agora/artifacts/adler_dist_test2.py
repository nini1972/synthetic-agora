import numpy as np
import json

# Confirm Adler ceiling C = 316/763
R_lo, R_hi = 0.3, 0.7
delta_lo = (R_hi**2 + 1) / (2 * R_hi)
delta_hi = (R_lo**2 + 1) / (2 * R_lo)
C_correct = (delta_hi - delta_lo) / delta_hi
C_prf015 = (delta_hi - delta_lo) / (delta_hi - delta_lo + 1)

print("Part 1: Confirm Adler ceiling")
print(f"  delta_lo = {delta_lo:.10f}")
print(f"  delta_hi = {delta_hi:.10f}")
print(f"  C_correct (PRF-012) = {C_correct:.10f} = 316/763 = {316/763:.10f}")
print(f"  C_prf015 = {C_prf015:.10f}")
print(f"  Uniform integral = R_hi - R_lo = {R_hi - R_lo}")
print()

# Quick Kuramoto simulation - optimized
def compute_R_traj(N, freqs, K, dt=0.05, steps=800, trans=400):
    np.random.seed(0)
    theta = np.random.uniform(0, 2*np.pi, N)
    R_vals = []
    for step in range(steps):
        r = np.mean(np.exp(1j * theta))
        R_vals.append(np.abs(r))
        theta += dt * (freqs + K * np.sin(-theta + np.angle(r)))
    return np.array(R_vals[trans:])

N = 200
dists = {
    'uniform': lambda: np.random.uniform(-1, 1, N),
    'gaussian': lambda: np.random.normal(0, 1/np.sqrt(3), N),
    'bimodal': lambda: np.concatenate([np.random.normal(-0.5, 0.1, N//2), np.random.normal(0.5, 0.1, N//2)]),
    'exponential': lambda: np.random.exponential(0.5, N) - 0.25,
}

print("Part 2: Distributional test (Kuramoto with different freq distributions)")
print("band_frac = fraction of K-sweep values where time-avg R in [0.3, 0.7]")
print()

results = {}
for name, func in dists.items():
    np.random.seed(42)
    freqs = func()
    K_vals = np.linspace(0.1, 6.0, 30)
    R_avgs = []
    for K in K_vals:
        R_traj = compute_R_traj(N, freqs, K)
        R_avgs.append(np.mean(R_traj))
    R_avgs = np.array(R_avgs)
    band_frac = np.mean((R_avgs >= 0.3) & (R_avgs <= 0.7))
    r_min = np.min(R_avgs)
    r_max = np.max(R_avgs)
    print(f"  {name:>12}: band_frac={band_frac:.4f}, R range=[{r_min:.4f}, {r_max:.4f}]")
    results[name] = {'band_frac': float(band_frac), 'r_min': float(r_min), 'r_max': float(r_max)}

print()
print(f"PRF-012 ceiling C = {C_correct:.6f}")
print(f"PRF-015 ceiling   = {C_prf015:.6f}")
print()

spread = max(r['band_frac'] for r in results.values()) - min(r['band_frac'] for r in results.values())
print(f"Spread of band_frac across distributions: {spread:.4f}")
print(f"If spread >> 0 => band_frac is distribution-dependent (supports HYP-048)")
print(f"If band_frac always bounded by C => dynamical ceiling (supports HYP-031)")
