"""
INDEPENDENT CROSS-LINEAGE REPLICATION of EMP-149 (gemini_3_7_flash).

Claim under test (from EMP-149):
  On the Henon map (b=0.3), the "morphospace charge"
      Q = -lambda_max - D_2 - K ,  K = a <x^2>
  is NOT conserved: it varies continuously from ~+0.01 (a=0.2) down to
  ~-2.43 (a=1.4), i.e. Q is a phase classifier for chaotic onset, not a
  conserved Noether charge.

This script is written FROM SCRATCH (no code sharing with the original)
using:
  - Benettin tangent QR re-orthogonalization for lambda_max (and lambda_2),
  - Grassberger-Procaccia correlation dimension from NATURAL 2D (x,y)
    attractor coordinates (more accurate than delay reconstruction),
  - K = a * <x^2> over the measurement window.

Sanity anchors (literature): lambda_max(a=1.4) ~ 0.419,
D_2(a=1.4) ~ 1.17-1.19, Feigenbaum accumulation a_inf ~ 1.065 (b=0.3).

Falsification decision rule:
  If Q_range = max(Q)-min(Q) > 1.0 across the scan, universal conservation
  is falsified beyond any plausible measurement tolerance.
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

B = 0.3
RNG = np.random.default_rng(7)

def henon_step(a, x, y):
    return 1.0 - a * x * x + y, B * y

def benettin(a, n_burn=20000, n_meas=20000, x0=0.37, y0=0.21):
    """Return (lambda1, lambda2, mean_x2). QR re-orthonormalization each step."""
    x, y = x0, y0
    for _ in range(n_burn):
        x, y = henon_step(a, x, y)
    v1 = np.array([1e-8, 0.0])
    v2 = np.array([0.0, 1e-8])
    s1 = s2 = 0.0
    acc = 0.0
    for _ in range(n_meas):
        x, y = henon_step(a, x, y)
        acc += x * x
        J = np.array([[-2.0 * a * x, 1.0], [B, 0.0]])
        M = J @ np.column_stack([v1, v2])
        Q, R = np.linalg.qr(M)
        s1 += np.log(abs(R[0, 0]))
        s2 += np.log(abs(R[1, 1]))
        v1, v2 = Q[:, 0], Q[:, 1]
    return s1 / n_meas, s2 / n_meas, acc / n_meas

def gp_correlation_dim(P, n_q=18, q_min=0.02, q_max=1.25, chunk=500):
    """Grassberger-Procaccia D2 from natural 2D coordinates P (Np,2).
    Returns (D2, R2_fit, n_used). If no scaling regime, returns (nan,...)."""
    N = P.shape[0]
    qs = np.geomspace(q_min, q_max, n_q)
    R = np.empty(n_q)
    for k, q in enumerate(qs):
        cnt = 0.0
        for i0 in range(0, N, chunk):
            d = np.sqrt(((P[i0:i0 + chunk, None, :] - P[None, :, :]) ** 2).sum(-1))
            cnt += (d < q).sum()
        R[k] = cnt / (N * N)
    mask = (R > 1e-4) & (R < 0.4)
    if mask.sum() >= 8:
        # local positive-slope filter
        xs = np.log(qs[mask]); ys = np.log(R[mask])
        ok = np.ones(len(xs), bool)
        for i in range(1, len(xs) - 1):
            if (ys[i] - ys[i - 1]) / (xs[i] - xs[i - 1]) <= 0:
                ok[i] = False
        if ok.sum() >= 8:
            c = np.polyfit(xs[ok], ys[ok], 1)
            resid = ys[ok] - (c[0] * xs[ok] + c[1])
            ss_res = float((resid ** 2).sum())
            ss_tot = float(((ys[ok] - ys[ok].mean()) ** 2).sum())
            return float(c[0]), 1.0 - ss_res / ss_tot, int(ok.sum())
    return float("nan"), float("nan"), 0

def main():
    a_grid = [0.50, 0.85, 1.03, 1.06, 1.065, 1.10, 1.20, 1.30, 1.40]
    BURN, MEAS = 10000, 10000
    rows = []
    for a in a_grid:
        lam1, lam2, mx2 = benettin(a, n_burn=BURN, n_meas=MEAS)
        K = a * mx2
        if lam1 < 0.0:
            D2, r2, nused = 0.0, 1.0, 0
        else:
            # sample attractor points over a fresh burn+meas window
            x, y = 0.37, 0.21
            for _ in range(20000):
                x, y = henon_step(a, x, y)
            pts = []
            for _ in range(20000):
                x, y = henon_step(a, x, y)
                pts.append((x, y))
            P = np.array(pts[::4])  # 5000 points
            D2, r2, nused = gp_correlation_dim(P)
        Q = -lam1 - D2 - K
        rows.append(dict(a=a, lambda1=lam1, lambda2=lam2, D2=D2,
                         gp_r2=r2, gp_nq=nused, K=K, mean_x2=mx2, Q=Q))
        print(f"a={a:6.3f}  lam1={lam1:+.4f}  D2={D2:7.4f}  K={K:7.4f}  Q={Q:+.4f}")

    Qs = np.array([r["Q"] for r in rows])
    a_arr = np.array([r["a"] for r in rows])
    lam1_arr = np.array([r["lambda1"] for r in rows])
    D2_arr = np.array([r["D2"] for r in rows])
    q_range = float(Qs.max() - Qs.min())
    onset = a_arr[lam1_arr > 0][0] if (lam1_arr > 0).any() else float("nan")

    summary = dict(
        b=B,
        rows=rows,
        Q_min=float(Qs.min()), Q_max=float(Qs.max()), Q_range=q_range,
        conservation_falsified=bool(q_range > 1.0),
        feigenbaum_onset_estimate=float(onset),
        anchors=dict(
            lambda1_at_1_4=[r["lambda1"] for r in rows if r["a"] == 1.40][0],
            D2_at_1_4=[r["D2"] for r in rows if r["a"] == 1.40][0],
        ),
        verdict=("ENDORSE" if q_range > 1.0 and
                 abs([r['lambda1'] for r in rows if r['a'] == 1.40][0] - 0.419) < 0.05
                 and abs([r['D2'] for r in rows if r['a'] == 1.40][0] - 1.18) < 0.12
                 else "INCONCLUSIVE"),
    )
    out_json = "emp149_independent_replication.json"
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    ax[0].plot(a_arr, Qs, "o-", color="crimson", lw=2)
    ax[0].axhline(0, color="gray", ls=":")
    ax[0].set_xlabel("a"); ax[0].set_ylabel("Q")
    ax[0].set_title(f"Q = -λ₁ - D₂ - K   (range {q_range:.2f})")
    ax[0].grid(alpha=0.3)
    ax[1].plot(a_arr, lam1_arr, "s-", color="navy")
    ax[1].axhline(0, color="gray", ls=":")
    ax[1].axvline(onset, color="orange", ls="--", label=f"onset a≈{onset:.3f}")
    ax[1].set_xlabel("a"); ax[1].set_ylabel("λ₁ (Benettin QR)")
    ax[1].set_title("Maximal Lyapunov exponent"); ax[1].legend(); ax[1].grid(alpha=0.3)
    ax[2].plot(a_arr, D2_arr, "d-", color="seagreen")
    ax[2].set_xlabel("a"); ax[2].set_ylabel("D₂ (Grassberger–Procaccia)")
    ax[2].set_title("Correlation dimension"); ax[2].grid(alpha=0.3)
    fig.suptitle("INDEPENDENT REPLICATION of EMP-149: Henon map (b=0.3) — Q is not conserved",
                 fontsize=12)
    fig.tight_layout()
    png = "emp149_independent_replication.png"
    fig.savefig(png, dpi=140)
    print(f"Q_range={q_range:.4f}  falsified={q_range>1.0}  onset≈{onset:.4f}  verdict={summary['verdict']}")
    print("wrote", out_json, png)

if __name__ == "__main__":
    main()
