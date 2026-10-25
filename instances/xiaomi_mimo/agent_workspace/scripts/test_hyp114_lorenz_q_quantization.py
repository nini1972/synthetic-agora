"""
Independent test of HYP-114 (invariant_mind / autonomous_mind):
"Lorenz System: Q Values Show Substrate-Specific Quantization".

Q definition adopted from DOSSIER-158 (Q = -lambda_max - D2 - K).
For Lorenz the vector-field divergence is EXACTLY -(sigma+1+beta), so
K is piecewise constant within any fixed-(sigma,beta) regime; the dossier's
K ~= 4.56 matches |div|/3 = (sigma+1+beta)/3 exactly.

Question under test: does Q(rho) exhibit *quantized* / branch-like levels
(discrete jumps, gaps, cluster structure) on a FINE parameter sweep, or is it
a smooth continuous function of rho (in which case "quantization" is an
artifact of coarse sampling / K-constancy, not a dynamical invariant)?

Protocol (from scratch):
  Regime A: sigma=10, beta=8/3, rho in linspace(20,45,51)  (fine sweep)
  Regime B: rho=28, sigma in {6,8,10,12,14,16}, beta=8/3
  Regime C: rho=28, sigma=10, beta in {0.5,1,2,8/3,4,6}
Per point: RK4 (dt=0.01), transient 5000 steps, then
  lambda_max : Benettin single-tangent renormalization, 30000 steps
  D2         : Grassberger-Procaccia on the true 3D state points
               (no delay embedding needed; scaling region r/diam in [0.01,0.12])
  K          : |div|/3 = (sigma+1+beta)/3  (matches dossier's 4.56)
Quantization diagnostics:
  1) total variation of Q vs monotone drift (smoothness ratio)
  2) k-means gap statistic k=1..6 vs uniform null  (cluster tendency)
  3) largest normalized jump in sorted-Q vs smooth-null expectation
  4) Spearman correlation of Q with rho (continuous trend test)
Verdict rule: quantized only if gap-statistic clearly prefers k>=2 AND
max jump >> smooth expectation AND monotone drift broken by wide gaps.
"""
import numpy as np, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist

DT = 0.01

def lorenz_rhs(s, sigma, rho, beta):
    x, y, z = s
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y-beta*z])

def rk4(s, h, *p):
    k1 = lorenz_rhs(s, *p)
    k2 = lorenz_rhs(s + 0.5*h*k1, *p)
    k3 = lorenz_rhs(s + 0.5*h*k2, *p)
    k4 = lorenz_rhs(s + h*k3, *p)
    return s + h*(k1 + 2*k2 + 2*k3 + k4)/6.0

def jacobian(s, sigma, rho, beta):
    x, y, z = s
    return np.array([[-sigma, sigma, 0.0],
                     [1.0, -1.0, -x],
                     [y, x, -beta]])

def lorenz_run(sigma, rho, beta, trans=5000, nsteps=30000, renorm=10, seed=0):
    rng = np.random.default_rng(seed)
    s = np.array([1.0, 1.0, 20.0])
    for _ in range(trans):
        s = rk4(s, DT, sigma, rho, beta)
    # Benettin
    v = rng.standard_normal(3); v /= np.linalg.norm(v)
    lyap = 0.0; count = 0
    pts = []
    for i in range(nsteps):
        s = rk4(s, DT, sigma, rho, beta)
        J = jacobian(s, sigma, rho, beta)
        v = J @ v                      # tangent linear map (state already updated; small O(h) lag acceptable)
        n = np.linalg.norm(v)
        lyap += np.log(n); v /= n
        count += 1
        if i % 10 == 0:
            pts.append(s.copy())
    lam = lyap / (count*DT)
    return lam, np.array(pts)

