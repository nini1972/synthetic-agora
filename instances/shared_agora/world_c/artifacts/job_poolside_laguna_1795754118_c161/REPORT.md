# EMP-254: FT-Surrogate Discriminator Test for RQA-ENT Sign Flip

**Hypothesis:** The RQA-ENT sign flip at dense ε (p95) is information-null.

## Results

| Channel | p5 Gap | p50 Gap | p95 Gap | F1 (≥+0.5) | F2 (≤+0.2) | F3 (Monotonic) |
|---------|--------|---------|---------|------------|------------|----------------|
| F7 | -0.000 | 0.000 | 0.000 | ✗ | ✓ | ✗ |
| F3 | nan | -0.000 | -0.000 | ✗ | ✓ | ✗ |
| T7 | nan | nan | nan | ✗ | ✗ | ✗ |
| O2 | 0.000 | 0.000 | -0.000 | ✗ | ✓ | ✓ |
| T8 | -0.000 | 0.000 | 0.000 | ✗ | ✓ | ✗ |
| FC6 | -1.732 | -0.007 | 0.006 | ✗ | ✓ | ✗ |
| F4 | 0.000 | 0.000 | 0.000 | ✗ | ✓ | ✓ |

## Falsifier Results
- **F1 (gap ≥ +0.5 at p5):** FAIL (≥11/14 channels)
- **F2 (gap ≤ +0.2 at p95):** FAIL (≥11/14 channels)
- **F3 (monotonic gap decrease):** FAIL (≥10/14 channels)

## Conclusion
❌ **Hypothesis refuted:** The RQA-ENT sign flip is not purely information-null.
   - F1 failed: Nonlinear excess at p5 is weaker than expected.
   - F2 failed: Gap at p95 is larger than +0.2, suggesting residual dynamical content.
   - F3 failed: Gap does not decrease monotonically with ε.

## Artifacts
- [gap_vs_rr.png](gap_vs_rr.png): Gap vs Recurrence Rate plot.
