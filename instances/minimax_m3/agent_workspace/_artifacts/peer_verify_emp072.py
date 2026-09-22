"""Independent verification of EMP-072's master-curve collapse refutation.
We test the claim: R_ss is NOT a single-valued function of K_eff = K0·R^alpha in reflexive Kuramoto.

Method: For each (K0, alpha) pair, run 10 seeds and compute R_ss and K_eff.
Then bin by K_eff and check if R_ss has low variance within each bin.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

N = 150
gamma = 1.0
dt = 0.05
T = 30.0
n_steps = int(T / dt)
trans = int(n_steps * 0.7)

def run(K0, alpha, seed=0, N=N, gamma=gamma):
    rng = np.random.default_rng(seed)
    omega = rng.normal(0, gamma, N)
    theta = rng.uniform(0, 2*np.pi, N)
    R_sum = 0.0
    n_avg = 0
    last_R = 0.0
    for t in range(n_steps):
        Z = np.mean(np.exp(1j * theta))
        R = abs(Z)
        Psi = np.angle(Z)
        # K_eff = K0 * R^alpha, but for alpha < 0 we cap R away from 0
        R_safe = max(R, 1e-9)
        K_eff = K0 * R_safe**alpha
        coupling = K_eff * R * np.sin(Psi - theta)
        theta = theta + dt * (omega + coupling)
        if t >= trans:
            R_sum += R
            n_avg += 1
        last_R = R
    R_ss = R_sum / n_avg
    R_safe_ss = max(R_ss, 1e-9)
    K_eff_ss = K0 * R_safe_ss**alpha
    return R_ss, K_eff_ss

# Scan over (K0, alpha) grid
K0_grid = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
alpha_grid = [-1.0, -0.5, 0.0, 0.5, 1.0, 1.5]
n_seeds = 5

points = []
for K0 in K0_grid:
    for alpha in alpha_grid:
        rs = []
        for s in range(n_seeds):
            r_ss, k_eff = run(K0, alpha, seed=s*7 + 13)
            rs.append((r_ss, k_eff))
        # Average per (K0, alpha)
        R_mean = np.mean([r for r, _ in rs])
        K_mean = np.mean([k for _, k in rs])
        # Sanity: if R_ss = F(K_eff) (a single-valued function),
        # then binning by K_eff should give a tight cluster of R values.
        # We just save all points (1 per (K0, alpha)) for now.
        points.append({'K0': K0, 'alpha': alpha, 'R_ss': R_mean, 'K_eff': K_mean})

# Now bin by K_eff (bins of width 0.5) and check R spread within bin
print("\nMaster-curve collapse test: R_ss vs K_eff")
print("=" * 70)
bins = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0), (5.0, 10.0)]
for lo, hi in bins:
    in_bin = [p for p in points if lo <= p['K_eff'] < hi]
    if not in_bin:
        continue
    R_vals = [p['R_ss'] for p in in_bin]
    span = max(R_vals) - min(R_vals)
    print(f"\nK_eff ∈ [{lo:.1f}, {hi:.1f}): {len(in_bin)} points")
    for p in in_bin:
        print(f"   K0={p['K0']}, α={p['alpha']:+}: R_ss={p['R_ss']:.3f}, K_eff={p['K_eff']:.3f}")
    print(f"   R span in bin = {span:.3f}")
    if span > 0.15:
        print(f"   *** SPAN > 0.15 -> NOT a single-valued function ***")

# Save
with open('peer_emp072_verification.json', 'w') as f:
    json.dump({'points': points, 'bins': [(lo, hi) for lo, hi in bins]}, f, indent=2, default=str)

# Plot R_ss vs K_eff colored by alpha
fig, ax = plt.subplots(figsize=(10, 6))
for alpha in alpha_grid:
    xs = [p['K_eff'] for p in points if p['alpha'] == alpha]
    ys = [p['R_ss'] for p in points if p['alpha'] == alpha]
    ax.scatter(xs, ys, label=f'α={alpha:+.1f}', s=80, alpha=0.8)
ax.set_xlabel(r'$K_{eff} = K_0 \cdot R_{ss}^\alpha$', fontsize=13)
ax.set_ylabel(r'$R_{ss}$', fontsize=13)
ax.set_title('Master-Curve Collapse Test: R_ss vs K_eff\n(if collapse held, all points would lie on a curve)')
ax.legend(fontsize=10, ncol=2)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('peer_emp072_master_curve.png', dpi=120)
print("\nSaved peer_emp072_master_curve.png")