#!/usr/bin/env python3
"""Exact rational verification of band_frac coincidences (no numerics).

Identity used: for Beta(a,b) with integer a,b,
  P(X <= x) = sum_{j=0}^{a-1} C(a+b-1, j) x^j (1-x)^(a+b-1-j)
so
  P(lo <= X <= hi) = CDF(hi) - CDF(lo).
"""
from fractions import Fraction
import math

def beta_cdf_exact(a, b, x):
    n = a + b - 1
    s = Fraction(0)
    for j in range(0, a):
        s += Fraction(math.comb(n, j)) * x**j * (1-x)**(n-j)
    return s

def band_frac_exact(a, b):
    return beta_cdf_exact(a, b, Fraction(7,10)) - beta_cdf_exact(a, b, Fraction(3,10))

print("Exact rational band_frac values (band = [0.3, 0.7]):")
results = {}
for (a, b) in [(1,1), (1,2), (2,1), (2,2), (2,3), (3,2), (1,3), (3,1), (2,4), (4,2)]:
    bf = band_frac_exact(a, b)
    results[(a,b)] = bf
    print(f"  Beta({a},{b}): band_frac = {bf} = {float(bf):.10f}")

# U-shaped Beta(0.5,0.5): closed form (2/pi)(asin sqrt(x)|_.7 - asin sqrt(x)|_.3)
import numpy as np
bf_half = (2/np.pi)*(np.arcsin(np.sqrt(0.7)) - np.arcsin(np.sqrt(0.3)))
print(f"  Beta(0.5,0.5): (2/pi)(asin sqrt(.7) - asin sqrt(.3)) = {bf_half:.10f}")

print("\n=== COINCIDENCE 1: bf = 2/5 exactly ===")
f11, f12, f21 = results[(1,1)], results[(1,2)], results[(2,1)]
print(f"  Beta(1,1) = {f11}, Beta(1,2) = {f12}, Beta(2,1) = {f21}")
print(f"  All exactly 2/5? {f11 == Fraction(2,5) and f12 == Fraction(2,5) and f21 == Fraction(2,5)}")
print("  Shapes: flat vs right-skewed vs left-skewed -> single scalar cannot separate them.")

print("\n=== COINCIDENCE 2: beta-family 'bell plateau' ===")
f22, f23, f32 = results[(2,2)], results[(2,3)], results[(3,2)]
print(f"  Beta(2,2) = {f22} = {float(f22):.10f}")
print(f"  Beta(2,3) = {f23} = {float(f23):.10f}")
print(f"  Beta(3,2) = {f32} = {float(f32):.10f}")
print(f"  All equal? {f22 == f23 == f32}")
print("  Beta(2,2) is the canonical SYMMETRIC bell; Beta(2,3)/Beta(3,2) are")
print("  SKEWED unimodal. The taxonomy's 'Bell-shaped: bf > 0.5' class therefore")
print("  conflates symmetric bells with asymmetric skewed unimodals.")

print("\n=== GAP COUNTEREXAMPLES (integer-param, named) ===")
f13, f31 = results[(1,3)], results[(3,1)]
print(f"  Beta(1,3) = {f13} = {float(f13):.10f}  -> falls in GAP 1 [0.3, 0.35)")
f24, f42 = results[(2,4)], results[(4,2)]
print(f"  Beta(2,4) = {f24} = {float(f24):.10f}  -> falls in GAP 2 (0.45, 0.5]")
print(f"  Beta(4,2) = {f42} = {float(f42):.10f}  -> same GAP 2 value (symmetry)")
print("  These are standard textbook distributions that the SYN-050 3-bucket")
print("  taxonomy (U / Uniform-like / Bell) leaves unclassified.")
