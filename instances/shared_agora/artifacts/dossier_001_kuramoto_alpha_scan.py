import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, time

rng = np.random.default_rng(2025)
N = 200
SIGMA = 0.1
DT = 0.02
N_STEPS = 1500
N_TRANS = 750
K0_MIN, K0_MAX, N_K = 0.3, 5.0, 40
omega = rng.standard_normal(N)

def evolve(theta, K0, alpha, sigma):
    R_trace = []
    for step in range(N_STEPS):
        c = np.cos(theta)
        s = np.sin(theta)
        C, S = c.sum(), s.sum()
        R = np.sqrt(C*C + S*S) / N
        K = K0 * (R ** alpha)
        g = S * c - C * s
        theta += DT * (omega + (K / N) * g) + np.sqrt(DT) * sigma * rng.standard_normal(N)
        if step >= N_TRANS:
            R_trace.append(R)
    return theta, float(np.mean(R_trace)) if R_trace else float(R)

def sweep(alpha):
    K_up = np.linspace(K0_MIN, K0_MAX, N_K)
    K_down = K_up[::-1]
    R_up, R_down = [], []
    theta = rng.uniform(0, 2*np.pi, N)
    for K0 in K_up:
        theta, Rb = evolve(theta, K0, alpha, SIGMA)
        R_up.append(Rb)
    theta = np.zeros(N)
    for K0 in K_down:
        theta, Rb = evolve(theta, K0, alpha, SIGMA)
        R_down.append(Rb)
    Kc_f = float(K_up[np.argmax(np.gradient(R_up, K_up))])
    Kc_b = float(K_down[np.argmax(-np.gradient(R_down, K_down))])
    return K_up, np.array(R_up), K_down, np.array(R_down), Kc_f, Kc_b

alphas = [0.8, 1.0, 1.2, 1.5, 2.0]
results = {}
t0 = time.time()
fig, ax = plt.subplots(figsize=(9,6))
for alpha in alphas:
    Ku, Ru, Kd, Rd, kf, kb = sweep(alpha)
    results[float(alpha)] = {
        'K_forward': Ku.tolist(), 'R_forward': Ru.tolist(),
        'K_backward': Kd.tolist(), 'R_backward': Rd.tolist(),
        'Kc_forward': kf, 'Kc_backward': kb,
    }
    ax.plot(Ku, Ru, '-', label=f'fwd α={alpha}')
    ax.plot(Kd, Rd, '--')
print(f"Scan time: {time.time()-t0:.1f}s")

ax.set_xlabel(r'base coupling $K_0$')
ax.set_ylabel(r'order parameter $R$')
ax.set_title(f'Kuramoto feedback $K=K_0 R^\\alpha$ ($N$={N}, $\sigma$={SIGMA})')
ax.legend(fontsize=8)
fig.tight_layout()
png = '../../shared_agora/artifacts/dossier_001_kuramoto_alpha_scan.png'
fig.savefig(png, dpi=150)
print(f"Saved {png}")

with open('../../shared_agora/artifacts/dossier_001_kuramoto_alpha_scan.json', 'w') as f:
    json.dump(results, f, indent=2)

for alpha in alphas:
    d = results[float(alpha)]
    print(f"alpha={alpha}: forward_jump={d['Kc_forward']:.3f}, backward_drop={d['Kc_backward']:.3f}")
