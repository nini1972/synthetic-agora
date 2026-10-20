"""
REFINEMENT OF EMP-153: the lock criterion at (a=2, K0=5, N=300) is controlled by the
"winnable fraction" f(K0) = P(|omega| < K0), NOT by tail heaviness.

Theory (self-consistent mean field for reflexive coupling):
  An oscillator locks iff |omega_i| < K_eff = K0 * R^a  (max restoring pull at order R).
  Locked oscillators align -> contribute ~cos to R.  Leading order:
      R  ~  f(K0 * R^a),   f(x) = P(|omega| < x)
  This is a fixed-point equation.  The attractor exists iff R_hs=0 is unstable,
  i.e. R = f(K0 R^a) has a nonzero root.  For bounded omega and any a>0,
  R=0 is always stable (Jacobian -0 to leading order on R^(a+1) term) -> a finite-size
  ACTIVATION problem: R grows only if the initial finite-N fluctuation R_0 ~ 1/sqrt(N)
  is amplified past the barrier.  If f(K0) << 1, R_max is capped and no lock.

We test:
  (1) Gamma sweep of Lorentzian omega -> empirical lock fraction vs empirical f(K0).
  (2) Self-consistent prediction R* = fixed point of R = f(K0 R^a) (smoothed f).
"""
import numpy as np
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def simulate(omega, K0, a, seeds, dt=0.05, T=200.0, R_lock=0.5):
    N = len(omega); succ = 0; rf = []
    for s in seeds:
        rng = np.random.default_rng(s)
        theta = rng.uniform(0, 2*np.pi, N)
        nsteps = int(T/dt)
        def deriv(th):
            z = np.mean(np.exp(1j*th)); R = np.abs(z); Psi = np.angle(z)
            return omega + K0*(R**a)*np.sin(Psi - th)
        for step in range(nsteps):
            k1 = deriv(theta); k2 = deriv(theta+0.5*dt*k1)
            k3 = deriv(theta+0.5*dt*k2); k4 = deriv(theta+dt*k3)
            theta = theta + (dt/6.0)*(k1+2*k2+2*k3+k4)
        Rf = np.abs(np.mean(np.exp(1j*theta)))
        rf.append(Rf)
        if Rf > R_lock: succ += 1
    return succ, np.mean(rf), np.std(rf)

def empirical_f(omega, x):
    return np.mean(np.abs(omega) < x)

K0 = 5.0; a = 2.0; N = 300
seeds = list(range(8))
gammas = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5]

print("="*96)
print(f"LORENTZIAN GAMMA SWEEP  (a={a}, K0={K0}, N={N}, 8 seeds)")
print("="*96)
print(f"{'gamma':<8}{'std(omega)':<12}{'f(K0)':<10}{'max|w|':<10}{'lock':<9}{'R_final':<10}{'R*_theory':<11}")

rows = []
for g in gammas:
    rng = np.random.default_rng(int(g*1000)+7)
    u = rng.uniform(1e-4, 1-1e-4, N)
    omega = g*np.tan(np.pi*(u-0.5))  # Lorentzian(gamma=g)
    succ, rmean, rstd = simulate(omega, K0, a, seeds)
    fK0 = empirical_f(omega, K0)
    # theory: fixed point of R = f_tail(K0 R^a) using a heavy-tail-ish smooth surrogate
    # Use the empirical smooth CDF of |omega| (Lorentzian: F(x)=2/pi*arctan(x/g))
    def F(x): return (2/np.pi)*np.arctan(x/g)
    def g_eq(R): return F(K0*(R**a)) - R
    Rstar = 0.0
    try:
        # look for nonzero root above 0.02
        if g_eq(0.02) > 0:
            Rstar = brentq(g_eq, 0.02, 0.999)
    except Exception:
        Rstar = 0.0
    rows.append((g, np.std(omega), fK0, np.max(np.abs(omega)), succ, rmean, Rstar))
    print(f"{g:<8}{np.std(omega):<12.2f}{fK0:<10.3f}{np.max(np.abs(omega)):<10.1f}{str(succ)+'/8':<9}{rmean:<10.4f}{Rstar:<11.3f}")

# Plot
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
arr = np.array([(r[0], r[2], r[4]/8.0, r[5], r[6]) for r in rows])
ax = axes[0]
ax.plot(arr[:,0], arr[:,2], 'o-', label='empirical lock fraction', color='C0', ms=8)
ax.plot(arr[:,0], np.clip(arr[:,4],0,1), 's--', label='theory R* (fixed point)', color='C3', ms=8)
ax.set_xlabel('Lorentzian gamma (tail heaviness)'); ax.set_ylabel('lock / R*')
ax.set_title('Lock success collapses as gamma grows\n(a=2, K0=5, N=300)')
ax.legend(); ax.grid(alpha=0.3)

ax = axes[1]
ax.scatter(arr[:,1], arr[:,2], c=arr[:,0], s=110, cmap='viridis')
for i,(gg,sd,lf,rm,rs) in enumerate(arr):
    ax.annotate(f'g={gg}', (sd, lf), fontsize=8, xytext=(3,3), textcoords='offset points')
ax.axvline(K0, color='k', ls='--', alpha=0.6, label=f'K0={K0}')
ax.set_xlabel('std(omega)'); ax.set_ylabel('empirical lock fraction')
ax.set_title('Lock fails when spread >> coupling K0'); ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('emp153_gamma_sweep.png', dpi=110)
print("\nSaved emp153_gamma_sweep.png")

# Critical gamma estimate
for r in rows:
    print(f"  gamma={r[0]:.2f}: f(K0)={r[2]:.3f} -> lock {r[4]}/8")
