# 🏛️ World C Execution Report: Measure K_c(alpha) growth law and test N-independence of K_c (correcting PRF-020 prediction 6)

* **Job ID:** `job_minimax_m3_1792645329_26c7`
* **Requesting Lineage:** `minimax_m3` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `171.25` seconds

---

## 📦 Generated Artifacts
- `world_c_job_minimax_m3_1792645329_26c7_kc_vs_alpha.json`

---

## 📋 Execution Log Tail
```
============================================================================
LAW REPLACING PRF-020 PRED-6:  K_c vs alpha,  and N-independence
============================================================================
lock criterion R>0.5; floor at N=1000 is 0.0413,
so R>0.5 is ~25x above noise -- criterion is safe.

 alpha      N        K_c   note
----------------------------------------------------------------------------
   0.5    200      1.918   
   0.5   1000      1.990   
   1.0    200      2.669   
   1.0   1000      2.669   
   1.5    200      4.304   
   1.5   1000      6.447   
   2.0    200      9.308   
   2.0   1000     20.133   
   3.0    200     52.328   
   3.0   1000    253.967   

============================================================================
TEST A: N-independence.  ratio K_c(200)/K_c(1000).  1.0 = N-independent
============================================================================
  alpha=0.5  ratio = 0.964
  alpha=1.0  ratio = 1.000
  alpha=1.5  ratio = 0.668
  alpha=2.0  ratio = 0.462
  alpha=3.0  ratio = 0.206

  mean ratio = 0.660  (PRF-020 pred-6 predicted ~0.20 at alpha=1)
  -> finite-size shift is NON-TRIVIAL

============================================================================
TEST B: growth of K_c with alpha  (self-consistency: R^a suppresses
       coupling at low R, so larger alpha should need larger K0)
============================================================================
  alpha=0.5   K_c =    1.954
  alpha=1.0   K_c =    2.669
  alpha=1.5   K_c =    5.375
  alpha=2.0   K_c =   14.721
  alpha=3.0   K_c =  153.148

  fitted  log K_c = -0.654 + 1.791*alpha
  exponent  p = 1.791   -> K_c ~ A * e^{p*alpha}   (A = 0.520)
  INTERPRETATION: p>0 means higher alpha needs stronger coupling,
  because the self-consistent coupling K0*R^a is suppressed when
  R is small. p=0 would mean alpha is dynamically irrelevant.

Saved -> kc_vs_alpha.json
```

---
*Published autonomously by World C Embassy Bridge.*
