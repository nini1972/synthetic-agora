"""
RED-TEAM ADJUDICATION REPLICATION
=================================
Independent third-party replication of two disputed empirical claims:

  DISPUTE 1 - Thomas cyclically symmetric attractor (World A Dossier #002)
     EMP-011 (minimax): lambda_1 decreases SMOOTHLY from ~0.34 (b=0.05) to ~0.015 (b=0.30),
                        NO sharp bifurcation at b_c ~ 0.208, system chaotic everywhere.
     EMP-010 (gemini):  b < 0.208 -> chaos; b > 0.22-0.23 -> abrupt crisis collapse
                        into symmetric fixed point sinks.

  DISPUTE 2 - Kuramoto nonlinear feedback (World A Dossier #001)
     K_eff = K_0 * R^alpha, alpha=2, N=200
     EMP-008 (minimax, Cauchy freqs): NO hysteresis, incoherent everywhere, R ~ 0.05.
     EMP-004 (gemini, normal freqs):  first-order explosive sync with hysteresis at K_c ~ 1.4-1.8.

Method: fully independent implementations (own integrators, own parameter coverage,
including BOTH frequency distributions and BOTH b-ranges claimed).
Author: independent red-team verifier (third model family).
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(20250213)

# =====================================================================
# DISPUTE 1 : THOMAS ATTRACTOR
#   dx/dt = sin(y) - b*x ; dy/dt = sin(z) - b*y ; dz/dt = sin(x) - b*z
# =====================================================================
def thomas_dynamics(x, b):
    return np.array([np.sin(x[1]) - b * x[0],
                     np.sin(x[2]) - b * x[1],
                     np.sin(x[0]) - b * x[2]])

def thomas_jacobian(x, b):
    J = np.zeros((3, 3))
    J[0, 0] = -b; J[0, 1] = np.cos(x[1])
    J[1, 1] = -b; J[1, 2] = np.cos(x[2])
    J[2, 2] = -b; J[2, 0] = np.cos(x[0])
    return J

def integrate_thomas(b, T_trans=1500.0, T_lyap=800.0, dt=0.01):
    """Return (lambda_1, final_state, octant_switch_count)."""
    x = rng.uniform(-1.0, 1.0, 3)
    n_tr = int(T_trans / dt)
    for _ in range(n_tr):
        k1 = thomas_dynamics(x, b)
        k2 = thomas_dynamics(x + 0.5*dt*k1, b)
        k3 = thomas_dynamics(x + 0.5*dt*k2, b)
        k4 = thomas_dynamics(x + dt*k3, b)
        x = x + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
    v = rng.normal(size=3); v /= np.linalg.norm(v)
    n_ly = int(T_lyap / dt)
    lam_sum = 0.0
    count = 0
    for _ in range(n_ly):
        # evolve x one RK4 step
        k1 = thomas_dynamics(x, b)
        k2 = thomas_dynamics(x + 0.5*dt*k1, b)
        k3 = thomas_dynamics(x + 0.5*dt*k2, b)
        k4 = thomas_dynamics(x + dt*k3, b)
        x = x + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        # evolve tangent vector with RK4 on v' = J(x(t)) v
        # (using Jacobian at current x is standard for autonomous flows)
        J = thomas_jacobian(x, b)
        kv1 = J @ v
        J2 = thomas_jacobian(x + 0.5*dt*k1, b)
        kv2 = J2 @ (v + 0.5*dt*kv1)
        kv3 = J2 @ (v + 0.5*dt*kv2)
        J4 = thomas_jacobian(x + dt*k1, b)
        kv4 = J4 @ (v + dt*kv3)
        v = v + (dt/6.0)*(kv1 + 2*kv2 + 2*kv3 + kv4)
        nrm = np.linalg.norm(v)
        lam_sum += np.log(nrm)
        v /= nrm
        count += 1
    lambda_1 = lam_sum / (count * dt)
    # octant switching in a post-transient window
    x2 = x.copy()
    oct_count = 0
    prev_sign = np.sign(x2)
    n_oct = int(300.0 / dt)
    for _ in range(n_oct):
        k1 = thomas_dynamics(x2, b)
        k2 = thomas_dynamics(x2 + 0.5*dt*k1, b)
        k3 = thomas_dynamics(x2 + 0.5*dt*k2, b)
        k4 = thomas_dynamics(x2 + dt*k3, b)
        x2 = x2 + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        s = np.sign(x2)
        if not np.array_equal(s, prev_sign):
            oct_count += 1
            prev_sign = s
    return lambda_1, x2, oct_count

print("=" * 70)
print("DISPUTE 1: THOMAS ATTRACTOR - independent lambda_1 scan")
print("=" * 70)
b_grid = np.array([0.05, 0.10, 0.15, 0.18, 0.19, 0.20, 0.205, 0.208, 0.21,
                   0.215, 0.22, 0.23, 0.25, 0.28, 0.30])
lam_vals = []
oct_vals = []
for b in b_grid:
    lam, xf, noct = integrate_thomas(b)
    lam_vals.append(lam)
    oct_vals.append(noct)
    print(f"  b = {b:.3f}  lambda_1 = {lam:+.4f}  octant_switches/300tu = {noct:3d}  "
          f"|x|_final = {np.linalg.norm(xf):.3f}")

# =====================================================================
# DISPUTE 2 : KURAMOTO with feedback K_eff = K0 * R^alpha
# =====================================================================
def kuramoto_step(theta, omega, K0, alpha, sigma, dt):
    N = len(theta)
    # order parameter
    z = np.mean(np.exp(1j * theta))
    R = np.abs(z)
    psi = np.angle(z)
    K_eff = K0 * (R ** alpha)
    theta = theta + dt * (omega + K_eff * R * np.sin(psi - theta)) \
            + sigma * np.sqrt(dt) * rng.normal(size=N)
    return theta, R

def kuramoto_sweep(alpha, N, omegas, sigma, K0_vals, dt=0.05,
                   T_trans=300.0, T_meas=100.0, forward=True):
    """Adiabatic sweep; forward=True starts incoherent, False starts coherent."""
    # initial condition
    if forward:
        theta = rng.uniform(-np.pi, np.pi, N)   # incoherent
    else:
        theta = omegas * 0.0 + 0.1              # near-synchronized
    Rs = []
    for K0 in K0_vals:
        n_tr = int(T_trans / dt)
        for _ in range(n_tr):
            theta, R = kuramoto_step(theta, omegas, K0, alpha, sigma, dt)
        # measure
        n_ms = int(T_meas / dt)
        R_acc = 0.0
        for _ in range(n_ms):
            theta, R = kuramoto_step(theta, omegas, K0, alpha, sigma, dt)
            R_acc += R
        Rs.append(R_acc / n_ms)
    return np.array(Rs)

print()
print("=" * 70)
print("DISPUTE 2: KURAMOTO FEEDBACK - independent hysteresis scan")
print("=" * 70)

N = 200
alpha = 2
sigma = 0.02
K0_vals = np.linspace(0.5, 6.0, 23)

# (a) Cauchy frequencies (as EMP-008)
cauchy_freqs = rng.standard_cauchy(size=N)
# (b) Normal frequencies (as EMP-004)
normal_freqs = rng.normal(size=N)

for name, om in [("CAUCHY (EMP-008 setup)", cauchy_freqs),
                 ("NORMAL (EMP-004 setup)", normal_freqs)]:
    print(f"\n--- {name} ---")
    R_fwd = kuramoto_sweep(alpha, N, om, sigma, K0_vals, forward=True)
    R_bwd = kuramoto_sweep(alpha, N, om, sigma, K0_vals, forward=False)
    for i, K0 in enumerate(K0_vals):
        print(f"  K0 = {K0:4.2f}   R_fwd = {R_fwd[i]:.3f}   R_bwd = {R_bwd[i]:.3f}")
    hyst = np.max(np.abs(R_fwd - R_bwd))
    print(f"  MAX |R_fwd - R_bwd| = {hyst:.3f}  -> {'HYSTERESIS' if hyst > 0.2 else 'NO HYSTERESIS'}")

# =====================================================================
# FIGURE
# =====================================================================
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

ax = axes[0]
ax.plot(b_grid, lam_vals, 'o-', color='crimson', lw=2)
ax.axvline(0.208, color='gray', ls='--', label='b_c = 0.208 (dossier claim)')
ax.set_xlabel('dissipation b')
ax.set_ylabel('max Lyapunov exponent $\\lambda_1$')
ax.set_title('Thomas attractor: $\\lambda_1$ vs b (independent RK4 + Benettin)')
ax.grid(alpha=0.3)
ax.legend()

ax = axes[1]
ax.plot(K0_vals, R_fwd, 'o-', color='steelblue', label='forward (incoherent init)')
ax.plot(K0_vals, R_bwd, 's-', color='darkorange', label='backward (coherent init)')
ax.set_xlabel('base coupling $K_0$')
ax.set_ylabel('order parameter R')
ax.set_title('Kuramoto feedback $K_{eff}=K_0 R^\\alpha$, normal freqs')
ax.grid(alpha=0.3)
ax.legend()

plt.tight_layout()
plt.savefig("shared_agora/artifacts/redteam_adjudication.png", dpi=130)
print("\nSaved figure: shared_agora/artifacts/redteam_adjudication.png")
print("DONE")