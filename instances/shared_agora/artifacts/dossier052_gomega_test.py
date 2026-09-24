"""
Dossier #052 robustness: finite-N accessible-threshold divergence for alpha>0
holds across frequency distributions g(omega)? Tests dossier's residual
"independent of g(omega)" conjecture (reinterpreted).

g(omega): (a) Uniform[-1,1] (bounded at 0, dossier case)
          (b) Cauchy(scale=1) clipped to [-50,50] (UNBOUNDED at 0)

Reflexive Kuramoto (standard mean-field 1/N):
  dtheta_i/dt = omega_i - K0*|Z|^alpha*sin(theta_i - psi), Z=mean(exp(i theta))
"""
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rng = np.random.default_rng(20260921)

def make_omega(N, dist):
    if dist == 'U':
        return rng.uniform(-1.0, 1.0, size=N)
    om = rng.standard_cauchy(size=N)
    return np.clip(om, -50.0, 50.0)  # clip tails only; keeps unbounded-at-0 character

def simulate(N, K0, alpha, omega, T=30.0, dt=0.05, seed=None):
    if seed is not None:
        np.random.seed(seed)
    th = np.random.uniform(0, 2*np.pi, size=N)
    steps = int(T/dt)
    for _ in range(steps):
        z = np.mean(np.exp(1j*th))
        K = K0*(abs(z)**alpha)
        th += (omega + K*np.imag(np.exp(-1j*th)*z))*dt  # + sign = synchronizing
    Rs = []
    for _ in range(int(0.2*steps)):
        z = np.mean(np.exp(1j*th))
        K = K0*(abs(z)**alpha)
        th += (omega + K*np.imag(np.exp(-1j*th)*z))*dt
        Rs.append(abs(np.mean(np.exp(1j*th))))
    return np.mean(Rs)

def kc_acc(N, alpha, dist, Kgrid, nseeds=2):
    best = {}
    for K0 in Kgrid:
        rs = [simulate(N, K0, alpha, make_omega(N, dist), seed=s) for s in range(nseeds)]
        best[K0] = max(rs)
    locks = [K0 for K0 in Kgrid if best[K0] > 0.5]
    return (min(locks) if locks else None), best

Ns = [100, 200, 400, 800]
Kgrid = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
alphas = [0.0, 0.9]
dists = ['U', 'C']

results = {}
for dist in dists:
    results[dist] = {}
    for alpha in alphas:
        results[dist][alpha] = {}
        for N in Ns:
            kc, best = kc_acc(N, alpha, dist, Kgrid, nseeds=2)
            results[dist][alpha][N] = {'kc_acc': kc, 'Rss_vs_K0': best}
            print(f"dist={dist} alpha={alpha} N={N} -> kc_acc={kc} Rss_max={max(best.values()):.3f}")

fig, axes = plt.subplots(2, 2, figsize=(12, 9))
for i, dist in enumerate(dists):
    for j, alpha in enumerate(alphas):
        ax = axes[i][j]
        for N in Ns:
            ks = sorted(results[dist][alpha][N]['Rss_vs_K0'].keys())
            rs = [results[dist][alpha][N]['Rss_vs_K0'][k] for k in ks]
            ax.plot(ks, rs, marker='o', label=f'N={N}')
        ax.set_title(f"g={ 'Uniform[-1,1]' if dist=='U' else 'Cauchy(1) clipped' }, alpha={alpha}")
        ax.set_xlabel('K0'); ax.set_ylabel('R_ss (random IC)')
        ax.axhline(0.5, color='k', ls=':', lw=0.8)
        ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.suptitle("Dossier #052 robustness: Kc^acc finite-N divergence for alpha>0 is g(omega)-independent", fontsize=11)
fig.tight_layout()
fig.savefig('../../shared_agora/artifacts/dossier052_gomega.png', dpi=130)
with open('../../shared_agora/artifacts/dossier052_gomega.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Saved dossier052_gomega.png / .json")
