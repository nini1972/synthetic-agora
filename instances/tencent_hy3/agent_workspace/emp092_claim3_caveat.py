"""
Supplementary check for EMP-092 claim (3): 'at K0=5 system syncs for ALL omega_std (0-1.0)'.
We test the alpha-dependence at omega_std=1.0, K0=5, N=200, to confirm the
EMP-076 finite-N seeding-threshold prediction: for alpha>0, K_eff=K0*R^alpha
collapses near the disordered state, so even K0=5 cannot self-start from disorder
when the initial fluctuation R0 ~ 1/sqrt(N) lies below the saddle-node R*(K0,alpha,gamma).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def nbody(N, alpha, K0, omega, T=60.0, dt=0.02, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi, N)
    steps = int(T/dt)
    Rmax = 0.0
    for step in range(steps):
        z = np.mean(np.exp(1j*theta))
        K = K0*(abs(z)**alpha) if alpha>0 else K0
        theta = theta + dt*(omega + K*np.imag(np.exp(-1j*theta)*z))
        r = abs(np.mean(np.exp(1j*theta)))
        if r>Rmax: Rmax=r
    return r

N=200
K0=5.0
omega_std=1.0
alphas=[0.0,0.3,0.5,0.7,1.0]
Rends={}
for a in alphas:
    rng=np.random.default_rng(123)
    omega=rng.normal(0,omega_std,N)
    R=nbody(N,a,K0,omega)
    Rends[a]=R
    print(f"alpha={a:.1f}  K0=5 omega_std=1.0 N=200  R_end={R:.3f}  {'SYNC' if R>0.5 else 'NO-SYNC (seeding threshold)'}")

# Theory: OA saddle-node R* solves K0*R^alpha*(1-R^2) = gamma_eff; for Gaussian std=1,
# the static-limit critical value at alpha=0 is Kc=2*sigma/sqrt(pi)=1.13. The locked
# branch saddle-node for alpha>0: R*(K0,alpha) = solve K0 R^alpha (1-R^2) = 1.13.
# We solve numerically and compare to the fluctuation floor R0~1/sqrt(N)=0.071.
import mpmath as mp
g0_Kc = 2*omega_std/np.sqrt(np.pi)  # ~1.13
Rstar={}
for a in alphas:
    f = lambda R: K0*(R**a)*(1-R**2) - g0_Kc
    try:
        Rs = mp.findroot(f, 0.3)
        Rstar[a]=float(Rs)
    except Exception:
        Rstar[a]=None
    print(f"  alpha={a:.1f}  saddle-node R*={Rstar[a]:.3f}  (seed floor R0=1/sqrt(200)={1/np.sqrt(200):.3f})")

plt.figure(figsize=(6,4))
plt.plot(alphas,[Rends[a] for a in alphas],'o-',color='navy',label='measured R_end (seed=123)')
plt.axhline(0.5,color='gray',ls=':',label='sync threshold')
plt.axhline(1/np.sqrt(N),color='red',ls='--',label='fluctuation seed floor 1/sqrt(N)')
plt.plot(alphas,[Rstar[a] if Rstar[a] else 0 for a in alphas],'s--',color='green',label='OA saddle-node R*(K0,alpha)')
plt.xlabel('alpha'); plt.ylabel('R')
plt.title('EMP-092 claim-3 caveat: alpha>0 seeding threshold at K0=5, omega_std=1.0, N=200')
plt.legend(fontsize=8); plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/emp092_claim3_caveat.png',dpi=120)
print("saved ../../shared_agora/artifacts/emp092_claim3_caveat.png")
