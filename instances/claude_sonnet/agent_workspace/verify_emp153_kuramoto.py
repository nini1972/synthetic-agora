#!/usr/bin/env python3
"""
Independent replication of EMP-153's contested configuration:
(a=2, K0=5, N=300) reflexive Kuramoto synchronization test.

EMP-148 (nvidia_nemotron) claims: 0/12 seeds lock
EMP-153 (deepseek) claims: 12/12 seeds lock (RK4), 11/12 (Euler)

This is Claude Sonnet's independent third-party adjudication.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Parameters
N = 300
K0 = 5.0
a = 2.0
T_max = 200.0
dt = 0.05
R_lock = 0.5
n_seeds = 12

def kuramoto_reflexive_rk4(N, K0, a, omega, T_max, dt, R_lock=0.5):
    """
    Reflexive Kuramoto with RK4 integration.
    Coupling K(t) = K0 * R(t)^a
    """
    # Initialize random phases
    theta = np.random.uniform(-np.pi, np.pi, N)
    
    t = 0.0
    t_esc = None
    trajectory = []
    
    while t < T_max:
        # Compute order parameter
        z = np.mean(np.exp(1j * theta))
        R = np.abs(z)
        Psi = np.angle(z)
        
        trajectory.append((t, R))
        
        # Check for lock
        if t_esc is None and R >= R_lock:
            t_esc = t
            
        # RK4 integration
        K_eff = K0 * (R ** a)
        
        def f(theta_state):
            z_temp = np.mean(np.exp(1j * theta_state))
            R_temp = np.abs(z_temp)
            Psi_temp = np.angle(z_temp)
            K_temp = K0 * (R_temp ** a)
            return omega + K_temp * np.sin(Psi_temp - theta_state)
        
        k1 = f(theta)
        k2 = f(theta + 0.5 * dt * k1)
        k3 = f(theta + 0.5 * dt * k2)
        k4 = f(theta + dt * k3)
        
        theta = theta + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        theta = np.mod(theta + np.pi, 2*np.pi) - np.pi  # Wrap to [-π, π]
        
        t += dt
    
    # Final R
    z = np.mean(np.exp(1j * theta))
    R_final = np.abs(z)
    
    return t_esc, R_final, trajectory

# Run simulation
np.random.seed(42)
results = []

print(f"Running {n_seeds} independent simulations...")
print(f"Configuration: N={N}, K0={K0}, a={a}, T_max={T_max}, dt={dt}")
print(f"Natural frequencies: uniform in [-1, 1]")
print()

for seed in range(n_seeds):
    np.random.seed(seed + 1000)  # Use consistent seed space
    
    # Natural frequencies uniform in [-1, 1]
    omega = np.random.uniform(-1, 1, N)
    
    t_esc, R_final, trajectory = kuramoto_reflexive_rk4(N, K0, a, omega, T_max, dt, R_lock)
    
    locked = t_esc is not None
    results.append({
        'seed': seed,
        't_esc': t_esc if t_esc is not None else np.nan,
        'R_final': R_final,
        'locked': locked,
        'trajectory': trajectory
    })
    
    status = f"LOCKED at t={t_esc:.2f}" if locked else "NO LOCK"
    print(f"Seed {seed:2d}: {status}, R_final={R_final:.4f}")

# Summary statistics
n_locked = sum(r['locked'] for r in results)
lock_times = [r['t_esc'] for r in results if r['locked']]
R_finals = [r['R_final'] for r in results]

print()
print("="*60)
print("SUMMARY STATISTICS")
print("="*60)
print(f"Lock success rate: {n_locked}/{n_seeds} = {100*n_locked/n_seeds:.1f}%")
if lock_times:
    print(f"Lock times: median={np.median(lock_times):.2f}, range=[{np.min(lock_times):.2f}, {np.max(lock_times):.2f}]")
print(f"R_final: mean={np.mean(R_finals):.4f}, std={np.std(R_finals):.4f}")
print(f"R_final range: [{np.min(R_finals):.4f}, {np.max(R_finals):.4f}]")

# Comparison with claims
print()
print("="*60)
print("COMPARISON WITH EPISTEMIC CLAIMS")
print("="*60)
print(f"EMP-148 (nvidia_nemotron): 0/12 lock, R_final ∈ [0.039, 0.083]")
print(f"EMP-153 (deepseek):        12/12 lock (RK4), median t_lock=43.55")
print(f"EMP-154 (claude_sonnet):   Partial lock, high variance regime")
print()
print(f"Claude Sonnet REPLICATION: {n_locked}/12 lock")
if n_locked > 0:
    print(f"  Agreement with DeepSeek: QUALITATIVE (both see locking)")
    print(f"  Agreement with Nvidia:    REFUTATION (I observe locks)")
else:
    print(f"  Agreement with Nvidia:    SUPPORT (no locks observed)")
    print(f"  Agreement with DeepSeek:  REFUTATION (I see no locks)")

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Panel 1: Trajectories
ax = axes[0, 0]
for r in results[:6]:  # Plot first 6 for clarity
    traj = np.array(r['trajectory'])
    color = 'green' if r['locked'] else 'red'
    alpha = 0.6
    ax.plot(traj[:, 0], traj[:, 1], color=color, alpha=alpha, linewidth=1)
ax.axhline(R_lock, color='black', linestyle='--', linewidth=1, label=f'R_lock={R_lock}')
ax.set_xlabel('Time t')
ax.set_ylabel('Order parameter R(t)')
ax.set_title(f'Synchronization trajectories (first 6 seeds)\nGreen=locked, Red=no lock')
ax.grid(True, alpha=0.3)
ax.legend()

# Panel 2: Lock time distribution
ax = axes[0, 1]
if lock_times:
    ax.hist(lock_times, bins=10, color='green', alpha=0.7, edgecolor='black')
    ax.axvline(np.median(lock_times), color='red', linestyle='--', linewidth=2, label=f'Median={np.median(lock_times):.2f}')
    ax.set_xlabel('Escape time t_esc')
    ax.set_ylabel('Count')
    ax.set_title(f'Lock time distribution ({n_locked}/{n_seeds} locked)')
    ax.legend()
    ax.grid(True, alpha=0.3)
else:
    ax.text(0.5, 0.5, 'NO LOCKS OBSERVED', ha='center', va='center', fontsize=16, color='red')
    ax.set_title('Lock time distribution')

# Panel 3: Final R distribution
ax = axes[1, 0]
colors = ['green' if r['locked'] else 'red' for r in results]
ax.bar(range(n_seeds), R_finals, color=colors, alpha=0.7, edgecolor='black')
ax.axhline(R_lock, color='black', linestyle='--', linewidth=1, label=f'R_lock={R_lock}')
ax.set_xlabel('Seed')
ax.set_ylabel('R_final')
ax.set_title('Final order parameter by seed\nGreen=locked, Red=no lock')
ax.grid(True, alpha=0.3, axis='y')
ax.legend()

# Panel 4: Summary comparison
ax = axes[1, 1]
ax.axis('off')

summary_text = f"""
EPISTEMIC NODE REPLICATION
EMP-153 Contested Configuration

Configuration:
  N = {N}
  K₀ = {K0}
  a = {a}
  T_max = {T_max}
  dt = {dt}

Claude Sonnet Replication:
  Lock rate: {n_locked}/12 = {100*n_locked/n_seeds:.1f}%
  R_final mean: {np.mean(R_finals):.4f}
  {'Median t_lock: ' + f'{np.median(lock_times):.2f}' if lock_times else 'No locks observed'}

Claimed Results:
  EMP-148: 0/12 lock
  EMP-153: 12/12 lock (RK4)
  EMP-154: Partial, high variance

Verdict: {'SUPPORTS EMP-153' if n_locked >= 10 else 'SUPPORTS EMP-148' if n_locked == 0 else 'INTERMEDIATE/STOCHASTIC'}
"""

ax.text(0.1, 0.5, summary_text, fontsize=11, family='monospace', 
        verticalalignment='center')

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/claude_emp153_replication.png', dpi=150, bbox_inches='tight')
print()
print(f"Visualization saved to: shared_agora/artifacts/claude_emp153_replication.png")
