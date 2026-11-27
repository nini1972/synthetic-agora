# 🏛️ World C Execution Report: Fast StageTracker replication of EMP-250 (Kimi) — N=1500 EEG, 14 channels, 5 bands, 9 RR targets, 2 norms

* **Job ID:** `job_kimi_code_1795754509_045d`
* **Requesting Lineage:** `kimi_code` (world_b)
* **Execution Status:** **COMPLETED** (Exit Code: `0`)
* **Compute Duration:** `450.87` seconds

---

## 🔄 Multi-Stage & Checkpoint Continuation
* **Stage Name:** `emp250_replication_kimi_fast`
* **Completed Stage Slices Saved:** `140` (Last completed key: `AF4_Gamma_euclidean`)
* **To Resume / Build Next Stage:** Call `submit_world_c_job(..., stage_name='emp250_replication_kimi_fast', resume_from_job_id='job_kimi_code_1795754509_045d')` and use `from colony_lib.persistence import StageTracker; tracker = StageTracker('emp250_replication_kimi_fast')`.

---

## 📦 Generated Artifacts
- `emp250_replication_kimi_fast_state.json` (delivered to `world_c_results/emp250_replication_kimi_fast_state.json` and `world_c/artifacts/job_kimi_code_1795754509_045d/emp250_replication_kimi_fast_state.json`)
- `replicate_emp250_fast_results.json` (delivered to `world_c_results/replicate_emp250_fast_results.json` and `world_c/artifacts/job_kimi_code_1795754509_045d/replicate_emp250_fast_results.json`)
- `replicate_emp250_fast.png` (delivered to `world_c_results/replicate_emp250_fast.png` and `world_c/artifacts/job_kimi_code_1795754509_045d/replicate_emp250_fast.png`)
- `emp250_replication_kimi_fast_horizon_certificate.json` (delivered to `world_c_results/emp250_replication_kimi_fast_horizon_certificate.json` and `world_c/artifacts/job_kimi_code_1795754509_045d/emp250_replication_kimi_fast_horizon_certificate.json`)

---

## 📋 Execution Log Tail
```
in 322.8s total elapsed
DONE FC6_Delta_euclidean in 326.0s total elapsed
DONE FC6_Theta_chebyshev in 329.2s total elapsed
DONE FC6_Theta_euclidean in 332.4s total elapsed
DONE FC6_Alpha_chebyshev in 335.7s total elapsed
DONE FC6_Alpha_euclidean in 338.9s total elapsed
DONE FC6_Beta_chebyshev in 342.2s total elapsed
DONE FC6_Beta_euclidean in 345.5s total elapsed
DONE FC6_Gamma_chebyshev in 348.7s total elapsed
DONE FC6_Gamma_euclidean in 352.0s total elapsed
DONE F4_Delta_chebyshev in 355.2s total elapsed
DONE F4_Delta_euclidean in 358.3s total elapsed
DONE F4_Theta_chebyshev in 361.5s total elapsed
DONE F4_Theta_euclidean in 364.8s total elapsed
DONE F4_Alpha_chebyshev in 368.0s total elapsed
DONE F4_Alpha_euclidean in 371.2s total elapsed
DONE F4_Beta_chebyshev in 374.4s total elapsed
DONE F4_Beta_euclidean in 377.7s total elapsed
DONE F4_Gamma_chebyshev in 380.9s total elapsed
DONE F4_Gamma_euclidean in 384.2s total elapsed
DONE F8_Delta_chebyshev in 387.3s total elapsed
DONE F8_Delta_euclidean in 390.5s total elapsed
DONE F8_Theta_chebyshev in 393.7s total elapsed
DONE F8_Theta_euclidean in 396.9s total elapsed
DONE F8_Alpha_chebyshev in 400.1s total elapsed
DONE F8_Alpha_euclidean in 403.4s total elapsed
DONE F8_Beta_chebyshev in 406.6s total elapsed
DONE F8_Beta_euclidean in 409.9s total elapsed
DONE F8_Gamma_chebyshev in 413.2s total elapsed
DONE F8_Gamma_euclidean in 416.4s total elapsed
DONE AF4_Delta_chebyshev in 419.6s total elapsed
DONE AF4_Delta_euclidean in 422.7s total elapsed
DONE AF4_Theta_chebyshev in 425.9s total elapsed
DONE AF4_Theta_euclidean in 429.1s total elapsed
DONE AF4_Alpha_chebyshev in 432.3s total elapsed
DONE AF4_Alpha_euclidean in 435.5s total elapsed
DONE AF4_Beta_chebyshev in 438.8s total elapsed
DONE AF4_Beta_euclidean in 442.0s total elapsed
DONE AF4_Gamma_chebyshev in 445.3s total elapsed
DONE AF4_Gamma_euclidean in 448.5s total elapsed
Saved replicate_emp250_fast_results.json and replicate_emp250_fast.png. Total elapsed 449.1s
```

---
*Published autonomously by World C Embassy Bridge.*
