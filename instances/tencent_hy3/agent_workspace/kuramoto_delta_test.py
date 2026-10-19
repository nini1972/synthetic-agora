"""Decisive test: does the a=2 'failure' in EMP-148 arise from natural-frequency spread Δ≠0?
Escape-time law t_esc=2/(a*K0*R0^a) is derived for IDENTICAL oscillators (Delta=0).
We test a in {1,2}, Delta in {0, 0.5, 1.0}, N=300, K0=5, T=200, 8 seeds.
"""
import numpy as np, json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sim(N, a, K0, Delta, T=200.0, dt=0.01, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi, N)
    if Delta > 0:
        # exact Lorentzian(0,Delta) via inverse CDF
        U = rng.uniform(1e-6, 1-1e-6, N)
        omega = Delta * np.tan(np.pi*(U-0.5))
    else:
        omega = np.zeros(N)
    steps = int(T/dt)
    R_arr=[]
    for _ in range(steps):
        z = np.mean(np.exp(1j*theta)); R=np.abs(z); psi=np.angle(z)
        Keff = K0*(R**a)
        theta = theta + dt*(omega + Keff*R*np.sin(psi-theta))
        R_arr.append(R)
    R_arr=np.array(R_arr)
    final=R_arr[-1]
    tail=R_arr[int(0.75*len(R_arr)):]
    locked = bool(np.all(tail>=0.5))
    return final, locked

configs=[(1,0.0),(1,0.5),(1,1.0),(2,0.0),(2,0.5),(2,1.0)]
seeds=range(8)
out={}
for a,Delta in configs:
    finals=[]; locks=[]
    for s in seeds:
        f,l=sim(300,a,5,Delta,seed=s)
        finals.append(f); locks.append(l)
    key=f"a{a}_Delta{Delta}"
    out[key]=dict(a=a,Delta=Delta,lock_rate=float(np.mean(locks)),
                  R_final_mean=float(np.mean(finals)),
                  R_final_min=float(np.min(finals)),
                  R_final_max=float(np.max(finals)))
    print(f"a={a} Delta={Delta}: lock_rate={np.mean(locks):.3f} R_final_mean={np.mean(finals):.4f} R_final_range=[{np.min(finals):.4f},{np.max(finals):.4f}]")

# OA flow for each, with Delta
Rs=np.linspace(0.001,1.0,500)
plt.figure(figsize=(10,4))
for a in [1,2]:
    for Delta in [0.0,1.0]:
        f=(Rs/2)*(5*Rs**a*(1-Rs*Rs) - Delta)
        plt.plot(Rs,f,label=f'a={a},Δ={Delta}')
plt.axhline(0,color='k',lw=0.5); plt.xlabel('R'); plt.ylabel('dR/dt (OA)')
plt.title('OA flow: Δ≠0 introduces barrier (esp. for a=2)'); plt.legend()
plt.tight_layout(); plt.savefig('kuramoto_delta_oa.png',dpi=120)

with open('kuramoto_delta_test.json','w') as fh:
    json.dump(out,fh,indent=2)
print("DONE")
