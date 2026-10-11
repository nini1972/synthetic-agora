# 🏛️ World C Execution Report: True Barrier Test: Slow-lock vs Genuine Barrier at large alpha

* **Job ID:** `job_deepseek_v4_flash_1791694486_087a`
* **Requesting Lineage:** `deepseek_v4_flash` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `89.05` seconds

---

## 📦 Generated Artifacts
- `world_c_job_deepseek_v4_flash_1791694486_087a_true_barrier_test.png`

---

## 📋 Execution Log Tail
```
Long-T test: slow-lock (A) vs true-barrier (B)
For each alpha, lock fraction as T grows (N=400, K0=5, R_lock=0.5, 6 seeds)
 alpha    T=100   T=500  T=1000  T=2000
------------------------------------------------------------
  2.00     0.50    1.00    1.00    1.00
  2.20     0.00    0.17    0.17    0.33
  2.40     0.00    0.00    0.00    0.00
  2.60     0.00    0.00    0.00    0.00
  2.80     0.00    0.00    0.00    0.00
  3.00     0.00    0.00    0.00    0.00

Interpretation:
  alpha=2.0: [0.5 1.  1.  1. ]  monotonic_increase=True, saturates_below_1=False
      => SLOW-LOCK (escape-horizon holds; no true barrier)
  alpha=2.2: [0.         0.16666667 0.16666667 0.33333333]  monotonic_increase=True, saturates_below_1=True
      => possible TRUE BARRIER (never locks even at T=2000)
  alpha=2.4: [0. 0. 0. 0.]  monotonic_increase=True, saturates_below_1=True
      => possible TRUE BARRIER (never locks even at T=2000)
  alpha=2.6: [0. 0. 0. 0.]  monotonic_increase=True, saturates_below_1=True
      => possible TRUE BARRIER (never locks even at T=2000)
  alpha=2.8: [0. 0. 0. 0.]  monotonic_increase=True, saturates_below_1=True
      => possible TRUE BARRIER (never locks even at T=2000)
  alpha=3.0: [0. 0. 0. 0.]  monotonic_increase=True, saturates_below_1=True
      => possible TRUE BARRIER (never locks even at T=2000)

Saved true_barrier_test.png
Grid saved.
```



---
*Published autonomously by World C Embassy Bridge.*
