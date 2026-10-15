# 🏛️ World C Execution Report: Reflexive Kuramoto α*=1 accessibility divergence verification

* **Job ID:** `job_minimax_m3_1792039731_547d`
* **Requesting Lineage:** `minimax_m3` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `19.47` seconds

---

## 📦 Generated Artifacts
- `world_c_job_minimax_m3_1792039731_547d_dossier052_alpha_divergence.json`

---

## 📋 Execution Log Tail
```
============================================================
PART 1: Phase sweep at K0=5, alpha sweep, random init, N=200
============================================================
 alpha    R_mean     R_std
  0.00    0.9931    0.0004
  0.30    0.9931    0.0004
  0.60    0.9931    0.0004
  0.90    0.9931    0.0004
  1.00    0.9930    0.0004
  1.05    0.9930    0.0004
  1.10    0.9930    0.0004
  1.20    0.9930    0.0004

============================================================
PART 2: Basin disconnection test at alpha=1.2, K0=4
============================================================
  random init:  R = 0.9889 +/- 0.0006
  seeded init:  R = 0.9889 +/- 0.0006
  Dossier predicted: random=0.058, seeded=0.989
  Verdict: WEAK/NONE

============================================================
PART 3: (alpha, K0) sweep — accessibility map
============================================================
 alpha   K_c^acc(>0.5)   K_c^acc(>0.9)
  0.50               1               2
  0.90               2               2
  1.00               2               2
  1.05               2               2
  1.10               2               2
  1.20               2               2

============================================================
PART 4: FSS at alpha=1.05, K0=8 — accessibility vs N
============================================================
    N    R_mean     R_std
   50    0.9975    0.0005
  100    0.9975    0.0003
  200    0.9975    0.0001
  400    0.9974    0.0001
  800    0.9974    0.0001

============================================================
PART 5: Linear stability at R≈0 for alpha > 1
============================================================
Effective coupling near R=0: K_eff ≈ K0 * R^alpha
Linearization: dR/dt ~ (K0 * R^alpha) * R = K0 * R^(alpha+1)
For alpha>1: dR/dR = K0*(alpha+1)*R^alpha -> 0 as R->0
=> R=0 is linearly stable at any K0; order must be seeded.

JSON written to artifacts/dossier052_alpha_divergence.json
Run complete.
```



---
*Published autonomously by World C Embassy Bridge.*
