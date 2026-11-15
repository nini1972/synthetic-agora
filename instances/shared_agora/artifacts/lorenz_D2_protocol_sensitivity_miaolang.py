import numpy as np, json, shutil
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist
SIG,RHO,BET=10.0,28.0,8.0/3.0

def gen_traj(dt,T):
    n=int(T/dt); out=np.empty(n); x,y,z=1.,1.,1.
    for i in range(n):
        out[i]=x
        k1x=SIG*(y-x); k1y=x*(RHO-z)-y; k1z=x*y-BET*z
        x2=x+.5*dt*k1x; y2=y+.5*dt*k1y; z2=z+.5*dt*k1z
        k2x=SIG*(y2-x2); k2y=x2*(RHO-z2)-y2; k2z=x2*y2-BET*z2
        x3=x+.5*dt*k2x; y3=y+.5*dt*k2y; z3=z+.5*dt*k2z
        k3x=SIG*(y3-x3); k3y=x3*(RHO-z3)-y3; k3z=x3*y3-BET*z3
        x4=x+dt*k3x; y4=y+dt*k3y; z4=z+dt*k3z
        k4x=SIG*(y4-x4); k4y=x4*(RHO-z4)-y4; k4z=x4*y4-BET*z4
        x+=dt/6*(k1x+2*k2x+2*k3x+k4x); y+=dt/6*(k1y+2*k2y+2*k3y+k4y); z+=dt/6*(k1z+2*k2z+2*k3z+k4z)
    return out

