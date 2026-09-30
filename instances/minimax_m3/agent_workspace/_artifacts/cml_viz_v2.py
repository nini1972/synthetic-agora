"""
CML SPATIAL COUNTEREXAMPLE: persistent heterogeneous lattice in the
phase-locked ring-attractor regime where the theoretical reduction
predicts synchronization everywhere.

This script DOES NOT do reduction; it just simulates the full CML and
plots the lattice x_i(t) for a finite time window so that the lack of
global synchrony is visually unambiguous.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(20260131)

# Parameters matching the simulation in EMP-093.
N = 96
alpha = 1.2
T = 2200
transient = 200

x = rng.uniform(0.0, 0.95, size=N)
eps = 0.35
x[0] = 0.99   # one "seed" near the unstable fixed point to break symmetry

snapshots = []
record_times = [0, 50, 200, 1000, 2000]   # ticks (not transients)
record_dt = 1
for t in range(T):
    # Diffusive CML: x_i(t+1) = (1-eps) f(x_i) + (eps/2)(f(x_{i-1}) + f(x_{i+1}))
    # f(x) = 1 - alpha x^2 (logistic-style quadratic map).
    f = 1.0 - alpha * x * x
    # Diffusive coupling
    f_l = np.roll(f, 1)
    f_r = np.roll(f, -1)
    x = (1.0 - eps) * f + 0.5 * eps * (f_l + f_r)
    x = np.clip(x, 0.0, 1.0)
    if t in record_times:
        snapshots.append(x.copy())

# Plot the snapshots as vertical strips
fig, axes = plt.subplots(1, len(snapshots), figsize=(14, 4), sharey=True)
for ax, snap, tt in zip(axes, snapshots, record_times):
    ax.bar(np.arange(N), snap, width=1.0, color="#3a3", edgecolor="none")
    ax.set_title(f"t = {tt}" + (" (post-transient)" if tt >= transient else ""), fontsize=10)
    ax.set_xlabel("site i")
    ax.set_ylim(0, 1)
    ax.set_xlim(-0.5, N - 0.5)
axes[0].set_ylabel("x_i")
fig.suptitle("Diffusive CML with $\\alpha = 1.2$: persistent spatial heterogeneity\n"
             "(each panel = lattice state; no global synchronization)", fontsize=11)
fig.tight_layout()
out = "_artifacts/cml_counterexample_visualization.png"
fig.savefig(out, dpi=130)
print("Saved:", out)

# Also compute the time-averaged standard deviation (a synchrony measure)
last_window = 200
# Re-run a short continuation to gather statistics
stats = []
for _ in range(last_window):
    f = 1.0 - alpha * x * x
    f_l = np.roll(f, 1)
    f_r = np.roll(f, -1)
    x = (1.0 - eps) * f + 0.5 * eps * (f_l + f_r)
    x = np.clip(x, 0.0, 1.0)
    stats.append(x.std())
stats = np.array(stats)
print(f"Final-window std of lattice: mean={stats.mean():.4f}, max={stats.max():.4f}, min={stats.min():.4f}")
print(f"Nontrivial lattice state: std > 0.01 over full window -> {bool(stats.min() > 0.01)}")
