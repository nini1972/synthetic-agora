import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Vectorized Kuramoto implementation with mean-field projection
def kuramoto_mean_field(t, thetas, K, N, omegas):
    """
    Vectorized Kuramoto implementation using mean-field projection
    dtheta_i/dt = omega_i + K/N * Im[ Z * exp(-i*theta_i) ]
    """
    # Calculate complex order parameter
    Z = np.sum(np.exp(1j * thetas)) / N
    
    # Calculate coupling term
    coupling = K * np.imag(Z * np.exp(-1j * thetas))
    
    return omegas + coupling

# Simulation parameters
N_values = [32, 64, 128, 256, 512, 1024]
K_values = np.linspace(0.7, 1.9, 25)
t_span = (0, 500)
t_eval = np.linspace(400, 500, 1001)  # Measure after transient

# Natural frequency distribution (uniform [-1,1])
omegas = {}
for N in N_values:
    omegas[N] = np.random.uniform(-1, 1, N)

# Run simulations
results = {}
for N in N_values:
    results[N] = {}
    for K in K_values:
        # Initial conditions
        theta0 = np.random.uniform(0, 2*np.pi, N)
        
        # Solve ODE
        sol = solve_ivp(kuramoto_mean_field, t_span, theta0, 
                        args=(K, N, omegas[N]), t_eval=t_eval, rtol=1e-6)
        
        # Calculate order parameter
        R = np.abs(np.sum(np.exp(1j * sol.y), axis=0) / N)
        mean_R = np.mean(R)
        var_R = np.var(R)
        
        results[N][K] = {'mean_R': mean_R, 'var_R': var_R}

# Save results for analysis
np.save('workspace/kuramoto_results.npy', results)
print("Simulations completed. Results saved to workspace/kuramoto_results.npy")