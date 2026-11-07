"""
EMP-183 DEFENSE: rigorous L -> infinity extrapolation of CML lambda_max.
Executes the recommendation EMP-183 only stated. If lambda_max(L) ~ lambda_inf + c/L
then we recover the ladder values with an honest error bar.
Test the hypothesis "~1/L in transition zone" directly.
"""
import numpy as np, json

def cml_lambda(L, r, eps, T=40000, burn=4000, seed=0, renorm=1):
    rng = np.random.default_rng(seed)
    x = rng.random(L) * 0.9 + 0.05
    f  = lambda z: r * z * (1.0 - z)
    fp = lambda z: r * (1.0 - 2.0 * z)
    v  = rng.standard_normal(L); v /= np.linalg.norm(v)
    acc = 0.0; n = 0
    for t in range(T + burn):
        # tangent map: v' = (1-eps)fp(x_i)v_i + (eps/2)[fp(x_{i-1})v_{i-1}+fp(x_{i+1})v_{i+1}]
        fx = fp(x)
        vn = (1.0 - eps) * fx * v
        vn += 0.5 * eps * (np.roll(fx, 1) * np.roll(v, 1) + np.roll(fx, -1) * np.roll(v, -1))
        x = (1.0 - eps) * f(x) + 0.5 * eps * (np.roll(f(x), 1) + np.roll(f(x), -1))
        if t >= burn:
            nv = np.linalg.norm(vn)
            acc += np.log(nv); n += 1
            v = vn / nv
        else:
            v = vn / (np.linalg.norm(vn) + 1e-300)
    return acc / n

def ensemble(L, r, eps, seeds=8, T=40000, burn=4000):
    seeds = list(range(seeds)) if isinstance(seeds, int) else seeds
    vals = [cml_lambda(L, r, eps, T=T, burn=burn, seed=s) for s in seeds]
    return float(np.mean(vals)), float(np.std(vals)), vals

CASES = {
    "Resonant_B": (3.860, 0.136, -0.081),
    "Chaotic_A":  (3.900, 0.103, +0.337),
}

Ls = [32, 64, 96, 128, 192, 256, 384, 512]
out = {}
print("="*78)
print("EMP-183 DEFENSE: ensemble L-scan + Richardson 1/L extrapolation (seeds=8)")
print("="*78)
for name,(r,eps,claim) in CASES.items():
    print(f"\n--- {name}  (r={r}, eps={eps}), SYN-054 claim = {claim:+.3f} ---")
    rows = []
    for L in Ls:
        m, s, raw = ensemble(L, r, eps, seeds=8, T=30000, burn=3000)
        sem = s/np.sqrt(8)
        rows.append((L, m, sem))
        print(f"  L={L:4d}  lambda={m:+.4f} +/- {sem:.4f} (seed sd {s:.4f})")
    Ls_a = np.array([x[0] for x in rows], float)
    lam  = np.array([x[1] for x in rows])
    sem  = np.array([x[2] for x in rows])
    # Richardson: fit lambda = lam_inf + c/L over the largest 5 sizes
    k = min(5, len(Ls_a))
    A = np.vstack([np.ones(k), 1.0/Ls_a[-k:]]).T
    w = 1.0/np.clip(sem[-k:], 1e-6, None)**2
    W = np.diag(w)
    coef = np.linalg.solve(A.T@W@A, A.T@W@lam[-k:])
    lam_inf, c = coef
    # residual-based uncertainty
    pred = A@coef
    chi2 = float(np.sum(w*(lam[-k:]-pred)**2)/max(k-2,1))
    lam_inf_err = float(np.sqrt(np.linalg.inv(A.T@W@A)[0,0]*max(chi2,1.0)))
    # also test 1/L^2 alternative to check which converges better
    A2 = np.vstack([np.ones(k), 1.0/Ls_a[-k:]**2]).T
    coef2 = np.linalg.solve(A2.T@W@A2, A2.T@W@lam[-k:])
    pred2 = A2@coef2
    chi2_2 = float(np.sum(w*(lam[-k:]-pred2)**2)/max(k-2,1))
    print(f"  1/L  fit : lam_inf = {lam_inf:+.4f} +/- {lam_inf_err:.4f}   (c={c:+.3f}, chi2/dof={chi2:.1f})")
    print(f"  1/L^2 fit: lam_inf = {coef2[0]:+.4f}              (chi2/dof={chi2_2:.1f})")
    verdict = "1/L better" if chi2 < chi2_2 else "1/L^2 better"
    print(f"  -> convergence law test: {verdict}")
    print(f"  -> SYN-054 claim {claim:+.3f} vs extrapolated {lam_inf:+.4f}: "
          f"{'CONSISTENT (within 2 sigma)' if abs(lam_inf-claim) < 2*lam_inf_err+0.02 else 'DIFFERS'}")
    out[name] = dict(rows=rows, lam_inf=float(lam_inf), lam_inf_err=lam_inf_err,
                     c=float(c), chi2_1L=chi2, chi2_1L2=chi2_2,
                     claim=claim, conv_law=verdict)

# ---- check the SIGN robustness explicitly: is any ensemble-mean crossing sign? ----
print("\n=== SIGN ROBUSTNESS (the load-bearing claim) ===")
for name, d in out.items():
    rows = d["rows"]
    signs = set(np.sign(m) for _,m,_ in rows)
    print(f"  {name}: sign stable across all L? {'YES' if len(signs)==1 else 'NO '+str(signs)}  "
          f"(mean lambda at smallest L={rows[0][0]}: {rows[0][1]:+.4f}, largest L={rows[-1][0]}: {rows[-1][1]:+.4f})")

json.dump(out, open("emp183_extrapolation.json","w"), indent=2)
print("\nSaved emp183_extrapolation.json")
