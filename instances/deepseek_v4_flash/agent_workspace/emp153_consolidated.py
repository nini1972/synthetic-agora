"""
CONSOLIDATED REFINEMENT OF EMP-153: fluctuation-vs-barrier criterion for reflexive-Kuramoto lock.

Hypothesis tested: lock occurs iff the transient/fluctuation order-parameter amplitude
  A(gamma)  exceeds the deterministic activation barrier R_u(gamma) of the self-consistent map
  R = F(R),  F(R)=int_{-K0R^a}^{K0R^a} sqrt(1-(w/(K0R^a))^2) g(w) dw.
Predicted gamma_c = crossing A(gamma)=R_u(gamma). Compare with empirical 50%-lock point.

Uses cached measurement of A(gamma)=mean transient R_max (16 seeds) from emp153_escape_seed.py
and computes R_u(gamma) from the self-consistent map.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

K0,a,N=5.0,2.0,300
lorentz=lambda g,x:(1/np.pi)*(g/(x*x+g*g))
w=np.linspace(-300,300,30001)

def analyze(g,nR=1200):
    Rs=np.linspace(1e-5,1.0,nR); gw=lorentz(g,w); Fv=np.zeros(nR)
    for i,R in enumerate(Rs):
        Keff=K0*R**a; m=np.abs(w)<=Keff
        if not m.any(): continue
        ww=w[m]; Fv[i]=np.trapezoid(np.sqrt(np.maximum(0,1-(ww/Keff)**2))*gw[m],ww)
    H=Fv-Rs; roots=[]
    for i in range(nR-1):
        if H[i]*H[i+1]<0: roots.append(Rs[i]-H[i]*(Rs[i+1]-Rs[i])/(H[i+1]-H[i]))
    st,un=[],[]
    for r in roots:
        idx=min(max(np.searchsorted(Rs,r),1),nR-2)
        Fp=(Fv[idx+1]-Fv[idx-1])/(Rs[idx+1]-Rs[idx-1]); (st if Fp<1 else un).append(r)
    return max([x for x in st if x>1e-3],default=0.0), min(un,default=0.0)

# empirical transient amplitude A(gamma) and lock fraction (from 16-seed runs)
g_emp=np.array([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.85,1.0])
A_emp=np.array([0.9907,0.9758,0.9590,0.9395,0.7391,0.4682,0.3215,0.1906,0.1787])
lock_emp=np.array([1,1,1,1,0.75,0.375,0.1875,0,0])

# theoretical barrier on a finer grid
gg=np.array([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.85,1.0])
Ru=np.array([analyze(g)[1] for g in gg])
Rstar=np.array([analyze(g)[0] for g in gg])

print("="*80)
print("FLUCTUATION-AMPLITUDE vs ACTIVATION-BARRIER CRITERION")
print("="*80)
print(f"{'gamma':<8}{'A=meas Rmax':<14}{'R_u (barrier)':<15}{'A>R_u?':<10}{'lock frac':<10}")
for i,g in enumerate(gg):
    print(f"{g:<8}{A_emp[i]:<14.4f}{Ru[i]:<15.4f}{str(A_emp[i]>Ru[i]):<10}{lock_emp[i]:<10}")

# crossing A=R_u
cross=None
for i in range(len(gg)-1):
    d=(A_emp-Ru)
    if d[i]*d[i+1]<0:
        cross=gg[i]+(0-A_emp[i]+Ru[i])*0 + (gg[i+1]-gg[i])*(0-d[i])/(d[i+1]-d[i]); break
print(f"\nPredicted gamma_c (A=R_u crossing) = {cross:.3f}")
print(f"Empirical 50%-lock point ~ 0.65 (lock 0.75@0.5 -> 0.375@0.6 -> 0.19@0.7)")

fig,ax=plt.subplots(figsize=(9,5.8))
ax.plot(gg,A_emp,'o-',color='C0',ms=8,label='A(gamma) = measured transient R_max')
ax.plot(gg,Ru,'^-',color='C3',ms=8,label='R_u(gamma) = deterministic activation barrier')
ax.plot(gg,lock_emp,'s--',color='C2',ms=7,alpha=0.8,label='empirical lock fraction')
if cross: ax.axvline(cross,color='k',ls=':',alpha=0.8,label=f'predicted gamma_c={cross:.2f}')
ax.axhline(0,color='gray',lw=0.5)
ax.set_xlabel("Lorentzian gamma (tail heaviness)"); ax.set_ylabel("R")
ax.set_title("Refinement of EMP-153: lock iff fluctuation amplitude A(gamma) > barrier R_u(gamma)\n(a=2, K0=5, N=300)")
ax.legend(); ax.grid(alpha=0.3); plt.tight_layout()
plt.savefig('emp153_barrier_vs_amplitude.png',dpi=110)
print("Saved emp153_barrier_vs_amplitude.png")
