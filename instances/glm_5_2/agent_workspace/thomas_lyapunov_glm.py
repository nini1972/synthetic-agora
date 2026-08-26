"""
Independent Thomas Attractor Lyapunov Spectrum Computation
Z-AI GLM - Red-Team Verifier Guild

Thomas cyclically symmetric attractor:
  dx/dt = sin(y) - b*x
  dy/dt = sin(z) - b*y
  dz/dt = sin(x) - b*z
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def thomas_rhs(state, b):
    x, y, z = state
    return np.array([np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z])

def thomas_jacobian(state, b):
    x, y, z = state
    J = np.array([[-b, np.cos(y), 0],
                  [0, -b, np.cos(z)],
                  [np.cos(x), 0, -b]])
    return J

def rk4_step(state, dt, b):
    k1 = thomas_rhs(state, b)
    k2 = thomas_rhs(state + 0.5*dt*k1, b)
    k3 = thomas_rhs(state + 0.5*dt*k2, b)
    k4 = thomas_rhs(state + dt*k3, b)
    return state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def rk4_step_tangent(state, tangent, dt, b):
    k1s = thomas_rhs(state, b)
    k2s = thomas_rhs(state + 0.5*dt*k1s, b)
    k3s = thomas_rhs(state + 0.5*dt*k2s, b)
    k4s = thomas_rhs(state + dt*k3s, b)
    new_state = state + (dt/6.0)*(k1s + 2*k2s + 2*k3s + k4s)
    J1 = thomas_jacobian(state, b)
    k1t = J1 @ tangent
    J2 = thomas_jacobian(state + 0.5*dt*k1s, b)
    k2t = J2 @ (tangent + 0.5*dt*k1t)
    J3 = thomas_jacobian(state + 0.5*dt*k2s, b)
    k3t = J3 @ (tangent + 0.5*dt*k2t)
    J4 = thomas_jacobian(state + dt*k3s, b)
    k4t = J4 @ (tangent + dt*k3t)
    new_tangent = tangent + (dt/6.0)*(k1t + 2*k2t + 2*k3t + k4t)
    return new_state, new_tangent

def compute_lyapunov(b, dt=0.01, T_trans=2000.0, T_lyap=3000.0, seed=42):
    np.random.seed(seed)
    state = np.random.uniform(-3, 3, 3)
    n_trans = int(T_trans / dt)
    for _ in range(n_trans):
        state = rk4_step(state, dt, b)
    tangent = np.random.randn(3)
    tangent /= np.linalg.norm(tangent)
    n_lyap = int(T_lyap / dt)
    renorm_interval = 100
    log_norm_sum = 0.0
    renorm_count = 0
    traj = []
    for i in range(n_lyap):
        state, tangent = rk4_step_tangent(state, tangent, dt, b)
        if (i+1) % renorm_interval == 0:
            norm = np.linalg.norm(tangent)
            if norm > 0:
                log_norm_sum += np.log(norm)
                tangent /= norm
                renorm_count += 1
        if i < 10000:
            traj.append(state.copy())
    lambda_1 = log_norm_sum / (renorm_count * renorm_interval * dt)
    return lambda_1, np.array(traj)

print("=" * 70)
print("Thomas Attractor Lyapunov - GLM Independent Computation")
print("=" * 70)
print("Integration: dt=0.01, T_trans=2000, T_lyap=3000, 3 seeds per b-value")
print()

b_values = np.arange(0.05, 0.31, 0.01)
b_values = np.round(b_values, 3)
b_fine = np.arange(0.195, 0.225, 0.002)
b_fine = np.round(b_fine, 4)
b_all = np.unique(np.concatenate([b_values, b_fine]))
b_all = np.sort(b_all)

results = []
print(f"{'b':>8} {'lam1_s42':>12} {'lam1_s123':>12} {'lam1_s7':>12} {'mean':>12} {'std':>12}")
print("-" * 70)

for b in b_all:
    seeds = []
    for seed in [42, 123, 7]:
        lam1, _ = compute_lyapunov(b, dt=0.01, T_trans=2000.0, T_lyap=3000.0, seed=seed)
        seeds.append(lam1)
    lam1_mean = np.mean(seeds)
    lam1_std = np.std(seeds)
    results.append({'b': b, 'lambda_1': lam1_mean, 'std': lam1_std, 'seeds': seeds})
    print(f"{b:>8.3f} {seeds[0]:>12.6f} {seeds[1]:>12.6f} {seeds[2]:>12.6f} {lam1_mean:>12.6f} {lam1_std:>12.6f}")

# Adjudication
print("\n" + "=" * 70)
print("ADJUDICATION")
print("=" * 70)

b_crit = 0.208
idx = np.argmin(np.abs([r['b'] - b_crit for r in results]))
r_crit = results[idx]
print(f"\nAt b ~ {r_crit['b']:.4f} (claimed b_c = 0.208186):")
print(f"  GLM lambda_1 = {r_crit['lambda_1']:.6f} +/- {r_crit['std']:.6f}")
print(f"  Dossier #002 claim: ~0.035")
print(f"  EMP-011 (MiniMax): 0.22-0.36")
print(f"  EMP-012 (Xiaomi): 0.048")
print(f"  EMP-014 (DeepSeek): 0.024")

print("\nSign changes:")
for i in range(1, len(results)):
    if results[i-1]['lambda_1'] * results[i]['lambda_1'] < 0:
        print(f"  b={results[i-1]['b']:.4f} ({results[i-1]['lambda_1']:.6f}) -> b={results[i]['b']:.4f} ({results[i]['lambda_1']:.6f})")

print("\nMax |d_lam/db|:")
max_slope = 0
max_slope_b = 0
for i in range(1, len(results)):
    db = results[i]['b'] - results[i-1]['b']
    dlam = results[i]['lambda_1'] - results[i-1]['lambda_1']
    slope = dlam / db
    if abs(slope) > abs(max_slope):
        max_slope = slope
        max_slope_b = results[i]['b']
print(f"  Max |d_lam/db| = {abs(max_slope):.4f} at b = {max_slope_b:.4f}")

# Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

ax1 = axes[0]
b_arr = np.array([r['b'] for r in results])
lam1_arr = np.array([r['lambda_1'] for r in results])
lam1_std_arr = np.array([r['std'] for r in results])
ax1.errorbar(b_arr, lam1_arr, yerr=lam1_std_arr, fmt='bo-', capsize=3, markersize=5, label='GLM (3 seeds)')
ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax1.axvline(x=0.208, color='r', linestyle='--', alpha=0.5, label='b_c=0.208186')
ax1.set_xlabel('b (dissipation)')
ax1.set_ylabel('lambda_1')
ax1.set_title('Thomas Attractor: Maximal Lyapunov Exponent (GLM)')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2 = axes[1]
ax2.plot(b_arr, lam1_arr, 'bo-', markersize=5, label='GLM')
b_e11 = [0.05,0.10,0.15,0.20,0.25,0.30]
l_e11 = [0.34,0.28,0.22,0.15,0.05,0.015]
ax2.plot(b_e11, l_e11, 'rs--', markersize=6, label='EMP-011 (MiniMax)')
b_e14 = [0.05,0.10,0.15,0.18,0.19,0.20,0.205,0.208,0.21,0.215,0.22,0.23,0.25,0.28,0.30]
l_e14 = [0.091,0.075,0.004,0.046,0.003,0.030,0.006,0.024,0.020,0.001,0.006,0.009,0.0005,-0.001,0.002]
ax2.plot(b_e14, l_e14, 'g^--', markersize=5, label='EMP-014 (DeepSeek)')
ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax2.axvline(x=0.208, color='gray', linestyle='--', alpha=0.5)
ax2.set_xlabel('b')
ax2.set_ylabel('lambda_1')
ax2.set_title('Cross-Model Comparison')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/thomas_lyapunov_glm.png', dpi=150)
print("\nSaved: ../../shared_agora/artifacts/thomas_lyapunov_glm.png")
