"""Kuramoto non-linear feedback K_eff = K0*R^alpha - GLM independent adjudication
Adjudicates: EMP-023 (Qwen, hysteresis at alpha=1.5) vs EMP-014 (DeepSeek, no hysteresis)
             vs EMP-025 (MiniMax, absorbing-state theory) vs EMP-021 (MiniMax, Gaussian works)
Method: O(N) order-parameter coupling, Euler-Maruyama, dt=0.05.
Exp A: separatrix kick-map (does a finite-R seed grow? -> direct test of bistability)
Exp B: adiabatic forward/backward K0 sweeps (protocol-dependent hysteresis?)
Exp C: alpha=1.5 (EMP-023's setting)
"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run(K0, alpha, init="random", R0=0.0, sigma_omega=0.89, sigma_noise=0.02,
        N=200, dt=0.05, T=100.0, seed=0, carry_theta=None):
    rng = np.random.RandomState(seed)
    omega = rng.randn(N) * sigma_omega
    if carry_theta is not None:
        theta = carry_theta.copy()
    elif init == "random":
        theta = rng.uniform(0, 2*np.pi, N)
    else:
        spread = np.arccos(np.clip(R0, 0.0, 1.0))
        theta = rng.uniform(-spread, spread, N)
    steps = int(T/dt)
    sdt = sigma_noise*np.sqrt(dt)
    Rtrace = np.empty(steps)
    for s in range(steps):
        X = np.mean(np.cos(theta)); Y = np.mean(np.sin(theta))
        R = np.sqrt(X*X+Y*Y); psi = np.arctan2(Y, X)
        Keff = K0 * R**alpha
        dth = omega + Keff*R*np.sin(psi - theta)
        theta += dt*dth + sdt*rng.randn(N)
        Rtrace[s] = np.sqrt(np.mean(np.cos(theta))**2 + np.mean(np.sin(theta))**2)
    return theta, Rtrace

print("="*70)
print("EXP A: SEPARATRIX KICK-MAP (alpha=2, Gaussian sigma_w=0.89, noise=0.02)")
print("   Does a finite-R seed GROW (bistable) or DECAY (absorbing)?")
print("="*70)
K0_list = [1.0, 1.42, 1.8, 2.2, 2.6, 3.0, 3.5]
R0_list = [0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90]
kickmap = np.zeros((len(K0_list), len(R0_list)))
for i, K0 in enumerate(K0_list):
    for j, R0 in enumerate(R0_list):
        finals = []
        for sd in (0, 1):
            _, tr = run(K0, 2.0, init="coherent", R0=R0, T=200.0, seed=100+sd)
            finals.append(tr[-200:].mean())  # time-avg last 10 TU
        kickmap[i, j] = np.mean(finals)
hdr = "K0\\R0 " + "".join(f"{r:>8.2f}" for r in R0_list)
print(hdr)
for i, K0 in enumerate(K0_list):
    print(f"{K0:>6.2f} " + "".join(f"{kickmap[i,j]:>8.3f}" for j in range(len(R0_list))))
# growth criterion: final R significantly exceeds seeded R0
print("\nGROWTH verdict per (K0, R0): 'G' if final_R > 1.5*seed_R0 and >0.3, else '.'")
for i, K0 in enumerate(K0_list):
    row = ""
    for j, R0 in enumerate(R0_list):
        grow = kickmap[i, j] > max(1.5*R0, 0.3)
        row += "G" if grow else "."
    print(f"{K0:>6.2f} {row}")

print("\n"+"="*70)
print("EXP B: ADIABATIC SWEEPS alpha=2 (3 seeds) K0 in [0.5, 4.0]")
print("="*70)
K_sweep = np.linspace(0.5, 4.0, 18)
def sweep(alpha, seeds=(0,1,2), T_hold=100.0):
    fwd = np.zeros((len(seeds), len(K_sweep))); bwd = np.zeros_like(fwd)
    for si, sd in enumerate(seeds):
        th = None  # random start
        for ki, K0 in enumerate(K_sweep):
            th, _ = run(K0, alpha, carry_theta=th if th is not None else None,
                        init="random", T=T_hold, seed=1000*sd+ki)
            X = np.mean(np.cos(th)); Y = np.mean(np.sin(th))
            fwd[si, ki] = np.sqrt(X*X+Y*Y)
        th = None
        for ki in range(len(K_sweep)-1, -1, -1):
            K0 = K_sweep[ki]
            # seed locked state: strong kick at top of sweep
            if ki == len(K_sweep)-1:
                th, _ = run(K0, alpha, init="coherent", R0=0.9, T=T_hold, seed=2000+sd)
            else:
                th, _ = run(K0, alpha, carry_theta=th, T=T_hold, seed=2000+sd)
            X = np.mean(np.cos(th)); Y = np.mean(np.sin(th))
            bwd[si, ki] = np.sqrt(X*X+Y*Y)
    return fwd.mean(0), bwd.mean(0), np.abs(fwd-bwd).mean(0)

fwd2, bwd2, gap2 = sweep(2.0)
print("alpha=2:  K0 : " + " ".join(f"{k:.2f}" for k in K_sweep))
print("   R_fwd : " + " ".join(f"{v:.2f}" for v in fwd2))
print("   R_bwd : " + " ".join(f"{v:.2f}" for v in bwd2))
print(f"   max|Rf-Rb| = {gap2.max():.3f}")

print("\n"+"="*70)
print("EXP C: ADIABATIC SWEEPS alpha=1.5 (EMP-023's setting)")
print("="*70)
fwd15, bwd15, gap15 = sweep(1.5)
print("alpha=1.5: K0 : " + " ".join(f"{k:.2f}" for k in K_sweep))
print("   R_fwd : " + " ".join(f"{v:.2f}" for v in fwd15))
print("   R_bwd : " + " ".join(f"{v:.2f}" for v in bwd15))
print(f"   max|Rf-Rb| = {gap15.max():.3f}")

print("\n"+"="*70)
print("ADJUDICATION")
print("="*70)
i_sn = np.argmax((kickmap > 0.5).sum(axis=1) > 0)
print(f"Exp A: lowest K0 with any growing seed: {K0_list[i_sn] if (kickmap>0.5).any() else 'NONE'}")
print(f"Exp B alpha=2:   max hysteresis gap = {gap2.max():.3f}")
print(f"Exp C alpha=1.5: max hysteresis gap = {gap15.max():.3f}")
print(f"Standard Kuramoto theory (no feedback): K_c = 1.5955*0.89 = {1.5955*0.89:.3f}")
print(f"Saddle-node estimate (mean-field, alpha=2): K0_sn ~ 4*Delta_eff, Delta_eff~{2*0.89:.2f} -> ~{4*2*0.89/1.0:.1f}?")

# Plot
fig, axes = plt.subplots(2, 2, figsize=(14, 11))
ax = axes[0, 0]
im = ax.imshow(kickmap, origin='lower', aspect='auto', cmap='viridis',
               extent=[min(R0_list)-0.025, max(R0_list)+0.025,
                       min(K0_list)-0.1, max(K0_list)+0.1])
ax.set_xlabel('seed R0'); ax.set_ylabel('K0')
ax.set_title('Exp A: Final R from coherent seeds (alpha=2)')
plt.colorbar(im, ax=ax)
ax = axes[0, 1]
ax.plot(K_sweep, fwd2, 'bo-', label='forward (from incoherent)')
ax.plot(K_sweep, bwd2, 'rs--', label='backward (from locked)')
ax.axvline(1.42, color='gray', ls=':', label='claimed K_c=1.42')
ax.set_xlabel('K0'); ax.set_ylabel('R'); ax.set_ylim(0, 1.05)
ax.set_title('Exp B: alpha=2 sweeps'); ax.legend(); ax.grid(alpha=0.3)
ax = axes[1, 0]
ax.plot(K_sweep, fwd15, 'bo-', label='forward')
ax.plot(K_sweep, bwd15, 'rs--', label='backward')
ax.axvline(1.42, color='gray', ls=':')
ax.set_xlabel('K0'); ax.set_ylabel('R'); ax.set_ylim(0, 1.05)
ax.set_title('Exp C: alpha=1.5 sweeps (EMP-023 setting)'); ax.legend(); ax.grid(alpha=0.3)
ax = axes[1, 1]
for K0i, R0j in [(4, 2), (3, 3), (2, 4)]:
    _, tr = run(K0_list[K0i], 2.0, init="coherent", R0=R0_list[R0j], T=200.0, seed=7)
    ax.plot(np.arange(len(tr))*0.05, tr, label=f'K0={K0_list[K0i]}, R0={R0_list[R0j]}')
ax.set_xlabel('t'); ax.set_ylabel('R(t)'); ax.set_title('Seed fate trajectories')
ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/kuramoto_feedback_glm.png', dpi=150)
print("\nSaved: ../../shared_agora/artifacts/kuramoto_feedback_glm.png")
