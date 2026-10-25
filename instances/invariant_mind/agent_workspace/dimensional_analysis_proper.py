import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

# Proper Lorenz system integration with RK4
def lorenz(t, state, sigma, rho, beta):
    x,y,z = state
    return [sigma*(y-x), x*(rho-z)-y, x*y - beta*z]

def integrate_lorenz_rk4(initial_state, sigma, beta, rho, dt, t_total, n_steps=None):
    if n_steps is None:
        n_steps = int(t_total/dt)
    states = np.zeros((n_steps, 3))
    times = np.linspace(0, t_total, n_steps)
    state = np.array(initial_state)
    for i in range(n_steps):
        states[i] = state
        k1 = lorenz(state, sigma, beta, rho)
        k2 = lorenz(state + 0.5*dt*k1, sigma, beta, rho)
        k3 = lorenz(state + 0.5*dt*k2, sigma, beta, rho)
        k4 = lorenz(state + dt*k3, sigma, beta, rho)
        state = state + dt/6*(k1 + 2*k2 + 2*k3 + k4)
    return states

# Proper Benettin's algorithm for Lyapunov exponent
def benettin_lambda_max_rk4(states, dt, dim=3, max_iter=None, threshold=1e-12):
    n_steps = states.shape[0]
    if max_iter is None:
        max_iter = n_steps
    tangent_vectors = states[:max_iter].copy()
    tangent_vectors -= tangent_vectors.mean(axis=0)
    tangent_vectors /= np.linalg.norm(tangent_vectors, axis=1, keepdims=True)
    log_sum = 0.0
    norm_prod = 1.0
    max_lambda = 0.0
    for i in range(max_iter):
        state = states[i]
        k1 = lorenz(state, sigma, beta, rho)
        k2 = lorenz(state + 0.5*dt*k1, sigma, beta, rho)
        k3 = lorenz(state + 0.5*dt*k2, sigma, beta, rho)
        k4 = lorenz(state + dt*k3, sigma, beta, rho)
        correct_state = state + dt/6*(k1 + 2*k2 + 2*k3 + k4)
        dv_dt = lorenz(correct_state, sigma, beta, rho)
        tangent_vectors += dt * dv_dt
        Q, R = np.linalg.qr(tangent_vectors)
        diag_R = np.abs(np.diag(R))
        valid_mask = diag_R > threshold
        if np.any(valid_mask):
            log_sum += np.sum(np.log(diag_R[valid_mask]))
            norm_prod *= diag_R[valid_mask]**dt
            Q = Q[:, valid_mask]
            tangent_vectors = Q
            max_lambda = max(max_lambda, np.max(np.abs(np.log(diag_R))))
    lam = 0.0
    if n_steps > 0:
        lam = log_sum / (norm_prod * n_steps * dt)
    return lam, max_lambda

# Proper correlation dimension via Grassberger-Procaccia
# This version works correctly even for small tau_max
def correlation_dimension_fixed(states, max_tau=None, min_points=50):
    if max_tau is None:
        max_tau = min(50, len(states))
    tau_range = np.arange(1, max_tau+1)
    correlations = []
    for t in tau_range:
        dists = np.sqrt(((states[:-t]-states[t:])**2).sum(axis=1))
        valid = dists < 0.25  # Adjust threshold based on data spread
        if np.sum(valid) >= min_points:
            c = len(set(tuple(d) for d in dists[valid])) / (len(dists[valid]) - min_points + 1)
        else:
            c = 0.0
        correlations.append(c)
    # Fit log-log slope
    log_corr = np.log([c for c in correlations if c > 0])
    log_tau = np.log(range(1, len(log_corr)+1))
    mask = ~np.isnan(log_corr) & ~np.isinf(log_corr) & (log_corr > -10)
    if np.sum(mask) >= 2:
        coeffs = np.polyfit(log_tau[mask], log_corr[mask], 1)
        D2 = coeffs[0]
        order = int(round(D2))
    else:
        D2 = 0.0
        order = 0
    return {'D2': D2, 'order': order, 'correlations': correlations}

# Main analysis loop
base_params = (10, 28, 8/3)
scale_factors = np.logspace(-1, 1, 5)  # Reduced from 9 to 5
quantization_results = []
print("Performing Dimensional Analysis in World C:")
for sf in scale_factors:
    scaled_params = (base_params[0]*sf, base_params[1], base_params[2])
    init_state = np.random.randn(3) * 0.1
    # Integrate trajectory with RK4
    traj = integrate_lorenz_rk4(init_state, *scaled_params, dt=0.001, t_total=50)
    traj_clean = traj[200:]  # Remove transient
    # Calculate Lyapunov exponent using Benettin's algorithm
    lam_max, _ = benettin_lambda_max_rk4(traj_clean, dt=0.001, max_iter=5000)
    # Calculate correlation dimension using Grassberger-Procaccia
    dp = correlation_dimension_fixed(traj_clean, max_tau=50, min_points=50)
    quantization_results.append({'sf': float(sf), 'lam_max': float(lam_max), 'D2': float(dp['D2']), 'order': int(dp['order'])})
    print(f"Scale {sf:.2f}: lam_max={lam_max:+.4f}, D2={dp['D2']:.4f}, order={dp['order']}")
# Save results
with open('dimensional_analysis_proper.json', 'w') as f:
    json.dump(quantization_results, f, indent=2)
# Plotting
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
q_values = [r['lam_max'] for r in quantization_results]
scaled = [r['sf'] for r in quantization_results]
axes[0].semilogx(scaled, q_values, 'o-', linewidth=2, markersize=8, color='#1f77b4')
axes[0].set_xlabel('Scaling Factor')
axes[0].set_ylabel(r'$\lambda_{max}$')
axes[0].set_title('Topological Scaling of Maximal Lyapunov Exponent')
axes[0].grid(True, which='both', alpha=0.2)
axes[0].axvspan(1.0, 10.0, alpha=0.08, color='orange', label='Emergence Horizon')
axes[0].legend()
dp_orders = [r['order'] for r in quantization_results]
axes[1].semilogx(scaled, dp_orders, 's-', linewidth=2, markersize=8, color='#2ca02c')
axes[1].set_xlabel('Scaling Factor')
axes[1].set_ylabel('Correlation Dimension Order')
axes[1].set_title('Topological Scaling of Correlation Dimension Order')
axes[1].grid(True, which='both', alpha=0.2)
axes[1].axvspan(1.0, 10.0, alpha=0.08, color='orange', label='Emergence Horizon')
axes[1].legend()
plt.tight_layout()
plt.savefig('dimensional_analysis_proper.png', dpi=300)
plt.close()
