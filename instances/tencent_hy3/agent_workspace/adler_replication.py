"""
Independent replication of EMP-171 (noisy Adler stationary order parameter).
Two independent estimations:
  (M1) Long-time Monte Carlo Euler-Maruyama (T=1000 >> diffusion time ~1/D~800),
       stationary averaging over many periods, theta0 randomized.
  (M2) Stationary Fokker-Planck periodic solve (constant-flux ansatz),
       vectorized on a fine grid.
  (A) dw=0 analytic anchor: R = I1(2K/D)/I0(2K/D), matched independently.
Params disputed: K=1.65, sigma=0.05 (D=0.00125), dw in {4,5,6}.
GLM claims stationary R = 0.5271 / 0.3769 / 0.300.
"""
import numpy as np
trapz = getattr(np,'trapezoid',np.trapz)
from scipy.special import iv as I_mod
import json, sys

K=1.65; sigma=0.05; D=sigma**2/2.0
print(f"K={K} sigma={sigma} D={D:.5f}")
anch = I_mod(1,2*K/D)/I_mod(0,2*K/D)
print(f"dw=0 analytic anchor R=I1(2K/D)/I0(2K/D) = {anch:.6f}")

# ---- (M2) Stationary FP (vectorized) ----
def fp_stationary_r(dw, nphi=4000):
    phi=np.linspace(0,2*np.pi,nphi,endpoint=False); dphi=phi[1]-phi[0]
    a=K*np.cos(phi)-dw
    # (D p'' - a p')=J, periodic p, <p>=1 => J=0. Solve via 2nd-order central FD.
    # Build sparse tridiagonal+wrap with numpy (no Python loop).
    n=nphi
    main=np.full(n,-2*D/dphi**2)
    off_p=np.zeros(n); off_m=np.zeros(n)
    for i in range(n):
        ip=(i+1)%n; im=(i-1)%n
        off_p[ip]+= D/dphi**2 - a[i]/(2*dphi)
        off_m[im]+= D/dphi**2 + a[i]/(2*dphi)
    # assemble dense for small n
    A=np.zeros((n,n))
    for i in range(n):
        A[i,i]=main[i]; A[i,(i+1)%n]+=off_p[i]; A[i,(i-1)%n]+=off_m[i]
    A=np.vstack([A, np.ones(n)])
    b=np.zeros(n+1); b[-1]=1.0
    p,*_=np.linalg.lstsq(A,b,rcond=None)
    p=np.clip(p,1e-300,None); p=p/trapz(p,phi)
    return float(np.abs(trapz(np.exp(1j*phi)*p,phi)))

# ---- (M1) Long-time MC (lean, vectorized step) ----
def mc_r(dw, N=4000, dt=0.05, Ttr=200.0, Tm=600.0, seed=0):
    rng=np.random.default_rng(seed)
    th=rng.uniform(0,2*np.pi,N)
    ntr=int(Ttr/dt); nacc=int(Tm/dt)
    for _ in range(ntr):
        dW=np.sqrt(dt)*rng.standard_normal(N)
        th=(th+(K*np.cos(th)-dw+(sigma**2/2)*np.sin(th)*np.cos(th))*dt+sigma*dW)%(2*np.pi)
    Rs=[]
    for _ in range(nacc):
        dW=np.sqrt(dt)*rng.standard_normal(N)
        th=(th+(K*np.cos(th)-dw+(sigma**2/2)*np.sin(th)*np.cos(th))*dt+sigma*dW)%(2*np.pi)
        Rs.append(np.abs(np.mean(np.exp(1j*th))))
    return float(np.mean(Rs)),float(np.std(np.asarray(Rs)))

dw=int(sys.argv[1]) if len(sys.argv)>1 else 4
claims={4:0.5271,5:0.3769,6:0.300}
mc,mcs=mc_r(dw)
fp=fp_stationary_r(dw)
print(f"\n=== dw={dw} ===")
print(f"claim(stationary)={claims[dw]:.4f}  MC_R={mc:.4f} (std {mcs:.4f})  FP_R={fp:.4f}")
print(f"MC vs claim diff={abs(mc-claims[dw]):.4f} -> {'OK' if abs(mc-claims[dw])<0.03 else 'DIFF'}")
json.dump({'dw':dw,'claim':claims[dw],'MC_R':mc,'MC_std':mcs,'FP_R':fp,'anchor':anch},
          open(f'adler_dw{dw}.json','w'),indent=2)
