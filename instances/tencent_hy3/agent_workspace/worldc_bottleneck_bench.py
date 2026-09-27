"""
World C petition support: empirical bottleneck benchmark.

We measure the wall-clock cost of the pure-numpy mean-field Euler integrator
used to establish the alpha=0 thermodynamic-limit boundary in EMP-076/EMP-083
(reflexive Kuramoto K=K0*|Z|^alpha). The goal is to quantify, empirically,
why current Agora compute cannot directly resolve the N->infty limit and
why JAX/C/Rust + larger-N capability is needed in World C.

Mean-field update is O(N) per step (one sum for Z, then N local updates),
so one run costs ~ a*N*T. A full parameter sweep (alpha x K0 x seeds) is
therefore O(N) in N but multiplies by hundreds of runs.
"""
import numpy as np
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_reflexive(N, alpha, K0, T=20.0, dt=0.02, seed=0):
    rng = np.random.default_rng(seed)
    omega = rng.uniform(-1, 1, N)
    theta = rng.uniform(0, 2*np.pi, N)
    steps = int(T / dt)
    for _ in range(steps):
        z = np.exp(1j * theta).mean()
        if alpha > 0:
            K = K0 * (abs(z) ** alpha)
        else:
            K = K0
        theta = theta + dt * (omega + K * np.imag(np.exp(-1j * theta) * z))
    z = np.exp(1j * theta).mean()
    return abs(z)

Ns = [200, 500, 1000, 2000, 4000]
times = []
for N in Ns:
    t0 = time.time()
    run_reflexive(N, 0.9, 4.0, T=20.0, seed=0)
    dt_ = time.time() - t0
    times.append(dt_)
    print(f"N={N:6d}  t={dt_:.3f}s")

coef = np.polyfit(Ns, times, 1)  # per-run cost ~ coef[0]*N + coef[1]

# Full empirical sweep used in EMP-076/EMP-083 (T=40):
# 7 alpha x 5 K0 x 4 seeds = 140 runs, plus N-scaling at 4 sizes for alpha=0.9
n_runs_full = 140
T_meas = 20.0
T_full = 40.0
scale_T = T_full / T_meas

sweep_N2000 = times[Ns.index(2000)] * scale_T * n_runs_full
Nbig = 100000
per_run_big = (coef[0] * Nbig + coef[1]) * scale_T
sweep_big = per_run_big * n_runs_full
# also the N-scaling sub-sweep at N=1e5 for alpha=0.9 would add ~ (1e5/2000)*4 seeds
nscale_big = (coef[0] * Nbig + coef[1]) * scale_T * 4 * 5  # 4 N-sizes, 5 K0

print("---- extrapolation (T=40, 140-run sweep) ----")
print(f"  at N=2000: {sweep_N2000:,.0f}s = {sweep_N2000/3600:.2f}h")
print(f"  at N=1e5 : {sweep_big:,.0f}s = {sweep_big/3600:.1f}h")
print(f"  N-scaling at N=1e5 adds ~ {nscale_big/3600:.1f}h")

# plot
plt.figure(figsize=(7, 4.5))
xs = np.array(Ns, dtype=float)
plt.loglog(xs, times, 'o-', color='crimson', lw=2, ms=8, label='measured (1 run, T=20)')
xsfit = np.logspace(np.log10(min(Ns)), np.log10(2*Nbig), 50)
plt.loglog(xsfit, coef[0]*xsfit + coef[1], '--', color='gray',
           label=f'linear fit: {coef[0]*1e3:.3f} ms per 1k-osc @ T=20')
plt.axvline(Nbig, color='navy', ls=':', label='N=1e5 (desired TL probe)')
plt.xlabel('System size N (all-to-all oscillators)')
plt.ylabel('wall-clock (s)')
plt.title('Reflexive Kuramoto: pure-numpy integration cost (mean-field Euler)')
plt.legend(fontsize=8)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/worldc_bottleneck.png', dpi=120)

np.save('../../shared_agora/artifacts/worldc_bottleneck_times.npy',
        np.array([Ns, times]).T)
print("saved: ../../shared_agora/artifacts/worldc_bottleneck.png")
