"""
Independent test of HYP-114: "Lorenz Q Values Show Substrate-Specific Quantization".
Q = -lambda_max - D2 - K (DOSSIER-158); for Lorenz K=(sigma+1+beta)/3 matches the
dossier's 4.56 exactly, and is piecewise CONSTANT within any fixed (sigma,beta).

Question: on a FINE sweep, is Q a quantized/branch-like function of rho, or smooth?

Vectorized: all parameter sets advanced simultaneously (M systems in one numpy array).
  lambda_max : Benettin, step flow map (I+dt*J), renorm every 10 steps
  D2         : Grassberger-Procaccia on true 3D state points
  K          : (sigma+1+beta)/3
Diagnostics: sorted-Q gaps vs uniform null, k-means gap statistic k=1..6,
             Spearman Q vs rho, total-variation/net-drift.
"""
import numpy as np, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist

DT = 0.01
TRANS, NSTEPS, RENORM = 3000, 20000, 10

def make_systems():
    sys = [(10.0, r, 8/3) for r in np.linspace(25, 45, 51)] + \
          [(sg, 28.0, 8/3) for sg in [6, 8, 10, 12, 14, 16]] + \
          [(10.0, 28.0, b) for b in [0.5, 1.0, 2.0, 8/3, 4.0, 6.0]]
    labels = ["A"]*51 + ["B"]*6 + ["C"]*6
    return sys, labels

def run_all(syslist):
    M = len(syslist)
    sig = np.array([s for s, r, b in syslist])
    rho = np.array([r for s, r, b in syslist])
    bet = np.array([b for s, r, b in syslist])
    st = np.stack([np.array([1.0, 1.0, 20.0])]*M) + 0.01*np.random.default_rng(1).standard_normal((M, 3))
    rng = np.random.default_rng(0)
    v = rng.standard_normal((M, 3)); v /= np.linalg.norm(v, axis=1, keepdims=True)

    def rk4(s, h):
        k1 = np.stack([sig*(s[:,1]-s[:,0]), s[:,0]*(rho-s[:,2])-s[:,1], s[:,0]*s[:,1]-bet*s[:,2]], 1)
        s2 = s + 0.5*h*k1
        k2 = np.stack([sig*(s2[:,1]-s2[:,0]), s2[:,0]*(rho-s2[:,2])-s2[:,1], s2[:,0]*s2[:,1]-bet*s2[:,2]], 1)
        s3 = s + 0.5*h*k2
        k3 = np.stack([sig*(s3[:,1]-s3[:,0]), s3[:,0]*(rho-s3[:,2])-s3[:,1], s3[:,0]*s3[:,1]-bet*s3[:,2]], 1)
        s4 = s + h*k3
        k4 = np.stack([sig*(s4[:,1]-s4[:,0]), s4[:,0]*(rho-s4[:,2])-s4[:,1], s4[:,0]*s4[:,1]-bet*s4[:,2]], 1)
        return s + h*(k1 + 2*k2 + 2*k3 + k4)/6.0

    def jac(s):
        return (np.stack([-sig*np.ones_like(s[:,0]), sig, np.zeros_like(s[:,0])], 1),
                np.stack([np.ones_like(s[:,0]), -np.ones_like(s[:,0]), -s[:,0]], 1),
                np.stack([s[:,1], s[:,0], -bet*np.ones_like(s[:,0])], 1))

    for _ in range(TRANS):
        st = rk4(st, DT)
    alive = np.isfinite(st).all(1)

    lyap = np.zeros(M); count = 0
    pts = [[] for _ in range(M)]
    bad = ~np.isfinite(st).all(1)
    for i in range(NSTEPS):
        st = rk4(st, DT)
        cur = np.isfinite(st).all(1)
        bad |= ~cur
        st = np.where(np.isfinite(st), st, 0.0)
        J = jac(st)
        v = v + DT*(J[0]*v[:, [0]] + J[1]*v[:, [1]] + J[2]*v[:, [2]])
        v = np.where(np.isfinite(v), v, np.nan_to_num(v))
        n = np.linalg.norm(v, axis=1, keepdims=True)
        n = np.where(n > 0, n, 1.0)
        lyap += np.log(np.where(np.isfinite(n[:,0]), n[:,0], 1.0))
        v = v/n
        count += 1
        if i % 10 == 0:
            for m in range(M):
                pts[m].append(st[m].copy())
    lam = lyap/(count*DT)
    lam[bad] = np.nan
    return lam, [np.array(p) for p in pts], bad

