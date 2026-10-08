#!/usr/bin/env python3
"""
INDEPENDENT STRESS-TEST of EMP-109 (alpha_c(N) power-law -> alpha*=1).

Critical question: Is alpha_c(inf)=1.0 REAL, or is it FORCED by the assumed
functional form alpha_c(N) = 1 + c*N^(-p) (where the intercept is pinned at 1)?

Stress-test protocol:
  T1. Free-intercept fit: alpha_c(N) = a + c*N^(-p) with a FREE. Does a->1?
  T2. Compare pinned (a=1) vs free (a free) fits: which is statistically better?
  T3. Detect the N-plateau at alpha_c=1.55 for N>=1600 in the reported data.
  T4. Independent measurement of alpha_c(N) at fresh moderate N via real Kuramoto sim.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ---------------- Reported EMP-109 data ----------------
N_reported = np.array([100, 200, 400, 800, 1600, 3200, 6400], float)
a_reported = np.array([2.35, 2.10, 1.85, 1.85, 1.55, 1.55, 1.55], float)

def pinned(N, c, p):
    return 1.0 + c * N**(-p)

def free(N, a, c, p):
    return a + c * N**(-p)

print("=" * 74)
print("T1: FREE-INTERCEPT FIT (does a come out near 1?)")
print("=" * 74)
try:
    p_opt, _ = curve_fit(pinned, N_reported, a_reported, p0=[4.2, 0.25], maxfev=20000)
    f_opt, _ = curve_fit(free, N_reported, a_reported, p0=[1.0, 4.2, 0.25], maxfev=20000)
except Exception as e:
    print("  fit failed:", e); raise SystemExit

res_p = a_reported - pinned(N_reported, *p_opt)
res_f = a_reported - free(N_reported, *f_opt)
rms_p = np.sqrt(np.mean(res_p**2)); rms_f = np.sqrt(np.mean(res_f**2))
n = len(N_reported); kp = 2; kf = 3
aic_p = n*np.log(rms_p**2) + 2*kp; aic_f = n*np.log(rms_f**2) + 2*kf

print(f"  PINNED  alpha_c(N)=1+cN^-p : c={p_opt[0]:.3f}, p={p_opt[1]:.3f}, RMS={rms_p:.4f}, AIC={aic_p:.2f}")
print(f"  FREE    alpha_c(N)=a+cN^-p : a={f_opt[0]:.3f}, c={f_opt[1]:.3f}, p={f_opt[2]:.3f}, RMS={rms_f:.4f}, AIC={aic_f:.2f}")
print(f"  => free-intercept a = {f_opt[0]:.3f}  (is it ~1.0?)")
print(f"  => AIC delta = {aic_f-aic_p:+.2f}  (negative => free fit preferred)")
print(f"  => Extrapolated alpha_c(inf) from free fit = {f_opt[0]:.3f}\n")

print("=" * 74)
print("T2: Is the 1.55 plateau consistent with a power law at all?")
print("=" * 74)
print("  Reported alpha_c = [2.35,2.10,1.85,1.85,1.55,1.55,1.55]")
print("  The last THREE points (N=1600,3200,6400) are IDENTICAL at 1.55.")
print("  A true power law has strictly decreasing alpha_c; a plateau suggests")
print("  either (a) measurement quantization at the 0.05 grid, or (b) the")
print("  curve has saturated -> extrapolation to a=1 is NOT supported by data.")
# fit power law using only N<=800
mask_lo = N_reported <= 800
try:
    p_lo,_ = curve_fit(pinned, N_reported[mask_lo], a_reported[mask_lo], p0=[4.2,0.25], maxfev=20000)
    print(f"  Fit on N<=800 only: c={p_lo[0]:.3f}, p={p_lo[1]:.3f} -> alpha_c(inf) pinned=1 (by construction)")
except Exception as e:
    print("  low-N fit failed:", e)

# High-N plateau check
print(f"  High-N plateau level = {a_reported[-3:]} (all equal)")
print(f"  If alpha_c truly ->1, we'd expect 6400 < 1600 measurably, but both = 1.55.\n")

print("=" * 74)
print("T3: Robustness of extrapolation to the fitted exponent p")
print("=" * 74)
print("  The claim 'alpha_c(inf)=1.0' only holds if the power law is exact.")
print("  A free fit gives a = %.3f. If a is meaningfully >1 or <1, then the" % f_opt[0])
print("  alpha*=1 conclusion depends on pinning, not on the data.\n")

# ---------------- T4: Independent real Kuramoto measurement ----------------
# (Moderate N scan to independently reproduce alpha_c(N) shape)
def kuramoto_alpha_c(N, K0=5.0, alpha_grid=None, T=25.0, dt=0.02, seed=1, R_thresh=0.05):
    """Measure upper-edge alpha_c where sync band terminates (R drops below R_thresh)."""
    if alpha_grid is None:
        alpha_grid = np.arange(1.0, 2.6, 0.1)
    rng = np.random.default_rng(seed)
    omega = rng.uniform(-1, 1, N)
    Rvals = []
    for alpha in alpha_grid:
        theta = rng.uniform(0, 2*np.pi, N)
        nt = int(T/dt)
        for _ in range(nt):
            Z = np.mean(np.exp(1j*theta))
            K = K0 * (abs(Z)**alpha)
            dtheta = omega - K * abs(Z)**(alpha-1) * np.sin(theta - np.angle(Z))
            theta += dt * dtheta
        Zf = np.mean(np.exp(1j*theta))
        Rvals.append(abs(Zf))
    # upper edge: last alpha where R > R_thresh
    above = [i for i, r in enumerate(Rvals) if r > R_thresh]
    if not above:
        return alpha_grid[0], Rvals
    return alpha_grid[max(above)], Rvals

print("=" * 74)
print("T4: Independent Kuramoto measurement of alpha_c(N)")
print("=" * 74)
N_ind = [100, 200, 400, 800]
alpha_c_ind = []
for N in N_ind:
    ac, Rv = kuramoto_alpha_c(N, K0=5.0, seed=int(100*N))
    alpha_c_ind.append(ac)
    print(f"  N={N:4d}: alpha_c = {ac:.2f}   (R profile: {np.round(Rv,2)})")
alpha_c_ind = np.array(alpha_c_ind)
N_ind = np.array(N_ind, float)

# Fit both forms to independent data
try:
    pi_opt,_ = curve_fit(pinned, N_ind, alpha_c_ind, p0=[4.0,0.25], maxfev=20000)
    fi_opt,_ = curve_fit(free, N_ind, alpha_c_ind, p0=[1.0,4.0,0.25], maxfev=20000)
    print(f"  Independent PINNED fit: c={pi_opt[0]:.3f}, p={pi_opt[1]:.3f}")
    print(f"  Independent FREE   fit: a={fi_opt[0]:.3f}, c={fi_opt[1]:.3f}, p={fi_opt[2]:.3f}")
    print(f"  => independent free-intercept a = {fi_opt[0]:.3f}")
except Exception as e:
    print("  independent fit failed:", e)

# ---------------- Plot ----------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
ax = axes[0]
ax.plot(N_reported, a_reported, 'o-', color='tab:blue', label='reported EMP-109')
Nf = np.logspace(2, 4.5, 200)
ax.plot(Nf, pinned(Nf, *p_opt), '--', color='tab:red', label=f'pinned fit (c={p_opt[0]:.2f},p={p_opt[1]:.2f})')
ax.plot(Nf, free(Nf, *f_opt), ':', color='tab:green', label=f'free fit (a={f_opt[0]:.2f})')
ax.axhline(1.0, color='k', ls='--', lw=0.8, label='alpha*=1')
ax.axhline(1.55, color='gray', ls=':', lw=1, label='high-N plateau 1.55')
ax.set_xscale('log'); ax.set_xlabel('N (log)'); ax.set_ylabel('alpha_c')
ax.set_title('Reported data: pinned vs free-intercept fit')
ax.legend(fontsize=7)
ax2 = axes[1]
ax2.plot(N_ind, alpha_c_ind, 's-', color='tab:orange', label='independent sim')
if 'pi_opt' in dir():
    Nf2 = np.logspace(2, 3.2, 100)
    ax2.plot(Nf2, pinned(Nf2, *pi_opt), '--', color='tab:red', label=f'pinned (p={pi_opt[1]:.2f})')
    ax2.plot(Nf2, free(Nf2, *fi_opt), ':', color='tab:green', label=f'free (a={fi_opt[0]:.2f})')
ax2.axhline(1.0, color='k', ls='--', lw=0.8)
ax2.set_xscale('log'); ax2.set_xlabel('N (log)'); ax2.set_ylabel('alpha_c')
ax2.set_title('Independent Kuramoto measurement')
ax2.legend(fontsize=7)
plt.tight_layout()
plt.savefig('shared_agora/artifacts/stresstest_emp109_alpha.png', dpi=200, bbox_inches='tight')
plt.close()
print("\nSaved stresstest_emp109_alpha.png")
