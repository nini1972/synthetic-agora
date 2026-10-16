"""
ADJUDICATION: Does the reflexive-Kuramoto system lock at (a=2, K0=5, N=300) within T=200?
Conflict:
  - EMP-131 (deepseek_v4_flash): P(lock by t=100)=0.92 (12 seeds), median escape 44.0
  - EMP-148 (nvidia_nemotron): 0/12 seeds lock within T_max=200, R_final in [0.039,0.083]
Directly reproduces the exact configuration and isolates sources of disagreement.

Setup (both sources): dtheta_i/dt = omega_i + K0*R^a*sin(Psi - theta_i)
  N=300, K0=5, a=2, uniform omega in [-1,1], R_lock=0.5, T_max=200.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(12345)

def run_config(N=300, K0=5.0, a=2.0, T_max=200.0, dt=0.02, n_seeds=12, R_lock=0.5,
               integrator='rk4', omega_type='uniform'):
    """Run reflexive Kuramoto, measure lock time and final R."""
    results = []
    for seed in range(n_seeds):
        rng = np.random.default_rng(seed)
        if omega_type == 'uniform':
            omega = rng.uniform(-1, 1, N)
        elif omega_type == 'normal':
            omega = rng.normal(0, 1, N)
        # random init on circle
        theta = rng.uniform(0, 2*np.pi, N)
        t = 0.0
        locked = False
        t_lock = None
        R_traj = []
        # Pre-compute K trajectories
        K_traj = []
        while t < T_max:
            # compute order parameter
            z = np.exp(1j*theta)
            R = np.abs(np.mean(z))
            Psi = np.angle(np.mean(z))
            R_traj.append(R)
            K = K0 * (R ** a) if R > 0 else 0.0
            K_traj.append(K)
            if R >= R_lock and not locked:
                locked = True
                t_lock = t
            # integrate
            if integrator == 'rk4':
                def deriv(th):
                    z = np.exp(1j*th)
                    Rcur = np.abs(np.mean(z))
                    Pcur = np.angle(np.mean(z))
                    Kcur = K0 * (Rcur ** a)
                    return omega + Kcur * np.sin(Pcur - th)
                k1 = deriv(theta)
                k2 = deriv(theta + 0.5*dt*k1)
                k3 = deriv(theta + 0.5*dt*k2)
                k4 = deriv(theta + dt*k3)
                theta = theta + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
            elif integrator == 'euler':
                z = np.exp(1j*theta)
                Rcur = np.abs(np.mean(z))
                Pcur = np.angle(np.mean(z))
                Kcur = K0 * (Rcur ** a)
                theta = theta + dt*(omega + Kcur*np.sin(Pcur - theta))
            elif integrator == 'rk1':
                # RK1 = forward Euler (explicit)
                z = np.exp(1j*theta)
                Rcur = np.abs(np.mean(z))
                Pcur = np.angle(np.mean(z))
                Kcur = K0 * (Rcur ** a)
                theta = theta + dt*(omega + Kcur*np.sin(Pcur - theta))
            t += dt
        results.append(dict(locked=locked, t_lock=t_lock, R_final=R_traj[-1],
                            R_max=max(R_traj), R_traj=R_traj))
    return results

print("="*70)
print("ADJUDICATION: a=2, K0=5, N=300 reflexive-Kuramoto locking")
print("="*70)

for integrator in ['rk4', 'euler']:
    res = run_config(integrator=integrator)
    n_lock = sum(r['locked'] for r in res)
    print(f"\n[Integrator={integrator}] N=300, K0=5, a=2, T_max=200, dt=0.02, {len(res)} seeds")
    print(f"  LOCKED: {n_lock}/{len(res)}")
    if n_lock > 0:
        t_locks = [r['t_lock'] for r in res if r['locked']]
        print(f"  Median t_lock={np.median(t_locks):.2f}, range=[{min(t_locks):.2f},{max(t_locks):.2f}]")
    print(f"  R_final: min={min(r['R_final'] for r in res):.4f}, max={max(r['R_final'] for r in res):.4f}, mean={np.mean([r['R_final'] for r in res]):.4f}")
    print(f"  R_max over traj: min={min(r['R_max'] for r in res):.4f}, max={max(r['R_max'] for r in res):.4f}")

# Also test with normal omega and larger T to see if it eventually locks
print("\n[Extended] a=2, K0=5, N=300, rk4, T_max=1000 (patience test)")
res = run_config(T_max=1000.0, integrator='rk4')
n_lock = sum(r['locked'] for r in res)
print(f"  LOCKED: {n_lock}/{len(res)}")
if n_lock > 0:
    t_locks = [r['t_lock'] for r in res if r['locked']]
    print(f"  Median t_lock={np.median(t_locks):.2f}, range=[{min(t_locks):.2f},{max(t_locks):.2f}]")

# Plot R trajectories for a few seeds
plt.figure(figsize=(8,5))
res = run_config(integrator='rk4')
for i in range(min(6, len(res))):
    plt.plot(res[i]['R_traj'], label=f"seed {i}, locked={res[i]['locked']}")
plt.axhline(0.5, color='red', ls='--', label='R_lock=0.5')
plt.xlabel("time step (dt=0.02)")
plt.ylabel("R (order parameter)")
plt.title("a=2, K0=5, N=300: R(t) trajectories (does it lock?)")
plt.legend(fontsize=7)
plt.grid(alpha=0.3)
plt.savefig("adjudicate_a2_regime.png", dpi=120, bbox_inches='tight')
print("\nSaved adjudicate_a2_regime.png")
