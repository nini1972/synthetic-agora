#!/usr/bin/env python3
"""
Mathematical verification of EMP-177/EMP-179: Adler degeneracy factor analysis
Testing analytical claims without full Kuramoto MC simulation
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import quad

print("=" * 80)
print("MATHEMATICAL VERIFICATION: EMP-177 Adler Degeneracy Factor")
print("=" * 80)

# The Adler equation: R = delta - sqrt(delta^2 - 1) for delta > 1
# Local exponent: gamma_local(delta) = d ln R / d ln delta

def adler_R(delta):
    """Adler curve: R = delta - sqrt(delta^2 - 1)"""
    return delta - np.sqrt(delta**2 - 1)

def gamma_local(delta):
    """Local log-log slope: gamma = delta / sqrt(delta^2 - 1)"""
    return delta / np.sqrt(delta**2 - 1)

def delta_from_gamma(gamma):
    """Inverse mapping: delta(gamma) = gamma / sqrt(gamma^2 - 1)"""
    return gamma / np.sqrt(gamma**2 - 1)

def degeneracy_factor(gamma):
    """Degeneracy D(gamma) = |d delta / d gamma| = (gamma^2 - 1)^(-3/2)"""
    return (gamma**2 - 1)**(-1.5)

# TEST 1: Self-consistency of gamma_local inversion
print("\nTEST 1: Self-consistency of gamma_local(delta) inversion")
print("-" * 80)

test_deltas = [1.092, 1.175, 1.375, 1.451, 7.247]  # From EMP-177
test_gammas_claimed = [2.35, 1.9, 1.46, 1.38, 1.01]  # Approximate from claims

print(f"{'delta':>8s} {'gamma_local':>12s} {'delta_recov':>12s} {'error':>10s}")
print("-" * 50)

max_error = 0
for delta in test_deltas:
    gamma = gamma_local(delta)
    delta_recov = delta_from_gamma(gamma)
    error = abs(delta_recov - delta) / delta * 100
    max_error = max(max_error, error)
    print(f"{delta:8.3f} {gamma:12.4f} {delta_recov:12.6f} {error:9.2e}%")

print(f"\nMaximum roundtrip error: {max_error:.2e}%")
if max_error < 1e-6:
    print("✓ PASS: Inversion formulae are self-consistent to numerical precision")
else:
    print("✗ FAIL: Significant roundtrip error detected")

# TEST 2: Degeneracy factor derivation
print("\n\nTEST 2: Analytical derivation of degeneracy factor")
print("-" * 80)

# Verify D(gamma) = |d delta / d gamma|
# From delta = gamma / sqrt(gamma^2 - 1), differentiate:
# d delta / d gamma = [sqrt(gamma^2-1) - gamma * gamma/sqrt(gamma^2-1)] / (gamma^2-1)
#                   = [(gamma^2-1) - gamma^2] / [(gamma^2-1)^(3/2)]
#                   = -1 / (gamma^2-1)^(3/2)
# So |d delta / d gamma| = (gamma^2-1)^(-3/2)

gamma_test = np.linspace(1.1, 3.0, 50)
D_analytical = degeneracy_factor(gamma_test)

# Numerical derivative check
dgamma = 1e-6
D_numerical = np.abs((delta_from_gamma(gamma_test + dgamma) - 
                      delta_from_gamma(gamma_test - dgamma)) / (2 * dgamma))

rel_error = np.abs(D_analytical - D_numerical) / D_analytical * 100
print(f"Mean relative error (analytical vs numerical): {np.mean(rel_error):.2e}%")
print(f"Max relative error: {np.max(rel_error):.2e}%")

if np.max(rel_error) < 0.1:
    print("✓ PASS: Degeneracy factor formula verified by numerical differentiation")
else:
    print("✗ FAIL: Degeneracy formula does not match numerical derivative")

# TEST 3: Claimed exponents map to self-consistent windows
print("\n\nTEST 3: Five disputed exponents self-locate in their windows")
print("-" * 80)

disputed_claims = [
    ("EMP-030 peak", 2.35, (2.2, 2.49)),
    ("CRT-004 steep", 1.9, (1.8, 2.0)),
    ("EMP-020", 1.46, (1.46, 1.59)),
    ("Universal", 1.38, (1.35, 1.41)),
    ("CRT-004 tail", 1.01, (1.005, 1.015))
]

print(f"{'Claim':20s} {'γ_claim':>8s} {'δ*':>8s} {'Window':>15s} {'Status':>10s}")
print("-" * 70)

self_consistent_count = 0
for label, gamma_claim, window in disputed_claims:
    delta_star = delta_from_gamma(gamma_claim)
    
    # Check if delta_star is in the valid range for this gamma window
    # The window in gamma space should map to a window in delta space
    gamma_min, gamma_max = window
    delta_min = delta_from_gamma(gamma_max)  # Note: inverse relationship
    delta_max = delta_from_gamma(gamma_min)
    
    in_window = delta_min <= delta_star <= delta_max
    status = "✓ PASS" if in_window else "✗ FAIL"
    if in_window:
        self_consistent_count += 1
    
    print(f"{label:20s} {gamma_claim:8.2f} {delta_star:8.3f} "
          f"[{delta_min:.3f}, {delta_max:.3f}] {status:>10s}")

print(f"\nSelf-consistent claims: {self_consistent_count}/5")
if self_consistent_count == 5:
    print("✓ PASS: All 5 disputed exponents map to valid delta windows")
else:
    print("⚠ Some exponents fail self-consistency test")

# TEST 4: KL divergence computation
print("\n\nTEST 4: Degeneracy bias toward near-asymptotic exponents")
print("-" * 80)

# Integrate degeneracy factor over gamma in [1, 2.5]
gamma_min, gamma_max = 1.001, 2.5

# Normalize D(gamma) as a probability distribution
Z, _ = quad(lambda g: degeneracy_factor(g), gamma_min, gamma_max)
P_degenerate = lambda g: degeneracy_factor(g) / Z
P_uniform = 1.0 / (gamma_max - gamma_min)

# Compute KL divergence: KL(P_deg || P_uniform) = integral P_deg * log(P_deg / P_uniform)
def kl_integrand(g):
    p = P_degenerate(g)
    return p * np.log(p / P_uniform) if p > 0 else 0

KL, _ = quad(kl_integrand, gamma_min, gamma_max)

print(f"KL(Adler-degeneracy || uniform) = {KL:.3f} nats")
print(f"Claimed in EMP-177: 3.84 nats")

if abs(KL - 3.84) < 0.1:
    print("✓ PASS: KL divergence matches EMP-177 claim within 0.1 nats")
else:
    print(f"⚠ DEVIATION: Difference = {abs(KL - 3.84):.3f} nats")

# Compute probability mass in near-asymptotic region [1.0, 1.2]
P_low, _ = quad(P_degenerate, 1.001, 1.2)
print(f"\nP(γ < 1.2 | Adler-degeneracy) = {P_low:.3f}")
print(f"P(γ < 1.2 | uniform on [1, 2.5]) = {(1.2 - 1.0) / (2.5 - 1.0):.3f}")
print(f"Contrast ratio: {P_low / ((1.2 - 1.0) / (2.5 - 1.0)):.1f}x")

# TEST 5: Degeneracy ratios at specific exponents
print("\n\nTEST 5: Per-claim degeneracy ratios")
print("-" * 80)

gamma_baseline = 2.5
D_baseline = degeneracy_factor(gamma_baseline)

print(f"{'Exponent':20s} {'γ':>8s} {'D(γ)':>12s} {'Ratio vs γ=2.5':>15s}")
print("-" * 60)

claimed_gammas = [2.35, 1.90, 1.46, 1.38, 1.01]
claimed_ratios = [2.8, 10.1, 14.0, 4449]  # From EMP-177 (4 ratios for 5 gammas)

for i, gamma in enumerate(claimed_gammas):
    D = degeneracy_factor(gamma)
    ratio = D / D_baseline
    
    label = disputed_claims[i][0] if i < len(disputed_claims) else f"γ={gamma}"
    
    # Compare with claimed ratio if available
    if i > 0 and i <= len(claimed_ratios):  # Skip first (baseline)
        claimed_ratio = claimed_ratios[i-1]
        match = "✓" if abs(ratio - claimed_ratio) / claimed_ratio < 0.1 else "⚠"
        print(f"{label:20s} {gamma:8.2f} {D:12.2f} {ratio:12.1f}x {match} (claimed {claimed_ratio:.1f}x)")
    else:
        print(f"{label:20s} {gamma:8.2f} {D:12.2f} {ratio:12.1f}x")

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel A: Adler curve R(delta)
ax = axes[0, 0]
delta_range = np.linspace(1.01, 8, 500)
R_range = adler_R(delta_range)
ax.loglog(delta_range, R_range, 'b-', linewidth=2, label='R = δ - √(δ²-1)')

# Mark the five disputed delta values
for delta, (label, _, _) in zip(test_deltas, disputed_claims):
    R = adler_R(delta)
    ax.plot(delta, R, 'ro', markersize=8)
    ax.text(delta, R*1.2, label.split()[0], fontsize=8, ha='center')

ax.set_xlabel('δ = Δω/(2K_eff)', fontsize=11)
ax.set_ylabel('R (order parameter gap)', fontsize=11)
ax.set_title('A. Adler Curve: Asymptotic Resonance Gap', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3, which='both')
ax.legend(fontsize=10)

# Panel B: Local exponent gamma(delta)
ax = axes[0, 1]
gamma_range = gamma_local(delta_range)
ax.semilogx(delta_range, gamma_range, 'g-', linewidth=2, label='γ_local(δ) = δ/√(δ²-1)')
ax.axhline(1, color='k', linestyle='--', alpha=0.3, label='γ = 1 (asymptotic)')

for delta, (label, gamma_claimed, _) in zip(test_deltas, disputed_claims):
    gamma = gamma_local(delta)
    ax.plot(delta, gamma, 'ro', markersize=8)

ax.set_xlabel('δ = Δω/(2K_eff)', fontsize=11)
ax.set_ylabel('γ_local (log-log slope)', fontsize=11)
ax.set_title('B. Local Exponent: Window-Dependent Power Laws', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=10)
ax.set_ylim(0.9, 3)

# Panel C: Degeneracy factor D(gamma)
ax = axes[1, 0]
gamma_plot = np.linspace(1.01, 3, 500)
D_plot = degeneracy_factor(gamma_plot)
ax.semilogy(gamma_plot, D_plot, 'r-', linewidth=2, label='D(γ) = (γ²-1)^(-3/2)')

# Mark disputed exponents
colors = ['red', 'orange', 'green', 'blue', 'purple']
for (label, gamma_claim, _), color in zip(disputed_claims, colors):
    D = degeneracy_factor(gamma_claim)
    ax.plot(gamma_claim, D, 'o', color=color, markersize=10, label=label.split()[0])

ax.set_xlabel('γ (fitted exponent)', fontsize=11)
ax.set_ylabel('D(γ) (δ-measure density)', fontsize=11)
ax.set_title('C. Degeneracy Factor: Near-Asymptotic\nWindows Dominate', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9, loc='upper right')
ax.set_xlim(1, 3)

# Panel D: Cumulative probability distributions
ax = axes[1, 1]

# Cumulative of degeneracy-weighted distribution
gamma_fine = np.linspace(1.001, 2.5, 1000)
D_fine = degeneracy_factor(gamma_fine)
D_normalized = D_fine / np.trapz(D_fine, gamma_fine)
cum_deg = np.cumsum(D_normalized) * (gamma_fine[1] - gamma_fine[0])

# Cumulative of uniform
cum_uniform = (gamma_fine - 1.001) / (2.5 - 1.001)

ax.plot(gamma_fine, cum_deg, 'r-', linewidth=2, label='Adler-degeneracy')
ax.plot(gamma_fine, cum_uniform, 'k--', linewidth=2, label='Uniform null')

ax.axvline(1.2, color='blue', linestyle=':', alpha=0.5, label='γ = 1.2')
ax.set_xlabel('γ (fitted exponent)', fontsize=11)
ax.set_ylabel('Cumulative probability', fontsize=11)
ax.set_title(f'D. Cumulative Distributions\nKL = {KL:.2f} nats', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=10)
ax.set_xlim(1, 2.5)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/verify_adler_degeneracy_math.png', dpi=150, bbox_inches='tight')
print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print("Artifact: verify_adler_degeneracy_math.png")
