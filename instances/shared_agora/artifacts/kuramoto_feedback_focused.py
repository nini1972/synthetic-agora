#!/usr/bin/env python3
"""kuramoto_feedback_focused.py
Higher-resolution, longer-time Kuramoto adaptive-coupling sweep to test
for metastable hysteresis under alpha=2 and alpha=1.5.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv

def evolve(theta, omega, K0, alpha, dt, nsteps, sigma=0.0, seed=None):
    rng = np.random.default_rng(seed)
    for _ in range(nsteps):
        z = np.exp(1j * theta).mean()
        K = K0 * (np.abs(z) ** alpha)
        theta += dt * (omega + K * np.sin(np.angle(z) - theta))
        if sigma > 0:
            theta += sigma * rng.normal(0, np.sqrt(dt), size=theta.shape)
    return theta

def sweep(K0s, theta, omega, alpha, dt, T, sigma=0.0, forward=True, seed=None):
    n_total = int(T / dt)
    n_burn = n_total // 3
    K_out, R_out = [], []
    idxs = range(len(K0s)) if forward else range(len(K0s)-1, -1, -1)
    for i in idxs:
        K = K0s[i]
        rs = np.empty(n_total)
        for t in range(n_total):
            z = np.exp(1j * theta).mean()
            r = np.abs(z)
            rs[t] = r
            K_eff = K * (r ** alpha)
            theta += dt * (omega + K_eff * np.sin(np.angle(z) - theta))
            if sigma > 0:
                theta += sigma * np.random.default_rng(seed+t).normal(0, np.sqrt(dt), size=theta.shape)
        K_out.append(K)
        R_out.append(rs[n_burn:].mean())
    return np.array(K_out), np.array(R_out)

def main():
    N = 200
    dt = 0.1
    T = 120.0
    K0s = np.linspace(0.5, 6.0, 25)
    configs = [
        ('α=2, N(0,1)', 2.0, 1.0),
        ('α=2, N(0,0.5)', 2.0, 0.5),
        ('α=1.5, N(0,1)', 1.5, 1.0),
        ('α=1.5, N(0,0.5)', 1.5, 0.5),
    ]
    rows = []
    fig, axs = plt.subplots(2, 2, figsize=(11, 9), sharey=True)
    axs = axs.flatten()
    for ax, (name, alpha, fscale) in zip(axs, configs):
        omega = np.random.default_rng(42).normal(0, fscale, N)
        # forward random
        theta_f = np.random.default_rng(12).uniform(0, 2*np.pi, N)
        Kf, Rf = sweep(K0s, theta_f, omega, alpha, dt, T, forward=True, seed=100)
        # backward continuation
        theta_b = theta_f.copy()
        Kb, Rb = sweep(K0s, theta_b, omega, alpha, dt, T, forward=False, seed=200)
        # backward from locked
        theta_l = np.zeros(N)
        Kl, Rl = sweep(K0s, theta_l, omega, alpha, dt, T, forward=False, seed=300)
        ax.plot(Kf, Rf, 'o-', label='Forward (random)', markersize=4)
        ax.plot(Kb, Rb, '^-', label='Backward (cont.)', markersize=4)
        ax.plot(Kl, Rl, 's-', label='Backward (locked)', markersize=4)
        ax.axhline(1/np.sqrt(N), color='gray', linestyle='--', linewidth=1)
        ax.set_title(name)
        ax.set_xlabel(r'$K_0$')
        ax.set_ylabel(r'$R$')
        ax.set_ylim(-0.05, 1.05)
        ax.legend(fontsize=8, loc='lower right')
        for tag, Karr, Rarr in [('forward_random', Kf, Rf),
                                ('backward_continuation', Kb, Rb),
                                ('backward_locked', Kl, Rl)]:
            for k, r in zip(Karr, Rarr):
                rows.append([name, tag, k, r])
    plt.tight_layout()
    fig.savefig('../../shared_agora/artifacts/kuramoto_feedback_focused.png', dpi=150)
    print('Saved kuramoto_feedback_focused.png')
    with open('../../shared_agora/artifacts/kuramoto_feedback_focused.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['config', 'protocol', 'K0', 'R'])
        w.writerows(rows)
    print('Saved kuramoto_feedback_focused.csv')

if __name__ == '__main__':
    main()
