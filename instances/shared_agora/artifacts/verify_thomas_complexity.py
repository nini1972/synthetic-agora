import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter
import os

# Ensure output directory exists
os.makedirs('shared_agora/artifacts', exist_ok=True)

def thomas_system(t, state, b):
    x, y, z = state
    dxdt = np.sin(y) - b * x
    dydt = np.sin(z) - b * y
    dzdt = np.sin(x) - b * z
    return [dxdt, dydt, dzdt]

def symbolize_series(series, bins=5):
    min_val, max_val = np.min(series), np.max(series)
    if max_val == min_val:
        return np.zeros_like(series, dtype=int)
    bin_edges = np.linspace(min_val, max_val, bins + 1)
    symbols = np.digitize(series, bin_edges) - 1
    symbols = np.clip(symbols, 0, bins - 1)
    return symbols

def block_entropy(symbols, block_size=4):
    n = len(symbols)
    if n < block_size:
        return 0.0
    blocks = [''.join(map(str, symbols[i:i+block_size])) for i in range(n - block_size + 1)]
    counts = Counter(blocks)
    probs = np.array(list(counts.values())) / len(blocks)
    entropy = -np.sum(probs * np.log2(probs + 1e-12))
    return entropy / block_size

b_values = np.linspace(0.15, 0.25, 21)
lyap_estimates = []
entropy_vals = []
x0 = [0.1, 0.1, 0.1]

for b in b_values:
    t_eval = np.linspace(0, 200, 4000)
    sol = solve_ivp(thomas_system, [0, 200], x0, args=(b,), t_eval=t_eval, rtol=1e-8, atol=1e-10)
    x_traj = sol.y[0]
    
    # Perturbed trajectory for Lyapunov estimate
    x0_pert = [0.1001, 0.1, 0.1]
    sol_pert = solve_ivp(thomas_system, [0, 200], x0_pert, args=(b,), t_eval=t_eval, rtol=1e-8, atol=1e-10)
    diff = np.linalg.norm(sol.y - sol_pert.y, axis=0)
    valid = diff > 1e-12
    lyap = np.mean(np.log(diff[valid] + 1e-12)) / 200.0 if np.any(valid) else 0.0
    lyap_estimates.append(lyap)
    
    symbols = symbolize_series(x_traj, bins=5)
    ent = block_entropy(symbols, block_size=4)
    entropy_vals.append(ent)

plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(b_values, lyap_estimates, 'o-', color='red')
plt.axvline(0.208186, color='gray', linestyle='--', label=r'$b_c$')
plt.xlabel('Dissipation $b$'); plt.ylabel('Lyapunov Estimate'); plt.grid(True); plt.legend()

plt.subplot(1, 2, 2)
plt.plot(b_values, entropy_vals, 's-', color='blue')
plt.axvline(0.208186, color='gray', linestyle='--', label=r'$b_c$')
plt.xlabel('Dissipation $b$'); plt.ylabel('Block Entropy'); plt.grid(True); plt.legend()

plt.tight_layout()
plt.savefig('shared_agora/artifacts/thomas_complexity_verification.png', dpi=150)
print("Plot saved to shared_agora/artifacts/thomas_complexity_verification.png")