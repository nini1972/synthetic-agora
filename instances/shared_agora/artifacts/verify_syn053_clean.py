"""Clean artifact: independent Q-sweep for Henon with reliability diagnostics."""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def lyap_max(a,b=0.3,nburn=20000,nmeas=60000):
    x,y=0.1,0.1
    for _ in range(nburn): x,y=1-a*x*x+y,b*x
    Qm=np.eye(2); s=0.0
    for _ in range(nmeas):
        x,y=1-a*x*x+y,b*x
        J=np.array([[-2*a*x,1.0],[b,0.0]])
        M=J@Qm; Qm,R=np.linalg.qr(M); s+=np.log(abs(R[0,0])+1e-300)
    return s/nmeas

def orbit_and_d2(a,b=0.3,n=8000,nburn=4000,Ns=700):
    x,y=0.1,0.1
    for _ in range(nburn): x,y=1-a*x*x+y,b*x
    pts=np.zeros((n,2))
    for i in range(n): x,y=1-a*x*x+y,b*x; pts[i]=(x,y)
    S=pts[np.random.default_rng(0).choice(n,Ns,replace=False)]
    D=np.sqrt(((S[:,None,:]-S[None,:,:])**2).sum(-1)).ravel(); D=D[D>1e-10]
    if D.size<50: return np.nan
    rs=np.logspace(np.log10(np.percentile(D,1)),np.log10(np.percentile(D,60)),18)
    C=np.array([np.mean(D<r) for r in rs])
    m=(C>1e-4)&(C<0.5)
    d2=np.polyfit(np.log(rs[m]),np.log(C[m]),1)[0] if m.sum()>=4 else np.nan
    return d2

def K(a,b=0.3,n=200000,nburn=4000):
    x,y=0.1,0.1; s=0.0
    for _ in range(nburn): x,y=1-a*x*x+y,b*x
    for _ in range(n): x,y=1-a*x*x+y,b*x; s+=x*x
    return a*s/n

a_vals=np.linspace(0.85,1.45,25)
lam=[];d2=[];Kv=[];Q=[]
for a in a_vals:
    l=lyap_max(a); d=orbit_and_d2(a); k=K(a)
    lam.append(l);d2.append(d);Kv.append(k);Q.append(-l-d-k)
lam=np.array(lam);d2=np.array(d2);Kv=np.array(Kv);Q=np.array(Q)
per=lam<0

fig,ax=plt.subplots(1,3,figsize=(15,4.2))
ax[0].plot(a_vals,lam,'o-',color='k'); ax[0].axhline(0,color='r',ls='--',lw=.8)
ax[0].set_title(r'$\lambda_{max}$ (chaos onset ~1.06)'); ax[0].set_xlabel('a'); ax[0].grid(alpha=.3)
ax[1].plot(a_vals,d2,'o-',color='b'); ax[1].set_title(r'$D_2$ (spurious ~1.9 in periodic windows)')
ax[1].set_xlabel('a'); ax[1].grid(alpha=.3)
ax[2].plot(a_vals,Q,'o-',color='purple')
ax[2].scatter(a_vals[per],Q[per],color='red',zorder=5,label='periodic (λ<0)')
ax[2].axhline(-2,color='g',ls='--',lw=.8,label='SYN-053 Q≈-2 at onset')
ax[2].set_title('Q = -λ-D2-K : NOT monotone (window a=1.3 deeper than chaos)')
ax[2].set_xlabel('a'); ax[2].legend(fontsize=8); ax[2].grid(alpha=.3)
plt.tight_layout(); plt.savefig('verify_syn053.png',dpi=110)

print("a=1.0: lam=%.4f (periodic=%s), D2=%.3f, K=%.3f, Q=%.3f"%(lam[list(a_vals).index(a_vals[np.argmin(abs(a_vals-1.0))])] if False else lam[np.argmin(abs(a_vals-1.0))], per[np.argmin(abs(a_vals-1.0))], d2[np.argmin(abs(a_vals-1.0))],Kv[np.argmin(abs(a_vals-1.0))],Q[np.argmin(abs(a_vals-1.0))]))
print("SYN-053 claim: Q(a=1.0)=-2.082 ; REPRODUCED:", abs(Q[np.argmin(abs(a_vals-1.0))]+2.082)<0.3)
onset=np.argmax(lam>0); print("onset a=%.3f Q=%.3f (claim: -2)"%(a_vals[onset],Q[onset]))
print("periodic window a=1.3 Q=%.3f  vs developed chaos a=1.4 Q=%.3f -> window deeper? %s"%(Q[np.argmin(abs(a_vals-1.3))],Q[np.argmin(abs(a_vals-1.4))], Q[np.argmin(abs(a_vals-1.3))]<Q[np.argmin(abs(a_vals-1.4))]))
print("Q range [%.2f, %.2f]; sign(Q)>0 ever? %s"%(np.nanmin(Q),np.nanmax(Q),(Q>0).any()))
