"""DOSSIER_003 v2: Two-cluster Kuramoto with R^2 inter-cluster feedback.
Intra-cluster coupling fixed strong (clusters self-lock, R_f~R_s~1);
inter-cluster K_eff = K0*(R_f R_s)^2. Relative phase then obeys the
Adler equation phi' = Dw - 2 K_eff sin(phi), whose period-averaged
coherence is exactly  |<e^{i phi}>| = delta - sqrt(delta^2-1),  delta=Dw/(2 K_eff)
-> asymptotic slope -1 (UNIVERSAL), steep local slope near threshold.
Compare Gaussian / Lorentzian / Uniform / wide-Cauchy cluster widths.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

K0, K_intra = 2.0, 4.0
dt, T, burn = 0.05, 300.0, 150.0
N = 150
sigma_n = 0.02

def sim(Dw, kind, seed):
    r = np.random.default_rng(seed)
    if kind == "gauss_tight":
        wf, ws = r.normal(Dw/2, .1, N), r.normal(-Dw/2, .1, N)
    elif kind == "gauss_wide":
        wf, ws = r.normal(Dw/2, .5, N), r.normal(-Dw/2, .5, N)
    elif kind == "cauchy":
        wf, ws = Dw/2 + r.standard_cauchy(N)*.4, -Dw/2 + r.standard_cauchy(N)*.4
    else:  # uniform
        wf, ws = r.uniform(Dw/2-.3, Dw/2+.3, N), r.uniform(-Dw/2-.3, -Dw/2+.3, N)
    th = r.uniform(0, 2*np.pi, 2*N)
    w = np.concatenate([wf, ws])
    steps = int(T/dt); b = int(burn/dt)
    acc = 0j; n = 0
    fi = r.choice(N, 20, replace=False); sj = r.choice(N, 20, replace=False)
    for s in range(steps):
        zf = np.exp(1j*th[:N]).mean(); zs = np.exp(1j*th[N:]).mean()
        Keff = K0 * (abs(zf)*abs(zs))**2
        drive_f = K_intra*np.imag(np.exp(-1j*th[:N])*zf) + Keff*np.imag(np.exp(-1j*th[:N])*zs)
        drive_s = K_intra*np.imag(np.exp(-1j*th[N:])*zs) + Keff*np.imag(np.exp(-1j*th[:N])*zf)
        th[:N] = (th[:N] + dt*(w[:N] + drive_f + sigma_n*r.standard_normal(N))) % (2*np.pi)
        th[N:] = (th[N:] + dt*(w[N:] + drive_s + sigma_n*r.standard_normal(N))) % (2*np.pi)
        if s > b and s % 2 == 0:
            acc += np.exp(1j*(th[:N][fi, None] - th[N:][None, sj])).mean()
            n += 1
    return float(np.abs(acc/n))

kinds = ["gauss_tight", "gauss_wide", "cauchy", "uniform"]
Dws = np.array([0.5, 0.8, 1.2, 2.0, 3.0, 5.0, 8.0, 12.0])
fig, ax = plt.subplots(figsize=(7.5, 5.5))
gam = {}
for k in kinds:
    vals = np.array([sim(Dw, k, seed=10+i) for i, Dw in enumerate(Dws)])
    m = Dws >= 3.0
    g, c = np.polyfit(np.log(Dws[m]), np.log(vals[m]), 1)
    gam[k] = -g
    ax.loglog(Dws, vals, 'o-', label=f"{k}: tail slope {-g:.2f}")
# exact Adler prediction with K'=2*K0
dd = np.linspace(1.0001, 30, 300)
xadl = 2*K0*dd
yadl = dd - np.sqrt(dd**2 - 1)
ax.loglog(xadl, yadl, 'k--', lw=1.5, label=r"Adler exact: $|\delta-\sqrt{\delta^2-1}|$")
ax.set_xlabel(r'$\Delta\omega$'); ax.set_ylabel(r'$R_{cross}$')
ax.set_title(f'Dossier003 v2: gap scaling vs topology (K0={K0}, R^2 feedback)')
ax.legend(fontsize=8); fig.tight_layout()
fig.savefig("dossier003_v2_adler.png", dpi=120)
print("TAIL SLOPES:", {k: round(v, 3) for k, v in gam.items()})
# local effective exponent in a mid window like the dossier's range
for k in kinds[:2]:
    pass
print("Saved dossier003_v2_adler.png")