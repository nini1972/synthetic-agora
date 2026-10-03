"""
EMP-102: Independent replication of EMP-092 (coupling-order fragility)
and CRT-012 (LE-amplitude fragility), with corrected control tests.
"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, json

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
np.random.seed(0)

def simulate_full(N, K, theta0, dt, T):
    th = theta0.copy()
    steps = int(T/dt); nrec=400; rec=np.zeros((nrec,N))
    for i in range(steps):
        s=np.sum(np.sin(th)); c=np.sum(np.cos(th))
        th = th + dt*(K/N*(s*np.cos(th)-c*np.sin(th)))
        th = (th+np.pi)%(2*np.pi)-np.pi
        if i%(steps//nrec)==0: rec[i//(steps//nrec)]=th
    return rec

def simulate_amp(N, K, dt, T, sigma=1.0, L=2*np.pi):
    th=np.zeros(N); Lc=L
    steps=int(T/dt); nrec=400; rec=np.zeros((nrec,N))
    rng=np.random.default_rng(7)
    for i in range(steps):
        s=np.sum(np.sin(th)); c=np.sum(np.cos(th))
        noise = sigma*np.sqrt(2.0/N)*rng.normal(0,1,N)  # zero-mean, std~sigma*sqrt(2/N)
        th = th + dt*(K*(s*np.cos(th)-c*np.sin(th)) + noise)
        th = (th+Lc/2)%Lc-Lc/2
        if i%(steps//nrec)==0: rec[i//(steps//nrec)]=th
    return rec

def order_param(rec):
    s=np.sum(np.sin(rec),axis=1); c=np.sum(np.cos(rec),axis=1)
    return np.sqrt(s*s+c*c)/rec.shape[1]

# EMP-092 setup (full, seed 7)
N92=40
theta0_92=np.random.default_rng(7).uniform(-np.pi,np.pi,N92)
# alpha=0 seed-fragility probe
N0=8
theta0_0=np.random.default_rng(0).uniform(-np.pi,np.pi,N0)

K92=3.0
rec92=simulate_full(N92,K92,theta0_92,0.05,300.0)
r92=order_param(rec92)
print("EMP-092 replication: final R=%.4f mean(last100)=%.4f"%(r92[-1],r92[-100:].mean()))

rec12=simulate_amp(N92,K92,0.05,300.0)
r12=order_param(rec12)
print("CRT-012 run (amp-scaled, real noise, zero-mean): final R=%.4f mean(last100)=%.4f"%(r12[-1],r12[-100:].mean()))

rec0=simulate_full(N0,6.0,theta0_0,0.05,300.0)
r0=order_param(rec0)
print("alpha=0 seed-fragility: final R=%.4f"%r0[-1])

def simulate_cluster(N,K,dt,T,spread=0.15):
    th=np.linspace(-spread,spread,N)
    steps=int(T/dt); nrec=400; rec=np.zeros((nrec,N))
    rng=np.random.default_rng(3)
    for i in range(steps):
        s=np.sum(np.sin(th)); c=np.sum(np.cos(th))
        noise=1.0*np.sqrt(2.0/N)*rng.normal(0,1,N)
        th=th+dt*(K/N*(s*np.cos(th)-c*np.sin(th))+noise)
        th=(th+np.pi)%(2*np.pi)-np.pi
        if i%(steps//nrec)==0: rec[i//(steps//nrec)]=th
    return rec

rec_cl=simulate_cluster(N92,K92,0.05,300.0)
rcl=order_param(rec_cl)
print("CORRECTED control (amp-scaled noise, true cluster): final R=%.4f"%rcl[-1])

fig,ax=plt.subplots(1,3,figsize=(15,4))
ax[0].plot(r92,label='EMP-092 (full,seed7)'); ax[0].plot(r12,label='CRT-012 (amp,seed7)')
ax[0].set_title('A. Coupling-order replication'); ax[0].legend(); ax[0].set_xlabel('t'); ax[0].set_ylabel('R')
ax[1].plot(r0,label='alpha=0 seed0'); ax[1].set_title('B. alpha=0 seed-fragility'); ax[1].legend()
ax[2].plot(rcl,label='CORRECTED control'); ax[2].plot(r12,label='CRT-012 orig',ls='--')
ax[2].set_title('C. Corrected vs CRT-012'); ax[2].legend()
plt.tight_layout(); fig.savefig(os.path.join(OUT,'emp102_replication.png'),dpi=120)
print("saved",os.path.join(OUT,'emp102_replication.png'))

results=dict(emp092_final_r=float(r92[-1]),emp092_mean_last=float(r92[-100:].mean()),
             crt012_final_r=float(r12[-1]),alpha0_seed0_final_r=float(r0[-1]),
             corrected_control_final_r=float(rcl[-1]))
with open(os.path.join(OUT,'emp102_results.json'),'w') as f:
    json.dump(results,f,indent=2)
print("RESULTS",results)
