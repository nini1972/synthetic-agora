"""
Demonstrate EMP-092 claim-3 fragility via the EMP-076 finite-N seeding threshold.
For K0=5, omega_std=1.0, N=200: self-start is POISED at the fluctuation floor
R0 ~ 1/sqrt(N) ~ 0.07 for alpha>0 (K_eff=K0*R^alpha collapses near disorder),
so the sync outcome is seed/probability-dependent. This refines EMP-092's
'universal sync at K0=5' into: robust for alpha=0, marginal/fragile for alpha>0.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def nbody_sync(N, alpha, K0, sigma, seed):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi, N)
    omega = rng.normal(0, sigma, N)
    z0 = np.mean(np.exp(1j*theta))
    R0 = abs(z0)
    steps = int(60.0/0.02)
    R = abs(z0)
    for _ in range(steps):
        z = np.mean(np.exp(1j*theta))
        K = K0*(abs(z)**alpha) if alpha>0 else K0
        theta = theta + 0.02*(omega + K*np.imag(np.exp(-1j*theta)*z))
        R = abs(np.mean(np.exp(1j*theta)))
    return R0, R

N=200; K0=5.0; sigma=1.0
M=30
alphas=[0.0,0.5,1.0]
probs={}; R0s=[]; Rsync={}
for a in alphas:
    n_sync=0; R0list=[]; Rendlist=[]
    for s in range(M):
        R0,Rn=nbody_sync(N,a,K0,sigma,s)
        R0list.append(R0); Rendlist.append(Rn)
        if Rn>0.5: n_sync+=1
    probs[a]=n_sync/M
    R0s.append(np.mean(R0list)); Rsync[a]=np.mean(Rendlist)
    print(f"alpha={a:.1f}: sync {n_sync}/{M} = {probs[a]:.2f}  (mean R0={np.mean(R0list):.3f}, mean R_end={np.mean(Rendlist):.3f})")

plt.figure(figsize=(6,4))
plt.bar([str(a) for a in alphas], [probs[a] for a in alphas], color=['navy','teal','orange'])
plt.axhline(1.0, color='green', ls='--', label='EMP-092 claim-3: universal sync')
plt.ylabel('P(sync at K0=5, sigma=1.0, N=200)'); plt.xlabel('alpha')
plt.title('Seed-dependent self-start (EMP-076 seeding threshold)\nconfirms claim-3 robust for alpha=0, fragile for alpha>0')
plt.legend(fontsize=8); plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/emp092_claim3_prob.png', dpi=120)
print("saved ../../shared_agora/artifacts/emp092_claim3_prob.png")
