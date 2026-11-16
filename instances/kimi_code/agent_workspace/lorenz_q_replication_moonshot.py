import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os, time

# ---------------------------------------------------------------------------
# Independent replication of EMP-226 Lorenz Q-metric sweep
# Q(K=0) = -(lambda_max + D2)
# ---------------------------------------------------------------------------

sigma = 10.0
beta = 8.0 / 3.0
dt = 0.01
burn_steps = int(1000 / dt)      # 100 time units
meas_steps = int(500 / dt)       # 50 time units
renorm_every = 10

def rhs(X, rho):
    x, y, z = X
    return np.array([sigma * (y - x),
                     x * (rho - z) - y,
                     x * y - beta * z])

def jac(X, rho):
    x, y, z = X
    return np.array([[-sigma, sigma, 0.0],
                     [rho - z, -1.0, -x],
                     [y, x, -beta]])

def step_rk4(X, v, rho):
    k1 = rhs(X, rho)
    J1 = jac(X, rho)
    kv1 = J1 @ v

    X2 = X + 0.5 * dt * k1
    k2 = rhs(X2, rho)
    J2 = jac(X2, rho)
    kv2 = J2 @ (v + 0.5 * dt * kv1)

    X3 = X + 0.5 * dt * k2
    k3 = rhs(X3, rho)
    J3 = jac(X3, rho)
    kv3 = J3 @ (v + 0.5 * dt * kv2)

    X4 = X + dt * k3
    k4 = rhs(X4, rho)
    J4 = jac(X4, rho)
    kv4 = J4 @ (v + dt * kv3)

    Xnew = X + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    vnew = v + dt / 6.0 * (kv1 + 2 * kv2 + 2 * kv3 + kv4)
    return Xnew, vnew

def largest_lyapunov(rho):
    X = np.array([1.0, 1.0, 1.0], dtype=float)
    # burn-in
    for _ in range(burn_steps):
        k1 = rhs(X, rho)
        k2 = rhs(X + 0.5 * dt * k1, rho)
        k3 = rhs(X + 0.5 * dt * k2, rho)
        k4 = rhs(X + dt * k3, rho)
        X += dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)

    v = np.array([1.0, 0.0, 0.0], dtype=float)
    lyap_sum = 0.0
    for i in range(meas_steps):
        X, v = step_rk4(X, v, rho)
        if i % renorm_every == 0:
            norm = np.linalg.norm(v)
            lyap_sum += np.log(norm)
            v /= norm
    # total measurement time = meas_steps * dt
    return lyap_sum / (meas_steps * dt)

def correlation_dimension(series, m=5, tau_steps=15, w=20):
    """
    Grassberger-Procaccia correlation dimension from a scalar time series.
    series : 1D array (already after burn-in)
    m      : embedding dimension
    tau_steps : delay in samples
    w      : Theiler window
    """
    N = len(series)
    # embed
    M = N - (m - 1) * tau_steps
    Y = np.zeros((M, m))
    for k in range(m):
        Y[:, k] = series[k * tau_steps:k * tau_steps + M]

    # radii
    chunk = 512
    # sample a subset for min/max estimation
    idx = np.random.default_rng(0).choice(M, size=min(M, 2000), replace=False)
    samp = Y[idx]
    dmax = np.max(np.max(samp, axis=0) - np.min(samp, axis=0))
    rmin = 1e-4
    rmax = dmax
    radii = np.geomspace(max(rmin, 1e-4), rmax, 60)

    counts = np.zeros(len(radii), dtype=np.float64)
    total_pairs = 0
    for start in range(0, M, chunk):
        end = min(start + chunk, M)
        D = np.linalg.norm(Y[start:end, None, :] - Y[None, :, :], axis=2)
        # Theiler window mask: keep pairs with |i-j| > w
        i_idx = np.arange(start, end)[:, None]
        j_idx = np.arange(M)[None, :]
        mask = (np.abs(i_idx - j_idx) > w)
        for ri, r in enumerate(radii):
            counts[ri] += np.count_nonzero((D < r) & mask)
        total_pairs += np.count_nonzero(mask)

    C = counts / total_pairs
    # fit scaling region with highest R^2 over contiguous windows
    logr = np.log(radii)
    logC = np.log(C + 1e-12)
    best_d2 = np.nan
    best_r2 = -1.0
    window = 12
    for a in range(len(radii) - window):
        b = a + window
        # require monotonic increase and within reasonable C range
        if np.any(np.diff(logC[a:b]) <= 0):
            continue
        slope, intercept = np.polyfit(logr[a:b], logC[a:b], 1)
        pred = slope * logr[a:b] + intercept
        ss_res = np.sum((logC[a:b] - pred) ** 2)
        ss_tot = np.sum((logC[a:b] - np.mean(logC[a:b])) ** 2)
        r2 = 1 - ss_res / (ss_tot + 1e-12)
        if 0 < slope < m and r2 > best_r2:
            best_r2 = r2
            best_d2 = slope
    return float(best_d2)

def estimate(rho):
    lam = largest_lyapunov(rho)
    if lam <= 0:
        return {'rho': rho, 'lambda_max': float(lam), 'D2': None, 'Q': None, 'regime': 'non-chaotic'}
    # re-integrate and store trajectory for D2 (short run is enough)
    X = np.array([1.0, 1.0, 1.0], dtype=float)
    for _ in range(burn_steps):
        k1 = rhs(X, rho)
        k2 = rhs(X + 0.5 * dt * k1, rho)
        k3 = rhs(X + 0.5 * dt * k2, rho)
        k4 = rhs(X + dt * k3, rho)
        X += dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    traj = np.zeros((meas_steps, 3))
    for i in range(meas_steps):
        k1 = rhs(X, rho)
        k2 = rhs(X + 0.5 * dt * k1, rho)
        k3 = rhs(X + 0.5 * dt * k2, rho)
        k4 = rhs(X + dt * k3, rho)
        X += dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        traj[i] = X
    # downsample for D2 to reduce temporal correlation
    x_series = traj[::4, 0]  # dt_eff = 0.04
    d2 = correlation_dimension(x_series, m=5, tau_steps=4, w=10)
    Q = -(lam + d2)
    return {'rho': rho, 'lambda_max': float(lam), 'D2': d2, 'Q': float(Q), 'regime': 'chaotic'}

if __name__ == '__main__':
    rhos = [14, 22, 28, 35, 50]
    results = []
    for rho in rhos:
        t0 = time.time()
        res = estimate(rho)
        res['time_seconds'] = round(time.time() - t0, 2)
        results.append(res)
        print(res)

    os.makedirs('../../shared_agora/artifacts', exist_ok=True)
    json_path = '../../shared_agora/artifacts/lorenz_q_replication_moonshot.json'
    with open(json_path, 'w') as f:
        json.dump({'dt': dt, 'burn': burn_steps * dt, 'meas': meas_steps * dt,
                   'results': results}, f, indent=2)

    fig, ax = plt.subplots(figsize=(6, 4))
    chaotic = [r for r in results if r['regime'] == 'chaotic']
    ax.plot([r['rho'] for r in chaotic], [r['Q'] for r in chaotic], 'o-', label='Q = -(λ_max + D2)')
    ax.axhline(-3, color='gray', ls='--', label='O(1) ≈ -3')
    ax.set_xlabel('ρ')
    ax.set_ylabel('Q')
    ax.set_title('Moonshot replication: Lorenz Q-metric ρ-sweep')
    ax.legend()
    png_path = '../../shared_agora/artifacts/lorenz_q_replication_moonshot.png'
    fig.savefig(png_path, dpi=150)
    print('saved', png_path, json_path)
