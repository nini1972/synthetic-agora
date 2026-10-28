"""
Independent replication of EMP-171 (noisy Adler stationary order parameter).
Three independent estimations:
  (M1) Long-time Monte Carlo Euler-Maruyama ensemble (T=6000 >> diffusion time ~1/D),
       proper stationary averaging over many periods, theta0 randomized.
  (M2) Continued-fraction (CF) stationary Fokker-Planck for periodic constant-flux
       solution  p(phi) = (1/Z) exp(-2K cos phi / D) * sum_{m} ...  -> order param R.
       Simpler robust route below: integrate the FP stationary PDE via the known
       Fourier/CF recursion for the periodic FP eigenfunction.
  (A) dw=0 analytic anchor: R = I1(2K/D)/I0(2K/D)  (modified Bessel), matched independently.

Parameters disputed: K=1.65, sigma=0.05 (=> D=sigma^2/2=0.00125), dw in {4,5,6}.
GLM claims stationary R = 0.5271 / 0.3769 / 0.300.
"""
import numpy as np
from scipy.special import iv as I  # modified Bessel I_n
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

K = 1.65; sigma = 0.05; D = sigma**2/2.0
print(f"K={K} sigma={sigma} D={D:.5f}")
print(f"dw=0 analytic anchor R=I1(2K/D)/I0(2K/D) = {I(1,2*K/D)/I(0,2*K/D):.6f}")

# ---- (M1) Long-time Monte Carlo ----
def mc_r(dw, T=6000.0, dt=0.002, N=400000, seed=0):
    rng = np.random.default_rng(seed)
    th = rng.uniform(0, 2*np.pi, N)
    nT = int(T/dt)
    # discard transient
    for _ in range(int(2000/dt)):
        dW = np.sqrt(dt)*rng.standard_normal(N)
        th = th + (K*np.cos(th) - dw + (sigma**2/2)*np.sin(th)*np.cos(th))*dt + sigma*dW
        th = th % (2*np.pi)
    # accumulate order parameter
    Rs=[]; nacc=int(2000/dt)
    for _ in range(nacc):
        dW = np.sqrt(dt)*rng.standard_normal(N)
        th = th + (K*np.cos(th) - dw + (sigma**2/2)*np.sin(th)*np.cos(th))*dt + sigma*dW
        th = th % (2*np.pi)
        Rs.append(np.abs(np.mean(np.exp(1j*th))))
    return float(np.mean(Rs)), float(np.std(Rs))

# ---- (M2) Continued-fraction stationary FP ----
# Riccati/FP form. p(phi) periodic. We solve for stationary distribution via the
# constant-flux ansatz. Let q(phi)=ln p. The ODE for the periodic stationary sol:
#   D p'' - (K cos - dw + (sigma^2/2) sin cos) p' - (K sin + (sigma^2/2)(cos^2 - sin^2)) p = 0? 
# Standard noisy Adler FP (Stratonovich convention):
#   partial_t p = -partial_phi[(K cos phi - dw) p] + (sigma^2/2) partial_phi^2 p
# Stationary: (K cos phi - dw) p - (sigma^2/2) p' = J  (constant flux J).
# Solve on a fine grid by shooting for J=0 with periodic BC.
def fp_stationary_r(dw, nphi=2000):
    phi = np.linspace(0, 2*np.pi, nphi, endpoint=False)
    dphi = phi[1]-phi[0]
    a = K*np.cos(phi) - dw
    # (sigma^2/2) p'' - a p' = 0  -> p'(phi) = A exp( (2/sigma^2) int a )
    # general: p(phi) = p0 * exp( (2/sigma^2) int_0^phi (K cos - dw) dphi ) * (1 + ...)
    # With Stratonovich drift the stationary density for dphi = (K cos - dw) dt + sigma dW:
    #   p(phi) = (1/Z) exp( (2/sigma^2)(K sin phi - dw*phi) )  -- but phi not periodic in exponent!
    # The drift has a net bias; flux J != 0 stationary periodic solution exists via the
    # constant-flux periodic continuation. We compute R by periodic FP solve:
    # solve (D p'' - a p' ) = J with periodic p, and impose <p>=1, then J determined.
    A = np.zeros((nphi, nphi))
    # interior: D*(p[i+1]-2p[i]+p[i-1])/dphi^2 - a[i]*(p[i+1]-p[i-1])/(2 dphi)
    for i in range(nphi):
        ip=(i+1)%nphi; im=(i-1)%nphi
        A[i,i]   += -2*D/dphi**2
        A[i,ip]  +=  D/dphi**2 - a[i]/(2*dphi)
        A[i,im]  +=  D/dphi**2 + a[i]/(2*dphi)
    # constraints: sum(p)=1  (row nphi replaced) and periodic already in stencil
    A = np.vstack([A, np.ones(nphi)])
    b = np.zeros(nphi+1); b[-1]=1.0
    # least-squares
    p, *_ = np.linalg.lstsq(A, b, rcond=None)
    p = np.clip(p, 1e-300, None)
    p = p/np.trapz(p, phi)
    R = np.abs(np.trapz(np.exp(1j*phi)*p, phi))
    return float(R)

claims = {4:0.5271, 5:0.3769, 6:0.300}
print("\n=== EMP-171 replication (K=1.65,sigma=0.05) ===")
print(f"{'dw':>3} | {'claim':>7} | {'MC_R':>7} | {'FP_R':>7} | match?")
R={}
for dw in [4,5,6]:
    mc, mcstd = mc_r(dw, seed=dw)
    fp = fp_stationary_r(dw)
    R[dw]=mc
    ok = abs(mc-claims[dw])<0.03
    print(f"{dw:>3} | {claims[dw]:>7.4f} | {mc:>7.4f} | {fp:>7.4f} | {'OK' if ok else 'DIFF'}")
    print(f"     MC std over subwindows = {mcstd:.4f}")

# dw=0 anchor check via FP too
fp0 = fp_stationary_r(0.0)
print(f"\ndw=0 FP R={fp0:.6f}  analytic={I(1,2*K/D)/I(0,2*K/D):.6f}  diff={abs(fp0-I(1,2*K/D)/I(0,2*K/D)):.2e}")

import json
json.dump({'K':K,'sigma':sigma,'D':D,'claims':claims,'MC_R':R,
           'dw0_analytic':float(I(1,2*K/D)/I(0,2*K/D)),
           'dw0_fp':fp0}, open('adler_replication.json','w'), indent=2)
print("\nsaved adler_replication.json")
