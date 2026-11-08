"""Evidence figure: three contradictory reconstructions of DOSSIER-170 / HYP-135."""
import numpy as np, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

WM,Wm=2.0,0.1; h0=0.3; s=0.9; g=0.25; c=0.05; hb=0.5
rhos=np.linspace(-0.9,0.9,37); T=3000
def max_eig(a,b,cc,d):
    tr=a+d; det=a*d-b*cc; disc=max(tr*tr-4*det,0.0)
    return 0.5*(tr+math.sqrt(disc))

# (A) faithful 2x2 GME matrix: P-win if lyap_P>lyap_S
def matrix_map():
    res=np.zeros_like(rhos)
    for i,r in enumerate(rhos):
        rng=np.random.default_rng(0); psw=0.5*(1-r)
        e=np.zeros(T,dtype=int); cur=0
        for t in range(1,T):
            if rng.random()<psw: cur=1-cur
            e[t]=cur
        lyP=lyS=0.0; pe=e[0]
        for t in range(T):
            et=e[t]; Wt=WM if et==0 else Wm; m=1 if pe==1 else 0
            hP=min(max(h0+hb*m,0.0),1.0)
            lyP+=math.log(max(max_eig((1-hP)*Wt*(1-c),g,hP*Wt*(1-c),s*(1-g)),1e-12))
            lyS+=math.log(max(max_eig((1-h0)*Wt,g,h0*Wt,s*(1-g)),1e-12))
            pe=et
        res[i]=(lyP-lyS)/T
    return res

# (B) direct temporal recurrence: P-win if final P-fraction>0.5
def temporal_map():
    rng=np.random.default_rng(0)
    res=np.zeros_like(rhos)
    for i,r in enumerate(rhos):
        psw=0.5*(1-r); e=np.zeros(T,dtype=int); cur=0
        for t in range(1,T):
            if rng.random()<psw: cur=1-cur
            e[t]=cur
        Pw=Pd=Sw=Sd=0.5; prev=e[0]
        for t in range(T):
            et=e[t]; Wt=WM if et==0 else Wm; m=1 if prev==1 else 0
            hP=min(max(h0+hb*m,0.0),1.0)
            nPw=(1-hP)*Wt*(1-c)*Pw+g*Pd; nPd=hP*Wt*(1-c)*Pw+s*(1-g)*Pd
            nSw=(1-h0)*Wt*Sw+g*Sd; nSd=h0*Wt*Sw+s*(1-g)*Sd
            tot=nPw+nPd+nSw+nSd
            Pw=nPw/tot; Pd=nPd/tot; Sw=nSw/tot; Sd=nSd/tot; prev=et
        res[i]=Pw+Pd
    return res

mD=matrix_map(); tD=temporal_map()
fig,ax=plt.subplots(1,2,figsize=(11,4))
ax[0].plot(rhos,mD,'k-',lw=2); ax[0].axhline(0,color='r',ls='--')
ax[0].set_title('(A) Faithful 2x2 GME matrix \\nDelta=lyap_P-lyap_S (c=0.05,hb=0.5)')
ax[0].set_xlabel('rho'); ax[0].set_ylabel('invasion exponent'); ax[0].set_ylim(-0.25,0.05)
ax[0].annotate('S wins everywhere\\n(Delta<0)',xy=(0,-0.1),ha='center',color='r')
ax[1].plot(rhos,tD*100,'b-',lw=2); ax[1].axhline(50,color='r',ls='--')
ax[1].set_title('(B) Direct temporal recurrence\\nfinal P-population % (c=0.05,hb=0.5)')
ax[1].set_xlabel('rho'); ax[1].set_ylabel('P population %'); ax[1].set_ylim(0,105)
ax[1].annotate('P wins at rho<0',xy=(-0.6,90),color='b'); ax[1].annotate('S wins at rho>0',xy=(0.4,10),color='r')
fig.suptitle('DOSSIER-170/HYP-135 reconstructions CONTRADICT each other & the dossier (P wins 88-95% everywhere)',fontsize=10)
plt.tight_layout(); plt.savefig('../../shared_agora/artifacts/hyp135_contradiction.png',dpi=130)
print('saved. matrix Delta mean=%.4f (all<0? %s)'%(mD.mean(),(mD<0).all()))
print('temporal P%% at rho=-0.6,0,0.6:',[round(float(tD[rhos==r][0]*100),1) for r in [-0.6,0.0,0.6]])
