"""
EMP-043: Thomas Attractor - Edge-of-Chaos Resolution (FINAL optimized)
"""
import numpy as np
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import json, warnings
warnings.filterwarnings('ignore')

def thomas_rhs(s, b):
    return np.array([np.sin(s[1])-b*s[0], np.sin(s[2])-b*s[1], np.sin(s[0])-b*s[2]])

def rk4(s, dt, b):
    k1=thomas_rhs(s,b); k2=thomas_rhs(s+.5*dt*k1,b); k3=thomas_rhs(s+.5*dt*k2,b); k4=thomas_rhs(s+dt*k3,b)
    return s+(dt/6)*(k1+2*k2+2*k3+k4)

def jacobian(s, b):
    return np.array([[-b,np.cos(s[1]),0],[0,-b,np.cos(s[2])],[np.cos(s[0]),0,-b]])

def lyapunov(b, dt=0.03, Tt=100, Tm=300, seed=42):
    rng = np.random.default_rng(seed)
    st = rng.standard_normal(3)*0.5; Q = np.eye(3); re = int(0.5/dt)
    for _ in range(int(Tt/dt)): st = rk4(st,dt,b)
    ls = np.zeros(3); nr = 0
    for i in range(int(Tm/dt)):
        st = rk4(st,dt,b); J = jacobian(st,b)
        for c in range(3): Q[:,c] += dt*(J@Q[:,c])
        if (i+1)%re==0:
            Qr,R = np.linalg.qr(Q)
            for k in range(3):
                if abs(R[k,k])>0: ls[k]+=np.log(abs(R[k,k]))
            Q=Qr; nr+=1
    T = nr*re*dt
    return ls/T if T>0 else np.zeros(3)

def symbolize(traj, n=8, c=0):
    x=traj[:,c]; p=np.linspace(0,100,n+1); b=np.percentile(x,p); b[0]=-np.inf; b[-1]=np.inf
    return np.clip(np.digitize(x,b)-1,0,n-1)

def block_ent(sym, k):
    N=len(sym)
    if N<k: return 0.0
    bl=[tuple(sym[i:i+k]) for i in range(N-k+1)]
    ct=Counter(bl); t=len(bl)
    return -sum((c/t)*np.log2(c/t) for c in ct.values() if c>0)

def lz78(sym):
    s=''.join(str(int(c)) for c in sym); i,w,comp,d=0,'',0,set()
    while i<len(s):
        wc=w+s[i]
        if wc in d: w=wc
        else: comp+=1; d.add(wc); w=s[i]
        i+=1
    return comp

def pe(sym, order=4):
    import math
    n=len(sym)
    if n<order: return 0.0
    pats=[tuple(np.argsort([sym[i+k] for k in range(order)])) for i in range(n-order+1)]
    ct=Counter(pats); t=len(pats); mH=np.log2(math.factorial(order))
    H=-sum((c/t)*np.log2(c/t) for c in ct.values() if c>0)
    return H/mH if mH>0 else 0

# ── Parameters ──
dt=0.05; Tt=200; Tm=200  # 4000 symbolic points - enough for 8-block entropy
bs=np.unique(np.round(np.concatenate([np.linspace(0.05,0.15,3),np.linspace(0.15,0.27,7),np.linspace(0.27,0.40,3)]),3))

res=dict(b=[],lam1=[],lam1_std=[],lam1_spec=[],H1=[],H2=[],H4=[],H6=[],H8=[],lz_raw=[],lz_norm=[],pe=[])

print("EMP-043: Thomas EoC Resolution")
for idx,b in enumerate(bs):
    sp1=lyapunov(b,seed=42); sp2=lyapunov(b,seed=123)
    lam1v=[sp1[0],sp2[0]]; ms=np.mean([sp1,sp2],axis=0)
    
    rng=np.random.default_rng(7); st=rng.standard_normal(3)*0.5
    for _ in range(int(Tt/dt)): st=rk4(st,dt,b)
    traj=np.zeros((int(Tm/dt),3))
    for j in range(len(traj)): st=rk4(st,dt,b); traj[j]=st
    sym=symbolize(traj)
    
    lz=lz78(sym); n=len(sym); lzn=lz/(n/np.log2(n)) if n>1 else 0
    
    res['b'].append(float(b)); res['lam1'].append(float(ms[0])); res['lam1_std'].append(float(np.std(lam1v)))
    res['lam1_spec'].append(ms.tolist())
    for k,key in [(1,'H1'),(2,'H2'),(4,'H4'),(6,'H6'),(8,'H8')]:
        res[key].append(block_ent(sym,k))
    res['lz_raw'].append(int(lz)); res['lz_norm'].append(float(lzn)); res['pe'].append(pe(sym))
    print(f"  b={b:.3f} λ1={ms[0]:.4f} LZ_norm={lzn:.4f} PE={pe(sym):.4f} H4={block_ent(sym,4):.3f}")

with open('thomas_eoc_results_v3.json','w') as f: json.dump(res,f)

b_arr=np.array(res['b']); lam_arr=np.array(res['lam1']); lz_arr=np.array(res['lz_norm'])
pe_arr=np.array(res['pe']); H4_arr=np.array(res['H4']); std_arr=np.array(res['lam1_std'])

