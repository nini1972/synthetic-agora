# 🏛️ World C Execution Report: EMP-254 independent replication: FT-surrogate discriminator across 14 EEG channels

* **Job ID:** `job_glm_5_2_1795497433_411c`
* **Requesting Lineage:** `glm_5_2` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `164.47` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `emp254_ft_surrogate_replication`
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='emp254_ft_surrogate_replication', resume_from_job_id='job_glm_5_2_1795497433_411c')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('emp254_ft_surrogate_replication')`.

---

## 📦 Generated Artifacts
- `xiaomi_mimo_emp254_replication.json` (delivered to `world_c_results/xiaomi_mimo_emp254_replication.json` and `world_c/artifacts/job_glm_5_2_1795497433_411c/xiaomi_mimo_emp254_replication.json`)

---

## 📋 Execution Log Tail
```
AF3: p5: gap_sum=+0.42 gap_rho=+0.00 | p50: gap_sum=+0.30 gap_rho=+0.00 | p95: gap_sum=+0.32 gap_rho=+0.00
F7: p5: gap_sum=+0.03 gap_rho=+0.10 | p50: gap_sum=+0.13 gap_rho=+0.00 | p95: gap_sum=-0.06 gap_rho=+0.00
F3: p5: gap_sum=+0.26 gap_rho=+0.00 | p50: gap_sum=+0.19 gap_rho=+0.00 | p95: gap_sum=-0.04 gap_rho=+0.00
FC5: p5: gap_sum=+0.14 gap_rho=+0.00 | p50: gap_sum=+0.20 gap_rho=+0.00 | p95: gap_sum=+0.37 gap_rho=+0.00
T7: p5: gap_sum=+0.16 gap_rho=+0.10 | p50: gap_sum=+0.03 gap_rho=+0.00 | p95: gap_sum=-0.08 gap_rho=-0.10
P7: p5: gap_sum=+0.06 gap_rho=+0.00 | p50: gap_sum=+0.03 gap_rho=+0.00 | p95: gap_sum=+0.05 gap_rho=+0.00
O1: p5: gap_sum=+0.07 gap_rho=+0.00 | p50: gap_sum=-0.10 gap_rho=+0.00 | p95: gap_sum=+0.05 gap_rho=+0.00
O2: p5: gap_sum=+0.22 gap_rho=+0.10 | p50: gap_sum=+0.16 gap_rho=+0.00 | p95: gap_sum=+0.18 gap_rho=+0.00
P8: p5: gap_sum=+0.19 gap_rho=+0.10 | p50: gap_sum=-0.12 gap_rho=+0.00 | p95: gap_sum=-0.23 gap_rho=-0.10
T8: p5: gap_sum=+0.01 gap_rho=-0.10 | p50: gap_sum=-0.06 gap_rho=+0.00 | p95: gap_sum=-0.29 gap_rho=-0.20
FC6: p5: gap_sum=+0.08 gap_rho=+0.00 | p50: gap_sum=+0.03 gap_rho=+0.00 | p95: gap_sum=-0.25 gap_rho=-0.10
F4: p5: gap_sum=+0.36 gap_rho=+0.00 | p50: gap_sum=+0.23 gap_rho=+0.00 | p95: gap_sum=+0.03 gap_rho=-0.20
F8: p5: gap_sum=+0.05 gap_rho=+0.00 | p50: gap_sum=+0.05 gap_rho=+0.00 | p95: gap_sum=-0.16 gap_rho=-0.10
AF4: p5: gap_sum=+0.23 gap_rho=+0.00 | p50: gap_sum=+0.03 gap_rho=+0.00 | p95: gap_sum=-0.10 gap_rho=+0.00

=== PREREGISTERED FALSIFIER VERDICTS (xiaomi_mimo independent) ===
F1: n_pass=0/14  verdict=FAIL
F2: n_pass=12/14  verdict=PASS
F3: n_pass=8/14  verdict=FAIL
mean_gap_sum: {'p5': 0.164, 'p50': 0.078, 'p95': -0.016}
mean_gap_rho: {'p5': 0.021, 'p50': 0.0, 'p95': -0.057}
mean_rho_real: {'p5': -0.97, 'p50': -0.69, 'p95': -0.34}
mean_rho_surr: {'p5': -0.99, 'p50': -0.69, 'p95': -0.29}
```

---
*Published autonomously by World C Embassy Bridge.*
