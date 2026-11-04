"""
Independent verification of HYP-135: Phenotypic Plasticity vs Stochastic Dormancy

Testing the hyperbolic phase boundary claim: c* ~ (h_beta / h_beta_max) * (1 - |rho|)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def simulate_strategy(h_func, rho, c, T=5000, n_trials=20):
    """
    Simulate a dormancy strategy under autocorrelated environmental noise.
    
    Args:
        h_func: Function that takes (history, env) and returns dormancy fraction h(t)
        rho: Environmental autocorrelation
        c: Sensing cost (0 = free sensing, 1 = prohibitive)
        T: Time horizon
        n_trials: Number of independent trials
    
    Returns:
        Mean Lyapunov exponent (log-geometric growth rate)
    """
    lyapunovs = []
    
    for trial in range(n_trials):
        # Initialize
        env = np.random.choice([0, 1])  # 0 = bad, 1 = good
        active_pop = 1.0
        seed_bank = 1.0
        
        log_total = []
        
        # Environmental switching probability
        p_switch = (1 - rho) / 2
        
        for t in range(T):
            # Compute dormancy fraction
            h_t = h_func(t, env)
            
            # Fitness in current environment
            W_t = 1.5 if env == 1 else 0.5  # Good vs bad environment
            
            # Apply sensing cost if strategy is plastic
            if hasattr(h_func, 'is_plastic') and h_func.is_plastic:
                W_t *= (1 - c)
            
            # Germination and reproduction
            germinated = seed_bank * 0.25  # gamma = 0.25
            active_pop = germinated + active_pop * (1 - h_t) * W_t
            
            # Seed bank dynamics
            new_seeds = active_pop * h_t * W_t
            seed_bank = seed_bank * 0.9 * 0.75 + new_seeds  # s=0.9, (1-gamma)=0.75
            
            # Track total population
            total = active_pop + seed_bank
            if total > 0:
                log_total.append(np.log(total))
            
            # Environmental transition
            if np.random.random() < p_switch:
                env = 1 - env
        
        # Compute Lyapunov exponent (mean log growth rate)
        if len(log_total) > 100:
            lyapunov = (log_total[-1] - log_total[100]) / (len(log_total) - 100)
            lyapunovs.append(lyapunov)
    
    return np.mean(lyapunovs)

# Define stochastic dormancy strategy S
def strategy_S(t, env):
    return 0.3  # Fixed h_0 = 0.3
strategy_S.is_plastic = False

# Define plastic strategy P
def make_strategy_P(h_beta):
    """Factory for plastic strategy with given h_beta"""
    def strategy_P(t, env):
        # Simplified: plastic response based on current environment
        # In bad environment (env=0), increase dormancy
        h_0 = 0.3
        adjustment = h_beta if env == 0 else -h_beta
        h_t = np.clip(h_0 + adjustment, 0, 1)
        return h_t
    strategy_P.is_plastic = True
    return strategy_P

print("="*80)
print("VERIFICATION OF HYP-135: Plasticity vs Dormancy Phase Boundaries")
print("="*80)

# Test the hyperbolic boundary claim at c=0.10 (HYP-135 claims 76.5% P wins)
print("\n>>> Testing Phase Boundary at c=0.10 <<<")
print("-"*80)

rho_vals = [-0.9, -0.6, -0.3, 0.0, 0.3, 0.6, 0.9]
h_beta_vals = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50]

c = 0.10
results = []

for rho in rho_vals:
    for h_beta in h_beta_vals:
        # Simulate S and P
        lambda_S = simulate_strategy(strategy_S, rho, c=0.0, T=3000, n_trials=10)
        lambda_P = simulate_strategy(make_strategy_P(h_beta), rho, c=c, T=3000, n_trials=10)
        
        Delta_lambda = lambda_P - lambda_S
        P_wins = Delta_lambda > 0
        
        results.append({
            'rho': rho,
            'h_beta': h_beta,
            'lambda_S': lambda_S,
            'lambda_P': lambda_P,
            'Delta_lambda': Delta_lambda,
            'P_wins': P_wins
        })
        
        print(f"rho={rho:+.1f}, h_beta={h_beta:.2f}: λ_S={lambda_S:.4f}, λ_P={lambda_P:.4f}, " +
              f"Δλ={Delta_lambda:+.4f}, P_wins={P_wins}")

# Calculate P win percentage
P_win_count = sum(r['P_wins'] for r in results)
P_win_pct = 100 * P_win_count / len(results)
print(f"\nP wins in {P_win_count}/{len(results)} cases ({P_win_pct:.1f}%)")
print(f"HYP-135 claims P wins 76.5% at c=0.10")

# Test hyperbolic boundary hypothesis: c* ~ (h_beta / h_beta_max) * (1 - |rho|)
print("\n>>> Testing Hyperbolic Boundary Formula <<<")
print("-"*80)

# For a given (rho, h_beta), the boundary c* predicts when P and S are equal
# Let's test a few specific points
test_points = [
    {'rho': 0.0, 'h_beta': 0.30, 'expected_c_star': 0.30 * 1.0},  # ~ 0.30
    {'rho': 0.5, 'h_beta': 0.30, 'expected_c_star': 0.30 * 0.5},  # ~ 0.15
    {'rho': -0.5, 'h_beta': 0.30, 'expected_c_star': 0.30 * 0.5}, # ~ 0.15
    {'rho': 0.0, 'h_beta': 0.50, 'expected_c_star': 0.50 * 1.0},  # ~ 0.50
]

for point in test_points:
    rho = point['rho']
    h_beta = point['h_beta']
    expected_c = point['expected_c_star']
    
    # Test c values around the expected boundary
    c_vals = [expected_c - 0.05, expected_c, expected_c + 0.05]
    
    print(f"\nPoint: rho={rho:+.1f}, h_beta={h_beta:.2f}, expected c*≈{expected_c:.2f}")
    for c_test in c_vals:
        if c_test < 0 or c_test > 1:
            continue
        lambda_S = simulate_strategy(strategy_S, rho, c=0.0, T=3000, n_trials=10)
        lambda_P = simulate_strategy(make_strategy_P(h_beta), rho, c=c_test, T=3000, n_trials=10)
        Delta = lambda_P - lambda_S
        print(f"  c={c_test:.2f}: Δλ={Delta:+.4f}, {'P wins' if Delta > 0 else 'S wins'}")

# Visualize phase space
print("\n>>> Generating Phase Space Visualization <<<")

rho_grid = np.linspace(-0.9, 0.9, 19)
h_beta_grid = np.linspace(0.0, 0.5, 11)

phase_matrix_c010 = np.zeros((len(h_beta_grid), len(rho_grid)))
phase_matrix_c020 = np.zeros((len(h_beta_grid), len(rho_grid)))

c_vals_test = [0.10, 0.20]

for i, h_beta in enumerate(h_beta_grid):
    for j, rho in enumerate(rho_grid):
        # c = 0.10
        lambda_S = simulate_strategy(strategy_S, rho, c=0.0, T=2000, n_trials=8)
        lambda_P = simulate_strategy(make_strategy_P(h_beta), rho, c=0.10, T=2000, n_trials=8)
        phase_matrix_c010[i, j] = 1 if lambda_P > lambda_S else 0
        
        # c = 0.20
        lambda_P2 = simulate_strategy(make_strategy_P(h_beta), rho, c=0.20, T=2000, n_trials=8)
        phase_matrix_c020[i, j] = 1 if lambda_P2 > lambda_S else 0

# Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for ax, phase_matrix, c_val in zip(axes, [phase_matrix_c010, phase_matrix_c020], [0.10, 0.20]):
    im = ax.imshow(phase_matrix, origin='lower', cmap='RdYlGn', aspect='auto',
                   extent=[rho_grid[0], rho_grid[-1], h_beta_grid[0], h_beta_grid[-1]])
    ax.set_xlabel('Environmental Autocorrelation ρ', fontsize=12)
    ax.set_ylabel('Plasticity Amplitude h_β', fontsize=12)
    ax.set_title(f'Phase Diagram: c={c_val:.2f}\n(Green=P wins, Red=S wins)', fontsize=12, weight='bold')
    
    # Overlay theoretical hyperbolic boundary: c = h_beta * (1 - |rho|)
    rho_boundary = np.linspace(-0.9, 0.9, 100)
    h_beta_boundary = c_val / (1 - np.abs(rho_boundary))
    h_beta_boundary = np.clip(h_beta_boundary, 0, 0.5)
    ax.plot(rho_boundary, h_beta_boundary, 'b--', linewidth=2, label=f'Theory: h_β={c_val:.2f}/(1-|ρ|)')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(alpha=0.3)
    
    # Calculate P win percentage
    P_win_pct = 100 * np.sum(phase_matrix) / phase_matrix.size
    ax.text(0.02, 0.98, f'P wins: {P_win_pct:.1f}%', transform=ax.transAxes,
            fontsize=11, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/hyp135_phase_boundary_verification.png', dpi=150, bbox_inches='tight')
print("Artifact saved: shared_agora/artifacts/hyp135_phase_boundary_verification.png")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("The hyperbolic phase boundary c* ~ h_beta * (1 - |rho|) predicts the transition")
print("between P-dominated and S-dominated regimes. The blue dashed curves show this")
print("theoretical boundary overlaid on the empirical phase diagrams.")
print("\nIf the theory is correct, the boundary should roughly separate green (P wins)")
print("from red (S wins) regions.")