# ── Find edge-of-chaos ──
# Sign change: lambda1 goes from positive to negative
for i in range(len(lam_arr)-1):
    if lam_arr[i]>0 and lam_arr[i+1]<0:
        # Linear interpolation
        bc = b_arr[i] + (b_arr[i+1]-b_arr[i]) * lam_arr[i]/(lam_arr[i]-lam_arr[i+1])
        print(f"\nEdge-of-chaos (lambda1=0 crossing): b_c = {bc:.4f}")
        break

print(f"\nLMC peak b = {b_arr[np.argmax(lz_arr)]:.3f}")
print(f"PE peak b = {b_arr[np.argmax(pe_arr)]:.3f}")
print(f"H(4) peak b = {b_arr[np.argmax(H4_arr)]:.3f}")

# ── Visualization ──
fig=plt.figure(figsize=(18,28)); gs=GridSpec(6,1,figure=fig,hspace=0.35)

ax1=fig.add_subplot(gs[0])
ax1.fill_between(b_arr,lam_arr-std_arr,lam_arr+std_arr,alpha=0.3,color='gray')
ax1.plot(b_arr,lam_arr,'ko-',ms=4,lw=1.5,label='lambda1 (mean ± std, 2 seeds)')
ax1.axhline(0,color='red',ls='--',lw=2)
ax1.axvline(0.208,color='green',ls=':',lw=2,label='b_c=0.208 (DOSSIER_002)')
for i in range(len(b_arr)-1):
    c='red' if lam_arr[i]>0.01 else ('blue' if lam_arr[i]<-0.01 else 'green')
    ax1.axvspan(b_arr[i],b_arr[i+1],alpha=0.08,color=c)
ax1.set_xlabel('b'); ax1.set_ylabel('lambda_1')
ax1.set_title('Panel 1: Largest Lyapunov Exponent'); ax1.legend()

ax2=fig.add_subplot(gs[1])
lams=np.array(res['lam1_spec'])
for k in range(3): ax2.plot(b_arr,lams[:,k],'o-',ms=3,lw=1,label=f'lambda_{k+1}')
ax2.axhline(0,color='red',ls='--',alpha=0.5); ax2.axvline(0.208,color='green',ls=':',alpha=0.5)
ax2.set_xlabel('b'); ax2.set_ylabel('lambda_k'); ax2.set_title('Panel 2: Lyapunov Spectrum'); ax2.legend()

ax3=fig.add_subplot(gs[2])
for key,lbl,col in [('H1','H(1)','#e74c3c'),('H2','H(2)','#e67e22'),('H4','H(4)','#27ae60'),('H6','H(6)','#2980b9'),('H8','H(8)','#8e44ad')]:
    ax3.plot(b_arr,np.array(res[key]),'o-',color=col,ms=3,lw=1.5,label=lbl)
ax3.axvline(0.208,color='green',ls=':',lw=2)
ax3.set_xlabel('b'); ax3.set_ylabel('Block Entropy (bits)'); ax3.set_title('Panel 3: Block Entropy'); ax3.legend(ncol=3,fontsize=9)

ax4=fig.add_subplot(gs[3])
ax4.plot(b_arr,lz_arr,'o-',color='#e74c3c',ms=4,lw=1.5,label='Normalized LZ78')
ax4.axvline(0.208,color='green',ls=':',lw=2)
ax4.set_xlabel('b'); ax4.set_ylabel('LZ norm'); ax4.set_title('Panel 4: Lempel-Ziv Complexity'); ax4.legend()

ax5=fig.add_subplot(gs[4])
ax5.plot(b_arr,pe_arr,'o-',color='#8e44ad',ms=4,lw=1.5,label='Perm Entropy')
ax5.axvline(0.208,color='green',ls=':',lw=2)
ax5.set_xlabel('b'); ax5.set_ylabel('Perm Entropy'); ax5.set_title('Panel 5: Permutation Entropy'); ax5.legend()

ax6=fig.add_subplot(gs[5])
nm=lambda x:(x-x.min())/(x.max()-x.min()+1e-10)
ax6.plot(b_arr,nm(lam_arr),'k-',lw=2.5,label='lambda1')
ax6.plot(b_arr,nm(lz_arr),'r-',lw=2.5,label='LZ78')
ax6.plot(b_arr,nm(pe_arr),color='purple',lw=2.5,label='Perm Entropy')
ax6.plot(b_arr,nm(H4_arr),'g-',lw=2.5,label='H(4)')
ax6.axvline(0.208,color='green',ls=':',lw=2)
ax6.set_xlabel('b'); ax6.set_ylabel('Normalized'); ax6.set_title('Panel 6: All Metrics Overlaid'); ax6.legend()

plt.suptitle('EMP-043: Thomas Attractor Edge-of-Chaos Resolution\nResolving DOSSIER_002 vs EMP-035/EMP-040',fontsize=16,y=0.98)
plt.savefig('thomas_eoc_resolution_v3.png',dpi=150,bbox_inches='tight')
print("\nSaved: thomas_eoc_resolution_v3.png")