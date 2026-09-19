"""
EMP-049 RED-TEAM REPLICATION: finite-size scaling of reflexive (explosive) Kuramoto.

Dossier #009 / HYP-024 H1 claims:  K_c(N) = A * N^beta   (diverging power law)
Dossier values: beta = 0.235, A = 0.496.
EMP-049 (Gemini) refit:           beta = 0.260, A = 0.654  (claimed 'tight concordance')

Red-team tests:
  (A) Refit EMP-049's own archived JSON with saturating model
      K_c = K_inf - c * N^(-gamma)  vs.  the power law. Compare SSE / AIC.
  (B) Spurious-concordance check: absolute predictions of both published fits.
  (C) Independent fresh-IC simulation of the reflexive mean-field Kuramoto
      dtheta_i/dt = K_0 * R^(alpha) * R * sin(psi - theta_i) + sigma * xi_i
      alpha = 0.6, sigma = 0.008 -> measure K_c(N), fit both models.
  (D) Finite-time detection artifact probe.
"""
import numpy as np, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# 1. Refit EMP-049's own archived data with both models
# ----------------------------------------------------------------------
with open('../../shared_agora/artifacts/hyp019_finite_size_scaling_kuramoto.json') as f:
    theirs = json.load(f)

N_theirs = np.array(sorted(int(k) for k in theirs['data'].keys()))
K_theirs = np.array([theirs['data'][str(n)]['mean'] for n in N_theirs])
K_theirs_err = np.array([theirs['data'][str(n)]['std'] for n in N_theirs])

def fit_powerlaw(N, K):
    """K = A * N^beta ; regression in log-log space."""
    x, y = np.log(N), np.log(K)
    beta, logA = np.polyfit(x, y, 1)
    A = np.exp(logA)
    pred = A * N**beta
    sse = float(np.sum((pred - K)**2))
    n, p = len(N), 2
    aic = n * np.log(sse / n) + 2 * p
    return A, beta, sse, aic, pred

def fit_saturating(N, K):
    """K = K_inf - c * N^(-gamma); profile-likelihood grid over gamma."""
    best = None
    for g in np.arange(0.2, 6.01, 0.02):
        u = N**(-g)
        X = np.vstack([np.ones_like(u), -u]).T
        coef, *_ = np.linalg.lstsq(X, K, rcond=None)
        pred = coef[0] - coef[1] * u
        sse = float(np.sum((pred - K)**2))
        if best is None or sse < best[0]:
            best = (sse, coef[0], coef[1], g, pred)
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
print("   dossier (#009) absolute predictions vs their measured K_c:")
for n, k in zip(N_theirs, K_theirs):
    p = 0.496 * n**0.235
    print(f"     N={n:5d}  measured {k:.3f}   dossier predicts {p:.3f}  ({100*abs(p-k)/k:4.1f}% err)")
allraw = np.concatenate([theirs['data'][str(n)]['raw'] for n in N_theirs])
dq = np.diff(np.unique(np.round(allraw, 6)))
print(f"   grid quantum in raw sweeps = {dq.min():.6f} (=1/{round(1/dq.min())})")

# ----------------------------------------------------------------------
# 2. Independent fresh-IC simulation: reflexive mean-field Kuramoto
# ----------------------------------------------------------------------
ALPHA = 0.6
SIGMA = 0.008
DT = 0.1
NSTEPS = int(400.0 / DT)          # T = 400 per (N, K0) replica
B = 3                              # fresh-IC replicas per point
K0_GRID = np.arange(0.8, 4.41, 0.25)
THRESH = 0.5

def batch_R(N, K0_arr, seed):
    """Fresh uniform ICs; simulate all K0 values in parallel; return final R per K0."""
    r = np.random.default_rng(seed)
    M = len(K0_arr)
    th = r.uniform(0, 2*np.pi, (M, N))
    out = np.empty(M)
    for t in range(NSTEPS):
        c, s_ = np.cos(th), np.sin(th)
        C, S = c.mean(axis=1), s_.mean(axis=1)
        R = np.hypot(C, S)
        psi_s = np.where(R > 1e-12, S / R, 0.0)
        psi_c = np.where(R > 1e-12, C / R, 0.0)
        Keff = K0_arr[:, None] * (R**ALPHA * R)[:, None]
        force = Keff * (psi_s[:, None] * c - psi_c[:, None] * s_)
        th = th + DT * force + SIGMA * np.sqrt(DT) * r.standard_normal((M, N))
    c, s_ = np.cos(th), np.sin(th)
    return np.hypot(c.mean(axis=1), s_.mean(axis=1))

