#!/usr/bin/env python3
"""
Careful independent verification of HYP-047: Lorenz attractor invariants.
Uses variational equations for Lyapunov spectrum and multi-scale box-counting.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def lorenz_rhs(state, sigma, beta, rho):
    x, y, z = state
    return np.array([sigma*(y-x), x*(rho-z)-y, x*y - beta*z])


def lorenz_variational(state, sigma, beta, rho):
    """Full variational: state is [x,y,z, V_flat(9)]"""
    x, y, z = state[0], state[1], state[2]
    dxdt = sigma*(y-x)
    dydt = x*(rho-z)-y
    dzdt = x*y - beta*z

    J = np.array([
        [-sigma, sigma, 0.0],
        [rho-z, -1.0, -x],
        [y, x, -beta]
    ])
    V = state[3:].reshape(3, 3)
    dV = J @ V
    return np.concatenate([[dxdt, dydt, dzdt], dV.flatten()])


def rk4(f, s, dt, *args):
    k1 = f(s, *args)
    k2 = f(s + 0.5*dt*k1, *args)
    k3 = f(s + 0.5*dt*k2, *args)
    k4 = f(s + dt*k3, *args)
    return s + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)


def lyapunov_spectrum(sigma, beta, rho, dt=0.005, T_trans=200, T_calc=500):
    """Benettin algorithm with QR reorthonormalization."""
    s = np.concatenate([[1.0, 1.0, 1.0], np.eye(3).flatten()])
    n_trans = int(T_trans / dt)
    for _ in range(n_trans):
        s = rk4(lorenz_variational, s, dt, sigma, beta, rho)
        s[3:] = np.eye(3).flatten()

    lyap_sum = np.zeros(3)
    n_renorm = 0
    steps_per = int(1.0 / dt)
    n_total = int(T_calc / dt)

    for step in range(n_total):
        s = rk4(lorenz_variational, s, dt, sigma, beta, rho)
        if (step + 1) % steps_per == 0:
            V = s[3:].reshape(3, 3)
            Q, R = np.linalg.qr(V)
            for i in range(3):
                lyap_sum[i] += np.log(abs(R[i, i]))
            s[3:] = Q.flatten()
            n_renorm += 1

    return np.sort(lyap_sum / (n_renorm * 1.0))[::-1]


def kaplan_yorke(lyaps):
    sly = np.sort(lyaps)[::-1]
    cs = np.cumsum(sly)
    for j in range(len(sly) - 1):
        if cs[j] + sly[j+1] < 0:
            return j + cs[j] / abs(sly[j+1])
    return float(len(sly))


def box_count_dim(traj, scales=None):
    if scales is None:
        scales = [0.3, 0.5, 1.0, 2.0, 4.0, 8.0]
    data = traj[::5]
    mn = np.min(data, axis=0)
    mx = np.max(data, axis=0)
    rng = mx - mn

    counts = []
    valid_scales = []
    for bs in scales:
        bins = np.maximum(np.ceil(rng / bs).astype(int), 1)
        idx = np.clip(np.floor((data - mn) / bs).astype(int), 0, bins - 1)
        n_boxes = len(set(map(tuple, idx)))
        if n_boxes > 10:
            counts.append(n_boxes)
            valid_scales.append(bs)

    if len(valid_scales) < 3:
        return float('nan')
    le = np.log(1.0 / np.array(valid_scales))
    ln = np.log(np.array(counts))
    slope, _ = np.polyfit(le, ln, 1)
    return slope


def main():
    sigma, beta = 10.0, 8.0/3.0
    rho_vals = [24, 26, 28, 30, 32]

    print("="*70)
    print("LORENZ INVARIANTS VERIFICATION (HYP-047)")
    print("dt=0.005, T_trans=200, T_calc=500, QR reorthonormalization")
    print("="*70)
    print()

    results = []
    for rho in rho_vals:
        print(f"rho = {rho} ...")
        lyaps = lyapunov_spectrum(sigma, beta, rho)
        D_KY = kaplan_yorke(lyaps)

        # Collect trajectory for box-counting
        s = np.array([1.0, 1.0, 1.0])
        for _ in range(int(200/0.005)):
            s = rk4(lorenz_rhs, s, 0.005, sigma, beta, rho)
        n = int(200/0.005)
        traj = np.zeros((n, 3))
        for i in range(n):
            s = rk4(lorenz_rhs, s, 0.005, sigma, beta, rho)
            traj[i] = s

        D_box = box_count_dim(traj)

        left = np.mean(traj[:, 0] < 0)
        right = np.mean(traj[:, 0] > 0)
        asym = left / right if right > 0 else float('inf')

        results.append(dict(rho=rho, l1=lyaps[0], l2=lyaps[1], l3=lyaps[2],
                            D_KY=D_KY, D_box=D_box, asym=asym))
        print(f"  lambda = ({lyaps[0]:.4f}, {lyaps[1]:.4f}, {lyaps[2]:.4f})")
        print(f"  D_KY = {D_KY:.4f}, D_box = {D_box:.3f}, asym = {asym:.4f}")
        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print(f"{'rho':>5}  {'l1':>8}  {'l2':>8}  {'l3':>8}  {'D_KY':>7}  {'D_box':>7}  {'asym':>7}")
    print("-"*60)
    for r in results:
        print(f"{r['rho']:5.0f}  {r['l1']:8.4f}  {r['l2']:8.4f}  {r['l3']:8.4f}  {r['D_KY']:7.4f}  {r['D_box']:7.3f}  {r['asym']:7.4f}")

    D_KY_vals = [r['D_KY'] for r in results]
    l1_vals = [r['l1'] for r in results]
    asym_vals = [r['asym'] for r in results]

    print()
    print("HYP-047 targets: D=2.06+/-0.01, l_max=0.9056+/-0.005, asym=1.00+/-0.05")
    print(f"Measured D_KY: {np.mean(D_KY_vals):.4f} +/- {np.std(D_KY_vals):.4f}")
    print(f"Measured l1:   {np.mean(l1_vals):.4f} +/- {np.std(l1_vals):.4f}")
    print(f"Measured asym: {np.mean(asym_vals):.4f} +/- {np.std(asym_vals):.4f}")

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    rhos = [r['rho'] for r in results]

    axes[0].plot(rhos, D_KY_vals, 'bo-', ms=8, label='Kaplan-Yorke (this work)')
    axes[0].axhline(2.06, color='r', ls='--', label='HYP-047: D=2.06')
    axes[0].set_xlabel('rho'); axes[0].set_ylabel('D_KY'); axes[0].legend(); axes[0].grid(alpha=0.3)

    axes[1].plot(rhos, l1_vals, 'bo-', ms=8, label='lambda_max (this work)')
    axes[1].axhline(0.9056, color='r', ls='--', label='HYP-047: 0.9056')
    axes[1].set_xlabel('rho'); axes[1].set_ylabel('lambda_max'); axes[1].legend(); axes[1].grid(alpha=0.3)

    axes[2].plot(rhos, asym_vals, 'bo-', ms=8, label='Wing asymmetry (this work)')
    axes[2].axhline(1.0, color='r', ls='--', label='HYP-047: 1.00')
    axes[2].set_xlabel('rho'); axes[2].set_ylabel('Asymmetry'); axes[2].legend(); axes[2].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('shared_agora/artifacts/lorenz_invariants_v2.png', dpi=150)
    print("\nPlot saved to shared_agora/artifacts/lorenz_invariants_v2.png")


if __name__ == '__main__':
    main()