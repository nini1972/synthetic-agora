"""
Independent Thomas Attractor Lyapunov - GLM Red-Team
Reduced integration for speed, still scientifically meaningful.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def thomas_rhs(state, b):
    x, y, z = state
    return np.array([np.sin(y) - b*x, np.sin(z) - b*y, np.sin(x) - b*z])

def thomas_jac(state, b):
    x, y, z = state
    return np.array([[-b, np.cos(y), 0],
                     [0, -b, np.cos(z)],
                     [np.cos(x), 0, -b]])

def rk4_step(state, dt, b):
    k1 = thomas_rhs(state, b)
    k2 = thomas_rhs(state + 0.5*dt*k1, b)
    k3 = thomas_rhs(state + 0.5*dt*k2, b)
    k4 = thomas_rhs(state + dt*k3, b)
    return state + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def rk4_tangent(state, tan, dt, b):
    k1s = thomas_rhs(state, b)
    k2s = thomas_rhs(state + 0.5*dt*k1s, b)
    k3s = thomas_rhs(state + 0.5*dt*k2s, b)
    k4s = thomas_rhs(state + dt*k3s, b)
    ns = state + (dt/6.0)*(k1s + 2*k2s + 2*k3s + k4s)
    k1t = thomas_jac(state, b) @ tan
    k2t = thomas_jac(state + 0.5*dt*k1s, b) @ (tan + 0.5*dt*k1t)
    k3t = thomas_jac(state + 0.5*dt*k2s, b) @ (tan + 0.5*dt*k2t)
    k4t = thomas_jac(state + dt*k3s, b) @ (tan + dt*k3t)
    nt = tan + (dt/6.0)*(k1t + 2*k2t + 2*k3t + k4t)
    return ns, nt

def compute_lyap(b, dt=0.05, T_trans=500.0, T_lyap=500.0, seed=42):
    np.random.seed(seed)
    state = np.random.uniform(-3, 3, 3)
    n_trans = int(T_trans / dt)
    for _ in range(n_trans):
        state = rk4_step(state, dt, b)
    tan = np.random.randn(3)
    tan /= np.linalg.norm(tan)
    n_lyap = int(T_lyap / dt)
    ri = 50  # renorm interval
    log_sum = 0.0
    rc = 0
    traj = []
    for i in range(n_lyap):
        state, tan = rk4_tangent(state, tan, dt, b)
        if (i+1) % ri == 0:
            norm = np.linalg.norm(tan)
            if norm > 0:
                log_sum += np.log(norm)
                tan /= norm
                rc += 1
        if i < 5000:
            traj.append(state.copy())
    lam = log_sum / (rc * ri * dt)
    return lam, np.array(traj)

print("=" * 60)
print("Thomas Attractor Lyapunov - GLM Independent")
print("dt=0.05, T_trans=500, T_lyap=500, 3 seeds")
print("=" * 60)

b_vals = np.round(np.arange(0.05, 0.31, 0.01), 3)
b_fine = np.round(np.arange(0.195, 0.225, 0.003), 4)
b_all = np.sort(np.unique(np.concatenate([b_vals, b_fine])))

results = []
print(f"{'b':>8} {'s42':>10} {'s123':>10} {'s7':>10} {'mean':>10} {'std':>10}")
print("-" * 60)

for b in b_all:
    seeds = []
    for s in [42, 123, 7]:
        lam, _ = compute_lyap(b, seed=s)
        seeds.append(lam)
    m = np.mean(seeds)
    sd = np.std(seeds)
    results.append({'b': b, 'lam': m, 'std': sd, 'seeds': seeds})
    print(f"{b:>8.4f} {seeds[0]:>10.6f} {seeds[1]:>10.6f} {seeds[2]:>10.6f} {m:>10.6f} {sd:>10.6f}")

# Adjudication
print("\n" + "=" * 60)
print("ADJUDICATION")
print("=" * 60)
idx = np.argmin(np.abs([r['b'] - 0.208 for r in results]))
rc = results[idx]
print(f"\nAt b={rc['b']:.4f} (claimed b_c=0.208186):")
print(f"  GLM: lam1={rc['lam']:.6f} +/- {rc['std']:.6f}")
print(f"  Dossier#002: ~0.035")
print(f"  EMP-011(MiniMax): 0.22-0.36")
print(f"  EMP-012(Xiaomi): 0.048")
print(f"  EMP-014(DeepSeek): 0.024")

print("\nSign changes:")
for i in range(1, len(results)):
    if results[i-1]['lam'] * results[i]['lam'] < 0:
        print(f"  {results[i-1]['b']:.4f}({results[i-1]['lam']:.6f}) -> {results[i]['b']:.4f}({results[i]['lam']:.6f})")

# Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
b_arr = np.array([r['b'] for r in results])
lam_arr = np.array([r['lam'] for r in results])
std_arr = np.array([r['std'] for r in results])

ax1 = axes[0]
ax1.errorbar(b_arr, lam_arr, yerr=std_arr, fmt='bo-', capsize=3, markersize=5, label='GLM (3 seeds)')
ax1.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax1.axvline(x=0.208, color='r', linestyle='--', alpha=0.5, label='b_c=0.208186')
ax1.set_xlabel('b (dissipation)')
ax1.set_ylabel('lambda_1')
ax1.set_title('Thomas Attractor: Max Lyapunov (GLM)')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2 = axes[1]
ax2.plot(b_arr, lam_arr, 'bo-', markersize=5, label='GLM')
b_e11 = [0.05,0.10,0.15,0.20,0.25,0.30]
l_e11 = [0.34,0.28,0.22,0.15,0.05,0.015]
ax2.plot(b_e11, l_e11, 'rs--', markersize=6, label='EMP-011(MiniMax)')
b_e14 = [0.05,0.10,0.15,0.18,0.19,0.20,0.205,0.208,0.21,0.215,0.22,0.23,0.25,0.28,0.30]
l_e14 = [0.091,0.075,0.004,0.046,0.003,0.030,0.006,0.024,0.020,0.001,0.006,0.009,0.0005,-0.001,0.002]
ax2.plot(b_e14, l_e14, 'g^--', markersize=5, label='EMP-014(DeepSeek)')
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
