"""
CORRECT exact periodic stationary density of the NOISY ADLER equation on the circle
via the vectorized Miller continued-fraction method.

    dtheta/dt = dw - 2K sin(theta) + sigma * xi(t),  <xi xi>=delta

Fokker-Planck stationary (D = sigma^2/2), constant flux J:
    D P' - (dw - 2K sin theta) P = -J,  P(2pi)=P(0)

Fourier P = sum_n c_n e^{in theta}, real => c_{-n}=conj(c_n):
  n != 0:  (i D n - dw) c_n - i K c_{n-1} + i K c_{n+1} = 0
  =>  c_{n+1} = a_n c_n + c_{n-1},   a_n = (dw - i D n)/(i K)
Backward Miller (minimal decaying solution):
  r_{M+1} = 0;   r_n = 1/(r_{n+1} - a_n)
  R = |<e^{i theta}>| = |2 pi c_{-1}| = |r_1|

This is exact for the TRUE (periodic, non-Gibbs) stationary density. The naive
Gibbs form p ~ exp[(dw*theta + 2K cos theta)/D] used in EMP-069 is INVALID for
dw != 0 (breaks 2pi-periodicity). This script quantifies the resulting error.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def R_cf_vectorized(dw, K, sigma, M=1500):
    """dw: (ndw,) array, K: (nK,) array, sigma scalar. Returns R shape (ndw,nK)."""
    D = 0.5*sigma**2
    dw = np.asarray(dw, float)[:, None]     # (ndw,1)
    K  = np.asarray(K, float)[None, :]      # (1,nK)
    if sigma < 1e-9:
        delta = np.abs(dw)/(2*K)
        R = np.where(delta <= 1.0, 1.0, delta - np.sqrt(np.maximum(delta**2-1,0)))
        return np.broadcast_to(R, (dw.shape[0], K.shape[1])).copy()
    r = np.zeros((dw.shape[0], K.shape[1]), dtype=complex)
    for n in range(M, 0, -1):
        a_n = (dw - 1j*D*n)/(1j*K)
        r = 1.0/(r - a_n)
    return np.abs(r)

def band_frac_max_scan(Omega_max=6.0, band=(0.3,0.7), sigma_list=None,
                       nK=300, ndw=401, M=800):
    if sigma_list is None:
        sigma_list = [0.0, 0.05, 0.10, 0.20, 0.30, 0.50, 0.80]
    K_list = np.linspace(0.9, 2.6, nK)   # refined near the true optimum K*=1.6513
    dw_list = np.linspace(-Omega_max, Omega_max, ndw)
    out = []
    for sigma in sigma_list:
        R = R_cf_vectorized(dw_list, K_list, sigma, M=M)   # (ndw,nK)
        inband = (R >= band[0]) & (R <= band[1])
        bf_per_K = inband.mean(axis=0)                     # (nK,)
        j = int(np.argmax(bf_per_K))
        out.append((sigma, bf_per_K[j], K_list[j], bf_per_K))
    return out, K_list, dw_list

if __name__ == "__main__":
    print("="*78)
    print("EXACT periodic-FP noisy Adler: band_frac_max vs sigma  (Omega_max=6, band[0.3,0.7])")
    print("="*78)
    print(f"{'sigma':>6} | {'band_frac_max':>13} | {'K*':>6} | {'EMP-069 claim':>13}")
    emp069 = {0.0:0.400, 0.05:0.0025, 0.10:0.0025, 0.20:0.0100, 0.30:0.0200, 0.50:0.0750, 0.80:0.2450}
    res, K_list, dw_list = band_frac_max_scan(M=1500)
    for sigma, bf, Kst, _ in res:
        claim = emp069.get(round(sigma,2), float('nan'))
        print(f"{sigma:6.2f} | {bf:13.4f} | {Kst:6.2f} | {claim:13.4f}")
    print()
    print("Deterministic ceiling (PRF-015 dispute): C = 316/763 = 0.414155 (EMP-063/EMP-069 agree).")
    print("EMP-069 asserted sigma=0 -> 0.400 and a collapse-then-recover at sigma~0.8 -> 0.245.")

    # Figure: compare exact CF vs EMP-069's claimed table
    sig = [r[0] for r in res]; bf = [r[1] for r in res]
    cl  = [emp069.get(round(s,2), np.nan) for s in sig]
    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(sig, bf, 'o-', color='crimson', lw=2, label='EXACT periodic FP (corrected)')
    ax.plot(sig, cl, 's--', color='steelblue', lw=2, label="EMP-069 (non-periodic Gibbs, INVALID)")
    ax.axhline(316/763, color='green', ls=':', lw=2, label='deterministic ceiling 316/763=0.414155')
    ax.set_xlabel('noise sigma'); ax.set_ylabel('band_frac_max')
    ax.set_title('Corrected noisy-Adler ceiling: exact periodic FP vs EMP-069 Gibbs artifact')
    ax.set_ylim(-0.02, 0.5); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig('adler_ceiling_corrected_vs_emp069.png', dpi=115)
    print("saved adler_ceiling_corrected_vs_emp069.png")

    # Also directly show the density non-periodicity error magnitude for a specific case
    print()
    print("=== Density check: periodicity violation of EMP-069's Gibbs form ===")
    th = np.linspace(0,2*np.pi,9)
    for dw,K,sig in [(3.0,2.0,0.1),(6.0,2.0,0.2)]:
        D = 0.5*sig**2
        g = (dw*th + 2*K*np.cos(th))/D
        print(f"dw={dw},K={K},sig={sig}: p_gibbs(0)/p_gibbs(2pi) = {np.exp(g[0]-g[-1]):.3e}  (should be 1 for periodic!)")
