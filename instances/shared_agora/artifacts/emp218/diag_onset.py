"""Diagnose Stage1 vs Stage2 discrepancy for Kuramoto r near onset.
Hypothesis: r-threshold K_c estimates are unreliable due to CRITICAL SLOWING DOWN
+ finite burn-in, near K_c. Test burn-in sensitivity at fixed K."""
import numpy as np
from numba import njit

@njit(cache=True, fastmath=True)
def integ(th, om, K, dt, n):
    N = th.shape[0]
    for s in range(n):
        cx=0.0; cy=0.0
        for i in range(N): cx+=np.cos(th[i]); cy+=np.sin(th[i])
        R=np.sqrt(cx*cx+cy*cy)/N; psi=np.arctan2(cy,cx)
        k1=om+K*R*np.sin(psi-th); t1=th+0.5*dt*k1
        cx=0.0; cy=0.0
        for i in range(N): cx+=np.cos(t1[i]); cy+=np.sin(t1[i])
        R=np.sqrt(cx*cx+cy*cy)/N; psi=np.arctan2(cy,cx)
        k2=om+K*R*np.sin(psi-t1); t2=th+0.5*dt*k2
        cx=0.0; cy=0.0
        for i in range(N): cx+=np.cos(t2[i]); cy+=np.sin(t2[i])
        R=np.sqrt(cx*cx+cy*cy)/N; psi=np.arctan2(cy,cx)
        k3=om+K*R*np.sin(psi-t2); t3=th+dt*k3
        cx=0.0; cy=0.0
        for i in range(N): cx+=np.cos(t3[i]); cy+=np.sin(t3[i])
        R=np.sqrt(cx*cx+cy*cy)/N; psi=np.arctan2(cy,cx)
        k4=om+K*R*np.sin(psi-t3)
        th=th+(dt/6.0)*(k1+2*k2+2*k3+k4)
    return th

@njit(cache=True, fastmath=True)
def r_now(th):
    N=th.shape[0]; cx=0.0; cy=0.0
    for i in range(N): cx+=np.cos(th[i]); cy+=np.sin(th[i])
    return np.sqrt(cx*cx+cy*cy)/N

N=1024; dt=0.02
rng=np.random.default_rng(22)
om=rng.uniform(-1.0,1.0,N)   # uniform W=1
Kc=4/np.pi
print(f"Uniform W=1: analytic Kc = {Kc:.4f}")
for K in [1.15, 1.20, 1.25, 1.2732, 1.30, 1.40]:
    r0=np.random.default_rng(5).uniform(0,2*np.pi,N)
    row=[]
    for Tb in [50,150,300,600,1200,2400]:
        th=integ(r0,om,K,dt,int(Tb/dt))
        # time-average over 40 time units
        acc=0.0; nA=2000
        for s in range(nA):
            acc+=r_now(th)
            th=integ(th,om,K,dt,1)
        row.append(acc/nA)
    print(f"K={K:.4f} (K-Kc={K-Kc:+.3f}): r vs burnin[50,150,300,600,1200,2400] = "+
          " ".join(f"{v:.3f}" for v in row))
