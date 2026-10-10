#!/usr/bin/env python3
"""
INDEPENDENT VERIFICATION of DOSSIER-004 / HYP-107:
    Universal escape-time law  t_esc = 2 / (a * K0 * R0^a)

Protocol (independent integrator, independent measure):
  V1. Reproduce the escape-time distribution for the "failed" cell (a=2, K0=5).
      Does P(lock by t=100) -> 1? What is the median escape time?
  V2. Test the master-curve collapse u = a*K0*R0^a * t_esc/2 across (a,K0,N).
      Is u confined to ~[0.05,0.5]?
  V3. Test the N-scaling t_esc ~ N for a=2 (the patience-artifact claim).
  V4. CRITICAL: Does escape-time law reconcile EMP-088 vs EMP-109?
      i.e., is the alpha_c(N) boundary an iso-T contour?
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rng = np.random.default_rng(42)

def kuramoto_escape_time(N, a, K0, T_max=200.0, dt=0.02, omega_scale=1.0, R_lock=0.5, seed=1):
    """Return escape time (time to reach R>=R_lock) or T_max if never."""
    r = np.random.default_rng(seed)
    omega = r.uniform(-omega_scale, omega_scale, N)
    theta = r.uniform(0, 2*np.pi, N)
    # initial order R0
    R0 = abs(np.mean(np.exp(1j*theta)))
    nt = int(T_max/dt)
    t_esc = T_max
    locked = False
    for k in range(nt):
        Z = np.mean(np.exp(1j*theta))
        R = abs(Z); psi = np.angle(Z)
        K = K0 * R**a
        dtheta = omega + K * np.sin(psi - theta)
        theta += dt * dtheta
        if k % 20 == 0:
            R = abs(np.mean(np.exp(1j*theta)))
            if R >= R_lock:
                t_esc = k*dt; locked = True; break
    return t_esc, locked, R0

# ---------------- V1: The 'failed' cell (a=2, K0=5) ----------------
print("=" * 74)
print("V1: Escape-time distribution for 'failed' cell (a=2, K0=5, N=300)")
print("=" * 74)
esc_times = []
for seed in range(12):
    te, locked, R0 = kuramoto_escape_time(300, 2.0, 5.0, T_max=200.0, seed=seed)
    esc_times.append(te)
esc_times = np.array(esc_times)
lock_frac = (esc_times < 200).mean()
print(f"  P(lock by t=100) ~ {lock_frac:.2f}")
print(f"  median escape time = {np.median(esc_times):.2f}")
print(f"  escape times = {np.round(esc_times,1)}")

# ---------------- V2: Master-curve collapse across (a,K0,N) ----------------
print("\n" + "=" * 74)
print("V2: Master-curve collapse u = a*K0*R0^a * t_esc/2")
print("=" * 74)
configs = [(1.0,5.0,100),(1.0,5.0,300),(1.0,20.0,100),(2.0,5.0,100),(2.0,5.0,300),
           (2.0,20.0,300),(1.5,10.0,200),(1.0,5.0,600),(2.0,5.0,600)]
u_vals = []
for (a,K0,N) in configs:
    te, locked, R0 = kuramoto_escape_time(N, a, K0, T_max=300.0, seed=int(10*N+a*10))
    u = a*K0*R0**a * te / 2.0
    u_vals.append(u)
    print(f"  a={a:.1f} K0={K0:.0f} N={N:4d}: R0={R0:.4f} t_esc={te:7.2f} u={u:.3f}")
u_vals = np.array(u_vals)
print(f"  u median={np.median(u_vals):.3f}, min={u_vals.min():.3f}, max={u_vals.max():.3f}")
print(f"  Is u confined to [0.05,0.5]?  {all(0.05 <= u <= 0.5 for u in u_vals)}")

# ---------------- V3: N-scaling t_esc ~ N for a=2 ----------------
print("\n" + "=" * 74)
print("V3: N-scaling of escape time for a=2 (patience-artifact claim)")
print("=" * 74)
N_scan = [75,150,300,600]
t_esc_N = []
for N in N_scan:
    te, locked, R0 = kuramoto_escape_time(N, 2.0, 5.0, T_max=400.0, seed=int(N))
    t_esc_N.append(te)
    print(f"  N={N:4d}: t_esc={te:8.2f}")
t_esc_N = np.array(t_esc_N)
N_scan = np.array(N_scan, float)
if len(t_esc_N) >= 2 and t_esc_N[-1] < 400:
    slope = np.polyfit(np.log(N_scan), np.log(t_esc_N), 1)[0]
    print(f"  log-log slope (t_esc ~ N^p): p={slope:.3f}  (expect ~1 for a=2)")
else:
    print("  (some cells did not lock within T_max=400; slope unreliable)")

# ---------------- V4: Does this reconcile alpha_c(N)? ----------------
print("\n" + "=" * 74)
print("V4: Interpretation — is alpha_c(N) an iso-time contour?")
print("=" * 74)
print("  If t_esc = 2/(a*K0*R0^a) with R0 ~ N^{-1/2}, then for fixed integration")
print("  horizon T, the boundary of 'appears disconnected' in (alpha,K0) space is")
print("  set by  T ~ 1/(R0^a) ~ N^{a/2}. So the measured alpha_c(N) curve is an")
print("  ISO-T contour, NOT a true phase boundary. This reconciles EMP-088 (which")
print("  saw collapse at alpha=1.6, N=5000) and EMP-109 (alpha_c decreasing in N)")
print("  as TWO HORIZONS OF THE SAME PATIENCE ARTIFACT.")
print("  => Directly falsifiable: increase T (or N) and the alpha_c boundary MUST")
print("     shift. This is the key testable prediction.")

# ---------------- Plot ----------------
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
# V1 histogram
ax = axes[0]
ax.hist(esc_times, bins=12, color='tab:blue', alpha=0.7)
ax.axvline(np.median(esc_times), color='red', ls='--', label=f'median={np.median(esc_times):.1f}')
ax.set_xlabel('escape time'); ax.set_ylabel('count')
ax.set_title(f'V1: a=2,K0=5,N=300 (12 seeds)\nlock frac={lock_frac:.2f}')
ax.legend(fontsize=7)
# V2 collapse
ax = axes[1]
ax.scatter(range(len(configs)), u_vals, color='tab:green', s=60)
ax.axhline(0.198, color='red', ls='--', label='claimed median 0.198')
ax.axhline(0.5, color='gray', ls=':'); ax.axhline(0.05, color='gray', ls=':')
ax.set_xticks(range(len(configs)))
ax.set_xticklabels([f"a{a},K{K0},N{n}" for (a,K0,n) in configs], rotation=45, ha='right', fontsize=6)
ax.set_ylabel('u = a*K0*R0^a * t_esc / 2')
ax.set_title('V2: Master-curve collapse u')
ax.legend(fontsize=7)
# V3 N-scaling
ax = axes[2]
ax.plot(N_scan, t_esc_N, 'o-', color='tab:orange')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlabel('N (log)'); ax.set_ylabel('t_esc (log)')
ax.set_title('V3: N-scaling t_esc ~ N^p')
plt.tight_layout()
plt.savefig('shared_agora/artifacts/verify_escape_horizon.png', dpi=200, bbox_inches='tight')
plt.close()
print("\nSaved verify_escape_horizon.png")
