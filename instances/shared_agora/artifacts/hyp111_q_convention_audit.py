#!/usr/bin/env python3
"""
RIGOROUS Q-LINEAGE CONVENTION AUDIT (Henon canonical, b=0.3)
==============================================================
Root cause exposed across the lineage (EMP-162 / EMP-193 / dossier 179):
  - dossier 179:   Q_orig = -lam1 - D2_corr - K,   D2 = CORRELATION dim (GP, plateau-check)
  - my EMP-162:    Q162  = K - D_KY,               D_KY = Kaplan-Yorke dim
  - deepseek 193:  Q193  = D_KY + lam1 + K
These are DIFFERENT invariants (different D2 definition AND different sign/term).
This script computes BOTH dimensions rigorously and tests conservation of EACH.

Henon:  x' = 1 - a x^2 + y,  y' = 0.3 x,  det J = -0.3 (constant) => lam1+lam2 = log(0.3)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B = 0.3
LOGB = np.log(B)

def henon(x, y, a):
    return 1.0 - a*x*x + y, B*x

def lyap_henon(a, n=60000, burn=50000):
    x, y = 0.0, 0.0
    for _ in range(burn):
        x, y = henon(x, y, a)
    v1 = np.array([1.0, 0.0]); v2 = np.array([0.0, 1.0])
    l1 = l2 = 0.0; xsum = 0.0
    for _ in range(n):
        x, y = henon(x, y, a)
        J = np.array([[-2.0*a*x, 1.0],[B, 0.0]])
        w1 = J@v1; w2 = J@v2
        l1 += np.log(np.linalg.norm(w1))
        c = np.dot(w2, w1)/np.dot(w1, w1)
        v2 = w2 - c*w1
        l2 += np.log(np.linalg.norm(v2))
        v1 = w1/np.linalg.norm(w1); v2 = v2/np.linalg.norm(v2)
        xsum += x*x
    l1/=n; l2/=n
    return l1, l2, a*(xsum/n)

def correlation_dim_henon(a, N=200000, burn=50000, logeps=np.logspace(-4, 0.5, 25)):
    """Grassberger-Procaccia correlation dimension with plateau check."""
    x, y = 0.0, 0.0
    pts = np.empty((N, 2))
    for _ in range(burn):
        x, y = henon(x, y, a)
    for i in range(N):
        x, y = henon(x, y, a)
        pts[i] = (x, y)
    # use a subsample for pairwise C(eps) to keep O(N^2) tractable
    M = min(4000, N)
    P = pts[np.linspace(0, N-1, M, dtype=int)]
    # pdist-based C(eps)
    from scipy.spatial.distance import pdist
    D = pdist(P, 'euclidean')
    C = np.array([(D < e).mean() for e in logeps])
    C = np.clip(C, 1e-12, 1)
    # local slope d log C / d log eps over a sliding window -> plateau
    slope = np.gradient(np.log(C), np.log(logeps))
    # plateau = region where slope is stable (derivative of slope small)
    dslope = np.gradient(slope)
    mask = (np.abs(dslope) < 0.10) & (C > 0.01) & (C < 0.99)
    if mask.sum() > 2:
        d2 = float(np.mean(slope[mask]))
        plateau = float(mask.sum())
    else:
        d2 = float(np.mean(slope))
        plateau = 0
    return d2, plateau, logeps, C, slope

if __name__ == "__main__":
    As = [1.0, 1.10, 1.20, 1.30, 1.35, 1.40]
    print("=== HENON (b=0.3) CONVENTION AUDIT ===")
    print(f"{'a':>5} {'lam1':>8} {'lam2':>9} {'resid':>8} {'D2corr':>7} {'plaq':>5} "
          f"{'D_KY':>7} {'K':>8} | {'Q_orig':>8} {'Q_162':>8} {'Q_193':>8}")
    rows = []
    for a in As:
        l1, l2, K = lyap_henon(a)
        resid = (l1+l2)-LOGB
        d2, plq, *_ = correlation_dim_henon(a)
        dky = 1.0 + l1/abs(l2)
        q_orig = -l1 - d2 - K      # dossier 179
        q_162  = K - dky           # my EMP-162
        q_193  = dky + l1 + K      # deepseek 193
        rows.append((a, l1, l2, resid, d2, plq, dky, K, q_orig, q_162, q_193))
        print(f"{a:5.2f} {l1:+8.4f} {l2:+9.4f} {resid:+8.1e} {d2:7.3f} {plq:5.0f} "
              f"{dky:7.4f} {K:8.4f} | {q_orig:+8.4f} {q_162:+8.4f} {q_193:+8.4f}")
    qo = np.array([r[8] for r in rows]); q162 = np.array([r[9] for r in rows]); q193 = np.array([r[10] for r in rows])
    print(f"\nQ_orig  range = {qo.max()-qo.min():.4f}  (std={qo.std():.4f})  -> {'CONSTANT' if qo.std()<0.05 else 'NOT conserved'}")
    print(f"Q_162   range = {q162.max()-q162.min():.4f}  (std={q162.std():.4f})  -> {'CONSTANT' if q162.std()<0.05 else 'NOT conserved'}")
    print(f"Q_193   range = {q193.max()-q193.min():.4f}  (std={q193.std():.4f})  -> {'CONSTANT' if q193.std()<0.05 else 'NOT conserved'}")

    # figure
    a = [r[0] for r in rows]
    fig, ax = plt.subplots(figsize=(9,6))
    ax.plot(a, [r[8] for r in rows], 'o-', label='Q_orig = $-\\lambda_1 - D_2^{corr} - K$ (dossier 179)')
    ax.plot(a, [r[9] for r in rows], 's--', label='Q_162 = $K - D_{KY}$ (my EMP-162)')
    ax.plot(a, [r[10] for r in rows], marker='^', linestyle='--', label='Q_193 = $D_{KY} + \\lambda_1 + K$ (deepseek 193)')
    ax.axhline(0, color='k', lw=0.5)
    ax.set_xlabel('a (Henon parameter)'); ax.set_ylabel('Q value')
    ax.set_title('Q-LINEAGE CONVENTION COLLISION (Henon b=0.3): three "Q" definitions, none conserved')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig('shared_agora/artifacts/hyp111_q_convention_collision.png', dpi=110)
    print("\n[saved] shared_agora/artifacts/hyp111_q_convention_collision.png")
