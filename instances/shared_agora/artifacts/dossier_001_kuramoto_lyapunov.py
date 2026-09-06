import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, time

rng = np.random.default_rng(2025)
N = 200
ALPHA = 2.0
DT = 0.02
T_TRANS = 80.0
T_MEAS = 120.0
N_TRANS = int(T_TRANS / DT)
N_MEAS = int(T_MEAS / DT)
omega = rng.standard_normal(N)

def integrate(theta, K0, n_steps):
    for _ in range(n_steps):
        c = np.cos(theta)
        s = np.sin(theta)
        C, S = c.sum(), s.sum()
        R = np.sqrt(C*C + S*S) / N
        K = K0 * (R ** ALPHA)
        g = S * c - C * s
        theta += DT * (omega + (K / N) * g)
    return theta

def lyapunov_nontrivial(K0):
    theta = rng.uniform(0, 2*np.pi, N)
    theta = integrate(theta, K0, N_TRANS)
    w = rng.standard_normal(N)
    w -= w.mean()
    nrm = np.linalg.norm(w)
    w /= nrm
    lyap_sum = 0.0
    for _ in range(N_MEAS):
        c = np.cos(theta)
        s = np.sin(theta)
        C, S = c.sum(), s.sum()
        R = np.sqrt(C*C + S*S) / N
        K = K0 * (R ** ALPHA)
        g = S * c - C * s
        B = C * c + S * s
        # state step
        theta += DT * (omega + (K / N) * g)
        # tangent step (includes derivative of K=R^2 feedback)
        cw, sw, gw = np.dot(c, w), np.dot(s, w), np.dot(g, w)
        Jw = (K / N) * (c * cw + s * sw - B * w) + (2.0 * K0 / (N * N)) * g * gw
        w += DT * Jw
        w -= w.mean()  # project out rotational zero mode
        nrm = np.linalg.norm(w)
        lyap_sum += np.log(nrm)
        w /= nrm
    return lyap_sum / T_MEAS

if __name__ == '__main__':
    K0s = np.linspace(1.0, 4.5, 16)
    lambdas = []
    t0 = time.time()
    for K0 in K0s:
        lam = lyapunov_nontrivial(K0)
        lambdas.append(lam)
        print(f"K0={K0:.3f}, lambda_max_perp={lam:.5f}")
    print(f"Lyapunov scan time: {time.time()-t0:.1f}s")

    with open('../../shared_agora/artifacts/dossier_001_kuramoto_lyapunov.json', 'w') as f:
        json.dump({'K0': K0s.tolist(), 'lambda_perp': lambdas}, f, indent=2)

    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(K0s, lambdas, 'o-')
    ax.axhline(0.0, color='k', ls='--', alpha=0.4)
    ax.set_xlabel(r'base coupling $K_0$')
    ax.set_ylabel(r'maximal nontrivial Lyapunov exponent')
    ax.set_title(f'Deterministic Kuramoto feedback $K=K_0 R^{ALPHA}$ ($N$={N})')
    fig.tight_layout()
    png = '../../shared_agora/artifacts/dossier_001_kuramoto_lyapunov.png'
    fig.savefig(png, dpi=150)
    print(f"Saved {png}")
