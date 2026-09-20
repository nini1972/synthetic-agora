#!/usr/bin/env python3
"""
Empirical validation of HYP-043: CML Phase Transitions via Coupling-Driver Parameter Interplay
Tests the three-regime hypothesis from Frontier Dossier #021
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def cml_evolution(N=50, r=3.8, epsilon=0.1, steps=200, x0=None):
    """
    Simulate 1D Coupled Map Lattice with logistic maps
    x_i^(t+1) = (1-ε)f(x_i^t) + ε/2[f(x_{i-1}^t) + f(x_{i+1}^t)]
    where f(x) = rx(1-x)
    """
    if x0 is None:
        x = np.random.random(N)
    else:
        x = x0.copy()
    
    trajectory = np.zeros((steps, N))
    complexities = np.zeros(steps)
    
    for t in range(steps):
        # Logistic map evolution
        f_x = r * x * (1 - x)
        
        # Nearest neighbor coupling with periodic boundary
        x_left = np.roll(f_x, 1)  # x_{i-1}
        x_right = np.roll(f_x, -1)  # x_{i+1}
        
        # CML update rule
        x = (1 - epsilon) * f_x + epsilon/2 * (x_left + x_right)
        
        trajectory[t] = x
        complexities[t] = np.std(x)  # Spatial complexity metric
    
    return trajectory, complexities

# Test parameters from Dossier #021
epsilon_values = [0.01, 0.1, 0.5]
r_values = [3.5, 3.8, 4.0]
steps = 100
settling_time = 50  # Allow transients to die out

print("=== CML Phase Transition Validation ===")
print("Testing HYP-043 from Frontier Dossier #021\n")

results = {}
final_complexities = {}

# Run simulations
for r in r_values:
    for epsilon in epsilon_values:
        traj, complexity = cml_evolution(N=50, r=r, epsilon=epsilon, steps=steps)
        
        # Average complexity over final half (post-transient)
        steady_complexity = np.mean(complexity[settling_time:])
        final_complexities[(r, epsilon)] = steady_complexity
        results[(r, epsilon)] = (traj, complexity)
        
        print(f"r={r:.1f}, ε={epsilon:.2f}: Final complexity = {steady_complexity:.4f}")

print("\n=== REGIME ANALYSIS ===")

# Test Regime 1: High-driving (r=4.0) should be uniformly chaotic
r4_complexities = [final_complexities[(4.0, eps)] for eps in epsilon_values]
r4_variance = np.var(r4_complexities)
print(f"Regime 1 (r=4.0): Complexities = {r4_complexities}")
print(f"Variance across ε values: {r4_variance:.6f} (should be LOW for uniform chaos)")

# Test Regime 2: Moderate-driving (r=3.8) should show coupling sensitivity
r38_complexities = [final_complexities[(3.8, eps)] for eps in epsilon_values]
r38_decreasing = all(r38_complexities[i] >= r38_complexities[i+1] for i in range(len(r38_complexities)-1))
print(f"Regime 2 (r=3.8): Complexities = {r38_complexities}")
print(f"Monotonic decrease with coupling: {r38_decreasing}")

# Test Regime 3: Low-driving (r=3.5) should be uniformly low complexity
r35_complexities = [final_complexities[(3.5, eps)] for eps in epsilon_values]
r35_low = all(comp < 0.1 for comp in r35_complexities)
print(f"Regime 3 (r=3.5): Complexities = {r35_complexities}")
print(f"All low complexity (< 0.1): {r35_low}")

# Create visualization
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Complexity vs time for different regimes
colors = ['red', 'green', 'blue']
for i, epsilon in enumerate(epsilon_values):
    _, comp38 = results[(3.8, epsilon)]
    ax1.plot(comp38, color=colors[i], label=f'ε={epsilon}', alpha=0.7)
ax1.set_title('Regime 2: r=3.8 (Coupling Sensitivity)')
ax1.set_xlabel('Time steps')
ax1.set_ylabel('Spatial complexity σ')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Final complexity heatmap
r_grid, eps_grid = np.meshgrid(r_values, epsilon_values)
complexity_matrix = np.array([[final_complexities[(r, eps)] for r in r_values] for eps in epsilon_values])

im = ax2.imshow(complexity_matrix, aspect='auto', cmap='plasma', 
                extent=[min(r_values)-0.1, max(r_values)+0.1, 
                       min(epsilon_values), max(epsilon_values)])
ax2.set_xlabel('Driving parameter r')
ax2.set_ylabel('Coupling strength ε')
ax2.set_title('Final Complexity Landscape')
plt.colorbar(im, ax=ax2, label='Complexity σ')

# Plot 3: Coupling sensitivity at r=3.8
ax3.plot(epsilon_values, r38_complexities, 'o-', color='red', linewidth=2)
ax3.set_xlabel('Coupling strength ε')
ax3.set_ylabel('Final complexity')
ax3.set_title('Coupling Sensitivity (r=3.8)')
ax3.grid(True, alpha=0.3)

# Plot 4: Cross-regime comparison
width = 0.25
x_pos = np.arange(len(epsilon_values))
ax4.bar(x_pos - width, [final_complexities[(3.5, eps)] for eps in epsilon_values], 
        width, label='r=3.5', alpha=0.7)
ax4.bar(x_pos, [final_complexities[(3.8, eps)] for eps in epsilon_values], 
        width, label='r=3.8', alpha=0.7)
ax4.bar(x_pos + width, [final_complexities[(4.0, eps)] for eps in epsilon_values], 
        width, label='r=4.0', alpha=0.7)
ax4.set_xlabel('Coupling strength')
ax4.set_ylabel('Final complexity')
ax4.set_title('Cross-Regime Comparison')
ax4.set_xticks(x_pos)
ax4.set_xticklabels([f'ε={eps}' for eps in epsilon_values])
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/cml_phase_validation.png', dpi=150, bbox_inches='tight')
plt.close()

# Hypothesis validation summary
print("\n=== HYPOTHESIS VALIDATION ===")
print(f"REGIME 1 (Uniform chaos): {'SUPPORTED' if r4_variance < 0.01 else 'REFUTED'}")
print(f"REGIME 2 (Coupling sensitivity): {'SUPPORTED' if r38_decreasing else 'REFUTED'}")
print(f"REGIME 3 (Low complexity): {'SUPPORTED' if r35_low else 'REFUTED'}")

# Additional test: Check for critical coupling
if len(r38_complexities) >= 3:
    coupling_derivative = np.diff(r38_complexities)
    max_sensitivity = np.argmax(np.abs(coupling_derivative))
    print(f"Maximum coupling sensitivity between ε={epsilon_values[max_sensitivity]:.2f} and ε={epsilon_values[max_sensitivity+1]:.2f}")

print(f"\nArtifact saved: shared_agora/artifacts/cml_phase_validation.png")