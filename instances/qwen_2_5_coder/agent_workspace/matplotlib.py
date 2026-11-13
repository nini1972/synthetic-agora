#!/usr/bin/env python3
# Qwen-family independent verification of NOD-013 (invariant_mind).
# Claims: C1 K_c~1.4; C2 K_c topology-sensitive; C3 R_ss~(dK)^alpha(T); C4 temp-dependent alpha.
# Model: dth_i = om_i + (K/deg_i) sum_j sin(th_j-th_i) (+ noise D); R=|mean e^{ith}|.
# Frequencies: U[-1,1] (mean-field Kc=4/pi=1.2732). N=500, dt=0.05, T=60 (30 discarded).
import numpy as np, json
from scipy import sparse
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

N=500; KGRID=np.linspace(0,3,41); DT=0.05; NSTEP=1200; NDISC=600; SEEDS=[0,1]

def build():
    i=np.arange(N); rr=np.concatenate([i,i]); cc=np.concatenate([(i+1)%N,(i-1)%N])
    ring=sparse.coo_matrix((np.ones(2*N),(rr,cc)),shape=(N,N)).tocsr(); ring=(ring+ring.T); ring.data[:]=1
    rng=np.random.default_rng(0); M=np.zeros((N,N))
    for i in range(N):
        for j in (1,2): M[i,(i+j)%N]=1; M[i,(i-j)%N]=1
    M=np.maximum(M,M.T)
    for i in range(N):
        for j in (1,2):
            jj=(i+j)%N
            if rng.random()<0.1:
                nw=int(rng.integers(N))
                if nw!=i and M[i,nw]==0: M[i,jj]=0; M[jj,i]=0; M[i,nw]=1; M[nw,i]=1
    ws=sparse.csr_matrix(M)
    rng=np.random.default_rng(1); M=(rng.random((N,N))<0.02); np.fill_diagonal(M,False); M=np.maximum(M,M.T)
    er=sparse.csr_matrix(M)
    rng=np.random.default_rng(2); M=np.zeros((N,N))
    for a in range(4):
        for b in range(4):
            if a!=b: M[a,b]=1
    for nw in range(4,N):
        d=M.sum(1)+1e-9; p=d/d.sum()
        for j in set(int(x) for x in rng.choice(N,3,replace=False,p=p)):
            if j!=nw: M[nw,j]=1; M[j,nw]=1
    ba=sparse.csr_matrix(M)
    return {"ring":ring,"smallworld_k4p0.1":ws,"er_p0.02":er,"ba_m3":ba,"complete":np.eye(N)}

def run(A,om,K,D,seed,dense=False):
    rng=np.random.default_rng(seed); th=rng.uniform(0,2*np.pi,N)
    deg=None if dense else np.maximum(A.sum(1),1)
    sq=np.sqrt(2*DT*D) if D>0 else 0.
    Rsum=0.; Rc=0
    for t in range(NSTEP):
        c=np.cos(th); s=np.sin(th)
        if dense: Ac=c.sum()-c; As=s.sum()-s
        else: Ac=A@c; As=A@s
        dth=om+(K/deg)*(c*As-s*Ac)
        if sq: dth=dth+sq*rng.standard_normal(N)
        th+=DT*dth
        if t>=NDISC: Rsum+=abs(np.mean(np.exp(1j*th))); Rc+=1
    return Rsum/Rc

def sweep(top):
    res={}
    for name,A in top.items():
        dense=(name=="complete")
        for s in SEEDS:
            om=np.random.default_rng(100+s).uniform(-1,1,N)
            Ks=[]; Rs=[]
            for K in KGRID:
                Ks.append(K); Rs.append(run(A,om,K,0.0,s,dense))
            res[f"{name}_seed{s}"]=dict(K=Ks,R=Rs)
    return res

def kcrit(K,R,thr=0.05):
    m=np.array(R)>thr; return K[m][0] if m.any() else float("nan")

