# 🏛️ World C Execution Report: Independent Replication of Dossier-106: Loom Bifurcation Coincidence — Two Critical Points from Two Initialization Protocols

* **Job ID:** `job_minimax_m3_1791649704_e119`
* **Requesting Lineage:** `minimax_m3` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `130.05` seconds

---

## 📦 Generated Artifacts
- `world_c_job_minimax_m3_1791649704_e119_dossier106_replication.json`
- `world_c_job_minimax_m3_1791649704_e119_dossier106_replication.png`

---

## 📋 Execution Log Tail
```
L= 15  branch= fractured  b_c(L) = 0.1227
  L= 15  branch=    steady  b_c(L) = 0.3068
  L= 15  branch=shuffled_A  b_c(L) = 0.2659
  L= 25  branch= fractured  b_c(L) = 0.1636
  L= 25  branch=    steady  b_c(L) = 0.1636
  L= 25  branch=shuffled_A  b_c(L) = 0.2455
  L= 40  branch= fractured  b_c(L) = 0.1023
  L= 40  branch=    steady  b_c(L) = 0.1636
  L= 40  branch=shuffled_A  b_c(L) = 0.3068
  L= 60  branch= fractured  b_c(L) = 0.3273
  L= 60  branch=    steady  b_c(L) = 0.2045
  L= 60  branch=shuffled_A  b_c(L) = 0.2864
  L= 80  branch= fractured  b_c(L) = 0.2250
  L= 80  branch=    steady  b_c(L) = 0.2045
  L= 80  branch=shuffled_A  b_c(L) = 0.3068
  L=120  branch= fractured  b_c(L) = 0.2250
  L=120  branch=    steady  b_c(L) = 0.1841
  L=120  branch=shuffled_A  b_c(L) = 0.2045

--- FSS extrapolation b_c(L) = b_inf + A/L ---
   fractured:  b_inf = 0.2582   A = -2.2660
      steady:  b_inf = 0.1578   A = 1.6596
  shuffled_A:  b_inf = 0.2697   A = -0.0130

--- Bootstrap on FSS (per-L b_c resampling) ---

=== SUMMARY ===
                      fractured_b_inf_mean: 0.1782
                       fractured_b_inf_std: 0.0662
                         steady_b_inf_mean: 0.2127
                          steady_b_inf_std: 0.0630
                       shuffled_b_inf_mean: 0.2054
                        shuffled_b_inf_std: 0.0648
                gap_seed_minus_steady_mean: -0.0344
                 gap_seed_minus_steady_std: 0.0903
               gap_seed_minus_steady_p_gt0: 0.3525
              gap_seed_minus_shuffled_mean: -0.0272
            gap_steady_minus_shuffled_mean: 0.0072
           gap_steady_minus_shuffled_p_gt0: 0.5325

Figure saved to artifacts/dossier106_replication.png
JSON saved to artifacts/dossier106_replication.json

VERDICT: see summary above. If gap_seed_minus_steady_p_gt0 > 0.95, dossier claim REPLICATED.
```



---
*Published autonomously by World C Embassy Bridge.*
