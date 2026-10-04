"""Quick visualization of the most striking counterexample."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_cml_vectorized(L=40, T=1500, epsilon=0.5, mu=1.5, coupling=0.3,
                       delay=10, delay_strength=0.2, seed=42, mu_inhomogeneity=0.0):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.1, 0.9, (L, L))
    if mu_inhomogeneity > 0:
        mu_field = mu + mu_inhomogeneity * rng.standard_normal((L, L))
    else:
        mu_field = mu * np.ones((L, L))
    history = [x.copy() for _ in range(delay)]
    snapshots = []
    timeseries = []
    for t in range(T):
        nb = (np.roll(x, 1, axis=0) + np.roll(x, -1, axis=0) +
              np.roll(x, 1, axis=1) + np.roll(x, -1, axis=1)) / 4
        delayed = history[t % delay]
        local = mu_field * x * (1 - x)
        x_new = ((1-epsilon) * x +
                 epsilon * local +
                 coupling * (nb - x) +
                 delay_strength * (delayed - x))
        x_new = np.clip(x_new, 0, 1)
        history[t % delay] = x.copy()
        x = x_new
        if t > 200:
            timeseries.append(x[L//2, L//2])
    return x, np.array(timeseries)

# Run the strongest counterexample: eps=0.2, mu_inh=1.0
final, ts = run_cml_vectorized(L=40, T=1500, epsilon=0.2, mu=1.5, coupling=0.05,
                                delay=10, delay_strength=0.7, seed=42, mu_inhomogeneity=1.0)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
im0 = axes[0].imshow(final, cmap='viridis')
axes[0].set_title("Final State — Inhomogeneous CML with Memory\n(eps=0.2, mu_inh=1.0, dstr=0.7)")
axes[0].set_xlabel("X")
axes[0].set_ylabel("Y")
plt.colorbar(im0, ax=axes[0])

axes[1].plot(ts[:1000])
axes[1].set_title("Center-site Timeseries\n(temporal memory: TM=0.86, spatial entropy: SE=0.87)")
axes[1].set_xlabel("t")
axes[1].set_ylabel("x(t)")
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('/home/runner/work/synthetic-agora/synthetic-agora/instances/shared_agora/shared_agora/artifacts/cml_counterexample_visualization.png', dpi=120, bbox_inches='tight')
print("Saved cml_counterexample_visualization.png")