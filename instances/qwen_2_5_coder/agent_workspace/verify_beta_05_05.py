import numpy as np
from scipy.integrate import quad
from scipy.special import beta as beta_func

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

# Beta(0.5, 0.5) PDF: f(x) = 1/(π√(x(1-x))) on [0,1]
def beta_05_05_pdf(x):
    return 1.0 / (np.pi * np.sqrt(x * (1 - x)))

# Compute theoretical band_frac
theoretical_integral, _ = quad(beta_05_05_pdf, 0.3, 0.7)
print(f"Theoretical Beta(0.5,0.5) band_frac: {theoretical_integral:.3f}")

# Empirical verification
np.random.seed(42)
samples = np.random.beta(0.5, 0.5, 1000000)
empirical_bf = compute_band_frac(samples)
print(f"Empirical Beta(0.5,0.5) band_frac: {empirical_bf:.3f}")

print(f"Difference: {abs(theoretical_integral - empirical_bf):.3f}")