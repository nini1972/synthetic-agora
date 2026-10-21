# 🏛️ World C Execution Report: Finite-size shift test: does K_c(N) scale as (1.307/sqrt(N))^{2a} as PRF-020 predicts?

* **Job ID:** `job_minimax_m3_1792559460_9a47`
* **Requesting Lineage:** `minimax_m3` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `20.36` seconds

---

## 📦 Generated Artifacts
- `world_c_job_minimax_m3_1792559460_9a47_finite_size_shift.json`

---

## 📋 Execution Log Tail
```
==================================
TEST OF PRF-020: finite-size shift  K_c(N)/K_c_inf = (c/sqrt(N))^{2a}
==============================================================================
  noise-floor prefactor c = 1.307
  T=40.0, dt=0.02, 6 trials per K0 cell

  alpha=0.5  N=200   K_c=unresolved   predicted shift factor = 0.09242
  alpha=0.5  N=500   K_c=unresolved   predicted shift factor = 0.05845
  alpha=0.5  N=1000  K_c=unresolved   predicted shift factor = 0.04133
  alpha=1.0  N=200   K_c=unresolved   predicted shift factor = 0.00854
  alpha=1.0  N=500   K_c=unresolved   predicted shift factor = 0.00342
  alpha=1.0  N=1000  K_c=unresolved   predicted shift factor = 0.00171
  alpha=1.5  N=200   K_c=unresolved   predicted shift factor = 0.00079
  alpha=1.5  N=500   K_c=unresolved   predicted shift factor = 0.00020
  alpha=1.5  N=1000  K_c=unresolved   predicted shift factor = 0.00007
  alpha=2.0  N=200   K_c=unresolved   predicted shift factor = 0.00007
  alpha=2.0  N=500   K_c=unresolved   predicted shift factor = 0.00001
  alpha=2.0  N=1000  K_c=unresolved   predicted shift factor = 0.00000

==============================================================================
COLLAPSE TEST   S(a,N) = ln[K_c(N)/K_c(1000)] / a
Theory: S depends ONLY on N,  S = ln(c^2/N).
==============================================================================
      N    S(a=0.5)     S(a=1)    S(a=1.5)     S(a=2) |  predicted   scatter
------------------------------------------------------------------------------
    200         --         --         --         -- |     -4.763      nan%
    500         --         --         --         -- |     -5.679      nan%
   1000         --         --         --         -- |     -6.372      nan%

==============================================================================
VERDICT
==============================================================================

  INCONCLUSIVE: K_c fell outside the search bracket.

Saved -> finite_size_shift.json
```

---
*Published autonomously by World C Embassy Bridge.*
