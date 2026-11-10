"""
INDEPENDENT VERIFICATION of EMP-192 (tencent_hy3) / EMP-171 (glm_5_2):
Stationary order parameter of the noisy Adler equation
    dtheta = (dw - 2K sin theta) dt + sigma dW ,  D = sigma^2/2
at K=1.65, sigma=0.05, dw in {4,5,6}.
Claimed: R(4)=0.5271, R(5)=0.3769, R(6)=0.300.

METHODS (all written from scratch, no shared code):
 (PF) Exact stationary Fokker-Planck via periodic constant-flux form:
      p(theta) ∝ ∫_0^{2π} exp(-h_theta(s)/D) ds,
      h_theta(s) = dw*s + 2K*(cos(theta+s)-cos(theta)).
      Since dw > 2K, dh/ds = dw - 2K cos(theta+s) >= dw-2K > 0, so h is
      monotonically increasing in s; bound h >= dw*s - 4K => truncate at
      s_max = (c+4K)/dw with c=32 (tail < e^-32 ~ 1e-14). Clustered grid
      s = s_max * t^4 to resolve the ~1e-3 decay scale.
 (HF) Weak-diffusion (high-flux) closed form via Laplace method:
      p ≈ C/(dw - 2K sin theta)  =>  R = (dw - sqrt(dw^2 - 4K^2))/(2K).
 (BZ) dw=0 Bessel anchor: R = I1(2K/D)/I0(2K/D) (von Mises, J=0 by symmetry).
 (MC) Independent Euler-Maruyama ergodic average, own seed/dt/walkers.
"""
import numpy as np
from scipy import special
import json

K = 1.65; SIG = 0.05; D = 0.5*SIG*SIG
dws = [4.0, 5.0, 6.0]
claimed = {4.0: 0.5271, 5.0: 0.3769, 6.0: 0.300}
twopi = 2*np.pi

def R_hf(dw):
    return (dw - np.sqrt(dw*dw - 4*K*K)) / (2*K)

def R_pf(dw, Nth=2048, Ns=600, c=32.0):
    th = np.linspace(0, twopi, Nth, endpoint=False)
    dth = twopi/Nth
    cosh = np.cos(th)
    s_max = (c + 4*K)/dw
    t = np.linspace(0, 1, Ns)
    s = s_max * t**4
    w = np.zeros(Ns)
    for i in range(Ns-1):
        d = s[i+1]-s[i]
        w[i] += 0.5*d; w[i+1] += 0.5*d
    Q = np.empty(Nth)
    CH = 128
    for a in range(0, Nth, CH):
        b = min(a+CH, Nth)
        thb = th[a:b]; cb = cosh[a:b]
        h = dw*s[None,:] + 2*K*(np.cos(thb[:,None] + s[None,:]) - cb[:,None])
        Q[a:b] = np.exp(-h/D) @ w
    eith = np.exp(1j*th)
    z = (Q * dth).sum()
    R = np.abs(z)
    return R

R0 = special.i1e(2*K/D)/special.i0e(2*K/D)

def mc(dw, nwalk=128, dt=0.005, t_burn=6000.0, t_meas=40000.0, seed=20261110):
    rng = np.random.default_rng(seed)
    nb = int(t_burn/dt); nm = int(t_meas/dt)
    th = rng.uniform(0, twopi, nwalk)
    sq = SIG*np.sqrt(dt)
    for i in range(nb):
        th += (dw - 2*K*np.sin(th))*dt + sq*rng.standard_normal(nwalk)
    acc_re = 0.0; acc_im = 0.0; n = 0
    CH = 2000
    for i in range(0, nm, CH):
        m = min(CH, nm-i)
        for j in range(m):
            th += (dw - 2*K*np.sin(th))*dt + sq*rng.standard_normal(nwalk)
            acc_re += np.cos(th).sum(); acc_im += np.sin(th).sum(); n += nwalk
    return np.hypot(acc_re/n, acc_im/n)

print(f"Bessel anchor dw=0: kappa=2K/D={2*K/D:.0f}, R = I1/I0 = {R0:.10f}")
print(f"{'dw':>4} {'PF-exact':>10} {'HF-closed':>10} {'MC(own)':>10} {'claimed':>9} {'dPF':>9} {'dPF-HF':>9} {'dMC':>9}")
print('-'*75)
res = {}
for dw in dws:
    r_pf = R_pf(dw); r_hf = R_hf(dw); r_mc = mc(dw)
    res[str(dw)] = dict(pf=float(r_pf), hf=float(r_hf), mc=float(r_mc),
                        claimed=claimed[dw], d_pf_claimed=float(r_pf-claimed[dw]),
                        d_pf_hf=float(r_pf-r_hf), d_mc_claimed=float(r_mc-claimed[dw]))
    print(f"{dw:>4.0f} {r_pf:>10.6f} {r_hf:>10.6f} {r_mc:>10.4f} {claimed[dw]:>9.4f} "
          f"{r_pf-claimed[dw]:>+9.2e} {r_pf-r_hf:>+9.2e} {r_mc-claimed[dw]:>+9.2e}")
print()
print("PF grid convergence (Nth, Ns):")
for dw in dws:
    r1 = R_pf(dw, 1024, 300); r2 = R_pf(dw, 2048, 600); r3 = R_pf(dw, 4096, 1200)
    print(f"dw={dw:.0f}: (1024,300)={r1:.8f}  (2048,600)={r2:.8f}  (4096,1200)={r3:.8f}")

res['bessel_dw0'] = float(R0)
with open('emp192_fp_verify_results.json','w') as f:
    json.dump(res, f, indent=2)
print("\nSaved emp192_fp_verify_results.json")
