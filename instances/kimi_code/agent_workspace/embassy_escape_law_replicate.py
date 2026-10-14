import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from time import time
import json
from collections import defaultdict
np.random.seed(0)

def simulate(N,K0,a,kappa=1.0,tmax=100.0,dt=0.05,lock_thr=0.95,seed=0):
    rng=np.random.default_rng(seed)
    omega=rng.normal(0,kappa,size=N)
    theta=rng.uniform(0,2*np.pi,size=N)
    z=np.exp(1j*theta).mean()
    R0=np.abs(z)
    steps=int(tmax/dt)
    t_lock=np.nan
    z_now=z
    for s in range(steps+1):
        R=np.abs(z_now)
        if R>=lock_thr:
            t_lock=s*dt
            break
        psi=np.angle(z_now)
        # Heun predictor-corrector
        theta_local=np.angle(z_now) # dummy, need actual theta
        # maintain theta array
    # Re-implement with theta array for correctness
    rng=np.random.default_rng(seed)
    omega=rng.normal(0,kappa,size=N)
    theta=rng.uniform(0,2*np.pi,size=N)
    t_lock=np.nan
    for s in range(steps+1):
        z=np.exp(1j*theta).mean()
        R=np.abs(z)
        if R>=lock_thr:
            t_lock=s*dt
            break
        psi=np.angle(z)
        dtheta=omega + K0*(R**a)*np.sin(psi-theta)
        thp=theta+dt*dtheta
        zp=np.exp(1j*thp).mean()
        psip=np.angle(zp)
        dtheta2=omega + K0*(np.abs(zp)**a)*np.sin(psip-thp)
        theta=theta+0.5*dt*(dtheta+dtheta2)
    return R0,t_lock

# primary collapse across parameter grid
K0s=[5.0,20.0]
alpha_vals=[1.0,2.0]
kappas=[0.5,1.0,2.0]
N=300
nseeds=12
records=[]
print('Running N=300 parameter sweep...'); t0=time()
for K0 in K0s:
    for a in alpha_vals:
        for kap in kappas:
            tmax=100.0 if a==1.0 else 200.0
            for s in range(nseeds):
                seed=1000*(int(K0)+int(a*10)+int(kap*10))+s
                R0,t_lock=simulate(N=N,K0=K0,a=a,kappa=kap,tmax=tmax,seed=seed)
                u=0.5*a*K0*(R0**a)*t_lock if np.isfinite(t_lock) else np.nan
                records.append({'K0':K0,'a':a,'kappa':kap,'seed':s,'R0':R0,'t_lock':t_lock,'u':u})
print('sweep done in %.1fs, locked %d/%d'%(time()-t0, np.sum(np.isfinite([r['t_lock'] for r in records])), len(records)))

def pct(x,p):
    x=np.asarray(x)
    return np.percentile(x[~np.isnan(x)],p) if np.any(~np.isnan(x)) else np.nan
uvals=np.array([r['u'] for r in records])
print('u median %.3f, p10 %.3f, p90 %.3f'%(pct(uvals,50),pct(uvals,10),pct(uvals,90)))

fig,ax=plt.subplots(figsize=(6,4))
finite=[r for r in records if np.isfinite(r['u'])]
ax.loglog([r['R0'] for r in finite], [r['t_lock'] for r in finite], 'o', alpha=0.35, ms=5)
R0s=np.logspace(-1.4,-0.3,200)
for a in alpha_vals:
    for K0 in K0s:
        t_hat=2.0/(a*K0*R0s**a)
        ax.loglog(R0s,t_hat,'-',label=r'$t_{esc}=2/(a K_0 R_0^a)$, a=%.0f K0=%.0f'%(a,K0))
ax.set_xlabel('Initial order parameter $R_0$')
ax.set_ylabel('Time to lock $t_{lock}$')
ax.set_title('EMP? embassy: escape-time law replication (N=300, uniform $\pm\kappa$)')
ax.legend(fontsize=8); ax.grid(True,ls='--',alpha=0.3)
fig.tight_layout(); fig.savefig('../../shared_agora/artifacts/embassy_escape_law_R0_tlock.png',dpi=150)
print('saved R0_tlock')

fig,ax=plt.subplots(figsize=(6,4))
ax.hist(uvals[~np.isnan(uvals)], bins=30, color='steelblue', edgecolor='k', alpha=0.7)
ax.axvline(1.0,color='r',ls='--',label='predictor=1')
ax.set_xlabel('$u = a K_0 R_0^a t_{lock}/2$'); ax.set_ylabel('count')
ax.set_title('u-distribution (median %.3f)'%pct(uvals,50))
ax.legend(); fig.tight_layout(); fig.savefig('../../shared_agora/artifacts/embassy_escape_law_u_hist.png',dpi=150)
print('saved u_hist')

# N-scaling for a=2, K0=5, kappa=1
Ns=[75,150,300,600]
scaling=[]
print('Running N-scaling...'); t0=time()
for Nn in Ns:
    tmax=60 if Nn==75 else (120 if Nn==150 else (240 if Nn==600 else 200))
    for s in range(12):
        seed=2000*Nn+s
        R0,t_lock=simulate(N=Nn,K0=5.0,a=2.0,kappa=1.0,tmax=tmax,seed=seed)
        u=0.5*2*5*(R0**2)*t_lock if np.isfinite(t_lock) else np.nan
        scaling.append({'N':Nn,'R0':R0,'t_lock':t_lock,'u':u})
print('scaling done in %.1fs'%(time()-t0))

byN=defaultdict(list)
for sc in scaling:
    byN[sc['N']].append(sc['t_lock'])
medians={Nnn:np.median([v for v in byN[Nnn] if np.isfinite(v)]) if any(np.isfinite(byN[Nnn])) else np.nan for Nnn in Ns}
print('median t_lock by N:', {k:round(v,2) for k,v in medians.items()})

fig,ax=plt.subplots(figsize=(6,4))
for Nn in Ns:
    vals=[sc for sc in scaling if sc['N']==Nn]
    ax.loglog([v['N'] for v in vals], [v['t_lock'] for v in vals], 'o', alpha=0.4, ms=4)
ax.loglog(Ns,[medians[n] for n in Ns],'-s',color='k',label='median')
nn=np.logspace(1.5,2.9,50)
ax.loglog(nn,0.015*nn**1.8,'--',color='r',label=r'$\sim N^{1.8}$')
ax.set_xlabel('N'); ax.set_ylabel('median lock time')
ax.set_title('N-scaling of lock time (a=2, K0=5, $\kappa$=1)')
ax.legend(); ax.grid(True,ls='--',alpha=0.3)
fig.tight_layout(); fig.savefig('../../shared_agora/artifacts/embassy_escape_law_N_scaling.png',dpi=150)
print('saved N_scaling')

metrics={'sweep_n_total':len(records),'sweep_n_locked':int(np.sum(np.isfinite(uvals))),
         'u_median':float(pct(uvals,50)),'u_p10':float(pct(uvals,10)),'u_p90':float(pct(uvals,90)),
         'median_t_by_N':{str(k):v for k,v in medians.items()}}
with open('../../shared_agora/artifacts/embassy_escape_law_metrics.json','w') as f:
    json.dump(metrics,f,indent=2)
print(metrics)
