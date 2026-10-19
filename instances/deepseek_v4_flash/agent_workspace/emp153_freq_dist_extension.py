"""
EMP-153 EXTENSION: Does the natural-frequency distribution (bounded vs heavy-tailed)
control lock success at (a=2, K0=5, N=300)?

Claude Sonnet (EMP-153 endorsement) hypothesizes: bounded uniform omega -> 100% lock,
heavy-tailed Lorentzian (kappa=2) -> 0%. If true, this fully reconciles EMP-148's 0/12
with my 12/12 and Claude's 12/12: EMP-148 likely used a heavy-tailed / unbounded omega.

Reflexive Kuramoto: dtheta_i/dt = omega_i + K0 * R^a * sin(Psi - theta_i), R e^{iPsi}= mean e^{i theta}
Integrate RK4 dt=0.05, T=200, 12 seeds. R_lock = 0.5.
Compare 4 omega distributions with matched interquartile-ish scale.
"""
import numpy as np

def simulate(omega, K0, a, seeds, dt=0.05, T=200.0, R_lock=0.5):
    N = len(omega)
    succ = 0; t_locks = []; R_finals = []
    for s in seeds:
        rng = np.random.default_rng(s)
        theta = rng.uniform(0, 2*np.pi, N)
        nsteps = int(T/dt)
        tlock = None
        R_final = None
        def deriv(th):
            z = np.mean(np.exp(1j*th))
            R = np.abs(z); Psi = np.angle(z)
            K = K0 * (R**a)
            return omega + K*np.sin(Psi - th)
        for step in range(nsteps):
            k1 = deriv(theta)
            k2 = deriv(theta + 0.5*dt*k1)
            k3 = deriv(theta + 0.5*dt*k2)
            k4 = deriv(theta + dt*k3)
            theta = theta + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
            if step % 10 == 0:
                R = np.abs(np.mean(np.exp(1j*theta)))
                if tlock is None and R > R_lock:
                    tlock = step*dt
        R_final = np.abs(np.mean(np.exp(1j*theta)))
        R_finals.append(R_final)
        if R_final > R_lock:
            succ += 1
            if tlock is not None: t_locks.append(tlock)
    return succ, t_locks, R_finals

N = 300; K0 = 5.0; a = 2.0
seeds = list(range(12))
rng0 = np.random.default_rng(42)

distributions = {}
# 1. Uniform bounded [-1,1] (my EMP-153 setup)
distributions['uniform[-1,1]'] = rng0.uniform(-1, 1, N)
# 2. Standard normal (bounded-ish tails)
distributions['gaussian(0,0.5)'] = rng0.normal(0, 0.5, N)
# 3. Lorentzian / Cauchy kappa=2 heavy tails (clipped very wide to avoid inf)
#    use inverse-CDF sampling: x = gamma*tan(pi*(u-0.5)), gamma=0.3 -> heavy tails
u = rng0.uniform(1e-4, 1-1e-4, N)
distributions['lorentzian(gamma=0.3)'] = 0.3*np.tan(np.pi*(u-0.5))
# 4. Lorentzian wide (gamma=1.0), heavy tails -> near-critical spread
u2 = rng0.uniform(1e-4, 1-1e-4, N)
distributions['lorentzian(gamma=1.0)'] = 1.0*np.tan(np.pi*(u2-0.5))

print("="*78)
print(f"(a={a}, K0={K0}, N={N}) @ 12 seeds, T=200, R_lock=0.5")
print("="*78)
print(f"{'distribution':<26}{'lock':<8}{'t_lock_median':<16}{'R_final_mean':<14}")
results = {}
for name, om in distributions.items():
    succ, tl, rf = simulate(om, K0, a, seeds)
    med = np.median(tl) if tl else float('nan')
    results[name] = (succ, med, np.mean(rf), np.std(om))
    print(f"{name:<26}{succ}/12   {med:<16.2f}{np.mean(rf):<14.4f}")

print("\nomega std (spread) per distribution:")
for name, om in distributions.items():
    print(f"  {name:<26} std={np.std(om):.3f}  max|omega|={np.max(np.abs(om)):.2f}")
