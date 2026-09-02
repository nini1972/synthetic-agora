"""EMP-030 candidate: Independent two-population Kuramoto cross-locking probe.

Corrected cross order parameter:
  R_cross(dw) = | (1/T_meas) sum_t exp(i*(phi_A(t) - phi_B(t))) |
  where phi_A, phi_B are the centroid phases of the two ensembles.
This measures PHASE LOCKING between the two population centroids
(not internal coherence, which is trivially ~1 for tight clusters).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def simulate(dw, sigma_w=0.05, K=2.0, N1=100, N2=100, dt=0.05,
             T_trans=100.0, T_meas=200.0, seed=0, use_feedback=False):
    rng = np.random.default_rng(seed)
    N = N1 + N2
    omega = np.concatenate([
        dw / 2.0 + sigma_w * rng.standard_normal(N1),
        -dw / 2.0 + sigma_w * rng.standard_normal(N2),
    ])
    theta = rng.uniform(-np.pi, np.pi, N)
    n_trans = int(T_trans / dt)
    n_meas = int(T_meas / dt)
    sinT = np.sin(theta)
    cosT = np.cos(theta)
    for _ in range(n_trans):
        z = sinT.sum() + 1j * cosT.sum()
        R = np.abs(z) / N
        Keff = (K * R ** 2) if use_feedback else K
        coup = Keff * np.imag(z * np.exp(-1j * theta)) / N
        theta = theta + dt * (omega + coup)
        sinT = np.sin(theta)
        cosT = np.cos(theta)
    z_cross = 0.0 + 0.0j
    for _ in range(n_meas):
        z = sinT.sum() + 1j * cosT.sum()
        R = np.abs(z) / N
        Keff = (K * R ** 2) if use_feedback else K
        coup = Keff * np.imag(z * np.exp(-1j * theta)) / N
        theta = theta + dt * (omega + coup)
        sinT = np.sin(theta)
        cosT = np.cos(theta)
        zA = np.sum(np.exp(1j * theta[:N1]))
        zB = np.sum(np.exp(1j * theta[N1:]))
        phiA = np.angle(zA)
        phiB = np.angle(zB)
        z_cross += np.exp(1j * (phiA - phiB))
    R_cross = np.abs(z_cross) / n_meas
    return R_cross


def sliding_gamma(dw_arr, R_arr, half=0.5):
    g = np.full(len(dw_arr), np.nan)
    for i, dw in enumerate(dw_arr):
        mask = (dw_arr >= dw - half) & (dw_arr <= dw + half)
        xs = np.log(dw_arr[mask])
        ys = np.log(R_arr[mask] + 1e-9)
        if len(xs) >= 3:
            A = np.vstack([xs, np.ones_like(xs)]).T
            coef, *_ = np.linalg.lstsq(A, ys, rcond=None)
            g[i] = -coef[0]
    return g


def sweep(label, sigma_w, K, outcsv, dws=None):
    if dws is None:
        dws = np.round(np.arange(0.1, 3.05, 0.15), 2)
    R_all = []
    for seed in range(2):
        Rr = []
        for dw in dws:
            Rr.append(simulate(dw, sigma_w=sigma_w, K=K, seed=seed))
        R_all.append(Rr)
    R_all = np.array(R_all)
    R_mean = R_all.mean(axis=0)
    R_std = R_all.std(axis=0)
    mask = dws >= 0.5
    xs = np.log(dws[mask])
    ys = np.log(R_mean[mask] + 1e-9)
    A = np.vstack([xs, np.ones_like(xs)]).T
    coef, *_ = np.linalg.lstsq(A, ys, rcond=None)
    gamma_global = -coef[0]
    g_local = sliding_gamma(dws, R_mean, half=0.5)
    print(f"[{label}] GLOBAL gamma(dw>=0.5)={gamma_global:.3f}")
    print(f"[{label}] R_mean: {np.round(R_mean,3)}")
    with open(outcsv, "w") as f:
        f.write("dw,R_mean,R_std,gamma_local\n")
        for i, dw in enumerate(dws):
            gl = g_local[i]
            f.write(f"{dw},{R_mean[i]:.4f},{R_std[i]:.4f}," +
                    (f"{gl:.3f}" if not np.isnan(gl) else "nan") + "\n")
    return dws, R_mean, R_std, gamma_global, g_local


def main():
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    colors = {'strong_coherent': 'navy', 'weak': 'darkred', 'noisy_clusters': 'green'}
    for ax_i, (label, sigma_w, K) in enumerate([
            ('strong_coherent', 0.05, 2.0),
            ('weak', 0.05, 0.5),
            ('noisy_clusters', 0.30, 2.0)]):
        dws, Rm, Rs, gG, gl = sweep(label, sigma_w, K, f"rg_{label}.csv")
        ax[0].plot(dws, Rm, 'o-', color=colors[label], label=f'{label} g={gG:.2f}')
        ax[0].fill_between(dws, Rm - Rs, Rm + Rs, alpha=0.15, color=colors[label])
        ax[1].semilogy(dws, Rm, 'o-', color=colors[label], label=label)
        ax[2].plot(dws, gl, 's-', color=colors[label], label=label)
    ax[0].set_ylabel(r'$R_{cross}$ (centroid lock)')
    ax[0].set_xlabel(r'$\Delta\omega$')
    ax[0].set_title('Cross-locking order parameter'); ax[0].legend(); ax[0].grid(alpha=0.3)
    ax[1].set_ylabel(r'$R_{cross}$'); ax[1].set_xlabel(r'$\Delta\omega$')
    ax[1].set_title('Semilog'); ax[1].legend(); ax[1].grid(alpha=0.3, which='both')
    ax[2].set_ylabel(r'$\gamma_{local}$'); ax[2].set_xlabel(r'$\Delta\omega$')
    ax[2].set_title('Sliding-window local exponent'); ax[2].legend(); ax[2].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('resonance_gap_probe.png', dpi=130)
    print("SAVED resonance_gap_probe.png")


if __name__ == '__main__':
    main()
