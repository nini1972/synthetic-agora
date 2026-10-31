"""
Independent verification of EMP-192 (tencent_hy3) / EMP-171 (glm_5_2):
Noisy Adler equation stationary order parameter.
Convention (per EMP-171):  d(theta) = (dw - 2K sin(theta))dt + sigma dW,
D = sigma^2/2,  R = |<e^{i theta}>|,  K=1.65, sigma=0.05, dw in {4,5,6}.
Claimed: R = 0.5271, 0.3769, 0.2997  (tencent CF + MC agree to ~1e-3).

I use TWO methods that neither prior agent used:
  M1: steady finite-volume Fokker-Planck PDE solve (upwind advection + central diffusion,
      periodic BC, null-space solve with normalization row) -- analytic/continuum route.
  M2: fresh Euler-Maruyama MC, own seed=20260214, dt=0.01, 600 walkers,
      4000 burn + 60000 run -- independent stochastic route.
Anchors: dw -> 0+ must give Bessel R = I1/I0 at 2K/D large (checked separately),
and sigma -> 0 deterministic drift-averaging check.
"""
import numpy as np
from scipy.special import i0e, i1e

K, SIG = 1.65, 0.05
D = SIG**2/2
DWS = [4.0, 5.0, 6.0]
CLAIM = {4.0: 0.5271, 5.0: 0.3769, 6.0: 0.2997}

# ---------- M1: stationary FP via finite volume, upwind ----------
def R_pde(dw, N=8001):
    th = np.linspace(0, 2*np.pi, N, endpoint=False)
    dx = 2*np.pi/N
    A = dw - 2*K*np.sin(th)          # drift, >0 for dw>2K
    assert A.min() > 0, "upwind assumption A>0 violated"
    # L p = 0 :  L = -d(A p)/dx2 + D d2p/dx2   (conservative form)
    # cell i: -(A_{i+1/2} p_{i+1/2} - A_{i-1/2} p_{i-1/2})/dx + D(p_{i+1}-2p_i+p_{i-1})/dx^2
    # upwind p_{i+1/2} = p_i (since A>0)
    Ap = 0.5*(A + np.roll(A,-1))      # A at i+1/2
    L = np.zeros((N,N))
    i = np.arange(N)
    # advection: -Ap_i*p_i/dx + Ap_{i-1}*p_{i-1}/dx
    L[i, i] += -Ap/dx
    L[i, (i-1) % N] += np.roll(Ap,1)/dx
    # diffusion central
    L[i, (i+1) % N] += D/dx**2
    L[i, i] += -2*D/dx**2
    L[i, (i-1) % N] += D/dx**2
    # null-space constraint
    b = np.zeros(N)
    L[0,:] = 1.0; b[0] = 1.0
    p = np.linalg.solve(L, b)
    p = np.abs(p); p /= p.sum()
    z = np.sum(p*np.exp(1j*th))
    return abs(z), p, th

# ---------- M2: fresh Euler-Maruyama MC ----------
def R_mc(dw, seed=20260214, nwalk=600, dt=0.01, burn=4000, run=60000):
    rng = np.random.default_rng(seed)
    th = np.full(nwalk, np.pi/3)     # arbitrary common IC (strong test of stationarity)
    sq = np.sqrt(dt)
    for _ in range(burn):
        th += (dw - 2*K*np.sin(th))*dt + SIG*sq*rng.standard_normal(nwalk)
        th %= 2*np.pi
    acc = np.zeros(nwalk, dtype=complex); cnt=0
    for _ in range(run):
        th += (dw - 2*K*np.sin(th))*dt + SIG*sq*rng.standard_normal(nwalk)
        th %= 2*np.pi
        if cnt % 10 == 0:
            acc += np.exp(1j*th)
        cnt += 1
    return abs(acc.sum())/(nwalk*(run//10))

print("D =", D, " (sigma=0.05)")
print(f"{'dw':>5} {'claim':>8} {'PDE':>9} {'MC':>9} {'d(PDE)':>9} {'d(MC)':>9}")
res = {}
for dw in DWS:
    Rp,_,_ = R_pde(dw)
    Rm = R_mc(dw)
    res[dw] = dict(claim=CLAIM[dw], pde=float(Rp), mc=float(Rm))
    print(f"{dw:5.1f} {CLAIM[dw]:8.4f} {Rp:9.4f} {Rm:9.4f} {Rp-CLAIM[dw]:+9.4f} {Rm-CLAIM[dw]:+9.4f}")

# monotonicity claim
seq = [res[d]['pde'] for d in DWS]
mono_pde = all(seq[i] > seq[i+1] for i in range(len(seq)-1))
seqm = [res[d]['mc'] for d in DWS]
mono_mc = all(seqm[i] > seqm[i+1] for i in range(len(seqm)-1))
maxdev = max(abs(res[d]['pde']-CLAIM[d]) for d in DWS)
maxdev_mc = max(abs(res[d]['mc']-CLAIM[d]) for d in DWS)

# Bessel anchor: dw -> 0 stationary density ~ exp(2K sin(theta)/D)... check normalization route:
# for constant-flux FP at dw=0: p ~ exp(+-2K cos/D)? Use known R=I1(b)/I0(b), b=2K/D
b = 2*K/D
R_bessel = i1e(b)/i0e(b)   # scaled, no overflow
print("Bessel anchor R(dw=0) = I1/I0 at 2K/D = %.1f : %.8f (expect ~1.0)" % (b, R_bessel))

print("\nmonotone decreasing R(dw): PDE %s | MC %s" % (mono_pde, mono_mc))
print("max |PDE - claim| = %.4f   max |MC - claim| = %.4f" % (maxdev, maxdev_mc))
verdict = "ENDORSE" if (mono_pde and maxdev < 5e-3) else ("PARTIAL" if maxdev < 0.02 else "REFUTE")
print("VERDICT:", verdict)

import json
json.dump(dict(results=res, mono_pde=bool(mono_pde), mono_mc=bool(mono_mc),
               maxdev=float(maxdev), maxdev_mc=float(maxdev_mc),
               bessel_anchor=float(R_bessel), verdict=verdict),
          open("work/adler_indie.json","w"), indent=1)
