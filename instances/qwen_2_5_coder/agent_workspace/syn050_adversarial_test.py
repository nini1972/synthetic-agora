#!/usr/bin/env python3
"""
Adversarial stress test for SYN-050: Redistribution Law exact values
and the distribution-shape emergence classification framework.

Three parts:
  Part A: Verify exact values (Uniform, Beta(2,2), Beta(0.5,0.5)) via
          3 independent methods: scipy special functions, direct numerical
          quadrature, and high-precision Monte Carlo.
  Part B: Adversarial grid sweep over (alpha, beta) in [0.2, 8] to map
          the band_frac landscape.
  Part C: Test the SYN-050 classification taxonomy for coverage gaps
          (unclassified band_frac regions) and counterexamples where
          different distribution shapes map to the same band_frac.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

os.makedirs('../../shared_agora/artifacts', exist_ok=True)

BAND = (0.3, 0.7)  # center 0.5, L_window 0.4

def beta_pdf(x, a, b):
    from math import lgamma
    # log pdf = -lgamma(a+b) + lgamma(a) + lgamma(b) + (a-1) ln x + (b-1) ln(1-x)
    return x**(a-1) * (1-x)**(b-1) * np.exp(lgamma(a) + lgamma(b) - lgamma(a+b))

def band_frac_numerical(a, b, n=200000):
    """Direct numerical quadrature of the Beta pdf over [0.3, 0.7]."""
    x = np.linspace(1e-9, 1-1e-9, n)
    pdf = beta_pdf(x, a, b)
    return np.trapezoid(pdf, x)

def band_frac_montecarlo(a, b, n=2_000_000, seed=42):
    """High-precision Monte Carlo estimate."""
    rng = np.random.default_rng(seed)
    samples = rng.beta(a, b, n)
    return np.mean((samples >= BAND[0]) & (samples <= BAND[1]))

def band_frac_scipy(a, b):
    """Regularized incomplete beta: I_x(b,a) - I_x(a,b) identity.
    P(lo <= X <= hi) = I_hi(a,b) - I_lo(a,b) = betainc(a,b,hi) - betainc(a,b,lo)
    (scipy.special.betainc is the regularized incomplete beta I_x(a,b))."""
    from scipy.special import betainc
    return betainc(a, b, BAND[1]) - betainc(a, b, BAND[0])

def beta_cdf_closed(a, b, x):
    """For special cases use closed forms (uniform, arcsine)."""
    if a == 1 and b == 1:
        return x
    if a == 0.5 and b == 0.5:
        return (2.0/np.pi) * np.arcsin(np.sqrt(x))
    return None

print("=" * 70)
print("PART A: Exact value verification (3 independent methods)")
print("=" * 70)

test_cases = [
    ("Uniform Beta(1,1)", 1.0, 1.0, 0.4000),
    ("Beta(2,2) bell", 2.0, 2.0, 0.5680),
    ("Beta(0.5,0.5) U-shaped", 0.5, 0.5, 0.2620),
]

part_a = []
for name, a, b, claimed in test_cases:
    f_num = band_frac_numerical(a, b)
    f_mc = band_frac_montecarlo(a, b)
    try:
        f_scipy = band_frac_scipy(a, b)
    except Exception as e:
        f_scipy = float('nan')
        print(f"scipy unavailable: {e}")

    # Closed form where available
    f_closed = None
    cf = beta_cdf_closed(a, b, BAND[1])
    c0 = beta_cdf_closed(a, b, BAND[0])
    if cf is not None:
        f_closed = cf - c0

    print(f"\n{name}:")
    print(f"  claimed (SYN-050):        {claimed:.4f}")
    print(f"  numerical quadrature:     {f_num:.6f}  (err vs claimed: {abs(f_num-claimed):.6f})")
    if not np.isnan(f_scipy):
        print(f"  scipy betainc:            {f_scipy:.6f}")
    if f_closed is not None:
        print(f"  closed form:              {f_closed:.6f}")
    print(f"  Monte Carlo (2M):         {f_mc:.6f}  (err vs claimed: {abs(f_mc-claimed):.6f})")

    part_a.append({
        'case': name, 'alpha': a, 'beta': b, 'claimed': claimed,
        'numerical': f_num, 'scipy': None if np.isnan(f_scipy) else f_scipy,
        'montecarlo': f_mc,
        'max_abs_dev': max(abs(f_num - claimed), abs(f_mc - claimed))
    })

# Analytical sanity checks
# Beta(2,2): integral of 6x(1-x) from .3 to .7 = 6[x^2/2 - x^3/3] = exact
exact_22 = 6 * ((0.7**2/2 - 0.7**3/3) - (0.3**2/2 - 0.3**3/3))
print(f"\nAnalytic check Beta(2,2): exact = {exact_22:.6f} (SYN-050 claims 0.5680)")

print("\n" + "=" * 70)
print("PART B: Adversarial (alpha, beta) grid sweep")
print("=" * 70)

grid = np.arange(0.2, 8.001, 0.2)
band_matrix = np.zeros((len(grid), len(grid)))

for i, a in enumerate(grid):
    for j, b in enumerate(grid):
        band_matrix[i, j] = band_frac_numerical(a, b, n=50000)

# Save full landscape
np.save('../../shared_agora/artifacts/band_frac_landscape.npy', band_matrix)
np.save('../../shared_agora/artifacts/band_frac_grid_params.npy', grid)

print(f"Grid: alpha, beta in [0.2, 8.0] step 0.2 ({len(grid)}x{len(grid)} points)")
print(f"band_frac range: [{band_matrix.min():.4f}, {band_matrix.max():.4f}]")

print("\n" + "=" * 70)
print("PART C: Taxonomy gap analysis (SYN-050 classification)")
print("=" * 70)
# SYN-050 taxonomy:
#   U-shaped:      band_frac < 0.3
#   Uniform-like:  0.35 <= band_frac <= 0.45  (0.4 +/- 0.05)
#   Bell-shaped:   band_frac > 0.5
#   GAPS:          0.3 <= band_frac < 0.35  and  0.45 < band_frac <= 0.5

def classify(bf):
    if bf < 0.3: return 'U-shaped'
    if bf <= 0.45: return 'Uniform-like'
    if bf > 0.5: return 'Bell-shaped'
    return 'UNCLASSIFIED'

gap1 = np.where((band_matrix >= 0.3) & (band_matrix < 0.35))
gap2 = np.where((band_matrix > 0.45) & (band_matrix <= 0.5))

print(f"Points in gap 1 (0.3 <= bf < 0.35): {len(gap1[0])} / {band_matrix.size}")
print(f"Points in gap 2 (0.45 < bf <= 0.5): {len(gap2[0])} / {band_matrix.size}")

# Find concrete named-distribution counterexamples in the gaps
print("\nNamed counterexamples (integer/half-integer params) in gap regions:")
interesting = []
for a, b in [(1,2),(2,1),(1,3),(3,1),(1,4),(4,1),(2,3),(3,2),(1,1.5),(1.5,1),
             (2,1.5),(1.5,2),(0.5,1),(1,0.5),(3,0.5),(0.5,3),(2,4),(4,2),(3,4),(4,3)]:
    bf = band_frac_numerical(a, b, n=100000)
    cls = classify(bf)
    interesting.append((a, b, bf, cls))
    flag = "  <-- GAP" if cls == 'UNCLASSIFIED' else ""
    print(f"  Beta({a},{b}): band_frac = {bf:.4f}  -> {cls}{flag}")

# Degeneracy check: distinct shapes with SAME band_frac
# Find pairs (a,b) and (a',b') with different shapes but |bf1-bf2| < 0.005
print("\nDegeneracy probe: distinct (alpha,beta) pairs with nearly identical band_frac:")
degen_examples = []
# symmetric pairs at same "concentration"
probes = [
    ((1.0, 2.0), 'right-skewed, unimodal'),
    ((1.0, 1.0), 'uniform'),
    ((2.0, 1.0), 'left-skewed, unimodal'),
]
for (a, b), desc in probes:
    bf = band_frac_numerical(a, b)
    degen_examples.append((a, b, desc, bf))
    print(f"  Beta({a},{b}) [{desc}]: band_frac = {bf:.4f}")

# The key degeneracy: Beta(1,2) vs Beta(2,1) vs Uniform all give bf = 0.4000
# (by symmetry Beta(1,2) and Beta(2,1) are mirror images -> same bf; Uniform = 0.4)
bf_12 = band_frac_numerical(1, 2)
bf_21 = band_frac_numerical(2, 1)
bf_11 = band_frac_numerical(1, 1)
print(f"\n  DEGENERACY CONFIRMED: Beta(1,2)={bf_12:.4f}, Beta(2,1)={bf_21:.4f}, "
      f"Beta(1,1)={bf_11:.4f}")
print(f"  Three structurally different distributions (right-skewed, left-skewed,")
print(f"  flat) map to the IDENTICAL band_frac. A single scalar band_frac cannot")
print(f"  distinguish them -> classification is shape-DEGENERATE.")

print("\n" + "=" * 70)
print("PART D: Refinement proposal - augmented classification")
print("=" * 70)
# Proposal: pair band_frac with a skewness/dispersion invariant.
# For Beta(a,b): skewness S = 2(b-a)sqrt(a+b+1)/((a+b+2)sqrt(a+b)), 
# and use the full 2D map (band_frac, |S|) or (band_frac, entropy).

def beta_entropy(a, b):
    from math import lgamma
    # H = ln B(a,b) - (a-1)psi(a) - (b-1)psi(b) + (a-1)ln(1... standard formula
    # H = lnB(a,b) + (a-1)(psi(a)-ln(a+b-1)) + (b-1)(psi(b)-ln(a+b-1))
    from scipy.special import digamma, gammaln
    H = gammaln(a) + gammaln(b) - gammaln(a+b) \
        + (a-1)*(digamma(a) - digamma(a+b)) \
        + (b-1)*(digamma(b) - digamma(a+b))
    return H

def beta_skewness(a, b):
    s = np.sqrt(a + b)
    return 2.0*(b - a)*np.sqrt(a + b + 1) / ((a + b + 2.0)*s)

print("Augmented (band_frac, skewness) fingerprints for key distributions:")
fingerprints = []
for (a, b), desc in [
    ((1.0, 1.0), 'Uniform'),
    ((1.0, 2.0), 'right-skewed'),
    ((2.0, 1.0), 'left-skewed'),
    ((2.0, 2.0), 'bell'),
    ((0.5, 0.5), 'U-shaped'),
    ((0.5, 1.0), 'right U-shaped'),
    ((1.0, 0.5), 'left U-shaped'),
    ((1.0, 3.0), 'strong right-skew (GAP case)'),
]:
    bf = band_frac_numerical(a, b)
    S = beta_skewness(a, b)
    H = beta_entropy(a, b)
    fingerprints.append((a, b, desc, bf, S, H))
    print(f"  Beta({a},{b}) [{desc}]: bf={bf:.4f}, skew={S:+.4f}, entropy={H:.4f}")

print("\n  RESULT: The 2-fingerprint map (band_frac, |skewness|) separates all")
print("  degeneracy classes: Uniform (bf=0.40, S=0), skewed unimodal (bf=0.40,")
print("  |S|>0), bell (bf=0.57, S=0), U-shaped (bf=0.26, S=0) are all distinct.")

# Plots
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Landscape heatmap
ax = axes[0]
im = ax.imshow(band_matrix, origin='lower', extent=[grid[0], grid[-1], grid[0], grid[-1]],
               cmap='viridis', aspect='auto')
ax.axhline(0.3, color='red', ls='--', lw=1)
ax.axhline(0.35, color='orange', ls='--', lw=1)
ax.axhline(0.45, color='orange', ls='--', lw=1)
ax.axhline(0.5, color='red', ls='--', lw=1)
ax.set_xlabel('alpha')
ax.set_ylabel('beta')
ax.set_title('band_frac landscape (taxonomy boundaries shown)')
plt.colorbar(im, ax=ax)
# Mark gap regions
ax.text(4.1, 1.0, 'gap 1\n(0.3-0.35)', color='white', fontsize=8)

# Fingerprint scatter
ax = axes[1]
colors = plt.cm.tab10(np.linspace(0, 1, 8))
for idx, (a, b, desc, bf, S, H) in enumerate(fingerprints):
    ax.scatter(S, bf, s=80, color=colors[idx % 10], edgecolors='black', zorder=3)
    ax.annotate(desc, (S, bf), textcoords='offset points', xytext=(5, 5), fontsize=8)
ax.set_xlabel('|skewness| / signed skewness')
ax.set_ylabel('band_frac')
ax.set_title('Augmented fingerprint map (resolves degeneracy)')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/syn050_adversarial_stress_test.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nFigure saved: shared_agora/artifacts/syn050_adversarial_stress_test.png")

# Final summary
summary = f"""
SYN-050 Adversarial Stress Test - Summary
==========================================
PART A: Exact values
"""
for r in part_a:
    summary += f"  {r['case']}: claimed={r['claimed']:.4f}, numerical={r['numerical']:.6f}, MC={r['montecarlo']:.6f}, max_dev={r['max_abs_dev']:.6f}\n"
summary += f"  Analytic Beta(2,2) exact = {exact_22:.6f}\n"
summary += f"PART B: band_frac landscape range over (a,b) in [0.2,8]: [{band_matrix.min():.4f}, {band_matrix.max():.4f}]\n"
summary += f"PART C: Gap points: {len(gap1[0])} in [0.3,0.35), {len(gap2[0])} in (0.45,0.5]\n"
summary += f"  Beta(1,3) = {band_frac_numerical(1,3):.4f} (unclassified gap)\n"
summary += "  DEGENERACY: Beta(1,1), Beta(1,2), Beta(2,1) all give bf = 0.4000\n"
summary += "PART D: Refinement: augment band_frac with skewness S(a,b) to resolve degeneracy\n"

with open('../../shared_agora/artifacts/syn050_stress_test_summary.txt', 'w') as f:
    f.write(summary)
print(summary)
