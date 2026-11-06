"""
World C Empirical Test: HYP-140 Lenia Critical Exponent
Finite-size scaling test of beta ~ 0.05 claim
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Minimal Lenia2D implementation (continuous CA)
def lenia_update(state, kernel, growth_params):
    """
    Single Lenia timestep
    state: 2D array of cell states [0, 1]
    kernel: 2D convolution kernel
    growth_params: dict with 'mu', 'sigma'
    """
    from scipy.signal import convolve2d
    
    # Convolve with kernel to get neighborhood field
    field = convolve2d(state, kernel, mode='same', boundary='wrap')
    
    # Growth function: Gaussian bell centered at mu
    mu = growth_params['mu']
    sigma = growth_params['sigma']
    growth = np.exp(-((field - mu)**2) / (2 * sigma**2))
    
    # Update rule with dt=0.1
    dt = 0.1
    new_state = np.clip(state + dt * (2 * growth - 1), 0, 1)
    return new_state

def make_kernel(R, grid_size):
    """
    Create circular kernel with radius R
    Normalized so sum = 1
    """
    x = np.arange(grid_size) - grid_size // 2
    y = np.arange(grid_size) - grid_size // 2
    X, Y = np.meshgrid(x, y)
    dist = np.sqrt(X**2 + Y**2)
    kernel = (dist < R).astype(float)
    kernel = kernel / kernel.sum()
    return kernel

def measure_activity(state):
    """Order parameter: spatial mean activity"""
    return np.mean(state)

def run_lenia_phase_scan(grid_size, R, sigma_g, mu_values, steps=500, n_trials=3):
    """
    Scan growth center mu and measure steady-state activity
    """
    kernel = make_kernel(R, grid_size)
    results = {'mu': [], 'activity_mean': [], 'activity_std': []}
    
    for mu in mu_values:
        activities = []
        for trial in range(n_trials):
            # Random initial condition
            np.random.seed(trial + int(mu * 1000))
            state = np.random.rand(grid_size, grid_size) * 0.5
            
            # Relax for 'steps' timesteps
            for t in range(steps):
                state = lenia_update(state, kernel, {'mu': mu, 'sigma': sigma_g})
            
            # Measure final activity
            A = measure_activity(state)
            activities.append(A)
        
        results['mu'].append(mu)
        results['activity_mean'].append(np.mean(activities))
        results['activity_std'].append(np.std(activities))
    
    return results

def fit_critical_exponent(mu, A, mu_c):
    """
    Fit A(mu) = A0 * (mu - mu_c)^beta for mu > mu_c
    Returns beta estimate
    """
    # Use only points above critical point
    mask = mu > mu_c
    if mask.sum() < 3:
        return np.nan, np.nan
    
    mu_fit = mu[mask]
    A_fit = A[mask]
    
    # Filter out near-zero activities (log-space issues)
    valid = A_fit > 0.01
    mu_fit = mu_fit[valid]
    A_fit = A_fit[valid]
    
    if len(mu_fit) < 3:
        return np.nan, np.nan
    
    # Log-log fit: log(A) = log(A0) + beta * log(mu - mu_c)
    x = np.log(mu_fit - mu_c)
    y = np.log(A_fit)
    
    # Linear regression
    poly = np.polyfit(x, y, 1)
    beta = poly[0]
    A0 = np.exp(poly[1])
    
    return beta, A0

# Experimental parameters matching HYP-140
R = 15
sigma_g = 0.05
mu_values = np.linspace(0.12, 0.19, 20)
grid_sizes = [64, 128, 256]  # Finite-size scaling
steps = 800  # Longer relaxation
n_trials = 5

print("="*80)
print("WORLD C EMPIRICAL TEST: HYP-140 LENIA CRITICAL EXPONENT")
print("="*80)
print(f"Parameters: R={R}, sigma_g={sigma_g}")
print(f"Grid sizes: {grid_sizes}")
print(f"Relaxation steps: {steps}")
print(f"Trials per point: {n_trials}")
print("="*80)

# Run phase scans
results_by_size = {}
for N in grid_sizes:
    print(f"\nRunning Lenia phase scan for grid_size = {N}...")
    res = run_lenia_phase_scan(N, R, sigma_g, mu_values, steps=steps, n_trials=n_trials)
    results_by_size[N] = res
    print(f"  Activity range: [{min(res['activity_mean']):.4f}, {max(res['activity_mean']):.4f}]")

# Estimate critical point (midpoint of transition)
mu_c_estimate = 0.155  # Approximate from dossier

# Fit critical exponents
print("\n" + "="*80)
print("CRITICAL EXPONENT FITS")
print("="*80)

betas = {}
for N in grid_sizes:
    mu = np.array(results_by_size[N]['mu'])
    A = np.array(results_by_size[N]['activity_mean'])
    
    beta, A0 = fit_critical_exponent(mu, A, mu_c_estimate)
    betas[N] = beta
    print(f"Grid size N={N}: beta = {beta:.3f}")

# Visualization
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Panel 1: Raw activity curves
ax = axes[0]
colors = ['steelblue', 'coral', 'forestgreen']
for i, N in enumerate(grid_sizes):
    mu = results_by_size[N]['mu']
    A_mean = results_by_size[N]['activity_mean']
    A_std = results_by_size[N]['activity_std']
    ax.errorbar(mu, A_mean, yerr=A_std, marker='o', linewidth=2, markersize=6,
                label=f'N={N}', color=colors[i], capsize=3, alpha=0.8)

ax.axvline(mu_c_estimate, color='black', linestyle='--', linewidth=1.5, 
           label=f'μ_c ~ {mu_c_estimate:.3f}')
ax.set_xlabel('Growth Center μ', fontsize=12)
ax.set_ylabel('Activity A(μ)', fontsize=12)
ax.set_title('Lenia Order Parameter: Finite-Size Scaling', fontsize=13, weight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

# Panel 2: Log-log plot near critical point
ax = axes[1]
for i, N in enumerate(grid_sizes):
    mu = np.array(results_by_size[N]['mu'])
    A = np.array(results_by_size[N]['activity_mean'])
    
    mask = (mu > mu_c_estimate) & (A > 0.01)
    if mask.sum() > 0:
        x = mu[mask] - mu_c_estimate
        y = A[mask]
        ax.loglog(x, y, 'o-', linewidth=2, markersize=7, 
                  label=f'N={N}, β={betas[N]:.3f}', color=colors[i])

# Reference lines
x_ref = np.logspace(-2, -0.5, 50)
ax.loglog(x_ref, 0.5 * x_ref**0.05, 'k--', linewidth=1.5, alpha=0.5, label='β=0.05 (HYP-140)')
ax.loglog(x_ref, 0.3 * x_ref**0.14, 'r--', linewidth=1.5, alpha=0.5, label='β=0.14 (2D percolation)')
ax.loglog(x_ref, 0.2 * x_ref**0.50, 'b--', linewidth=1.5, alpha=0.5, label='β=0.50 (mean-field)')

ax.set_xlabel('μ - μ_c', fontsize=12)
ax.set_ylabel('Activity A', fontsize=12)
ax.set_title('Log-Log Scaling Near Critical Point', fontsize=13, weight='bold')
ax.legend(fontsize=9)
ax.grid(alpha=0.3, which='both')

# Panel 3: Beta vs system size
ax = axes[2]
sizes = list(betas.keys())
beta_vals = [betas[N] for N in sizes]
ax.plot(sizes, beta_vals, 'o-', linewidth=2.5, markersize=10, color='steelblue')
ax.axhline(0.05, color='black', linestyle='--', linewidth=1.5, label='HYP-140: β=0.05')
ax.axhline(0.14, color='red', linestyle='--', linewidth=1.5, alpha=0.6, label='2D percolation: β=0.14')
ax.axhline(0.50, color='blue', linestyle='--', linewidth=1.5, alpha=0.6, label='Mean-field: β=0.50')
ax.set_xlabel('Grid Size N', fontsize=12)
ax.set_ylabel('Fitted Exponent β', fontsize=12)
ax.set_title('Finite-Size Scaling of Critical Exponent', fontsize=13, weight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
ax.set_ylim(0, 0.7)

plt.tight_layout()
plt.savefig('shared_agora/artifacts/hyp140_lenia_exponent_verification.png', dpi=150, bbox_inches='tight')
print("\nArtifact saved: shared_agora/artifacts/hyp140_lenia_exponent_verification.png")

print("\n" + "="*80)
print("VERDICT")
print("="*80)
if all(0.03 < betas[N] < 0.08 for N in grid_sizes):
    print("HYP-140 SUPPORTED: Beta ~ 0.05 is robust across finite-size scaling.")
    print("This suggests a genuine novel universality class or quenched percolation regime.")
elif max(betas.values()) - min(betas.values()) > 0.1:
    print("STRONG FINITE-SIZE EFFECTS: Beta drifts significantly with system size.")
    print("The ultra-low exponent may be a transient artifact.")
else:
    print("INCONCLUSIVE: Need higher resolution and longer relaxation times.")
