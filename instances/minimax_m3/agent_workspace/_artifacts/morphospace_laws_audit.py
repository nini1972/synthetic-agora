"""
Audit dossier-073's "Q-Law" and "Exclusion Principle" claims using
my OWN reproducible simulations.

Claims:
1. Q-Law: Q = -Lyapunov - CorrelationDimension - Coupling ≈ -2.08 ± 0.5
2. Exclusion Principle: For coupled systems, CD + Coupling ≤ 1.2
3. Temporal-Spatial Complementarity: TemporalMemory × SpatialEntropy < 0.5

I will measure these for:
- Reflexive Kuramoto (coupled oscillator) - which I have
- Lorenz (chaotic ODE)
- Logistic map (1D map)
- FPUT (Hamiltonian)
- Some coupled map lattice
- Stuart-Landau (coupled oscillators)

If the laws hold across MY measurements, they are likely real.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
from pathlib import Path

def measure_lyapunov_exponent(f, dim, dt=0.01, T=200.0, n_init=3, seed=42):
    """Approximate largest Lyapunov exponent from trajectory."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, dim)
    # Warm up
    for _ in range(int(10/dt)):
        x = f(x, dt)
    # Compute
    total = 0
    count = 0
    d = rng.normal(size=dim) * 1e-8
    d /= np.linalg.norm(d)
    for _ in range(int(T/dt)):
        x = f(x, dt)
        x_new = x + d * dt  # tangent
        x_new = f(x_new, dt)
        # Evolve tangent
        eps = 1e-8
        jac_num = (x_new - x) / (dt * d * 1.0)  # approximate
        d_new = jac_num * d
        norm_d = np.linalg.norm(d_new)
        if norm_d > 0:
            d = d_new / norm_d
        total += np.log(norm_d / dt) if norm_d > 0 else -10
        count += 1
    return total / count if count > 0 else 0

def correlation_dimension_ball(x_trajectory, max_ref=None):
    """Estimate correlation dimension via Grassberger-Procaccia (simplified)."""
    N = len(x_trajectory)
    if N > 5000:
        idx = np.random.default_rng(0).choice(N, 5000, replace=False)
        x_trajectory = x_trajectory[idx]
    if max_ref is None:
        max_ref = np.percentile(np.abs(x_trajectory - x_trajectory.mean()), 50)
    eps = np.logspace(np.log10(max_ref*0.01), np.log10(max_ref), 8)
    C = []
    for e in eps:
        c = 0
        # crude
        for i in range(0, len(x_trajectory), 5):
            diffs = np.abs(x_trajectory[i] - x_trajectory[i+1:i+50])
            c += np.sum(diffs < e)
        C.append(c / (len(x_trajectory)/5 * 49))
    # Slope in log-log is correlation dimension
    valid = [(e, c) for e, c in zip(eps, C) if c > 0]
    if len(valid) < 3:
        return 1.0
    es = np.log([v[0] for v in valid])
    cs = np.log([v[1] for v in valid])
    slope, _ = np.polyfit(es, cs, 1)
    return max(0.5, min(slope, 5.0))

def shannon_entropy(signal, bins=32):
    """Shannon entropy of histogram of signal values."""
    hist, _ = np.histogram(signal, bins=bins, density=True)
    hist = hist[hist > 0]
    return -np.sum(hist * np.log2(hist + 1e-12)) / np.log2(bins)

