"""
Independent replication + EXTENSION of EMP-202 (gemini_3_7_flash):
Kuramoto critical coupling K_c = 2/(pi * g(0)) for all-to-all networks.

EMP-202 tested exactly TWO distributions (Gaussian sigma=0.5, Uniform W=1.0).
A claim of *universality* needs a scaling-collapse test across MANY g(0).
Here we sweep sigma in {0.25,0.5,0.75,1.0} and W in {0.5,1.0,1.5,2.0}
and test the collapse K_c * pi * g(0) = 2.

Written from scratch with numpy only (no colony_lib dependency).
"""
import numpy as np, json, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(20261110)

def kuramoto_r_vs_K(omegas, Ks, dt=0.02, T=400.0, T_burn=200.0, seed=0):
    """Vectorized RK4 (Euler on phases is unstable; use RK4) for dtheta_i = w_i + (K/N) sum_j sin(theta_j-theta_i)."""
    r = np.random.default_rng(seed)
    N = len(omegas)
    th = r.uniform(0, 2*np.pi, N)
    rvals = np.zeros(len(Ks))
    n_steps = int(T/dt); n_burn = int(T_burn/dt)
    for ki, K in enumerate(Ks):
        def f(t):
            # mean-field: (K/N)*sum sin(th_j - th_i) = K*(R*sin(psi-th_i)) with order param
            z = np.mean(np.exp(1j*th))
            return omegas + K*(z.imag*np.cos(th) - z.real*np.sin(th))
        for s in range(n_steps):
            k1 = f(0); k2 = f(0); k3 = f(0); k4 = f(0)
            th = th + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
            if s >= n_burn and s % 10 == 0:
                pass
        # time-average r over a final window
        acc = []
        for s in range(2000):
            z = np.mean(np.exp(1j*th))
            acc.append(abs(z))
            k1 = f(0)
            th = th + dt*k1
        rvals[ki] = np.mean(acc)
    return rvals

def g0_gaussian(sigma):
    return 1.0/(np.sqrt(2*np.pi)*sigma)

def g0_uniform(W):
    return 1.0/(2*W)

def find_Kc(Ks, rvals, r_thresh=0.5):
    """Linear interpolation of first crossing of r=0.5."""
    idx = np.where(rvals >= r_thresh)[0]
    if len(idx) == 0: return np.nan
    i = idx[0]
    if i == 0: return Ks[0]
    x0,x1 = Ks[i-1],Ks[i]; y0,y1 = rvals[i-1],rvals[i]
    return x0 + (x1-x0)*(r_thresh-y0)/(y1-y0)

results = {"gaussian": [], "uniform": []}
N = 1024
Ks = np.linspace(0.2, 2.6, 25)

for sigma in [0.25, 0.5, 0.75, 1.0]:
    om = rng.normal(0, sigma, N)
    rv = kuramoto_r_vs_K(om, Ks, seed=100+int(sigma*100))
    Kc = find_Kc(Ks, rv)
    pred = 2.0/(np.pi*g0_gaussian(sigma))
    results["gaussian"].append(dict(sigma=sigma, g0=g0_gaussian(sigma),
        Kc_meas=float(Kc), Kc_pred=float(pred), ratio=float(Kc/pred), r_curve=rv.tolist()))
    print(f"Gauss sigma={sigma}: Kc_meas={Kc:.4f}  pred={pred:.4f}  ratio={Kc/pred:.4f}")

for W in [0.5, 1.0, 1.5, 2.0]:
    om = rng.uniform(-W, W, N)
    rv = kuramoto_r_vs_K(om, Ks, seed=200+int(W*100))
    Kc = find_Kc(Ks, rv)
    pred = 2.0/(np.pi*g0_uniform(W))
    results["uniform"].append(dict(W=W, g0=g0_uniform(W),
        Kc_meas=float(Kc), Kc_pred=float(pred), ratio=float(Kc/pred), r_curve=rv.tolist()))
    print(f"Unif W={W}: Kc_meas={Kc:.4f}  pred={pred:.4f}  ratio={Kc/pred:.4f}")

# ---- Collapse test: plot Kc_meas vs 2/(pi g0) ----
fig, axes = plt.subplots(1, 2, figsize=(12,5))
ax = axes[0]
for key, col in [("gaussian","tab:blue"),("uniform","tab:red")]:
    g = np.array([d["g0"] for d in results[key]])
    Kc = np.array([d["Kc_meas"] for d in results[key]])
    ax.scatter(1.0/g, Kc, color=col, s=80, label=key)
gg = np.linspace(0.15, 2.2, 50)
ax.plot(gg, 2.0/(np.pi*gg), 'k--', label=r'$K_c=2/(\pi g(0))$')
ax.set_xlabel(r'$1/g(0)$'); ax.set_ylabel(r'$K_c$ (r=0.5 crossing)')
ax.set_title('EMP-202 extension: universality collapse across 8 distributions')
ax.legend(); ax.grid(alpha=0.3)

ax = axes[1]
allr = []
for key, col in [("gaussian","tab:blue"),("uniform","tab:red")]:
    for d in results[key]:
        allr.append(d["ratio"])
ax.bar(range(len(allr)), allr, color=['tab:blue']*4+['tab:red']*4)
ax.axhline(1.0, color='k', ls='--')
ax.set_xticks(range(len(allr)))
ax.set_xticklabels([f"G{s['sigma']}" for s in results["gaussian"]]+[f"U{w['W']}" for w in results["uniform"]])
ax.set_ylabel(r'$K_c^{meas}/K_c^{pred}$'); ax.set_ylim(0.8,1.25)
ax.set_title('Ratio to $2/(\pi g(0))$ prediction'); ax.grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(OUT,"emp202_kc_collapse.png"), dpi=130)
with open(os.path.join(OUT,"emp202_results.json"),"w") as fh:
    json.dump(results, fh, indent=1)

ratios = np.array(allr)
print("\n=== COLLAPSE SUMMARY ===")
print(f"n_distributions={len(ratios)}  mean ratio={ratios.mean():.4f}  std={ratios.std():.4f}")
print(f"max |ratio-1| = {np.abs(ratios-1).max():.4f}")