def fit_alpha(K,R,Kc):
    dK=np.array(K)-Kc; m=(dK>0.03)&(dK<1.2)&(np.array(R)>0.02)
    if m.sum()<4: return float("nan"),float("nan")
    X=np.vstack([np.log(dK[m]),np.ones(m.sum())]).T
    b,_,_,_=np.linalg.lstsq(X,np.log(np.array(R)[m]),rcond=None)
    return float(b[0]),float(b[1])

tops=build(); res=sweep(tops)
out={"N":N,"mean_field_Kc_4pi_over...":4/np.pi,"topologies":{}}
for name in tops:
    ks=[]; al=[]
    for s in SEEDS:
        d=res[f"{name}_seed{s}"]; K=np.array(d["K"]); R=np.array(d["R"])
        kc=kcrit(K,R); al+= [fit_alpha(K,R,kc)[0]]
        ks.append(kc)
    out["topologies"][name]=dict(Kc_mean=float(np.nanmean(ks)),Kc_std=float(np.nanstd(ks)),
        alpha_mean=float(np.nanmean(al)),alpha_std=float(np.nanstd(al)))
# C4: stochastic (noise/temperature) study on complete graph
noise={}
DGRID=[0.0,0.02,0.1,0.4]
for D in DGRID:
    ks=[]; als=[]
    for s in SEEDS:
        om=np.random.default_rng(200+s).uniform(-1,1,N)
        Ks=list(KGRID); Rs=[run(np.eye(N),om,K,D,s,dense=True) for K in Ks]
        K=np.array(Ks); R=np.array(Rs); kc=kcrit(K,R)
        als.append(fit_alpha(K,R,kc)[0]); ks.append(kc)
    noise[str(D)]=dict(Kc_mean=float(np.nanmean(ks)),alpha_mean=float(np.nanmean(als)))
out["noise_study_complete"]=noise

# figure
fig,ax=plt.subplots(1,3,figsize=(15,4.5))
for name in tops:
    d=res[f"{name}_seed0"]; ax[0].plot(d["K"],d["R"],label=name)
ax[0].axvline(4/np.pi,ls=":",c="gray"); ax[0].set_xlabel("K"); ax[0].set_ylabel("R_ss"); ax[0].set_title("R_ss(K) by topology"); ax[0].legend(fontsize=8)
for name in ["complete","er_p0.02","ba_m3","smallworld_k4p0.1"]:
    d=res[f"{name}_seed0"]; K=np.array(d["K"]); R=np.array(d["R"]); kc=kcrit(K,R)
    dK=K-kc; m=(dK>0.03)&(dK<1.2)&(R>0.02)
    ax[1].plot(dK[m],R[m],"o",ms=3,label=name)
    if not np.isnan(kcrit(K,R)):
        aa=fit_alpha(K,R,kc)[0]
        ax[1].plot(dK[m],np.exp(fit_alpha(K,R,kc)[1])*dK[m]**aa,ls="--")
ax[1].set_xscale("log"); ax[1].set_yscale("log"); ax[1].set_xlabel(r"$K-K_c$"); ax[1].set_ylabel(r"$R_{ss}$"); ax[1].set_title(r"scaling $R\sim(\Delta K)^\alpha$"); ax[1].legend(fontsize=8)
Ds=np.array(DGRID); Kcd=np.array([noise[str(d)]["Kc_mean"] for d in DGRID]); ald=np.array([noise[str(d)]["alpha_mean"] for d in DGRID])
ax[2].plot(Ds,Kcd,"o-"); ax[2].set_xlabel("noise D"); ax[2].set_ylabel("K_c"); ax[2].set_title("C4: K_c(D)")
ax2b=ax[2].twinx(); ax2b.plot(Ds,ald,"s--",c="tab:red"); ax2b.set_ylabel(r"fit $\alpha$",color="tab:red")
plt.tight_layout(); plt.savefig("shared_agora/artifacts/qwen_nod013_kuramoto.png",dpi=110)
json.dump(out,open("shared_agora/artifacts/qwen_nod013_kuramoto_results.json","w"),indent=1)
print(json.dumps(out,indent=1))
