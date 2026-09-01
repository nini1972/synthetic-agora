"""EMP-030 candidate: Independent two-population Kuramoto measurement of the
multi-timescale resonance-gap order parameter R_cross(Delta_omega)."""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def simulate(dw, sigma_w=0.05, K=2.0, N1=100, N2=100, dt=0.05,
             T_trans=200.0, T_meas=400.0, seed=0, use_feedback=False):
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
    cosA = 0.0
    sinA = 0.0
    cosB = 0.0
    sinB = 0.0
    for _ in range(n_meas):
        z = sinT.sum() + 1j * cosT.sum()
        R = np.abs(z) / N
        Keff = (K * R ** 2) if use_feedback else K
        coup = Keff * np.imag(z * np.exp(-1j * theta)) / N
        theta = theta + dt * (omega + coup)
        sinT = np.sin(theta)
        cosT = np.cos(theta)
        cA = cosT[:N1].sum()
        sA = sinT[:N1].sum()
        cB = cosT[N1:].sum()
        sB = sinT[N1:].sum()
        cosA += cA
        sinA += sA
        cosB += cB
        sinB += sB
    nA = N1
    nB = N2
    R_A = np.hypot(cosA, sinA) / (nA * n_meas)
    R_B = np.hypot(cosB, sinB) / (nB * n_meas)
    R_cross = np.sqrt(R_A * R_B)
    return R_cross, R_A, R_B


def sliding_gamma(dw_arr, R_arr, half=1.6):
    g = np.full(len(dw_arr), np.nan)
    for i, dw in enumerate(dw_arr):
        mask = (dw_arr >= dw - half) & (dw_arr <= dw + half)
        xs = np.log(dw_arr[mask])
        ys = np.log(R_arr[mask])
        if len(xs) >= 4:
            A = np.vstack([xs, np.ones_like(xs)]).T
            coef, *_ = np.linalg.lstsq(A, ys, rcond=None)
            g[i] = -coef[0]
    return g


def main():
    dws = np.round(np.arange(0.1, 3.05, 0.1), 2)
    sigma_w = 0.05
    K = 2.0
    R_all = []
    for seed in range(3):
        Rr = []
        for dw in dws:
            Rc, _, _ = simulate(dw, sigma_w=sigma_w, K=K, seed=seed)
            Rr.append(Rc)
        R_all.append(Rr)
    R_all = np.array(R_all)
    R_mean = R_all.mean(axis=0)
    R_std = R_all.std(axis=0)

    mask = dws >= 0.5
    xs = np.log(dws[mask])
    ys = np.log(R_mean[mask])
    A = np.vstack([xs, np.ones_like(xs)]).T
    coef, *_ = np.linalg.lstsq(A, ys, rcond=None)
    gamma_global = -coef[0]
    print(f"GLOBAL gamma fit (dw>=0.5): {gamma_global:.3f}  intercept={coef[1]:.3f}")
    print(f"R_mean[first 6] (dw 0.1..0.6): {np.round(R_mean[:6],3)}")

    g_local = sliding_gamma(dws, R_mean, half=1.6)

    with open("resonance_gap_results.csv", "w") as f:
        f.write("dw,R_mean,R_std,gamma_local\n")
        for i, dw in enumerate(dws):
            gl = g_local[i]
            f.write(f"{dw},{R_mean[i]:.4f},{R_std[i]:.4f}," +
                    (f"{gl:.3f}" if not np.isnan(gl) else "nan") + "\n")

    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    ax[0].plot(dws, R_mean, 'o-', color='navy')
    ax[0].fill_between(dws, R_mean - R_std, R_mean + R_std, alpha=0.2, color='navy')
    ax[0].set_xlabel(r'$\Delta\omega$')
    ax[0].set_ylabel(r'$R_{cross}$')
    ax[0].set_title('Two-pop cross order parameter')
    ax[0].grid(alpha=0.3)

    ax[1].loglog(dws, R_mean, 'o-', color='darkred')
    ax[1].set_xlabel(r'$\Delta\omega$')
    ax[1].set_ylabel(r'$R_{cross}$')
    ax[1].set_title(f'Log-log; global gamma={gamma_global:.2f}')
    ax[1].grid(alpha=0.3, which='both')

    ax[2].plot(dws, g_local, 's-', color='green')
    ax[2].axhline(gamma_global, ls='--', color='gray', label=f'global={gamma_global:.2f}')
    ax[2].set_xlabel(r'$\Delta\omega$')
    ax[2].set_ylabel(r'$\gamma_{local}$ (sliding)')
    ax[2].set_title('CRT-004 sliding-window local exponent')
    ax[2].legend()
    ax[2].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('resonance_gap_probe.png', dpi=130)
    print("SAVED resonance_gap_probe.png and resonance_gap_results.csv")


if __name__ == '__main__':
    main()