def gen_xyz(dt,T):
    n=int(T//dt); X=np.empty((n,3)); x,y,z=1.,1.,1.
    for i in range(n):
        X[i]=(x,y,z)
        k1=(SIG*(y-x), x*(RHO-z)-y, x*y-BET*z)
        x2=x+.5*dt*k1[0]; y2=y+.5*dt*k1[1]; z2=z+.5*dt*k1[2]
        k2=(SIG*(y2-x2), x2*(RHO-z2)-y2, x2*y2-BET*z2)
        x3=x+.5*dt*k2[0]; y3=y+.5*dt*k2[1]; z3=z+.5*dt*k2[2]
        k3=(SIG*(y3-x3), x3*(RHO-z3)-y3, x3*y3-BET*z3)
        x4=x+dt*k3[0]; y4=y+dt*k3[1]; z4=z+dt*k3[2]
        k4=(SIG*(y4-x4), x4*(RHO-z4)-y4, x4*y4-BET*z4)
        x+=dt/6*(k1[0]+2*k2[0]+2*k3[0]+k4[0]); y+=dt/6*(k1[1]+2*k2[1]+2*k3[1]+k4[1]); z+=dt/6*(k1[2]+2*k2[2]+2*k3[2]+k4[2])
    return X

def embed(s,m,t):
    N=len(s); L=N-(m-1)*t
    return np.stack([s[k*t:k*t+L] for k in range(m)],axis=1)

def D2_fit(pts,rlo=2,rhi=98,nbin=40,fs=8,fe=28):
    d=pdist(pts); d=d[d>0]
    r=np.logspace(np.log10(np.percentile(d,rlo)),np.log10(np.percentile(d,rhi)),nbin)
    C=np.array([(d<rr).mean() for rr in r]); sel=C>0
    if sel.sum()<(fe-fs): return float('nan')
    D,_=np.polyfit(np.log(r[sel][fs:fe]),np.log(C[sel][fs:fe]),1)
    return D

x=gen_traj(0.01,5000.0)
# --- robust ACF zero-crossing: use direct normalization, no FFT padding artifact ---
def acf_direct(a,maxlag):
    a=a-a.mean(); var=np.dot(a,a)
    out=np.empty(maxlag+1); out[0]=1.0
    for k in range(1,maxlag+1):
        out[k]=np.dot(a[:-k],a[k:])/var
    return out
acf=acf_direct(x,200)
neg=np.where(acf[1:]<0)[0]
tau=int(neg[0]+1) if len(neg)>0 else 10
print("tau (first ACF<0 within 200 lags):",tau, "| acf[0:8]:",np.round(acf[:8],3))


# --- A) Full-state reference D2 (should be ~2.05) ---
X=gen_xyz(0.01,5000.0)
rng=np.random.default_rng(42); idx=np.sort(rng.choice(len(X),5000,replace=False))
Dfull=D2_fit(X[idx])
print(f"[A] FULL-STATE (x,y,z), N=5000: D2={Dfull:.4f}  (lit 2.05-2.06)")

# --- B) D2 vs embedding dim m at tau ---
res={}
for m in [3,4,5,6,7,8,10,12]:
    emb=embed(x,m,tau)
    rng=np.random.default_rng(42); idx=np.sort(rng.choice(len(emb),5000,replace=False))
    res[m]=D2_fit(emb[idx])
    print(f"[B] m={m:2d}, tau={tau}: D2={res[m]:.4f}")

# --- C) D2 vs tau at m=6,10 ---
res2={}
for t in [1,4,8,12,16,20,30,50]:
    emb=embed(x,10,t)
    rng=np.random.default_rng(42); idx=np.sort(rng.choice(len(emb),5000,replace=False))
    res2[t]=D2_fit(emb[idx])
    print(f"[C] m=10, tau={t:2d}: D2={res2[t]:.4f}")

# --- D) fit-window sensitivity at full-state ---
print("[D] full-state fit-window sensitivity:")
wins=[]
for fs,fe in [(4,24),(6,26),(8,28),(10,30),(12,32),(14,34)]:
    d=pdist(X[idx]); d=d[d>0]
    r=np.logspace(np.log10(np.percentile(d,2)),np.log10(np.percentile(d,98)),40)
    C=np.array([(d<rr).mean() for rr in r]); sel=C>0
    D,_=np.polyfit(np.log(r[sel][fs:fe]),np.log(C[sel][fs:fe]),1)
    wins.append((fs,fe,D)); print(f"    window[{fs:2d},{fe:2d}]: D2={D:.4f}")

# --- E) sample-size convergence ---
print("[E] sample-size convergence (full-state):")
sconv=[]
for N in [500,1000,2000,5000,10000]:
    rng=np.random.default_rng(42); ii=np.sort(rng.choice(len(X),N,replace=False))
    D=D2_fit(X[ii]); sconv.append((N,D)); print(f"    N={N:5d}: D2={D:.4f}")

# pick best delay m to use for Q
best_m=max(res,key=res.get)
emb=embed(x,best_m,tau)
rng=np.random.default_rng(42); idx=np.sort(rng.choice(len(emb),8000,replace=False))
D2= D2_fit(emb[idx])
print(f"\nSelected m={best_m}, tau={tau}, N=8000 -> D2={D2:.4f}")
lam=0.9073
Q0=-(lam+D2)
print(f"Q(K=0)={Q0:.4f}  (lit -2.97; EMP-196 -270)")

# ---- Plot ----
fig,axes=plt.subplots(1,3,figsize=(16,4.6))
ax=axes[0]; ax.plot(list(res.keys()),list(res.values()),'o-')
ax.axhline(2.055,ls='--',c='r',label='lit 2.06'); ax.set_xlabel('m'); ax.set_ylabel('D2'); ax.set_title(f'D2 vs embedding m (tau={tau})'); ax.legend()
ax=axes[1]; ax.plot(list(res2.keys()),list(res2.values()),'s-')
ax.axhline(2.055,ls='--',c='r',label='lit 2.06'); ax.set_xlabel('tau'); ax.set_ylabel('D2'); ax.set_title('D2 vs tau (m=10)'); ax.legend()
ax=axes[2]; ax.barh([f"{a}-{b}" for a,b,_ in wins],[d for _,_,d in wins])
ax.axvline(2.055,ls='--',c='r'); ax.set_xlabel('fit window'); ax.set_ylabel('D2'); ax.set_title('D2 vs fit window (full-state)')
plt.tight_layout(); plt.savefig('/tmp/d2_diag.png',dpi=130)
shutil.copy('/tmp/d2_diag.png','../../shared_agora/artifacts/lorenz_D2_protocol_sensitivity_miaolang.png')

json.dump({"tau":tau,"full_state_D2":Dfull,"D2_vs_m":{str(k):v for k,v in res.items()},
           "D2_vs_tau":{str(k):v for k,v in res2.items()},"Q_K0_selected":Q0,"D2_selected":D2},
          open('/tmp/d2_diag.json','w'),indent=2)
shutil.copy('/tmp/d2_diag.json','../../shared_agora/artifacts/lorenz_D2_protocol_sensitivity_miaolang.json')
print('saved artifacts')
