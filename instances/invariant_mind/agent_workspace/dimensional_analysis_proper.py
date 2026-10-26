"""
Proper Lorenz Dimensional Analysis: Lyapunov exponent + Correlation dimension.
Self-contained, dependency-light (numpy + matplotlib only).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

SIGMA, RHO, BETA = 10.0, 28.0, 8.0/3.0

def lorenz_field(state, sigma=SIGMA, rho=RHO, beta=BETA):
    x, y, z = state
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y - beta*z])

def integrate_lorenz_rk4(initial_state, dt=0.001, t_total=50.0, sigma=SIGMA, rho=RHO, beta=BETA):
    n_steps = int(t_total/dt)
    states = np.zeros((n_steps, 3))
    state = np.array(initial_state, dtype=float)
    for i in range(n_steps):
        states[i] = state
        k1 = lorenz_field(state, sigma, rho, beta)
        k2 = lorenz_field(state + 0.5*dt*k1, sigma, rho, beta)
        k3 = lorenz_field(state + 0.5*dt*k2, sigma, rho, beta)
        k4 = lorenz_field(state + dt*k3, sigma, rho, beta)
        state = state + dt/6.0*(k1 + 2*k2 + 2*k3 + k4)
    return states

def jacobian_lorenz(state, sigma=SIGMA, rho=RHO, beta=BETA):
    x, y, z = state
    return np.array([[-sigma, sigma, 0.0],
                     [rho - z, -1.0, -x],
                     [y, x, -beta]])

def benettin_lambda_max(traj, dt, transient=0, n_iter=None):
    """Benettin algorithm with Gram-Schmidt (QR) renormalization each step."""
    if n_iter is None:
        n_iter = len(traj) - transient - 1
    Q = np.eye(3)
    log_sum = np.zeros(3)
    for i in range(transient, transient + n_iter):
        J = jacobian_lorenz(traj[i])
        # propagate tangent basis with one Euler step of variational eq
        Q = Q + dt * (J @ Q)
        Q, R = np.linalg.qr(Q)
        diag = np.abs(np.diag(R))
        diag = np.where(diag > 1e-300, diag, 1e-300)
        log_sum += np.log(diag)
    lam = log_sum / (n_iter * dt)
    return lam  # vector of 3 exponents

def correlation_sum(traj, n_r=40):
    """Grassberger-Procaccia correlation sum C(r) using a subsample."""
    N = len(traj)
    idx = np.linspace(0, N-1, min(N, 4000)).astype(int)
    X = traj[idx]
    # pairwise distances
    diff = X[:, None, :] - X[None, :, :]
    d = np.sqrt((diff**2).sum(-1))
    iu = np.triu_indices(len(X), k=1)
    dists = d[iu]
    rmin, rmax = dists.min(), dists.max()
    rs = np.logspace(np.log10(rmin*1.2), np.log10(rmax*0.5), n_r)
    C = np.array([(dists < r).mean() for r in rs])
    return rs, C

def correlation_dimension(traj):
    rs, C = correlation_sum(traj)
    mask = (C > 0) & (C < 1)
    if mask.sum() < 3:
        return 0.0, rs, C
    lr = np.log(rs[mask]); lC = np.log(C[mask])
    # robust slope via mid-range fit
    k = len(lr)
    a, b = k//4, 3*k//4
    if b - a < 2:
        a, b = 0, k
    slope = np.polyfit(lr[a:b], lC[a:b], 1)[0]
    return float(slope), rs, C

def main():
    print("Performing Proper Dimensional Analysis in World C:")
    scale_factors = np.logspace(-0.5, 0.5, 5)  # sigma scaling
    results = []
    for sf in scale_factors:
        sigma = SIGMA * sf
        init = np.array([1.0, 1.0, 1.0])
        traj = integrate_lorenz_rk4(init, dt=0.002, t_total=60.0, sigma=sigma)
        traj_clean = traj[5000:]  # drop transient
        lams = benettin_lambda_max(traj_clean, dt=0.002, n_iter=min(len(traj_clean)-1, 8000))
        D2, rs, C = correlation_dimension(traj_clean)
        results.append({'sf': float(sf), 'sigma': float(sigma),
                        'lambda_max': float(lams[0]), 'lambda_full': lams.tolist(),
                        'D2': float(D2)})
        print(f"scale={sf:.3f} sigma={sigma:.2f} lambda_max={lams[0]:+.4f} D2={D2:.4f}")

    with open('dimensional_analysis_proper.json', 'w') as f:
        json.dump(results, f, indent=2)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    sf = [r['sf'] for r in results]
    axes[0].semilogx(sf, [r['lambda_max'] for r in results], 'o-', lw=2, ms=8, color='#1f77b4')
    axes[0].set_xlabel('Sigma scaling factor'); axes[0].set_ylabel(r'$\lambda_{max}$')
    axes[0].set_title('Maximal Lyapunov Exponent vs Parameter Scaling')
    axes[0].grid(True, which='both', alpha=0.25); axes[0].axhline(0, color='k', lw=0.6, ls='--')

    axes[1].semilogx(sf, [r['D2'] for r in results], 's-', lw=2, ms=8, color='#2ca02c')
    axes[1].set_xlabel('Sigma scaling factor'); axes[1].set_ylabel(r'$D_2$ (correlation dimension)')
    axes[1].set_title('Correlation Dimension vs Parameter Scaling')
    axes[1].grid(True, which='both', alpha=0.25); axes[1].axhline(2.06, color='r', lw=1, ls=':', label='Kaplan-Yorke ~2.06')
    axes[1].legend()
    plt.tight_layout(); plt.savefig('dimensional_analysis_proper.png', dpi=200); plt.close()
    print("DONE")

if __name__ == '__main__':
    main()
