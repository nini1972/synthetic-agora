#!/usr/bin/env python3
"""
EMPIRICAL TEST: Is the "ultra-low critical exponent beta ~ 0.05" of DOSSIER-173 /
HYP-139 / HYP-140 a genuine dynamical invariant, or an artifact of the estimator
`colony_lib.bifurcation_cartography.extract_critical_exponent`?

KEY PRIOR FINDING (code inspection):
    beta = float(np.clip(slope, 0.05, 2.5))
The reported beta ~ 0.05 sits EXACTLY on the estimator's lower clip floor.
Whenever the raw log-log slope is <= 0.05 (including NEGATIVE), the function
returns exactly 0.05. So beta = 0.05 is the default floor value, not a
measurement. We test this hypothesis directly.

Tests performed:
  T1  Reproduce the frontier scan protocol (N=64, R=15, sigma_g=0.05, mu in [0.12,0.19]).
  T2  Recover the RAW (pre-clip) log-log slope for many fitting windows.
  T3  Joint free-K_c power-law fit (no gradient-based K_c detection).
  T4  Bootstrap confidence intervals on beta (stationary block bootstrap over mu).
  T5  Finite-size scaling: N in {64,128,256,512}; is beta a scale-invariant exponent?
  T6  Finite-horizon: T in {25,50,100,200,400}; is the "transition" a relaxation artifact?
  T7  Metric sensitivity: spatial mean <A> vs active-area fraction vs mass.
  T8  Initial-condition sensitivity: random vs orbium-blob vs uniform.
"""
import json
import os
import time

import numpy as np

from colony_lib.bifurcation_cartography import extract_critical_exponent
from colony_lib.dynamics import Lenia2D

OUT = os.path.dirname(os.path.abspath(__file__))
RESULTS = {}


# ----------------------------------------------------------------- core scan
def lenia_scan(mus, N=64, R=15, sigma_g=0.05, steps=100, seed=0,
               init="random", density=0.5, low=0.0, high=1.0):
    """Scan growth-center mu, return order parameters."""
    rows = []
    for mu in mus:
        L = Lenia2D(grid_size=N, kernel_radius=R, mu_g=mu, sigma_g=sigma_g)
        if init == "random":
            if hasattr(L, "initialize_random"):
                L.initialize_random(seed=seed, density=density, low=low, high=high)
            else:
                rng = np.random.default_rng(seed)
                raw = rng.uniform(low, high, size=(N, N))
                if 0.0 < density < 1.0:
                    raw *= rng.random((N, N)) < density
                L.state = np.clip(raw, 0.0, 1.0)
        elif init == "orbium":
            L.seed_orbium()
        elif init == "uniform":
            L.state = np.full((N, N), 0.5)
        L.run(steps=steps)
        st = L.state
        rows.append(dict(
            mu=float(mu),
            mean=float(st.mean()),
            active=float(np.mean(st > 0.05)),
            mass=float(st.sum()),
            amax=float(st.max()),
        ))
    return rows


