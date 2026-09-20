"""Debug: trace the dynamics of vanilla Kuramoto (alpha=0, K=5) to see why it doesn't lock."""
import numpy as np

N = 200
gamma = 1.0
K = 5.0
dt = 0.02  # match dossier
T = 35.0
n_steps = int(T / dt)

rng = np.random.default_rng(42)
omega = rng.uniform(-gamma, gamma, N)
theta = rng.uniform(0, 2*np.pi, N)

print(f"omega stats: min={omega.min():.3f}, max={omega.max():.3f}, mean={omega.mean():.3f}")

for t in range(n_steps):
    Z = np.mean(np.exp(1j * theta))
    R = abs(Z)
    Psi = np.angle(Z)
    # Direct pairwise computation (slow but correct)
    # dtheta_i = omega_i + (K/N) sum_j sin(theta_j - theta_i)
    # = omega_i - K*R*sin(theta_i - Psi)
    coupling = -K * R * np.sin(theta - Psi)
    dtheta = omega + coupling
    theta = theta + dt * dtheta
    if t % 100 == 0 or t < 10:
        print(f"  t={t*dt:6.2f}: R={R:.4f}, R_imag={Z.imag:+.4f}, R_real={Z.real:+.4f}")

print(f"\nFinal R = {R:.4f}")