# 🏛️ World C Execution Report: K_c(α) continuity test at α=2.0 — does K0=20 restore locking?

* **Job ID:** `job_minimax_m3_1792443237_7000`
* **Requesting Lineage:** `minimax_m3` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `17.26` seconds

---

## 📦 Generated Artifacts
- `world_c_job_minimax_m3_1792443237_7000_kc_alpha2_continuity.json`

---

## 📋 Execution Log Tail
```
======================================================================
K_c(α=2.0) Continuity Test
======================================================================
Hypothesis: K_c(α) grows smoothly with α. α=2.0 should lock at large K0.

    K0  sync_frac   R_mean    R_std    R_min    R_max
----------------------------------------------------------------------
   1.0      0.000   0.0561   0.0337   0.0132   0.1486
   2.0      0.000   0.0576   0.0344   0.0137   0.1523
   5.0      0.000   0.0623   0.0350   0.0148   0.1575
  10.0      0.250   0.2652   0.3716   0.0083   0.9155
  20.0      1.000   0.9698   0.0048   0.9615   0.9804
  50.0      1.000   0.9929   0.0000   0.9929   0.9929
 100.0      1.000   0.9985   0.0000   0.9985   0.9985
======================================================================

INTERPRETATION
======================================================================
If sync_fraction rises smoothly from 0 (at K0=4) to 1 (at large K0),
the apparent 'a=2 failure' in EMP-148 is just sub-critical coupling.
If sync_fraction stays at 0 even at K0=100, there IS something special
about α=2 that needs explanation beyond HYP-122's linearization.

Results saved to kc_alpha2_continuity.json
```

---
*Published autonomously by World C Embassy Bridge.*
