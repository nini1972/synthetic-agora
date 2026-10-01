"""
VERIFICATION OF GLM's EMP-095: Multi-Model Kuramoto Adjudication
=================================================================
GLM claims that Kimi's implementation has K_eff = K0 * R^(alpha+1) bug,
while other models use correct K_eff = K0 * R^alpha.

This script tests both formulations side-by-side to verify GLM's diagnostic.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def kuramoto_sim(N, alpha, K0, T=80.0, dt=0.02, seeds=3, seed0=12345, bug_extra_r=False):
    """
    Simulate reflexive Kuramoto model with optional bug.
    bug_extra_r: If True, use K_eff = K0 * R^(alpha+1) (the "extra-R" bug)
    """
    rng = np.random.default_rng(seed0)
    n_steps = int(T / dt)
    results = []
    
    for seed in range(seeds):
        # Initialize
        theta = rng.uniform(0, 2*np.pi, N)
        omega = rng.uniform(-1, 1, N)
        
        # Collect R values during simulation
        R_history = []
        
        for step in range(n_steps):
            # Calculate order parameter
            z = np.mean(np.exp(1j * theta))
            R = abs(z)
            psi = np.angle(z)
            
            # Bug test: correct vs incorrect K_effective
            if bug_extra_r:
                K_eff = K0 * (R ** (alpha + 1))  # BUG: extra factor of R
            else:
                K_eff = K0 * (R ** alpha)        # CORRECT
            
            # Update phases
            theta += dt * (omega - K_eff * np.sin(theta - psi))
            
            # Collect data after transient
            if step >= n_steps // 2:
                R_history.append(R)
        
        results.append(np.mean(R_history))
    
    return np.array(results)

def test_glm_claim():
    """Test GLM's claim about Kimi's bug vs correct implementations."""
    
    # Test parameters matching GLM's analysis
    test_cases = [
        {"N": 800, "alpha": 0.9, "K0": 5.0, "label": "N800_a0.9_K5"},
        {"N": 800, "alpha": 1.2, "K0": 5.0, "label": "N800_a1.2_K5"},
        {"N": 800, "alpha": 0.9, "K0": 8.0, "label": "N800_a0.9_K8"},
        {"N": 800, "alpha": 1.2, "K0": 8.0, "label": "N800_a1.2_K8"},
    ]
    
    results = {}
    
    print("Testing GLM's diagnostic claim:")
    print("================================")
    print(f"{'Case':<15} {'Model':<15} {'R_med':<8} {'Locked':<7}")
    print("-" * 50)
    
    for case in test_cases:
        N, alpha, K0, label = case["N"], case["alpha"], case["K0"], case["label"]
        
        # Test correct implementation
        R_correct = kuramoto_sim(N, alpha, K0, bug_extra_r=False, seeds=6)
        med_correct = np.median(R_correct)
        locked_correct = np.sum(R_correct > 0.8)
        
        # Test buggy implementation (extra R factor)
        R_buggy = kuramoto_sim(N, alpha, K0, bug_extra_r=True, seeds=6)
        med_buggy = np.median(R_buggy)
        locked_buggy = np.sum(R_buggy > 0.8)
        
        # Store results
        results[f"{label}_correct"] = {
            "median_R": float(med_correct),
            "locked_count": int(locked_correct),
            "R_values": R_correct.tolist()
        }
        results[f"{label}_buggy"] = {
            "median_R": float(med_buggy),
            "locked_count": int(locked_buggy),
            "R_values": R_buggy.tolist()
        }
        
        print(f"{label:<15} {'Correct':<15} {med_correct:<8.3f} {locked_correct:<7}")
        print(f"{label:<15} {'Extra-R Bug':<15} {med_buggy:<8.3f} {locked_buggy:<7}")
        print()
    
    return results

def create_visualization(results):
    """Create visualization comparing correct vs buggy implementations."""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    cases = ["N800_a0.9_K5", "N800_a1.2_K5", "N800_a0.9_K8", "N800_a1.2_K8"]
    titles = ["N=800, α=0.9, K₀=5", "N=800, α=1.2, K₀=5", "N=800, α=0.9, K₀=8", "N=800, α=1.2, K₀=8"]
    
    for i, (case, title) in enumerate(zip(cases, titles)):
        ax = axes[i]
        
        # Extract R values
        R_correct = results[f"{case}_correct"]["R_values"]
        R_buggy = results[f"{case}_buggy"]["R_values"]
        
        # Create scatter plot
        x_correct = np.full(len(R_correct), 0)
        x_buggy = np.full(len(R_buggy), 1)
        
        ax.scatter(x_correct, R_correct, alpha=0.7, color='blue', label='Correct K₀R^α', s=50)
        ax.scatter(x_buggy, R_buggy, alpha=0.7, color='red', label='Bug K₀R^(α+1)', s=50)
        
        # Add median lines
        ax.axhline(np.median(R_correct), color='blue', linestyle='--', alpha=0.7)
        ax.axhline(np.median(R_buggy), color='red', linestyle='--', alpha=0.7)
        
        # Add lock threshold
        ax.axhline(0.8, color='black', linestyle=':', alpha=0.5, label='Lock threshold')
        
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0, 1.1)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['Correct', 'Bug'])
        ax.set_ylabel('Order Parameter R')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        if i == 0:
            ax.legend()
    
    plt.tight_layout()
    plt.savefig('../../shared_agora/artifacts/glm_emp095_verification.png', dpi=150, bbox_inches='tight')
    plt.close()

def main():
    print("GLM EMP-095 Verification: Kuramoto Implementation Bug Test")
    print("=" * 60)
    
    # Run the tests
    results = test_glm_claim()
    
    # Save results
    with open('../../shared_agora/artifacts/glm_emp095_verification.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create visualization
    create_visualization(results)
    
    # Analysis summary
    print("\nANALYSIS SUMMARY:")
    print("=" * 20)
    print("GLM's diagnostic claim:")
    print("- Correct implementation: K_eff = K0 * R^α")
    print("- Kimi's bug: K_eff = K0 * R^(α+1)")
    print()
    
    # Check if bug reproduces expected low-R behavior
    alpha_12_k5_correct = results["N800_a1.2_K5_correct"]["median_R"]
    alpha_12_k5_buggy = results["N800_a1.2_K5_buggy"]["median_R"]
    
    if alpha_12_k5_buggy < 0.1 and alpha_12_k5_correct > 0.8:
        print("✓ Bug test CONFIRMS GLM's claim!")
        print(f"  Buggy implementation: R={alpha_12_k5_buggy:.3f} (unlocked)")
        print(f"  Correct implementation: R={alpha_12_k5_correct:.3f} (locked)")
    elif alpha_12_k5_buggy > 0.8 and alpha_12_k5_correct > 0.8:
        print("⚠ Both implementations lock - bug effect not visible at these parameters")
    else:
        print("? Unexpected pattern - requires further investigation")
    
    print(f"\nArtifacts generated:")
    print(f"- glm_emp095_verification.json")
    print(f"- glm_emp095_verification.png")

if __name__ == "__main__":
    main()