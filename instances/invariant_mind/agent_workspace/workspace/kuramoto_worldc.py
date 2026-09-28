import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from colony_lib.dynamics import vectorized_kuramoto

# High-precision Kuramoto finite-size scaling study
N_values = [32, 64, 128, 256, 512, 1024, 2048, 4096]
K_values = np.linspace(1.0, 1.6, 61)  # Finer resolution around critical point

# Thermodynamic critical coupling
K_c_inf = 4 / np.pi

# Run simulations
results = {}

for N in N_values:
    print(f"Processing N={N}")
    results[N] = {}
    
    # Generate natural frequencies (fixed for all K)
    omegas = np.random.uniform(-1, 1, N)
    
    for K in K_values:
        # Run simulation with longer transient
        sol = vectorized_kuramoto(
            N=N, 
            K=K, 
            omega=omegas,
            t_transient=500,
            t_measure=1000,
            dt=0.01
        )
        
        # Calculate order parameter statistics
        R = sol['R']
        mean_R = np.mean(R)
        var_R = np.var(R)
        
        results[N][K] = {'mean_R': mean_R, 'var_R': var_R}

# Save results
np.save('kuramoto_highres_results.npy', results)
print("All simulations completed. Results saved.")

# Generate preliminary plot
plt.figure(figsize=(10, 6))
for N in N_values:
    Ks = sorted(results[N].keys())
    R_means = [results[N][K]['mean_R'] for K in Ks]
    plt.plot(Ks, R_means, 'o-', label=f'N={N}')

plt.axvline(K_c_inf, color='k', linestyle='--', label='K_c(∞)')
plt.xlabel('Coupling Strength K')
plt.ylabel('Mean Order Parameter <R>')
plt.title('High-Resolution Kuramoto Synchronization Transition')
plt.legend()
plt.grid(True)
plt.savefig('kuramoto_highres_transition.png')
print("Saved transition plot.")