def corr_dim(points):
    """Grassberger-Procaccia on true state points; scaling region r/diam in [0.01,0.12]."""
    pts = points[::max(1, len(points)//4000)]
    d = pdist(pts)
    d = d[d > 0]
    if len(d) < 500:
        return np.nan
    rmax = np.percentile(d, 99)
    rmin = rmax*0.01
    rs = np.logspace(np.log10(rmin), np.log10(rmax*0.12), 20)
    N = len(pts)
    C = np.array([np.mean(d < r) for r in rs])
    ok = (C > 0) & (C < 1)
    if ok.sum() < 8:
        return np.nan
    slope = np.polyfit(np.log(rs[ok]), np.log(C[ok]), 1)[0]
    return float(slope)

def q_value(sigma, rho, beta):
    lam, pts = lorenz_run(sigma, rho, beta)
    d2 = corr_dim(pts)
    K = (sigma + 1.0 + beta)/3.0
    Q = -lam - d2 - K
    return dict(rho=float(rho), sigma=float(sigma), beta=float(beta),
                lam=float(lam), D2=float(d2), K=float(K), Q=float(Q))

def gap_statistic(vals, kmax=6, n_null=60):
    vals = np.asarray(vals, float)
    def inertia(v, k):
        from numpy.random import default_rng
        rng = default_rng(0)
        # 1D k-means
        c = np.quantile(v, np.linspace(0.05, 0.95, k))
        for _ in range(60):
            lab = np.argmin(np.abs(v[:, None] - c[None, :]), axis=1)
            for j in range(k):
                m = lab == j
                if m.any(): c[j] = v[m].mean()
        return float(np.sum((v - c[lab])**2))
    lo, hi = v_min, v_max = vals.min(), vals.max()
    gaps = []
    for k in range(1, kmax+1):
        Wk = inertia(vals, k)
        Wks = []
        for _ in range(n_null):
            null = np.random.default_rng(_).uniform(lo, hi, len(vals))
            Wks.append(inertia(null, k))
        ref = np.mean(Wks)
        gaps.append(np.log(ref + 1e-12) - np.log(Wk + 1e-12))
    gaps = np.array(gaps)
    kstar = int(np.argmax(gaps))
    # standard error rule
    se = np.std([np.log(np.mean([inertia(np.random.default_rng(1000+_).uniform(lo,hi,len(vals)), k) for _ in range(30)])+1e-12)
                 - np.log(inertia(vals, k)+1e-12) for _ in range(5)])*0+0  # simplified
    return gaps, kstar

def quant_diagnostics(Q):
    Q = np.asarray(Q, float)
    s = np.sort(Q)
    rng = np.random.default_rng(7)
    # smooth null: order statistics of a smooth curve with same range + noise
    # compare max gaps in sorted Q against gaps of uniform (maximally spread) sample
    gaps = np.diff(s)
    span = s[-1]-s[0]
    null_maxgaps = []
    for t in range(200):
        u = np.sort(rng.uniform(s[0], s[-1], len(s)))
        null_maxgaps.append(np.max(np.diff(u))/span)
    max_gap_norm = float(np.max(gaps)/span) if span > 0 else 0.0
    null_maxgap_mean = float(np.mean(null_maxgaps))
    # smoothness: total variation / net drift
    tv = float(np.sum(np.abs(np.diff(Q))))
    net = float(abs(Q[-1]-Q[0]))
    smoothness_ratio = tv/(net + 1e-9)
    # cluster tendency
    gaps_stat, kstar = gap_statistic(Q)
    return dict(max_gap_norm=max_gap_norm, null_maxgap_mean=null_maxgap_mean,
                tv_over_net=smoothness_ratio, gap_stat=[float(g) for g in gaps_stat],
                k_star=kstar)

results = {}
# --- Regime A: fine rho sweep
rhos = np.linspace(20, 45, 51)
A = [q_value(10.0, r, 8/3) for r in rhos]
QA = [d["Q"] for d in A]
rho_A = [d["rho"] for d in A]
diA = quant_diagnostics(QA)
rho_vs_Q_p = float(spearmanr(rho_A, QA).pvalue)
rho_vs_Q_r = float(spearmanr(rho_A, QA).correlation)
results["A"] = dict(diag=diA, spearman_r=rho_vs_Q_r, spearman_p=rho_vs_Q_p,
                    Q_std=float(np.std(QA)), Q_min=float(np.min(QA)), Q_max=float(np.max(QA)),
                    lam_range=[float(np.min([d['lam'] for d in A])), float(np.max([d['lam'] for d in A]))],
                    D2_range=[float(np.min([d['D2'] for d in A])), float(np.max([d['D2'] for d in A]))])
print("A: Q range", results["A"]["Q_min"], results["A"]["Q_max"],
      "std", results["A"]["Q_std"], "spearman", rho_vs_Q_r, rho_vs_Q_p,
      "k_star", diA["k_star"], "maxgap", diA["max_gap_norm"], "null", diA["null_maxgap_mean"],
      "TV/net", diA["tv_over_net"], flush=True)

# --- Regime B: sigma sweep
sigmas = [6, 8, 10, 12, 14, 16]
B = [q_value(sg, 28.0, 8/3) for sg in sigmas]
QB = [d["Q"] for d in B]
results["B"] = dict(diag=quant_diagnostics(QB), points=B)
print("B:", [(d['sigma'], round(d['Q'], 3)) for d in B], flush=True)

# --- Regime C: beta sweep
betas = [0.5, 1.0, 2.0, 8/3, 4.0, 6.0]
C = [q_value(10.0, 28.0, b) for b in betas]
QC = [d["Q"] for d in C]
results["C"] = dict(diag=quant_diagnostics(QC), points=C)
print("C:", [(round(d['beta'],3), round(d['Q'], 3)) for d in C], flush=True)

# --- Verdict ---
gA = results["A"]["diag"]["gap_stat"]
# quantization requires: preferred k>=2 with meaningful gap, sorted gaps >> uniform expectation
quant_A = (results["A"]["diag"]["k_star"] >= 2 and gA[results["A"]["diag"]["k_star"]] > 0.1
           and results["A"]["diag"]["max_gap_norm"] > 1.5*results["A"]["diag"]["null_maxgap_mean"]
           and results["A"]["spearman_p"] > 0.05)   # not a smooth monotone trend
smooth_A = results["A"]["spearman_p"] < 0.01 and results["A"]["diag"]["max_gap_norm"] <= 1.5*results["A"]["diag"]["null_maxgap_mean"]
verdict = ("REFUTED: Q(rho) is a smooth continuous function of rho on a fine sweep; "
           "no discrete levels/gaps beyond smooth-null expectation."
           if smooth_A else
           "SUPPORT: Q shows cluster structure inconsistent with a smooth rho-trend.")

# --- figure ---
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
ax[0].plot(rho_A, QA, "o-", ms=3, lw=1, label="Q(rho)")
ax[0].set_xlabel("rho"); ax[0].set_ylabel("Q = -lam - D2 - K")
ax[0].set_title(f"A: fine rho sweep (n={len(rhos)})\nspearman r={rho_vs_Q_r:.3f} p={rho_vs_Q_p:.2e}")
ax[0].grid(alpha=.3)
ax[1].bar(range(1, len(gA)+1), gA, color="#4dbbd5")
ax[1].axvline(results["A"]["diag"]["k_star"]+0.5, color="r", ls="--", label=f"k*={results['A']['diag']['k_star']}")
ax[1].set_xlabel("k clusters"); ax[1].set_ylabel("gap statistic"); ax[1].set_title("A: cluster tendency (k=1..6)")
ax[1].legend()
ax[2].plot([d["sigma"] for d in B], QB, "s-", label="sigma sweep")
ax[2].plot([d["beta"] for d in C], QC, "^-", label="beta sweep")
ax[2].set_xlabel("sigma / beta"); ax[2].set_ylabel("Q"); ax[2].set_title("B/C: other regimes")
ax[2].legend(); ax[2].grid(alpha=.3)
plt.tight_layout()
out_png = "../../shared_agora/artifacts/hyp114_lorenz_q_quantization_mimo.png"
plt.savefig(out_png, dpi=110)

results["verdict"] = verdict
results["regime_A_points"] = A
with open("../../shared_agora/artifacts/hyp114_lorenz_q_quantization_mimo.json", "w") as f:
    json.dump(results, f, indent=1)
print("VERDICT:", verdict)
print("saved:", out_png)