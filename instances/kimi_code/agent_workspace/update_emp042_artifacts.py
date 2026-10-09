import json, numpy as np
from scipy.integrate import quad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# load existing data
with open('../../shared_agora/artifacts/emp042_defense.json','r') as f:
    data=json.load(f)

def h_scalar(x):
    if x <= 0.0: return 0.0
    val,_=quad(lambda u: np.exp(-u*u/2)/np.sqrt(2*np.pi)*np.sqrt(max(0.0,1-(u/x)**2)), -x, x, limit=80)
    return val

xs=np.linspace(0.05,8.0,1600)
hs=np.array([h_scalar(x) for x in xs])
sigma=1.0
new_mean={}
for alpha in [1.0,2.0]:
    K0=sigma*xs/(hs**alpha)
    imin=np.argmin(K0)
    new_mean[str(alpha)]={'K0_c':float(K0[imin]),'x_c':float(xs[imin]),'R_c':float(hs[imin])}
print('Corrected mean-field:', new_mean)
data['mean_field_corrected']=new_mean

# Save updated JSON
with open('../../shared_agora/artifacts/emp042_defense.json','w') as f:
    json.dump(data,f,indent=2)

# Plot hysteresis
fig,ax=plt.subplots(figsize=(8,5))
colors={1.0:'C0',2.0:'C1'}
for alpha_str, vals in data['hysteresis'].items():
    alpha=float(alpha_str)
    K0=np.array(vals['K0'])
    ax.plot(K0, vals['R_back'], 'o--', color=colors[alpha], label=f'backward α={alpha}')
    ax.errorbar(K0, vals['R_forward_mean'], yerr=vals['R_forward_std'], fmt='s-', color=colors[alpha], label=f'forward α={alpha}', capsize=3)
    # corrected threshold line
    kc=new_mean[alpha_str]['K0_c']
    ax.axvline(kc, color=colors[alpha], linestyle=':', alpha=0.7, label=f'mean-field Kc α={alpha}={kc:.2f}')
ax.set_xlabel('K0')
ax.set_ylabel('Order parameter R')
ax.set_title('State-dependent Kuramoto: forward/backward hysteresis')
ax.legend()
ax.set_ylim(-0.05,1.05)
fig.tight_layout()
fig.savefig('../../shared_agora/artifacts/emp042_defense_hysteresis.png',dpi=150)

# Plot Lyapunov
fig,ax=plt.subplots(figsize=(8,5))
ly=data['lyapunov']
cases=[(d['alpha'],d['K0'],d['LE']) for d in ly]
# group
for alpha in [0.0,1.0,2.0]:
    pts=[(k,le) for a,k,le in cases if a==alpha]
    if pts:
        ks,les=zip(*pts)
        label='constant K' if alpha==0.0 else f'feedback α={alpha}'
        ax.plot(ks,les,'o-',label=label)
for alpha in [1.0,2.0]:
    ax.axvline(new_mean[str(alpha)]['K0_c'], color='gray', linestyle=':', alpha=0.5)
ax.axhline(0,color='k',lw=0.5)
ax.set_xlabel('K0')
ax.set_ylabel('Projected finite-difference LE')
ax.set_title('Transverse Lyapunov exponents')
ax.legend()
fig.tight_layout()
fig.savefig('../../shared_agora/artifacts/emp042_defense_lyapunov.png',dpi=150)
print('Updated artifacts saved.')
