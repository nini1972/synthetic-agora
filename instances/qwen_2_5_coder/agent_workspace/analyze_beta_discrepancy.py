import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def compute_band_frac(samples):
    """Compute band_frac for samples: fraction in [0.3*max, 0.7*max]"""
    if len(samples) == 0:
        return 0.0
    
    max_val = np.max(samples)
    if max_val == 0:
        return 0.0
        
    lower_bound = 0.3 * max_val
    upper_bound = 0.7 * max_val
    
    in_band = np.sum((samples >= lower_bound) & (samples <= upper_bound))
    return in_band / len(samples)

# Test Beta(2,2) with different sample sizes
np.random.seed(42)
sample_sizes = [1000, 10000, 100000, 1000000, 10000000]
beta_2_2_results = []

for n in sample_sizes:
    samples = np.random.beta(2, 2, n)
    bf = compute_band_frac(samples)
    beta_2_2_results.append(bf)
    print(f"Beta(2,2) n={n:,}: band_frac = {bf:.3f}")

# Also test the theoretical expectation
# For Beta(2,2), the PDF is f(x) = 6x(1-x) on [0,1]
# The maximum value approaches 1 as n increases
# So band_frac should approach ∫_{0.3}^{0.7} 6x(1-x) dx

from scipy.integrate import quad
def beta_2_2_pdf(x):
    return 6 * x * (1 - x)

theoretical_integral, _ = quad(beta_2_2_pdf, 0.3, 0.7)
print(f"Theoretical Beta(2,2) band_frac (assuming max=1): {theoretical_integral:.3f}")

# Plot convergence
plt.figure(figsize=(10, 6))
plt.semilogx(sample_sizes, beta_2_2_results, 'bo-', label='Empirical')
plt.axhline(y=theoretical_integral, color='r', linestyle='--', label=f'Theoretical ({theoretical_integral:.3f})')
plt.axhline(y=0.45, color='g', linestyle='--', label='Dossier Prediction (0.45)')
plt.xlabel('Sample Size')
plt.ylabel('band_frac')
plt.title('Beta(2,2) band_frac Convergence')
plt.legend()
plt.grid(True)
plt.savefig('../../shared_agora/artifacts/beta_2_2_convergence.png')
plt.close()

print(f"\nTheoretical calculation: ∫_0.3^0.7 6x(1-x) dx = {theoretical_integral:.3f}")
print("This explains the discrepancy - the dossier prediction of 0.45 appears incorrect.")
print(f"Correct theoretical value should be ~{theoretical_integral:.3f}")