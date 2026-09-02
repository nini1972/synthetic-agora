"""DOSSIER_003 adjudication: Is the resonance-gap exponent gamma ~ 1.38 universal
across frequency-distribution topologies (Gaussian vs Lorentzian vs Uniform)?

Theory prior (Adler equation): for a single pair of oscillators with frequency
gap Dw below the locking threshold K_eff, the relative phase drifts; the
period-averaged cross-correlation is
    <e^{i phi}> = (Dw - sqrt(Dw^2 - K^2)) / K  ~=  K / (2 Dw)   for Dw >> K
=>  R_cross ~ K0 R^alpha / (2 Dw)  =>  gamma -> 1 asymptotically, UNIVERSAL,
independent of the global frequency-distribution shape (the topology enters
only through K_eff and R0 prefactors). gamma=1.38 measured at moderate Dw is
plausibly a finite-Dw crossover, not a universal exponent.

Protocol: two clusters (fast omegas +Dw/2, slow omegas -Dw/2), N=100 each,
feedback K_eff = K0*R^alpha, alpha=2. Measure R_cross = |<e^{i(theta_f - theta_s)}>|
by splitting the order parameter: R_cross = |R_f e^{-i psi_f} - R_s e^{-i psi_s}| /2
... simpler: R_cross = |<e^{i theta}>_f * conj(<e^{i theta}>_s)| / (R_f R_s) -> 1 if
both locked; if drifting, use |<e^{i(theta_f - theta_s)}>| computed directly.
Sweep Dw, fit log-log slope on the tail (Dw/K0 in [3, 30]).
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(7)
K0, alpha, dt, T = 2.0, 2.0, 0.05, 400.0
Nf = Ns = 100
sigma_n = 0.02

def sim_cluster_gap(Dw, topo, K0=K0, alpha=alpha, T=T, seed=0):
    r = np.random.default_rng(seed)
    if topo == "gauss":
        wf = r.normal(+Dw/2, 0.1, Nf); ws = r.normal(-Dw/2, 0.1, Ns)
    elif topo == "lorentz":
        wf = Dw/2 + r.standard_cauchy(Nf)*0.1; ws = -Dw/2 + r.standard_cauchy(Ns)*0.1
    else:
        wf = r.uniform(+Dw/2-0.1, +Dw/2+0.1, Nf); ws = r.uniform(-Dw/2-0.1, -Dw/2+0.1, Ns)
    th = r.uniform(0, 2*np.pi, Nf+Ns)
    w = np.concatenate([wf, ws])
    steps = int(T/dt); acc = 0.0 + 0.0j
    n_acc = 0
    fi = r.choice(Nf, 25, replace=False); sj = r.choice(Ns, 25, replace=False)
    for s in range(steps):
        z = np.exp(1j*th).mean()
        Keff = K0 * max(abs(z), 1e-3)**alpha
        dth = w + Keff*np.imag(np.exp(-1j*th)*z) + sigma_n*r.standard_normal(Nf+Ns)
        th = (th + dt*dth) % (2*np.pi)
        if s > steps*0.5 and s % 2 == 0:
            acc += np.exp(1j*(th[:Nf][fi, None] - th[Nf:][None, sj])).mean()
            n_acc += 1
    return float(np.abs(acc / n_acc))

topos = ["gauss", "lorentz", "uniform"]
Dws = np.array([0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.5, 6.0])
res = {t: [] for t in topos}
for t in topos:
    for i, Dw in enumerate(Dws):
        res[t].append(sim_cluster_gap(Dw, t, seed=i))
    res[t] = np.array(res[t])
    print(t, np.round(res[t], 3))

# tail fit on last 4 points (Dw >= 1.2, i.e. Dw/K_eff from ~1.5 to ~7)
mask = Dws >= 1.2
fig, ax = plt.subplots(figsize=(7, 5))
gammas = {}
for t in topos:
    g, c = np.polyfit(np.log(Dws[mask]), np.log(res[t][mask]), 1)
    gammas[t] = -g
    ax.loglog(Dws, res[t], 'o-', label=f"{t}: tail gamma={-g:.2f}")
ax.set_xlabel(r'$\Delta\omega$'); ax.set_ylabel(r'$R_{cross}$')
ax.set_title(f'Dossier 003: resonance-gap scaling (K0={K0}, alpha={alpha})')
ax.legend(); fig.tight_layout()
fig.savefig("dossier003_gamma_topology.png", dpi=120)
print("FITTED TAIL GAMMAS:", {k: round(v, 3) for k, v in gammas.items()})
print("Saved dossier003_gamma_topology.png")
