import numpy as np
import os

print("="*70)
print("CRITICAL VERIFICATION: PRF-012's Adler Ceiling Derivation")
print("="*70)
print()

R_lo, R_hi = 0.3, 0.7

# PRF-012's delta function: delta(y) = (1 + y^2) / (2y)
def delta(y):
    return (1 + y**2) / (2*y)

delta_lo = delta(R_lo)
delta_hi = delta(R_hi)

print(f"delta(y) = (1 + y^2) / (2y)")
print(f"delta(0.3) = {delta_lo:.10f} = {1 + 0.09}/{0.6} = 1.09/0.6 = {1.09/0.6:.10f}")
print(f"  Exact: 109/60 = {109/60:.10f}")
print(f"delta(0.7) = {delta_hi:.10f} = {1 + 0.49}/{1.4} = 1.49/1.4 = {1.49/1.4:.10f}")
print(f"  Exact: 149/140 = {149/140:.10f}")
print()

# The Adler ceiling: C = 1 - delta(0.7) / delta(0.3)
C_adler = 1 - delta_hi / delta_lo
C_adler_exact = 1 - (149/140) / (109/60)
C_adler_exact_frac = 1 - (149*60) / (140*109)

print(f"C = 1 - delta(0.7) / delta(0.3)")
print(f"  = 1 - (149/140) / (109/60)")
print(f"  = 1 - (149 * 60) / (140 * 109)")
print(f"  = 1 - {149*60} / {140*109}")
print(f"  = 1 - {149*60}/{140*109}")
print(f"  = 1 - 8940/15260")
print(f"  = 1 - {8940/15260:.10f}")
print(f"  = {1 - 8940/15260:.10f}")
print(f"  = 316/763 = {316/763:.10f}")
print()

print(f"PRF-012 closed form: C = 316/763 = {316/763:.10f}")
print(f"Direct computation:  C = {C_adler:.10f}")
print(f"Exact fraction:      C = {C_adler_exact_frac:.10f}")
print(f"Match: {np.isclose(C_adler, 316/763, rtol=1e-10)}")
print()

# HYP-048's claim: C = integral_{0.3}^{0.7} dx = 0.4
C_uniform = 0.7 - 0.3
print(f"HYP-048's uniform integral: C = 0.7 - 0.3 = {C_uniform:.10f}")
print(f"316/763 = {316/763:.10f}")
print(f"Difference: {316/763 - C_uniform:.10f}")
print()

# Key question: Is delta(y) = (1+y^2)/(2y) related to 2*arcsin(y/2)?
# delta(y) = (1+y^2)/(2y) is the formula from the Adler equation
# 2*arcsin(y/2) is from the Kuramoto R = 2*sin(delta/2) geometry
# These are DIFFERENT functions!

print("="*70)
print("COMPARISON: PRF-012's delta(y) vs Kuramoto R(delta) inversion")
print("="*70)
print()

for y in [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
    d_prf012 = (1 + y**2) / (2*y)
    d_kuramoto = 2 * np.arcsin(y/2)  # inverse of R = 2*sin(delta/2)
    print(f"y={y:.1f}: delta_PRF012 = (1+y²)/(2y) = {d_prf012:.6f}")
    print(f"         delta_kuramoto = 2*arcsin(y/2) = {d_kuramoto:.6f}")
    print(f"         ratio = {d_prf012/d_kuramoto:.6f}")
    print()

print("="*70)
print("CONCLUSION: PRF-012's delta(y) = (1+y²)/(2y) is NOT the same as")
print("2*arcsin(y/2) from the Kuramoto R = 2*sin(delta/2) mapping.")
print("HYP-048 conflated these two different geometric relationships.")
print("The Adler ceiling C = 316/763 is a genuine dynamical bound from")
print("the Adler synchronization condition, NOT a distributional integral.")
print("="*70)
print()

# Let's also show that C = 1 - delta(0.7)/delta(0.3) is NOT equal to 0.4
# The fraction 316/763 is irreducible
import math
g = math.gcd(316, 763)
print(f"gcd(316, 763) = {g}")
print(f"316/763 is {'irreducible' if g == 1 else 'reducible'}")
print(f"0.4 = 2/5, and 316/763 ≠ 2/5 since 2*763 = {2*763} ≠ 5*316 = {5*316}")