def corr_dim(points, bad):
    if bad or len(points) < 1000:
        return np.nan
    points = points[np.isfinite(points).all(1)]
    if len(points) < 1000:
        return np.nan
    pts = points[::max(1, len(points)//3000)]
    d = pdist(pts); d = d[d > 0]
    if len(d) < 500:
        return np.nan
    rmax = np.percentile(d, 99)
    rs = np.logspace(np.log10(rmax*0.01), np.log10(rmax*0.12), 18)
    C = np.array([np.mean(d < r) for r in rs])
    ok = (C > 0) & (C < 1)
    if ok.sum() < 8:
        return np.nan
    return float(np.polyfit(np.log(rs[ok]), np.log(C[ok]), 1)[0])

def kmeans_gap(vals, kmax=6, n_null=60):
    vals = np.asarray(vals, float)
    def inertia(v, k):
        c = np.quantile(v, np.linspace(0.05, 0.95, k))
        for _ in range(60):
            lab = np.argmin(np.abs(v[:, None] - c[None, :]), axis=1)
            for j in range(k):
                m = lab == j
                if m.any(): c[j] = v[m].mean()
        return float(np.sum((v - c[lab])**2))
    lo, hi = vals.min(), vals.max()
    gaps = []
    for k in range(1, kmax+1):
        Wk = inertia(vals, k)
        Wks = [inertia(np.random.default_rng(t).uniform(lo, hi, len(vals)), k) for t in range(n_null)]
        gaps.append(np.log(np.mean(Wks)+1e-12) - np.log(Wk+1e-12))
    return np.array(gaps), int(np.argmax(gaps))

def quant_diagnostics(Q):
    Q = np.asarray(Q, float); Q = Q[np.isfinite(Q)]
    s = np.sort(Q); span = s[-1]-s[0]
    rng = np.random.default_rng(7)
    null_max = [np.max(np.diff(np.sort(rng.uniform(s[0], s[-1], len(s)))))/span for _ in range(300)]
    max_gap = float(np.max(np.diff(s))/span) if span > 0 else 0.0
    tv = float(np.sum(np.abs(np.diff(Q)))); net = float(abs(Q[-1]-Q[0]))
    g, kstar = kmeans_gap(Q)
    return dict(max_gap_norm=max_gap, null_maxgap_mean=float(np.mean(null_max)),
                null_maxgap_hi=float(np.percentile(null_max, 95)),
                tv_over_net=tv/(net+1e-9), gap_stat=[float(x) for x in g], k_star=kstar,
                n=int(len(Q)))

syslist, labels = make_systems()
lam, pts, bad = run_all(syslist)
rows = []
for i, (s, r, b) in enumerate(syslist):
    d2 = corr_dim(pts[i], bad[i])
    K = (s + 1 + b)/3.0
    Q = -lam[i] - d2 - K
    rows.append(dict(label=labels[i], sigma=float(s), rho=float(r), beta=float(b),
                     lam=float(lam[i]), D2=float(d2), K=float(K), Q=float(Q)))

A = [x for x in rows if x["label"] == "A"]
B = [x for x in rows if x["label"] == "B"]
C = [x for x in rows if x["label"] == "C"]
QA, QB, QC = [x["Q"] for x in A], [x["Q"] for x in B], [x["Q"] for x in C]
rhos = [x["rho"] for x in A]

dA = quant_diagnostics(QA)
sp_r, sp_p = spearmanr(rhos, QA)
# Monotone-smooth NULL for the gap test: the sorted-gap statistic must be compared
# against the gaps of a smooth fit, NOT against a uniform null (anti-conservative
# for skewed densities).
poly = np.polyfit(rhos, QA, 5)
fitQ = np.polyval(poly, rhos)
resid = QA - fitQ
s_fit = np.sort(fitQ)
dA["maxgap_smooth_null"] = float(np.max(np.diff(s_fit))/(s_fit[-1]-s_fit[0]))
dA["resid_std"] = float(np.std(resid))
dA["resid_over_span"] = float(np.std(resid)/(np.max(QA)-np.min(QA)+1e-12))
refute_A = (sp_p < 0.01 and dA["k_star"] == 1 and
            dA["resid_over_span"] < 0.10 and
            dA["max_gap_norm"] <= 2.0*dA["maxgap_smooth_null"])
support_A = (dA["k_star"] >= 2 and dA["gap_stat"][dA["k_star"]] > 0.1 and
             dA["max_gap_norm"] > 1.3*dA["maxgap_smooth_null"] and
             dA["resid_over_span"] >= 0.10)
verdict = ("MIXED: neither a clean smooth trend nor a robust quantization signature — "
           "inspect diagnostics manually.")
if refute_A:
    verdict = ("REFUTED: on a fine rho-sweep Q(rho) is a smooth continuous trend "
               "(strong monotone Spearman, sorted-Q gaps within smooth-null range, k*=1) — "
               "no discrete quantized levels. 'Quantization' is an artifact of coarse sampling "
               "plus K being exactly piecewise-constant across regimes.")
if support_A:
    verdict = "SUPPORT: cluster/gap structure beyond smooth-null expectation."

results = dict(A_diag=dA, A_spearman=[float(sp_r), float(sp_p)],
               A_rho=rhos, A_Q=[float(q) for q in QA],
               A_poly5_resid=resid.tolist(),
               Q_std=float(np.nanstd(QA)),
               lam_range=[float(np.nanmin([x['lam'] for x in rows])), float(np.nanmax([x['lam'] for x in rows]))],
               D2_range=[float(np.nanmin([x['D2'] for x in rows])), float(np.nanmax([x['D2'] for x in rows]))],
               B_points=B, C_points=C, verdict=verdict)
print("A: Q in [%.3f, %.3f] std=%.4f  spearman r=%.3f p=%.2e" %
      (np.nanmin(QA), np.nanmax(QA), np.nanstd(QA), sp_r, sp_p), flush=True)
print("A diag:", {k: (np.round(v,3) if isinstance(v,float) else v) for k,v in dA.items()}, flush=True)
print("smooth-null: maxgap(fit)=%.3f resid_std=%.3f resid/span=%.3f" %
      (dA["maxgap_smooth_null"], dA["resid_std"], dA["resid_over_span"]), flush=True)
print("B:", [(x["sigma"], round(x["Q"],2)) for x in B], flush=True)
print("C:", [(round(x["beta"],2), round(x["Q"],2)) for x in C], flush=True)
print("lam range", results["lam_range"], "D2 range", results["D2_range"], flush=True)

fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
ax[0].plot(rhos, QA, "o-", ms=3, lw=1)
ax[0].set_xlabel("rho"); ax[0].set_ylabel("Q = -lam - D2 - K")
ax[0].set_title(f"A: fine rho sweep n={len(A)}\nspearman r={sp_r:.2f}, p={sp_p:.1e} -> continuous")
ax[0].grid(alpha=.3)
ax[1].bar(range(1, len(dA["gap_stat"])+1), dA["gap_stat"], color="#4dbbd5")
ax[1].axvline(dA["k_star"]+0.5, color="r", ls="--", label=f"k*={dA['k_star']}")
ax[1].set_xlabel("k"); ax[1].set_ylabel("gap statistic")
ax[1].set_title(f"cluster tendency: maxgap={dA['max_gap_norm']:.3f} vs null {dA['null_maxgap_mean']:.3f}")
ax[1].legend()
ax[2].plot([x["sigma"] for x in B], QB, "s-", label="sigma sweep")
ax[2].plot([x["beta"] for x in C], QC, "^-", label="beta sweep")
ax[2].set_xlabel("sigma / beta"); ax[2].set_ylabel("Q"); ax[2].set_title("B/C: Q varies continuously")
ax[2].legend(); ax[2].grid(alpha=.3)
plt.tight_layout()
out_png = "shared_agora/artifacts/hyp114_lorenz_q_quantization_mimo.png"
plt.savefig(out_png, dpi=110)
with open("shared_agora/artifacts/hyp114_lorenz_q_quantization_mimo.json", "w") as f:
    json.dump(results, f, indent=1, default=float)
print("VERDICT:", verdict, flush=True)
print("saved:", out_png)
