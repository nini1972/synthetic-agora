"""
ACTIVATION BARRIER (lean).  Build F(R) on a coarse R-grid, interpolate.
F(R)=int_{-K0R^a}^{K0R^a} sqrt(1-(w/(K0R^a))^2) g(w) dw
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

K0, a = 5.0, 2.0
N = 300
R0 = 1.0/np.sqrt(N)
w = np.linspace(-300, 300, 30001)
lorentz = lambda g, x: (1/np.pi)*(g/(x*x+g*g))

def build_F(g, nR=1500):
    Rs = np.linspace(1e-5, 1.0, nR)
    Fv = np.zeros(nR)
    gw = lorentz(g, w)
    for i, R in enumerate(Rs):
        Keff = K0 * R**a
        m = np.abs(w) <= Keff
        if not m.any(): continue
        ww = w[m]
        Fv[i] = np.trapezoid(np.sqrt(np.maximum(0,1-(ww/Keff)**2))*gw[m], ww)
    return Rs, Fv

def analyze(g):
    Rs, Fv = build_F(g)
    H = Fv - Rs
    roots=[]
    for i in range(len(Rs)-1):
        if H[i]*H[i+1] < 0:
            roots.append(Rs[i]-H[i]*(Rs[i+1]-Rs[i])/(H[i+1]-H[i]))
    st,un=[],[]
    for r in roots:
        idx=np.searchsorted(Rs,r); idx=min(max(idx,1),len(Rs)-2)
        Fp=(Fv[idx+1]-Fv[idx-1])/(Rs[idx+1]-Rs[idx-1])
        (st if Fp<1 else un).append(r)
    return max([x for x in st if x>1e-3], default=0.0), min(un, default=0.0)

print("="*88)
print(f"ACTIVATION BARRIER  a={a}, K0={K0}, N={N}, R0={R0:.4f}")
print("="*88)
emp={0.1:'8/8',0.3:'8/8',0.5:'4/8',0.7:'0/8',1.0:'0/8',1.5:'0/8'}
print(f"{'gamma':<8}{'R*(sync)':<12}{'R_u':<12}{'R0>R_u?':<12}{'empirical':<10}")
for g in [0.1,0.3,0.5,0.7,1.0,1.5]:
    Rstar,Ru = analyze(g)
    print(f"{g:<8}{Rstar:<12.4f}{Ru:<12.4f}{str(R0>Ru):<12}{emp[g]:<10}")

gg=np.linspace(0.05,1.2,26)
res=np.array([analyze(g) for g in gg])
Rus=res[:,1]
gc=None
for i in range(len(gg)-1):
    if (Rus[i]-R0)*(Rus[i+1]-R0)<0:
        gc=gg[i]+(R0-Rus[i])*(gg[i+1]-gg[i])/(Rus[i+1]-Rus[i]); break
print(f"\npredicted gamma_crit (R_u=R0) = {gc:.3f}" if gc else "no crossing")

fig,ax=plt.subplots(figsize=(8.5,5.5))
ax.plot(gg,res[:,1],'-',color='C3',lw=2.2,label='activation barrier R_u(gamma)')
ax.plot(gg,res[:,0],'--',color='C2',lw=1.5,label='sync attractor R*(gamma)')
ax.axhline(R0,color='C0',ls='--',lw=2,label=f'finite-N seed R0=1/sqrt({N})={R0:.3f}')
if gc: ax.axvline(gc,color='k',ls=':',alpha=0.8,label=f'gamma_c={gc:.2f}')
ax.fill_between(gg,0,R0,where=(res[:,1]<R0),color='C0',alpha=0.12,label='escape (lock)')
ax.set_xlabel("Lorentzian gamma"); ax.set_ylabel("R")
ax.set_title("Activation-barrier theory vs empirical lock collapse\n(a=2,K0=5,N=300): lock iff R0>R_u")
ax.legend(); ax.grid(alpha=0.3); plt.tight_layout()
plt.savefig('emp153_activation_barrier.png',dpi=110)
print("Saved emp153_activation_barrier.png")
