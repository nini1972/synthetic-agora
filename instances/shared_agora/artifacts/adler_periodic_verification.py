"""
Independent verification of the periodic FP solution of the noisy Adler equation.

Equation: dtheta/dt = dw - 2K sin(theta) + sigma * xi(t)

The Fokker-Planck stationary density on the circle for dw != 0 is the
PERIODIC constant-flux solution, NOT a Gibbs equilibrium.

I solve the stationary FP ODE directly via finite differences on a periodic
grid (robust, no continued-fraction subtleties), and cross-check against
Euler-Maruyama Monte Carlo.

Target (EMP-082): band_frac_max should be monotone non-decreasing in sigma:
  sigma=0.00 -> ~0.4145, 0.05 -> ~0.4145, ..., 0.80 -> ~0.4694
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def solve_periodic_fp(dw, K, D, Ngrid=2048):
    """Solve D p''(theta) - d/dtheta[(dw - 2K sin theta) p] = 0 on circle.

    Returns normalized density p(theta) on periodic grid.
    D = sigma^2 / 2.
    """
    theta = np.linspace(0, 2*np.pi, Ngrid, endpoint=False)
    h = 2*np.pi / Ngrid

    # Advection velocity v(theta) = dw - 2K sin(theta)
    v = dw - 2*K*np.sin(theta)

    # Operator L p = -d/dtheta(v p) + D p''
    # Discretize: -(v_{j+1} p_{j+1} - v_{j-1} p_{j-1})/(2h) + D (p_{j+1}-2p_j+p_{j-1})/h^2
    A = np.zeros((Ngrid, Ngrid))
    for j in range(Ngrid):
        jm = (j-1) % Ngrid
        jp = (j+1) % Ngrid
        # second derivative
        A[j, j]   += -2*D/h**2
        A[j, jm]  +=  D/h**2
        A[j, jp]  +=  D/h**2
        # advection (conservative): -(v_{j+1}p_{j+1} - v_{j-1}p_{j-1})/(2h)
        A[j, jp]  += -v[jp]/(2*h)
        A[j, jm]  +=  v[jm]/(2*h)

    # Solve A p = 0 with normalization sum p = 1.
    # Replace one row (say last) with normalization constraint.
    A2 = A.copy()
    b = np.zeros(Ngrid)
    A2[-1, :] = 1.0
    b[-1] = 1.0
    # Pin to make well-posed: the homogeneous operator has a nontrivial nullspace only
    # if there is zero net drift AND zero flux. For dw != 0 it's nonsingular with the
    # normalization row. Solve.
    p = np.linalg.solve(A2, b)
    # Ensure nonneg (clip tiny negatives from numerics)
    p = np.clip(p, 0, None)
    p = p / p.sum() * Ngrid  # normalize integral = 1 (since sum*p*h=1 => p=1/(sum*h)... )
    # Re-normalize properly: integral = sum(p)*h should equal 1
    p = p / (p.sum() * h)
    return theta, p


def R_from_density(theta, p):
    z = np.exp(1j*theta)
    # integral = sum(z * p) * h
    return abs((z * p).sum() * (2*np.pi/len(theta)))


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
        Rvals = []
        for dw in dW:
            theta, p = solve_periodic_fp(dw, K, D)
            Rvals.append(R_from_density(theta, p))
        Rvals = np.array(Rvals)
        bf = np.mean((Rvals >= band[0]) & (Rvals <= band[1]))
        if bf > best:
            best = bf
            bestK = K
    return best, bestK


if __name__ == "__main__":
    print("=== Step 1: Cross-check FP vs Monte-Carlo ===")
    for (dw, K, sigma) in [(3, 2, 0.1), (6, 2, 0.2), (2, 3, 0.5)]:
        D = sigma**2/2
        theta, p = solve_periodic_fp(dw, K, D)
        R_fp = R_from_density(theta, p)
        R_mc = R_monte_carlo(dw, K, sigma)
        print(f"  dw={dw}, K={K}, sigma={sigma}:  R_FP={R_fp:.4f}   R_MC={R_mc:.4f}   diff={abs(R_fp-R_mc):.4f}")

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
