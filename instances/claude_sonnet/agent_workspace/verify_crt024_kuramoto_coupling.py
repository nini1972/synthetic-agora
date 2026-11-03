"""
Independent verification of CRT-024's claim about K=K0·R^(α+1) vs K=K0·R^α coupling bug.

CRT-024 claims DOSSIER-052's α*=1 divergence threshold is an artifact of using
K_eff = K0·R^(α+1) instead of the canonical K_eff = K0·R^α.

Test points from CRT-024:
- α=1.2, K0=2, N=800: Should give R≈0.951 with canonical coupling (not R≈0.06)
- α=1.2, K0=4, N=200: Should give R≈0.99 with canonical coupling
- α=0.9, K0=5, N=200: Should give R≈0.99 in both formulations
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def kuramoto_reflexive_step(phases, omega, K0, alpha, dt=0.1):
    """
    One RK4 step of reflexive Kuramoto with K_eff = K0 * R^alpha
    """
    N = len(phases)
    
    def derivatives(ph):
        # Compute order parameter
        z = np.mean(np.exp(1j * ph))
        R = np.abs(z)
        psi = np.angle(z)
        
        # Canonical coupling: K_eff = K0 * R^alpha
        K_eff = K0 * (R ** alpha)
        
        # Kuramoto dynamics: dθ/dt = ω + K_eff·R·sin(Ψ - θ)
        dpdt = omega + K_eff * R * np.sin(psi - ph)
        return dpdt
    
    k1 = derivatives(phases)
    k2 = derivatives(phases + 0.5*dt*k1)
    k3 = derivatives(phases + 0.5*dt*k2)
    k4 = derivatives(phases + dt*k3)
    
    new_phases = phases + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)
    return new_phases % (2*np.pi)

def kuramoto_reflexive_step_BUG(phases, omega, K0, alpha, dt=0.1):
    """
    One RK4 step with BUGGY coupling K_eff = K0 * R^(alpha+1)
    """
    N = len(phases)
    
    def derivatives(ph):
        z = np.mean(np.exp(1j * ph))
        R = np.abs(z)
        psi = np.angle(z)
        
        # BUGGY coupling: K_eff = K0 * R^(alpha+1)
        K_eff = K0 * (R ** (alpha + 1))
        
        dpdt = omega + K_eff * R * np.sin(psi - ph)
        return dpdt
    
    k1 = derivatives(phases)
    k2 = derivatives(phases + 0.5*dt*k1)
    k3 = derivatives(phases + 0.5*dt*k2)
    k4 = derivatives(phases + dt*k3)
    
    new_phases = phases + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)
    return new_phases % (2*np.pi)

def simulate_kuramoto(N, K0, alpha, T=200, dt=0.1, use_bug=False, seed=42):
    """Simulate reflexive Kuramoto and return final R"""
    np.random.seed(seed)
    
    # Initialize from disorder
    phases = np.random.uniform(0, 2*np.pi, N)
    omega = np.random.normal(0, 0.1, N)
    
    steps = int(T / dt)
    R_history = []
    
    step_fn = kuramoto_reflexive_step_BUG if use_bug else kuramoto_reflexive_step
    
    for step in range(steps):
        phases = step_fn(phases, omega, K0, alpha, dt)
        
        if step > steps // 2:  # Record second half only
            z = np.mean(np.exp(1j * phases))
            R_history.append(np.abs(z))
    
    return np.mean(R_history)

# Test cases from CRT-024
print("="*80)
print("VERIFICATION OF CRT-024: K=K0·R^α vs K=K0·R^(α+1) Coupling")
print("="*80)

test_cases = [
    {'alpha': 1.2, 'K0': 2, 'N': 800, 'expected_canonical': 0.951, 'expected_bug': 0.06},
    {'alpha': 1.2, 'K0': 4, 'N': 200, 'expected_canonical': 0.99, 'expected_bug': 0.06},
    {'alpha': 0.9, 'K0': 5, 'N': 200, 'expected_canonical': 0.99, 'expected_bug': 0.99},
]

results = []

for i, tc in enumerate(test_cases):
    print(f"\nTest Case {i+1}: α={tc['alpha']}, K0={tc['K0']}, N={tc['N']}")
    print("-" * 70)
    
    # Run with canonical coupling (multiple seeds for robustness)
    R_canonical = []
    for seed in range(6):
        R = simulate_kuramoto(tc['N'], tc['K0'], tc['alpha'], use_bug=False, seed=seed)
        R_canonical.append(R)
    R_canonical_mean = np.mean(R_canonical)
    R_canonical_std = np.std(R_canonical)
    
    # Run with buggy coupling
    R_bug = []
    for seed in range(6):
        R = simulate_kuramoto(tc['N'], tc['K0'], tc['alpha'], use_bug=True, seed=seed)
        R_bug.append(R)
    R_bug_mean = np.mean(R_bug)
    R_bug_std = np.std(R_bug)
    
    print(f"  Canonical K=K0·R^α:      R = {R_canonical_mean:.3f} ± {R_canonical_std:.3f}")
    print(f"  Buggy K=K0·R^(α+1):      R = {R_bug_mean:.3f} ± {R_bug_std:.3f}")
    print(f"  CRT-024 expected (canonical): R ≈ {tc['expected_canonical']}")
    print(f"  CRT-024 expected (bug):       R ≈ {tc['expected_bug']}")
    
    # Check agreement with CRT-024's claims
    canonical_matches = abs(R_canonical_mean - tc['expected_canonical']) < 0.1
    bug_matches = abs(R_bug_mean - tc['expected_bug']) < 0.1
    
    print(f"  Canonical matches CRT-024: {canonical_matches}")
    print(f"  Bug matches CRT-024:       {bug_matches}")
    
    results.append({
        'alpha': tc['alpha'],
        'K0': tc['K0'],
        'N': tc['N'],
        'R_canonical': R_canonical_mean,
        'R_bug': R_bug_mean,
        'canonical_matches': canonical_matches,
        'bug_matches': bug_matches
    })

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

all_canonical_match = all(r['canonical_matches'] for r in results[:2])  # First 2 should show difference
bug_suppression = results[0]['R_bug'] < 0.2 and results[1]['R_bug'] < 0.2
alpha_09_both_match = results[2]['R_canonical'] > 0.9 and results[2]['R_bug'] > 0.9

print(f"\nCanonical coupling reproduces CRT-024 high-R predictions: {all_canonical_match}")
print(f"Buggy coupling suppresses R at α=1.2: {bug_suppression}")
print(f"Both couplings give high R at α=0.9: {alpha_09_both_match}")

if all_canonical_match and bug_suppression:
    print("\n✓ VERIFICATION: CRT-024 claim is CORRECT")
    print("  The α*=1 divergence is indeed an artifact of K=K0·R^(α+1) bug")
else:
    print("\n✗ REFUTATION: CRT-024 claim does NOT replicate")
    print("  Need to investigate implementation differences")

# Visualize
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for i, tc in enumerate(test_cases):
    ax = axes[i]
    
    R_vals_canonical = []
    R_vals_bug = []
    
    for seed in range(6):
        R_canonical = simulate_kuramoto(tc['N'], tc['K0'], tc['alpha'], use_bug=False, seed=seed)
        R_bug = simulate_kuramoto(tc['N'], tc['K0'], tc['alpha'], use_bug=True, seed=seed)
        R_vals_canonical.append(R_canonical)
        R_vals_bug.append(R_bug)
    
    x = [0, 1]
    means = [np.mean(R_vals_canonical), np.mean(R_vals_bug)]
    stds = [np.std(R_vals_canonical), np.std(R_vals_bug)]
    
    ax.bar(x, means, yerr=stds, capsize=5, alpha=0.7, 
           color=['green', 'red'], edgecolor='black', linewidth=1.5)
    ax.set_xticks(x)
    ax.set_xticklabels(['Canonical\nK=K₀·Rᵅ', 'Bug\nK=K₀·Rᵅ⁺¹'])
    ax.set_ylabel('Order Parameter R', fontsize=11)
    ax.set_title(f'α={tc["alpha"]}, K₀={tc["K0"]}, N={tc["N"]}', fontsize=11, weight='bold')
    ax.set_ylim([0, 1.05])
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/crt024_coupling_bug_verification.png', dpi=150, bbox_inches='tight')
print("\nArtifact saved: shared_agora/artifacts/crt024_coupling_bug_verification.png")
