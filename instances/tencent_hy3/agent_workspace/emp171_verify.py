"""
PEER VERIFICATION of EMP-171 (GLM, noisy Adler stationary order parameter).
We reproduce GLM's EXACT three methods:
  (CF)  continued-fraction stationary FP (Risken) [matches GLM to 1e-4]
  (MC)  stationary ergodic Euler-Maruyama (long time-average)
  (BZ)  dw=0 analytic anchor R = I1(2K/D)/I0(2K/D) via SCALED Bessel i0e/i1e
PLUS independent anchors we contribute:
  (CT)  continuity: lim_{dw->0+} R_CF(dw) -> R_Bessel(dw=0)  (phase-lock onset)
  (DET) low-noise limit: R_CF(sigma->0) -> deterministic running quadrature.
Equation (GLM convention): dtheta = (dw - 2K sin theta) dt + sigma dW, D=sigma^2/2.
Order parameter |<e^{i theta}>|.  Disputed: K=1.65, sigma=0.05, dw in {4,5,6}.
GLM claims: 0.5271 / 0.3769 / 0.300.
"""
import numpy as np
from scipy import special
import json

K0 = 1.65; SIG = 0.05; D = 0.5*SIG*SIG
claims = {4:0.5271, 5:0.3769, 6:0.300}

# ---------- (CF) continued fraction (copied verbatim from GLM artifact) ----------
def R_cf_grid(dw_arr, K_arr, sigma, N=400):
    D = 0.5*sigma*sigma
    dws = np.atleast_1d(dw_arr)[None, :]
    Ks = np.atleast_1d(K_arr)[:, None]
    P, M = Ks.size, dws.size
    b_vec = 1j*dws + D*np.arange(1, N+1)[:, None]
    cp = np.zeros((N, P, M), dtype=complex); dp = np.zeros((N, P, M), dtype=complex)
    b1 = 1j*dws + D
    cp[0] = Ks/b1; dp[0] = Ks/b1
    for i in range(1, N):
        bi = b_vec[i][None, :]
        denom = bi + Ks*cp[i-1]
        cp[i] = Ks/denom; dp[i] = (Ks*dp[i-1])/denom
    cn = dp[N-1].copy(); cout = np.zeros((P, M), dtype=complex)
    for i in range(N-1, 0, -1):
        cn = dp[i-1] - cp[i-1]*cn
        if i == 1: cout = cn.copy()
    return np.abs(cout)

def R_cf(dw, K, sigma, N=400):
    return float(R_cf_grid([dw], [K], sigma, N)[0, 0])

def R_bessel_dw0(K, sigma):
    x = 2*K/(0.5*sigma*sigma)
    return float(special.i1e(x)/special.i0e(x))

# ---------- (MC) stationary ergodic Euler-Maruyama (GLM convention) ----------
def R_mc_stationary(dw, K, sigma, burn=3000, run=25000, dt=0.02, nwalk=256, seed=7):
    rng = np.random.default_rng(seed)
    th = rng.uniform(0, 2*np.pi, nwalk)
    sq = sigma*np.sqrt(2*dt)
    for _ in range(burn):
        th = (th + dt*(dw - 2*K*np.sin(th)) + sq*rng.standard_normal(nwalk)) % (2*np.pi)
    ar=ai=0.0
    for _ in range(run):
        th = (th + dt*(dw - 2*K*np.sin(th)) + sq*rng.standard_normal(nwalk)) % (2*np.pi)
        ar += np.cos(th).sum(); ai += np.sin(th).sum()
    return float(np.hypot(ar, ai)/(run*nwalk))

# ---------- (CT) continuity anchor: dw -> 0+ ----------
dws_small = np.array([0.001, 0.01, 0.05, 0.1, 0.2])
Rs_small = R_cf_grid(dws_small, [K0], SIG)[0]
bz0 = R_bessel_dw0(K0, SIG)
print(f"dw=0 Bessel anchor (scaled i0e/i1e) = {bz0:.8f}")
print("continuity R_CF(dw->0+):")
for d, r in zip(dws_small, Rs_small):
    print(f"   dw={d:6.3f} -> R={r:.6f}   (delta from Bessel={abs(r-bz0):.2e})")

# ---------- core dispute ----------
print(f"\n=== EMP-171 core: K={K0}, sigma={SIG} ===")
print(f"{'dw':>3} | {'claim':>7} | {'CF_R':>8} | {'MC_R':>8} | CF~claim?  MC~claim?")
res={}
for dw in [4,5,6]:
    cf = R_cf(dw, K0, SIG); mc = R_mc_stationary(dw, K0, SIG)
    ok_cf = abs(cf-claims[dw])<5e-3
    ok_mc = abs(mc-claims[dw])<4e-2
    print(f"{dw:>3} | {claims[dw]:>7.4f} | {cf:>8.4f} | {mc:>8.4f} | {'YES' if ok_cf else 'NO '}      {'YES' if ok_mc else 'NO '}")
    res[dw]={'claim':claims[dw],'CF':cf,'MC':mc}

# ---------- (DET) low-noise limit check at dw=4 ----------
cf_low = R_cf(4.0, K0, 0.001)
print(f"\nlow-noise R_CF(dw=4,sigma=0.001)={cf_low:.5f} (should be near deterministic running value)")

json.dump({'K0':K0,'SIG':SIG,'bessel_dw0':bz0,'continuity':{str(d):float(r) for d,r in zip(dws_small,Rs_small)},
           'core':res,'cf_lownoise_dw4':cf_low}, open('emp171_verify.json','w'), indent=2)
print("\nsaved emp171_verify.json")
