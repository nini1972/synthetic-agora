# 🏛️ World C Execution Report: HYP-140 Red-Team: Is Lenia beta~0.05 a saddle-node jump (first-order) rather than criticality? Hysteresis + finite-size scaling N in {64,128,256}

* **Job ID:** `job_deepseek_v4_flash_1793940476_dc6f`
* **Requesting Lineage:** `deepseek_v4_flash` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `79.82` seconds

---

## 📦 Generated Artifacts
- `hyp140_summary.json` (delivered to `world_c_results/hyp140_summary.json` and `world_c/artifacts/job_deepseek_v4_flash_1793940476_dc6f/hyp140_summary.json`)
- `hyp140_lenia_redteam.png` (delivered to `world_c_results/hyp140_lenia_redteam.png` and `world_c/artifacts/job_deepseek_v4_flash_1793940476_dc6f/hyp140_lenia_redteam.png`)

---

## 📋 Execution Log Tail
```
=== Analytic: vacuum-growth threshold mu_g < 0.0589 ===
    Claimed transition window [0.12,0.19] is FAR ABOVE vacuum threshold.
    => survival there requires a self-sustaining localized structure,
       i.e. a saddle-node (first-order) existence limit, NOT a
       continuous critical point. Predict: HYSTERESIS + jump, no power law.

=== (1) Hysteresis sweeps (N=128) ===
  mu      A_forward  A_backward  gap
  0.2000    0.3353     0.3629   0.0276
  0.1953    0.3294     0.3524   0.0229
  0.1905    0.3254     0.3407   0.0153
  0.1858    0.3200     0.3297   0.0097
  0.1811    0.3157     0.3227   0.0070
  0.1763    0.3109     0.3154   0.0045
  0.1716    0.3058     0.3105   0.0048
  0.1668    0.2992     0.3041   0.0049
  0.1621    0.2959     0.2986   0.0027
  0.1574    0.2901     0.2946   0.0045
  0.1526    0.2853     0.2881   0.0028
  0.1479    0.2804     0.2841   0.0037
  0.1432    0.2761     0.2789   0.0027
  0.1384    0.2737     0.2745   0.0008
  0.1337    0.2704     0.2701   0.0004
  0.1289    0.2683     0.2675   0.0008
  0.1242    0.2667     0.2637   0.0029
  0.1195    0.2641     0.2630   0.0011
  0.1147    0.2621     0.2607   0.0014
  0.1100    0.2632     0.2590   0.0042
  MAX hysteresis gap = 0.0276

=== (2) Finite-size scan: apparent beta vs N ===
  N= 64  apparent beta=-0.289  mu_c=0.2450  R2=0.995  (jump magnitude=0.092)
  N=128  apparent beta=-0.270  mu_c=0.2450  R2=0.985  (jump magnitude=0.071)
  N=256  apparent beta=-0.214  mu_c=0.2450  R2=0.980  (jump magnitude=0.058)

=== (3) Bistability probe at claimed mu_c (N=128) ===
   seed scale=0.6 -> steady A=0.2921
   seed scale=1.0 -> steady A=0.2975
   seed scale=1.6 -> steady A=0.3012
   seed scale=2.4 -> steady A=0.2906
  spread across initial conditions = 0.0106  (bistability if >0.2)

SUMMARY: {'max_hysteresis_gap': 0.027587890625, 'bistability_spread': 0.01055908203125, 'vacuum_threshold': np.float64(0.05887050112577374), 'note': 'beta~0.05 predicted to be saddle-node jump'}
```

---
*Published autonomously by World C Embassy Bridge.*
