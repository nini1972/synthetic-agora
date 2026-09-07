import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
def lyap1(b, T=400.0, trans=300.0, dt=0.02, seed=3):
    s=np.random.default_rng(seed).uniform(-2,2,3); Q=np.eye(3); n=int(T/dt); nt=int(trans/dt); acc=0.0;cnt=0
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
bs=np.array([0.05,0.10,0.15,0.18,0.20,0.208186,0.22,0.24,0.26,0.28,0.30,0.32,0.35,0.40])
lam=np.array([lyap1(b) for b in bs])
print('=== CONVERGED lam1(b), trans=300,T=400 ===')
for b,l in zip(bs,lam): print('  b=%.4f lam1=%+.5f'%(b,l))
fig,ax=plt.subplots(figsize=(9,5.5))
ax.plot(bs,lam,'o-',color='#8e44ad',lw=2,label='Converged lam1(b)')
ax.axhline(0,color='black',lw=1)
ax.axvline(0.208186,color='#e74c3c',ls='--',lw=2,label='Dossier b_c=0.208186')
ax.axhspan(-0.01,0.01,color='#95a5a6',alpha=0.2,label='resolution floor |lam1|<0.01')
i0=np.argmin(np.abs(bs-0.208186))
ax.scatter([0.208186],[lam[i0]],color='#e67e22',zorder=5,s=90,label='lam1(b_c)=%+.4f'%lam[i0])
ax.set_xlabel('dissipation b'); ax.set_ylabel('max Lyapunov exponent lambda_1')
ax.set_title('Dossier #002 RED-TEAM (converged): Thomas lambda_1(b)\nLam1 SMALL ~0.01-0.03 near b_c -> magnitude CONFIRMED; transition gradual')
ax.grid(True,ls='--',alpha=0.4); ax.legend(fontsize=8,loc='lower left')
plt.tight_layout(); plt.savefig('verify_thomas_converged.png',dpi=150,bbox_inches='tight')
print('saved verify_thomas_converged.png')
