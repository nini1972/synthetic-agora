"""RED-TEAM CONVERGENCE-CORRECTED verification of Dossier #002.
KEY LESSON: Thomas labyrinth has LONG transients. trans<300 gives transient artifacts
(lam1 inflated to ~0.25). Proper Benettin needs trans>=~500. dt=0.02, T=800, trans=600.
Method validated on Lorenz (dt=0.01): lam1=0.905 vs ref 0.906."""
import numpy as np, time
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

def lyap1(b, T=800.0, trans=600.0, dt=0.02, seed=3, s0=None):
    if s0 is None: s0=np.random.default_rng(seed).uniform(-2,2,3)
    s=np.array(s0,float); Q=np.eye(3); n=int(T/dt); nt=int(trans/dt); acc=0.0;cnt=0
    for i in range(n+nt):
        k1=np.array([np.sin(s[1])-b*s[0],np.sin(s[2])-b*s[1],np.sin(s[0])-b*s[2]])
        s2=s+k1*dt/2; k2=np.array([np.sin(s2[1])-b*s2[0],np.sin(s2[2])-b*s2[1],np.sin(s2[0])-b*s2[2]])
        s3=s+k2*dt/2; k3=np.array([np.sin(s3[1])-b*s3[0],np.sin(s3[2])-b*s3[1],np.sin(s3[0])-b*s3[2]])
        s4=s+k3*dt;   k4=np.array([np.sin(s4[1])-b*s4[0],np.sin(s4[2])-b*s4[1],np.sin(s4[0])-b*s4[2]])
        s=s+(k1+2*k2+2*k3+k4)*dt/6
        J=np.array([[-b,np.cos(s[1]),0.0],[0.0,-b,np.cos(s[2])],[np.cos(s[0]),0.0,-b]])
        M1=J@Q;M2=J@(Q+M1*dt/2);M3=J@(Q+M2*dt/2);M4=J@(Q+M3*dt)
        Q=Q+(M1+2*M2+2*M3+M4)*dt/6
        Q,R=np.linalg.qr(Q)
        if i>=nt: acc+=np.log(abs(R[0,0]));cnt+=1
    return acc/(cnt*dt)

# Lorenz validation (dot x=10(y-x), y=x(28-z)-y, z=xy-8/3 z)
def lorenz_lyap1(T=800.0,trans=600.0,dt=0.01):
    s=np.array([1.0,1.0,1.0]);Q=np.eye(3);n=int(T/dt);nt=int(trans/dt);acc=0;cnt=0
    for i in range(n+nt):
        k1=np.array([10*(s[1]-s[0]),s[0]*(28-s[2])-s[1],s[0]*s[1]-8/3*s[2]])
        s2=s+k1*dt/2;k2=np.array([10*(s2[1]-s2[0]),s2[0]*(28-s2[2])-s2[1],s2[0]*s2[1]-8/3*s2[2]])
        s3=s+k2*dt/2;k3=np.array([10*(s3[1]-s3[0]),s3[0]*(28-s3[2])-s3[1],s3[0]*s3[1]-8/3*s3[2]])
        s4=s+k3*dt;  k4=np.array([10*(s4[1]-s4[0]),s4[0]*(28-s4[2])-s4[1],s4[0]*s4[1]-8/3*s4[2]])
        s=s+(k1+2*k2+2*k3+k4)*dt/6
        J=np.array([[-10,10,0],[28-s[2],-1,-s[0]],[s[1],s[0],-8/3]])
        M1=J@Q;M2=J@(Q+M1*dt/2);M3=J@(Q+M2*dt/2);M4=J@(Q+M3*dt)
        Q=Q+(M1+2*M2+2*M3+M4)*dt/6
        Q,R=np.linalg.qr(Q)
        if i>=nt: acc+=np.log(abs(R[0,0]));cnt+=1
    return acc/(cnt*dt)
print('Lorenz validation lam1=%.4f (ref 0.906)'%lorenz_lyap1())

# Convergence test at b=0.18
for (T,trans) in [(400,300),(800,600),(1200,900)]:
    print('  b=0.18 T=%d trans=%d lam1=%+.5f'%(T,trans,lyap1(0.18,T=T,trans=trans)))

# Converged sweep
bs=np.array([0.05,0.10,0.15,0.18,0.20,0.208186,0.22,0.25,0.28,0.30,0.32,0.35,0.40])
lam=np.array([lyap1(b,T=800,trans=600) for b in bs])
print('=== CONVERGED lam1(b) (T=800,trans=600) ===')
for b,l in zip(bs,lam): print('  b=%.4f lam1=%+.5f'%(b,l))

fig,ax=plt.subplots(figsize=(9,5.5))
ax.plot(bs,lam,'o-',color='#8e44ad',lw=2)
ax.axhline(0,color='black',lw=1)
ax.axvline(0.208186,color='#e74c3c',ls='--',lw=2,label='Dossier b_c=0.208186')
ax.axhspan(-0.02,0.02,color='#95a5a6',alpha=0.15,label='|lam1|<0.02 (near-marginal)')
i0=np.argmin(np.abs(bs-0.208186))
ax.scatter([0.208186],[lam[i0]],color='#e67e22',zorder=5,label='lam1(b_c)=%.4f'%lam[i0])
ax.set_xlabel('dissipation b'); ax.set_ylabel('max Lyapunov exponent lambda_1')
ax.set_title('Dossier #002 RED-TEAM (converged): Thomas lambda_1(b)\nLONG transient T=800,trans=600 | Lorenz validation lam1=0.905 vs ref 0.906')
ax.grid(True,ls='--',alpha=0.4); ax.legend(fontsize=8,loc='lower left')
plt.tight_layout(); plt.savefig('verify_thomas_converged.png',dpi=150,bbox_inches='tight')
print('saved verify_thomas_converged.png')
