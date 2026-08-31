"""Kuramoto non-linear feedback K_eff = K0*R^alpha - GLM independent adjudication (vectorized)"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_batch(K0, alpha, thetas, omegas, sigma_noise=0.02, dt=0.05, T=100.0):
    """thetas: (B, N) batch of initial phase configs. Returns final thetas, mean R over last 10 TU."""
    steps = int(T/dt); sdt = sigma_noise*np.sqrt(dt)
    Rsum = 0.0; cnt = 0
    for s in range(steps):
        X = thetas[:, :].cos() if False else np.cos(thetas).mean(1)
        Y = np.sin(thetas).mean(1)
        R = np.sqrt(X*X+Y*Y); psi = np.arctan2(Y, X)
        Keff = (K0 * R**alpha)[:, None]
        dth = omegas[None, :] + Keff*R[:, None]*np.sin(psi[:, None] - thetas)
        thetas = thetas + dt*dth + sdt*np.random.randn(*thetas.shape)
        if s >= steps - 200:
            Rsum += np.sqrt(np.cos(thetas).mean(1)**2 + np.sin(thetas).mean(1)**2); cnt += 1
    return thetas, Rsum/cnt

N = 200; sigma_omega = 0.89
rng = np.random.RandomState(42)
omegas = rng.randn(N) * sigma_omega

def make_batch(R0_list, n_seeds, init="coherent"):
    thetas = []
    for R0 in R0_list:
        for sd in range(n_seeds):
            r = np.random.RandomState(1000*sd + int(R0*100) + 7)
            if init == "coherent":
                spread = np.arccos(np.clip(R0, 0, 1))
                thetas.append(r.uniform(-spread, spread, N))
            else:
                thetas.append(r.uniform(0, 2*np.pi, N))
    return np.array(thetas)

print("EXP A: SEPARATRIX KICK-MAP (alpha=2): final R from coherent seeds")
K0_list = [1.0, 1.42, 1.8, 2.2, 2.6, 3.0, 3.5]
R0_list = [0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90]
# batch: rows = K0 x R0, each with 2 seeds -> vectorize over (R0,seeds) per K0
kickmap = np.zeros((len(K0_list), len(R0_list)))
for i, K0 in enumerate(K0_list):
    th = make_batch(R0_list, 2, "coherent")
    _, Rf = run_batch(K0, 2.0, th, omegas, T=150.0)
    kickmap[i] = Rf.reshape(len(R0_list), 2).mean(1)
print("K0\\R0 " + "".join(f"{r:>7.2f}" for r in R0_list))
for i, K0 in enumerate(K0_list):
    print(f"{K0:>5.2f} " + "".join(f"{v:>7.3f}" for v in kickmap[i]))

print("\nEXP B/C: ADIABATIC SWEEPS (3 seeds), T_hold=100")
K_sweep = np.linspace(0.5, 4.0, 18)

def sweep(alpha):
    nf = len(K_sweep); ns = 3
    fwd = np.zeros((ns, nf)); bwd = np.zeros((ns, nf))
    # forward: random init, adiabatic carry
    th = make_batch([0], ns, "random")  # (3, N) different seeds
    for ki, K0 in enumerate(K_sweep):
        th, Rf = run_batch(K0, alpha, th, omegas, T=100.0)
        fwd[:, ki] = Rf
    # backward: start locked at top
    th = np.array([np.random.RandomState(500+sd).uniform(-0.45, 0.45, N) for sd in range(ns)])
    for ki in range(nf-1, -1, -1):
        K0 = K_sweep[ki]
        th, Rb = run_batch(K0, alpha, th, omegas, T=100.0)
        bwd[:, ki] = Rb
    return fwd.mean(0), bwd.mean(0), np.abs(fwd-bwd).mean(0)

fwd2, bwd2, gap2 = sweep(2.0)
print("alpha=2   Rf:", " ".join(f"{v:.2f}" for v in fwd2))
print("alpha=2   Rb:", " ".join(f"{v:.2f}" for v in bwd2))
print(f"alpha=2   max|Rf-Rb| = {gap2.max():.3f}")
fwd15, bwd15, gap15 = sweep(1.5)
print("alpha=1.5 Rf:", " ".join(f"{v:.2f}" for v in fwd15))
print("alpha=1.5 Rb:", " ".join(f"{v:.2f}" for v in bwd15))
print(f"alpha=1.5 max|Rf-Rb| = {gap15.max():.3f}")

print("\nADJUDICATION")
grow = (kickmap > np.maximum(1.5*np.array(R0_list)[None,:], 0.3))
firstK = next((K0_list[i] for i in range(len(K0_list)) if grow[i].any()), None)
print(f"Lowest K0 with growing seed (bistability onset): {firstK}")
print(f"Standard Kuramoto K_c (no feedback, Gaussian s=0.89): {1.5955*0.89:.3f}")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
ax = axes[0, 0]
im = ax.imshow(kickmap, origin='lower', aspect='auto', cmap='viridis',
               extent=[0.0, 1.0, 0.75, 3.75])
ax.set_xlabel('seed R0'); ax.set_ylabel('K0'); plt.colorbar(im, ax=ax)
ax.set_title('Exp A: final R from coherent seeds (alpha=2)')
ax = axes[0, 1]
ax.plot(K_sweep, fwd2, 'bo-', label='fwd (incoherent start)')
ax.plot(K_sweep, bwd2, 'rs--', label='bwd (locked start)')
ax.axvline(1.42, color='gray', ls=':', label='claimed K_c=1.42')
ax.set_ylim(0, 1.05); ax.set_xlabel('K0'); ax.set_ylabel('R')
ax.set_title('Exp B: alpha=2'); ax.legend(); ax.grid(alpha=0.3)
ax = axes[1, 0]
ax.plot(K_sweep, fwd15, 'bo-'); ax.plot(K_sweep, bwd15, 'rs--')
ax.axvline(1.42, color='gray', ls=':')
ax.set_ylim(0, 1.05); ax.set_xlabel('K0'); ax.set_ylabel('R')
ax.set_title('Exp C: alpha=1.5'); ax.grid(alpha=0.3)
ax = axes[1, 1]
th = make_batch([0.1, 0.3, 0.5], 1, "coherent")
th_run = th.copy()
tr = []
for K0 in (1.42, 2.2, 3.0):
    t2, Rf = run_batch(K0, 2.0, th_run, omegas, T=100.0)
    tr.append(float(np.mean(Rf)))
ax.bar([1.42, 2.2, 3.0], tr, width=0.2)
for x, v, r0 in zip([1.42, 2.2, 3.0], tr, [0.1, 0.3, 0.5]):
    ax.plot([x-0.15, x+0.15], [r0, r0], 'r--', label='seed R0' if x == 1.42 else None)
ax.set_xlabel('K0'); ax.set_ylabel('final R'); ax.legend()
ax.set_title('Seed survival at fixed K0')
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/kuramoto_feedback_glm.png', dpi=150)
print("Saved kuramoto_feedback_glm.png")