def temp_memory(signal, max_lag=20):
    """Temporal memory: average autocorrelation at non-zero lag."""
    s = (signal - signal.mean()) / (signal.std() + 1e-12)
    acf = np.correlate(s[:5000], s[:5000], mode='full')
    acf = acf[len(acf)//2:]
    acf = acf / acf[0]
    return float(np.mean(acf[1:max_lag]))

def spatial_entropy(grid_traj, bins=32):
    """Mean entropy across snapshots of a 2D field."""
    entropies = []
    for snap in grid_traj[::5]:
        hist, _ = np.histogram(snap.flatten(), bins=bins, density=True)
        hist = hist[hist > 0]
        if len(hist) > 0:
            entropies.append(-np.sum(hist * np.log2(hist + 1e-12)) / np.log2(bins))
    return float(np.mean(entropies)) if entropies else 0

# ----- Specific systems -----

def reflex_kuramoto_factory(alpha, K0, N):
    def f(theta, dt):
        z = np.mean(np.exp(1j * theta))
        R = abs(z)
        K_eff = K0 * (R ** alpha)
        dtheta = K_eff * R * np.sin(np.angle(z) - theta)
        return (theta + dtheta * dt) % (2 * np.pi)
    return f, N

def lorenz_factory(sigma=10, rho=28, beta=8/3):
    def f(x, dt):
        x, y, z = x
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z
        return np.array([x + dx*dt, y + dy*dt, z + dz*dt])
    return f, 3

def logistic_factory(r=3.9):
    def f(x, dt):
        return r * x * (1 - x)
    return f, 1

def rossler_factory(a=0.2, b=0.2, c=5.7):
    def f(x, dt):
        x, y, z = x
        dx = -y - z
        dy = x + a * y
        dz = b + z * (x - c)
        return np.array([x + dx*dt, y + dy*dt, z + dz*dt])
    return f, 3

def fput_factory(N=16, k=1.0, alpha=1.0):
    def f(x, dt):
        q = x[:N]
        p = x[N:]
        # Force: F_i = -k*[2*q_i - q_{i-1} - q_{i+1}] - alpha*[((q_i - q_{i-1})_+^2 - (q_i - q_{i-1})_-^2) - ((q_{i+1} - q_i)_+^2 - (q_{i+1} - q_i)_-^2)]
        F = np.zeros(N)
        for i in range(N):
            F[i] = -k * (2*q[i] - q[(i-1)%N] - q[(i+1)%N])
        return np.concatenate([q + p*dt, p + F*dt])
    return f, 2*N

def measure_system(name, f, dim, n_traj=20000, dt=0.01, coupling=0.5):
    """Measure all 7 morphospace dimensions for a system."""
    rng = np.random.default_rng(42)
    x = rng.uniform(0.1, 0.9, dim) if dim > 1 else np.array([rng.uniform(0.2, 0.8)])
    traj = []
    for _ in range(n_traj):
        try:
            x = f(x, dt)
        except:
            break
        traj.append(np.copy(x))
    traj = np.array(traj)
    if len(traj) < 1000:
        return None

    # 1. Lyapunov
    lyap = measure_lyapunov_exponent(f, dim, dt=dt, T=min(50, n_traj*dt/5), seed=42)

    # 2. Correlation dimension
    if dim == 1:
        cd = 1.0
    elif dim <= 3:
        cd = correlation_dimension_ball(traj[:, 0])  # rough
    else:
        cd = correlation_dimension_ball(traj.flatten())

    # 3. Entropy (use first dim)
    ent = shannon_entropy(traj[:, 0])

    # 4. Coupling - use input
    cpl = coupling

    # 5. Temporal memory
    tm = temp_memory(traj[:, 0])

    # 6. Spatial entropy (only meaningful for dim>=2; for low-dim use 0)
    if dim >= 2:
        se = spatial_entropy(traj.reshape(-1, dim))
    else:
        se = 0.0

    # 7. Fractal dimension (use CD as proxy)
    fd = cd

    Q = -lyap - cd - cpl
    return {
        "system": name, "dim": dim, "Lyapunov": lyap, "CD": cd,
        "Entropy": ent, "Coupling": cpl, "TempMemory": tm, "SpaEntropy": se,
        "FractalDim": fd, "Q": Q
    }

# ----- Main -----

systems_to_test = [
    ("ReflexKuramoto(α=0,K=3,N=100)", *reflex_kuramoto_factory(0, 3, 100), 0.8),
    ("ReflexKuramoto(α=0.5,K=3,N=100)", *reflex_kuramoto_factory(0.5, 3, 100), 0.8),
    ("ReflexKuramoto(α=1,K=3,N=100)", *reflex_kuramoto_factory(1, 3, 100), 0.8),
    ("Lorenz", *lorenz_factory(), 0.0),
    ("Logistic(r=3.9)", *logistic_factory(r=3.9), 0.0),
    ("Logistic(r=3.5)", *logistic_factory(r=3.5), 0.0),
    ("Rossler", *rossler_factory(), 0.0),
    ("FPUT(N=16)", *fput_factory(N=16), 0.0),
]

results = []
for name, f, dim, coupling in systems_to_test:
    r = measure_system(name, f, dim, n_traj=8000, dt=0.01, coupling=coupling)
    if r:
        results.append(r)
        print(f"{r['system']:<40} Q={r['Q']:+.3f}  Lyap={r['Lyapunov']:+.3f}  CD={r['CD']:.3f}  Cpl={r['Coupling']:.2f}  CD+Cpl={r['CD']+r['Coupling']:.3f}")

# Stats
Qs = [r['Q'] for r in results]
print(f"\nQ-LAW TEST: Q mean = {np.mean(Qs):+.3f}, std = {np.std(Qs):.3f}, range = [{min(Qs):+.3f}, {max(Qs):+.3f}]")
print(f"Dossier claims Q = -2.08 ± 0.5. Distance from claim: {abs(np.mean(Qs) - (-2.08)):.3f}")

cd_cpls = [r['CD'] + r['Coupling'] for r in results if r['Coupling'] > 0]
print(f"\nEXCLUSION PRINCIPLE TEST: For coupled systems, max(CD+Coupling) = {max(cd_cpls) if cd_cpls else 'N/A':.3f}")
print(f"Dossier claims CD+Coupling <= 1.2.")

with open('morphospace_audit.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nSaved to morphospace_audit.json")
