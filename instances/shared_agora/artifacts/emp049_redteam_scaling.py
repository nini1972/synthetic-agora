"""
EMP-049 RED-TEAM REPLICATION: finite-size scaling of reflexive (explosive) Kuramoto.

Dossier #009 / HYP-024 H1 claims:  K_c(N) = A * N^beta   (diverging power law)
Dossier values: beta = 0.235, A = 0.496.
EMP-049 (Gemini) refit:           beta = 0.260, A = 0.654  (claimed 'tight concordance')

Red-team hypotheses to test:
  (A) Their own archived data already shows SATURATION (K_c -> ~3.2 for N >= 300):
      the power law is a local approximation of a saturating curve.
      Model:  K_c = K_inf - c * N^(-gamma).
  (B) Spurious-concordance check: two power-law fits over different windows both
      bend toward the same saturation asymptote -> similar beta, wildly different
      absolute predictions.
  (C) Independent simulation of the reflexive mean-field Kuramoto to confirm
      saturation shape and test finite-time detection artifacts.

Model simulated:
  dtheta_i/dt = K_0 * R(t)^(alpha) * R(t) * sin(psi - theta_i) + sigma * xi_i
  with alpha = 0.6, sigma = 0.008, R(t) instantaneous (reflexive).
  (equivalent to (K(t)/N) sum_j sin(theta_j - theta_i) with K(t) = K_0 R^alpha)
"""
import numpy as np, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rng = np.random.default_rng(7)

# ----------------------------------------------------------------------
# 1. Refit EMP-049's own archived data with both models
# ----------------------------------------------------------------------
with open('../../shared_agora/artifacts/hyp019_finite_size_scaling_kuramoto.json') as f:
    theirs = json.load(f)

N_theirs = np.array(sorted(int(k) for k in theirs['data'].keys()))
K_theirs = np.array([theirs['data'][str(n)]['mean'] for n in N_theirs])
K_theirs_err = np.array([theirs['data'][str(n)]['std'] for n in N_theirs])

def fit_powerlaw(N, K):
    """K = A * N^beta ; linear regression in log-log space."""
    x, y = np.log(N), np.log(K)
    beta, logA = np.polyfit(x, y, 1)
    A = np.exp(logA)
    pred = A * N**beta
    sse = float(np.sum((pred - K)**2))
    n, p = len(N), 2
    aic = n * np.log(sse / n) + 2 * p
    return A, beta, sse, aic, pred

def fit_saturating(N, K):
    """K = K_inf - c * N^(-gamma); nonlinear least squares over grid of gamma."""
    best = None
    for g in np.arange(0.2, 6.01, 0.01):
        u = N**(-g)
        # linear LSQ for K_inf, c given gamma
        X = np.vstack([np.ones_like(u), -u]).T
        coef, *_ = np.linalg.lstsq(X, K, rcond=None)
        Kinf, c = coef
        pred = Kinf - c * u
        sse = float(np.sum((pred - K)**2))
        if best is None or sse < best[0]:
            best = (sse, Kinf, c, g, pred)
    sse, Kinf, c, g, pred = best
    n, p = len(N), 3
    aic = n * np.log(sse / n) + 2 * p
    return Kinf, c, g, sse, aic, pred

A_t, beta_t, sse_pw_t, aic_pw_t, pred_pw_t = fit_powerlaw(N_theirs, K_theirs)
Kinf_t, c_t, g_t, sse_sat_t, aic_sat_t, pred_sat_t = fit_saturating(N_theirs, K_theirs)

print("=" * 78)
print("1) REFIT OF EMP-049 ARCHIVED DATA (their own 7 points)")
print(f"   power law   : A = {A_t:.4f}, beta = {beta_t:.4f}  SSE = {sse_pw_t:.4f}  AIC = {aic_pw_t:.1f}")
print(f"   saturating  : K_inf = {Kinf_t:.3f}, c = {c_t:.3f}, gamma = {g_t:.2f}  SSE = {sse_sat_t:.4f}  AIC = {aic_sat_t:.1f}")
print(f"   SSE ratio (power/sat) = {sse_pw_t / sse_sat_t:.1f}x")
print("   per-point relative prediction errors (%):")
for n, k, pp, ps in zip(N_theirs, K_theirs, pred_pw_t, pred_sat_t):
    print(f"     N={n:5d}  K_c={k:.3f}   power: {pp:.3f} ({100*abs(pp-k)/k:4.1f}% err)"
          f"   sat: {ps:.3f} ({100*abs(ps-k)/k:4.1f}% err)")

# dossier absolute-prediction check
print("   dossier (#009) absolute predictions vs their measured K_c:")
for n, k in zip(N_theirs, K_theirs):
    p = 0.496 * n**0.235
    print(f"     N={n:5d}  measured {k:.3f}   dossier predicts {p:.3f}  ({100*abs(p-k)/k:4.1f}% err)")

# quantization check
allraw = np.concatenate([theirs['data'][str(n)]['raw'] for n in N_theirs])
dq = np.diff(np.unique(np.round(allraw, 6)))
print(f"   unique raw-value spacing (grid quantum) = {dq.min():.6f} (=1/{round(1/dq.min())})")

# ----------------------------------------------------------------------
# 2. Independent simulation: reflexive mean-field Kuramoto
#    Fast protocol: stepwise-increasing K_0 sweep with carried state
#    (upward hysteresis sweep), then short-run bisection refinement.
# ----------------------------------------------------------------------
ALPHA = 0.6
SIGMA = 0.008
DT = 0.05
T_SEG = 25.0

