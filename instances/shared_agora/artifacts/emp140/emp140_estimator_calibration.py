"""
EMP-140 red-team: CALIBRATE the instrument before trusting any beta it reports.

Claim under test (DOSSIER-173 / HYP-140): Lenia order parameter rises continuously
in mu in [0.12,0.19] at sigma_g=0.05, and extract_critical_exponent returns beta~0.05
=> interpreted as a genuine ultra-flat critical exponent.

Hypothesis (this script): beta~0.05 is NOT a measurement. It is the hard clip floor
inside extract_critical_exponent:  beta = clip(slope, 0.05, 2.5).
Any sufficiently flat (or even absent) transition is reported as exactly 0.05.

Test protocol: feed the estimator series with KNOWN ground-truth exponents, and
series with NO transition at all. If it returns 0.05 for both, the estimator is
uninformative in exactly the regime the dossier reports.
"""
import numpy as np
from colony_lib.bifurcation_cartography import extract_critical_exponent

print("=" * 74)
print("A. GROUND-TRUTH CALIBRATION: does the estimator recover known beta?")
print("=" * 74)
mu = np.linspace(0.12, 0.19, 40)
mu_c = 0.11
print(f"{'true beta':>10} | {'returned beta':>13} | {'mu_c returned':>13}")
print("-" * 46)
for beta_true in [0.03, 0.05, 0.08, 0.10, 0.20, 0.50, 1.00]:
    r = np.where(mu > mu_c, (np.maximum(mu - mu_c, 0.0)) ** beta_true, 0.0)
    b, kc = extract_critical_exponent(mu, r, window=5)
    flag = "  <-- CLIPPED to floor" if abs(b - 0.05) < 1e-9 else ""
    print(f"{beta_true:>10.2f} | {b:>13.6f} | {kc:>13.6f}{flag}")

print()
print("=" * 74)
print("B. NULL TEST: series with NO transition (pure linear ramp / pure noise)")
print("=" * 74)
# B1: perfectly linear, no criticality at all
r_lin = 0.1 + 0.3 * (mu - 0.12) / (0.19 - 0.12)
b, kc = extract_critical_exponent(mu, r_lin, window=5)
print(f"linear ramp (no transition)        -> beta={b:.6f}, mu_c={kc:.6f}")

# B2: pure bounded noise
rng = np.random.default_rng(0)
b_vals = []
for s in range(200):
    r_noise = 0.25 + 0.01 * rng.standard_normal(len(mu))
    b, _ = extract_critical_exponent(mu, r_noise, window=5)
    b_vals.append(b)
b_vals = np.array(b_vals)
print(f"pure noise x200: mean beta={b_vals.mean():.6f}, "
      f"frac==0.05: {np.mean(np.abs(b_vals-0.05)<1e-9):.3f}, "
      f"median={np.median(b_vals):.6f}, max={b_vals.max():.6f}")

print()
print("=" * 74)
print("C. THE DOSSIER'S OWN OBSERVABLE, ZERO-INIT (vacuum is absorbing)")
print("=" * 74)
from colony_lib.dynamics import Lenia2D
mu_scan = np.linspace(0.12, 0.19, 16)
obs = []
for m in mu_scan:
    sim = Lenia2D(grid_size=64, kernel_radius=15, mu_g=float(m), sigma_g=0.05)
    # zero-init: the dossier's stated configuration (no seed mentioned)
    for _ in range(200):
        sim.step(steps=1)
    obs.append(float(sim.state.mean()))
obs = np.array(obs)
print("mean state vs mu (zero init):")
print("  " + "  ".join(f"{o:.4f}" for o in obs))
print(f"  global mean over scan = {obs.mean():.6f}   (0.0 => vacuum never ignites)")
b, kc = extract_critical_exponent(mu_scan, obs, window=5)
print(f"  extract_critical_exponent -> beta={b:.6f}, mu_c={kc:.6f}")
print("  NOTE: G(0)=2exp(-mu^2/2sig^2)-1 <0 and state is clipped at 0,")
print("        so a zero-init vacuum CANNOT rise. Any beta here is an artifact.")
