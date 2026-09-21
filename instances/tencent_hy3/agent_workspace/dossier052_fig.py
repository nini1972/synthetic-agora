import numpy as np, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sim(N, alpha, K0, T=40.0, dt=0.02, mode='rand', seed=0, g=1.0):
    rg = np.random.default_rng(seed)
    om = rg.uniform(-g, g, N)
    th = rg.uniform(0, 2*np.pi, N) if mode=='rand' else rg.uniform(-0.3, 0.3, N)
    ns = int(round(T/dt)); ms = int(round(5/dt))
    for _ in range(ns):
        z = np.mean(np.exp(1j*th)); K = K0*(abs(z)**alpha)
        th += (om + K*np.imag(np.exp(-1j*th)*z))*dt
    Rs=[]
    for _ in range(ms):
        z = np.mean(np.exp(1j*th)); K = K0*(abs(z)**alpha)
        th += (om + K*np.imag(np.exp(-1j*th)*z))*dt; Rs.append(abs(z))
    return float(np.mean(Rs))

# ---- seed sensitivity at alpha in {1.0,1.1,1.2}, K0=5, N=200, 8 seeds ----
sens={}
for a in [1.0,1.1,1.2]:
    vals=[sim(200,a,5.0,mode='rand',seed=s) for s in range(8)]
    sens[f'a{a}']=vals
    print('sens a',a,vals,'mean',round(np.mean(vals),3))
json.dump(sens, open('dossier052_sens.json','w'))

# ---- load main sweep ----
D=json.load(open('dossier052_repl.json')); A=D['alphas']; K=D['K0s']; R=D['res']
Dn=json.load(open('dossier052_nscale.json'))

# estimate Kc^acc(alpha) = first K0 where random R>0.5
def kcacc(a):
    rr=R[f'a{a}_rand']; ks=[k for k,r in zip(K,rr) if r>0.5]
    return ks[0] if ks else None
kcs=[(a,kcacc(a)) for a in A]
xs=[]; ys=[]
for a,k in kcs:
    if k is not None: xs.append(a); ys.append(k)

fig,ax=plt.subplots(1,3,figsize=(16,4.5))
for a in A:
    ax[0].plot(K,R[f'a{a}_rand'],'-o',label=f'a={a}',ms=3)
    ax[0].plot(K,R[f'a{a}_seed'],'--',alpha=0.6)
ax[0].axhline(0.5,color='k',lw=0.8,ls=':'); ax[0].set_xlabel('K0'); ax[0].set_ylabel('R_ss')
ax[0].set_title('Random (solid) vs Seeded (dashed) init'); ax[0].legend(fontsize=7,ncol=2)

ax[1].plot(xs,ys,'o-')
ax[1].set_xlabel('feedback exponent alpha'); ax[1].set_ylabel('Kc^acc (from-disorder)')
ax[1].set_title('From-disorder threshold rises SMOOTHLY\n(no sharp break at alpha=1)')

# N scaling heatmap: alpha in {0.0,0.9}, N x K0
Ns=[100,200,400,800]
im=[]
for a in [0.0,0.9]:
    row=[Dn[f'a{a}_N{N}'][i] for N in Ns for i in range(len(K))]
    im.append(np.array(row).reshape(len(Ns),len(K)))
ax[2].imshow(np.vstack(im),aspect='auto',vmin=0,vmax=1,cmap='viridis',
             extent=[K[0],K[-1],1.5,0.5])
ax[2].set_yticks([0.5,1.5]); ax[2].set_yticklabels(['a=0.9','a=0.0'])
ax[2].set_xlabel('K0'); ax[2].set_title('N-scaling: a=0 robust, a=0.9 locks vanish at N=800')
ax[2].axvline(1.5,color='w',ls=':',lw=0.8)
fig.tight_layout(); fig.savefig('dossier052_fig.png',dpi=130)
print('Kc^acc:',kcs)