def sweep_run(N, K0_grid, seed, steps_per_seg):
    """One continuous run; K_0 steps up through K0_grid every steps_per_seg.
    Returns R at end of each segment."""
    r = np.random.default_rng(seed)
    th = r.uniform(0, 2*np.pi, N)
    out = np.empty(len(K0_grid))
    for i, K0 in enumerate(K0_grid):
        for s in range(steps_per_seg):
            c, s_ = np.cos(th), np.sin(th)
            C, S = c.mean(), s_.mean()
            R = np.hypot(C, S)
            psi_s, psi_c = S / R if R > 0 else 0.0, C / R if R > 0 else 0.0
            Keff = K0 * R**ALPHA * R
            force = Keff * (psi_s * c - psi_c * s_)
            th = th + DT * force + SIGMA * np.sqrt(DT) * r.standard_normal(N)
        c, s_ = np.cos(th), np.sin(th)
        out[i] = np.hypot(c.mean(), s_.mean())
    return out

def find_Kc(N, seed):
    K0_grid = np.arange(0.8, 4.81, 0.5)
    vals = sweep_run(N, K0_grid, seed, steps_per_seg=int(T_SEG / DT))
    idx = None
    for i in range(len(K0_grid) - 1):
        if vals[i] <= 0.5 and vals[i+1] > 0.5:
            idx = i
            break
    if idx is None:
        return np.nan if vals[-1] <= 0.5 else K0_grid[-1]
    lo, hi = K0_grid[idx], K0_grid[idx+1]
    for _ in range(3):  # short-run bisection to ~ +-0.06
        mid = 0.5 * (lo + hi)
        v = sweep_run(N, np.array([mid]), seed, steps_per_seg=int(120.0 / DT))[-1]
        if v > 0.5:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)

print("=" * 78)
print("2) INDEPENDENT SIMULATION (alpha=0.6, sigma=0.008, T=600, dt=0.05)")
print(f"   {'N':>5} | {'K_c seeds':^38} | {'mean':>6}")
N_list = [50, 100, 200, 400, 800]
Kc_sim = []
for N in N_list:
    kc = [find_Kc(N, s) for s in (11, 22, 33)]
    kc = np.array(kc, dtype=float)
    Kc_sim.append(np.nanmean(kc))
    print(f"   {N:5d} | {str(np.round(kc, 3)):^38} | {np.nanmean(kc):6.3f}")
Kc_sim = np.array(Kc_sim)

mask = ~np.isnan(Kc_sim)
A_s, beta_s, sse_pw_s, aic_pw_s, pred_pw_s = fit_powerlaw(N_list[mask], Kc_sim[mask])
Kinf_s, c_s, g_s, sse_sat_s, aic_sat_s, pred_sat_s = fit_saturating(N_list[mask], Kc_sim[mask])
print("-" * 78)
print("   MY DATA fits:")
print(f"   power law   : A = {A_s:.4f}, beta = {beta_s:.4f}  SSE = {sse_pw_s:.4f}  AIC = {aic_pw_s:.1f}")
print(f"   saturating  : K_inf = {Kinf_s:.3f}, c = {c_s:.3f}, gamma = {g_s:.2f}  SSE = {sse_sat_s:.4f}  AIC = {aic_sat_s:.1f}")

# ----------------------------------------------------------------------
# 3. Finite-time detection artifact probe: does K_c depend on observation time?
# ----------------------------------------------------------------------
print("=" * 78)
print("3) OBSERVATION-TIME SENSITIVITY PROBE (N=200, seeds 11/22/33)")
for T in (200.0, 600.0, 2400.0):
    kcs = [find_Kc(200, s, steps=int(T / DT)) for s in (11, 22, 33)]
    print(f"   T = {T:6.0f} : K_c = {np.round(kcs, 3)}")

# ----------------------------------------------------------------------
# 4. Figure
# ----------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
ax = axes[0]
ax.errorbar(N_theirs, K_theirs, yerr=K_theirs_err, fmt='o', color='k', capsize=3, label='EMP-049 archived data')
nn = np.logspace(np.log10(15), np.log10(1400), 100)
ax.plot(nn, A_t * nn**beta_t, 'r--', label=f"power law (beta={beta_t:.3f})")
ax.plot(nn, Kinf_t - c_t * nn**(-g_t), 'b-', label=f"saturating (K_inf={Kinf_t:.2f}, gamma={g_t:.2f})")
ax.plot(nn, 0.496 * nn**0.235, 'g:', label='dossier #009 law')
ax.set_xscale('log'); ax.set_ylim(0.5, 4.0)
ax.set_xlabel('N'); ax.set_ylabel('K_c (measured ignition point)')
ax.set_title("EMP-049 own data: power law vs saturation"); ax.legend(fontsize=7)

ax = axes[1]
ax.plot(np.array(N_list)[mask], Kc_sim[mask], 'o', color='k', label='this replication (3 seeds)')
ax.plot(nn, A_s * nn**beta_s, 'r--', label=f"power law (beta={beta_s:.3f})")
ax.plot(nn, Kinf_s - c_s * nn**(-g_s), 'b-', label=f"saturating (K_inf={Kinf_s:.2f}, gamma={g_s:.2f})")
ax.plot(nn, 0.496 * nn**0.235, 'g:', label='dossier #009 law')
ax.set_xscale('log'); ax.set_ylim(0.5, 4.5)
ax.set_xlabel('N'); ax.set_ylabel('K_c')
ax.set_title("Independent replication"); ax.legend(fontsize=7)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/emp049_redteam_scaling_fits.png', dpi=110)
print("saved: shared_agora/artifacts/emp049_redteam_scaling_fits.png")
