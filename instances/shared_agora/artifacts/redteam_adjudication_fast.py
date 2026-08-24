"""
RED-TEAM ADJUDICATION (fast analytic version)
Thomas attractor lambda_1 (analytic Benettin) + Kuramoto hysteresis scan.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rng = np.random.default_rng(20250213)

# ---------------- Thomas: analytic Jacobian ----------------
def thomas_dyn(x, b):
    return np.array([np.sin(x[1]) - b*x[0],
                     np.sin(x[2]) - b*x[1],
                     np.sin(x[0]) - b*x[2]])

def thomas_J(x, b):
    J = np.zeros((3,3))
    J[0,0] = -b; J[0,1] = np.cos(x[1])
    J[1,1] = -b; J[1,2] = np.cos(x[2])
    J[2,2] = -b; J[2,0] = np.cos(x[0])
    return J

def thomas_lambda(b, dt=0.01, T_trans=500.0, T_lyap=300.0):
    x = rng.uniform(-1, 1, 3)
    for _ in range(int(T_trans/dt)):
        k1 = thomas_dyn(x, b); k2 = thomas_dyn(x+0.5*dt*k1, b)
        k3 = thomas_dyn(x+0.5*dt*k2, b); k4 = thomas_dyn(x+dt*k3, b)
        x = x + dt/6*(k1+2*k2+2*k3+k4)
    v = rng.normal(size=3); v /= np.linalg.norm(v)
    lam_sum = 0.0; n = 0
    for _ in range(int(T_lyap/dt)):
        k1 = thomas_dyn(x, b); k2 = thomas_dyn(x+0.5*dt*k1, b)
        k3 = thomas_dyn(x+0.5*dt*k2, b); k4 = thomas_dyn(x+dt*k3, b)
        x = x + dt/6*(k1+2*k2+2*k3+k4)
        v = v + dt*(thomas_J(x, b) @ v)
        nrm = np.linalg.norm(v)
        lam_sum += np.log(nrm); v /= nrm; n += 1
    return lam_sum/(n*dt)

print("DISPUTE 1: Thomas lambda_1 (analytic Jacobian, RK4+Benettin)")
b_grid = np.array([0.05, 0.1, 0.15, 0.18, 0.19, 0.20, 0.205, 0.208, 0.21,
                   0.215, 0.22, 0.23, 0.25, 0.28, 0.30])
lam_vals = []
for b in b_grid:
    lam = thomas_lambda(b)
    lam_vals.append(lam)
    print(f"  b={b:.3f}  lambda_1={lam:+.4f}", flush=True)

# ---------------- Kuramoto ----------------
def kuramoto_sweep(omegas, sigma, K0_vals, forward=True,
                   dt=0.05, T_trans=100.0, T_meas=40.0):
    N = len(omegas)
    theta = rng.uniform(-np.pi, np.pi, N) if forward else np.full(N, 0.1)
    Rs = []
    for K0 in K0_vals:
        for _ in range(int(T_trans/dt)):
            z = np.mean(np.exp(1j*theta)); R = np.abs(z); psi = np.angle(z)
            theta = theta + dt*(omegas + K0*R**3*np.sin(psi-theta)) + sigma*np.sqrt(dt)*rng.normal(size=N)
        Racc = 0.0
        for _ in range(int(T_meas/dt)):
            z = np.mean(np.exp(1j*theta)); R = np.abs(z); psi = np.angle(z)
            theta = theta + dt*(omegas + K0*R**3*np.sin(psi-theta)) + sigma*np.sqrt(dt)*rng.normal(size=N)
            Racc += R
        Rs.append(Racc/int(T_meas/dt))
    return np.array(Rs)

print("\nDISPUTE 2: Kuramoto hysteresis (alpha=2, N=200, sigma=0.02)")
N = 200
K0_vals = np.linspace(0.5, 6.0, 13)
cauchy = rng.standard_cauchy(size=N)
normal = rng.normal(size=N)
results = {}
for name, om in [("CAUCHY", cauchy), ("NORMAL", normal)]:
    Rf = kuramoto_sweep(om, 0.02, K0_vals, True)
    Rb = kuramoto_sweep(om, 0.02, K0_vals, False)
    results[name] = (Rf, Rb)
    hyst = np.max(np.abs(Rf - Rb))
    print(f"  {name}: max|Rf-Rb|={hyst:.3f} -> {'HYSTERESIS' if hyst>0.2 else 'NO HYSTERESIS'}", flush=True)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].plot(b_grid, lam_vals, 'o-', color='crimson', lw=2)
axes[0].axvline(0.208, color='gray', ls='--', label='b_c=0.208')
axes[0].set_xlabel('b'); axes[0].set_ylabel('$\\lambda_1$')
axes[0].set_title('Thomas $\\lambda_1$'); axes[0].grid(alpha=0.3); axes[0].legend()
for name, (Rf, Rb) in results.items():
    axes[1].plot(K0_vals, Rf, 'o-', label=f'{name} fwd')
    axes[1].plot(K0_vals, Rb, 's--', label=f'{name} bwd')
axes[1].set_xlabel('K0'); axes[1].set_ylabel('R')
axes[1].set_title('Kuramoto hysteresis'); axes[1].grid(alpha=0.3); axes[1].legend()
plt.tight_layout(); plt.savefig("redteam_adjudication.png", dpi=120)
print("\nSaved redteam_adjudication.png")