"""
DOSSIER_003 v2: Test R_cross scaling with non-linear feedback enabled
and with explicit Arnold tongue regime.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

np.random.seed(42)

N_per = 30
K0 = 2.0
T = 40.0
dt = 0.05
N_steps = int(T / dt)
transient = int(15.0 / dt)

def run_two_cluster_alpha(Delta_omega, K0, alpha, sigma_intra=0.1, dist='gaussian', seed=42):
    rng = np.random.default_rng(seed)
    omega_half = Delta_omega / 2.0
    if dist == 'cauchy':
        omega_intra = sigma_intra * np.tan(np.pi * (rng.uniform(size=2*N_per) - 0.5))
    else:
        omega_intra = rng.normal(0, sigma_intra, size=2*N_per)
    omega = omega_half * np.concatenate([np.ones(N_per), -np.ones(N_per)]) + omega_intra
    theta = rng.uniform(0, 2*np.pi, 2*N_per)
    R_cross_ts = []
    R_fast_ts = []
    R_slow_ts = []
    for step in range(N_steps):
        sin_sum = np.sin(theta[:, None] - theta[None, :]).sum(axis=1)
        dtheta = omega + (K0 / (2*N_per)) * sin_sum
        if alpha > 0:
            z = np.exp(1j * theta)
            R = np.abs(z.mean())
            dtheta *= (R ** alpha)
        theta += dt * dtheta
        if step > transient:
            cross_phase = theta[:N_per] - theta[N_per:]
            R_cross_ts.append(np.abs(np.exp(1j*cross_phase).mean()))
            z_f = np.exp(1j * theta[:N_per]).mean()
            z_s = np.exp(1j * theta[N_per:]).mean()
            R_fast_ts.append(np.abs(z_f))
            R_slow_ts.append(np.abs(z_s))
    return np.mean(R_cross_ts), np.mean(R_fast_ts), np.mean(R_slow_ts)

print("=== alpha=2, Gaussian intra, K0=2.0, sigma=0.1 ===")
Delta_omegas = np.linspace(0.1, 3.0, 15)
results_alpha2_gauss = []
for dw in Delta_omegas:
    rc, rf, rs = run_two_cluster_alpha(dw, K0, alpha=2, sigma_intra=0.1, dist='gaussian', seed=42)
    results_alpha2_gauss.append((dw, rc, rf, rs))
    print(f"  Dw={dw:.2f}: R_cross={rc:.4f}, R_fast={rf:.4f}, R_slow={rs:.4f}")

print("\n=== alpha=2, Cauchy intra, K0=2.0, sigma=0.1 ===")
results_alpha2_cauchy = []
for dw in Delta_omegas:
    rc, rf, rs = run_two_cluster_alpha(dw, K0, alpha=2, sigma_intra=0.1, dist='cauchy', seed=42)
    results_alpha2_cauchy.append((dw, rc, rf, rs))
    print(f"  Dw={dw:.2f}: R_cross={rc:.4f}, R_fast={rf:.4f}, R_slow={rs:.4f}")

print("\n=== K0=0.5, alpha=0, Gaussian intra, sigma=0.3 ===")
Delta_omegas2 = np.linspace(0.1, 2.0, 15)
results_lowK = []
for dw in Delta_omegas2:
    rc, rf, rs = run_two_cluster_alpha(dw, K0=0.5, alpha=0, sigma_intra=0.3, dist='gaussian', seed=42)
    results_lowK.append((dw, rc, rf, rs))
    print(f"  Dw={dw:.2f}: R_cross={rc:.4f}, R_fast={rf:.4f}, R_slow={rs:.4f}")

def power_law(x, R0, gamma):
    return R0 * x**(-gamma)

def fit_gamma(ws, rs, label):
    rs = np.array(rs)
    mask = rs > 0.02
    if mask.sum() > 3:
        try:
            popt, _ = curve_fit(power_law, np.array(ws)[mask], rs[mask], p0=[1.0, 1.4])
            print(f"  {label}: gamma = {popt[1]:.4f}, R0 = {popt[0]:.4f}")
            return popt
        except Exception as e:
            print(f"  {label}: fit failed ({e})")
            return None
    print(f"  {label}: insufficient data points")
    return None

print("\n=== Power Law Fits ===")
ws_g, _, rfs_g, rss_g = zip(*results_alpha2_gauss)
ws_c, _, rfs_c, rss_c = zip(*results_alpha2_cauchy)
ws_l, _, rfs_l, rss_l = zip(*results_lowK)
rcs_g = [r[1] for r in results_alpha2_gauss]
rcs_c = [r[1] for r in results_alpha2_cauchy]
rcs_l = [r[1] for r in results_lowK]

fit_gamma(ws_g, rcs_g, "alpha=2, Gaussian: R_cross")
fit_gamma(ws_c, rcs_c, "alpha=2, Cauchy: R_cross")
fit_gamma(ws_l, rcs_l, "K0=0.5, alpha=0, Gaussian: R_cross")
fit_gamma(ws_g, rfs_g, "alpha=2, Gaussian: R_fast")
fit_gamma(ws_g, rss_g, "alpha=2, Gaussian: R_slow")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ax = axes[0]
ax.loglog(ws_g, rcs_g, 'o-', label='alpha=2, Gaussian intra')
ax.loglog(ws_c, rcs_c, 's-', label='alpha=2, Cauchy intra')
ax.loglog(ws_l, rcs_l, '^-', label='K0=0.5, alpha=0')
ax.set_xlabel('Delta_omega')
ax.set_ylabel('R_cross')
ax.set_title('R_cross vs Delta_omega (varied regimes)')
ax.legend()
ax.grid(True, alpha=0.3)

ax = axes[1]
ax.semilogx(ws_g, rfs_g, 'o-', label='R_fast (Gaussian)')
ax.semilogx(ws_g, rss_g, 's-', label='R_slow (Gaussian)')
ax.set_xlabel('Delta_omega')
ax.set_ylabel('R (cluster order parameter)')
ax.set_title('Intra-cluster order vs gap (alpha=2)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/r19z_gamma_verification_v2.png', dpi=120)
print("\nSaved: r19z_gamma_verification_v2.png")
