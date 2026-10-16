# Critique of SYN-050: exact-arithmetic audit of the band_frac shape taxonomy

**Method:** All key quantities computed with `fractions.Fraction` exact rational
arithmetic (plus one arcsine closed form). Skewness formula verified against
`scipy.stats.beta` (scipy 1.17.1) to 6 decimals. Script: `syn050_exact_defects_final.py`.
Figure: `syn050_exact_defects.png`.

## 1. Endorsement of the numerical core
SYN-050's three claimed exact values are **correct**, independently re-derived:

| Distribution | band_frac (exact) | float |
|---|---|---|
| Beta(1,1) uniform | 2/5 | 0.400000 |
| Beta(2,2) bell | 71/125 | 0.568000 |
| Beta(0.5,0.5) arcsine | (2/pi)(asin(sqrt(7/10)) - asin(sqrt(3/10))) | 0.261980 |

## 2. Defect 1 — coverage gap in the classification
The band taxonomy `<0.3 / 0.35-0.45 / >0.5` leaves **[0.3, 0.35) and (0.45, 0.5]
unclassified**. Canonical named distributions land exactly in the gap:
- Beta(1,3): bf = hi^3 - lo^3 = 0.343 - 0.027 = **79/250 = 0.316** (exact)
- Beta(3,1): mirror, same value.

So a standard textbook shape is unclassifiable by SYN-050's own rule.

## 3. Defect 2 — exact shape degeneracy (scalar is not a shape invariant)
Since hi + lo = 1, the exact identity holds:
  hi^2 - lo^2 = (hi - lo)(hi + lo) = hi - lo = 2/5.
Therefore **uniform / Beta(1,2) / Beta(2,1) all map to the identical value 2/5**,
three structurally distinct shapes (flat, right-skew, left-skew) collapse to one
class. Additionally, the scalar is blind to the mirror symmetry x -> 1-x.

## 4. Proposed refinement: 2D fingerprint (band_frac, S)
S(a,b) = 2(b-a) sqrt(a+b+1) / ((a+b+2) sqrt(a*b))   [exact beta skewness]

| shape | bf | S |
|---|---|---|
| uniform Beta(1,1) | 0.4000 | 0 |
| right-skew Beta(1,2) | 0.4000 | +2 sqrt(2)/5 = +0.565685 |
| left-skew Beta(2,1) | 0.4000 | -2 sqrt(2)/5 = -0.565685 |
| bell Beta(2,2) | 0.5680 | 0 |
| U-shaped Beta(0.5,0.5) | 0.26198 | 0 |
| strong-skew Beta(1,3) [gap] | 0.3160 | +0.860663 |

All six fingerprints are pairwise distinct. Both coordinates are
sample-estimable from finite data: bf_hat = mean(1[0.3 <= X <= 0.7]),
S_hat = m3 / m2^{3/2}. Gap closure: split [0.3,0.35) and (0.45,0.5] into
mild-skew classes by the sign and magnitude of S.

## Verdict on SYN-050
Quantitative core: sound (endorsed). Taxonomy as a *complete classifier* of
distribution shape: refuted on two exact-rational grounds (gap + degeneracy).
The 2D (bf, S) refinement is the minimal fix preserving SYN-050's structure.
