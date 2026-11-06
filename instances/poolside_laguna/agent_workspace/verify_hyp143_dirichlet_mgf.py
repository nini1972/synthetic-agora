import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import poch, gamma
from scipy.integrate import quad

# HYP-143: Dirichlet MGF Formula (Multi-Upper/Single-Lower Pochhammer Structure)
def dirichlet_mgf_hyp143(t, alpha, beta):
    # Proposed MGF formula from HYP-143
    s = len(alpha)
    numerator = gamma(np.sum(alpha)) * gamma(beta[0] - t)
    denominator = gamma(beta[0]) * gamma(np.sum(alpha) - t)
    pochhammer_ratio = poch(np.sum(alpha) - beta[0] + 1, t) / poch(1, t)
    return numerator / denominator * pochhammer_ratio

def dirichlet_mgf_ground_truth(t, alpha, beta):
    # Ground truth MGF via numerical integration
    def integrand(x):
        return np.exp(t * x) * x**(beta[0]-1) * (1 - x)**(np.sum(alpha) - beta[0] - 1) / (gamma(beta[0]) * gamma(np.sum(alpha) - beta[0]) / gamma(np.sum(alpha)))
    return quad(integrand, 0, 1)[0]

# Test parameters
alpha = np.array([2.0, 3.0, 1.5])
beta = np.array([5.0])
t_values = np.linspace(-10, 10, 100)
t_values = t_values[np.abs(t_values) < beta[0] - 1e-6]  # Avoid singularities

# Compute MGFs
hyp143_mgf = [dirichlet_mgf_hyp143(t, alpha, beta) for t in t_values]
ground_truth_mgf = [dirichlet_mgf_ground_truth(t, alpha, beta) for t in t_values]

# Plot results
plt.figure(figsize=(10, 6))
plt.plot(t_values, hyp143_mgf, label='HYP-143 Formula', color='blue', linestyle='--', linewidth=2)
plt.plot(t_values, ground_truth_mgf, label='Numerical Integration', color='red', alpha=0.7, linewidth=1)
plt.xlabel('t', fontsize=12)
plt.ylabel('MGF(t)', fontsize=12)
plt.title('HYP-143 Validation: Dirichlet MGF Formula vs. Ground Truth', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('hyp143_dirichlet_mgf_validation.png', dpi=150)

# Error analysis
relative_errors = np.abs(np.array(hyp143_mgf) - np.array(ground_truth_mgf)) / (np.abs(np.array(ground_truth_mgf)) + 1e-10)
max_error = np.max(relative_errors)
mean_error = np.mean(relative_errors)

with open('hyp143_validation_metrics.txt', 'w') as f:
    f.write(f"Max Relative Error: {max_error:.2e}\n")
    f.write(f"Mean Relative Error: {mean_error:.2e}\n")

print(f"✅ HYP-143 validation complete. Max error: {max_error:.2e}")