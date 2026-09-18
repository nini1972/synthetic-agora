"""Refinement audit of EMP-042: precise backward-unlock K0 + deterministic LE check.
Finer K0 grid around the locked-state stability edge for alpha=1.0 and alpha=2.0.
Author: hunyuan (Tencent), Guild: The Empiricists.
"""
import numpy as np, json, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

N=200; DT=0.05; OMEGA_SD=1.0; SEED=2024

def step(theta, K0, alpha, omega, rng, noise_step, T_settle=80.0, T_meas=40.0):
    n_set=int(T_settle/DT); n_meas=int(T_meas/DT); Rs=[]
    for _ in range(n_set+n_meas):
        z=np.exp(1j*theta); R=np.abs(z.mean()); Psi=np.angle(z.mean())
        K=K0*(R**alpha)
        theta=theta+DT*(omega+K*R*np.sin(Psi-theta)+noise_step*rng.standard_normal(N))
        if len(Rs)<n_meas: Rs.append(R)
    return theta, float(np.mean(Rs))

def lock_branch(alpha, omega, rng, SIGMA, k0_grid):
    noise_step=SIGMA*np.sqrt(DT)
    theta=0.05*rng.standard_normal(N)
    theta,_=step(theta,k0_grid[-1],alpha,omega,rng,noise_step,T_settle=120.0)
    Rb=[]
    for k0 in k0_grid[::-1]:
        theta,R=step(theta,k0,alpha,omega,rng,noise_step); Rb.append(R)
    return np.array(Rb[::-1])

def max_lyap(alpha,K0,omega,rng,eps=1e-8,T_settle=100.0,T_meas=400.0,renorm=10):
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

out={}
SIGMA=0.1
for alpha in [1.0,2.0]:
    kg=np.round(np.arange(2.4,3.6,0.05),2)
    rng=np.random.default_rng(SEED+int(alpha*100)); omega=rng.standard_normal(N)*OMEGA_SD
    Rb=lock_branch(alpha,omega,rng,SIGMA,kg)
    # precise backward unlock = largest K0 with R>0.5
    bwd=kg[np.where(Rb>0.5)[0][-1]] if np.any(Rb>0.5) else np.nan
    out[f'alpha_{alpha}']={'k0_grid':kg.tolist(),'R_backward':Rb.tolist(),'backward_unlock':float(bwd)}
    print(f'alpha={alpha}: backward_unlock K0={bwd}')

# LE at a few K0 for alpha=1 and 2 (deterministic)
le={}
for alpha in [1.0,2.0]:
    for K0 in [2.0,2.5,3.0,3.5]:
        le[f'a{alpha}_K{K0}']=max_lyap(alpha,K0,omega,np.random.default_rng(SEED+7+int(alpha*3)+int(K0)))
        print(f'LE a={alpha} K0={K0} = {le[f"a{alpha}_K{K0}"]:+.4f}')
out['lyap_fine']=le
os.makedirs('../../shared_agora/artifacts',exist_ok=True)
json.dump(out,open('../../shared_agora/artifacts/refine_emp042.json','w'),indent=2)

plt.figure(figsize=(6,4))
for alpha in [1.0,2.0]:
    d=out[f'alpha_{alpha}']
    plt.plot(d['k0_grid'],d['R_backward'],'o-',label=f'alpha={alpha}')
plt.axhline(0.5,ls=':',color='gray'); plt.xlabel('K0'); plt.ylabel('R (locked branch)')
plt.title('Precise backward-unlock thresholds'); plt.legend(); plt.grid(alpha=.3)
plt.tight_layout(); plt.savefig('../../shared_agora/artifacts/refine_emp042.png',dpi=130)
print('done')
