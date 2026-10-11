#!/usr/bin/env python3
"""
CRITICAL OPEN QUESTION (from EMP-133): Is there a TRUE BARRIER at very large alpha?
At alpha=2.4, 2.6 no seeds locked within T=200. Two hypotheses:
  (A) SLOW-LOCK: escape-time law holds; t_esc just becomes enormous -> barrier is an
      illusion; eventually locks given enough T.
  (B) TRUE BARRIER: escape-time law BREAKS; there is a genuine frozen state that
      never locks even as T -> infinity.

Test: For alpha in [2.0, 2.2, 2.4, 2.6, 2.8, 3.0], run LONG integration (T up to 2000)
and see if lock fraction monotonically increases (slow-lock A) or plateaus below 1 (B).
Also track whether t_esc continues to follow the escape-time law.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_escape_time(N, alpha, K0, T_max, R_lock=0.5, seed=1, dt=0.02, omega_scale=1.0):
    r = np.random.default_rng(seed)
    omega = r.uniform(-omega_scale, omega_scale, N)
    theta = r.uniform(0, 2*np.pi, N)
    R0 = abs(np.mean(np.exp(1j*theta)))
    nt = int(T_max/dt)
    for k in range(nt):
        Z = np.mean(np.exp(1j*theta))
        R = abs(Z); psi = np.angle(Z)
        K = K0 * R**alpha
        theta += dt * (omega + K * np.sin(psi - theta))
        if k % 30 == 0:
            R = abs(np.mean(np.exp(1j*theta)))
            if R >= R_lock:
                return k*dt, R0, True
    return T_max, R0, False

N = 400
K0 = 5.0
alphas = [2.0, 2.2, 2.4, 2.6, 2.8, 3.0]
horizons = [100, 500, 1000, 2000]
nseeds = 6

print("Long-T test: slow-lock (A) vs true-barrier (B)")
print("For each alpha, lock fraction as T grows (N=400, K0=5, R_lock=0.5, 6 seeds)")
print(f"{'alpha':>6} " + "".join([f"{'T='+str(T):>8}" for T in horizons]))
print("-" * 60)

grid = np.zeros((len(alphas), len(horizons)))
for i, a in enumerate(alphas):
    row = []
    for j, T in enumerate(horizons):
        locks = 0
        for s in range(nseeds):
            te, R0, locked = kuramoto_escape_time(N, a, K0, T, seed=100*s+int(a*10))
            if locked:
                locks += 1
        grid[i, j] = locks / nseeds
        row.append(f"{locks/nseeds:8.2f}")
    print(f"{a:6.2f} " + "".join(row))

print("\nInterpretation:")
for i, a in enumerate(alphas):
    trend = grid[i]
    increasing = all(trend[j] <= trend[j+1] + 1e-9 for j in range(len(trend)-1))
    saturates_below_1 = trend[-1] < 1.0
    print(f"  alpha={a}: {trend}  monotonic_increase={increasing}, saturates_below_1={saturates_below_1}")
    if increasing and not saturates_below_1:
        print(f"      => SLOW-LOCK (escape-horizon holds; no true barrier)")
    elif not increasing:
        print(f"      => NON-MONOTONIC (noise or complex dynamics)")
    elif saturates_below_1:
        print(f"      => possible TRUE BARRIER (never locks even at T=2000)")

# Plot lock fraction vs alpha for each T
fig, ax = plt.subplots(figsize=(9, 6))
colors = plt.cm.plasma(np.linspace(0, 0.9, len(horizons)))
for j, T in enumerate(horizons):
    ax.plot(alphas, grid[:, j], 'o-', color=colors[j], label=f'T={T}')
ax.axhline(1.0, color='gray', ls=':', label='P(lock)=1')
ax.set_xlabel('alpha')
ax.set_ylabel('P(lock by T)')
ax.set_title(f'True barrier test: slow-lock (A) vs barrier (B)\nN={N}, K0={K0}, 6 seeds')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('shared_agora/artifacts/true_barrier_test.png', dpi=200, bbox_inches='tight')
plt.close()
print("\nSaved true_barrier_test.png")
