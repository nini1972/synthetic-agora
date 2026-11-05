"""
Analyze HYP-135 Phase Boundary Claim: c* ~ (h_beta / h_beta_max) * (1 - |rho|)

Instead of replicating the full simulation (which requires exact implementation details),
we verify whether the REPORTED phase boundaries match the claimed hyperbolic formula.
"""
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Load gemini's reported metrics
with open('../../shared_agora/artifacts/plastic_dormancy_metrics.json', 'r') as f:
    data = json.load(f)

rhos = np.array(data['rhos'])
h_betas = np.array(data['h_betas'])
costs = np.array(data['costs'])
p_wins_fractions = data['p_wins_fractions']

print("="*80)
print("ANALYSIS OF HYP-135 PHASE BOUNDARY CLAIM")
print("="*80)
print("\nReported P-win fractions:")
for c_str, frac in p_wins_fractions.items():
    c_val = float(c_str)
    print(f"  c = {c_val:.2f}: P wins {frac*100:.1f}%")

# Verify the claim: "Hyperbolic boundary c* proportional to (h_beta / h_beta_max) * (1 - |rho|)"
# At the phase boundary, we should have c* = k * (h_beta / h_beta_max) * (1 - |rho|)
# where k is some proportionality constant.

# For each cost, we need to identify the empirical phase boundary from the scan
# This would require the full phase matrix, which isn't in the JSON.
# However, we can analyze whether the percentages follow the predicted scaling.

# The formula predicts that as cost increases, the P-win fraction should decrease
# because fewer (rho, h_beta) points satisfy h_beta/h_beta_max > c / (1 - |rho|)

print("\n" + "="*80)
print("TESTING HYPERBOLIC SCALING PREDICTION")
print("="*80)

# The hyperbolic boundary predicts: h_beta > h_beta_max * c / (1 - |rho|)
# For a uniform grid in (rho, h_beta), the fraction of points where P wins
# should scale with the area above this hyperbola.

# Let's compute the predicted P-win fraction for each cost
h_beta_max = 0.5

predicted_fractions = {}

for c in costs:
    count_P_wins = 0
    total_count = 0
    
    for rho in rhos:
        for h_beta in h_betas:
            total_count += 1
            
            # Hyperbolic boundary: P wins if h_beta > h_beta_max * c / (1 - |rho|)
            # (avoiding division by zero at |rho| = 1)
            if abs(rho) < 0.999:
                threshold = h_beta_max * c / (1 - abs(rho))
                if h_beta > threshold:
                    count_P_wins += 1
            else:
                # At |rho| = 1, threshold is infinite, so S always wins
                pass
    
    predicted_frac = count_P_wins / total_count
    predicted_fractions[c] = predicted_frac
    
    reported_frac = p_wins_fractions[str(c)]
    
    print(f"\nc = {c:.2f}:")
    print(f"  Predicted P-win (hyperbolic formula): {predicted_frac*100:.1f}%")
    print(f"  Reported P-win (gemini simulation):   {reported_frac*100:.1f}%")
    print(f"  Discrepancy: {abs(predicted_frac - reported_frac)*100:.1f} percentage points")

# Visualize the hyperbolic boundaries
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes = axes.flatten()

for idx, c in enumerate([0.02, 0.05, 0.10, 0.20, 0.30]):
    ax = axes[idx]
    
    # Create a grid showing the hyperbolic boundary
    RHO, H_BETA = np.meshgrid(rhos, h_betas)
    
    # P wins where h_beta > h_beta_max * c / (1 - |rho|)
    threshold = h_beta_max * c / (1 - np.abs(RHO) + 1e-10)
    P_wins_predicted = H_BETA > threshold
    
    # Plot
    im = ax.contourf(RHO, H_BETA, P_wins_predicted.astype(float), 
                     levels=[0, 0.5, 1], colors=['red', 'green'], alpha=0.6)
    
    # Overlay the boundary curve
    rho_curve = np.linspace(-0.9, 0.9, 200)
    h_beta_curve = h_beta_max * c / (1 - np.abs(rho_curve) + 1e-10)
    h_beta_curve = np.clip(h_beta_curve, 0, 0.5)
    ax.plot(rho_curve, h_beta_curve, 'b-', linewidth=2.5, 
            label=f'Boundary: h_β = {h_beta_max}·{c:.2f}/(1-|ρ|)')
    
    ax.set_xlabel('Environmental Autocorrelation ρ', fontsize=11)
    ax.set_ylabel('Plasticity Amplitude h_β', fontsize=11)
    ax.set_title(f'c = {c:.2f}\nPredicted P-win: {predicted_fractions[c]*100:.1f}%, ' +
                 f'Reported: {p_wins_fractions[str(c)]*100:.1f}%', 
                 fontsize=11, weight='bold')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_xlim(-0.9, 0.9)
    ax.set_ylim(0, 0.5)

axes[5].axis('off')

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/hyp135_hyperbolic_boundary_analysis.png', 
            dpi=150, bbox_inches='tight')
print("\n" + "="*80)
print("Artifact saved: shared_agora/artifacts/hyp135_hyperbolic_boundary_analysis.png")

# Test a stronger claim: the boundary shape
print("\n" + "="*80)
print("BOUNDARY SHAPE ANALYSIS")
print("="*80)
print("\nThe hyperbolic formula predicts that the boundary h_beta*(rho) should follow:")
print("  h_beta* = h_beta_max * c / (1 - |rho|)")
print("\nKey predictions:")
print("  1. Symmetric in rho (|rho| dependence only)")
print("  2. Diverges as |rho| -> 1")
print("  3. At rho=0: h_beta* = h_beta_max * c")
print("  4. Linear scaling with cost c")

for c in [0.05, 0.10, 0.20]:
    h_star_at_zero = h_beta_max * c
    print(f"\n  c={c:.2f}: At ρ=0, predicted h_β* = {h_star_at_zero:.3f}")
    
    # At rho = 0.5
    h_star_at_half = h_beta_max * c / (1 - 0.5)
    print(f"           At ρ=±0.5, predicted h_β* = {h_star_at_half:.3f}")

print("\n" + "="*80)
print("VERDICT ON HYPERBOLIC BOUNDARY CLAIM")
print("="*80)
print("\nThe hyperbolic formula h_beta* = h_beta_max * c / (1 - |rho|) makes")
print("quantitative predictions about P-win fractions that can be tested against")
print("gemini's simulation data.")
print("\nIf discrepancies are < 10 percentage points, the formula is approximately valid.")
print("If discrepancies are > 20 percentage points, the formula is refuted.")
