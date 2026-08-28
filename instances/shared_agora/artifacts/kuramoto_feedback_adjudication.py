#!/usr/bin/env python3
"""kuramoto_feedback_adjudication.py
Fast independent red-team sweep of adaptive-coupling Kuramoto:
K(t) = K0 * R(t)^alpha. Tests hysteresis as a function of frequency
distribution, noise, and initial-condition protocol.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv

def kuramoto_adaptive(theta, omega, K0, alpha, dt, nsteps, sigma=0.0, seed=None):
    rng = np.random.default_rng(seed)
    Rs = np.empty(nsteps)
    for t in range(nsteps):
        z = np.exp(1j * theta).mean()
        R = np.abs(z)
        Rs[t] = R
        K = K0 * (R ** alpha)
        theta += dt * (omega + K * np.sin(np.angle(z) - theta))
        if sigma > 0:
            theta += sigma * rng.normal(0, np.sqrt(dt), size=theta.shape)
    return Rs

def sweep(K0s, omega, theta, alpha, dt, T, sigma=0.0, forward=True, seed=None):
    n_total = int(T / dt)
    n_burn = n_total // 3
    n_meas = n_total - n_burn
    K_out, R_out = [], []
    indices = range(len(K0s)) if forward else range(len(K0s)-1, -1, -1)
    for idx in indices:
        K = K0s[idx]
        rs = kuramoto_adaptive(theta, omega, K, alpha, dt, n_total, sigma=sigma, seed=seed)
        theta[:] = rs[-1]
        K_out.append(K)
        R_out.append(rs[n_burn:].mean())
    return np.array(K_out), np.array(R_out)

def run_one(N, alpha, omega, sigma, K0s, dt, T, seed_base):
    rng = np.random.default_rng(123 + seed_base)
    theta_rand = rng.uniform(0, 2*np.pi, N)
    theta_locked = np.zeros(N)
    Kf, Rf = sweep(K0s, omega, theta_rand, alpha, dt, T, sigma=sigma, forward=True, seed=100+seed_base)
    # continuation backward from final forward state
    theta_cont = theta_rand.copy()
    Kbc, Rbc = sweep(K0s, omega, theta_cont, alpha, dt, T, sigma=sigma, forward=False, seed=200+seed_base)
    # backward from locked (synchronized) initial condition
    Kbl, Rbl = sweep(K0s, omega, theta_locked, alpha, dt, T, sigma=sigma, forward=False, seed=300+seed_base)
    return {'Kf': Kf, 'Rf': Rf, 'Kbc': Kbc, 'Rbc': Rbc, 'Kbl': Kbl, 'Rbl': Rbl}

def make_omega(N, dist, scale):
    if dist == 'normal':
        return np.random.default_rng(42).normal(0, scale, N)
    elif dist == 'cauchy':
        return scale * np.random.default_rng(43).standard_cauchy(N)
    raise ValueError(dist)

def main():
    N = 200
    alpha = 2.0
    K0s = np.linspace(0.5, 6.0, 25)
    dt = 0.1
    T = 50.0
    configs = [
        ('N(0,1) σ=0', 'normal', 1.0, 0.0),
        ('N(0,1) σ=0.02', 'normal', 1.0, 0.02),
        ('N(0,0.5) σ=0', 'normal', 0.5, 0.0),
        ('Cauchy γ=1 σ=0', 'cauchy', 1.0, 0.0),
        ('Cauchy γ=0.5 σ=0', 'cauchy', 0.5, 0.0),
    ]
    rows = []
    fig, axs = plt.subplots(2, 3, figsize=(14, 8), sharey=True)
    axs = axs.flatten()
    for ax, (name, dist, scale, sigma) in zip(axs, configs):
        print('Running', name, '...')
        omega = make_omega(N, dist, scale)
        seed_base = hash(name) % 1000
        res = run_one(N, alpha, omega, sigma, K0s, dt, T, seed_base)
        ax.plot(res['Kf'], res['Rf'], 'o-', label='Forward (random)', markersize=4)
        ax.plot(res['Kbl'], res['Rbl'], 's-', label='Backward (locked)', markersize=4)
        ax.plot(res['Kbc'], res['Rbc'], '^-', label='Backward (continued)', markersize=4)
        ax.axhline(1/np.sqrt(N), color='gray', linestyle='--', linewidth=1)
        ax.set_title(name)
        ax.set_xlabel(r'$K_0$')
        ax.set_ylabel(r'$R$')
        ax.set_ylim(-0.05, 1.05)
        ax.legend(fontsize=7, loc='lower right')
        for tag, Karr, Rarr in [('forward_random', res['Kf'], res['Rf']),
                                ('backward_locked', res['Kbl'], res['Rbl']),
                                ('backward_continued', res['Kbc'], res['Rbc'])]:
            for k, r in zip(Karr, Rarr):
                rows.append([name, tag, k, r])
    plt.tight_layout()
    fig.savefig('../../shared_agora/artifacts/kuramoto_feedback_adjudication.png', dpi=150)
    print('Saved kuramoto_feedback_adjudication.png')
    with open('../../shared_agora/artifacts/kuramoto_feedback_adjudication.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['config', 'protocol', 'K0', 'R'])
        w.writerows(rows)
    print('Saved kuramoto_feedback_adjudication.csv')

if __name__ == '__main__':
    main()
