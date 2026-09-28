"""
Independent verification of the periodic FP solution of the noisy Adler equation.

Equation: dtheta/dt = dw - 2K sin(theta) + sigma * xi(t)

The Fokker-Planck stationary density on the circle for dw != 0 is the
PERIODIC constant-flux solution, NOT a Gibbs equilibrium. Its Fourier
coefficients satisfy c_{n+1} = a_n c_n + c_{n-1}, a_n = (dw - i D n)/(i K),
and R = |<e^{i theta}>| = |c_1/c_0|.  We compute c_1/c_0 via the Miller
backward continued fraction, vectorized over (dw, K).

Target (EMP-082): band_frac_max should be monotone non-decreasing in sigma:
  sigma=0.00 -> ~0.4145, 0.05 -> ~0.4145, ..., 0.80 -> ~0.4694
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def R_continued(dw, K, D, NMAX=2000):
    """Vectorized R=|c_1/c_0| for the noisy Adler eq via backward continued fraction.

    dw, K, D can be arrays (broadcast).  D = sigma^2/2.
    x_n = c_n / c_{n-1},  x_n = 1/(x_{n+1} - a_n),  a_n = (dw - i D n)/(i K).
    """
    dw = np.asarray(dw, dtype=np.complex128)
    K = np.asarray(K, dtype=np.complex128)
    D = np.asarray(D, dtype=np.complex128)
    # broadcast
    bshape = np.broadcast(dw, K, D).shape
    dw, K, D = np.broadcast_arrays(dw, K, D)

    # x at n=NMAX+1 = 0
    x = np.zeros(dw.shape, dtype=np.complex128)
    for n in range(NMAX, 0, -1):
        a_n = (dw - 1j * D * n) / (1j * K)
        x = 1.0 / (x - a_n)
    return np.abs(x)  # |c_1/c_0|


def R_monte_carlo(dw, K, sigma, n_walkers=4000, T=60.0, dt=0.005, seed=0):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2*np.pi, n_walkers)
    n_steps = int(T/dt)
    for _ in range(n_steps):
        theta += (dw - 2*K*np.sin(theta))*dt + sigma*np.sqrt(dt)*rng.standard_normal(n_walkers)
    return abs(np.exp(1j*theta).mean())


def band_frac_for_sigma(sigma, Omega_max=6.0, band=(0.3, 0.7), Kgrid=None):
    D = sigma**2 / 2.0
    if Kgrid is None:
        Kgrid = np.linspace(0.5, 4.0, 40)
    dW = np.linspace(-Omega_max, Omega_max, 201)
    best = 0.0
    bestK = None
    for K in Kgrid:
        Rvals = R_continued(dW, K, D)
        bf = np.mean((Rvals >= band[0]) & (Rvals <= band[1]))
        if bf > best:
            best = bf
            bestK = K
    return best, bestK


if __name__ == "__main__":
    print("=== Step 1: Cross-check continued-fraction FP vs Monte-Carlo ===")
    for (dw, K, sigma) in [(3, 2, 0.1), (6, 2, 0.2), (2, 3, 0.5)]:
        D = sigma**2/2
        R_cf = R_continued(dw, K, D)
        R_mc = R_monte_carlo(dw, K, sigma)
        print(f"  dw={dw}, K={K}, sigma={sigma}:  R_CF={R_cf:.4f}   R_MC={R_mc:.4f}   diff={abs(R_cf-R_mc):.4f}")

    print("\n=== Step 2: band_frac_max vs sigma (Omega_max=6, band=[0.3,0.7]) ===")
    sigmas = [0.00, 0.05, 0.10, 0.20, 0.30, 0.50, 0.80]
    rows = []
    for sig in sigmas:
        bf, bK = band_frac_for_sigma(sig)
        rows.append((sig, bf, bK))
        print(f"  sigma={sig:.2f} -> band_frac_max={bf:.4f}  (K*={bK:.2f})")

    print("\n=== EMP-082 reference (for comparison) ===")
    ref = [(0.00,0.4145),(0.05,0.4145),(0.10,0.4145),(0.20,0.4145),(0.30,0.4170),(0.50,0.4295),(0.80,0.4694)]
    for (sig, r) in ref:
        print(f"  sigma={sig:.2f} -> ref={r:.4f}")

    # Figure
    fig, ax = plt.subplots(1, 1, figsize=(7, 5))
    sigs = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    refs = [r[1] for r in ref]
    ax.plot(sigs, vals, 'o-', label='my periodic-FP verification')
    ax.plot(sigs, refs, 's--', label='EMP-082 reference')
    ax.set_xlabel('noise sigma')
    ax.set_ylabel('band_frac_max')
    ax.set_title('Noisy Adler: band_frac_max vs noise (periodic FP)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('adler_periodic_verification.png', dpi=120)
    print("\nSaved adler_periodic_verification.png")
