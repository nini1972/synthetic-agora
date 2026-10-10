#!/usr/bin/env python3
"""
DECISIVE FALSIFICATION TEST (from EMP-131 V4 / HYP-107):
    Does the measured alpha_c(N) boundary SHIFT with integration horizon T?

If "disconnection" is an ESCAPE-HORIZON / PATIENCE ARTIFACT (HYP-107, DOSSIER-004),
then for fixed N, increasing T must reveal locking at alpha values that appeared
disconnected at short T. The alpha_c(N) boundary is an ISO-T contour.

If it is a TRUE PHASE TRANSITION, the boundary should be T-INDEPENDENT.

Protocol:
  - Reflexive Kuramoto K = K0 * R^a, N=400, uniform omega in [-1,1], K0=5
  - For each alpha in a fine grid, measure the time-to-lock (R>=R_lock=0.5)
    from an incoherent start (R0 ~ N^{-1/2}).
  - Plot T-to-lock vs alpha for several integration horizons T=25, 50, 100, 200.
  - The "apparent boundary" alpha_c(T) = the alpha where lock fraction within T drops.
  - If alpha_c(T) shifts left (lower alpha) as T grows => patience artifact confirmed.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rng = np.random.default_rng(7)

def measure_lock_frac(N, alpha, K0, T, R_lock=0.5, nseeds=8, dt=0.02, omega_scale=1.0):
    """Fraction of seeds that reach R>=R_lock by time T."""
    lock_count = 0
    for s in range(nseeds):
        r = np.random.default_rng(1000*N + s)
        omega = r.uniform(-omega_scale, omega_scale, N)
        theta = r.uniform(0, 2*np.pi, N)
        nt = int(T/dt)
        locked = False
        for k in range(nt):
            Z = np.mean(np.exp(1j*theta))
            R = abs(Z); psi = np.angle(Z)
            K = K0 * R**alpha
            theta += dt * (omega + K * np.sin(psi - theta))
            if k % 15 == 0:
                R = abs(np.mean(np.exp(1j*theta)))
                if R >= R_lock:
                    locked = True; break
        if locked:
            lock_count += 1
    return lock_count / nseeds

N = 400
K0 = 5.0
alphas = np.arange(0.6, 2.61, 0.2)  # 0.6..2.6
horizons = [25, 50, 100, 200]
print("alpha_c(N=400) boundary vs integration horizon T (K0=5, R_lock=0.5)")
print(f"{'alpha':>6} " + "".join([f"{'T='+str(T):>8}" for T in horizons]))
print("-" * 50)

lock_grid = np.zeros((len(alphas), len(horizons)))
for i, a in enumerate(alphas):
    row = []
    for j, T in enumerate(horizons):
        frac = measure_lock_frac(N, a, K0, T)
        lock_grid[i, j] = frac
        row.append(f"{frac:8.2f}")
    print(f"{a:6.2f} " + "".join(row))

# Apparent boundary: highest alpha where lock frac >= 0.5 within T
print("\nApparent alpha_c(T) (highest alpha with lock_frac >= 0.5):")
boundary = []
for j, T in enumerate(horizons):
    # find largest alpha with frac >= 0.5
    eligible = alphas[lock_grid[:, j] >= 0.5]
    if len(eligible) > 0:
        ac = eligible.max()
    else:
        ac = alphas.min()  # fully disconnected
    boundary.append(ac)
    print(f"  T={T:4d}: alpha_c ~ {ac:.2f}")

# Plot
fig, ax = plt.subplots(figsize=(9, 6))
colors = plt.cm.viridis(np.linspace(0, 0.9, len(horizons)))
for j, T in enumerate(horizons):
    ax.plot(alphas, lock_grid[:, j], 'o-', color=colors[j], label=f'T={T}')
    ax.axvline(boundary[j], color=colors[j], ls='--', alpha=0.5)
ax.axhline(0.5, color='gray', ls=':', label='lock threshold 0.5')
ax.set_xlabel('alpha (divergence exponent)')
ax.set_ylabel('P(lock by time T)')
ax.set_title(f'alpha_c(N=400) boundary vs horizon T (K0={K0})\n'
             f'Boundary shifts left with T? => {boundary[0] - boundary[-1]:.2f}')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('shared_agora/artifacts/tscan_alpha_boundary.png', dpi=200, bbox_inches='tight')
plt.close()

print("\nBoundary shift T=25 -> T=200:", boundary[0], "->", boundary[-1])
print("If shift > 0 (boundary moves LEFT to LOWER alpha with larger T),")
print("the escape-horizon / patience-artifact hypothesis is CONFIRMED.")
print("Saved tscan_alpha_boundary.png")
