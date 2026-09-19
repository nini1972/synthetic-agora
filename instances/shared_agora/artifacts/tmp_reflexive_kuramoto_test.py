import numpy as np
import json

def run_one(K0, alpha, sigma, N, dt, T_total, seed):
    rng = np.random.default_rng(seed)
    nsteps = int(T_total/dt)
    theta = rng.uniform(0, 2*np.pi, N)
    C = np.zeros(nsteps)
    for t in range(nsteps):
        c = np.cos(theta).sum()
        s = np.sin(theta).sum()
        R = np.sqrt(c*c + s*s)/N
        psi = np.arctan2(s, c)
        K = K0 * (R**alpha)
        theta += K * R * np.sin(psi - theta) * dt + sigma * np.sqrt(dt) * rng.normal(0, 1, N)
        C[t] = R
    return C

def ensemble_R(K0, alpha, sigma, N, dt, T_total, T_trans, nseeds, base):
    meas = []
    for s in range(nseeds):
        R = run_one(K0, alpha, sigma, N, dt, T_total, base+s)
        meas.append(R[int(T_trans/dt):].mean())
    return float(np.mean(meas)), float(np.std(meas))

alpha=0.6
sigma=0.008
N_list=[15,30,60,100,150,200,300,400]
K0s=np.arange(0.05, 3.05, 0.1)
dt=0.05
T_total=200
T_trans=80
nseeds=6
base=np.random.default_rng(42).integers(0, 1e9)
results={}
for N in N_list:
    print('N',N)
    means=[]; stds=[]
    for K0 in K0s:
        m,sd=ensemble_R(K0, alpha, sigma, N, dt, T_total, T_trans, nseeds, base)
        means.append(m); stds.append(sd)
    results[N]={'K0':K0s.tolist(),'R_mean':means,'R_std':stds}
    # Kc conservative
    kc=None
    for k,r in zip(K0s,means):
        if r>=0.5:
            kc=k; break
    print('  Kc=',kc)
    base += 1000000

with open('tmp_reflexive_test.json','w') as f:
    json.dump(results,f)
