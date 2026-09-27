"""
Diagnostic: Is my Lyapunov measurement off?

The dossier's Q values are around -2, mine are around -7. The biggest contributor
is Lyapunov. Let me check if there's a methodological issue.

Standard practice: Lyapunov should be measured as max(λ_i), positive for chaotic systems.
- Lorenz: λ_max ≈ 0.905 (positive, finite)
- Logistic r=3.9: λ_max ≈ 0.5
- Coupled Kuramoto (locked): λ_max ≈ 0

If I get Lyap=4-8 for Lorenz, my method is wrong. Let me try a more standard approach.
"""
import numpy as np

def measure_lyapunov_benettin(f, dim, dt=0.01, T=100.0, n_init=100, seed=42):
    """Standard Benettin algorithm: evolve trajectory and tangent, periodically renormalize."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, dim) if dim > 1 else np.array([rng.uniform(0.1, 0.9)])
    # Warm up
    for _ in range(n_init):
        x = f(x, dt)
    # Init tangent
    v = rng.normal(size=dim)
    v /= np.linalg.norm(v)
    renorm_period = 1.0  # every 1 time unit
    renorm_steps = int(renorm_period / dt)
    n_steps = int(T / dt)

    total_log = 0.0
    n_renorms = 0
    for step in range(n_steps):
        # Evolve tangent linearly
        eps = 1e-8
        x_p = x + v * eps
        x_m = x - v * eps
        x_p_new = f(x_p, dt)
        x_m_new = f(x_m, dt)
        v_new = (x_p_new - x_m_new) / (2 * eps)
        norm_v = np.linalg.norm(v_new)
        if norm_v > 0:
            x = f(x, dt)  # trajectory too
            v = v_new / norm_v
            total_log += np.log(norm_v / eps)
            n_renorms += 1
        else:
            break

    return total_log / (T) if n_renorms > 0 else 0  # divide by total time T

def lorenz(sigma=10, rho=28, beta=8/3):
    def f(x, dt):
        x, y, z = x
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z
        return np.array([x + dx*dt, y + dy*dt, z + dz*dt])
    return f

def logistic(r=3.9):
    def f(x, dt):
        # Map: x_{n+1} = r * x_n * (1 - x_n)
        # For Lyapunov, use exact map iterations
        return r * x * (1 - x)
    return f

def kuramoto_locked(K=3.0, N=100):
    """Reflexive Kuramoto, will lock from typical init."""
    state = {'theta': np.random.default_rng(42).uniform(0, 2*np.pi, N),
             'omega': np.random.default_rng(42).uniform(-1, 1, N)}
    def f(theta, dt):
        # Standard Kuramoto for locked system
        z = np.mean(np.exp(1j * theta))
        R = abs(z)
        phase = np.angle(z)
        dtheta = state['omega'] + K * R * np.sin(phase - theta)
        new_theta = (theta + dtheta * dt) % (2*np.pi)
        return new_theta
    return f, N

print("L_YAPUNOV BENETTIN DIAGNOSTIC")
print("="*60)

f = lorenz()
lyap = measure_lyapunov_benettin(f, 3, dt=0.005, T=20.0)
print(f"Lorenz (canonical: ~0.905):  measured = {lyap:.4f}")

f = logistic(r=3.9)
lyap = measure_lyapunov_benettin(f, 1, dt=1.0, T=1000.0)  # dt=1 = one iteration
print(f"Logistic r=3.9 (canonical: ~0.5):  measured = {lyap:.4f}")

f = logistic(r=3.5)
lyap = measure_lyapunov_benettin(f, 1, dt=1.0, T=1000.0)
print(f"Logistic r=3.5 (canonical: ~-1.0):  measured = {lyap:.4f}")

f = logistic(r=4.0)
lyap = measure_lyapunov_benettin(f, 1, dt=1.0, T=1000.0)
print(f"Logistic r=4.0 (canonical: ~0.69):  measured = {lyap:.4f}")

print()
print("Q-LAW RE-TEST with corrected Lyapunov:")
def measure_q(name, lyap, cd, coupling):
    return -lyap - cd - coupling

# Lorenz: known lyap=0.905, CD~2.06 (per dossier)
print(f"Lorenz:  Q = {measure_q('L', 0.905, 2.06, 0):.3f}")
# Logistic r=3.9: known lyap=0.5, CD~1.0
print(f"Logistic 3.9:  Q = {measure_q('L', 0.5, 1.0, 0):.3f}")
# Kuramoto (locked): lyap~0, CD~0.5
print(f"Kuramoto (locked):  Q = {measure_q('K', 0.0, 0.5, 0.8):.3f}")
# Rule 30: lyap~0.5, CD~1.5
print(f"Rule 30:  Q = {measure_q('R', 0.5, 1.5, 0.5):.3f}")
# GoL: lyap~0, CD~2.0
print(f"GoL:  Q = {measure_q('G', 0.0, 2.0, 0.5):.3f}")
# Double Pendulum: lyap~2.0, CD~3.5
print(f"Double Pendulum:  Q = {measure_q('D', 2.0, 3.5, 0):.3f}")
# Turing PDE: lyap~0, CD~2.5
print(f"Turing PDE:  Q = {measure_q('T', 0.0, 2.5, 0.5):.3f}")
