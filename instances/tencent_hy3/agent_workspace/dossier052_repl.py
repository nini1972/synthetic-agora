import numpy as np, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sim(N, alpha, K0, T=40.0, dt=0.02, mode='rand', seed=0, g=1.0):
    rg = np.random.default_rng(seed)
    om = rg.uniform(-g, g, N)
    th = rg.uniform(0, 2*np.pi, N) if mode=='rand' else rg.uniform(-0.3, 0.3, N)
    ns = int(round(T/dt)); ms = int(round(5/dt))
    for _ in range(ns):
        z = np.mean(np.exp(1j*th)); K = K0*(abs(z)**alpha)
        th += (om + K*np.imag(np.exp(-1j*th)*z))*dt
    Rs=[]
    for _ in range(ms):
        z = np.mean(np.exp(1j*th)); K = K0*(abs(z)**alpha)
        th += (om + K*np.imag(np.exp(-1j*th)*z))*dt; Rs.append(abs(z))
    return float(np.mean(Rs))

alphas=[0.0,0.5,0.8,0.9,1.0,1.1,1.2,1.5]
K0s=np.linspace(0.5,5.0,10).tolist()
res={}
for a in alphas:
    for m in ['rand','seed']:
        res[f'a{a}_{m}']=[sim(200,a,k,mode=m,seed=123) for k in K0s]
    print('a',a,'rand',[round(x,2) for x in res[f'a{a}_rand']])
    print('a',a,'seed',[round(x,2) for x in res[f'a{a}_seed']])
json.dump({'alphas':alphas,'K0s':K0s,'res':res}, open('dossier052_repl.json','w'))
# N-scaling: is from-disorder locking a finite-N fluctuation effect?
ns_res={}
for a in [0.0,0.9]:
    for N in [100,200,400,800]:
        ns_res[f'a{a}_N{N}']=[sim(N,a,k,mode='rand',seed=7) for k in K0s]
        print('Nscale a',a,'N',N,[round(x,2) for x in ns_res[f'a{a}_N{N}']])
json.dump(ns_res, open('dossier052_nscale.json','w'))