# ------------------------------------------------- raw (unclipped) exponent
def raw_exponent(K, r, window=5, k_critical=None):
    """Reimplementation of extract_critical_exponent that returns the RAW slope
    BEFORE the np.clip(slope, 0.05, 2.5) floor is applied."""
    K = np.asarray(K, float)
    r = np.asarray(r, float)
    o = np.argsort(K)
    K, r = K[o], r[o]
    if k_critical is None:
        from colony_lib.bifurcation_cartography import detect_critical_point
        grad = np.gradient(r, K)
        k_crit = float(detect_critical_point(K, np.maximum(grad, 0.0))["k_critical"])
    else:
        k_crit = float(k_critical)
    mask = (K > k_crit + 1e-8) & (r > 1e-6)
    Ks, rs = K[mask], r[mask]
    if len(Ks) < 2:
        mid = max(1, len(K) // 2)
        k_crit = float(K[mid - 1])
        Ks, rs = K[mid:], np.maximum(r[mid:], 1e-6)
    w = max(2, min(int(window), len(Ks)))
    dK = Ks[:w] - k_crit
    r_win = rs[:w]
    r_crit = float(np.interp(k_crit, K, r))
    dr = np.maximum(r_win - 0.5 * r_crit, 1e-6)
    valid = (dK > 1e-8) & (dr > 1e-8)
    if np.sum(valid) >= 2:
        slope, _ = np.polyfit(np.log(dK[valid]), np.log(dr[valid]), 1)
    else:
        slope = np.nan
    return float(slope), float(k_crit), int(np.sum(valid))


def free_kc_fit(K, r):
    """Joint non-linear fit r = A*(K-Kc)^beta with Kc, beta, A all free.
    Uses scipy least_squares on log-r residuals."""
    from scipy.optimize import least_squares
    K = np.asarray(K, float)
    r = np.asarray(r, float)
    o = np.argsort(K)
    K, r = K[o], r[o]
    pos = r > 1e-9
    K, r = K[pos], r[pos]
    if len(K) < 4:
        return dict(success=False)

    def resid(p):
        kc, beta, A = p
        d = np.maximum(K - kc, 1e-9)
        return np.log(np.maximum(A * d ** beta, 1e-12)) - np.log(r)

    best = None
    for kc0 in np.linspace(K[0], K[-2], 12):
        for beta0 in (0.05, 0.2, 0.5, 1.0):
            A0 = float(np.max(r) / max((K[-1] - kc0) ** beta0, 1e-9))
            try:
                sol = least_squares(resid, [kc0, beta0, A0],
                                    bounds=([K[0] - 1e-3, 0.01, 1e-12],
                                            [K[-1], 3.0, 1e12]),
                                    max_nfev=4000)
            except Exception:
                continue
            if best is None or sol.cost < best.cost:
                best = sol
    if best is None:
        return dict(success=False)
    kc, beta, A = best.x
    # residual scatter (log-space) -> goodness of fit
    res = best.fun
    ss = float(np.sum(res ** 2))
    ss_tot = float(np.sum((np.log(r) - np.log(r).mean()) ** 2))
    return dict(success=True, k_c=float(kc), beta=float(beta), A=float(A),
                rms_log_resid=float(np.sqrt(np.mean(res ** 2))),
                r2_log=1.0 - ss / ss_tot if ss_tot > 0 else float("nan"),
                n_points=int(len(K)))


def bootstrap_beta(K, r, window=5, n_boot=400, seed=0):
    """Moving-block bootstrap over the mu-grid to get a CI on the clipped beta."""
    rng = np.random.default_rng(seed)
    K = np.asarray(K, float)
    r = np.asarray(r, float)
    o = np.argsort(K)
    K, r = K[o], r[o]
    n = len(K)
    block = max(2, n // 6)
    betas, raws = [], []
    for _ in range(n_boot):
        idx = []
        while len(idx) < n:
            s = rng.integers(0, max(1, n - block))
            idx.extend(range(s, min(s + block, n)))
        idx = np.array(idx[:n])
        Kb, rb = K[idx], r[idx]
        if len(np.unique(Kb)) < 3:
            continue
        try:
            b, _, _ = extract_critical_exponent(Kb, rb, window=window)
        except Exception:
            continue
        raw, _, _ = raw_exponent(Kb, rb, window=window)
        betas.append(float(b))
        raws.append(float(raw))
    if not betas:
        return dict(success=False)
    betas = np.array(betas)
    raws = np.array(raws)
    return dict(success=True, n_boot=int(len(betas)),
                beta_mean=float(betas.mean()), beta_std=float(betas.std()),
                beta_ci95=[float(np.percentile(betas, 2.5)),
                           float(np.percentile(betas, 97.5))],
                frac_at_floor=float(np.mean(betas <= 0.05 + 1e-9)),
                raw_mean=float(raws.mean()), raw_std=float(raws.std()),
                raw_ci95=[float(np.percentile(raws, 2.5)),
                          float(np.percentile(raws, 97.5))],
                raw_frac_negative=float(np.mean(raws <= 0.0)))


# =============================================================== T1 + T2 + T3
def main():
    t0 = time.time()
    mus = np.linspace(0.12, 0.19, 29)

    # ---- T1: reproduce the frontier protocol
    rows = lenia_scan(mus, N=64, R=15, sigma_g=0.05, steps=100, seed=0)
    K = np.array([r["mu"] for r in rows])
    A = np.array([r["mean"] for r in rows])
    ACT = np.array([r["active"] for r in rows])
    MASS = np.array([r["mass"] for r in rows])
    RESULTS["T1_frontier_scan"] = dict(
        protocol=dict(N=64, R=15, sigma_g=0.05, steps=100, seed=0,
                      init="random(density=0.5)", mu_range=[0.12, 0.19], n_mu=len(mus)),
        rows=rows,
        A_min=float(A.min()), A_max=float(A.max()), A_span=float(A.max() - A.min()),
        A_rel_span=float((A.max() - A.min()) / max(A.max(), 1e-12)),
        monotonic_increasing=bool(np.all(np.diff(A) > 0)),
        monotonic_decreasing=bool(np.all(np.diff(A) < 0)),
    )

    # ---- T2: raw vs clipped exponent over many windows
    win_tab = []
    for w in range(2, 13):
        b_canon, kc = extract_critical_exponent(K, A, window=w)
        raw, kc_raw, nvalid = raw_exponent(K, A, window=w)
        win_tab.append(dict(window=w, beta_canon=float(b_canon),
                            beta_raw=raw, k_crit_canon=float(kc),
                            k_crit_raw=kc_raw, n_valid=nvalid,
                            at_floor=bool(abs(b_canon - 0.05) < 1e-9)))
    RESULTS["T2_window_scan"] = win_tab

    # ---- T3: free-K_c joint fit for three order parameters
    fits = {}
    for name, y in (("mean_A", A), ("active_frac", ACT), ("mass", MASS)):
        f = free_kc_fit(K, y)
        f["canon_beta_w5"] = float(extract_critical_exponent(K, y, window=5)[0])
        fits[name] = f
    RESULTS["T3_free_kc_fits"] = fits

    # ---- T4: bootstrap
    RESULTS["T4_bootstrap_mean"] = bootstrap_beta(K, A, window=5, n_boot=400, seed=1)
    RESULTS["T4_bootstrap_active"] = bootstrap_beta(K, ACT, window=5, n_boot=400, seed=2)

    # ---- T5: finite-size scaling
    fs = []
    for N in (64, 128, 256, 512):
        rr = lenia_scan(mus, N=N, R=15, sigma_g=0.05, steps=100, seed=0)
        Kn = np.array([x["mu"] for x in rr])
        An = np.array([x["mean"] for x in rr])
        bc, kc = extract_critical_exponent(Kn, An, window=5)
        raw, kc_raw, _ = raw_exponent(Kn, An, window=5)
        fk = free_kc_fit(Kn, An)
        fs.append(dict(N=N, beta_canon=float(bc), beta_raw=raw,
                       k_crit_canon=float(kc), k_crit_raw=kc_raw,
                       free_kc=fk, A_span=float(An.max() - An.min()),
                       A_min=float(An.min()), A_max=float(An.max()),
                       A_at_kc=float(np.interp(kc_raw, Kn, An))))
    RESULTS["T5_finite_size"] = fs

    # ---- T6: finite-horizon
    fh = []
    for T in (25, 50, 100, 200, 400):
        rr = lenia_scan(mus, N=64, R=15, sigma_g=0.05, steps=T, seed=0)
        Kt = np.array([x["mu"] for x in rr])
        At = np.array([x["mean"] for x in rr])
        bc, kc = extract_critical_exponent(Kt, At, window=5)
        raw, kc_raw, _ = raw_exponent(Kt, At, window=5)
        fh.append(dict(steps=T, beta_canon=float(bc), beta_raw=raw,
                       k_crit_canon=float(kc), k_crit_raw=kc_raw,
                       A_span=float(At.max() - At.min()),
                       A_min=float(At.min()), A_max=float(At.max())))
    RESULTS["T6_finite_horizon"] = fh

    # ---- T7/T8: metric and initial-condition sensitivity
    sens = []
    for init, kw in (("random", dict(seed=0, density=0.5)),
                     ("random_sparse", dict(seed=0, density=0.2)),
                     ("random_dense", dict(seed=0, density=0.9)),
                     ("orbium", {}),
                     ("uniform", {})):
        rr = lenia_scan(mus, N=64, R=15, sigma_g=0.05, steps=100, init=init, **kw)
        Ki = np.array([x["mu"] for x in rr])
        Ai = np.array([x["mean"] for x in rr])
        Ac = np.array([x["active"] for x in rr])
        bc, kc = extract_critical_exponent(Ki, Ai, window=5)
        raw, kc_raw, _ = raw_exponent(Ki, Ai, window=5)
        sens.append(dict(init=init, beta_canon=float(bc), beta_raw=raw,
                         k_crit=float(kc_raw),
                         A_span=float(Ai.max() - Ai.min()),
                         A_min=float(Ai.min()), A_max=float(Ai.max()),
                         active_span=float(Ac.max() - Ac.min())))
    RESULTS["T7_T8_sensitivity"] = sens

    RESULTS["runtime_sec"] = time.time() - t0
    with open(os.path.join(OUT, "lenia_beta_artifact_results.json"), "w") as f:
        json.dump(RESULTS, f, indent=2, default=float)

    # ------------------------------------------------------------- printout
    print("=" * 78)
    print("T1  FRONTIER PROTOCOL REPLICATION (N=64, R=15, sigma_g=0.05, T=100)")
    print("=" * 78)
    t1 = RESULTS["T1_frontier_scan"]
    print(f"  <A> range: {t1['A_min']:.6f} -> {t1['A_max']:.6f}  "
          f"(span {t1['A_span']:.6f}, rel {t1['A_rel_span']:.4f})")
    print(f"  monotone increasing: {t1['monotonic_increasing']}")
    for r in rows[::4]:
        print(f"    mu={r['mu']:.4f}  <A>={r['mean']:.6f}  "
              f"active={r['active']:.4f}  mass={r['mass']:.2f}")

    print()
    print("=" * 78)
    print("T2  RAW vs CLIPPED EXPONENT (canon beta vs pre-clip log-log slope)")
    print("=" * 78)
    print(f"  {'win':>4} {'beta_canon':>11} {'beta_RAW':>11} {'K_c':>9} "
          f"{'K_c_raw':>9} {'floor?':>7}")
    for w in win_tab:
        print(f"  {w['window']:>4} {w['beta_canon']:>11.5f} {w['beta_raw']:>11.5f} "
              f"{w['k_crit_canon']:>9.5f} {w['k_crit_raw']:>9.5f} "
              f"{str(w['at_floor']):>7}")
    n_floor = sum(w["at_floor"] for w in win_tab)
    print(f"  --> {n_floor}/{len(win_tab)} windows return EXACTLY 0.05 (the clip floor).")

    print()
    print("=" * 78)
    print("T3  FREE-K_c JOINT POWER-LAW FITS")
    print("=" * 78)
    for nm, f in fits.items():
        if f.get("success"):
            print(f"  {nm:12s} Kc={f['k_c']:.5f} beta={f['beta']:.4f} "
                  f"A={f['A']:.4g} rms(log)={f['rms_log_resid']:.4f} "
                  f"R2(log)={f['r2_log']:.4f}  [canon beta_w5={f['canon_beta_w5']:.4f}]")
        else:
            print(f"  {nm:12s} fit FAILED")

    print()
    print("=" * 78)
    print("T4  BOOTSTRAP CIs ON beta")
    print("=" * 78)
    for nm in ("T4_bootstrap_mean", "T4_bootstrap_active"):
        b = RESULTS[nm]
        if b.get("success"):
            print(f"  {nm}: beta={b['beta_mean']:.4f} +/- {b['beta_std']:.4f} "
                  f"CI95=[{b['beta_ci95'][0]:.4f},{b['beta_ci95'][1]:.4f}]")
            print(f"      fraction of bootstrap samples AT the 0.05 floor: "
                  f"{b['frac_at_floor']:.3f}")
            print(f"      RAW slope mean={b['raw_mean']:.4f} +/- {b['raw_std']:.4f} "
                  f"CI95=[{b['raw_ci95'][0]:.4f},{b['raw_ci95'][1]:.4f}]  "
                  f"frac<=0: {b['raw_frac_negative']:.3f}")

    print()
    print("=" * 78)
    print("T5  FINITE-SIZE SCALING  (is beta scale-invariant?)")
    print("=" * 78)
    print(f"  {'N':>5} {'beta_canon':>11} {'beta_RAW':>11} {'K_c':>9} "
          f"{'beta_free':>11} {'A_span':>9} {'A(K_c)':>9}")
    for e in fs:
        fb = e["free_kc"].get("beta", float("nan"))
        print(f"  {e['N']:>5} {e['beta_canon']:>11.5f} {e['beta_raw']:>11.5f} "
              f"{e['k_crit_raw']:>9.5f} {fb:>11.4f} {e['A_span']:>9.5f} "
              f"{e['A_at_kc']:>9.5f}")

    print()
    print("=" * 78)
    print("T6  FINITE-HORIZON SCALING  (is the 'transition' a relaxation artifact?)")
    print("=" * 78)
    print(f"  {'T':>5} {'beta_canon':>11} {'beta_RAW':>11} {'K_c':>9} "
          f"{'A_span':>9} {'A_min':>9} {'A_max':>9}")
    for e in fh:
        print(f"  {e['steps']:>5} {e['beta_canon']:>11.5f} {e['beta_raw']:>11.5f} "
              f"{e['k_crit_raw']:>9.5f} {e['A_span']:>9.5f} {e['A_min']:>9.5f} "
              f"{e['A_max']:>9.5f}")

    print()
    print("=" * 78)
    print("T7/T8  INITIAL-CONDITION & METRIC SENSITIVITY")
    print("=" * 78)
    print(f"  {'init':>14} {'beta_canon':>11} {'beta_RAW':>11} {'K_c':>9} "
          f"{'A_span':>9} {'act_span':>9}")
    for e in sens:
        print(f"  {e['init']:>14} {e['beta_canon']:>11.5f} {e['beta_raw']:>11.5f} "
              f"{e['k_crit']:>9.5f} {e['A_span']:>9.5f} {e['active_span']:>9.5f}")

    print()
    print(f"runtime = {RESULTS['runtime_sec']:.1f}s")
    print("RESULTS written to lenia_beta_artifact_results.json")


if __name__ == "__main__":
    main()
