#!/usr/bin/env python3
"""
Verify the ESCAPE-TIME SCALING LAW directly: t_esc ~ 2/(a*K0*R0^a).
Predicts log(t_esc) linear in alpha (slope -log(R0)) and slope in log(K0).

If the escape-horizon law HOLDS, then log(t_esc) vs alpha is a straight line,
and the barrier at alpha>=2.4 is simply "t_esc astronomically large" (slow-lock,
just beyond our reach). If it BREAKS (t_esc flattens / saturates), then there is
a genuine barrier.

Measure median escape time across alpha in [1.4, 2.4] with moderate T_max.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def escape_time(N, alpha, K0, T_max, R_lock=0.5, seed=1, dt=0.05, omega_scale=1.0):
    r = np.random.default_rng(seed)
    omega = r.uniform(-omega_scale, omega_scale, N)
    theta = r.uniform(0, 2*np.pi, N)
    nt = int(T_max/dt)
    for k in range(nt):
        Z = np.mean(np.exp(1j*theta))
        R = abs(Z); psi = np.angle(Z)
        K = K0 * R**alpha
        theta += dt * (omega + K * np.sin(psi - theta))
        if k % 40 == 0:
            R = abs(np.mean(np.exp(1j*theta)))
            if R >= R_lock:
                return k*dt
    return None  # did not lock within T_max

N = 300
K0 = 5.0
alphas = np.arange(1.4, 2.61, 0.1)
T_max = 800
nseeds = 5
R_lock = 0.5

print("Escape-time law check: t_esc vs alpha (N=%d, K0=%s, T_max=%d)" % (N, K0, T_max))
print(f"{'alpha':>6} {'t_esc(med)':>12} {'locked':>8} {'theory':>12}")
print("-" * 50)

times = []
alphas_valid = []
for a in alphas:
    ts = []
    for s in range(nseeds):
        te = escape_time(N, a, K0, T_max, R_lock, seed=100*s+int(a*100))
        if te is not None:
            ts.append(te)
    if ts:
        med = np.median(ts)
        R0 = 1/np.sqrt(N)
        theory = 2/(a*K0*R0**a)  # crude escape-time estimate
        times.append(med)
        alphas_valid.append(a)
        print(f"{a:6.2f} {med:12.2f} {len(ts):8d} {theory:12.2f}")
    else:
        print(f"{a:6.2f} {'--':>12} {0:8d} {'--':>12}")

alphas_valid = np.array(alphas_valid)
times = np.array(times)
print("\nLog-linear fit of log(t_esc) vs alpha:")
if len(times) >= 3:
    coeffs = np.polyfit(alphas_valid, np.log(times), 1)
    print(f"  slope = {coeffs[0]:.3f}, intercept = {coeffs[1]:.3f}")
    print(f"  predicted slope from -log(R0) = {-np.log(1/np.sqrt(N)):.3f}")
    resid = np.log(times) - (coeffs[0]*alphas_valid + coeffs[1])
    print(f"  R^2 = {1 - np.var(resid)/np.var(np.log(times)):.3f}")

# Plot
fig, ax = plt.subplots(figsize=(9, 6))
ax.semilogy(alphas_valid, times, 'o-', color='tab:blue', label='measured t_esc')
theory_full = [2/(a*K0*(1/np.sqrt(N))**a) for a in alphas_valid]
ax.semilogy(alphas_valid, theory_full, '--', color='tab:red', label='theory 2/(a*K0*R0^a)')
ax.axvline(2.0, color='gray', ls=':', label='alpha=2.0')
ax.set_xlabel('alpha')
ax.set_ylabel('median t_esc (log scale)')
ax.set_title(f'Escape-time scaling law: log-linear in alpha (N={N}, K0={K0})\n'
             f'Deviation from law = boundary of slow-lock vs true-barrier')
ax.legend(fontsize=8)
ax.grid(alpha=0.3, which='both')
plt.tight_layout()
plt.savefig('shared_agora/artifacts/escape_time_law.png', dpi=200, bbox_inches='tight')
plt.close()
print("Saved escape_time_law.png")
