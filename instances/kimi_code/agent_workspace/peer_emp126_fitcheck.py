import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# EMP-109 reported data (World C replication)
Ns=np.array([100.0,200.0,400.0,800.0,1600.0,3200.0,6400.0])
edges=np.array([2.35,2.10,1.85,1.85,1.55,1.55,1.55])

def pinned(N,c,p):
    return 1.0+c*N**(-p)
def free(N,a,c,p):
    return a+c*N**(-p)

def rss(y,yp):
    return np.sum((y-yp)**2)
def aicc(rss,k,n):
    return n*np.log(max(rss/n,1e-12))+2*k+2*k*(k+1)/max(n-k-1,1e-6)

pp,pcov=curve_fit(pinned,Ns,edges,p0=[5,0.4],maxfev=20000)
cp,ppar=pp
# free fit with a lower bound maybe for stability
pf,_=curve_fit(free,Ns,edges,p0=[1.3,8,0.5],bounds=([0,0,0],[5,50,2]),maxfev=20000)
af,cf,pfpar=pf

print('Pinned fit: 1 + %.4f * N^(-%.4f)'%(cp,ppar))
print('Free fit:   %.4f + %.4f * N^(-%.4f)'%(af,cf,pfpar))
print('RSS pinned = %.6f, free = %.6f'%(rss(edges,pinned(Ns,*pp)), rss(edges,free(Ns,*pf))))
print('RMS pinned = %.6f, free = %.6f'%(np.sqrt(rss(edges,pinned(Ns,*pp))/len(Ns)), np.sqrt(rss(edges,free(Ns,*pf))/len(Ns))))
print('AICc pinned = %.4f, free = %.4f'%(aicc(rss(edges,pinned(Ns,*pp)),2,7), aicc(rss(edges,free(Ns,*pf)),3,7)))

for Ntest in [2000,5000,10000,100000]:
    print('N=%6i -> pinned %.3f, free %.3f'%(Ntest, pinned(Ntest,*pp), free(Ntest,*pf)))

fig,ax=plt.subplots(figsize=(7,4))
nplot=np.logspace(2,4.2,200)
ax.semilogx(Ns,edges,'ko',label='EMP-109 upper edges')
ax.semilogx(nplot,pinned(nplot,*pp),'--',label=f'pinned: 1+{cp:.2f}N^(-{ppar:.3f})')
ax.semilogx(nplot,free(nplot,*pf),'-',label=f'free: {af:.3f}+{cf:.2f}N^(-{pfpar:.3f})')
ax.axhline(1.0,color='r',ls=':',label='alpha*=1')
ax.set_xlabel('N'); ax.set_ylabel('alpha_c')
ax.set_title('EMP-126 replication: pinned vs free intercept fit (EMP-109 data)')
ax.legend(); ax.grid(True,ls='--',alpha=0.4)
fig.tight_layout()
fig.savefig('../../shared_agora/artifacts/peer_emp126_fitcheck.png',dpi=150)
print('saved peer_emp126_fitcheck.png')
