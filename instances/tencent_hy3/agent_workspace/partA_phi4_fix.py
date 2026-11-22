"""Part A fixed: phi^4 kink wobble softening sign + coefficient.
Target the true internal (wobble) mode nearest omega^2 = 1.5 to avoid the
Dirichlet spurious near-zero mode.
"""
import numpy as np, json
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh

N = 4001; L = 120.0
x = np.linspace(-L/2, L/2, N); dx = x[1]-x[0]
def vprime(p): return 2*p - 2*p**3
def vpp(p): return 2.0 - 6.0*p**2
f = (1.0/np.cosh(x/np.sqrt(2.0)))**2

def solve_kink(lam, iters=6000):
    phi = np.tanh(x/np.sqrt(2.0)).copy()
    for _ in range(iters):
        rhs = vprime(phi) + lam*f
        phi = 0.5*(np.roll(phi,1)+np.roll(phi,-1)) - 0.5*dx**2*rhs
        phi[0]=-1.0; phi[-1]=1.0
    return phi

def omega1_sq(lam):
    phi = solve_kink(lam)
    Vpp = vpp(phi)
    off = -1.0/dx**2*np.ones(N-1)
    diag = 2.0/dx**2 + Vpp
    M = diags([off, diag, off], [-1,0,1])
    # shift-invert around the known wobble mode ~1.5 (analytic 3/2)
    vals = eigsh(M.tocsc(), k=2, sigma=1.5, which='LM', return_eigenvectors=False)
    vals = np.sort(np.real(vals))
    return float(vals[np.argmin(np.abs(vals-1.5))])

lams = np.array([0.0,0.05,0.1,0.2,0.3])
w2 = [omega1_sq(l) for l in lams]
slope,_ = np.polyfit(lams, w2, 1)
print("lams:", lams.tolist())
print("omega1^2:", [round(v,5) for v in w2])
print(f"baseline w2(0)={w2[0]:.4f} (analytic 1.5)")
print(f"linear slope d(w2)/dlam = {slope:.4f}  (SUSY=-0.80152 ; naive=+0.11564)")
print("SOFTENING (negative):", slope < 0)
json.dump({'lams':lams.tolist(),'omega1_sq':w2,'slope':float(slope),
           'softening':bool(slope<0)}, open('agora_phi4_partA.json','w'), indent=2)
