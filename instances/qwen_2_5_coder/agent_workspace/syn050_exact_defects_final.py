#!/usr/bin/env python3
"""Exact-rational audit of the SYN-050 band_frac taxonomy: two structural
defects (coverage gap + shape degeneracy) and the skewness-augmented fix.
All key values computed with Fraction arithmetic where possible."""
from fractions import Fraction
import numpy as np, math, itertools, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

lo, hi = Fraction(3, 10), Fraction(7, 10)
os.makedirs('../../shared_agora/artifacts', exist_ok=True)

print("=" * 66)
print("EXACT RATIONAL AUDIT (Fraction arithmetic)")
print("=" * 66)

p_uniform = hi - lo                    # Beta(1,1): pdf = 1
p_12 = hi**2 - lo**2                   # Beta(1,2): F = 1-(1-x)^2
p_21 = hi**2 - lo**2                   # Beta(2,1): F = x^2
p_13 = hi**3 - lo**3                   # Beta(1,3): F = 1-(1-x)^3
p_31 = hi**3 - lo**3                   # Beta(3,1)
p_22 = 6 * ((hi**2/2 - hi**3/3) - (lo**2/2 - lo**3/3))  # Beta(2,2)
p_05 = (2/math.pi) * (math.asin(math.sqrt(0.7)) - math.asin(math.sqrt(0.3)))

for name, p in [("Beta(1,1) uniform", p_uniform),
                ("Beta(1,2) right-skew", p_12),
                ("Beta(2,1) left-skew", p_21),
                ("Beta(1,3) strong skew", p_13),
                ("Beta(3,1) strong skew", p_31),
                ("Beta(2,2) bell", p_22)]:
    print(f"  {name:24s} bf = {p} = {float(p):.6f} (exact)")
print(f"  {'Beta(0.5,0.5) arcsine':24s} bf = {p_05:.6f} (arcsine closed form)")

print()
print("DEFECT 1 (coverage gap): bands = [<0.3, 0.35..0.45, >0.5]")
print(f"  Beta(1,3): bf = {float(p_13):.4f} = 0.7^3-0.3^3 lies in gap [0.3,0.35)")
print(f"  Beta(3,1): bf = {float(p_31):.4f} in the same gap (mirror).")
print()
print("DEFECT 2 (shape degeneracy): hi+lo = 1 gives the EXACT identity")
print(f"  hi^2 - lo^2 = (hi-lo)(hi+lo) = hi-lo = 0.4, so")
print(f"  uniform / Beta(1,2) / Beta(2,1) all map to {p_uniform}.")
print("  Three structurally distinct shapes -> one identical scalar.")
print("  (Mirror symmetry x -> 1-x also preserves the band in general.)")

def beta_skew(a, b):
    # exact beta skewness; denominator has sqrt(a*b), NOT sqrt(a+b)
    return 2*(b-a)*np.sqrt(a+b+1) / ((a+b+2)*np.sqrt(a*b))

print()
print("REFINEMENT: 2D fingerprint (band_frac, skewness S)")
rows = [("uniform Beta(1,1)", 1.0, 1.0, 0.4),
        ("right-skew Beta(1,2)", 1.0, 2.0, 0.4),
        ("left-skew Beta(2,1)", 2.0, 1.0, 0.4),
        ("bell Beta(2,2)", 2.0, 2.0, float(p_22)),
        ("U-shaped Beta(0.5,0.5)", 0.5, 0.5, p_05),
        ("strong-skew Beta(1,3) [gap]", 1.0, 3.0, float(p_13))]
pts = []
for name, a, b, bf in rows:
    S = beta_skew(a, b)
    pts.append((S, bf))
    note = "  [exact S = +2*sqrt(2)/5]" if (a, b) == (1.0, 2.0) else \
           "  [exact S = -2*sqrt(2)/5]" if (a, b) == (2.0, 1.0) else ""
    print(f"  {name:28s} bf={bf:.5f}  S={S:+.5f}{note}")

ok = all(np.hypot(s1-s2, b1-b2) > 1e-12
         for (s1, b1), (s2, b2) in itertools.combinations(pts, 2))
print(f"\n  All {len(pts)} fingerprints pairwise distinct in (bf, S): {ok}")
print("  Both coords sample-estimable: bf_hat = mean(0.3<=X<=0.7),")
print("  S_hat = m3/m2^1.5. Gap closure: split [0.3,0.35) & (0.45,0.5]")
print("  into mild-skew classes by sign/magnitude of S.")

x = np.linspace(1e-4, 1-1e-4, 2000)
def pdf(a, b, xx):
    from math import lgamma
    lnB = lgamma(a) + lgamma(b) - lgamma(a+b)
    return np.exp((a-1)*np.log(xx) + (b-1)*np.log(1-xx) - lnB)

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.axvspan(0.3, 0.7, color='gold', alpha=0.3, zorder=0)
ax.plot(x, pdf(1, 1, x), lw=2.5, color='tab:blue',
        label=r'Beta(1,1): bf = 0.4 (exact)')
ax.plot(x, pdf(1, 2, x), lw=2.5, color='tab:red',
        label=r'Beta(1,2): bf = 0.4 (exact)')
ax.plot(x, pdf(2, 1, x), lw=2.5, color='tab:green',
        label=r'Beta(2,1): bf = 0.4 (exact)')
ax.plot(x, pdf(1, 3, x), lw=2.0, ls='--', color='tab:purple',
        label=r'Beta(1,3): bf = 0.316 (gap case)')
ax.set_xlabel('x on [0,1]'); ax.set_ylabel('density')
ax.set_title('Three exact-degenerate shapes + one gap case, band [0.3, 0.7]')
ax.legend(fontsize=9); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('../../shared_agora/artifacts/syn050_exact_defects.png', dpi=150)
plt.close()
print("\nFigure saved: shared_agora/artifacts/syn050_exact_defects.png")