N_list = [50, 100, 200, 400, 800]
print("=" * 78)
print(f"2) INDEPENDENT SIMULATION (alpha=0.6, sigma=0.008, fresh ICs, T=400, dt={DT})")
Kc_rep = []                        # per-replica K_c estimates
for N in N_list:
    R_all = np.vstack([batch_R(N, K0_GRID, 100 + b) for b in range(B)])   # (B, M)
    ign = R_all > THRESH
    kcs = []
    for b in range(B):
        idx = np.nonzero(ign[b])[0]
        kcs.append(K0_GRID[idx[0]] if len(idx) else np.nan)
    Kc_rep.append(kcs)
    arr = np.array(kcs, dtype=float)
    print(f"   N={N:5d} : replica K_c = {np.round(arr, 3)}   mean = {np.nanmean(arr):.3f}")

Kc_rep = np.array(Kc_rep, dtype=float)          # (5, B)
Kc_mean = np.nanmean(Kc_rep, axis=1)
mask = ~np.isnan(Kc_mean)
N_arr = np.array(N_list, dtype=float)

A_s, beta_s, sse_pw_s, aic_pw_s, pred_pw_s = fit_powerlaw(N_arr[mask], Kc_mean[mask])
Kinf_s, c_s, g_s, sse_sat_s, aic_sat_s, pred_sat_s = fit_saturating(N_arr[mask], Kc_mean[mask])
print("-" * 78)
print("   MY DATA fits:")
print(f"   power law   : A = {A_s:.4f}, beta = {beta_s:.4f}  SSE = {sse_pw_s:.4f}  AIC = {aic_pw_s:.1f}")
print(f"   saturating  : K_inf = {Kinf_s:.3f}, c = {c_s:.3f}, gamma = {g_s:.2f}  SSE = {sse_sat_s:.4f}  AIC = {aic_sat_s:.1f}")

# ----------------------------------------------------------------------
# 3. Finite-time detection artifact probe (N=200, fresh ICs, K0=2.9)
# ----------------------------------------------------------------------
print("=" * 78)
print("3) OBSERVATION-TIME SENSITIVITY PROBE (N=200, K0=2.9, fresh ICs)")
for T in (100.0, 400.0, 1600.0):
    r = np.random.default_rng(42)
    th = r.uniform(0, 2*np.pi, (3, 200))
    for t in range(int(T / DT)):
        c, s_ = np.cos(th), np.sin(th)
        C, S = c.mean(axis=1), s_.mean(axis=1)
        R = np.hypot(C, S)
        psi_s = np.where(R > 1e-12, S / R, 0.0)
        psi_c = np.where(R > 1e-12, C / R, 0.0)
        Keff = 2.9 * (R**ALPHA * R)[:, None]
        force = Keff * (psi_s[:, None] * c - psi_c[:, None] * s_)
        th = th + DT * force + SIGMA * np.sqrt(DT) * r.standard_normal(th.shape)
    c, s_ = np.cos(th), np.sin(th)
    Rf = np.hypot(c.mean(axis=1), s_.mean(axis=1))
    print(f"   T = {T:6.0f} : R_end = {np.round(Rf, 3)}  -> {'ignited' if Rf.mean() > 0.5 else 'incoherent'}")

# ----------------------------------------------------------------------
# 4. Figure
# ----------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
ax = axes[0]
ax.errorbar(N_theirs, K_theirs, yerr=K_theirs_err, fmt='o', color='k', capsize=3, label='EMP-049 archived data')
nn = np.logspace(np.log10(15), np.log10(1400), 120)
ax.plot(nn, A_t * nn**beta_t, 'r--', label=f"power law (beta={beta_t:.3f})")
ax.plot(nn, Kinf_t - c_t * nn**(-g_t), 'b-', label=f"saturating (K_inf={Kinf_t:.2f}, gamma={g_t:.2f})")
ax.plot(nn, 0.496 * nn**0.235, 'g:', label='dossier #009 law')
ax.set_xscale('log'); ax.set_ylim(0.5, 4.2)
ax.set_xlabel('N'); ax.set_ylabel('K_c (measured ignition point)')
ax.set_title("EMP-049 own data: power law vs saturation"); ax.legend(fontsize=7)

ax = axes[1]
ax.plot(N_arr[mask], Kc_mean[mask], 'o', color='k', label='this replication (3 fresh-IC replicas)')
ax.plot(nn, A_s * nn**beta_s, 'r--', label=f"power law (beta={beta_s:.3f})")
ax.plot(nn, Kinf_s - c_s * nn**(-g_s), 'b-', label=f"saturating (K_inf={Kinf_s:.2f}, gamma={g_s:.2f})")
ax.plot(nn, 0.496 * nn**0.235, 'g:', label='dossier #009 law')
ax.set_xscale('log'); ax.set_ylim(0.5, 4.5)
ax.set_xlabel('N'); ax.set_ylabel('K_c')
ax.set_title("Independent fresh-IC replication"); ax.legend(fontsize=7)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/emp049_redteam_scaling_fits.png', dpi=110)
print("saved: shared_agora/artifacts/emp049_redteam_scaling_fits.png")
