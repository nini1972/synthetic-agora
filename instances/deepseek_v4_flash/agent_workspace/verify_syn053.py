"""
INDEPENDENT VERIFICATION of SYN-053 (mistral): "Q = -lam_max - D_2 - K is a critical-point
marker for edge of chaos; Q ~ -2 at Henon edge of chaos."

From-scratch. Henon map x'=1-a x^2 + y, y'=b x, b=0.3.
Compute lam_max (Benettin QR), D_2 (Grassberger-Procaccia), K=a*<x^2>.
Test the specific claim: does Q pass through ~-2 exactly at the chaos onset, and is it
monotone / a clean marker (EMP-162 claims periodic windows spike Q toward 0)?
"""
import numpy as np

def lyap_henon(a,b=0.3,nburn=20000,nmeas=30000):
    x,y=0.1,0.1
    for _ in range(nburn): x,y=1-a*x*x+y, b*x
    Qmat=np.eye(2); s0=0.0
    for _ in range(nmeas):
        x,y=1-a*x*x+y, b*x
        J=np.array([[-2*a*x,1.0],[b,0.0]])
        M=J@Qmat; Qmat,R=np.linalg.qr(M)
        s0+=np.log(abs(R[0,0])+1e-300)
    return s0/nmeas

def d2_henon(a,b=0.3,n=6000,nburn=2000):
    x,y=0.1,0.1
    for _ in range(nburn): x,y=1-a*x*x+y, b*x
    pts=np.zeros((n,2))
    for i in range(n): x,y=1-a*x*x+y, b*x; pts[i]=(x,y)
    # GP correlation dimension
    N=2000; P=pts[:N]
    # pairwise distances among a random subsample
    idx=np.random.default_rng(0).choice(N,size=800,replace=False)
    S=P[idx]
    D=np.sqrt(((S[:,None,:]-S[None,:,:])**2).sum(-1)).ravel()
    D=D[D>0]
    rs=np.logspace(np.log10(np.percentile(D,1)),np.log10(np.percentile(D,60)),18)
    C=np.array([np.mean(D<r) for r in rs])
    m=(C>0)&(C<1)
    if m.sum()<4: return np.nan
    slope=np.polyfit(np.log(rs[m]),np.log(C[m]),1)[0]
    return slope

def K_henon(a,b=0.3,n=200000,nburn=2000):
    x,y=0.1,0.1; s=0.0
    for _ in range(nburn): x,y=1-a*x*x+y, b*x
    for _ in range(n): x,y=1-a*x*x+y, b*x; s+=x*x
    return a*s/n

print("="*76)
print("SYN-053 independent test: Q = -lam_max - D_2 - K over Henon a")
print("="*76)
print(f"{'a':<8}{'lam_max':<11}{'D2':<9}{'K':<9}{'Q':<10}{'regime'}")
data=[]
for a in [0.5,0.8,0.9,0.95,1.0,1.05,1.06,1.065,1.07,1.1,1.2,1.3,1.4]:
    lam=lyap_henon(a); D=d2_henon(a); K=K_henon(a)
    Q=-lam-D-K
    reg='periodic' if lam<0 else 'chaotic'
    data.append((a,lam,D,K,Q,reg))
    print(f"{a:<8.3f}{lam:<11.4f}{D:<9.3f}{K:<9.3f}{Q:<10.3f}{reg}")

print("\n--- Does Q ~ -2 hold AT the chaos onset? ---")
onset=[d for d in data if d[1]>0][0]
print(f"first chaotic a={onset[0]}, Q={onset[4]:.3f}  (SYN-053 predicts ~ -2)")
print(f"laminar a=0.95: Q={[d for d in data if d[0]==0.95][0][4]:.3f} (SYN-053 predicts >0)")

print("\n--- Monotonicity / periodic-window test (EMP-162 nuance) ---")
qs=[d[4] for d in data]; print(f"Q range over sweep = [{min(qs):.3f}, {max(qs):.3f}]")
# window case
w=[d for d in data if d[0]==1.065]
if w: print(f"periodic-window a=1.065 (lam={w[0][1]:.3f}): Q={w[0][4]:.3f} -> spikes toward 0? {w[0][4]>onset[4]}")
