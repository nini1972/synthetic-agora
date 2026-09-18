"""Diagnostic: validate LE routine on plain Kuramoto (constant K) vs feedback.
Expectations: plain Kuramoto K<Kc -> LE ~= 0 (or slightly neg); K>Kc locked -> transversal LE negative.
If feedback gives a clean DIFFERENT positive value, the constant +0.0642 is a bug.
Author: hunyuan (Tencent).
"""
import numpy as np
N=200; DT=0.05; OMEGA_SD=1.0; SEED=7

def max_lyap_feedback(alpha,K0,omega,rng,eps=1e-8,T_settle=100.0,T_meas=400.0,renorm=10):
    theta=2*np.pi*rng.random(N); theta2=theta+eps*rng.standard_normal(N)
    for _ in range(int(T_settle/DT)):
        z=np.exp(1j*theta); R=np.abs(z.mean()); Psi=np.angle(z.mean()); K=K0*(R**alpha)
        theta=theta+DT*(omega+K*R*np.sin(Psi-theta))
    n_meas=int(T_meas/DT); n_ren=int(renorm); ly=[]
    for s in range(n_meas):
        z=np.exp(1j*theta); R=np.abs(z.mean()); Psi=np.angle(z.mean()); K=K0*(R**alpha)
        theta=theta+DT*(omega+K*R*np.sin(Psi-theta))
        z2=np.exp(1j*theta2); R2=np.abs(z2.mean()); Psi2=np.angle(z2.mean()); K2=K0*(R2**alpha)
        theta2=theta2+DT*(omega+K2*R2*np.sin(Psi2-theta2))
        if (s+1)%n_ren==0:
            d=np.linalg.norm(theta2-theta)
            if d>0:
                ly.append(np.log(d/eps)/(n_ren*DT)); theta2=theta+eps*(theta2-theta)/d
    return float(np.mean(ly)) if ly else 0.0

def max_lyap_plain(K,omega,rng,eps=1e-8,T_settle=100.0,T_meas=400.0,renorm=10):
    theta=2*np.pi*rng.random(N); theta2=theta+eps*rng.standard_normal(N)
    for _ in range(int(T_settle/DT)):
        theta=theta+DT*(omega+K*np.sin(np.angle(np.exp(1j*theta).mean())-theta))
    n_meas=int(T_meas/DT); n_ren=int(renorm); ly=[]
    for s in range(n_meas):
        theta=theta+DT*(omega+K*np.sin(np.angle(np.exp(1j*theta).mean())-theta))
        theta2=theta2+DT*(omega+K*np.sin(np.angle(np.exp(1j*theta2).mean())-theta2))
        if (s+1)%n_ren==0:
            d=np.linalg.norm(theta2-theta)
            if d>0:
                ly.append(np.log(d/eps)/(n_ren*DT)); theta2=theta+eps*(theta2-theta)/d
    return float(np.mean(ly)) if ly else 0.0

rng=np.random.default_rng(SEED); omega=rng.standard_normal(N)*OMEGA_SD
print('PLAIN Kuramoto (constant K):')
for K in [0.5,1.0,1.5,2.0,3.0,4.0]:
    print(f'  K={K}: LE={max_lyap_plain(K,omega,np.random.default_rng(SEED+int(K))):+.4f}')
print('FEEDBACK alpha=2 K0:')
for K0 in [1.0,2.0,3.0,4.0]:
    print(f'  K0={K0}: LE={max_lyap_feedback(2.0,K0,omega,np.random.default_rng(SEED+50+int(K0))):+.4f}')
print('done')
