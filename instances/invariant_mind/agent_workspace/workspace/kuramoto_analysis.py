import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Load results
results = np.load('workspace/kuramoto_results.npy', allow_pickle=True).item()

# Thermodynamic critical coupling
K_c_inf = 4 / np.pi

# For each N, find K that maximizes the variance (pseudo-critical point)
N_list = sorted(results.keys())
K_c_N = []
var_at_K_c = []

for N in N_list:
    Ks = sorted(results[N].keys())
    variances = [results[N][K]['var_R'] for K in Ks]
    max_idx = np.argmax(variances)
    K_c_N.append(Ks[max_idx])
    var_at_K_c.append(variances[max_idx])

# Compute delta K_c
Delta_K_c = [K_c_inf - K for K in K_c_N]

# Fit power law for Delta_K_c vs N
def power_law(x, a, b):
    return a * np.power(x, b)

# Fit Delta_K_c = a * N^b
p0 = [1.0, -0.5]  # Initial guess
params_delta, pcov_delta = curve_fit(power_law, N_list, Delta_K_c, p0=p0)
a_delta, b_delta = params_delta

# Fit variance at K_c: var = c * N^d
params_var, pcov_var = curve_fit(power_law, N_list, var_at_K_c, p0=[0.1, -0.5])
c_var, d_var = params_var

# Create plots
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

# Panel (a): Order parameter vs K for different N
for N in N_list:
    Ks = sorted(results[N].keys())
    mean_Rs = [results[N][K]['mean_R'] for K in Ks]
    axs[0,0].plot(Ks, mean_Rs, 'o-', label=f'N={N}')
axs[0,0].set_xlabel('Coupling Strength K')
axs[0,0].set_ylabel('Mean Order Parameter <R>')
axs[0,0].set_title('Synchronization Transition')
axs[0,0].legend()

# Panel (b): Variance vs K for different N
for N in N_list:
    Ks = sorted(results[N].keys())
    variances = [results[N][K]['var_R'] for K in Ks]
    axs[0,1].plot(Ks, variances, 'o-', label=f'N={N}')
axs[0,1].set_xlabel('Coupling Strength K')
axs[0,1].set_ylabel('Variance of R')
axs[0,1].set_title('Fluctuations')
axs[0,1].legend()

# Panel (c): Critical shift (log-log)
axs[1,0].loglog(N_list, Delta_K_c, 'bo-', label='Data')
axs[1,0].loglog(N_list, power_law(np.array(N_list), a_delta, b_delta), 'r--', 
                label=f'Fit: {a_delta:.3f} * N^{b_delta:.3f}')
axs[1,0].set_xlabel('System Size N (log scale)')
axs[1,0].set_ylabel('ΔK_c (log scale)')
axs[1,0].set_title('Critical Coupling Shift')
axs[1,0].legend()

# Panel (d): Fluctuation damping (log-log)
axs[1,1].loglog(N_list, var_at_K_c, 'go-', label='Data')
axs[1,1].loglog(N_list, power_law(np.array(N_list), c_var, d_var), 'r--', 
                label=f'Fit: {c_var:.3f} * N^{d_var:.3f}')
axs[1,1].set_xlabel('System Size N (log scale)')
axs[1,1].set_ylabel('Variance at K_c (log scale)')
axs[1,1].set_title('Critical Fluctuation Damping')
axs[1,1].legend()

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/kuramoto_finite_size_scaling.png', dpi=300)

# Print results
print(f"Fitted exponent for ΔK_c: {b_delta:.3f} ± {np.sqrt(pcov_delta[1,1]):.3f}")
print(f"Fitted exponent for variance: {d_var:.3f} ± {np.sqrt(pcov_var[1,1]):.3f}")