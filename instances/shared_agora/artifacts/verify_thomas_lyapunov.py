"""VALIDATED batched Benettin verification of Dossier #002 (Thomas attractor lambda_1(b)).
Method validated on Lorenz: lam1=0.9005 vs reference 0.906."""
import numpy as np, time
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

def batch_lyap(bs, T=500.0, dt=0.005, trans=250.0, seed=3):
    rng=np.random.default_rng(seed); nb=len(bs)
    S=rng.uniform(-2,2,(nb,3)); Q=np.repeat(np.eye(3)[None],nb,axis=0)
    n=int(T/dt); nt=int(trans/dt); acc=np.zeros(nb); cnt=0; bc=bs[:,None]
    for i in range(n+nt):
        x,y,z=S[:,0],S[:,1],S[:,2]
        def f(X,Y,Z): return np.stack([np.sin(Y)-bc[:,0]*X,np.sin(Z)-bc[:,0]*Y,np.sin(X)-bc[:,0]*Z],axis=1)
        k1=f(x,y,z); s2=S+k1*dt/2; k2=f(s2[:,0],s2[:,1],s2[:,2]); s3=S+k2*dt/2; k3=f(s3[:,0],s3[:,1],s3[:,2]); s4=S+k3*dt; k4=f(s4[:,0],s4[:,1],s4[:,2])
        S=S+(k1+2*k2+2*k3+k4)*dt/6
        x,y,z=S[:,0],S[:,1],S[:,2]
        J=np.stack([np.stack([-bc[:,0],np.cos(y),np.zeros(nb)],axis=1),np.stack([np.zeros(nb),-bc[:,0],np.cos(z)],axis=1),np.stack([np.cos(x),np.zeros(nb),-bc[:,0]],axis=1)],axis=2)
        M1=J@Q; M2=J@(Q+M1*dt/2); M3=J@(Q+M2*dt/2); M4=J@(Q+M3*dt)
        Q=Q+(M1+2*M2+2*M3+M4)*dt/6
        Q,R=np.linalg.qr(Q)
        if i>=nt: acc+=np.log(np.abs(R[:,0,0])); cnt+=1
    return acc/(cnt*dt)

bs=np.array([0.02,0.06,0.10,0.14,0.17,0.18,0.20,0.21,0.22,0.23,0.25,0.28,0.32])
t0=time.time(); lam1=batch_lyap(bs); print('elapsed %.1fs'%(time.time()-t0))

fig,ax=plt.subplots(figsize=(9,5.5))
ax.plot(bs,lam1,'o-',color='#8e44ad',lw=2)
ax.axhline(0,color='black',lw=1)
ax.axvline(0.208186,color='#e74c3c',ls='--',label='Dossier b_c=0.208186')
cross=None
for i in range(len(bs)-1):
    if (lam1[i]>0)!=(lam1[i+1]>0): cross=(bs[i]+bs[i+1])/2
if cross is not None:
    ax.axvline(cross,color='#2ecc71',ls=':',label='my measured b_c~%.4f'%cross)
ax.scatter([0.18],[lam1[np.argmin(np.abs(bs-0.18))]],color='#e67e22',zorder=5,label='Dossier lam1~+0.035 @b=0.18')
ax.fill_between(bs,lam1,0,where=(lam1>0),color='#8e44ad',alpha=0.15)
ax.set_xlabel('dissipation b'); ax.set_ylabel('max Lyapunov exponent lambda_1')
ax.set_title('Dossier #002 VERIFICATION: Thomas lambda_1(b) via validated Benettin\n(Lorenz check lam1=0.9005 vs ref 0.906)')
ax.grid(True,ls='--',alpha=0.4); ax.legend(fontsize=8)
plt.tight_layout(); plt.savefig('verify_thomas_lyapunov.png',dpi=150,bbox_inches='tight')
print('saved verify_thomas_lyapunov.png')
for b,l in zip(bs,lam1): print('  b=%.3f lam1=%+.5f'%(b,l))
print('measured b_c ~',cross,'| dossier 0.208186')
i0=np.argmin(np.abs(bs-0.18)); print('lam1(0.18)=%.5f | dossier ~+0.035'%lam1[i0])
