import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, time

rng = np.random.default_rng(2025)
N = 200
ALPHA = 2.0
SIGMA = 0.1
DT = 0.02
T = 30.0           # integration time per K0
T_TRANS = 15.0     # discard transient
N_STEPS = int(T / DT)
N_TRANS = int(T_TRANS / DT)
K0_MIN, K0_MAX, N_K = 0.4, 4.0, 50

omega = rng.standard_normal(N)

def evolve(theta, K0, alpha, sigma, n_steps):
    R_trace = []
    for _ in range(n_steps):
        c = np.cos(theta)
        s = np.sin(theta)
        C = c.sum()
        S = s.sum()
        R = np.sqrt(C*C + S*S) / N
        K = K0 * (R ** alpha)
        g = S * c - C * s
        theta += DT * (omega + (K / N) * g) + np.sqrt(DT) * sigma * rng.standard_normal(N)
        if _ >= N_TRANS:
            R_trace.append(R)
    return theta, np.mean(R_trace) if R_trace else R

def sweep(direction='up'):
    if direction == 'up':
        K0s = np.linspace(K0_MIN, K0_MAX, N_K)
        theta = rng.uniform(0, 2*np.pi, N)
    else:
        K0s = np.linspace(K0_MAX, K0_MIN, N_K)
        theta = np.zeros(N)  # start locked
    Rs = []
    for K0 in K0s:
        theta, Rbar = evolve(theta, K0, ALPHA, SIGMA, N_STEPS)
        Rs.append(Rbar)
    return K0s, np.array(Rs)

if __name__ == '__main__':
    t0 = time.time()
    K_up, R_up = sweep('up')
    K_down, R_down = sweep('down')
    print(f"Sweep time: {time.time()-t0:.1f}s")

    # rough threshold estimates from the steepest slope
    dR_up = np.gradient(R_up, K_up)
    Kc_forward = K_up[np.argmax(dR_up)]
    dR_down = np.gradient(R_down, K_down)
    Kc_backward = K_down[np.argmax(-dR_down)]

    results = {
        'N': N, 'alpha': ALPHA, 'sigma': SIGMA, 'dt': DT, 'T': T, 'T_trans': T_TRANS,
        'K_forward': K_up.tolist(), 'R_forward': R_up.tolist(),
        'K_backward': K_down.tolist(), 'R_backward': R_down.tolist(),
        'Kc_forward_estimate': float(Kc_forward),
        'Kc_backward_estimate': float(Kc_backward),
    }
    with open('../../shared_agora/artifacts/dossier_001_kuramoto_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(K_up, R_up, 'o-', label='forward sweep', color='C0')
    ax.plot(K_down, R_down, 's-', label='backward sweep', color='C1')
    ax.axvline(Kc_forward, color='C0', ls='--', alpha=0.5)
    ax.axvline(Kc_backward, color='C1', ls='--', alpha=0.5)
    ax.set_xlabel(r'base coupling $K_0$')
    ax.set_ylabel(r'order parameter $R$')
    ax.set_title(f'Kuramoto with feedback $K=K_0 R^{ALPHA}$ ($N$={N}, $\sigma$={SIGMA})')
    ax.legend()
    fig.tight_layout()
    out_png = '../../shared_agora/artifacts/dossier_001_kuramoto_hysteresis.png'
    fig.savefig(out_png, dpi=150)
    print(f"Saved {out_png}")
    print(f"Forward jump ~ {Kc_forward:.3f}, backward drop ~ {Kc_backward:.3f}")
