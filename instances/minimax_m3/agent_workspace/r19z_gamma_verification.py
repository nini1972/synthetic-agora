"""
DOSSIER_003 VERIFICATION: Multi-Timescale Resonance Gap Power Law
Claim: R_cross(Delta_omega) ~ R_0 * (Delta_omega/omega_0)^(-gamma)
       gamma ~ 1.38 ± 0.05

Test: Run two-cluster Kuramoto (one cluster at +omega, other at -omega),
vary gap Delta_omega = 2*omega, compute R_cross = |<exp(i(phi_fast - phi_slow))>|.

Also test Cauchy and Gaussian dispersion WITHIN clusters to check universality.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

np.random.seed(42)

N_per = 50  # oscillators per cluster
K0 = 2.0    # coupling
T = 50.0    # total time
dt = 0.02
N_steps = int(T / dt)
transient = int(20.0 / dt)

def run_two_cluster(Delta_omega, K0, alpha=0, sigma=0.0, dist='gaussian', seed=42):
    rng = np.random.default_rng(seed)
    # Frequencies: cluster +1 at +omega_half, cluster -1 at -omega_half, omega_half=Delta_omega/2
    omega_half = Delta_omega / 2.0
    if dist == 'cauchy':
        # Cauchy: x = tan(pi*(u-0.5)), scale=gamma
        omega_intra = sigma * np.tan(np.pi * (rng.uniform(size=2*N_per) - 0.5))
    else:
        omega_intra = rng.normal(0, sigma, size=2*N_per)
    omega = omega_half * np.concatenate([np.ones(N_per), -np.ones(N_per)]) + omega_intra
    # Phases
    theta = rng.uniform(0, 2*np.pi, 2*N_per)
    R_cross_ts = []
    for step in range(N_steps):
        # Kuramoto
        sin_sum = np.sin(theta[:, None] - theta[None, :]).sum(axis=1)
        # Mean-field coupling
        mean_sin = np.sin(theta - theta.mean())  # not used
        # Standard Kuramoto
        dtheta = omega + (K0 / (2*N_per)) * sin_sum
        if alpha > 0:
            # Compute order parameter
            z = np.exp(1j * theta)
            R = np.abs(z.mean())
            dtheta *= (R ** alpha)
        theta += dt * dtheta
        if step > transient:
            # Cross-correlation: avg(exp(i*(theta_fast - theta_slow)))
            cross_phase = theta[:N_per] - theta[N_per:]
            R_cross_ts.append(np.abs(np.exp(1j*cross_phase).mean()))
    return np.mean(R_cross_ts)

# Test multiple Delta_omega values
Delta_omegas = np.linspace(0.1, 5.0, 20)
R_cross_gauss_intra = []
R_cross_cauchy_intra = []

for dw in Delta_omegas:
    R_g = run_two_cluster(dw, K0, alpha=0, sigma=0.3, dist='gaussian', seed=42)
    R_c = run_two_cluster(dw, K0, alpha=0, sigma=0.3, dist='cauchy', seed=42)
    R_cross_gauss_intra.append(R_g)
    R_cross_cauchy_intra.append(R_c)
    print(f"Delta_omega={dw:.2f}: R_cross_gauss={R_g:.4f}, R_cross_cauchy={R_c:.4f}")

# Fit power law
def power_law(x, R0, gamma):
    return R0 * x**(-gamma)

# Filter out zero/negative values
mask_g = np.array(R_cross_gauss_intra) > 0.01
mask_c = np.array(R_cross_cauchy_intra) > 0.01

try:
    popt_g, _ = curve_fit(power_law, Delta_omegas[mask_g], np.array(R_cross_gauss_intra)[mask_g], p0=[1.0, 1.4])
    popt_c, _ = curve_fit(power_law, Delta_omegas[mask_c], np.array(R_cross_cauchy_intra)[mask_c], p0=[1.0, 1.4])
    print(f"\nGAUSSIAN intra-cluster: gamma = {popt_g[1]:.4f}")
    print(f"CAUCHY intra-cluster: gamma = {popt_c[1]:.4f}")
except Exception as e:
    popt_g = [1.0, 0.0]
    popt_c = [1.0, 0.0]
    print(f"Fit failed: {e}")

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.loglog(Delta_omegas, R_cross_gauss_intra, 'o-', label='Gaussian intra-cluster dispersion')
ax.loglog(Delta_omegas, R_cross_cauchy_intra, 's-', label='Cauchy intra-cluster dispersion')
xx = np.linspace(0.1, 5.0, 100)
ax.loglog(xx, power_law(xx, *popt_g), '--', label=f'Gaussian fit: gamma={popt_g[1]:.3f}')
ax.loglog(xx, power_law(xx, *popt_c), '--', label=f'Cauchy fit: gamma={popt_c[1]:.3f}')
ax.axhline(0.5, color='gray', linestyle=':', label='R=0.5')
ax.set_xlabel('Delta_omega')
ax.set_ylabel('R_cross')
ax.set_title('DOSSIER_003: R_cross vs Delta_omega for Two-Cluster Kuramoto')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/r19z_gamma_verification.png', dpi=120)
print("\nSaved: r19z_gamma_verification.png")
